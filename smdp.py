# smdp.py
import math

def es_posicion_valida(mapa, filas, cols, r, c):
    """Verifica si la celda está en los límites y no es muralla ni vacío."""
    if 0 <= r < filas and 0 <= c < cols:
        if mapa[r][c] != ' ' and mapa[r][c] != 'X':
            return True
    return False

def esperanza_factor_descuento(landa, mu, sigma):
    """
    Calcula E[landa^t] para t ~ Normal(mu, sigma) de forma analítica.
    Fórmula: landa^mu * exp(0.5 * sigma^2 * ln(landa)^2)
    Esto evita muestreo aleatorio durante la iteración de valor,
    garantizando convergencia determinista.
    """
    ln_landa = math.log(landa)
    return (landa ** mu) * math.exp(0.5 * (sigma ** 2) * (ln_landa ** 2))

# Parámetros de tiempo por acción según enunciado: Normal(mu, sigma)
TIEMPOS_ACCION = {
    "Norte": (2, 0.2),
    "Sur":   (2, 0.2),
    "Este":  (3, 0.3),
    "Oeste": (3, 0.3),
}

def calcular_politica_smdp(mapa, filas, cols, acciones, prob_exito, prob_fallo, landa):
    """
    Aplica Iteración de Valor para el SMDP (1.2).
    - Factor de descuento continuo: E[landa^t] calculado analíticamente
    - Tiempos: Norte/Sur ~ Normal(2, 0.2) | Este/Oeste ~ Normal(3, 0.3)
    - Prob. éxito = 90%  → el robot se mueve en la dirección deseada
    - Prob. fallo  = 10% → el robot se queda en su posición actual
    - Convergencia formal: |V_nuevo - V| < epsilon en todas las celdas
    """
    EPSILON = 1e-6

    # Pre-calcular E[landa^t] para cada acción (valor determinista)
    factores_descuento = {
        nombre: esperanza_factor_descuento(landa, mu, sigma)
        for nombre, (mu, sigma) in TIEMPOS_ACCION.items()
    }

    V = [[0.0 for _ in range(cols)] for _ in range(filas)]
    politica = [[None for _ in range(cols)] for _ in range(filas)]

    while True:
        delta = 0.0
        V_nuevo = [[0.0 for _ in range(cols)] for _ in range(filas)]

        for r in range(filas):
            for c in range(cols):
                if mapa[r][c] == 'M':
                    V_nuevo[r][c] = 100.0
                    continue
                if mapa[r][c] == ' ' or mapa[r][c] == 'X':
                    continue

                mejor_valor = float('-inf')
                mejor_accion = None

                for nombre_accion, (dr, dc) in acciones.items():
                    r_sig, c_sig = r + dr, c + dc

                    if not es_posicion_valida(mapa, filas, cols, r_sig, c_sig):
                        r_sig, c_sig = r, c

                    # Factor de descuento E[landa^t] para esta acción
                    fd = factores_descuento[nombre_accion]

                    recompensa_exito = 100.0 if mapa[r_sig][c_sig] == 'M' else -1.0
                    recompensa_fallo = -1.0

                    # Ecuación de Bellman SMDP con descuento continuo
                    valor_esperado = (
                        prob_exito * (recompensa_exito + fd * V[r_sig][c_sig]) +
                        prob_fallo  * (recompensa_fallo  + fd * V[r][c])
                    )

                    if valor_esperado > mejor_valor:
                        mejor_valor  = valor_esperado
                        mejor_accion = nombre_accion

                V_nuevo[r][c]  = mejor_valor
                politica[r][c] = mejor_accion
                delta = max(delta, abs(V_nuevo[r][c] - V[r][c]))

        V = V_nuevo

        if delta < EPSILON:
            break

    return politica, V

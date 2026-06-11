# mdp.py

def es_posicion_valida(mapa, filas, cols, r, c):
    """Verifica si la celda está en los límites y no es muralla ni vacío."""
    if 0 <= r < filas and 0 <= c < cols:
        if mapa[r][c] != ' ' and mapa[r][c] != 'X':
            return True
    return False

def calcular_politica_mdp(mapa, filas, cols, acciones, prob_exito, prob_fallo, landa):
    """
    Aplica Iteración de Valor para el MDP Clásico (1.1).
    - Factor de descuento: landa = 0.97
    - Prob. éxito = 90%  → el robot se mueve en la dirección deseada
    - Prob. fallo  = 10% → el robot se queda en su posición actual
    - Convergencia formal: |V_nuevo - V| < epsilon en todas las celdas
    """
    EPSILON = 1e-6

    V = [[0.0 for _ in range(cols)] for _ in range(filas)]
    politica = [[None for _ in range(cols)] for _ in range(filas)]

    while True:
        delta = 0.0
        V_nuevo = [[0.0 for _ in range(cols)] for _ in range(filas)]

        for r in range(filas):
            for c in range(cols):
                # Celda meta: valor fijo
                if mapa[r][c] == 'M':
                    V_nuevo[r][c] = 100.0
                    continue
                # Celda no transitable: se ignora
                if mapa[r][c] == ' ' or mapa[r][c] == 'X':
                    continue

                mejor_valor = float('-inf')
                mejor_accion = None

                for nombre_accion, (dr, dc) in acciones.items():
                    r_sig, c_sig = r + dr, c + dc

                    # Si la celda destino no es válida, el robot se queda en su lugar
                    if not es_posicion_valida(mapa, filas, cols, r_sig, c_sig):
                        r_sig, c_sig = r, c

                    recompensa_exito  = 100.0 if mapa[r_sig][c_sig] == 'M' else -1.0
                    recompensa_fallo  = -1.0  # fallo: robot permanece en (r, c)

                    # Ecuación de Bellman con transición estocástica
                    valor_esperado = (
                        prob_exito * (recompensa_exito + landa * V[r_sig][c_sig]) +
                        prob_fallo  * (recompensa_fallo  + landa * V[r][c])
                    )

                    if valor_esperado > mejor_valor:
                        mejor_valor  = valor_esperado
                        mejor_accion = nombre_accion

                V_nuevo[r][c]  = mejor_valor
                politica[r][c] = mejor_accion
                delta = max(delta, abs(V_nuevo[r][c] - V[r][c]))

        V = V_nuevo

        # Criterio de convergencia formal
        if delta < EPSILON:
            break

    return politica, V

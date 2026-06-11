# mdp.py

def es_posicion_valida(mapa, filas, cols, r, c):
    """Verifica si la celda está en los límites y no es muralla ni vacío."""
    if 0 <= r < filas and 0 <= c < cols:
        if mapa[r][c] != ' ' and mapa[r][c] != 'X':
            return True
    return False

def calcular_politica_mdp(mapa, filas, cols, acciones, prob_exito, prob_fallo, landa):
    """Aplica Iteración de Valor para el MDP Clásico (1.1)."""
    V = [[0.0 for _ in range(cols)] for _ in range(filas)]
    politica = [[None for _ in range(cols)] for _ in range(filas)]
    
    for _ in range(100):  # Iteraciones para convergencia
        V_nuevo = [[0.0 for _ in range(cols)] for _ in range(filas)]
        for r in range(filas):
            for c in range(cols):
                if mapa[r][c] == 'M':
                    V_nuevo[r][c] = 100.0  # Meta
                    continue
                if mapa[r][c] == ' ' or mapa[r][c] == 'X':
                    continue
                    
                mejor_valor = float('-inf')
                mejor_accion = None
                
                for nombre_accion, (dr, dc) in acciones.items():
                    r_sig, c_sig = r + dr, c + dc
                    if not es_posicion_valida(mapa, filas, cols, r_sig, c_sig):
                        r_sig, c_sig = r, c  # Choca y se queda en su lugar
                        
                    recompensa_sig = 100 if mapa[r_sig][c_sig] == 'M' else -1
                    recompensa_actual = -1
                    
                    valor_exito = prob_exito * (recompensa_sig + landa * V[r_sig][c_sig])
                    valor_fallo = prob_fallo * (recompensa_actual + landa * V[r][c])
                    valor_esperado = valor_exito + valor_fallo
                    
                    if valor_esperado > mejor_valor:
                        mejor_valor = valor_esperado
                        mejor_accion = nombre_accion
                        
                V_nuevo[r][c] = mejor_valor
                politica[r][c] = mejor_accion
        V = V_nuevo
        
    return politica
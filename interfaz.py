# interfaz.py
import tkinter as tk
import random

# Importamos la lógica desde los otros dos archivos
from mdp import calcular_politica_mdp
from smdp import calcular_politica_smdp

# ---------------- CONFIGURACIÓN GLOBAL ----------------
MAPA_STR = [
    "  OOOO ",
    "  O  O ",
    "OOOXOOO",
    "  O  O ",
    "  OOOO ",
    "   M   "
]
MAPA = [list(fila) for fila in MAPA_STR]
FILAS, COLS = len(MAPA), len(MAPA[0])

LANDA = 0.97
PROB_EXITO = 0.90
PROB_FALLO = 0.10

ACCIONES = {
    "Norte": (-1, 0), "Sur": (1, 0),
    "Este": (0, 1), "Oeste": (0, -1)
}

# ---------------- INTERFAZ GRÁFICA ----------------
class SimulacionGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Navegación 2D - MDP vs SMDP")
        self.master.configure(padx=20, pady=20)
        
        # Panel de Botones
        frame_controles = tk.Frame(master)
        frame_controles.pack(pady=10)
        
        tk.Button(frame_controles, text="Ejecutar MDP Clásico", 
                  command=self.iniciar_mdp, width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_controles, text="Ejecutar SMDP", 
                  command=self.iniciar_smdp, width=20).pack(side=tk.LEFT, padx=10)
        
        # Panel del Mapa
        self.frame_mapa = tk.Frame(master)
        self.frame_mapa.pack()
        
        self.celdas_gui = [[None for _ in range(COLS)] for _ in range(FILAS)]
        self.construir_grilla()
        
        # Variables de estado
        self.robot_r, self.robot_c = 0, 0
        self.politica = None
        self.usar_smdp = False
        self.en_ejecucion = False

    def construir_grilla(self):
        """Arma el mapa en pantalla utilizando etiquetas (Labels) en una cuadrícula."""
        for r in range(FILAS):
            for c in range(COLS):
                celda = MAPA[r][c]
                color = self.master.cget('bg') # Color de fondo por defecto
                texto = ""
                
                if celda == 'X':
                    color = "gray"
                elif celda == 'M':
                    color = "lightgreen"
                    texto = "M"
                elif celda == 'O':
                    color = "lightblue"
                    
                lbl = tk.Label(self.frame_mapa, text=texto, width=6, height=3, 
                               bg=color, relief="groove", borderwidth=1)
                lbl.grid(row=r, column=c, padx=2, pady=2)
                self.celdas_gui[r][c] = lbl

    def reiniciar_mapa(self):
        """Limpia la posición anterior del robot antes de una nueva simulación."""
        for r in range(FILAS):
            for c in range(COLS):
                if MAPA[r][c] == 'O':
                    self.celdas_gui[r][c].config(bg="lightblue")
                elif MAPA[r][c] == 'M':
                    self.celdas_gui[r][c].config(bg="lightgreen")

    def encontrar_inicio(self):
        """Encuentra la primera celda libre arriba a la izquierda."""
        for r in range(FILAS):
            for c in range(COLS):
                if MAPA[r][c] == 'O':
                    return r, c
        return 0, 0

    def iniciar_mdp(self):
        self.preparar_simulacion(usar_smdp=False)

    def iniciar_smdp(self):
        self.preparar_simulacion(usar_smdp=True)

    def preparar_simulacion(self, usar_smdp):
        """Llama al archivo correspondiente para calcular la matemática e inicia el bucle visual."""
        if self.en_ejecucion:
            return 
            
        self.reiniciar_mapa()
        self.usar_smdp = usar_smdp
        self.master.title(f"Simulando: {'SMDP' if usar_smdp else 'MDP Clásico'}")
        
        # ¡Aquí se comunican los archivos!
        if usar_smdp:
            self.politica = calcular_politica_smdp(MAPA, FILAS, COLS, ACCIONES, PROB_EXITO, PROB_FALLO, LANDA)
        else:
            self.politica = calcular_politica_mdp(MAPA, FILAS, COLS, ACCIONES, PROB_EXITO, PROB_FALLO, LANDA)
            
        self.robot_r, self.robot_c = self.encontrar_inicio()
        self.celdas_gui[self.robot_r][self.robot_c].config(bg="red") # Dibuja al robot
        
        self.en_ejecucion = True
        self.master.after(800, self.mover_robot) # Espera un poco y arranca

    def mover_robot(self):
        """Actualiza la posición del robot basándose en la política calculada."""
        if MAPA[self.robot_r][self.robot_c] == 'M':
            print("Meta alcanzada!")
            self.en_ejecucion = False
            return
            
        # Borrar robot de la celda actual
        color_previo = "lightblue" if MAPA[self.robot_r][self.robot_c] == 'O' else "lightgreen"
        self.celdas_gui[self.robot_r][self.robot_c].config(bg=color_previo)
        
        accion_optima = self.politica[self.robot_r][self.robot_c]
        
        # Probabilidad de éxito del 90%
        if random.random() <= PROB_EXITO:
            dr, dc = ACCIONES[accion_optima]
            r_sig, c_sig = self.robot_r + dr, self.robot_c + dc
            # Validar si puede moverse ahí
            if 0 <= r_sig < FILAS and 0 <= c_sig < COLS and MAPA[r_sig][c_sig] not in [' ', 'X']:
                self.robot_r, self.robot_c = r_sig, c_sig
        
        # Pintar robot en la nueva celda
        self.celdas_gui[self.robot_r][self.robot_c].config(bg="red")
        
        # Si es SMDP, variar la velocidad visual para reflejar las distribuciones normales
        if self.usar_smdp:
            t = random.gauss(2, 0.2) if accion_optima in ["Norte", "Sur"] else random.gauss(3, 0.3)
            tiempo_espera = int(max(0, t) * 300) 
        else:
            tiempo_espera = 600
            
        self.master.after(tiempo_espera, self.mover_robot)

# ---------------- EJECUCIÓN ----------------
if __name__ == "__main__":
    ventana = tk.Tk()
    app = SimulacionGUI(ventana)
    ventana.mainloop()
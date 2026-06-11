# interfaz.py
import tkinter as tk
import random

from mdp  import calcular_politica_mdp
from smdp import calcular_politica_smdp, TIEMPOS_ACCION

# ─────────────────────────────────────────────
#  MAPA exacto según enunciado (imagen PDF)
#  7 columnas × 6 filas
#  ' ' = espacio vacío  |  'O' = celda libre
#  'X' = muralla        |  'M' = meta
# ─────────────────────────────────────────────
MAPA_STR = [
    " OOOO  ",   # fila 0: cols 2,3,4,5
    " O  O  ",   # fila 1: cols 2 y 5
    "OOOXOOO",   # fila 2: 0,1,2, X en 3, 4,5,6
    "  O O  ",   # fila 3: cols 2 y 5
    "  OOO  ",   # fila 4: cols 2,3,4
    "   M   ",   # fila 5: M en col 3
]
MAPA  = [list(fila) for fila in MAPA_STR]
FILAS = len(MAPA)
COLS  = len(MAPA_STR[0])

LANDA      = 0.97
PROB_EXITO = 0.90
PROB_FALLO = 0.10

ACCIONES = {
    "Norte": (-1, 0),
    "Sur":   ( 1, 0),
    "Este":  ( 0, 1),
    "Oeste": ( 0,-1),
}
FLECHA = {"Norte": "↑", "Sur": "↓", "Este": "→", "Oeste": "←"}

# Colores
COR_LIBRE  = "#AED6F1"
COR_MURO   = "#566573"
COR_META   = "#58D68D"
COR_ROBOT  = "#E74C3C"
COR_CAMINO = "#F9E79F"
COR_BG     = "#ECF0F1"
TAM_CELDA  = 80


class SimulacionGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Navegación 2D — MDP vs SMDP")
        self.master.configure(bg=COR_BG, padx=16, pady=16)

        self.politica = None
        self.valores  = None
        self.usar_smdp = False
        self.en_ejecucion = False
        self.robot_r = self.robot_c = 0
        self.rastro  = []
        self._robot_visible = False

        self._construir_ui()

    # ── Construcción de la UI ───────────────────────────────────────────────

    def _construir_ui(self):
        tk.Label(self.master,
                 text="Simulación de Navegación 2D — MDP / SMDP",
                 bg=COR_BG, font=("Helvetica", 14, "bold")).pack(pady=(0, 4))

        info = f"λ = {LANDA}   |   P(éxito) = {int(PROB_EXITO*100)}%   |   P(fallo) = {int(PROB_FALLO*100)}%"
        tk.Label(self.master, text=info, bg=COR_BG,
                 font=("Helvetica", 10)).pack(pady=(0, 8))

        fr_btn = tk.Frame(self.master, bg=COR_BG)
        fr_btn.pack(pady=(0, 10))

        btn_kw = dict(width=18, height=1, font=("Helvetica", 11, "bold"),
                      relief="raised", bd=2, cursor="hand2")

        tk.Button(fr_btn, text="▶  MDP Clásico",
                  bg="#2980B9", fg="white",
                  command=self.iniciar_mdp, **btn_kw).pack(side=tk.LEFT, padx=8)

        tk.Button(fr_btn, text="▶  SMDP",
                  bg="#8E44AD", fg="white",
                  command=self.iniciar_smdp, **btn_kw).pack(side=tk.LEFT, padx=8)

        tk.Button(fr_btn, text="↺  Reiniciar",
                  bg="#7F8C8D", fg="white",
                  command=self.reiniciar_todo, **btn_kw).pack(side=tk.LEFT, padx=8)

        self.canvas = tk.Canvas(self.master,
                                width=COLS * TAM_CELDA,
                                height=FILAS * TAM_CELDA,
                                bg=COR_BG, highlightthickness=0)
        self.canvas.pack()

        self.lbl_estado = tk.Label(
            self.master,
            text="Selecciona un algoritmo para comenzar.",
            bg=COR_BG, font=("Helvetica", 10, "italic"), fg="#555")
        self.lbl_estado.pack(pady=(8, 0))

        self._construir_leyenda()
        self._dibujar_mapa()

    def _construir_leyenda(self):
        fr = tk.Frame(self.master, bg=COR_BG)
        fr.pack(pady=(8, 0))
        items = [
            (COR_LIBRE,  "Celda libre"),
            (COR_MURO,   "Muralla (X)"),
            (COR_META,   "Meta (M)"),
            (COR_ROBOT,  "Robot"),
            (COR_CAMINO, "Rastro"),
        ]
        for color, texto in items:
            c = tk.Canvas(fr, width=16, height=16, bg=COR_BG, highlightthickness=0)
            c.create_rectangle(0, 0, 16, 16, fill=color, outline="#999")
            c.pack(side=tk.LEFT, padx=(10, 2))
            tk.Label(fr, text=texto, bg=COR_BG,
                     font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(0, 8))

    # ── Dibujado ─────────────────────────────────────────────────────────────

    def _dibujar_mapa(self, mostrar_politica=False):
        self.canvas.delete("all")
        for r in range(FILAS):
            for c in range(COLS):
                ch = MAPA[r][c]
                x0, y0 = c * TAM_CELDA, r * TAM_CELDA
                x1, y1 = x0 + TAM_CELDA, y0 + TAM_CELDA
                xm, ym = (x0 + x1) // 2, (y0 + y1) // 2

                # Celdas vacías: sin dibujar
                if ch == ' ':
                    continue

                # Color de fondo
                if ch == 'X':
                    color = COR_MURO
                elif ch == 'M':
                    color = COR_META
                elif (r, c) in self.rastro:
                    color = COR_CAMINO
                else:
                    color = COR_LIBRE

                self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill=color, outline="#999", width=1)

                # Etiquetas fijas
                if ch == 'X':
                    self.canvas.create_text(xm, ym, text="X",
                        font=("Helvetica", 20, "bold"), fill="#ECF0F1")
                elif ch == 'M':
                    self.canvas.create_text(xm, ym - 10, text="M",
                        font=("Helvetica", 18, "bold"), fill="#1A5276")
                    self.canvas.create_text(xm, ym + 12, text="META",
                        font=("Helvetica", 8), fill="#1A5276")

                # Política encima de celdas libres
                if mostrar_politica and self.politica and ch == 'O':
                    accion = self.politica[r][c]
                    if accion:
                        self.canvas.create_text(xm, ym - 8,
                            text=FLECHA[accion],
                            font=("Helvetica", 24), fill="#1A5276")
                        if self.valores:
                            v = self.valores[r][c]
                            self.canvas.create_text(xm, ym + 18,
                                text=f"{v:.1f}",
                                font=("Helvetica", 8), fill="#555")

        # Robot (siempre encima)
        if self._robot_visible:
            self._dibujar_robot()

    def _dibujar_robot(self):
        r, c = self.robot_r, self.robot_c
        pad = 10
        x0 = c * TAM_CELDA + pad
        y0 = r * TAM_CELDA + pad
        x1 = (c + 1) * TAM_CELDA - pad
        y1 = (r + 1) * TAM_CELDA - pad
        xm, ym = (x0 + x1) // 2, (y0 + y1) // 2
        self.canvas.create_oval(x0, y0, x1, y1,
                                fill=COR_ROBOT, outline="#922B21", width=2)
        self.canvas.create_text(xm, ym, text="R",
                                font=("Helvetica", 14, "bold"), fill="white")

    # ── Simulación ───────────────────────────────────────────────────────────

    def iniciar_mdp(self):
        self._preparar(usar_smdp=False)

    def iniciar_smdp(self):
        self._preparar(usar_smdp=True)

    def _preparar(self, usar_smdp):
        if self.en_ejecucion:
            return
        self.usar_smdp = usar_smdp
        self.rastro = []
        self._robot_visible = False

        nombre = "SMDP" if usar_smdp else "MDP Clásico"
        self.lbl_estado.config(text=f"Calculando política {nombre}…")
        self.master.update_idletasks()

        if usar_smdp:
            self.politica, self.valores = calcular_politica_smdp(
                MAPA, FILAS, COLS, ACCIONES, PROB_EXITO, PROB_FALLO, LANDA)
        else:
            self.politica, self.valores = calcular_politica_mdp(
                MAPA, FILAS, COLS, ACCIONES, PROB_EXITO, PROB_FALLO, LANDA)

        self.robot_r, self.robot_c = self._encontrar_inicio()
        self._robot_visible = True
        self.en_ejecucion   = True

        self.lbl_estado.config(
            text=f"Política {nombre} calculada — robot navegando…")
        self._dibujar_mapa(mostrar_politica=True)
        self.master.after(900, self._mover_robot)

    def _encontrar_inicio(self):
        """Primera celda 'O' del mapa (arriba-izquierda)."""
        for r in range(FILAS):
            for c in range(COLS):
                if MAPA[r][c] == 'O':
                    return r, c
        return 0, 0

    def _mover_robot(self):
        if MAPA[self.robot_r][self.robot_c] == 'M':
            self.en_ejecucion   = False
            self._robot_visible = False
            self.lbl_estado.config(
                text="✅  ¡Meta alcanzada!  Puedes ejecutar otro algoritmo.")
            self._dibujar_mapa(mostrar_politica=True)
            return

        self.rastro.append((self.robot_r, self.robot_c))
        accion = self.politica[self.robot_r][self.robot_c]

        # Movimiento estocástico: 90% éxito, 10% se queda
        if random.random() <= PROB_EXITO:
            dr, dc = ACCIONES[accion]
            r_sig, c_sig = self.robot_r + dr, self.robot_c + dc
            if (0 <= r_sig < FILAS and 0 <= c_sig < COLS
                    and MAPA[r_sig][c_sig] not in [' ', 'X']):
                self.robot_r, self.robot_c = r_sig, c_sig

        self._dibujar_mapa(mostrar_politica=True)

        if self.usar_smdp:
            mu, sigma = TIEMPOS_ACCION[accion]
            t = max(0.5, random.gauss(mu, sigma))
            delay = int(t * 280)
        else:
            delay = 550

        self.master.after(delay, self._mover_robot)

    def reiniciar_todo(self):
        if self.en_ejecucion:
            return
        self.politica       = None
        self.valores        = None
        self.rastro         = []
        self._robot_visible = False
        self._dibujar_mapa(mostrar_politica=False)
        self.lbl_estado.config(text="Selecciona un algoritmo para comenzar.")


# ── EJECUCIÓN ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ventana = tk.Tk()
    app = SimulacionGUI(ventana)
    ventana.mainloop()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overlay Windows simulant un compteur de taxi plus design pour afficher en direct votre salaire qui défile,
et qui affiche toutes les 30 sec un message d'encouragement aléatoire parmi une liste de 10,
et permet de déplacer la fenêtre par clic-glisser.

Design :
- Coins arrondis
- Barre supérieure jaune rappelant l'enseigne taxi
- Texte "SALARY" et montant en deux typographies
- Fenêtre sans bordure et toujours au premier plan
- Transparence autour de la zone arrondie uniquement
- Déplacement par clic-glisser
"""
import tkinter as tk
import time
import random
from tkinter import font as tkfont

# === CONFIGURATION ===
SALARY_PER_HOUR = 3000.00    # Votre salaire à l'heure
UPDATE_INTERVAL_MS = 100     # Intervalle de mise à jour (ms)
ENCOURAGE_INTERVAL_MS = 30000  # Intervalle de message encouragement (30 s)
# Dimensions de l'affichage
WIDTH, HEIGHT = 400, 120
# Offset par rapport au bord supérieur droit initial
X_OFFSET, Y_OFFSET = 50, 50
# Couleurs
BG_COLOR = "#333"          # Fond du compteur
ACCENT_COLOR = "#FFD700"   # Jaune taxi
TEXT_COLOR = "#FFFFFF"     # Texte principal
LABEL_COLOR = "#FFFFFF"    # Texte label
# Couleur masque pour la transparence (ne pas utiliser dans le dessin)
MASK_COLOR = "#123456"

# Liste de 10 messages d'encouragement
MESSAGES = [
    "Continue comme ça !",
    "Tu gères !",
    "Super boulot !",
    "Chaque seconde compte !",
    "Gardez le rythme !",
    "Tu es incroyable !",
    "Tu tiens le coup !",
    "Fonce !",
    "Ne lâche rien !",
    "Bravo, continue !"
]

# Fonction pour dessiner un rectangle arrondi
def round_rect(canvas, x1, y1, x2, y2, r=20, **kwargs):
    points = [
        x1+r, y1,
        x2-r, y1,
        x2, y1,
        x2, y1+r,
        x2, y2-r,
        x2, y2,
        x2-r, y2,
        x1+r, y2,
        x1, y2,
        x1, y2-r,
        x1, y1+r,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

class TaxiOverlay:
    def __init__(self):
        self.start_time = time.time()
        self.root = tk.Tk()
        # Initialisation des polices
        self.font_label = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.font_salary = tkfont.Font(family="Helvetica", size=32, weight="bold")
        self._setup_window()
        self._create_canvas()
        self._make_draggable()
        self._start_update()
        self._schedule_encouragement()
        self.root.mainloop()

    def _setup_window(self):
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        # Fenêtre masquée sur la couleur MASK_COLOR
        self.root.config(bg=MASK_COLOR)
        self.root.attributes("-transparentcolor", MASK_COLOR)
        screen_w = self.root.winfo_screenwidth()
        x = screen_w - WIDTH - X_OFFSET
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{Y_OFFSET}")

    def _create_canvas(self):
        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH,
            height=HEIGHT,
            bg=MASK_COLOR,
            highlightthickness=0
        )
        self.canvas.pack()
        # Zone arrondie principale
        round_rect(self.canvas, 0, 0, WIDTH, HEIGHT, r=20, fill=BG_COLOR, outline=ACCENT_COLOR, width=4)
        # Barre supérieure jaune
        round_rect(self.canvas, 4, 4, WIDTH-4, 30, r=16, fill=ACCENT_COLOR, outline=ACCENT_COLOR)
        # Label "SALARY"
        self.canvas.create_text(
            WIDTH/2, 18,
            text="SALARY",
            fill=LABEL_COLOR,
            font=self.font_label
        )
        # Texte montant initial
        self.text_id = self.canvas.create_text(
            WIDTH/2, HEIGHT/2 + 10,
            text="0.00",
            fill=TEXT_COLOR,
            font=self.font_salary
        )

    def _make_draggable(self):
        # Permet de déplacer la fenêtre par clic-glisser
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)

    def _on_press(self, event):
        # Coordonnées du clic
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _on_drag(self, event):
        # Calcule nouvelle position de la fenêtre
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self.root.geometry(f'+{x}+{y}')

    def _start_update(self):
        self._update()

    def _update(self):
        elapsed = time.time() - self.start_time
        sec_rate = SALARY_PER_HOUR / 3600.0
        amount = sec_rate * elapsed
        display = f"{amount:,.2f}"
        self.canvas.itemconfigure(self.text_id, text=display)
        self.root.after(UPDATE_INTERVAL_MS, self._update)

    def _schedule_encouragement(self):
        msg = random.choice(MESSAGES)
        if hasattr(self, 'enc_text_id'):
            self.canvas.delete(self.enc_text_id)
        self.enc_text_id = self.canvas.create_text(
            WIDTH/2, HEIGHT - 15,
            text=msg,
            fill=ACCENT_COLOR,
            font=self.font_label
        )
        self.root.after(5000, lambda: self.canvas.delete(self.enc_text_id))
        self.root.after(ENCOURAGE_INTERVAL_MS, self._schedule_encouragement)

if __name__ == '__main__':
    TaxiOverlay()

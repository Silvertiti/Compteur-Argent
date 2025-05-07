#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overlay Windows simulant un compteur de taxi design pour :
- afficher en direct votre salaire qui défile,
- afficher toutes les 30 s un message d'encouragement,
- déplacer la fenêtre (clic gauche sur compteur, clic droit sur cookie),
- carré 🍪 comptant les clics (peut être négatif, cache la vidéo si < –100),
- mini-calculatrice Pythagore à côté du cookie,
- bouton 🛒 ouvrant la boutique d’auto-clics dans une nouvelle fenêtre,
- inventaire affichant vos emojis achetés,
- course de chevaux intégrée à droite de la vidéo (pari & animation),
- vidéo YouTube en boucle sous le compteur,
- son de fond continu (vidéo dJs04lHumSA),
- vidéo spéciale toutes les 10 minutes en plein écran au centre,
- mini-jeu de Blackjack SOUS la vidéo avec table de pari,
  boutons Hit/Stand/New Game et mise de cookies.
PRÉREQUIS :
- Installer VLC (https://www.videolan.org/) pour libvlc.dll
- pip install python-vlc yt_dlp pillow
"""
import os
import sys
import time
import random
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk

# URL de la vidéo spéciale et intervalle (10 min)
SPECIAL_VIDEO_URL        = "https://www.youtube.com/watch?v=aaAZGJ6EpT4"
SPECIAL_VIDEO_INTERVAL_MS = 10 * 60 * 1000

# URL pour le son de fond
AUDIO_BG_URL = "https://www.youtube.com/watch?v=dJs04lHumSA"

# constantes course de chevaux intégrée
HORSE_COUNT = 6
HORSE_DELAY = 50
HORSE_SIZE  = 20

# detection VLC + yt_dlp
os_env = os.environ
USE_VIDEO = False
if sys.platform.startswith("win"):
    for p in (
        os_env.get("VLC_PATH",""),
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC"
    ):
        if p and os.path.isdir(p):
            os.add_dll_directory(p)
            plug = os.path.join(p, "plugins")
            if os.path.isdir(plug):
                os_env["VLC_PLUGIN_PATH"] = plug
            break
try:
    import vlc
    from yt_dlp import YoutubeDL
    USE_VIDEO = True
except ImportError:
    print("[Warning] Vidéo désactivée (python-vlc/yt_dlp manquant)")

# chemin table de pari Blackjack
IMAGE_PATH = r"C:\Users\axoncare\Desktop\te\table.jpg"

# CONFIG principale
SALARY_PER_HOUR = 3000.00
UPDATE_MS       = 100
ENCOURAGE_MS    = 30000
YT_URL          = "https://www.youtube.com/watch?v=L_fcrOyoWZ8"

METER_W, METER_H = 400, 120
COOKIE_SIZE      = METER_H
CALC_W           = 120
SHOP_W           = 50
INV_W            = 100
VIDEO_H          = 200
FAIR_W           = 200
BJ_SCALE         = 0.40

# déterminer hauteur BJ
try:
    _img = Image.open(IMAGE_PATH)
    scale_full = (METER_W + COOKIE_SIZE + CALC_W + SHOP_W + INV_W + FAIR_W) / _img.width
    BJ_H = int(_img.height * scale_full)
    TABLE_IMG = _img
except:
    BJ_H = 150
    TABLE_IMG = None

TOTAL_W = METER_W + COOKIE_SIZE + CALC_W + SHOP_W + INV_W + FAIR_W
TOTAL_H = METER_H + (VIDEO_H if USE_VIDEO else 0) + BJ_H
X_OFF, Y_OFF = 50, 50

BG_COLOR    = "#333"
ACCENT      = "#FFD700"
TEXT_COLOR  = "#FFF"
LABEL_COLOR = "#FFF"
MASK_COLOR  = "#123456"
TABLE_GREEN = "#006400"

MESSAGES = [
    "Continue comme ça !","Tu gères !","Super boulot !",
    "Chaque seconde compte !","Gardez le rythme !","Tu es incroyable !",
    "Tu tiens le coup !","Fonce !","Ne lâche rien !","Bravo, continue !"
]

def round_rect(c, x1, y1, x2, y2, r=20, **kw):
    pts = [
        x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
        x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
        x1,y2, x1,y2-r, x1,y1+r, x1,y1
    ]
    return c.create_polygon(pts, smooth=True, **kw)

class TaxiOverlay:
    def __init__(self):
        # état
        self.start       = time.time()
        self.click_count = 0
        self.current_bet = 0
        self.upgrades    = [
            {'emoji':'🍓','cost':10,'interval':5000,'amount':1,'count':0},
            {'emoji':'🐌','cost':50,'interval':10000,'amount':5,'count':0},
        ]
        self.shop_window = None

        # fenetre
        self.root      = tk.Tk()
        self.f_label   = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.f_salary  = tkfont.Font(family="Helvetica", size=32, weight="bold")

        self._setup_window()
        self._create_top_row()

        if USE_VIDEO:
            self._create_video()
            self._play_video()
            self._play_audio_bg()       # démarre le son de fond
            self._create_horse_race()

        self._create_blackjack()
        self._bind_drag()
        self._update_salary()
        self._schedule_enc()
        self._start_upgrades()
        self._schedule_special_video()

        self.root.mainloop()

    def _setup_window(self):
        self.root.overrideredirect(True)
        self.root.attributes("-topmost",True)
        self.root.config(bg=MASK_COLOR)
        self.root.attributes("-transparentcolor",MASK_COLOR)
        sw = self.root.winfo_screenwidth()
        x  = sw - TOTAL_W - X_OFF
        self.root.geometry(f"{TOTAL_W}x{TOTAL_H}+{x}+{Y_OFF}")

    def _create_top_row(self):
        frm = tk.Frame(self.root,bg=MASK_COLOR)
        frm.grid(row=0,column=0,columnspan=6,sticky="nw")
        # SALARY
        self.meter = tk.Canvas(frm,width=METER_W,height=METER_H,
                               bg=MASK_COLOR,highlightthickness=0)
        round_rect(self.meter,0,0,METER_W,METER_H,fill=BG_COLOR,outline=ACCENT,width=4)
        round_rect(self.meter,4,4,METER_W-4,30,fill=ACCENT,outline=ACCENT)
        self.meter.create_text(METER_W/2,18,text="SALARY",
                               fill=LABEL_COLOR,font=self.f_label)
        self.text_id = self.meter.create_text(
            METER_W/2,METER_H/2+10,text="0.00",fill=TEXT_COLOR,font=self.f_salary)
        self.meter.grid(row=0,column=0,sticky="nw")
        # COOKIE
        self.cookie = tk.Canvas(frm,width=COOKIE_SIZE,height=COOKIE_SIZE,
                                bg=ACCENT,highlightthickness=0)
        self.cookie.create_rectangle(0,0,COOKIE_SIZE,COOKIE_SIZE,
                                     fill=ACCENT,outline=ACCENT)
        self.cookie_text = self.cookie.create_text(
            COOKIE_SIZE/2,COOKIE_SIZE/2,
            text=f"🍪 {self.click_count}",fill=BG_COLOR,font=self.f_label)
        self.cookie.bind("<Button-1>",lambda _:self._on_cookie())
        self.cookie.grid(row=0,column=1,padx=5,sticky="n")
        # PYTHAGORE
        calc = tk.Frame(frm,width=CALC_W,height=METER_H,bg=MASK_COLOR)
        tk.Label(calc,text="PYTHAGORE",bg=MASK_COLOR,
                 fg=TEXT_COLOR,font=self.f_label).pack(pady=(8,4))
        self.ea = tk.Entry(calc,width=5,justify="center"); self.ea.pack(pady=2)
        self.eb = tk.Entry(calc,width=5,justify="center"); self.eb.pack(pady=2)
        tk.Button(calc,text="Calc √(a²+b²)",command=self._calc).pack(pady=2)
        self.res= tk.Label(calc,text="?",bg=MASK_COLOR,
                           fg=TEXT_COLOR,font=self.f_label)
        self.res.pack(pady=2)
        calc.grid(row=0,column=2,padx=5,sticky="n")
        # BOUTIQUE
        self.shop_btn = tk.Button(frm,text="🛒",font=self.f_label,
                                  command=self._open_shop)
        self.shop_btn.grid(row=0,column=3,padx=5,sticky="n")
        # INVENTAIRE
        inv = tk.Frame(frm,width=INV_W,bg=MASK_COLOR)
        self.inv_labels={}
        for i,up in enumerate(self.upgrades):
            lbl=tk.Label(inv,text=f"{up['emoji']} x{up['count']}",
                         bg=MASK_COLOR,fg=TEXT_COLOR,font=self.f_label)
            lbl.pack(pady=2); self.inv_labels[i]=lbl
        inv.grid(row=0,column=4,padx=5,sticky="n")
        # PARI COURSE DE CHEVAUX
        tk.Button(frm,text="🐎",font=self.f_label,
                  command=self._start_horse_race).grid(
            row=0,column=5,padx=5,sticky="n")

    def _play_audio_bg(self):
        """ Joue en boucle le son de fond (AUDIO_BG_URL). """
        with YoutubeDL({"format":"bestaudio"}) as ydl:
            info = ydl.extract_info(AUDIO_BG_URL, download=False)
        url = info["url"]
        inst = vlc.Instance()
        media = inst.media_new(url)
        self.audio_player = inst.media_player_new()
        self.audio_player.set_media(media)
        self.audio_player.play()
    def _open_shop(self):
        if self.shop_window and self.shop_window.winfo_exists():
            self.shop_window.lift()
            return
        w = tk.Toplevel(self.root); w.title("Boutique d'auto-clics")
        w.config(bg=MASK_COLOR); self.shop_window = w
        for i,up in enumerate(self.upgrades):
            f = tk.Frame(w,bg=MASK_COLOR)
            lbl = tk.Label(f,text=f"{up['emoji']} x{up['count']}",
                           bg=MASK_COLOR,fg=TEXT_COLOR,font=self.f_label)
            btn = tk.Button(f,text=f"Buy {up['emoji']} ({up['cost']}🍪)",
                            command=lambda i=i: self._buy_upgrade(i))
            lbl.pack(side="left",padx=5); btn.pack(side="left",padx=5)
            f.pack(pady=5,padx=10)
        tk.Button(w,text="Fermer",command=w.destroy).pack(pady=5)

    def _buy_upgrade(self,idx):
        if not (self.shop_window and self.shop_window.winfo_exists()):
            return
        up = self.upgrades[idx]
        if self.click_count >= up['cost']:
            self.click_count -= up['cost']
            up['count'] += 1
            for w in self.shop_window.winfo_children():
                if isinstance(w,tk.Frame):
                    lbl = w.winfo_children()[0]
                    if lbl.cget("text").startswith(up['emoji']):
                        lbl.config(text=f"{up['emoji']} x{up['count']}")
            self.inv_labels[idx].config(text=f"{up['emoji']} x{up['count']}")
            self._update_cookie()
        else:
            self.status_lbl.config(text="Pas assez de cookies")

    def _start_upgrades(self):
        for i,up in enumerate(self.upgrades):
            self.root.after(up['interval'],lambda i=i:self._upgrade_tick(i))

    def _upgrade_tick(self,idx):
        up = self.upgrades[idx]
        if up['count']>0:
            self.click_count += up['amount']*up['count']
            self._update_cookie()
        self.root.after(up['interval'],lambda i=idx:self._upgrade_tick(i))

    def _create_video(self):
        vf = tk.Frame(self.root,width=METER_W,height=VIDEO_H,bg=MASK_COLOR)
        vf.grid(row=1,column=0,columnspan=4,sticky="nw")
        self.video_frame = vf

    def _play_video(self):
        with YoutubeDL({"format":"best"}) as ydl:
            info = ydl.extract_info(YT_URL, download=False)
        url    = info["url"]
        inst   = vlc.Instance(['--input-repeat=-1','--no-video-title-show'])
        media  = inst.media_new(url)
        player = inst.media_player_new()
        player.set_media(media)
        player.set_hwnd(self.video_frame.winfo_id())
        player.play()
        # → playback à 100×
        player.set_rate(5.0)
        self.video_player = player

    def _create_horse_race(self):
        fr=tk.Frame(self.root,width=FAIR_W,height=VIDEO_H,bg="#552200")
        fr.grid(row=1,column=4,columnspan=2,sticky="nw",padx=5)
        tk.Label(fr,text="🐎 Course de chevaux",bg="#552200",
                 fg=ACCENT,font=self.f_label).pack(pady=4)

        track_len = FAIR_W - 20
        lane_h    = (VIDEO_H - 100) / HORSE_COUNT

        self.horse_canvas = tk.Canvas(
            fr, width=track_len, height=HORSE_COUNT*lane_h, bg="#228833"
        )
        self.horse_canvas.pack(pady=2)
        self.finish = track_len - HORSE_SIZE
        self.horse_canvas.create_line(
            self.finish, 0, self.finish, HORSE_COUNT*lane_h,
            fill="white", dash=(5,3), width=2
        )

        self.horse_positions = [0]*HORSE_COUNT
        self.horse_rects = []
        colors = ["red","blue","yellow","orange","purple","cyan"]
        for i in range(HORSE_COUNT):
            y = i*lane_h + lane_h/2
            rect = self.horse_canvas.create_rectangle(
                0, y-HORSE_SIZE/2, HORSE_SIZE, y+HORSE_SIZE/2,
                fill=colors[i%len(colors)], outline="black"
            )
            self.horse_rects.append(rect)

        ctrl = tk.Frame(fr,bg="#552200"); ctrl.pack(pady=4)
        cf = tkfont.Font(family="Helvetica", size=10)
        tk.Label(ctrl,text="Misez cheval (1–6):",bg="#552200",
                 fg=TEXT_COLOR,font=cf).pack(side="left")
        self.var_horse_bet = tk.IntVar(value=1)
        tk.Spinbox(ctrl, from_=1, to=HORSE_COUNT, width=3,
                   font=cf, textvariable=self.var_horse_bet
        ).pack(side="left",padx=5)

        tk.Label(ctrl,text="Mise (🍪):",bg="#552200",
                 fg=TEXT_COLOR,font=cf).pack(side="left",padx=(10,0))
        self.horse_bet_entry=tk.Entry(ctrl,width=5,justify="center",font=cf)
        self.horse_bet_entry.pack(side="left",padx=5)
        tk.Button(ctrl,text="Parier et Courir",font=cf,
                  command=self._start_horse_race
        ).pack(side="left",padx=5)

        self.horse_result_lbl = tk.Label(
            fr, text="", bg="#552200", fg=ACCENT, font=self.f_label
        )
        self.horse_result_lbl.pack(pady=4)

    def _start_horse_race(self):
        try:
            stake = int(self.horse_bet_entry.get())
        except ValueError:
            self.horse_result_lbl.config(text="Mise invalide"); return
        if stake <= 0 or stake > self.click_count:
            self.horse_result_lbl.config(text="Pas assez de cookies"); return

        self.click_count -= stake; self._update_cookie()
        self._horse_stake = stake
        for i,rect in enumerate(self.horse_rects):
            self.horse_positions[i] = 0
            y1,y2 = self.horse_canvas.coords(rect)[1], self.horse_canvas.coords(rect)[3]
            self.horse_canvas.coords(rect, 0, y1, HORSE_SIZE, y2)
        self.horse_result_lbl.config(text="")
        self._animate_horses()

    def _animate_horses(self):
        winner = None
        for i,rect in enumerate(self.horse_rects):
            step = random.randint(1,8)
            self.horse_positions[i] += step
            if self.horse_positions[i] >= self.finish:
                winner = i
            y1,y2 = self.horse_canvas.coords(rect)[1], self.horse_canvas.coords(rect)[3]
            self.horse_canvas.coords(
                rect,
                self.horse_positions[i], y1,
                self.horse_positions[i]+HORSE_SIZE, y2
            )
        if winner is None:
            self.root.after(HORSE_DELAY, self._animate_horses)
        else:
            pari  = self.var_horse_bet.get()
            num   = winner + 1
            stake = getattr(self, '_horse_stake', 0)
            if pari == num:
                gain = stake * 2
                self.click_count += gain
                msg = f"Cheval {num} gagne ! +{gain}🍪"
            else:
                msg = f"Cheval {num} gagne. –{stake}🍪"
            self.horse_result_lbl.config(text=msg)
            self._update_cookie()

    def _schedule_special_video(self):
        # lance la vidéo spéciale après l'intervalle
        self.root.after(SPECIAL_VIDEO_INTERVAL_MS, self._show_special_video)

    def _show_special_video(self):
        # cache la vidéo normale
        if hasattr(self, 'video_frame'):
            self.video_frame.grid_remove()

        # overlay plein écran
        self.special_frame = tk.Frame(self.root,
                                      width=TOTAL_W, height=TOTAL_H, bg="black")
        self.special_frame.place(x=0, y=0)
        vf = tk.Frame(self.special_frame,
                      width=TOTAL_W, height=TOTAL_H, bg=MASK_COLOR)
        vf.pack(expand=True, fill="both")

        # lance la vidéo spéciale
        inst = vlc.Instance(['--no-video-title-show'])
        with YoutubeDL({"format":"best"}) as ydl:
            info = ydl.extract_info(SPECIAL_VIDEO_URL, download=False)
        media = inst.media_new(info["url"])
        self.special_player = inst.media_player_new()
        self.special_player.set_media(media)
        self.special_player.set_hwnd(vf.winfo_id())
        self.special_player.play()

        # début du polling pour détecter la fin
        self._check_special_end()

    def _check_special_end(self):
        state = self.special_player.get_state()
        if state == vlc.State.Ended:
            self._hide_special_video()
        else:
            self.root.after(500, self._check_special_end)

    def _hide_special_video(self):
        # arrête et détruit l'overlay spéciale
        if hasattr(self, 'special_player'):
            self.special_player.stop()
        if hasattr(self, 'special_frame'):
            self.special_frame.destroy()
        # restore la vidéo normale
        if USE_VIDEO and hasattr(self, 'video_frame'):
            self.video_frame.grid()
        # reprogramme la prochaine diffusion
        self._schedule_special_video()

    def _create_blackjack(self):
        BJ_W  = int(TOTAL_W * BJ_SCALE)
        BJ_H2 = int(BJ_H     * BJ_SCALE)
        bj = tk.Canvas(self.root, width=BJ_W, height=BJ_H2,
                       bg=MASK_COLOR, highlightthickness=0)
        bj.grid(row=2, column=0, columnspan=6, sticky="nw", pady=5)

        if TABLE_IMG:
            img = TABLE_IMG.resize((BJ_W, BJ_H2), Image.LANCZOS)
            self._bj_bg = ImageTk.PhotoImage(img)
            bj.create_image(0, 0, anchor="nw", image=self._bj_bg)

        self.dealer_lbl = tk.Label(self.root, text="Dealer:", bg=TABLE_GREEN,
                                   fg=TEXT_COLOR, font=self.f_label)
        self.player_lbl = tk.Label(self.root, text="Player:", bg=TABLE_GREEN,
                                   fg=TEXT_COLOR, font=self.f_label)
        self.status_lbl = tk.Label(self.root, text="", bg=TABLE_GREEN,
                                   fg=ACCENT, font=self.f_label)
        self.hit_btn    = tk.Button(self.root, text="Hit",
                                    command=self._bj_hit,   state="disabled")
        self.stand_btn  = tk.Button(self.root, text="Stand",
                                    command=self._bj_stand, state="disabled")
        self.new_btn    = tk.Button(self.root, text="New Game",
                                    command=self._bj_new,   state="disabled")
        self.bet_entry  = tk.Entry(self.root, width=5, justify="center")
        self.bet_btn    = tk.Button(self.root, text="Place Bet",
                                    command=self._place_bet)

        pos = {
            "dealer": (0.15*BJ_W,      0.20*BJ_H2),
            "player": (0.25*BJ_W,      0.65*BJ_H2),
            "status": (0.25*BJ_W, 0.65*BJ_H2+25),
            "hit":    (0.60*BJ_W,      0.80*BJ_H2),
            "stand":  (0.70*BJ_W,      0.80*BJ_H2),
            "new":    (0.80*BJ_W,      0.80*BJ_H2),
            "bet_e":  (0.85*BJ_W,      0.50*BJ_H2),
            "bet_b":  (0.85*BJ_W, 0.50*BJ_H2+25),
        }
        for key, widget in {
            "dealer": self.dealer_lbl, "player": self.player_lbl,
            "status": self.status_lbl, "hit": self.hit_btn,
            "stand": self.stand_btn,  "new": self.new_btn,
            "bet_e": self.bet_entry,  "bet_b": self.bet_btn
        }.items():
            bj.create_window(*pos[key], window=widget, anchor="center")
        self._bj_new()

    def _bj_new(self):
        self.bet_entry.config(state="normal"); self.bet_entry.delete(0, tk.END)
        self.bet_btn.config(state="normal")
        self.hit_btn.config(state="disabled"); self.stand_btn.config(state="disabled")
        self.new_btn.config(state="disabled"); self.status_lbl.config(text="")
        self.dealer_lbl.config(text="Dealer:"); self.player_lbl.config(text="Player:")

    def _place_bet(self):
        try:
            amt = int(self.bet_entry.get())
            if amt > 0:
                self.current_bet = amt
                self.click_count -= amt
                self._update_cookie()
                self.bet_entry.config(state="disabled")
                self.bet_btn.config(state="disabled")
                self._deal_hand()
            else:
                self.status_lbl.config(text="Mise doit être > 0")
        except ValueError:
            self.status_lbl.config(text="Mise invalide")

    def _deal_hand(self):
        vals  = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        suits = ['♠','♥','♦','♣']
        deck  = [v+s for v in vals for s in suits]; random.shuffle(deck)
        self.bj_player = [deck.pop(), deck.pop()]
        self.bj_dealer = [deck.pop(), deck.pop()]
        self.bj_deck   = deck
        self._bj_update_labels()
        self.hit_btn.config(state="normal"); self.stand_btn.config(state="normal")

    def _bj_update_labels(self):
        def score(hand):
            tot, aces = 0,0
            for c in hand:
                v = c[:-1]
                if v=='A': tot+=11; aces+=1
                elif v in('K','Q','J'): tot+=10
                else: tot+=int(v)
            while tot>21 and aces: tot-=10; aces-=1
            return tot
        ds, ps = score(self.bj_dealer), score(self.bj_player)
        self.dealer_lbl.config(text=f"Dealer: {' '.join(self.bj_dealer)} ({ds})")
        self.player_lbl.config(text=f"Player: {' '.join(self.bj_player)} ({ps})")

    def _bj_hit(self):
        self.bj_player.append(self.bj_deck.pop()); self._bj_update_labels()
        if self._bj_score(self.bj_player)>21: self._end_round("Busted!")

    def _bj_stand(self):
        while self._bj_score(self.bj_dealer)<17:
            self.bj_dealer.append(self.bj_deck.pop())
        self._bj_update_labels()
        ps, ds = self._bj_score(self.bj_player), self._bj_score(self.bj_dealer)
        if ds>21 or ps>ds:    res="You win!"
        elif ps==ds:          res="Push!"
        else:                 res="Dealer wins!"
        self._end_round(res)

    def _end_round(self, result):
        if result=="You win!": self.click_count += 2*self.current_bet
        elif result=="Push!":  self.click_count += self.current_bet
        self._update_cookie()
        self.status_lbl.config(text=result)
        self.hit_btn.config(state="disabled"); self.stand_btn.config(state="disabled")
        self.new_btn.config(state="normal"); self.current_bet=0

    def _bj_score(self, hand):
        tot, aces = 0,0
        for c in hand:
            v = c[:-1]
            if v=='A': tot+=11; aces+=1
            elif v in('K','Q','J'): tot+=10
            else: tot+=int(v)
        while tot>21 and aces: tot-=10; aces-=1
        return tot

    # -- drag, salary, encouragement, cookie, calc --
    def _bind_drag(self):
        self.meter.bind("<ButtonPress-1>", self._press)
        self.meter.bind("<B1-Motion>",     self._drag)
        self.cookie.bind("<ButtonPress-3>", self._press)
        self.cookie.bind("<B3-Motion>",     self._drag)

    def _press(self, e):
        self._dx, self._dy = e.x_root, e.y_root

    def _drag(self, e):
        dx = e.x_root - self._dx; dy = e.y_root - self._dy
        x  = self.root.winfo_x() + dx; y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        self._dx, self._dy = e.x_root, e.y_root

    def _update_salary(self):
        elapsed = time.time() - self.start
        amt     = (SALARY_PER_HOUR/3600.0) * elapsed
        self.meter.itemconfigure(self.text_id, text=f"{amt:,.2f}")
        self.root.after(UPDATE_MS, self._update_salary)

    def _schedule_enc(self):
        msg = random.choice(MESSAGES)
        if hasattr(self, "enc_id"):
            self.meter.delete(self.enc_id)
        self.enc_id = self.meter.create_text(
            METER_W/2, METER_H-15,
            text=msg, fill=ACCENT, font=self.f_label
        )
        self.root.after(5000, lambda: self.meter.delete(self.enc_id))
        self.root.after(ENCOURAGE_MS, self._schedule_enc)

    def _on_cookie(self):
        self.click_count += 1
        self._update_cookie()

    def _update_cookie(self):
        self.cookie.itemconfigure(self.cookie_text, text=f"🍪 {self.click_count}")
        if USE_VIDEO and hasattr(self, "video_frame"):
            if self.click_count < -100:
                self.video_frame.grid_remove()
            else:
                self.video_frame.grid()

    def _calc(self):
        try:
            a = float(self.ea.get()); b = float(self.eb.get())
            r = (a*a + b*b)**0.5
            self.res.config(text=f"{r:.2f}")
        except ValueError:
            self.res.config(text="?")

if __name__=="__main__":
    TaxiOverlay()

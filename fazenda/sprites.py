"""Sprites desenhados por código: construções, lojas, personagens, animais e ícones de itens."""
import math
import random

import pygame

from . import assets
from . import data as data_mod
from .config import TILE as T
from .gfx import PAL, rnd, shade, shadow

WOOD = (160, 118, 70)


def _snow(screen, pts, season):
    if season == "inverno":
        pygame.draw.polygon(screen, (250, 252, 255), pts)


def roof(screen, px, py, w, rh, col, season):
    """Telhado em trapézio com telhas, beirada escura e neve no inverno."""
    pts = [(px - 4, py + rh), (px + w // 7, py + 2), (px + w - w // 7, py + 2), (px + w + 4, py + rh)]
    pygame.draw.polygon(screen, col, pts)
    for i in range(1, 5):
        y = py + 2 + i * (rh - 2) // 5
        pygame.draw.line(screen, shade(col, .8), (px + w // 7 - i * 3, y), (px + w - w // 7 + i * 3, y), 2)
    pygame.draw.rect(screen, shade(col, .6), (px - 4, py + rh - 5, w + 8, 6), border_radius=2)
    _snow(screen, [(px + w // 7, py + 2), (px + w - w // 7, py + 2), (px + w - w // 7 + 6, py + 10), (px + w // 7 - 6, py + 10)], season)


def window(screen, x, y, w=16, h=14):
    pygame.draw.rect(screen, (170, 214, 240), (x, y, w, h))
    pygame.draw.rect(screen, (96, 66, 44), (x, y, w, h), 2)
    pygame.draw.line(screen, (96, 66, 44), (x + w // 2, y), (x + w // 2, y + h), 1)
    pygame.draw.line(screen, (96, 66, 44), (x, y + h // 2), (x + w, y + h // 2), 1)


def rail(screen, x0, y0, x1, y1):
    """Cerca simples entre dois pontos (horizontal ou vertical)."""
    if y0 == y1:
        for yy in (y0 - 9, y0 - 19):
            pygame.draw.line(screen, WOOD, (x0, yy), (x1, yy), 4)
        for x in range(x0, x1 + 1, T):
            pygame.draw.rect(screen, (120, 84, 48), (x - 3, y0 - 26, 6, 28))
    else:
        for xx in (x0 - 3, x0 + 3):
            pygame.draw.line(screen, WOOD, (xx, y0 - 14), (xx, y1 - 14), 3)
        for y in range(y0, y1 + 1, T):
            pygame.draw.rect(screen, (120, 84, 48), (x0 - 3, y - 26, 6, 28))


def yard(screen, px, py, w, h, season):
    col = (150, 140, 96) if season != "inverno" else (200, 205, 205)
    pygame.draw.rect(screen, col, (px, py, w, h))
    for i in range(int(w * h / 150)):
        x, y = px + int(rnd(i, w, 1) * (w - 8)) + 2, py + int(rnd(i, h, 2) * (h - 4)) + 2
        pygame.draw.line(screen, (206, 180, 108), (x, y), (x + 6, y - 1), 2)
    rail(screen, px, py + h, px + w, py + h)
    rail(screen, px, py, px, py + h)
    rail(screen, px + w, py, px + w, py + h)


def draw_house(screen, px, py, w, h, season, t=0.0):
    """Casa com varanda, toldo, janelas com persianas, floreiras, chaminé com fumaça e lanterna."""
    OUT = (46, 32, 24)
    rh = int(h * .5)
    shadow(screen, px + w // 2, py + h - 2, w - 6, 14)
    # chaminé (atrás do telhado) e fumaça
    pygame.draw.rect(screen, OUT, (px + w - 47, py - 4, 22, 34))
    pygame.draw.rect(screen, (150, 120, 112), (px + w - 45, py - 2, 18, 30))
    for k in range(0, 30, 8):
        pygame.draw.line(screen, (120, 96, 90), (px + w - 45, py + k), (px + w - 27, py + k), 1)
    pygame.draw.rect(screen, (110, 90, 90), (px + w - 49, py - 6, 26, 6))
    for k in range(3):
        ph = (t * 0.5 + k / 3.0) % 1.0
        pygame.draw.circle(screen, (225, 225, 232), (int(px + w - 36 + math.sin(t + k) * 5 + ph * 8), int(py - 10 - ph * 34)), int(3 + ph * 5))
    # paredes de tábua com contorno e rodapé de pedra
    pygame.draw.rect(screen, OUT, (px + 4, py + rh - 8, w - 8, h - rh + 8), border_radius=2)
    pygame.draw.rect(screen, (238, 222, 188), (px + 6, py + rh - 6, w - 12, h - rh + 6))
    for x in range(px + 16, px + w - 10, 16):
        pygame.draw.line(screen, (214, 196, 160), (x, py + rh), (x, py + h - 6), 1)
    pygame.draw.rect(screen, (150, 148, 156), (px + 6, py + h - 8, w - 12, 8))
    for x in range(px + 8, px + w - 14, 14):
        pygame.draw.line(screen, (118, 116, 124), (x, py + h - 8), (x, py + h - 1), 1)
    # janelas com persiana e floreira
    for wx in (px + 16, px + w - 44):
        pygame.draw.rect(screen, (170, 60, 56), (wx - 7, py + rh + 6, 8, 26))
        pygame.draw.rect(screen, (170, 60, 56), (wx + 27, py + rh + 6, 8, 26))
        window(screen, wx, py + rh + 8)
        pygame.draw.rect(screen, (112, 76, 46), (wx - 4, py + rh + 32, 36, 8), border_radius=2)
        for fx, col in ((2, (240, 100, 140)), (10, (250, 220, 80)), (18, (240, 100, 140)), (26, (255, 255, 255))):
            pygame.draw.circle(screen, (70, 150, 60), (wx + fx, py + rh + 31), 3)
            pygame.draw.circle(screen, col, (wx + fx, py + rh + 29), 2)
    # porta com toldo, degraus e lanterna
    dx = px + w // 2 - 12
    pygame.draw.rect(screen, OUT, (dx - 2, py + h - 42, 28, 38), border_radius=4)
    pygame.draw.rect(screen, (112, 70, 40), (dx, py + h - 40, 24, 36), border_radius=3)
    pygame.draw.rect(screen, (140, 92, 54), (dx + 3, py + h - 37, 8, 14))
    pygame.draw.rect(screen, (140, 92, 54), (dx + 13, py + h - 37, 8, 14))
    pygame.draw.circle(screen, (240, 200, 80), (dx + 19, py + h - 20), 2)
    pygame.draw.polygon(screen, (200, 70, 70), [(dx - 10, py + h - 40), (dx + 34, py + h - 40), (dx + 30, py + h - 50), (dx - 6, py + h - 50)])
    for k in range(0, 40, 10):
        pygame.draw.rect(screen, (250, 244, 232), (dx - 8 + k, py + h - 49, 5, 9))
    pygame.draw.rect(screen, (190, 170, 130), (dx - 8, py + h - 4, 40, 4))
    pygame.draw.rect(screen, (170, 150, 112), (dx - 12, py + h - 1, 48, 3))
    lx = dx + 40
    pygame.draw.line(screen, (60, 60, 64), (lx, py + h - 44), (lx, py + h - 38), 2)
    glow = 200 + int(math.sin(t * 5) * 30)
    pygame.draw.rect(screen, (255, glow, 110), (lx - 3, py + h - 38, 7, 9), border_radius=2)
    pygame.draw.rect(screen, (60, 60, 64), (lx - 4, py + h - 40, 9, 2))
    roof(screen, px + 2, py + 8, w - 4, rh, (66, 112, 196), season)


def draw_coop(screen, px, py, w, h, season):
    bh = 64
    yard(screen, px, py + bh, w, h - bh, season)
    pygame.draw.rect(screen, (196, 120, 76), (px + 8, py + 24, w - 16, bh - 24))
    for x in range(px + 14, px + w - 8, 10):
        pygame.draw.line(screen, (170, 98, 60), (x, py + 24), (x, py + bh), 1)
    pygame.draw.rect(screen, (96, 60, 36), (px + w // 2 - 9, py + bh - 26, 18, 26), border_radius=8)
    pygame.draw.rect(screen, (170, 130, 80), (px + w // 2 - 12, py + bh, 24, 6))
    window(screen, px + 18, py + 34, 14, 12)
    window(screen, px + w - 32, py + 34, 14, 12)
    roof(screen, px + 2, py + 4, w - 4, 26, (150, 76, 56), season)


def draw_barn(screen, px, py, w, h, season):
    bh = 96
    yard(screen, px, py + bh, w, h - bh, season)
    pygame.draw.rect(screen, (184, 52, 44), (px + 8, py + 34, w - 16, bh - 34))
    for x in range(px + 14, px + w - 8, 12):
        pygame.draw.line(screen, (150, 40, 36), (x, py + 34), (x, py + bh), 1)
    dw = 56
    d = pygame.Rect(px + w // 2 - dw // 2, py + bh - 50, dw, 50)
    pygame.draw.rect(screen, (240, 232, 220), d)
    pygame.draw.rect(screen, (150, 40, 36), d, 3)
    pygame.draw.line(screen, (150, 40, 36), d.topleft, d.bottomright, 3)
    pygame.draw.line(screen, (150, 40, 36), d.topright, d.bottomleft, 3)
    pygame.draw.line(screen, (150, 40, 36), (d.centerx, d.top), (d.centerx, d.bottom), 3)
    pygame.draw.rect(screen, (240, 232, 220), (px + w // 2 - 12, py + 44, 24, 16), border_radius=3)
    pygame.draw.line(screen, (222, 192, 90), (px + w // 2 - 8, py + 52), (px + w // 2 + 8, py + 52), 3)
    roof(screen, px + 2, py + 6, w - 4, 34, (110, 80, 76), season)


def draw_shed(screen, px, py, w, h, season):
    """Quartinho de bagunça: casinha de madeira com porta dupla, caixotes e cadeado."""
    OUT = (46, 32, 24)
    rh = 30
    shadow(screen, px + w // 2, py + h - 2, w - 8, 12)
    spr = assets.load("sprites/world/quartinho.png", (w, h))
    if spr is not None:                                               # pixel art (assets/sprites/world)
        screen.blit(spr, (px, py))
        return
    pygame.draw.rect(screen, OUT, (px + 6, py + rh - 2, w - 12, h - rh + 2), border_radius=2)
    pygame.draw.rect(screen, (172, 124, 84), (px + 8, py + rh, w - 16, h - rh))
    for x in range(px + 14, px + w - 8, 10):
        pygame.draw.line(screen, (140, 98, 62), (x, py + rh), (x, py + h), 1)
    dw = 34
    d = pygame.Rect(px + w // 2 - dw // 2, py + h - 44, dw, 44)
    pygame.draw.rect(screen, OUT, d.inflate(4, 2), border_radius=3)
    pygame.draw.rect(screen, (112, 76, 46), d)
    pygame.draw.line(screen, OUT, (d.centerx, d.top), (d.centerx, d.bottom), 2)
    pygame.draw.line(screen, (80, 80, 90), (d.x, d.y + 10), (d.right, d.y + 10), 3)
    pygame.draw.line(screen, (80, 80, 90), (d.x, d.bottom - 10), (d.right, d.bottom - 10), 3)
    pygame.draw.rect(screen, (240, 200, 80), (d.centerx - 4, d.centery - 2, 8, 8), border_radius=2)
    pygame.draw.arc(screen, (240, 200, 80), (d.centerx - 3, d.centery - 7, 6, 8), 0, 3.14, 2)
    for bx, by in ((px + 12, py + h - 18), (px + w - 30, py + h - 24)):          # caixotes
        pygame.draw.rect(screen, OUT, (bx - 1, by - 1, 20, 20))
        pygame.draw.rect(screen, (196, 150, 92), (bx, by, 18, 18))
        pygame.draw.line(screen, (140, 100, 60), (bx, by), (bx + 17, by + 17), 2)
        pygame.draw.line(screen, (140, 100, 60), (bx + 17, by), (bx, by + 17), 2)
    roof(screen, px + 2, py + 6, w - 4, rh, (120, 86, 66), season)


def draw_hutch(screen, px, py, w, h, season):
    bh = 44
    yard(screen, px, py + bh, w, h - bh, season)
    pygame.draw.rect(screen, (176, 136, 96), (px + 14, py + 14, w - 28, bh - 14))
    pygame.draw.rect(screen, (200, 190, 170), (px + 22, py + 22, w - 44, bh - 24))
    for x in range(px + 22, px + w - 22, 6):
        pygame.draw.line(screen, (130, 130, 130), (x, py + 22), (x, py + bh - 2), 1)
    pygame.draw.rect(screen, (96, 60, 36), (px + w // 2 - 6, py + bh - 14, 12, 14), border_radius=6)
    roof(screen, px + 8, py + 2, w - 16, 16, (120, 90, 70), season)


def draw_fence(screen, px, py, conn, aberto=None):
    cx = px + T // 2
    l, r, u, d = conn
    for yy in (py + 14, py + 22):
        if r:
            pygame.draw.line(screen, WOOD, (cx, yy), (px + T, yy), 4)
        if l:
            pygame.draw.line(screen, WOOD, (px, yy), (cx, yy), 4)
    if u:
        pygame.draw.line(screen, WOOD, (cx - 3, py), (cx - 3, py + 18), 3)
        pygame.draw.line(screen, WOOD, (cx + 3, py), (cx + 3, py + 18), 3)
    if d:
        pygame.draw.line(screen, WOOD, (cx - 3, py + 18), (cx - 3, py + T), 3)
        pygame.draw.line(screen, WOOD, (cx + 3, py + 18), (cx + 3, py + T), 3)
    if aberto is None:
        pygame.draw.rect(screen, (120, 84, 48), (cx - 3, py + 6, 6, 24))
        pygame.draw.rect(screen, (170, 128, 80), (cx - 3, py + 6, 6, 3))
    else:                                                   # portão
        pygame.draw.rect(screen, (90, 60, 36), (px + 1, py + 4, 6, 28))
        pygame.draw.rect(screen, (90, 60, 36), (px + T - 7, py + 4, 6, 28))
        pygame.draw.rect(screen, (60, 40, 24), (px + 1, py + 4, 6, 3))
        pygame.draw.rect(screen, (60, 40, 24), (px + T - 7, py + 4, 6, 3))
        if aberto:
            # as duas folhas abertas para os lados (como vistas de cima), passagem livre no meio
            pygame.draw.line(screen, (190, 146, 92), (px + 7, py + 12), (px + 7, py + 3), 4)
            pygame.draw.line(screen, (190, 146, 92), (px + T - 8, py + 12), (px + T - 8, py + 3), 4)
            pygame.draw.line(screen, (190, 146, 92), (px + 7, py + 20), (px + 7, py + 29), 4)
            pygame.draw.line(screen, (190, 146, 92), (px + T - 8, py + 20), (px + T - 8, py + 29), 4)
            pygame.draw.rect(screen, (92, 160, 78), (px + 11, py + 24, 10, 3))
        else:
            for yy in (py + 9, py + 19):
                pygame.draw.rect(screen, (190, 146, 92), (px + 6, yy, T - 12, 6))
                pygame.draw.rect(screen, (120, 84, 48), (px + 6, yy + 5, T - 12, 1))
            pygame.draw.line(screen, (120, 84, 48), (px + 7, py + 25), (px + T - 8, py + 9), 2)
            pygame.draw.circle(screen, (240, 200, 80), (px + T // 2, py + 17), 2)


def draw_path(screen, px, py, kind, season):
    if kind == "caminho_terra":
        pygame.draw.rect(screen, (176, 138, 96), (px, py, T, T))
        for i in range(5):
            pygame.draw.circle(screen, (150, 116, 80), (px + int(rnd(px, py, i) * 28) + 2, py + int(rnd(px, py, i + 5) * 28) + 2), 2)
    else:
        pygame.draw.rect(screen, (150, 150, 158), (px, py, T, T))
        for i in range(2):
            for j in range(2):
                pygame.draw.rect(screen, (170 + i * 6, 170 + j * 4, 178), (px + i * 16 + 1, py + j * 16 + 1, 14, 14), border_radius=3)
    if season == "inverno":
        pygame.draw.rect(screen, (240, 246, 250), (px, py, T, 8))


def draw_garden(screen, px, py, w, h, seed):
    pygame.draw.rect(screen, (110, 78, 52), (px + 2, py + 2, w - 4, h - 4), border_radius=6)
    pygame.draw.rect(screen, (150, 110, 70), (px + 2, py + 2, w - 4, h - 4), 3, border_radius=6)
    cols = [(240, 130, 170), (250, 220, 90), (190, 150, 255), (255, 255, 255), (250, 150, 80)]
    for i in range(9):
        x, y = px + 10 + int(rnd(seed, i, 1) * (w - 22)), py + 12 + int(rnd(seed, i, 2) * (h - 22))
        pygame.draw.line(screen, (70, 140, 60), (x, y), (x, y + 8), 2)
        c = cols[int(rnd(seed, i, 3) * 5)]
        for k in range(5):
            a = k * math.tau / 5
            pygame.draw.circle(screen, c, (int(x + math.cos(a) * 3), int(y + math.sin(a) * 3)), 2)
        pygame.draw.circle(screen, (250, 220, 80), (x, y), 1)


def draw_misc(screen, sid, px, py, w, h, t, inst=None):
    cx = px + w // 2
    if sid == "banco":
        pygame.draw.rect(screen, (96, 66, 40), (px + 4, py + h - 10, 4, 10))
        pygame.draw.rect(screen, (96, 66, 40), (px + w - 8, py + h - 10, 4, 10))
        pygame.draw.rect(screen, (160, 116, 70), (px + 2, py + h // 2 - 4, w - 4, 10), border_radius=2)
        if w >= h:
            pygame.draw.rect(screen, (140, 100, 60), (px + 2, py + h // 2 - 12, w - 4, 6), border_radius=2)
    elif sid == "lampada":
        pygame.draw.rect(screen, (60, 60, 64), (cx - 2, py + 8, 4, 24))
        pygame.draw.rect(screen, (50, 50, 54), (cx - 7, py + 28, 14, 4))
        pygame.draw.rect(screen, (255, 226, 130), (cx - 6, py + 2, 12, 12), border_radius=3)
        pygame.draw.rect(screen, (50, 50, 54), (cx - 7, py, 14, 3))
    elif sid == "espantalho":
        base = py + h - 4
        pygame.draw.line(screen, (110, 80, 50), (cx, py + 14), (cx, base), 4)
        pygame.draw.line(screen, (110, 80, 50), (cx - 14, py + 24), (cx + 14, py + 24), 4)
        pygame.draw.rect(screen, (90, 130, 190), (cx - 7, py + 20, 14, 18), border_radius=3)
        pygame.draw.circle(screen, (232, 200, 150), (cx, py + 14), 7)
        pygame.draw.ellipse(screen, (220, 190, 90), (cx - 11, py + 4, 22, 7))
        pygame.draw.rect(screen, (200, 170, 80), (cx - 6, py - 2, 12, 8))
        for dx in (-17, 15):
            pygame.draw.line(screen, (230, 200, 90), (cx + dx, py + 24), (cx + dx + 3, py + 32), 2)
    elif sid == "forno":
        d = (inst or {}).get("data", {})
        est = d.get("estado", "desligado")
        nome = f"forno_fogo_{int(t * 5) % 3}" if est == "funcionando" else "forno_pronto" if est == "pronto" else "forno_off"
        img = assets.load(f"sprites/world/{nome}.png", (w, h))
        if img is not None:
            screen.blit(img, (px, py))
        else:
            pygame.draw.rect(screen, (150, 150, 162), (px + 4, py + h // 3, w - 8, h * 2 // 3 - 4), border_radius=4)
            pygame.draw.rect(screen, (30, 26, 30), (px + w // 3, py + h // 2, w // 3, h // 3))
        if est == "funcionando":
            pygame.draw.circle(screen, (255, 190, 70), (px + w // 2, py + h * 2 // 3), 5 + int(2 * abs(math.sin(t * 8))))
            tot = max(1.0, d.get("restante", 0.0))
            pygame.draw.rect(screen, (30, 20, 14), (px + 8, py - 6, w - 16, 6))
            frac = 1.0
            try:
                from . import forno as _f
                frac = _f.progresso(inst)
            except Exception:
                pass
            pygame.draw.rect(screen, (250, 170, 50), (px + 9, py - 5, int((w - 18) * frac), 4))
        elif est == "pronto":
            pygame.draw.circle(screen, (120, 230, 120), (px + w - 8, py + 6), 5)
    elif sid == "misturador":
        tor = assets.load("sprites/world/moinho_torre.png", (w, h))
        if tor is not None:                                           # moinho de vento: as pás giram
            pas = assets.load(f"sprites/world/moinho_pas_{int(t * 6) % 6}.png", (w, h))
            screen.blit(tor, (px, py))
            if pas is not None:
                screen.blit(pas, (px, py))
            return
        pygame.draw.rect(screen, (110, 80, 52), (px + 6, py + h - 14, 8, 14))
        pygame.draw.rect(screen, (110, 80, 52), (px + w - 14, py + h - 14, 8, 14))
        pygame.draw.rect(screen, (196, 150, 92), (px + 4, py + 24, w - 8, h - 36), border_radius=6)
        pygame.draw.rect(screen, (140, 100, 60), (px + 4, py + 34, w - 8, 4))
        pygame.draw.rect(screen, (140, 100, 60), (px + 4, py + h - 24, w - 8, 4))
        pygame.draw.rect(screen, (230, 210, 150), (px + 10, py + 16, w - 20, 12), border_radius=4)
        pygame.draw.ellipse(screen, (170, 120, 60), (px + 14, py + 14, w - 28, 8))
        pygame.draw.line(screen, (90, 90, 96), (px + w - 10, py + 40), (px + w + 2, py + 28), 3)
        for dx in (-10, 0, 10):
            pygame.draw.circle(screen, (240, 210, 110), (cx + dx, py + 18), 3)
    elif sid == "barraca":
        OUT = (46, 32, 24)
        shadow(screen, cx, py + h - 3, w - 6, 10, 55)
        for dx in (6, w - 12):                                                     # postes do toldo
            pygame.draw.rect(screen, OUT, (px + dx - 1, py + 8, 8, h - 12))
            pygame.draw.rect(screen, (150, 106, 64), (px + dx, py + 9, 6, h - 14))
        pygame.draw.rect(screen, OUT, (px + 2, py + h - 38, w - 4, 34), border_radius=3)             # balcão
        pygame.draw.rect(screen, (176, 128, 80), (px + 4, py + h - 36, w - 8, 30), border_radius=3)
        pygame.draw.rect(screen, (214, 170, 110), (px + 4, py + h - 40, w - 8, 8), border_radius=3)
        for k in range(1, 6):
            pygame.draw.line(screen, (140, 98, 60), (px + 4 + k * (w - 8) // 6, py + h - 30), (px + 4 + k * (w - 8) // 6, py + h - 8), 1)
        if inst:
            for i, sl in enumerate(inst["data"].get("loja", [])[:6]):
                if sl:
                    draw_icon(screen, data_mod.ITEMS[sl["i"]], (px + 6 + i * ((w - 12) // 6), py + h - 36, 26, 26))
        n = 7
        sw_ = (w + 8) / n
        pygame.draw.rect(screen, OUT, (px - 5, py - 1, w + 10, 14))
        for i in range(n):
            col = (214, 70, 70) if i % 2 == 0 else (250, 246, 238)
            x0 = int(px - 4 + i * sw_)
            pygame.draw.rect(screen, col, (x0, py, int(sw_) + 1, 10))
            pygame.draw.circle(screen, OUT, (int(x0 + sw_ / 2), py + 11), int(sw_ / 2) + 1)
        for i in range(n):
            col = (214, 70, 70) if i % 2 == 0 else (250, 246, 238)
            x0 = int(px - 4 + i * sw_)
            pygame.draw.circle(screen, col, (int(x0 + sw_ / 2), py + 11), int(sw_ / 2) - 1)
    elif sid in ("macieira", "laranjeira", "pessegueiro", "arvore_jovem"):
        OUT = (46, 32, 24)
        sd = data_mod.STRUCTS[sid]
        idade = inst["data"].get("idade", 0) if inst else sd["dias_adulta"]
        fruto = inst["data"].get("fruto", 0) if inst else 0
        st = 2 if idade >= sd["dias_adulta"] else 1 if idade >= sd["dias_adulta"] // 2 else 0
        fcol = tuple(sd["cor"])
        base_y = py + h - 4
        shadow(screen, cx, base_y, 14 + st * 16, 6 + st * 3, 55)
        sway = math.sin(t * 1.4 + px) * (1 + st)
        spr = assets.load("sprites/trees/muda.png", (80, 80)) if st == 0 else assets.load(f"sprites/trees/fruit_{sid}_{st}.png", (80, 80))
        if sid == "arvore_jovem" and st:
            spr = assets.load("sprites/trees/fruit_macieira_%d.png" % st, (80, 80))
        if spr is not None:
            screen.blit(spr, (int(cx - 40 + sway * .5), base_y - 78))
            rr = 12 + st * 8
            cy2 = base_y - (20 + st * 14) - rr + 6
            if st == 2 and sid == "pessegueiro" and fruto == 0:
                for k in range(4):
                    pygame.draw.circle(screen, (250, 190, 210), (int(cx - 10 + k * 7 + sway), int(cy2 + (k % 2) * 8)), 2)
            if fruto > 0 and st:
                for k in range(min(6, fruto + 1)):
                    fx = cx + int(math.cos(k * 2.1) * rr * .8) + int(sway)
                    fy = cy2 + int(math.sin(k * 2.1 + 1) * rr * .6) + 4
                    pygame.draw.rect(screen, OUT, (fx - 4, fy - 4, 8, 8))
                    pygame.draw.rect(screen, fcol, (fx - 3, fy - 3, 6, 6))
                    pygame.draw.rect(screen, shade(fcol, 1.5), (fx - 2, fy - 2, 2, 2))
            return
        if st == 0:
            pygame.draw.line(screen, OUT, (cx, base_y), (cx, base_y - 14), 4)
            pygame.draw.line(screen, (120, 84, 50), (cx, base_y), (cx, base_y - 14), 2)
            pygame.draw.ellipse(screen, (70, 150, 60), (cx - 9 + sway, base_y - 22, 10, 7))
            pygame.draw.ellipse(screen, (90, 176, 80), (cx + sway, base_y - 18, 10, 7))
        else:
            th = 20 + st * 14
            pygame.draw.rect(screen, OUT, (cx - 5, base_y - th, 10, th))
            pygame.draw.rect(screen, (130, 92, 56), (cx - 3, base_y - th, 6, th))
            rr = 12 + st * 8
            cy2 = base_y - th - rr + 6
            leaf = (78, 158, 68) if sid != "pessegueiro" else (96, 170, 84)
            for ox, oy, r in ((0, 0, rr), (-rr * .6, rr * .4, rr * .7), (rr * .6, rr * .4, rr * .7)):
                pygame.draw.circle(screen, OUT, (int(cx + ox + sway), int(cy2 + oy)), int(r) + 1)
            for ox, oy, r in ((0, 0, rr), (-rr * .6, rr * .4, rr * .7), (rr * .6, rr * .4, rr * .7)):
                pygame.draw.circle(screen, leaf, (int(cx + ox + sway), int(cy2 + oy)), int(r))
            pygame.draw.circle(screen, (110, 190, 96), (int(cx - rr * .3 + sway), int(cy2 - rr * .3)), max(3, rr // 3))
            if st == 2 and sid == "pessegueiro" and fruto == 0:
                for k in range(4):
                    pygame.draw.circle(screen, (250, 190, 210), (int(cx - 10 + k * 7 + sway), int(cy2 + (k % 2) * 8)), 2)
            if fruto > 0:
                for k in range(min(6, fruto + 1)):
                    fx = cx + int(math.cos(k * 2.1) * rr * .8) + int(sway)
                    fy = cy2 + int(math.sin(k * 2.1 + 1) * rr * .6) + 4
                    pygame.draw.circle(screen, OUT, (fx, fy), 4)
                    pygame.draw.circle(screen, fcol, (fx, fy), 3)
    elif sid == "tanque":
        OUT = (46, 32, 24)
        pygame.draw.rect(screen, OUT, (px + 2, py + 14, w - 4, h - 14), border_radius=8)
        pygame.draw.rect(screen, (150, 106, 64), (px + 4, py + 16, w - 8, h - 18), border_radius=7)
        pygame.draw.rect(screen, (66, 140, 200), (px + 12, py + 24, w - 24, h - 34), border_radius=5)
        pygame.draw.rect(screen, (96, 170, 224), (px + 12, py + 24, w - 24, 8), border_radius=5)
        for k in range(3):
            ph = (t * 0.5 + k * 0.33) % 1.0
            pygame.draw.ellipse(screen, (180, 220, 250), (px + 22 + k * 22 - ph * 6, py + 40 + k * 8, 12 + ph * 12, 5 + ph * 3), 1)
        for k, (fx, fy, fl) in enumerate(((0.3, 0.55, False), (0.65, 0.7, True), (0.5, 0.4, False))):
            draw_fish(screen, int(px + w * fx + math.sin(t + k) * 6), int(py + h * fy), 7, (250, 160, 70), fl)
        for dx in (6, w - 10):
            pygame.draw.rect(screen, (96, 66, 40), (px + dx, py + 6, 5, 16))
    elif sid == "torneira":
        pygame.draw.rect(screen, (110, 80, 52), (cx - 12, py + h - 6, 24, 6), border_radius=2)       # base de pedra
        pygame.draw.rect(screen, (150, 148, 156), (cx - 12, py + h - 10, 24, 6), border_radius=2)
        pygame.draw.rect(screen, (96, 100, 112), (cx - 3, py + 8, 6, h - 16))                      # cano
        pygame.draw.rect(screen, (96, 100, 112), (cx - 3, py + 8, 14, 5))
        pygame.draw.rect(screen, (96, 100, 112), (cx + 8, py + 8, 5, 9))
        pygame.draw.circle(screen, (200, 60, 60), (cx, py + 6), 5)                                  # registro
        pygame.draw.circle(screen, (70, 140, 210), (cx + 10, py + 22 + int(t * 6) % 4), 2)         # gota
        pygame.draw.ellipse(screen, (70, 140, 210), (cx + 3, py + h - 6, 14, 4))
    elif sid == "vaso":
        pygame.draw.polygon(screen, (200, 110, 80), [(cx - 9, py + 16), (cx + 9, py + 16), (cx + 6, py + 30), (cx - 6, py + 30)])
        pygame.draw.rect(screen, (170, 86, 60), (cx - 10, py + 14, 20, 4))
        pygame.draw.circle(screen, (70, 150, 60), (cx, py + 10), 7)
        for dx, dy in ((-3, 7), (3, 8), (0, 12)):
            pygame.draw.circle(screen, (240, 110, 150), (cx + dx, py + dy - 1), 3)
    elif sid in ("aspersor", "aspersor_forte"):
        big = sid == "aspersor_forte"
        col = (80, 140, 220) if big else (120, 170, 220)
        pygame.draw.circle(screen, (90, 90, 96), (cx, py + 24), 9 if big else 7)
        pygame.draw.rect(screen, col, (cx - 3, py + 10, 6, 16))
        pygame.draw.circle(screen, (210, 230, 250), (cx, py + 9), 5 if big else 4)
        pygame.draw.circle(screen, (210, 230, 250), (cx, py + 9), 9 if big else 7, 1)
        if int(t * 2) % 2 == 0 and big:
            pygame.draw.circle(screen, (210, 230, 250), (cx, py + 9), 13, 1)


def draw_fish(screen, cx, cy, size, col, flip=False):
    """Peixinho de lado (cx, cy = centro)."""
    d = -1 if flip else 1
    L = size
    dark = tuple(max(0, c - 60) for c in col)
    pygame.draw.polygon(screen, dark, [(cx - d * L, cy), (cx - d * (L + L // 2), cy - L // 2), (cx - d * (L + L // 2), cy + L // 2)])
    pygame.draw.ellipse(screen, dark, (cx - L - 1, cy - L // 2 - 1, 2 * L + 2, L + 2))
    pygame.draw.ellipse(screen, col, (cx - L, cy - L // 2, 2 * L, L))
    pygame.draw.ellipse(screen, tuple(min(255, c + 50) for c in col), (cx - L + 3, cy - L // 2 + 2, 2 * L - 8, max(2, L // 3)))
    pygame.draw.circle(screen, (255, 255, 255), (cx + d * (L - 5), cy - 1), max(2, L // 5))
    pygame.draw.circle(screen, (20, 20, 20), (cx + d * (L - 5), cy - 1), max(1, L // 9))


def draw_decor(screen, kind, px, py, w, h, season, t):
    """Decoração da praça da vila."""
    OUT = (46, 32, 24)
    cx = px + w // 2
    if kind == "fonte":
        shadow(screen, cx, py + h - 6, w - 4, 16, 55)
        by = py + h - 8                                                     # chão da fonte
        pygame.draw.ellipse(screen, OUT, (px + 2, by - 50, w - 4, 52))
        pygame.draw.ellipse(screen, (176, 174, 184), (px + 4, by - 48, w - 8, 48))
        pygame.draw.ellipse(screen, (140, 138, 150), (px + 4, by - 30, w - 8, 28))
        pygame.draw.ellipse(screen, (96, 170, 224), (px + 12, by - 42, w - 24, 32))
        for k in range(3):
            ph = (t * 0.7 + k * 0.33) % 1.0
            rw, rh_ = 20 + ph * (w - 50), 8 + ph * 16
            pygame.draw.ellipse(screen, (196, 228, 252), (cx - rw / 2, by - 26 - rh_ / 2, rw, rh_), 1)
        pygame.draw.rect(screen, OUT, (cx - 7, by - 72, 14, 48))                  # coluna e bacia alta
        pygame.draw.rect(screen, (160, 158, 168), (cx - 5, by - 70, 10, 46))
        pygame.draw.ellipse(screen, OUT, (cx - 22, by - 62, 44, 18))
        pygame.draw.ellipse(screen, (176, 174, 184), (cx - 20, by - 61, 40, 15))
        pygame.draw.ellipse(screen, (110, 190, 240), (cx - 16, by - 59, 32, 10))
        pygame.draw.circle(screen, (230, 240, 255), (cx, by - 78), 4)
        for k in range(8):                                                   # jatos em arco
            a_ = k / 8.0
            ph = (t * 1.4 + a_) % 1.0
            for sgn in (-1, 1):
                xx = cx + sgn * ph * 24
                yy = by - 78 + (ph * 2 - 0.0) ** 2 * 16 - ph * 18
                pygame.draw.circle(screen, (206, 232, 255), (int(xx), int(yy)), 2)
    elif kind == "banco":
        shadow(screen, cx, py + h - 3, w - 4, 8, 50)
        for dx in (7, w - 11):
            pygame.draw.rect(screen, OUT, (px + dx - 1, py + h - 14, 7, 14))
            pygame.draw.rect(screen, (60, 60, 68), (px + dx, py + h - 13, 5, 12))
        pygame.draw.rect(screen, OUT, (px + 2, py + h - 26, w - 4, 14), border_radius=3)
        pygame.draw.rect(screen, (176, 128, 80), (px + 3, py + h - 25, w - 6, 12), border_radius=3)
        pygame.draw.line(screen, (130, 92, 56), (px + 6, py + h - 20), (px + w - 6, py + h - 20), 1)
        pygame.draw.rect(screen, OUT, (px + 2, py + h - 40, w - 4, 12), border_radius=3)
        pygame.draw.rect(screen, (196, 148, 96), (px + 3, py + h - 39, w - 6, 10), border_radius=3)
        pygame.draw.rect(screen, (60, 60, 68), (px + 2, py + h - 38, 4, 24))
        pygame.draw.rect(screen, (60, 60, 68), (px + w - 6, py + h - 38, 4, 24))
    elif kind == "canteiro":
        shadow(screen, cx, py + h - 3, w - 4, 8, 45)
        pygame.draw.rect(screen, OUT, (px + 2, py + h - 24, w - 4, 24), border_radius=4)
        pygame.draw.rect(screen, (160, 158, 168), (px + 4, py + h - 22, w - 8, 20), border_radius=3)
        pygame.draw.rect(screen, (96, 66, 44), (px + 7, py + h - 19, w - 14, 10), border_radius=2)
        cols = ((240, 100, 140), (250, 220, 80), (240, 240, 245), (180, 120, 230), (250, 150, 70))
        for i in range(0, w - 18, 7):
            fx = px + 11 + i
            lift = (i // 7 % 2) * 3
            pygame.draw.line(screen, (70, 150, 60), (fx, py + h - 12), (fx, py + h - 26 + lift), 2)
            pygame.draw.circle(screen, cols[(i // 7) % 5], (fx, py + h - 28 + lift), 4)
            pygame.draw.circle(screen, (250, 230, 120), (fx, py + h - 28 + lift), 1)
    elif kind == "quadro":
        shadow(screen, cx, py + h - 3, w - 6, 8, 50)
        for dx in (8, w - 14):
            pygame.draw.rect(screen, OUT, (px + dx - 1, py + h - 40, 8, 40))
            pygame.draw.rect(screen, (120, 84, 50), (px + dx, py + h - 39, 6, 38))
        pygame.draw.rect(screen, OUT, (px + 2, py + h - 62, w - 4, 34), border_radius=3)
        pygame.draw.rect(screen, (196, 150, 98), (px + 4, py + h - 60, w - 8, 30), border_radius=2)
        for i, (c, ox, oy) in enumerate(((250, 246, 230), (250, 236, 170), (230, 245, 250), (250, 246, 230))):
            pygame.draw.rect(screen, (c, c - 6, c - 20), (px + 9 + i * 13, py + h - 56 + (i % 2) * 5, 11, 15))
            pygame.draw.circle(screen, (210, 60, 60), (px + 14 + i * 13, py + h - 55 + (i % 2) * 5), 2)
        pygame.draw.rect(screen, OUT, (px + 2, py + h - 66, w - 4, 6), border_radius=2)
    elif kind == "mina":
        shadow(screen, cx, py + h - 4, w, 16, 60)
        # massa de rocha em volta da boca da mina
        pygame.draw.polygon(screen, OUT, [(px - 6, py + h - 4), (px + 6, py + 24), (px + w // 4, py + 4), (px + w * 3 // 4, py + 4),
                                          (px + w - 6, py + 24), (px + w + 6, py + h - 4)])
        pygame.draw.polygon(screen, (116, 112, 122), [(px - 2, py + h - 6), (px + 9, py + 27), (px + w // 4 + 2, py + 8),
                                                      (px + w * 3 // 4 - 2, py + 8), (px + w - 9, py + 27), (px + w + 2, py + h - 6)])
        for i, (rx, ry, rr) in enumerate(((.12, .38, 14), (.30, .16, 12), (.5, .1, 13), (.7, .17, 12), (.88, .38, 14),
                                          (.2, .62, 12), (.8, .62, 12), (.06, .84, 11), (.94, .84, 11))):
            pygame.draw.circle(screen, (134, 130, 140), (px + int(w * rx), py + int(h * ry)), rr)
            pygame.draw.circle(screen, (156, 152, 162), (px + int(w * rx) - 3, py + int(h * ry) - 3), rr // 2)
        ax, aw = px + w // 2 - 40, 80                                                              # boca da mina
        ay, ah = py + 34, h - 38
        pygame.draw.rect(screen, OUT, (ax - 12, ay - 10, aw + 24, ah + 10), border_radius=20)
        for k in range(7):                                                                          # arco de pedras
            ang = math.pi + k * math.pi / 6
            sx_ = ax + aw // 2 + int(math.cos(ang) * (aw // 2 + 6))
            sy_ = ay + 12 + int(math.sin(ang) * 26)
            pygame.draw.circle(screen, OUT, (sx_, sy_), 9)
            pygame.draw.circle(screen, (170, 166, 176), (sx_, sy_), 7)
        pygame.draw.rect(screen, (14, 10, 16), (ax, ay, aw, ah), border_top_left_radius=24, border_top_right_radius=24)
        pygame.draw.rect(screen, (32, 26, 36), (ax + 8, ay + 14, aw - 16, ah - 14), border_top_left_radius=16, border_top_right_radius=16)
        pygame.draw.rect(screen, (50, 42, 54), (ax + 18, ay + 30, aw - 36, ah - 30), border_top_left_radius=10, border_top_right_radius=10)
        for bx in (ax + 2, ax + aw - 10):                                                           # vigas
            pygame.draw.rect(screen, OUT, (bx - 1, ay + 8, 10, ah - 8))
            pygame.draw.rect(screen, (146, 102, 60), (bx, ay + 9, 8, ah - 9))
            pygame.draw.line(screen, (176, 132, 84), (bx + 2, ay + 10), (bx + 2, ay + ah - 2), 1)
        pygame.draw.rect(screen, OUT, (ax - 2, ay + 2, aw + 4, 12), border_radius=3)
        pygame.draw.rect(screen, (160, 114, 66), (ax - 1, ay + 3, aw + 2, 9), border_radius=3)
        for k in range(1, 4):                                                                       # trilhos saindo da mina
            yy = py + h - 2 - k * 7
            half = 9 + (3 - k) * 3
            pygame.draw.rect(screen, (110, 80, 50), (cx - half - 3, yy, 2 * half + 6, 3))
        for sx_ in (-9, 9):
            pygame.draw.line(screen, (170, 170, 180), (cx + sx_ // 3, ay + ah - 2), (cx + sx_, py + h - 2), 2)
        pygame.draw.rect(screen, OUT, (px + 10, py + h - 30, 30, 20), border_radius=3)             # carrinho de minério
        pygame.draw.rect(screen, (120, 84, 56), (px + 11, py + h - 29, 28, 17), border_radius=3)
        for k in range(4):
            pygame.draw.circle(screen, (36, 34, 40), (px + 16 + k * 6, py + h - 31 - (k % 2) * 2), 4)
        pygame.draw.circle(screen, (252, 212, 70), (px + 22, py + h - 32), 2)
        for wx in (px + 17, px + 33):
            pygame.draw.circle(screen, OUT, (wx, py + h - 9), 5)
            pygame.draw.circle(screen, (150, 150, 160), (wx, py + h - 9), 3)
        pygame.draw.rect(screen, OUT, (cx - 32, py - 4, 64, 20), border_radius=4)                  # placa
        pygame.draw.rect(screen, (196, 150, 98), (cx - 31, py - 3, 62, 18), border_radius=4)
        pygame.draw.line(screen, (150, 150, 160), (cx - 24, py + 12), (cx - 10, py - 1), 3)         # picaretas cruzadas
        pygame.draw.line(screen, (120, 84, 50), (cx - 10, py + 12), (cx - 24, py - 1), 3)
        for k, ch in enumerate("MINA"):
            pygame.draw.rect(screen, (90, 58, 36), (cx + 2 + k * 7, py + 2, 5, 10))
        for lx in (ax - 14, ax + aw + 8):                                                           # lanternas
            glow = 220 + int(math.sin(t * 4 + lx) * 25)
            pygame.draw.line(screen, OUT, (lx + 3, ay + 4), (lx + 3, ay + 16), 2)
            pygame.draw.rect(screen, OUT, (lx - 1, ay + 16, 10, 14), border_radius=3)
            pygame.draw.rect(screen, (255, glow, 120), (lx + 1, ay + 18, 6, 10), border_radius=2)
    elif kind == "poste":
        shadow(screen, cx, py + h - 3, 18, 7, 50)
        pygame.draw.rect(screen, OUT, (cx - 4, py + h - 8, 8, 8))
        pygame.draw.rect(screen, (70, 70, 78), (cx - 3, py + h - 7, 6, 6))
        pygame.draw.rect(screen, OUT, (cx - 3, py + 6, 6, h - 12))
        pygame.draw.rect(screen, (60, 60, 68), (cx - 2, py + 7, 4, h - 14))
        pygame.draw.rect(screen, OUT, (cx - 8, py - 8, 16, 18), border_radius=3)
        glow = 220 + int(math.sin(t * 4 + px) * 25)
        pygame.draw.rect(screen, (255, glow, 130), (cx - 6, py - 6, 12, 14), border_radius=2)
        pygame.draw.line(screen, (60, 60, 68), (cx, py - 6), (cx, py + 8), 1)
        pygame.draw.polygon(screen, (60, 60, 68), [(cx - 9, py - 8), (cx + 9, py - 8), (cx, py - 15)])
    elif kind == "arvore":
        shadow(screen, cx, py + h - 3, 40, 12, 55)
        pygame.draw.rect(screen, OUT, (cx - 11, py + h - 18, 22, 18), border_radius=3)
        pygame.draw.rect(screen, (170, 120, 76), (cx - 10, py + h - 17, 20, 16), border_radius=3)
        pygame.draw.rect(screen, (110, 76, 46), (cx - 3, py + h - 40, 6, 24))
        winter = season == "inverno"
        autumn = season == "outono"
        base = (214, 126, 40) if autumn else (70, 110, 70) if winter else (78, 158, 68)
        for ox, oy, r in ((0, -62, 17), (-12, -52, 13), (12, -52, 13), (0, -48, 15)):
            pygame.draw.circle(screen, OUT, (cx + ox, py + h + oy), r + 1)
        for ox, oy, r in ((0, -62, 17), (-12, -52, 13), (12, -52, 13), (0, -48, 15)):
            pygame.draw.circle(screen, base, (cx + ox, py + h + oy), r)
        pygame.draw.circle(screen, shade(base, 1.2), (cx - 5, py + h - 66), 8)
        if winter:
            pygame.draw.circle(screen, (240, 246, 250), (cx, py + h - 72), 8)


def draw_structure(screen, sid, inst, px, py, w, h, season, t, conn=None):
    """Desenha uma construção com o canto superior esquerdo em (px, py), tamanho w x h pixels."""
    if sid == "casa":
        draw_house(screen, px, py, w, h, season, t)
    elif sid == "quartinho":
        draw_shed(screen, px, py, w, h, season)
    elif sid == "galinheiro":
        draw_coop(screen, px, py, w, h, season)
    elif sid == "celeiro":
        draw_barn(screen, px, py, w, h, season)
    elif sid == "coelheira":
        draw_hutch(screen, px, py, w, h, season)
    elif sid == "cerca":
        shadow(screen, px + T // 2, py + T - 3, 26, 8, 40)
        draw_fence(screen, px, py, conn or (0, 0, 0, 0))
    elif sid == "portao":
        draw_fence(screen, px, py, conn or (0, 0, 0, 0), aberto=bool(inst and inst["data"].get("aberto")))
    elif sid in ("caminho_terra", "caminho_pedra"):
        draw_path(screen, px, py, sid, season)
    elif sid == "jardim":
        draw_garden(screen, px, py, w, h, (inst["id"] if inst else 1))
    else:
        shadow(screen, px + w // 2, py + h - 3, 26, 8, 40)
        draw_misc(screen, sid, px, py, w, h, t, inst)


def _awning(screen, x, y, w, c1, c2):
    """Toldo listrado com borda em ondas."""
    OUT = (46, 32, 24)
    n = max(4, w // 12)
    sw = w / n
    pygame.draw.rect(screen, OUT, (x - 1, y - 1, w + 2, 11))
    for i in range(n):
        pygame.draw.circle(screen, OUT, (int(x + i * sw + sw / 2), y + 9), int(sw / 2) + 1)
    for i in range(n):
        col = c1 if i % 2 == 0 else c2
        x0 = int(x + i * sw)
        pygame.draw.rect(screen, col, (x0, y, int(sw) + 1, 9))
        pygame.draw.circle(screen, col, (int(x0 + sw / 2), y + 9), int(sw / 2) - 1)
    pygame.draw.line(screen, shade(c1, .7), (x, y), (x + w, y), 2)


def _prop(screen, kind, x, y):
    """Objetos de cenário na frente de cada loja; (x, y) = pé do objeto."""
    OUT = (46, 32, 24)
    if kind == "barril":
        pygame.draw.rect(screen, OUT, (x - 9, y - 22, 18, 22), border_radius=6)
        pygame.draw.rect(screen, (150, 104, 62), (x - 8, y - 21, 16, 20), border_radius=5)
        for yy in (y - 16, y - 7):
            pygame.draw.line(screen, (80, 80, 90), (x - 8, yy), (x + 8, yy), 2)
        pygame.draw.line(screen, (180, 134, 86), (x - 3, y - 20), (x - 3, y - 2), 1)
    elif kind == "caixa":
        pygame.draw.rect(screen, OUT, (x - 11, y - 20, 22, 20))
        pygame.draw.rect(screen, (196, 150, 92), (x - 10, y - 19, 20, 18))
        pygame.draw.line(screen, (140, 100, 60), (x - 10, y - 10), (x + 10, y - 10), 2)
        pygame.draw.line(screen, (140, 100, 60), (x, y - 19), (x, y - 1), 2)
    elif kind == "frutas":
        _prop(screen, "caixa", x, y)
        for dx, c in ((-5, (220, 60, 50)), (2, (250, 200, 60)), (7, (120, 190, 80))):
            pygame.draw.circle(screen, c, (x + dx, y - 21), 4)
    elif kind == "saco":
        pygame.draw.ellipse(screen, OUT, (x - 11, y - 22, 22, 24))
        pygame.draw.ellipse(screen, (222, 200, 150), (x - 10, y - 21, 20, 22))
        pygame.draw.rect(screen, (170, 90, 70), (x - 8, y - 20, 16, 4))
        pygame.draw.ellipse(screen, (120, 190, 90), (x - 3, y - 14, 6, 8))
    elif kind == "feno":
        pygame.draw.rect(screen, OUT, (x - 13, y - 20, 26, 20), border_radius=3)
        pygame.draw.rect(screen, (226, 196, 100), (x - 12, y - 19, 24, 18), border_radius=3)
        for yy in (y - 15, y - 8):
            pygame.draw.line(screen, (176, 140, 60), (x - 12, yy), (x + 12, yy), 1)
        pygame.draw.line(screen, (130, 96, 50), (x - 4, y - 19), (x - 4, y - 1), 2)
        pygame.draw.line(screen, (130, 96, 50), (x + 5, y - 19), (x + 5, y - 1), 2)
    elif kind == "toras":
        for i, yy in enumerate((y - 6, y - 6, y - 17)):
            xx = x - 7 + (i % 2) * 14 if i < 2 else x
            pygame.draw.circle(screen, OUT, (xx, yy), 8)
            pygame.draw.circle(screen, (170, 120, 72), (xx, yy), 7)
            pygame.draw.circle(screen, (206, 160, 104), (xx, yy), 4)
            pygame.draw.circle(screen, (150, 104, 60), (xx, yy), 1)
    elif kind == "rede":
        pygame.draw.line(screen, OUT, (x - 9, y - 26), (x - 9, y), 3)
        pygame.draw.line(screen, OUT, (x + 9, y - 26), (x + 9, y), 3)
        pygame.draw.rect(screen, (120, 84, 50), (x - 10, y - 26, 20, 3))
        for k in range(5):
            pygame.draw.line(screen, (220, 214, 190), (x - 8 + k * 4, y - 23), (x - 8 + k * 4, y - 6), 1)
        for k in range(4):
            pygame.draw.line(screen, (220, 214, 190), (x - 8, y - 20 + k * 5), (x + 8, y - 20 + k * 5), 1)
        pygame.draw.circle(screen, (230, 90, 80), (x - 6, y - 5), 2)
        pygame.draw.circle(screen, (230, 90, 80), (x + 6, y - 5), 2)
    elif kind == "peixes":
        _prop(screen, "caixa", x, y)
        draw_fish(screen, x - 3, y - 20, 6, (170, 190, 200))
        draw_fish(screen, x + 3, y - 24, 5, (220, 170, 80), True)
    elif kind == "vaso":
        pygame.draw.polygon(screen, OUT, [(x - 9, y - 18), (x + 9, y - 18), (x + 6, y), (x - 6, y)])
        pygame.draw.polygon(screen, (196, 110, 80), [(x - 8, y - 17), (x + 8, y - 17), (x + 5, y - 1), (x - 5, y - 1)])
        pygame.draw.circle(screen, (70, 150, 60), (x, y - 24), 8)
        for dx, dy, c in ((-4, -26, (240, 100, 140)), (3, -22, (250, 220, 80)), (5, -28, (240, 100, 140))):
            pygame.draw.circle(screen, c, (x + dx, y + dy), 3)
    elif kind == "moedas":
        pygame.draw.rect(screen, OUT, (x - 12, y - 18, 24, 18), border_radius=3)
        pygame.draw.rect(screen, (96, 100, 112), (x - 11, y - 17, 22, 16), border_radius=3)
        pygame.draw.rect(screen, (240, 200, 80), (x - 4, y - 12, 8, 7), border_radius=1)
        for dx in (-7, 0, 7):
            pygame.draw.circle(screen, (250, 214, 90), (x + dx, y - 20), 4)
            pygame.draw.circle(screen, (200, 160, 40), (x + dx, y - 20), 4, 1)


_PROPS = {"sementes": ("saco", "vaso"), "animais": ("feno", "barril"), "mercado": ("frutas", "caixa"),
          "carpintaria": ("toras", "barril"), "banco": ("vaso", "vaso"), "peixaria": ("rede", "peixes")}


def _shop_sign_icon(screen, sid, cx, cy):
    OUT = (46, 32, 24)
    pygame.draw.circle(screen, OUT, (cx, cy), 9)
    pygame.draw.circle(screen, (250, 238, 200), (cx, cy), 8)
    if sid == "sementes":
        pygame.draw.ellipse(screen, (90, 160, 70), (cx - 4, cy - 6, 8, 12))
    elif sid == "animais":
        draw_face(screen, "vaca", cx, cy, 6)
    elif sid == "mercado":
        pygame.draw.circle(screen, (220, 60, 50), (cx, cy + 1), 5)
        pygame.draw.rect(screen, (70, 130, 60), (cx - 1, cy - 6, 2, 4))
    elif sid == "carpintaria":
        pygame.draw.line(screen, (120, 84, 50), (cx - 5, cy + 5), (cx + 4, cy - 5), 3)
        pygame.draw.rect(screen, (150, 150, 160), (cx + 1, cy - 7, 6, 4))
    elif sid == "banco":
        pygame.draw.circle(screen, (240, 200, 70), (cx, cy), 6)
        pygame.draw.rect(screen, (190, 140, 30), (cx - 1, cy - 4, 2, 8))
    elif sid == "peixaria":
        draw_fish(screen, cx, cy, 5, (90, 140, 200))


def draw_home(screen, sh, px, py, w, h, lit=False):
    """Casinha de um lojista: parede, telhado, porta (para baixo) e janela que acende à noite."""
    OUT = (46, 32, 24)
    tel, par = tuple(sh["telhado"]), tuple(sh["parede"])
    shadow(screen, px + w // 2, py + h - 2, w - 4, 10, 60)
    wall = pygame.Rect(px + 6, py + int(h * .42), w - 12, h - int(h * .42) - 4)
    pygame.draw.rect(screen, OUT, wall.inflate(4, 4))
    pygame.draw.rect(screen, par, wall)
    roof = [(px, wall.y + 4), (px + w // 2, py + 2), (px + w, wall.y + 4)]
    pygame.draw.polygon(screen, OUT, [(a, b + (2 if b > py + 4 else -1)) for a, b in roof])
    pygame.draw.polygon(screen, tel, roof)
    pygame.draw.line(screen, shade(tel, 1.25), (px + 6, wall.y), (px + w // 2, py + 6), 2)
    door = pygame.Rect(wall.centerx - 8, wall.bottom - 26, 16, 26)
    pygame.draw.rect(screen, OUT, door.inflate(2, 2))
    pygame.draw.rect(screen, (120, 80, 48), door)
    pygame.draw.circle(screen, (240, 210, 100), (door.right - 4, door.centery), 1)
    win = pygame.Rect(wall.x + 8, wall.y + 12, 14, 12)
    pygame.draw.rect(screen, OUT, win.inflate(2, 2))
    pygame.draw.rect(screen, (255, 226, 130) if lit else (170, 210, 235), win)
    pygame.draw.line(screen, OUT, (win.centerx, win.y), (win.centerx, win.bottom), 1)


def draw_shop_building(screen, sh, px, py, w, h, season, font):
    """Loja com fundação de pedra, vigas, janelas com persianas e floreiras, toldo, placa, lanternas e cenário."""
    OUT = (46, 32, 24)
    sid = sh.get("id", "")
    tel, par = tuple(sh["telhado"]), tuple(sh["parede"])
    rh = int(h * .5)
    shadow(screen, px + w // 2, py + h - 2, w - 4, 14, 70)
    wall = pygame.Rect(px + 6, py + rh - 6, w - 12, h - rh + 6)
    pygame.draw.rect(screen, OUT, wall.inflate(4, 4), border_radius=2)
    pygame.draw.rect(screen, par, wall)
    for x in range(wall.x + 6, wall.right - 4, 10):                         # reboco/tábuas
        pygame.draw.line(screen, shade(par, .93), (x, wall.y + 4), (x, wall.bottom - 8), 1)
    beam = shade(par, .55)
    for x in (wall.x, wall.right - 5):                                       # vigas de canto
        pygame.draw.rect(screen, beam, (x, wall.y, 5, wall.h))
    pygame.draw.rect(screen, beam, (wall.x, wall.y, wall.w, 4))
    pygame.draw.rect(screen, (140, 138, 148), (wall.x, wall.bottom - 9, wall.w, 9))   # fundação de pedra
    for x in range(wall.x + 2, wall.right - 8, 14):
        pygame.draw.line(screen, (104, 102, 112), (x, wall.bottom - 9), (x, wall.bottom - 1), 1)
    pygame.draw.line(screen, (104, 102, 112), (wall.x, wall.bottom - 5), (wall.right, wall.bottom - 5), 1)
    # janelas com persianas e floreira
    for wx in (px + 16, px + w - 40):
        pygame.draw.rect(screen, shade(tel, .85), (wx - 6, py + h - 56, 7, 28))
        pygame.draw.rect(screen, shade(tel, .85), (wx + 23, py + h - 56, 7, 28))
        window(screen, wx, py + h - 56, 23, 26)
        pygame.draw.rect(screen, (112, 76, 46), (wx - 3, py + h - 30, 29, 7), border_radius=2)
        for k, col in enumerate(((240, 100, 140), (250, 220, 80), (240, 240, 245), (240, 100, 140))):
            pygame.draw.circle(screen, (70, 150, 60), (wx + 2 + k * 7, py + h - 30), 3)
            pygame.draw.circle(screen, col, (wx + 2 + k * 7, py + h - 33), 2)
    # porta com degrau e lanternas
    dx = px + w // 2 - 11
    pygame.draw.rect(screen, OUT, (dx - 2, py + h - 46, 26, 40), border_radius=4)
    pygame.draw.rect(screen, (112, 70, 40), (dx, py + h - 44, 22, 38), border_radius=3)
    pygame.draw.rect(screen, (140, 92, 54), (dx + 3, py + h - 40, 7, 14))
    pygame.draw.rect(screen, (140, 92, 54), (dx + 12, py + h - 40, 7, 14))
    pygame.draw.circle(screen, (240, 200, 80), (dx + 18, py + h - 22), 2)
    pygame.draw.rect(screen, (170, 168, 176), (dx - 6, py + h - 6, 34, 6), border_radius=2)
    for lx in (dx - 12, dx + 34):
        pygame.draw.line(screen, (60, 60, 64), (lx, py + h - 52), (lx, py + h - 46), 2)
        pygame.draw.rect(screen, (255, 214, 120), (lx - 3, py + h - 46, 7, 9), border_radius=2)
        pygame.draw.rect(screen, (60, 60, 64), (lx - 4, py + h - 48, 9, 2))
    # chaminé atrás do telhado
    cxm = px + w - 34
    pygame.draw.rect(screen, OUT, (cxm - 1, py - 2, 18, 22))
    pygame.draw.rect(screen, (150, 120, 112), (cxm, py - 1, 16, 20))
    roof(screen, px + 2, py + 6, w - 4, rh, tel, season)
    # toldo + placa com o nome
    _awning(screen, px + 12, py + rh + 6, w - 24, tel, (250, 250, 245))
    label = font.render(sh["nome"], True, (255, 255, 255))
    board = label.get_rect(center=(px + w // 2, py + rh // 2 + 6)).inflate(14, 6)
    pygame.draw.rect(screen, OUT, board.inflate(4, 4), border_radius=5)
    pygame.draw.rect(screen, (112, 78, 50), board, border_radius=4)
    pygame.draw.rect(screen, (150, 108, 70), board.inflate(-4, -4), 1, border_radius=3)
    screen.blit(label, label.get_rect(center=board.center))
    # placa pendurada com o ícone da loja
    sx = px + 10
    pygame.draw.line(screen, OUT, (wall.x - 2, py + rh + 18), (sx + 10, py + rh + 18), 3)
    _shop_sign_icon(screen, sid, sx + 6, py + rh + 30)
    # cenário na frente
    left, right = _PROPS.get(sid, ("barril", "caixa"))
    _prop(screen, left, px + 12, py + h + 2)
    _prop(screen, right, px + w - 14, py + h + 2)


WORKER_COL = {"camisa": (70, 150, 90), "calca": (110, 90, 60), "cabelo": (80, 50, 30), "chapeu": (230, 210, 120)}


def _wheel(screen, x, y, r, t=0.0, moving=False):
    OUT = (30, 28, 30)
    pygame.draw.circle(screen, OUT, (x, y), r + 1)
    pygame.draw.circle(screen, (54, 54, 60), (x, y), r)
    pygame.draw.circle(screen, (220, 190, 70), (x, y), max(2, r // 2))
    a = t * 9 if moving else 0.0
    pygame.draw.line(screen, (150, 120, 40), (x, y), (x + int(math.cos(a) * r * .5), y + int(math.sin(a) * r * .5)), 2)


def draw_tractor(screen, x, y, facing, moving, t, load, person_fn):
    """Trator vermelho com carreta atrás. (x, y) = chão embaixo do trator. person_fn(x, y) desenha o piloto."""
    OUT = (46, 32, 24)
    fx, fy = facing
    horiz = fx != 0
    d = 1 if (fx > 0 or fy > 0) else -1                       # sentido para onde o trator olha
    x, y = int(x), int(y)
    bump = int(math.sin(t * 22) * 1) if moving else 0
    shadow(screen, x, y - 2, 60 if horiz else 40, 14, 70)
    if horiz:
        # carreta atrás
        tx = x - d * 46
        shadow(screen, tx, y - 2, 40, 10, 60)
        pygame.draw.line(screen, OUT, (x - d * 16, y - 8), (tx + d * 14, y - 8), 4)
        pygame.draw.rect(screen, OUT, (tx - 18, y - 24 + bump, 36, 18), border_radius=3)
        pygame.draw.rect(screen, (190, 140, 84), (tx - 17, y - 23 + bump, 34, 16), border_radius=3)
        for k in range(min(load, 6)):
            pygame.draw.circle(screen, (240, 170, 60), (tx - 12 + k * 5, y - 26 + bump - (k % 2) * 3), 4)
            pygame.draw.circle(screen, OUT, (tx - 12 + k * 5, y - 26 + bump - (k % 2) * 3), 4, 1)
        _wheel(screen, tx - 8, y - 4, 6, t, moving)
        _wheel(screen, tx + 8, y - 4, 6, t, moving)
        person_fn(x - d * 3, y - 4 + bump)
        pygame.draw.rect(screen, OUT, (x - 24, y - 26 + bump, 48, 16), border_radius=4)             # corpo
        pygame.draw.rect(screen, (206, 50, 44), (x - 23, y - 25 + bump, 46, 14), border_radius=4)
        pygame.draw.rect(screen, (240, 110, 90), (x - 21, y - 24 + bump, 40, 3))
        hx = x + d * 10                                                                         # capô
        pygame.draw.rect(screen, OUT, (min(hx, hx + d * 18) - 1, y - 22 + bump, 20, 12), border_radius=3)
        pygame.draw.rect(screen, (214, 60, 52), (min(hx, hx + d * 18), y - 21 + bump, 18, 10), border_radius=3)
        pygame.draw.rect(screen, (60, 60, 66), (x + d * 20 - 2, y - 32 + bump, 4, 10))             # escapamento
        if moving:
            for k in range(3):
                ph = (t * 2 + k / 3) % 1.0
                pygame.draw.circle(screen, (210, 210, 216), (x + d * 20 - int(d * ph * 8), y - 36 - int(ph * 16)), int(2 + ph * 4))
        _wheel(screen, x - d * 12, y - 8, 10, t, moving)
        _wheel(screen, x + d * 16, y - 6, 7, t, moving)
        pygame.draw.rect(screen, (60, 60, 66), (x - d * 18 - 4, y - 38 + bump, 8, 4))            # banco
    else:
        ty = y - d * 40
        shadow(screen, x, ty - 2, 36, 10, 60)
        pygame.draw.line(screen, OUT, (x, y - 8 - d * 6), (x, ty - 4), 4)
        pygame.draw.rect(screen, OUT, (x - 16, ty - 24 + bump, 32, 22), border_radius=3)
        pygame.draw.rect(screen, (190, 140, 84), (x - 15, ty - 23 + bump, 30, 20), border_radius=3)
        for k in range(min(load, 6)):
            pygame.draw.circle(screen, (240, 170, 60), (x - 10 + (k % 3) * 9, ty - 20 + bump + (k // 3) * 8), 4)
        _wheel_v(screen, x - 19, ty - 8, 6, 15, t, moving)
        _wheel_v(screen, x + 19, ty - 8, 6, 15, t, moving)
        c = y - 16                                                                                # centro do trator
        for sx in (-1, 1):                                                                        # rodas vistas de frente/trás
            _wheel_v(screen, x + sx * 19, c - d * 8, 10, 26, t, moving)
            _wheel_v(screen, x + sx * 14, c + d * 14, 7, 15, t, moving)
        cab = (x - 12, c - d * 10 - 9, 24, 18)
        hood = (x - 8, c + d * 9 - 9, 16, 18)

        def draw_cab():
            pygame.draw.rect(screen, OUT, (cab[0] - 1, cab[1] - 1 + bump, cab[2] + 2, cab[3] + 2), border_radius=4)
            pygame.draw.rect(screen, (206, 50, 44), (cab[0], cab[1] + bump, cab[2], cab[3]), border_radius=4)
            pygame.draw.rect(screen, (240, 110, 90), (cab[0] + 2, cab[1] + 1 + bump, cab[2] - 4, 3))
            pygame.draw.rect(screen, (60, 60, 66), (x - 5, cab[1] + 6 + bump, 10, 7))              # banco

        def draw_hood():
            pygame.draw.rect(screen, OUT, (hood[0] - 1, hood[1] - 1 + bump, hood[2] + 2, hood[3] + 2), border_radius=3)
            pygame.draw.rect(screen, (214, 60, 52), (hood[0], hood[1] + bump, hood[2], hood[3]), border_radius=3)
            pygame.draw.rect(screen, (240, 110, 90), (hood[0] + 2, hood[1] + 1 + bump, hood[2] - 4, 2))
            if d > 0:                                                                              # grade e faróis na frente
                for k in range(3):
                    pygame.draw.line(screen, (60, 60, 66), (x - 5, hood[1] + 11 + k * 2 + bump), (x + 5, hood[1] + 11 + k * 2 + bump), 1)
                pygame.draw.circle(screen, (255, 240, 170), (x - 11, hood[1] + 13 + bump), 3)
                pygame.draw.circle(screen, (255, 240, 170), (x + 11, hood[1] + 13 + bump), 3)
            else:
                pygame.draw.rect(screen, (60, 60, 66), (x - 2, hood[1] - 6 + bump, 4, 8))          # escapamento

        if d > 0:
            draw_cab()
            person_fn(x, c + 2 + bump)
            draw_hood()
        else:
            draw_hood()
            draw_cab()
            person_fn(x, c + 28 + bump)


def _wheel_v(screen, cx, cy, w, h, t, moving):
    """Roda vista de frente ou de trás: um retângulo com os sulcos do pneu rodando."""
    OUT = (30, 28, 30)
    r = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    pygame.draw.rect(screen, OUT, r.inflate(2, 2), border_radius=3)
    pygame.draw.rect(screen, (54, 54, 60), r, border_radius=3)
    off = int(t * 40) % 5 if moving else 0
    for k in range(-1, h // 5 + 1):
        yy = r.y + k * 5 + off
        if r.y <= yy < r.bottom:
            pygame.draw.line(screen, (90, 90, 98), (r.x + 1, yy), (r.right - 2, yy), 1)


# ----------------------------------------------------------------- pessoas
def draw_person(screen, x, y, facing, moving, t, col, tool=None):
    """Personagem com corpo, cabeça, roupas e animação de caminhada. (x,y) = pés."""
    x, y = int(x), int(y)
    shadow(screen, x, y - 1, 30, 10)
    if col.get("sheet") and _draw_hero(screen, x, y, facing, moving, t, tool):
        return
    sw = math.sin(t * 12) * 4 if moving else 0
    bob = int(abs(math.sin(t * 12)) * 2) if moving else 0
    ly, ry = int(max(0, sw)), int(max(0, -sw))
    shirt, pants = tuple(col["camisa"]), tuple(col["calca"])
    pele, hair = tuple(col.get("pele", (240, 196, 150))), tuple(col["cabelo"])
    pygame.draw.rect(screen, pants, (x - 7, y - 12 - ly, 6, 12))
    pygame.draw.rect(screen, pants, (x + 1, y - 12 - ry, 6, 12))
    pygame.draw.rect(screen, (70, 50, 30), (x - 8, y - 3 - ly, 8, 4))
    pygame.draw.rect(screen, (70, 50, 30), (x, y - 3 - ry, 8, 4))
    pygame.draw.rect(screen, shirt, (x - 9, y - 27 - bob, 18, 16), border_radius=3)
    pygame.draw.rect(screen, shirt, (x - 13, y - 26 - bob, 5, 12))
    pygame.draw.rect(screen, shirt, (x + 8, y - 26 - bob, 5, 12))
    pygame.draw.rect(screen, pele, (x - 13, y - 15 - bob, 5, 4))
    pygame.draw.rect(screen, pele, (x + 8, y - 15 - bob, 5, 4))
    pygame.draw.circle(screen, pele, (x, y - 34 - bob), 8)
    fx, fy = facing
    if fy < 0:
        pygame.draw.rect(screen, hair, (x - 8, y - 41 - bob, 16, 8))
    else:
        pygame.draw.rect(screen, hair, (x - 8, y - 42 - bob, 16, 5))
        for dx in (-3, 3):
            pygame.draw.circle(screen, (40, 30, 30), (x + dx + fx * 2, y - 33 - bob), 1)
    if col.get("chapeu"):
        pygame.draw.ellipse(screen, tuple(col["chapeu"]), (x - 13, y - 44 - bob, 26, 9))
        pygame.draw.ellipse(screen, shade(tuple(col["chapeu"]), 1.12), (x - 7, y - 51 - bob, 14, 10))
    if tool:
        k = tool["k"]
        hx, hy = x + fx * 10, y - 18 - bob + fy * 6
        off = (k - .5) * 26
        tx, ty = hx + fx * 16 - fy * off, hy + fy * 12 + fx * off * .6
        pygame.draw.line(screen, (120, 86, 50), (hx, hy), (tx, ty), 4)
        pygame.draw.circle(screen, tool["cor"], (int(tx), int(ty)), 5)


def _draw_hero(screen, x, y, facing, moving, t, tool):
    """Personagem do jogador a partir da folha de sprites (assets/sprites/player). False se os PNGs não existirem."""
    fr = assets.player_frame(facing, moving, t)
    if fr is None:
        return False
    bob = -int(abs(math.sin(t * 16)) * 2) if moving else 0
    held = None
    if tool and tool.get("icon"):
        held = assets.tool_sprite(tool["icon"], (32, 32))
    fx, fy = facing
    if held is not None and fy < 0:                                   # de costas: a ferramenta fica atrás do corpo
        _draw_held(screen, held, x, y, fx, fy, tool["k"], bob)
    screen.blit(fr, (x - fr.get_width() // 2, y - fr.get_height() + 1 + bob))
    if held is not None and fy >= 0:
        _draw_held(screen, held, x, y, fx, fy, tool["k"], bob)
    return True


def _draw_held(screen, img, x, y, fx, fy, k, bob):
    """Ferramenta na mão: gira conforme a animação do golpe (k vai de 1 a 0)."""
    side = 1 if fx >= 0 else -1
    ang = (-80 + 120 * (1 - k)) * (1 if side > 0 else -1)
    try:
        im = pygame.transform.rotate(img if side > 0 else pygame.transform.flip(img, True, False), ang)
    except Exception:
        im = img
    cx = x + (fx * 16 if fx else 12)
    cy = y - 24 + bob + (fy * 10)
    screen.blit(im, (cx - im.get_width() // 2, cy - im.get_height() // 2))


# ----------------------------------------------------------------- animais
def _bubble(screen, x, y, cor, t):
    yy = y + int(math.sin(t * 4 + x) * 2)
    pygame.draw.polygon(screen, (255, 255, 255), [(x - 4, yy + 8), (x + 4, yy + 8), (x, yy + 15)])
    pygame.draw.circle(screen, (255, 255, 255), (x, yy), 10)
    pygame.draw.circle(screen, (90, 70, 50), (x, yy), 10, 2)
    pygame.draw.circle(screen, tuple(cor), (x, yy), 5)


def draw_animal(screen, tipo, x, y, d, t, pronto, cor_produto, walk=False, baby=False):
    """Desenha o animal com os pés em (x, y). walk=True anima as pernas; baby=True desenha um filhote (menor)."""
    if not baby:
        _animal_body(screen, tipo, x, y, d, t, pronto, cor_produto, walk)
        return
    tmp = pygame.Surface((96, 96), pygame.SRCALPHA)
    _animal_body(tmp, tipo, 48, 86, d, t, False, cor_produto, walk)
    small = pygame.transform.scale(tmp, (58, 58))
    screen.blit(small, (int(x) - 29, int(y) - 52))
    if pronto:
        _bubble(screen, int(x), int(y) - 40, cor_produto, t)


def _animal_body(screen, tipo, x, y, d, t, pronto, cor_produto, walk=False):
    x, y = int(x), int(y)
    ph = math.sin(t * 12 + x * 0.1) if walk else 0.0            # fase do passo
    bob = int(math.sin(t * 3 + x) * 1.2) + (int(abs(math.sin(t * 9)) * -2) if walk else 0)
    if tipo in ("galinha", "pato"):
        pato = tipo == "pato"
        body = (240, 236, 200) if pato else (255, 252, 244)
        shadow(screen, x, y - 1, 24, 8)
        for i, lx in enumerate((-3, 3)):
            sw = int(ph * 3) * (1 if i else -1)               # pernas alternadas ao andar
            pygame.draw.line(screen, (230, 150, 40), (x + lx, y - 6), (x + lx + sw, y), 2)
        pygame.draw.polygon(screen, shade(body, .92), [(x - d * 8, y - 12 + bob), (x - d * 15, y - 21 + bob), (x - d * 6, y - 18 + bob)])
        pygame.draw.ellipse(screen, body, (x - 9, y - 17 + bob, 18, 13))
        pygame.draw.ellipse(screen, shade(body, .9), (x - 6 - d * 2, y - 14 + bob, 10, 6))
        hx = x + d * 8
        pygame.draw.circle(screen, (60, 130, 70) if pato else body, (hx, y - 21 + bob), 5)
        if not pato:
            pygame.draw.circle(screen, (220, 40, 40), (hx, y - 27 + bob), 2)
            pygame.draw.circle(screen, (220, 40, 40), (hx - 1, y - 26 + bob), 2)
        pygame.draw.polygon(screen, (240, 160, 40), [(hx + d * 4, y - 22 + bob), (hx + d * (11 if pato else 9), y - 20 + bob), (hx + d * 4, y - 19 + bob)])
        pygame.draw.circle(screen, (30, 30, 30), (hx + d * 2, y - 22 + bob), 1)
        if pronto:
            _bubble(screen, x, y - 38, cor_produto, t)
        return
    if tipo == "coelho":
        hop = int(abs(math.sin(t * 10)) * 5) if walk else 0      # coelho anda aos pulinhos
        bob -= hop
        shadow(screen, x, y - 1, 24, 8)
        pelo, pata = (214, 196, 180), (190, 170, 154)
        pygame.draw.line(screen, pata, (x - d * 5, y - 8 + bob), (x - d * 8, y - 1), 4)               # perna de trás (coxa grossa)
        pygame.draw.ellipse(screen, pata, (x - d * 8 - 4, y - 4, 9, 4))
        pygame.draw.line(screen, pata, (x + d * 5, y - 8 + bob), (x + d * 6, y - 1), 3)               # perninha da frente
        pygame.draw.ellipse(screen, pata, (x + d * 6 - 3, y - 3, 6, 3))
        pygame.draw.circle(screen, (250, 250, 250), (x - d * 8, y - 8 + bob), 3)
        pygame.draw.ellipse(screen, (214, 196, 180), (x - 9, y - 14 + bob, 18, 12))
        hx = x + d * 8
        pygame.draw.circle(screen, (214, 196, 180), (hx, y - 14 + bob), 5)
        pygame.draw.ellipse(screen, (214, 196, 180), (hx - 4 - d * 1, y - 28 + bob, 4, 13))
        pygame.draw.ellipse(screen, (240, 170, 180), (hx - 3 - d * 1, y - 26 + bob, 2, 8))
        pygame.draw.ellipse(screen, (214, 196, 180), (hx + 1, y - 28 + bob, 4, 13))
        pygame.draw.circle(screen, (30, 30, 30), (hx + d * 2, y - 15 + bob), 1)
        if pronto:
            _bubble(screen, x, y - 36, cor_produto, t)
        return
    # quadrúpedes
    big = tipo in ("vaca",)
    shadow(screen, x, y - 1, 56 if big else 40, 18 if big else 14)
    sc = 1.0 if big else .72
    coat = {"vaca": (250, 250, 250), "cabra": (226, 206, 170), "ovelha": (246, 244, 238), "porco": (244, 176, 184)}[tipo]
    leg = {"vaca": (60, 44, 36), "cabra": (110, 90, 70), "ovelha": (60, 56, 56), "porco": (220, 150, 160)}[tipo]
    for i, lx in enumerate((-15, -8, 4, 11)):
        lift = int(max(0.0, ph * (1 if i % 2 else -1)) * 4 * sc)   # pernas em diagonal sobem e descem
        pygame.draw.rect(screen, leg, (x + int(lx * sc), y - int(10 * sc) - lift, int(5 * sc) + 1, int(10 * sc)))
    bw, bhh = int(42 * sc), int(22 * sc)
    pygame.draw.ellipse(screen, coat, (x - bw // 2, y - int(30 * sc) + bob, bw, bhh))
    if tipo == "vaca":
        for sx_, sy_, w_, h_ in ((-12, -26, 10, 8), (3, -22, 12, 9), (-4, -31, 8, 6)):
            pygame.draw.ellipse(screen, (40, 36, 36), (x + sx_, y + sy_ + bob, w_, h_))
        pygame.draw.ellipse(screen, (244, 190, 190), (x - 6, y - 12 + bob, 12, 7))
    if tipo == "ovelha":
        for dx, dy in ((-10, -22), (-2, -26), (8, -22), (-6, -17), (4, -17)):
            pygame.draw.circle(screen, (252, 250, 246), (x + dx, y + dy + bob), 8)
    pygame.draw.line(screen, leg, (x - d * 20 * sc, y - 24 * sc + bob), (x - d * 25 * sc, y - 14 * sc + bob), 2)
    hx, hy = x + int(d * 22 * sc), y - int(26 * sc) + bob
    hc = (60, 56, 56) if tipo == "ovelha" else coat
    pygame.draw.ellipse(screen, hc, (hx - 8, hy - 8, 16, 15))
    if tipo == "porco":
        pygame.draw.ellipse(screen, (236, 140, 156), (hx - 6 + d * 3, hy - 1, 12, 8))
        pygame.draw.circle(screen, (150, 80, 90), (hx + d * 5, hy + 3), 1)
        pygame.draw.polygon(screen, (230, 150, 160), [(hx - 6, hy - 8), (hx - 1, hy - 10), (hx - 1, hy - 4)])
    elif tipo == "vaca":
        pygame.draw.ellipse(screen, (244, 170, 170), (hx - 6 + d * 3, hy, 12, 8))
        for dx in (-5, 5):
            pygame.draw.line(screen, (235, 225, 190), (hx + dx, hy - 8), (hx + dx * 1.4, hy - 13), 3)
    elif tipo == "cabra":
        for dx in (-3, 3):
            pygame.draw.line(screen, (150, 130, 100), (hx + dx, hy - 8), (hx + dx * 2, hy - 15), 2)
        pygame.draw.line(screen, (240, 240, 230), (hx + d * 4, hy + 6), (hx + d * 4, hy + 11), 2)
    pygame.draw.circle(screen, (30, 30, 30), (hx + d * 2, hy - 2), 1)
    if pronto:
        _bubble(screen, x, y - int(50 * sc) - 4, cor_produto, t)


def draw_face(screen, tipo, cx, cy, r):
    """Rosto do animal em estilo pixel art (blocos), centrado em (cx, cy), com raio ~r. Usado nos ícones."""
    u = max(2, r // 6)                                     # tamanho do "pixel"

    def px(dx, dy, w, h, col):
        pygame.draw.rect(screen, col, (cx + dx * u, cy + dy * u, w * u, h * u))
    OUT, EYE = (50, 36, 30), (24, 20, 24)
    if tipo in ("galinha", "pato"):
        pato = tipo == "pato"
        head = (62, 130, 76) if pato else (255, 252, 244)
        px(-4, -4, 8, 8, OUT)
        px(-3, -3, 6, 6, head)
        if not pato:
            px(-1, -6, 2, 2, (220, 40, 40))
            px(1, -5, 2, 1, (220, 40, 40))
            px(-1, 2, 2, 2, (220, 50, 50))
        px(-1, 0, 3, 2, (244, 170, 40))
        px(-3, -1, 1, 1, EYE)
        px(2, -1, 1, 1, EYE)
        if pato:
            px(-2, 1, 5, 2, (244, 170, 40))
    elif tipo == "coelho":
        px(-4, -8, 3, 6, OUT)
        px(1, -8, 3, 6, OUT)
        px(-3, -7, 1, 4, (240, 170, 180))
        px(2, -7, 1, 4, (240, 170, 180))
        px(-4, -3, 8, 7, OUT)
        px(-3, -2, 6, 5, (226, 208, 192))
        px(-2, -1, 1, 1, EYE)
        px(1, -1, 1, 1, EYE)
        px(-1, 1, 2, 1, (240, 150, 160))
    elif tipo == "vaca":
        px(-5, -4, 2, 2, (235, 225, 190))
        px(3, -4, 2, 2, (235, 225, 190))
        px(-4, -3, 8, 8, OUT)
        px(-3, -2, 6, 6, (250, 250, 250))
        px(-3, -2, 2, 2, (40, 36, 36))
        px(-2, 0, 1, 1, EYE)
        px(1, 0, 1, 1, EYE)
        px(-3, 2, 6, 3, (244, 180, 190))
        px(-2, 3, 1, 1, (150, 80, 90))
        px(1, 3, 1, 1, (150, 80, 90))
    elif tipo == "cabra":
        px(-4, -6, 1, 3, (150, 130, 100))
        px(3, -6, 1, 3, (150, 130, 100))
        px(-4, -3, 8, 7, OUT)
        px(-3, -2, 6, 5, (226, 206, 170))
        px(-2, 0, 1, 1, EYE)
        px(1, 0, 1, 1, EYE)
        px(-1, 2, 2, 2, (200, 170, 150))
        px(-1, 4, 2, 2, (240, 240, 230))
    elif tipo == "ovelha":
        for dx, dy in ((-4, -3), (-1, -4), (2, -3), (-4, 0), (3, 0)):
            px(dx, dy, 3, 3, (252, 250, 246))
        px(-3, -2, 6, 7, OUT)
        px(-2, -1, 4, 5, (70, 66, 66))
        px(-1, 0, 1, 1, (240, 240, 240))
        px(1, 0, 1, 1, (240, 240, 240))
        px(-1, 3, 2, 1, (150, 130, 130))
    else:                                                  # porco
        px(-5, -4, 3, 3, (230, 150, 160))
        px(2, -4, 3, 3, (230, 150, 160))
        px(-4, -3, 8, 8, OUT)
        px(-3, -2, 6, 6, (244, 176, 184))
        px(-2, -1, 1, 1, EYE)
        px(1, -1, 1, 1, EYE)
        px(-2, 1, 4, 3, (236, 130, 148))
        px(-1, 2, 1, 1, (150, 80, 90))
        px(1, 2, 1, 1, (150, 80, 90))


# ----------------------------------------------------------------- ícones de itens
TIER_HEAD = [(150, 110, 62), (166, 166, 176), (210, 214, 226), (248, 208, 72)]


def draw_icon(screen, it, r):
    """Ícone do item dentro do retângulo r."""
    x, y, w, h = r
    cx, cy = x + w // 2, y + h // 2
    k = it["kind"]
    cor = tuple(it.get("cor", (180, 180, 180)))
    s = min(w, h) / 48.0
    p = lambda a, b: (int(cx + a * s), int(cy + b * s))
    if k != "tool":
        sp = assets.item_sprite(it.get("id"))
        if sp is not None:                                            # pixel art em PNG (assets/sprites/items)
            side = max(16, int(min(w, h) * .95) // 16 * 16)               # ampliação inteira (pixel art nítida)
            screen.blit(pygame.transform.scale(sp, (side, side)), (cx - side // 2, cy - side // 2))
            return
    if k == "tool":
        sp = assets.tool_sprite(assets.tool_name(it))
        if sp is not None:                                            # pixel art em PNG (assets/sprites/tools)
            side = max(16, int(min(w, h) * .95) // 16 * 16)
            img = pygame.transform.scale(sp, (side, side))
            screen.blit(img, (cx - side // 2, cy - side // 2))
            return
        n = it["tool"]
        hc = TIER_HEAD[it.get("nivel", 0)]
        if n == "enxada":
            pygame.draw.line(screen, (140, 100, 56), p(-14, 16), p(10, -10), 4)
            pygame.draw.polygon(screen, (46, 32, 24), [p(5, -18), p(20, -8), p(10, 2), p(0, -6)])
            pygame.draw.polygon(screen, hc, [p(6, -16), p(18, -8), p(10, 0), p(2, -6)])
        elif n == "regador":
            pygame.draw.rect(screen, (70, 140, 210), (*p(-12, -2), int(24 * s), int(16 * s)), border_radius=4)
            pygame.draw.line(screen, (70, 140, 210), p(10, 4), p(18, -8), 4)
            pygame.draw.arc(screen, (50, 110, 180), (*p(-16, -12), int(16 * s), int(16 * s)), .2, 3.0, 3)
            if it.get("nivel", 0) > 0:
                pygame.draw.rect(screen, hc, (*p(-12, 4), int(24 * s), int(4 * s)))
        elif n == "foice":
            pygame.draw.arc(screen, (210, 210, 224), (*p(-14, -16), int(30 * s), int(30 * s)), .4, 3.3, 4)
            pygame.draw.line(screen, (140, 100, 56), p(-12, 10), p(-4, 18), 4)
        elif n == "machado":
            pygame.draw.line(screen, (140, 100, 56), p(-12, 16), p(8, -10), 4)
            pygame.draw.polygon(screen, (46, 32, 24), [p(1, -18), p(18, -8), p(13, 4), p(3, -4)])
            pygame.draw.polygon(screen, hc, [p(2, -16), p(16, -8), p(12, 2), p(4, -4)])
        elif n == "espada":
            pygame.draw.polygon(screen, (46, 32, 24), [p(-2, 8), p(16, -18), p(20, -16), p(4, 12)])
            pygame.draw.polygon(screen, (hc if it.get("nivel", 0) else (200, 204, 214)), [p(0, 6), p(16, -16), p(18, -15), p(3, 9)])
            pygame.draw.line(screen, (240, 244, 255), p(2, 4), p(15, -14), 1)
            pygame.draw.line(screen, (46, 32, 24), p(-8, 6), p(8, 14), 5)
            pygame.draw.line(screen, (230, 190, 70), p(-7, 6), p(7, 13), 3)
            pygame.draw.line(screen, (120, 80, 44), p(-4, 12), p(-12, 20), 4)
        elif n == "rede":
            pygame.draw.line(screen, (140, 100, 56), p(-14, 18), p(6, -6), 4)
            pygame.draw.ellipse(screen, (80, 70, 50), (*p(-2, -20), int(26 * s), int(22 * s)), 3)
            pygame.draw.ellipse(screen, (220, 214, 190), (*p(0, -18), int(22 * s), int(18 * s)), 1)
            pygame.draw.line(screen, (220, 214, 190), p(11, -18), p(11, 0), 1)
            pygame.draw.line(screen, (220, 214, 190), p(0, -9), p(22, -9), 1)
        else:
            pygame.draw.line(screen, (140, 100, 56), p(-6, 18), p(4, -8), 4)
            pygame.draw.arc(screen, (46, 32, 24), (*p(-17, -23), int(34 * s), int(26 * s)), .3, 2.8, 8)
            pygame.draw.arc(screen, hc, (*p(-16, -22), int(32 * s), int(24 * s)), .3, 2.8, 5)
    elif k == "loot":
        if it["id"] == "gosma":
            pygame.draw.ellipse(screen, (40, 90, 40), (*p(-14, -4), int(28 * s), int(22 * s)))
            pygame.draw.ellipse(screen, cor, (*p(-12, -2), int(24 * s), int(18 * s)))
            pygame.draw.circle(screen, (200, 250, 190), p(-4, 3), int(3 * s))
        else:
            pygame.draw.polygon(screen, (30, 24, 40), [p(-16, -6), p(0, -14), p(16, -6), p(10, 4), p(0, 0), p(-10, 4)])
            pygame.draw.polygon(screen, cor, [p(-14, -6), p(0, -12), p(14, -6), p(9, 2), p(0, -2), p(-9, 2)])
            pygame.draw.line(screen, (120, 100, 150), p(0, -12), p(0, -2), 1)
    elif k == "seed":
        pygame.draw.rect(screen, (214, 184, 130), (*p(-11, -10), int(22 * s), int(26 * s)), border_radius=4)
        pygame.draw.rect(screen, (160, 124, 76), (*p(-11, -10), int(22 * s), int(7 * s)), border_radius=3)
        pygame.draw.circle(screen, cor, p(0, 5), int(7 * s))
        pygame.draw.circle(screen, (60, 40, 25), p(0, 5), int(7 * s), 1)
    elif k == "crop":
        f = it.get("forma", "raiz")
        if f == "raiz":
            pygame.draw.polygon(screen, cor, [p(-8, -4), p(8, -4), p(0, 16)])
            for a in (-6, 0, 6):
                pygame.draw.line(screen, (80, 170, 70), p(0, -4), p(a, -14), 3)
        elif f == "folha":
            pygame.draw.circle(screen, shade(cor, .8), p(0, 2), int(12 * s))
            pygame.draw.circle(screen, cor, p(0, 0), int(8 * s))
        elif f == "haste":
            pygame.draw.ellipse(screen, cor, (*p(-5, -14), int(10 * s), int(28 * s)))
            pygame.draw.line(screen, (80, 160, 60), p(0, 14), p(-8, 2), 3)
        elif f == "trepadeira":
            pygame.draw.ellipse(screen, cor, (*p(-14, -9), int(28 * s), int(20 * s)))
            pygame.draw.line(screen, (60, 120, 50), p(0, -9), p(0, -14), 3)
        elif f == "flor":
            for i in range(6):
                a = i * math.tau / 6
                pygame.draw.circle(screen, cor, p(math.cos(a) * 7, math.sin(a) * 7 - 2), int(5 * s))
            pygame.draw.circle(screen, (250, 220, 90), p(0, -2), int(3 * s))
        elif f == "vagem":
            pygame.draw.ellipse(screen, cor, (*p(-4, -14), int(9 * s), int(28 * s)))
        else:
            pygame.draw.circle(screen, cor, p(0, 2), int(11 * s))
            pygame.draw.circle(screen, shade(cor, 1.3), p(-3, -1), int(3 * s))
    elif k == "material":
        n = it["id"]
        if n == "madeira":
            for i in range(3):
                pygame.draw.rect(screen, (150, 104, 60), (*p(-14, -10 + i * 8), int(28 * s), int(7 * s)), border_radius=3)
        elif n == "pedra":
            pygame.draw.polygon(screen, cor, [p(-12, 8), p(-8, -8), p(4, -12), p(13, 0), p(12, 8)])
        elif n == "fibra":
            for a in (-8, -3, 2, 7):
                pygame.draw.line(screen, cor, p(a, 12), p(a + 3, -12), 3)
        elif n == "alevino":
            pygame.draw.circle(screen, (150, 200, 235), p(0, 2), int(15 * s), 2)
            draw_fish(screen, *p(-3, 3), max(4, int(6 * s)), cor)
            draw_fish(screen, *p(6, -4), max(3, int(4 * s)), cor, True)
        elif n == "racao_peixe":
            pygame.draw.rect(screen, (190, 160, 110), (*p(-10, -10), int(20 * s), int(24 * s)), border_radius=5)
            pygame.draw.rect(screen, (240, 240, 230), (*p(-6, -2), int(12 * s), int(10 * s)))
            draw_fish(screen, *p(0, 3), max(3, int(4 * s)), (90, 130, 190))
        else:
            pygame.draw.ellipse(screen, cor, (*p(-14, -8), int(28 * s), int(20 * s)))
            for a in (-8, 0, 8):
                pygame.draw.line(screen, shade(cor, .8), p(a, -6), p(a - 2, 8), 1)
    elif k == "fertilizer":
        pygame.draw.rect(screen, shade(cor, 1.0), (*p(-10, -12), int(20 * s), int(26 * s)), border_radius=5)
        pygame.draw.rect(screen, (240, 240, 230), (*p(-6, -4), int(12 * s), int(10 * s)))
    elif k == "food":
        if it["id"] == "pao":
            pygame.draw.ellipse(screen, cor, (*p(-14, -7), int(28 * s), int(16 * s)))
            pygame.draw.line(screen, shade(cor, .7), p(-6, -3), p(-2, 3), 2)
        elif it["id"] == "bolo":
            pygame.draw.rect(screen, (46, 32, 24), (*p(-14, -2), int(28 * s), int(18 * s)), border_radius=3)
            pygame.draw.rect(screen, (150, 96, 60), (*p(-13, -1), int(26 * s), int(16 * s)), border_radius=3)
            pygame.draw.rect(screen, (255, 240, 235), (*p(-13, -1), int(26 * s), int(7 * s)), border_radius=3)
            pygame.draw.rect(screen, cor, (*p(-13, -9), int(26 * s), int(9 * s)), border_radius=4)
            pygame.draw.circle(screen, (210, 40, 60), p(0, -12), max(2, int(4 * s)))
        elif it["id"] == "omelete":
            pygame.draw.ellipse(screen, (46, 32, 24), (*p(-15, -8), int(30 * s), int(20 * s)))
            pygame.draw.ellipse(screen, cor, (*p(-14, -7), int(28 * s), int(18 * s)))
            pygame.draw.line(screen, (230, 180, 70), p(-9, 2), p(9, 2), 2)
            pygame.draw.circle(screen, (110, 190, 80), p(-4, -2), max(1, int(2 * s)))
        elif it["id"] in ("sopa", "salada"):
            pygame.draw.ellipse(screen, cor, (*p(-12, -8), int(24 * s), int(10 * s)))
            pygame.draw.polygon(screen, (46, 32, 24), [p(-14, -4), p(14, -4), p(9, 12), p(-9, 12)])
            pygame.draw.polygon(screen, (236, 232, 222), [p(-13, -3), p(13, -3), p(8, 11), p(-8, 11)])
            pygame.draw.ellipse(screen, cor, (*p(-11, -6), int(22 * s), int(8 * s)))
        elif it["id"] == "torta_abobora":
            pygame.draw.circle(screen, (46, 32, 24), p(0, 2), int(15 * s))
            pygame.draw.circle(screen, (214, 164, 96), p(0, 2), int(14 * s))
            pygame.draw.circle(screen, cor, p(0, 2), int(10 * s))
            for a in (-6, 0, 6):
                pygame.draw.line(screen, (190, 140, 80), p(a, -6), p(a, 10), 1)
        elif it["id"] == "geleia":
            pygame.draw.rect(screen, (46, 32, 24), (*p(-9, -6), int(18 * s), int(20 * s)), border_radius=4)
            pygame.draw.rect(screen, cor, (*p(-8, -3), int(16 * s), int(16 * s)), border_radius=3)
            pygame.draw.rect(screen, (240, 240, 230), (*p(-9, -9), int(18 * s), int(5 * s)), border_radius=2)
        elif it["id"] == "peixe_assado":
            pygame.draw.ellipse(screen, (236, 232, 222), (*p(-16, -8), int(32 * s), int(22 * s)))
            draw_fish(screen, *p(0, 3), max(5, int(10 * s)), cor)
        else:
            pygame.draw.polygon(screen, (240, 240, 250), [p(-8, -10), p(8, -10), p(6, 14), p(-6, 14)])
            pygame.draw.polygon(screen, cor, [p(-7, -2), p(7, -2), p(6, 14), p(-6, 14)])
    elif k == "fish":
        draw_fish(screen, cx, cy, max(8, int(15 * s)), cor, flip=(sum(cor) % 2 == 0))
    elif k == "ore":
        n = it["id"]
        if n == "carvao":
            pygame.draw.polygon(screen, (20, 20, 24), [p(-12, 8), p(-10, -6), p(0, -12), p(11, -5), p(12, 8)])
            pygame.draw.polygon(screen, (52, 52, 60), [p(-9, 6), p(-8, -4), p(0, -9), p(6, -3), p(4, 6)])
            pygame.draw.line(screen, (120, 120, 134), p(-4, -4), p(0, -7), 2)
        else:
            pygame.draw.polygon(screen, (46, 32, 24), [p(-13, 9), p(-11, -7), p(0, -13), p(12, -5), p(13, 9)])
            pygame.draw.polygon(screen, (126, 124, 134), [p(-11, 8), p(-9, -5), p(0, -10), p(10, -4), p(11, 8)])
            for dx, dy in ((-5, -2), (3, -5), (5, 3), (-2, 4)):
                pygame.draw.circle(screen, cor, p(dx, dy), max(2, int(3.4 * s)))
                pygame.draw.circle(screen, shade(cor, 1.3), p(dx - 1, dy - 1), max(1, int(1.4 * s)))
    elif k == "bar":
        pygame.draw.polygon(screen, (46, 32, 24), [p(-15, 6), p(-9, -8), p(15, -8), p(15, 6)])
        pygame.draw.polygon(screen, cor, [p(-13, 4), p(-8, -6), p(13, -6), p(13, 4)])
        pygame.draw.polygon(screen, shade(cor, 1.3), [p(-8, -6), p(13, -6), p(11, -3), p(-6, -3)])
        pygame.draw.rect(screen, shade(cor, .75), (*p(-13, 3), int(26 * s), max(2, int(3 * s))))
    elif k == "gem":
        pygame.draw.polygon(screen, (46, 32, 24), [p(-13, -3), p(-7, -11), p(7, -11), p(13, -3), p(0, 13)])
        pygame.draw.polygon(screen, cor, [p(-11, -3), p(-6, -9), p(6, -9), p(11, -3), p(0, 11)])
        pygame.draw.polygon(screen, shade(cor, 1.25), [p(-6, -9), p(6, -9), p(3, -3), p(-3, -3)])
        pygame.draw.line(screen, (255, 255, 255), p(-7, -4), p(-3, -8), 2)
    elif k == "product":
        n = it["id"]
        if n.startswith("ovo"):
            pygame.draw.ellipse(screen, cor, (*p(-8, -12), int(16 * s), int(22 * s)))
            pygame.draw.ellipse(screen, shade(cor, .8), (*p(-8, -12), int(16 * s), int(22 * s)), 1)
        elif n.startswith("leite"):
            pygame.draw.rect(screen, cor, (*p(-7, -8), int(14 * s), int(22 * s)), border_radius=3)
            pygame.draw.rect(screen, cor, (*p(-4, -14), int(8 * s), int(8 * s)))
            pygame.draw.rect(screen, (120, 140, 190), (*p(-7, -8), int(14 * s), int(22 * s)), 1, border_radius=3)
        else:
            for dx, dy in ((-7, 0), (0, -6), (7, 0), (0, 5)):
                pygame.draw.circle(screen, cor, p(dx, dy), int(7 * s))
    else:   # construção
        sid = it["struct"]
        if sid in ("galinheiro", "celeiro", "coelheira"):
            face = {"galinheiro": "galinha", "celeiro": "vaca", "coelheira": "coelho"}[sid]
            wall = {"galinheiro": (196, 120, 76), "celeiro": (184, 52, 44), "coelheira": (176, 136, 96)}[sid]
            roofc = {"galinheiro": (110, 70, 60), "celeiro": (110, 80, 76), "coelheira": (120, 90, 70)}[sid]
            pygame.draw.rect(screen, (40, 28, 22), (*p(-19, -5), int(38 * s), int(26 * s)), border_radius=3)
            pygame.draw.rect(screen, wall, (*p(-18, -4), int(36 * s), int(24 * s)), border_radius=2)
            pygame.draw.polygon(screen, (40, 28, 22), [p(-22, -3), p(0, -20), p(22, -3)])
            pygame.draw.polygon(screen, roofc, [p(-19, -4), p(0, -17), p(19, -4)])
            draw_face(screen, face, cx, int(cy + 8 * s), max(6, int(10 * s)))
        elif sid == "tanque":
            pygame.draw.rect(screen, (150, 106, 64), (*p(-16, -10), int(32 * s), int(26 * s)), border_radius=4)
            pygame.draw.rect(screen, (66, 140, 200), (*p(-12, -6), int(24 * s), int(18 * s)), border_radius=3)
            draw_fish(screen, *p(0, 3), max(4, int(6 * s)), (250, 160, 70))
        elif sid == "barraca":
            pygame.draw.rect(screen, (176, 128, 80), (*p(-16, 2), int(32 * s), int(14 * s)), border_radius=3)
            for i in range(4):
                pygame.draw.rect(screen, (214, 70, 70) if i % 2 == 0 else (250, 246, 238), (*p(-16 + i * 8, -10), int(8 * s), int(10 * s)))
        elif sid in ("macieira", "laranjeira", "pessegueiro", "arvore_jovem"):
            pygame.draw.rect(screen, (130, 92, 56), (*p(-3, 0), int(6 * s), int(18 * s)))
            pygame.draw.circle(screen, (78, 158, 68), p(0, -6), int(13 * s))
            for dx, dy in ((-6, -8), (5, -3), (0, -12)):
                pygame.draw.circle(screen, cor, p(dx, dy), max(2, int(3 * s)))
        elif sid == "torneira":
            pygame.draw.rect(screen, (150, 148, 156), (*p(-10, 10), int(20 * s), int(6 * s)), border_radius=2)
            pygame.draw.rect(screen, (96, 100, 112), (*p(-3, -12), int(6 * s), int(24 * s)))
            pygame.draw.rect(screen, (96, 100, 112), (*p(-3, -12), int(16 * s), int(5 * s)))
            pygame.draw.circle(screen, (200, 60, 60), p(0, -14), max(3, int(5 * s)))
            pygame.draw.circle(screen, (70, 140, 210), p(11, 4), max(2, int(3 * s)))
        elif sid == "quartinho":
            pygame.draw.rect(screen, (172, 124, 84), (*p(-16, -4), int(32 * s), int(22 * s)))
            pygame.draw.rect(screen, (112, 76, 46), (*p(-5, 4), int(10 * s), int(14 * s)))
            pygame.draw.polygon(screen, (46, 32, 24), [p(-20, -3), p(0, -20), p(20, -3)])
            pygame.draw.polygon(screen, (120, 86, 66), [p(-17, -4), p(0, -17), p(17, -4)])
            pygame.draw.circle(screen, (240, 200, 80), p(0, 11), max(2, int(2 * s)))
        elif sid == "forno":
            pygame.draw.rect(screen, (150, 150, 162), (*p(-14, -6), int(28 * s), int(20 * s)))
            pygame.draw.rect(screen, (30, 26, 30), (*p(-6, 2), int(12 * s), int(12 * s)))
            pygame.draw.circle(screen, (250, 150, 40), p(0, 10), max(2, int(3 * s)))
        elif sid == "misturador":
            pygame.draw.rect(screen, (196, 150, 92), (*p(-13, -6), int(26 * s), int(22 * s)), border_radius=4)
            pygame.draw.ellipse(screen, (240, 210, 110), (*p(-11, -12), int(22 * s), int(10 * s)))
            pygame.draw.rect(screen, (140, 100, 60), (*p(-13, 2), int(26 * s), int(3 * s)))
        elif sid in ("cerca", "portao"):
            for a in (-12, 0, 12):
                pygame.draw.rect(screen, (120, 84, 48), (*p(a - 2, -12), int(5 * s), int(24 * s)))
            pygame.draw.line(screen, cor, p(-14, -4), p(14, -4), 3)
            pygame.draw.line(screen, cor, p(-14, 4), p(14, 4), 3)
        elif sid.startswith("caminho"):
            pygame.draw.rect(screen, cor, (*p(-13, -13), int(26 * s), int(26 * s)), border_radius=3)
        elif sid == "jardim":
            pygame.draw.rect(screen, (110, 78, 52), (*p(-14, -10), int(28 * s), int(22 * s)), border_radius=5)
            for dx, dy in ((-7, -2), (3, 3), (7, -4)):
                pygame.draw.circle(screen, (240, 130, 170), p(dx, dy), int(4 * s))
        elif sid.startswith("aspersor"):
            pygame.draw.rect(screen, cor, (*p(-3, -10), int(6 * s), int(20 * s)))
            pygame.draw.circle(screen, (210, 230, 250), p(0, -11), int(6 * s))
        elif sid == "lampada":
            pygame.draw.rect(screen, (60, 60, 64), (*p(-2, -4), int(4 * s), int(18 * s)))
            pygame.draw.rect(screen, (255, 226, 130), (*p(-6, -14), int(12 * s), int(11 * s)), border_radius=3)
        else:
            pygame.draw.rect(screen, cor, (*p(-12, -8), int(24 * s), int(18 * s)), border_radius=4)


# ----------------------------------------------------------------- mina (andares)
def draw_mine_floor(surf, w, h, T, seed, rails=(), lanterns=()):
    """Fundo do andar: calçamento de pedras irregulares, parede de rocha, vigas de madeira, trilhos e cristais."""
    rng = random.Random(seed)
    OUT = (22, 20, 22)
    for y in range(h):
        for x in range(w):
            px, py = x * T, y * T
            if x in (0, w - 1) or y in (0, h - 1):                                     # parede: entulho de pedras escuras
                pygame.draw.rect(surf, (36, 38, 40), (px, py, T, T))
                for _ in range(5):
                    cx, cy = px + rng.randint(2, T - 3), py + rng.randint(2, T - 3)
                    v = rng.randint(50, 76)
                    rr = rng.randint(5, 9)
                    pygame.draw.circle(surf, OUT, (cx, cy), rr + 1)
                    pygame.draw.circle(surf, (v, v + 4, v + 2), (cx, cy), rr)
                    pygame.draw.circle(surf, (v + 20, v + 24, v + 22), (cx - 2, cy - 2), max(1, rr // 3))
            else:                                                                        # chão: pedras redondas com rejunte
                pygame.draw.rect(surf, (46, 48, 46), (px, py, T, T))
                for j in range(2):
                    for i in range(2):
                        ox = (8 if (j + y) % 2 else 0) - 8 + i * 16
                        sx, sy = px + ox + 1, py + j * 16 + 1
                        v = rng.randint(78, 100)
                        tint = rng.choice(((0, 4, 0), (4, 2, -6), (-4, 2, 4)))
                        col = (v + tint[0], v + tint[1], v + tint[2])
                        x0_, x1_ = max(px, sx), min(px + T, sx + 14)
                        if x1_ > x0_:
                            pygame.draw.rect(surf, col, (x0_, sy, x1_ - x0_, 14), border_radius=4)
                            pygame.draw.line(surf, (v + 18, v + 20, v + 14), (x0_ + 1, sy + 1), (x1_ - 2, sy + 1), 1)
                if rng.random() < .07:
                    pygame.draw.rect(surf, (66, 104, 60), (px + rng.randint(2, 20), py + rng.randint(2, 20), 5, 2))     # musgo
    for x, y in rails:                                                                  # trilhos
        px, py = x * T, y * T
        for k in range(4):
            pygame.draw.rect(surf, (88, 62, 40), (px + 3 + k * 8, py + 4, 5, T - 8))
        for yy in (py + 9, py + T - 11):
            pygame.draw.line(surf, (30, 36, 52), (px, yy + 1), (px + T, yy + 1), 2)
            pygame.draw.line(surf, (96, 120, 150), (px, yy), (px + T, yy), 2)
    for lx in lanterns:                                                                 # viga de madeira com postes na parede de cima
        px = lx * T
        for dx in (-T * 2, T * 2):
            pygame.draw.rect(surf, OUT, (px + dx + 9, 0, 14, T + 10))
            pygame.draw.rect(surf, (140, 98, 58), (px + dx + 10, 0, 12, T + 9))
            pygame.draw.line(surf, (176, 132, 84), (px + dx + 12, 0), (px + dx + 12, T + 8), 1)
        pygame.draw.rect(surf, OUT, (px - T * 2 + 4, 10, T * 4 + 24, 12))
        pygame.draw.rect(surf, (156, 112, 66), (px - T * 2 + 5, 11, T * 4 + 22, 10))
        pygame.draw.line(surf, (190, 146, 90), (px - T * 2 + 6, 12), (px + T * 2 + 26, 12), 1)
        pygame.draw.line(surf, OUT, (px + 16, 21), (px + 16, 30), 2)
        pygame.draw.rect(surf, OUT, (px + 11, 30, 10, 12), border_radius=3)
        pygame.draw.rect(surf, (255, 214, 120), (px + 13, 32, 6, 8), border_radius=2)
    for _ in range(7):                                                                  # cristais azuis encravados nas paredes
        wx = rng.randint(2, w - 3)
        cx, cy = wx * T + 16, (h - 1) * T + 8 if rng.random() < .5 else 14
        for dx, hh in ((-5, 12), (0, 17), (5, 11)):
            pygame.draw.polygon(surf, OUT, [(cx + dx - 5, cy + 8), (cx + dx, cy + 8 - hh - 2), (cx + dx + 5, cy + 8)])
            pygame.draw.polygon(surf, (70, 140, 236), [(cx + dx - 4, cy + 8), (cx + dx, cy + 8 - hh), (cx + dx + 4, cy + 8)])
            pygame.draw.line(surf, (170, 220, 255), (cx + dx - 1, cy + 6), (cx + dx, cy + 8 - hh + 2), 1)


ORE_COL = {"carvao": (36, 34, 40), "minerio_cobre": (214, 128, 70), "minerio_ferro": (190, 196, 210),
           "minerio_ouro": (252, 212, 70), "diamante": (140, 236, 250)}


def draw_mine_cell(surf, x, y, T, cell, hp_max):
    """Pedra ou minério num bloco (x, y em blocos)."""
    px, py = x * T, y * T
    shadow(surf, px + T // 2, py + T - 3, T - 4, 8, 70)
    OUT = (30, 26, 34)
    pygame.draw.rect(surf, OUT, (px + 1, py + 3, T - 2, T - 4), border_radius=7)
    pygame.draw.rect(surf, (128, 126, 136), (px + 3, py + 5, T - 6, T - 9), border_radius=6)
    pygame.draw.rect(surf, (160, 158, 168), (px + 6, py + 7, T - 16, 6), border_radius=3)
    pygame.draw.rect(surf, (100, 98, 108), (px + 4, py + T - 10, T - 8, 5), border_radius=3)
    if cell["k"] == "ore":
        c = ORE_COL[cell["ore"]]
        for ox, oy, r in ((9, 12, 4), (20, 15, 5), (13, 21, 4), (23, 22, 3)):
            pygame.draw.circle(surf, OUT, (px + ox, py + oy), r + 1)
            pygame.draw.circle(surf, c, (px + ox, py + oy), r)
            pygame.draw.circle(surf, tuple(min(255, v + 60) for v in c), (px + ox - 1, py + oy - 1), max(1, r // 3))
    if cell["hp"] < hp_max:                                     # rachaduras quando danificado
        pygame.draw.line(surf, OUT, (px + 10, py + 8), (px + 16, py + 17), 2)
        pygame.draw.line(surf, OUT, (px + 16, py + 17), (px + 13, py + 25), 2)


def draw_mine_stairs(surf, x, y, T):
    px, py = x * T, y * T
    pygame.draw.rect(surf, (20, 16, 22), (px + 2, py + 2, T - 4, T - 4), border_radius=4)
    for i in range(4):
        c = 150 - i * 28
        pygame.draw.rect(surf, (c, c - 10, c - 20), (px + 4 + i * 2, py + 4 + i * 6, T - 8 - i * 4, 5))


def draw_mine_ladder(surf, x, y, T):
    px, py = x * T, y * T
    pygame.draw.rect(surf, (24, 18, 22), (px + 2, py + 2, T - 4, T - 4), border_radius=3)
    for bx in (px + 8, px + T - 12):
        pygame.draw.rect(surf, (40, 28, 18), (bx - 1, py, 6, T))
        pygame.draw.rect(surf, (150, 106, 60), (bx, py, 4, T))
    for i in range(4):
        pygame.draw.rect(surf, (170, 124, 72), (px + 8, py + 4 + i * 8, T - 16, 3))


def draw_mine_enemy(surf, kind, x, y, t, hurt=False, frac=1.0):
    """Inimigo da mina com os pés em (x, y) (pixels)."""
    x, y = int(x), int(y)
    OUT = (24, 20, 30)
    flash = hurt
    if kind == "slime":
        sq = math.sin(t * 6 + x * .1) * 2
        shadow(surf, x, y - 1, 28, 9, 70)
        w, h = int(26 + sq), int(18 - sq)
        col = (250, 250, 250) if flash else (96, 200, 90)
        pygame.draw.ellipse(surf, OUT, (x - w // 2 - 1, y - h - 1, w + 2, h + 3))
        pygame.draw.ellipse(surf, col, (x - w // 2, y - h, w, h + 1))
        pygame.draw.ellipse(surf, shade(col, 1.25), (x - w // 2 + 4, y - h + 2, w // 2, h // 3))
        pygame.draw.rect(surf, OUT, (x - 6, y - h // 2 - 2, 3, 5))
        pygame.draw.rect(surf, OUT, (x + 3, y - h // 2 - 2, 3, 5))
        top = y - h - 8
    else:
        fl = math.sin(t * 18 + x) * 7
        yy = y - 26 + int(math.sin(t * 5 + x) * 3)
        shadow(surf, x, y - 1, 18, 6, 60)
        col = (250, 250, 250) if flash else (92, 70, 118)
        for sx in (-1, 1):
            pygame.draw.polygon(surf, OUT, [(x, yy), (x + sx * 20, yy - 10 - fl), (x + sx * 24, yy + 4), (x + sx * 14, yy + 2), (x + sx * 8, yy + 8)])
            pygame.draw.polygon(surf, col, [(x + sx * 2, yy), (x + sx * 18, yy - 8 - fl), (x + sx * 21, yy + 3), (x + sx * 13, yy + 1), (x + sx * 8, yy + 6)])
        pygame.draw.circle(surf, OUT, (x, yy), 8)
        pygame.draw.circle(surf, shade(col, .8), (x, yy), 7)
        pygame.draw.polygon(surf, OUT, [(x - 6, yy - 5), (x - 4, yy - 12), (x - 1, yy - 6)])
        pygame.draw.polygon(surf, OUT, [(x + 6, yy - 5), (x + 4, yy - 12), (x + 1, yy - 6)])
        pygame.draw.rect(surf, (255, 90, 80), (x - 4, yy - 2, 2, 2))
        pygame.draw.rect(surf, (255, 90, 80), (x + 2, yy - 2, 2, 2))
        top = yy - 16
    if frac < 1.0:
        pygame.draw.rect(surf, (30, 20, 20), (x - 12, top - 4, 24, 5))
        pygame.draw.rect(surf, (220, 60, 50), (x - 11, top - 3, int(22 * frac), 3))

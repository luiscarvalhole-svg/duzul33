"""Desenho do mundo: terreno e objetos por código; plantas e itens usam os PNGs de pixel art em assets/ quando existem."""
import math
import random

import pygame

from . import assets
from . import world as W
from .config import TILE as T

_shadow_cache = {}
_glow = None

PAL = {
    "primavera": dict(plaza=(226, 212, 182), grass=((108, 182, 82), (102, 174, 76)), forest=(64, 128, 58), sand=(226, 208, 152),
                      rock=(130, 130, 138), road=(156, 146, 132), water=(58, 128, 200), tuft=(76, 148, 58),
                      leaf=((78, 158, 68), (104, 184, 88), (60, 132, 56)), flores=True),
    "verao": dict(plaza=(230, 214, 180), grass=((92, 168, 62), (86, 160, 56)), forest=(52, 116, 48), sand=(232, 212, 150),
                  rock=(132, 132, 140), road=(160, 148, 130), water=(52, 124, 206), tuft=(64, 140, 48),
                  leaf=((60, 146, 56), (84, 170, 70), (44, 118, 46)), flores=True),
    "outono": dict(plaza=(214, 198, 166), grass=((170, 152, 76), (162, 144, 70)), forest=(130, 110, 56), sand=(220, 200, 146),
                   rock=(126, 124, 128), road=(150, 138, 122), water=(54, 112, 176), tuft=(150, 116, 50),
                   leaf=((214, 126, 40), (196, 84, 34), (168, 60, 30)), flores=False),
    "inverno": dict(plaza=(222, 224, 230), grass=((232, 240, 246), (224, 234, 242)), forest=(205, 222, 230), sand=(224, 222, 212),
                    rock=(176, 178, 190), road=(190, 190, 196), water=(96, 150, 200), tuft=(200, 214, 226),
                    leaf=((70, 110, 70), (90, 130, 90), (60, 96, 64)), flores=False),
}


def rnd(x, y, k=0):
    """Número pseudo-aleatório estável (0..1) a partir de coordenadas."""
    n = (x * 374761393 + y * 668265263 + k * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def shadow(surf, cx, cy, w, h, alpha=60):
    key = (w, h, alpha)
    s = _shadow_cache.get(key)
    if s is None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, w, h))
        _shadow_cache[key] = s
    surf.blit(s, (int(cx - w // 2), int(cy - h // 2)))


def shade(col, f):
    return tuple(max(0, min(255, int(v * f))) for v in col)


# ----------------------------------------------------------------- terreno
def _draw_paved(surf, world, x, y, g, P):
    """Rua de pedras irregulares ou praça de lajotas, com meio-fio onde encosta na grama."""
    px, py = x * T, y * T
    plaza = False                                    # a praça usa o mesmo calçamento das ruas do resto do jogo
    base = P["road"]
    pygame.draw.rect(surf, shade(base, .8), (px, py, T, T))                      # rejunte
    if plaza:
        for j in range(2):
            for i in range(2):
                f = 1.04 if (x * 2 + i + y * 2 + j) % 2 == 0 else .95
                f += (rnd(x * 2 + i, y * 2 + j, 4) - .5) * .06
                pygame.draw.rect(surf, shade(base, f), (px + i * 16 + 1, py + j * 16 + 1, 14, 14), border_radius=2)
                pygame.draw.line(surf, shade(base, 1.12), (px + i * 16 + 2, py + j * 16 + 2), (px + i * 16 + 13, py + j * 16 + 2), 1)
    else:
        for row in range(3):                                                      # tijolos desencontrados
            off = 8 if (row + y) % 2 else 0
            for k in range(-1, 3):
                bx = px + off + k * 16
                f = .9 + .16 * rnd(x * 4 + k + 8, y * 3 + row, 4)
                x0, x1 = max(px, bx + 1), min(px + T, bx + 15)
                if x1 > x0:
                    pygame.draw.rect(surf, shade(base, f), (x0, py + row * 10 + 1, x1 - x0, 9), border_radius=2)
    # meio-fio nas bordas que dão para grama/areia/etc.
    kinds = (W.ROAD, W.PLAZA)
    light = shade(base, 1.18)
    for dx, dy, rect, hl in ((0, -1, (px, py, T, 3), ((px, py + 3), (px + T - 1, py + 3))),
                             (0, 1, (px, py + T - 3, T, 3), ((px, py + T - 4), (px + T - 1, py + T - 4))),
                             (-1, 0, (px, py, 3, T), ((px + 3, py), (px + 3, py + T - 1))),
                             (1, 0, (px + T - 3, py, 3, T), ((px + T - 4, py), (px + T - 4, py + T - 1)))):
        nx, ny = x + dx, y + dy
        if world.in_bounds(nx, ny) and world.ground[ny][nx] not in (W.ROAD, W.PLAZA):
            pygame.draw.rect(surf, shade(base, .5), rect)
            pygame.draw.line(surf, light, hl[0], hl[1], 1)


def _draw_water(surf, world, x, y, P):
    """Água em pixel art: mais clara perto da margem, mais escura no fundo, com ondinhas e espuma na borda."""
    px, py = x * T, y * T
    base = P["water"]
    near = 0                                           # quanto de terra existe por perto (profundidade)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            nx, ny = x + dx, y + dy
            if world.in_bounds(nx, ny) and world.ground[ny][nx] != W.WATER:
                near += 1
    k = min(1.12, 0.9 + near * 0.03)
    col = shade(base, k)
    pygame.draw.rect(surf, col, (px, py, T, T))
    dark, light = shade(col, .88), shade(col, 1.22)
    for i in range(2):                                 # faixas de onda em blocos de pixels
        ox, oy = int(rnd(x, y, 10 + i) * 18), int(rnd(x, y, 12 + i) * 24) + 3
        pygame.draw.rect(surf, light, (px + ox, py + oy, 8, 2))
        pygame.draw.rect(surf, light, (px + ox + 8, py + oy + 2, 4, 2))
        pygame.draw.rect(surf, dark, (px + ox + 2, py + oy + 5, 8, 2))
    if rnd(x, y, 15) < .25:
        pygame.draw.rect(surf, light, (px + int(rnd(x, y, 16) * 22) + 2, py + int(rnd(x, y, 17) * 22) + 2, 2, 2))
    foam = (232, 244, 252)
    for dx, dy, rect in ((0, -1, (px, py, T, 3)), (0, 1, (px, py + T - 3, T, 3)), (-1, 0, (px, py, 3, T)), (1, 0, (px + T - 3, py, 3, T))):
        nx, ny = x + dx, y + dy
        if world.in_bounds(nx, ny) and world.ground[ny][nx] != W.WATER:
            pygame.draw.rect(surf, shade(base, 1.35), rect)
            for j in range(0, T, 6):                   # espuma salpicada
                if rnd(x + dx * 3, y + dy * 3, j) < .6:
                    a, b = ((px + j, rect[1] + (3 if dy < 0 else -2 if dy > 0 else 0)), (px + j + 3, 0))[0], None
                    if dy:
                        pygame.draw.rect(surf, foam, (px + j, rect[1] + (2 if dy < 0 else -1), 4, 2))
                    else:
                        pygame.draw.rect(surf, foam, (rect[0] + (2 if dx < 0 else -1), py + j, 2, 4))


def render_terrain(world, season):
    P = PAL[season]
    surf = pygame.Surface((world.w * T, world.h * T))
    for y in range(world.h):
        for x in range(world.w):
            g = world.ground[y][x]
            px, py = x * T, y * T
            r = rnd(x, y)
            if g in (W.GRASS, W.FOREST):
                vi = 3 if (g == W.GRASS and P["flores"] and rnd(x, y, 20) < 0.06) else int(rnd(x, y, 3) * 3)
                sp = assets.load(f"sprites/terrain/{'grass' if g == W.GRASS else 'forest'}_{season}_{(vi + x // 3 + y // 5) % 3 if vi < 3 else 3}.png", (T, T))
                if sp is not None:                                        # gramado em pixel art (assets/sprites/terrain)
                    surf.blit(sp, (px, py))
                else:
                    base = P["grass"][(x + y) % 2] if g == W.GRASS else P["forest"]
                    col = tuple(max(0, min(255, v + int((r - 0.5) * 12))) for v in base)
                    pygame.draw.rect(surf, col, (px, py, T, T))
                    for i in range(3):
                        ox, oy = int(rnd(x, y, i + 1) * (T - 8)) + 4, int(rnd(x, y, i + 7) * (T - 10)) + 8
                        pygame.draw.line(surf, P["tuft"], (px + ox, py + oy), (px + ox - 2, py + oy - 5), 1)
                        pygame.draw.line(surf, P["tuft"], (px + ox, py + oy), (px + ox + 2, py + oy - 4), 1)
                    if P["flores"] and g == W.GRASS and rnd(x, y, 20) < 0.06:
                        fx, fy = px + int(rnd(x, y, 21) * 24) + 4, py + int(rnd(x, y, 22) * 24) + 4
                        c = [(255, 255, 255), (255, 170, 200), (255, 230, 90), (190, 150, 255)][int(rnd(x, y, 23) * 4)]
                        pygame.draw.circle(surf, c, (fx, fy), 2)
                        pygame.draw.circle(surf, (240, 190, 60), (fx, fy), 1)
            elif g == W.SAND:
                pygame.draw.rect(surf, tuple(max(0, v + int((r - .5) * 10)) for v in P["sand"]), (px, py, T, T))
                for i in range(4):
                    pygame.draw.circle(surf, shade(P["sand"], .88), (px + int(rnd(x, y, i + 3) * 28) + 2,
                                                                      py + int(rnd(x, y, i + 9) * 28) + 2), 1)
            elif g == W.ROCK:
                pygame.draw.rect(surf, tuple(max(0, v + int((r - .5) * 14)) for v in P["rock"]), (px, py, T, T))
                a = (px + int(rnd(x, y, 1) * 20) + 4, py + int(rnd(x, y, 2) * 20) + 4)
                pygame.draw.line(surf, shade(P["rock"], .78), a, (a[0] + 9, a[1] + 6), 1)
                pygame.draw.line(surf, shade(P["rock"], .78), (a[0] + 9, a[1] + 6), (a[0] + 6, a[1] + 14), 1)
                pygame.draw.circle(surf, shade(P["rock"], 1.12), (px + int(rnd(x, y, 5) * 24) + 4, py + 6), 3)
            elif g in (W.ROAD, W.PLAZA):
                _draw_paved(surf, world, x, y, g, P)
            else:
                _draw_water(surf, world, x, y, P)
    return surf


def draw_water_shimmer(screen, world, cam, t, rng_tiles):
    x0, y0, x1, y1 = rng_tiles
    for y in range(y0, y1):
        for x in range(x0, x1):
            if world.ground[y][x] == W.WATER and rnd(x, y, 5) < 0.45:
                ph = t * 1.6 + rnd(x, y, 6) * 6.28
                a = int(40 + 40 * math.sin(ph))
                px = x * T - cam[0] + int(rnd(x, y, 7) * 14) + 4 + int(math.sin(ph) * 3)
                py = y * T - cam[1] + int(rnd(x, y, 8) * 18) + 6
                pygame.draw.line(screen, (120 + a, 170 + a // 2, 235), (px, py), (px + 10, py), 2)


# ----------------------------------------------------------------- natureza
def draw_tree(screen, cx, by, season, v, t):
    P = PAL[season]
    sway = math.sin(t * 1.5 + cx * 0.05 + v) * 1.5
    shadow(screen, cx, by - 2, 44, 14)
    spr = assets.load(f"sprites/trees/tree_{season}_{v % 2}.png", (80, 80))
    if spr is not None:                                               # árvore em pixel art (assets/sprites/trees)
        screen.blit(spr, (int(cx - 40 + sway * .6), by - 78))
        return
    pygame.draw.rect(screen, (100, 70, 44), (cx - 5, by - 28, 10, 28))
    pygame.draw.rect(screen, (74, 50, 30), (cx + 1, by - 28, 4, 28))
    if season == "inverno":
        for dx, dy in ((-14, -48), (12, -50), (0, -58), (-8, -40), (9, -40)):
            pygame.draw.line(screen, (80, 58, 40), (cx, by - 30), (cx + dx + sway, by + dy), 3)
            pygame.draw.circle(screen, (250, 252, 255), (int(cx + dx + sway), by + dy), 5)
        return
    c0, c1, c2 = P["leaf"]
    s = 22 + (v % 2) * 3
    pygame.draw.circle(screen, c2, (int(cx + sway * .3), by - 46), s + 2)
    pygame.draw.circle(screen, c0, (int(cx - 9 + sway * .6), by - 52), s - 4)
    pygame.draw.circle(screen, c1, (int(cx + 8 + sway), by - 58), s - 7)
    pygame.draw.circle(screen, shade(c1, 1.2), (int(cx - 6 + sway), by - 62), 6)


def draw_rock(screen, cx, by, season, v):
    P = PAL[season]
    shadow(screen, cx, by - 2, 40, 12)
    base = P["rock"] if season != "inverno" else (150, 152, 164)
    pts = [(cx - 15, by), (cx - 11, by - 14), (cx + 3, by - 20), (cx + 14, by - 9), (cx + 16, by)]
    pygame.draw.polygon(screen, base, pts)
    pygame.draw.polygon(screen, shade(base, 1.2), [(cx - 11, by - 14), (cx + 3, by - 20), (cx + 1, by - 9)])
    pygame.draw.polygon(screen, shade(base, .78), [(cx + 16, by), (cx + 14, by - 9), (cx + 5, by - 5), (cx + 7, by)])
    if season == "inverno":
        pygame.draw.polygon(screen, (250, 252, 255), [(cx - 9, by - 15), (cx + 3, by - 20), (cx + 9, by - 14), (cx, by - 12)])


def draw_bush(screen, cx, by, season, v, t):
    P = PAL[season]
    sw = math.sin(t * 2 + cx * .1) * 1
    shadow(screen, cx, by - 1, 30, 10)
    spr = assets.load(f"sprites/trees/bush_{season}_{v % 2}.png", (48, 48))
    if spr is not None:
        screen.blit(spr, (int(cx - 24 + sw), by - 44))
        return
    c0, c1, c2 = P["leaf"]
    if season == "inverno":
        c0, c1, c2 = (120, 100, 80), (150, 130, 100), (100, 80, 64)
    pygame.draw.circle(screen, c2, (int(cx - 7 + sw), by - 8), 9)
    pygame.draw.circle(screen, c2, (int(cx + 8 + sw), by - 8), 9)
    pygame.draw.circle(screen, c0, (int(cx + sw), by - 12), 11)
    pygame.draw.circle(screen, c1, (int(cx - 3 + sw), by - 15), 5)
    if season == "inverno":
        pygame.draw.circle(screen, (250, 252, 255), (int(cx + sw), by - 20), 6)
    elif v % 2 == 0:
        for dx, dy in ((-6, -8), (5, -14), (7, -6)):
            pygame.draw.circle(screen, (210, 50, 70) if season != "outono" else (120, 60, 140), (cx + dx, by + dy), 2)


# ----------------------------------------------------------------- plantações
def draw_crop(screen, c, stage, cx, by, t):
    cx, by = int(cx), int(by)
    shadow(screen, cx, by, 24, 8, 45)
    sw = math.sin(t * 2.2 + cx * .07) * 1.5
    leaf, fruit = tuple(c.get("folha", (70, 160, 60))), tuple(c["cor"])
    dark = shade(leaf, .72)
    spr = assets.plant_sprite(c["id"], min(3, max(0, stage)))
    if spr is not None:                                               # pixel art em PNG (assets/sprites/plants)
        screen.blit(spr, (cx - 16 + (int(sw) if stage >= 2 else 0), by - 29))
        if stage == 3 and math.sin(t * 5 + cx) > .2:
            pygame.draw.line(screen, (255, 250, 170), (cx + 8, by - 24), (cx + 14, by - 24), 2)
            pygame.draw.line(screen, (255, 250, 170), (cx + 11, by - 27), (cx + 11, by - 21), 2)
        return
    if stage == 0:
        for dx, dy in ((-6, 2), (5, 3)):
            pygame.draw.circle(screen, (92, 60, 34), (cx + dx, by + dy), 3)
        pygame.draw.circle(screen, (150, 108, 66), (cx, by - 1), 4)
        return
    if stage == 1:
        pygame.draw.line(screen, leaf, (cx, by), (cx + sw * .5, by - 10), 2)
        pygame.draw.ellipse(screen, leaf, (cx - 8 + int(sw * .5), by - 14, 9, 5))
        pygame.draw.ellipse(screen, shade(leaf, 1.15), (cx + int(sw * .5), by - 16, 9, 5))
        return
    big = stage == 3
    sc = 1.0 if big else .72
    f = c["forma"]
    if f == "raiz":
        for a in (-.9, -.45, 0, .45, .9):
            ex, ey = cx + math.sin(a) * 15 * sc + sw, by - math.cos(a) * 17 * sc - 2
            pygame.draw.line(screen, leaf, (cx, by - 2), (ex, ey), 3)
            pygame.draw.circle(screen, shade(leaf, 1.2), (int(ex), int(ey)), 2)
        if big:
            pygame.draw.ellipse(screen, fruit, (cx - 7, by - 6, 14, 9))
            pygame.draw.ellipse(screen, shade(fruit, 1.25), (cx - 4, by - 5, 6, 3))
    elif f == "folha":
        for dx, dy, w_, h_ in ((-9, -4, 12, 8), (3, -4, 12, 8), (-5, -9, 12, 8), (-3, 0, 10, 6)):
            pygame.draw.ellipse(screen, leaf, (cx + int(dx * sc), by + int(dy * sc) - 4, int(w_ * sc), int(h_ * sc)))
        if big:
            pygame.draw.circle(screen, fruit, (cx, by - 9), 7)
            pygame.draw.circle(screen, shade(fruit, 1.15), (cx - 2, by - 11), 3)
    elif f == "arbusto":
        for dx, dy in ((-9, -5), (9, -5), (0, -12), (0, -3)):
            pygame.draw.circle(screen, leaf, (cx + int(dx * sc), by + int(dy * sc)), int(8 * sc))
        for dx, dy in ((-9, -8), (8, -10), (0, -4), (3, -16)):
            if big:
                pygame.draw.circle(screen, fruit, (cx + dx, by + dy), 4)
                pygame.draw.circle(screen, shade(fruit, 1.35), (cx + dx - 1, by + dy - 1), 1)
            else:
                pygame.draw.circle(screen, (240, 240, 230), (cx + dx, by + dy), 1)
    elif f == "haste":
        hgt = int(36 * sc)
        pygame.draw.line(screen, dark, (cx, by), (cx + sw, by - hgt), 3)
        for yo, side in ((-9, -1), (-17, 1), (-25, -1)):
            if -yo < hgt:
                pygame.draw.line(screen, leaf, (cx, by + yo), (cx + side * 14 * sc + sw, by + yo - 8), 3)
        top = (cx + int(sw), by - hgt)
        if c["id"] == "girassol":
            if big:
                for i in range(10):
                    a = i * math.tau / 10
                    pygame.draw.circle(screen, fruit, (int(top[0] + math.cos(a) * 10), int(top[1] + math.sin(a) * 10)), 5)
                pygame.draw.circle(screen, (110, 70, 30), top, 7)
            else:
                pygame.draw.circle(screen, leaf, top, 5)
        elif c["id"] == "milho":
            if big:
                pygame.draw.ellipse(screen, fruit, (top[0] + 1, top[1] + 8, 8, 15))
                pygame.draw.ellipse(screen, shade(fruit, 1.3), (top[0] + 3, top[1] + 10, 3, 9))
                pygame.draw.line(screen, (220, 190, 80), top, (top[0] + 5, top[1] - 7), 2)
        else:
            if big:
                for i in range(3):
                    pygame.draw.ellipse(screen, fruit, (top[0] - 3 + (i - 1) * 4, top[1] - 6, 4, 11))
    elif f == "trepadeira":
        for dx, dy, w_, h_ in ((-22, -12, 18, 10), (4, -13, 18, 10), (-8, -20, 16, 9)):
            pygame.draw.ellipse(screen, leaf, (cx + int(dx * sc), by + int(dy * sc), int(w_ * sc), int(h_ * sc)))
        if big:
            if c["id"] == "uva":
                for i in range(6):
                    pygame.draw.circle(screen, fruit, (cx - 6 + (i % 3) * 6, by - 6 + (i // 3) * 6), 4)
            elif c["id"] in ("pepino", "abobrinha"):
                pygame.draw.ellipse(screen, fruit, (cx - 11, by - 8, 22, 9))
            else:
                pygame.draw.ellipse(screen, fruit, (cx - 13, by - 17, 26, 19))
                pygame.draw.ellipse(screen, shade(fruit, .75), (cx - 13, by - 17, 26, 19), 2)
                for dx in (-6, 0, 6):
                    pygame.draw.line(screen, shade(fruit, .75), (cx + dx, by - 16), (cx + dx, by - 1), 2)
        else:
            pygame.draw.ellipse(screen, fruit, (cx - 6, by - 8, 12, 8))
    elif f == "flor":
        pygame.draw.line(screen, leaf, (cx, by), (cx + sw, by - int(22 * sc)), 3)
        pygame.draw.ellipse(screen, leaf, (cx - 9, by - 10, 9, 5))
        top = (cx + int(sw), by - int(22 * sc))
        if big:
            for i in range(6):
                a = i * math.tau / 6
                pygame.draw.circle(screen, fruit, (int(top[0] + math.cos(a) * 6), int(top[1] + math.sin(a) * 6)), 4)
            pygame.draw.circle(screen, (250, 220, 90), top, 3)
        else:
            pygame.draw.circle(screen, shade(leaf, 1.2), top, 3)
    else:  # vagem
        pygame.draw.line(screen, dark, (cx - 6, by), (cx - 3 + sw, by - int(30 * sc)), 2)
        pygame.draw.line(screen, dark, (cx + 6, by), (cx + 3 + sw, by - int(30 * sc)), 2)
        for dy in (-8, -16, -24):
            pygame.draw.ellipse(screen, leaf, (cx - 4, by + int(dy * sc), 8, 5))
        if big:
            for dx, dy in ((-9, -12), (7, -18), (-8, -22)):
                pygame.draw.ellipse(screen, fruit, (cx + dx, by + dy, 4, 11))
    if big and math.sin(t * 5 + cx) > .2:
        pygame.draw.line(screen, (255, 250, 170), (cx + 8, by - 24), (cx + 14, by - 24), 2)
        pygame.draw.line(screen, (255, 250, 170), (cx + 11, by - 27), (cx + 11, by - 21), 2)


def draw_soil(screen, px, py, wet, fert):
    col = (92, 62, 40) if wet else (140, 98, 60)
    pygame.draw.rect(screen, col, (px, py, T, T))
    pygame.draw.rect(screen, shade(col, .8), (px, py, T, T), 1)
    for i in range(1, 4):
        pygame.draw.line(screen, shade(col, .82), (px + 3, py + i * 8), (px + T - 4, py + i * 8), 2)
    if fert:
        for dx, dy in ((6, 7), (20, 14), (12, 24)):
            pygame.draw.circle(screen, (70, 130, 190) if fert == "rapido" else (60, 40, 24), (px + dx, py + dy), 2)


# ----------------------------------------------------------------- clima e noite
def new_weather_particles(kind, w, h):
    n = {"chuva": 160, "tempestade": 260, "neve": 120}.get(kind, 0)
    return [[random.uniform(0, w), random.uniform(0, h), random.uniform(.7, 1.3), random.uniform(0, 6.28)] for _ in range(n)]


def update_weather_particles(ps, kind, dt, w, h):
    for p in ps:
        if kind == "neve":
            p[1] += 60 * p[2] * dt
            p[0] += math.sin(p[3] + p[1] * .02) * 20 * dt
        else:
            p[1] += (620 if kind == "chuva" else 800) * p[2] * dt
            p[0] -= (80 if kind == "chuva" else 220) * dt
        if p[1] > h or p[0] < -10:
            p[0], p[1] = random.uniform(0, w + 100), -10


def draw_weather(screen, kind, ps, flash):
    if kind in ("chuva", "tempestade"):
        for x, y, s, _ in ps:
            pygame.draw.line(screen, (176, 196, 232), (x, y), (x - 3 * s, y + 12 * s), 1)
    elif kind == "neve":
        for x, y, s, _ in ps:
            pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 2 if s > 1 else 1)
    if flash > 0:
        ov = pygame.Surface(screen.get_size())
        ov.fill((255, 255, 255))
        ov.set_alpha(int(150 * flash))
        screen.blit(ov, (0, 0))


def _glow_surface():
    global _glow
    if _glow is None:
        _glow = pygame.Surface((120, 120))
        for r in range(60, 0, -2):
            k = (1 - r / 60) ** 1.4
            pygame.draw.circle(_glow, (int(110 * k), int(90 * k), int(40 * k)), (60, 60), r)
    return _glow


def draw_night(screen, overlay, dark, glows):
    if dark <= 0.01:
        return
    overlay.fill((10, 14, 60, int(dark * 200)))
    screen.blit(overlay, (0, 0))
    if dark > .2:
        g = _glow_surface()
        for x, y in glows:
            screen.blit(g, (int(x - 60), int(y - 60)), special_flags=pygame.BLEND_RGB_ADD)

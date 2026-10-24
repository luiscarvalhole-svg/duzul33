"""Desenho do interior da casa (tudo por código). O cômodo é desenhado em 512x320 e ampliado 2x na tela."""
import math

import pygame

from . import gfx, interior
from .config import TILE as T
from .gfx import shade, shadow

OUT = (46, 32, 24)
WOOD, WOOD_D, WOOD_L = (150, 106, 64), (110, 76, 46), (190, 142, 90)
ROOM_W, ROOM_H = interior.W * T, interior.H * T


def _r(s, col, rect, br=0, out=True):
    """Retângulo com contorno escuro (dá volume, tira o aspecto 'chapado')."""
    if out:
        pygame.draw.rect(s, OUT, pygame.Rect(rect).inflate(2, 2), border_radius=br + 1)
    pygame.draw.rect(s, col, rect, border_radius=br)


def _wall_and_floor(s, t, dark, weather):
    # parede de trás: reboco claro, lambri de madeira embaixo e rodapé
    pygame.draw.rect(s, (238, 224, 190), (0, 0, ROOM_W, 64))
    for x in range(0, ROOM_W, 16):
        pygame.draw.line(s, (228, 212, 176), (x, 0), (x, 40), 1)
    pygame.draw.rect(s, (176, 130, 84), (0, 40, ROOM_W, 24))
    for x in range(0, ROOM_W, 24):
        pygame.draw.line(s, (150, 106, 64), (x, 42), (x, 62), 1)
    pygame.draw.rect(s, (120, 84, 50), (0, 38, ROOM_W, 4))
    pygame.draw.rect(s, (96, 66, 40), (0, 62, ROOM_W, 4))
    pygame.draw.rect(s, (60, 42, 28), (0, 0, ROOM_W, 4))           # viga do teto
    # piso de tábuas
    for i, y in enumerate(range(66, ROOM_H, 16)):
        base = (176, 128, 80) if i % 2 == 0 else (168, 120, 74)
        pygame.draw.rect(s, base, (0, y, ROOM_W, 16))
        pygame.draw.line(s, (130, 90, 54), (0, y), (ROOM_W, y), 1)
        off = (i * 53) % 96
        for x in range(-off, ROOM_W, 96):
            pygame.draw.line(s, (140, 98, 58), (x, y), (x, y + 15), 1)
    pygame.draw.rect(s, (120, 84, 50), (0, 66, 3, ROOM_H))
    pygame.draw.rect(s, (120, 84, 50), (ROOM_W - 3, 66, 3, ROOM_H))
    # janela com céu que muda conforme a hora e o clima
    wx, wy, ww, wh = 168, 8, 48, 40
    sky = _sky_color(dark)
    _r(s, (110, 76, 46), (wx - 4, wy - 4, ww + 8, wh + 8), 3)
    pygame.draw.rect(s, sky, (wx, wy, ww, wh))
    if dark > 0.5:
        for sx, sy in ((wx + 8, wy + 8), (wx + 30, wy + 14), (wx + 18, wy + 26), (wx + 38, wy + 6)):
            pygame.draw.circle(s, (250, 250, 220), (sx, sy), 1)
        pygame.draw.circle(s, (240, 240, 210), (wx + 36, wy + 12), 5)
        pygame.draw.circle(s, sky, (wx + 39, wy + 10), 4)
    elif weather in ("chuva", "tempestade"):
        pygame.draw.rect(s, (130, 140, 160), (wx, wy, ww, 16))
        for k in range(8):
            xx = wx + 4 + k * 6
            yy = wy + 14 + int((t * 60 + k * 9) % 24)
            pygame.draw.line(s, (170, 200, 240), (xx, yy), (xx - 2, yy + 5), 1)
    else:
        pygame.draw.circle(s, (255, 236, 150), (wx + 12, wy + 11), 6)
        pygame.draw.ellipse(s, (255, 255, 255), (wx + 22, wy + 8, 20, 8))
    pygame.draw.line(s, (110, 76, 46), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 3)
    pygame.draw.line(s, (110, 76, 46), (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 3)
    pygame.draw.rect(s, (200, 70, 70), (wx - 6, wy - 2, 11, wh - 4), border_radius=3)         # cortinas
    pygame.draw.rect(s, (200, 70, 70), (wx + ww - 5, wy - 2, 11, wh - 4), border_radius=3)
    pygame.draw.rect(s, (150, 40, 44), (wx - 6, wy - 2, 11, 4))
    pygame.draw.rect(s, (150, 40, 44), (wx + ww - 5, wy - 2, 11, 4))
    pygame.draw.rect(s, WOOD_L, (wx - 7, wy + wh + 2, ww + 14, 4))                           # peitoril
    _r(s, (220, 120, 140), (wx + 6, wy + wh - 4, 8, 6), 1)
    pygame.draw.circle(s, (80, 160, 70), (wx + 10, wy + wh - 8), 4)
    # quadros e relógio na parede
    _r(s, (110, 76, 46), (48, 12, 38, 26), 2)
    pygame.draw.rect(s, (120, 170, 210), (51, 15, 32, 20))
    pygame.draw.polygon(s, (90, 150, 80), [(51, 35), (63, 22), (74, 35)])
    pygame.draw.polygon(s, (70, 130, 70), [(64, 35), (74, 25), (83, 35)])
    _r(s, (110, 76, 46), (392, 12, 28, 22), 2)
    pygame.draw.rect(s, (240, 200, 120), (395, 15, 22, 16))
    pygame.draw.circle(s, (210, 90, 90), (406, 23), 4)
    cx, cy = 300, 22
    pygame.draw.circle(s, OUT, (cx, cy), 11)
    pygame.draw.circle(s, (250, 244, 226), (cx, cy), 9)
    ang = t * 0.2
    pygame.draw.line(s, OUT, (cx, cy), (cx + math.cos(ang) * 6, cy + math.sin(ang) * 6), 2)
    pygame.draw.line(s, OUT, (cx, cy), (cx, cy - 7), 1)


def _sky_color(dark):
    if dark > 0.5:
        return (24, 30, 74)
    if dark > 0.15:
        return (240, 150, 100)
    return (134, 200, 244)


def _rug(s):
    x, y, w, h = 4 * T, 4 * T + 6, 6 * T, 4 * T - 12
    _r(s, (150, 52, 56), (x, y, w, h), 6)
    pygame.draw.rect(s, (230, 200, 130), (x + 8, y + 8, w - 16, h - 16), 3, border_radius=4)
    pygame.draw.rect(s, (92, 62, 120), (x + 16, y + 16, w - 32, h - 32), border_radius=3)
    for i in range(5):
        pygame.draw.polygon(s, (230, 200, 130), [(x + 40 + i * 24, y + h // 2), (x + 52 + i * 24, y + h // 2 - 8),
                                                   (x + 64 + i * 24, y + h // 2), (x + 52 + i * 24, y + h // 2 + 8)])
    for k in range(0, w, 8):
        pygame.draw.line(s, (240, 230, 200), (x + k, y), (x + k, y - 3), 1)
        pygame.draw.line(s, (240, 230, 200), (x + k, y + h), (x + k, y + h + 3), 1)


def _door_mat(s, t):
    x, y, w = interior.DOOR[0] * T, interior.DOOR[1] * T, interior.DOOR[2] * T
    pygame.draw.rect(s, (252, 226, 150), (x - 4, y + 22, w + 8, 10))                    # luz da rua entrando
    _r(s, (120, 84, 56), (x + 4, y + 8, w - 8, 14), 3)
    for k in range(x + 8, x + w - 8, 6):
        pygame.draw.line(s, (90, 62, 40), (k, y + 10), (k, y + 20), 1)
    pygame.draw.polygon(s, (255, 244, 190), [(x + w // 2 - 6, y + 27), (x + w // 2 + 6, y + 27), (x + w // 2, y + 31)])


# --------------------------------------------------------------------------- móveis
def _bed(s, px, py, w, h, t):
    _r(s, WOOD_D, (px, py - 18, w, 30), 3)                                   # cabeceira alta
    pygame.draw.rect(s, WOOD, (px + 3, py - 15, w - 6, 24), border_radius=2)
    _r(s, WOOD_D, (px + 2, py + 6, w - 4, h - 8), 4)
    _r(s, (244, 240, 230), (px + 6, py + 10, w - 12, 18), 4)                 # colchão/lençol
    for dx in (10, 56):                                                      # travesseiros
        _r(s, (255, 252, 246), (px + dx, py + 10, 28, 13), 5)
    _r(s, (70, 110, 190), (px + 6, py + 26, w - 12, h - 24), 4)               # cobertor
    for k in range(3):
        pygame.draw.line(s, (96, 140, 214), (px + 14, py + 32 + k * 8), (px + w - 14, py + 32 + k * 8), 2)
    pygame.draw.rect(s, (230, 220, 120), (px + 6, py + 26, w - 12, 4))
    _r(s, WOOD_D, (px + 2, py + h - 6, w - 4, 8), 2)                         # peseira


def _criado(s, px, py, w, h, t):
    _r(s, WOOD, (px + 2, py + 6, w - 4, h - 6), 2)
    pygame.draw.line(s, WOOD_D, (px + 4, py + 16), (px + w - 4, py + 16), 2)
    pygame.draw.circle(s, (240, 210, 100), (px + w // 2, py + 22), 2)
    pygame.draw.rect(s, (90, 90, 96), (px + 14, py - 2, 4, 8))                # abajur
    pygame.draw.polygon(s, (255, 226, 140), [(px + 7, py - 2), (px + 25, py - 2), (px + 21, py - 14), (px + 11, py - 14)])
    pygame.draw.polygon(s, OUT, [(px + 7, py - 2), (px + 25, py - 2), (px + 21, py - 14), (px + 11, py - 14)], 1)


def _lareira(s, px, py, w, h, t):
    _r(s, (130, 128, 136), (px - 4, py - 34, w + 8, h + 34), 3)
    for yy in range(py - 30, py + h, 8):
        for k, xx in enumerate(range(px - 2, px + w, 12)):
            pygame.draw.rect(s, (150, 148, 156) if (k + yy // 8) % 2 else (112, 110, 120), (xx + (yy // 8 % 2) * 4, yy, 11, 7), 1)
    _r(s, WOOD_D, (px - 8, py - 40, w + 16, 7), 2)                            # manto
    for cx in (px + 4, px + w - 8):                                           # velas
        pygame.draw.rect(s, (250, 244, 226), (cx, py - 52, 4, 11))
        pygame.draw.circle(s, (255, 190, 70), (cx + 2, py - 55), 2)
    _r(s, (30, 22, 20), (px + 8, py - 18, w - 16, h + 14), 6)
    for k in range(4):                                                        # chamas
        fx = px + 14 + k * 9
        hgt = 10 + int(abs(math.sin(t * 7 + k * 1.7)) * 9)
        pygame.draw.polygon(s, (240, 90, 30), [(fx - 5, py + h + 8), (fx, py + h + 8 - hgt), (fx + 5, py + h + 8)])
        pygame.draw.polygon(s, (255, 214, 80), [(fx - 3, py + h + 8), (fx, py + h + 8 - hgt + 5), (fx + 3, py + h + 8)])
    pygame.draw.rect(s, (90, 60, 40), (px + 10, py + h + 6, w - 20, 4))


def _estante(s, px, py, w, h, t):
    _r(s, WOOD_D, (px, py - 52, w, 84), 2)
    cols = [(190, 60, 60), (70, 110, 190), (230, 190, 80), (80, 150, 90), (160, 90, 170), (220, 130, 60)]
    for row in range(3):
        y0 = py - 48 + row * 26
        pygame.draw.rect(s, (96, 66, 40), (px + 3, y0 + 21, w - 6, 3))
        x = px + 5
        for k in range(7):
            bw, bh = 5 + (k * 3 + row) % 3, 14 + (k * 5 + row * 2) % 7
            pygame.draw.rect(s, cols[(k + row * 2) % len(cols)], (x, y0 + 21 - bh, bw, bh))
            pygame.draw.line(s, OUT, (x, y0 + 21 - bh), (x, y0 + 20), 1)
            x += bw + 2
        if row == 1:
            pygame.draw.circle(s, (230, 130, 90), (px + w - 10, y0 + 14), 5)       # vasinho
            pygame.draw.circle(s, (90, 170, 80), (px + w - 10, y0 + 8), 4)


def _cozinha(s, px, py, w, h, t):
    for k in range(3):                                                         # armários de cima
        _r(s, (214, 188, 140), (px + k * 32 + 1, py - 52, 30, 26), 2)
        pygame.draw.rect(s, WOOD_D, (px + k * 32 + 12, py - 40, 6, 2))
    pygame.draw.line(s, (100, 100, 108), (px + 4, py - 20), (px + w - 4, py - 20), 2)   # panelas penduradas
    for dx in (14, 48, 80):
        pygame.draw.circle(s, (120, 120, 130), (px + dx, py - 14), 5)
        pygame.draw.circle(s, OUT, (px + dx, py - 14), 5, 1)
    _r(s, (200, 170, 124), (px, py + 2, w, h - 2), 2)                            # balcão
    _r(s, (232, 226, 214), (px - 2, py - 8, w + 4, 11), 2)                       # tampo
    for k in range(3):
        pygame.draw.rect(s, WOOD_D, (px + 4 + k * 32, py + 8, 24, 20), 1)
    # fogão (esquerda)
    _r(s, (70, 70, 78), (px + 3, py - 12, 26, 6), 2)
    pygame.draw.ellipse(s, (30, 30, 34), (px + 6, py - 11, 8, 4))
    pygame.draw.ellipse(s, (30, 30, 34), (px + 18, py - 11, 8, 4))
    _r(s, (150, 60, 50), (px + 5, py - 22, 12, 11), 2)                            # panela
    for k in range(3):                                                           # vapor
        yy = py - 26 - int((t * 14 + k * 8) % 18)
        pygame.draw.circle(s, (240, 240, 244), (px + 9 + k * 3, yy), 2 + k % 2)
    # pia (meio)
    _r(s, (110, 130, 150), (px + 38, py - 9, 22, 7), 2)
    pygame.draw.rect(s, (130, 140, 150), (px + 48, py - 20, 3, 12))
    pygame.draw.rect(s, (130, 140, 150), (px + 48, py - 21, 8, 3))
    # tábua com pão (direita)
    _r(s, (214, 170, 110), (px + 70, py - 11, 22, 5), 2)
    pygame.draw.ellipse(s, (214, 160, 90), (px + 74, py - 17, 14, 8))


def _armario(s, px, py, w, h, t):
    _r(s, WOOD_D, (px, py - 52, w, 84), 3)
    pygame.draw.rect(s, WOOD, (px + 3, py - 49, w // 2 - 4, 78), border_radius=2)
    pygame.draw.rect(s, (184, 214, 232), (px + w // 2 + 1, py - 49, w // 2 - 4, 78), border_radius=2)       # espelho
    pygame.draw.line(s, (240, 250, 255), (px + w // 2 + 6, py - 40), (px + w // 2 + 14, py - 20), 2)
    pygame.draw.circle(s, (240, 210, 100), (px + w // 2 - 4, py - 10), 2)
    pygame.draw.line(s, OUT, (px + w // 2, py - 50), (px + w // 2, py + 28), 1)


_PAPEL = [False]


def _mesa(s, px, py, w, h, t):
    for dx in (4, w - 8):
        _r(s, WOOD_D, (px + dx, py + 10, 5, h - 6), 1)
    _r(s, WOOD, (px, py + 2, w, 20), 3)
    pygame.draw.rect(s, (214, 80, 80), (px + 3, py + 4, w - 6, 8))                # toalha xadrez
    for k in range(0, w - 6, 8):
        pygame.draw.rect(s, (244, 244, 244), (px + 3 + k, py + 4, 4, 8))
    pygame.draw.polygon(s, (214, 80, 80), [(px + 3, py + 12), (px + w - 3, py + 12), (px + w - 9, py + 20), (px + 9, py + 20)])
    _r(s, (240, 230, 210), (px + 8, py - 2, 22, 8), 3)                              # fruteira
    for dx, col in ((12, (220, 60, 50)), (19, (250, 200, 60)), (25, (120, 190, 80))):
        pygame.draw.circle(s, col, (px + dx, py - 4), 4)
    if _PAPEL[0]:                                                                    # relatório do ajudante sobre a mesa
        pygame.draw.rect(s, (60, 50, 40), (px + 33, py - 1, 22, 14))
        pygame.draw.rect(s, (252, 248, 232), (px + 34, py, 20, 12))
        for k in range(3):
            pygame.draw.line(s, (120, 100, 80), (px + 37, py + 3 + k * 3), (px + 51, py + 3 + k * 3))
        pygame.draw.rect(s, (214, 70, 60), (px + 46, py + 8, 5, 3))
    pygame.draw.rect(s, (250, 244, 226), (px + w - 14, py - 6, 4, 10))
    pygame.draw.circle(s, (255, 196, 80), (px + w - 12, py - 8), 2 + int(abs(math.sin(t * 6))))


def _cadeira(s, px, py, w, h, t):
    _r(s, WOOD_D, (px + 6, py - 14, 20, 22), 2)
    pygame.draw.rect(s, WOOD, (px + 9, py - 11, 14, 14))
    _r(s, WOOD, (px + 4, py + 6, 24, 10), 3)
    _r(s, (200, 70, 70), (px + 6, py + 4, 20, 6), 2)
    pygame.draw.rect(s, WOOD_D, (px + 6, py + 15, 4, 12))
    pygame.draw.rect(s, WOOD_D, (px + 22, py + 15, 4, 12))


def _sofa(s, px, py, w, h, t):
    _r(s, (60, 112, 130), (px, py - 8, w, 28), 6)                                   # encosto
    for k in range(3):
        _r(s, (84, 140, 160), (px + 6 + k * 29, py - 4, 26, 16), 4)
    _r(s, (50, 100, 120), (px - 4, py + 2, 12, 28), 4)                              # braços
    _r(s, (50, 100, 120), (px + w - 8, py + 2, 12, 28), 4)
    _r(s, (72, 128, 148), (px + 8, py + 14, w - 16, 14), 4)
    _r(s, (230, 190, 90), (px + 10, py + 4, 14, 12), 3)                              # almofada


def _bau(s, px, py, w, h, t):
    _r(s, (130, 86, 50), (px, py + 2, w, h - 2), 2)
    pygame.draw.rect(s, (150, 104, 62), (px + 2, py + 4, w - 4, 10))
    for dx in (6, w - 10):
        pygame.draw.rect(s, (80, 80, 90), (px + dx, py + 2, 4, h - 2))
    pygame.draw.rect(s, (240, 210, 100), (px + w // 2 - 3, py + 10, 6, 7))


def _planta(s, px, py, w, h, t):
    _r(s, (190, 100, 70), (px + 8, py + 12, 16, 18), 2)
    pygame.draw.rect(s, (150, 76, 52), (px + 6, py + 10, 20, 4))
    sway = math.sin(t * 1.5) * 2
    for dx, hgt in ((-6, 14), (0, 20), (6, 15), (-2, 12)):
        pygame.draw.ellipse(s, (70, 150, 70), (px + 14 + dx + sway * hgt / 20, py - hgt + 8, 8, hgt))
        pygame.draw.ellipse(s, (100, 180, 90), (px + 16 + dx + sway * hgt / 20, py - hgt + 10, 3, hgt - 6))


_DRAW = {"cama": _bed, "criado": _criado, "lareira": _lareira, "estante": _estante, "cozinha": _cozinha,
         "armario": _armario, "mesa": _mesa, "cadeira": _cadeira, "sofa": _sofa, "bau": _bau, "planta": _planta}


def glows():
    """Pontos de luz (em pixels do cômodo) para a noite: lareira, abajur e luz da porta."""
    return [(8 * T, 3 * T), (4 * T + 16, 2 * T + 8), (8 * T, 9 * T + 10)]


def draw_room(surf, t, dark, weather, draw_player, papel=False):
    """Desenha o cômodo inteiro em `surf` (ROOM_W x ROOM_H). draw_player(surf) é chamado na ordem de profundidade certa."""
    _PAPEL[0] = bool(papel)
    _wall_and_floor(surf, t, dark, weather)
    _rug(surf)
    _door_mat(surf, t)
    items = []
    for name, x, y, w, h, solid in interior.FURNITURE:
        fn = _DRAW.get(name)
        if fn:
            items.append(((y + h) * T, fn, x * T, y * T, w * T, h * T))
    items.append((-1, None, 0, 0, 0, 0))
    objs = sorted(items, key=lambda i: i[0])
    # o jogador entra na ordenação pela posição dele (guardada por quem chama em draw_player.sort_y)
    sort_y = getattr(draw_player, "sort_y", ROOM_H)
    done = False
    for key, fn, px, py, w, h in objs:
        if fn is None:
            continue
        if not done and key > sort_y:
            draw_player(surf)
            done = True
        shadow(surf, px + w // 2, py + h - 2, w - 4, 8, 50)
        fn(surf, px, py, w, h, t)
    if not done:
        draw_player(surf)

"""Interior da casa: planta do cômodo, móveis, colisão e interações (lógica pura, sem pygame).

As coordenadas são em blocos dentro do cômodo (16 x 10). As 2 primeiras linhas são a parede dos fundos.
"""
import math

W, H = 16, 10
FLOOR_TOP = 2.0
SPAWN = (8.5, 8.4)              # onde o jogador aparece ao entrar (perto da porta)
SLEEP_HOUR = 19                 # só dá para dormir a partir das 19h
SLEEP_MINUTES = (SLEEP_HOUR - 6) * 60

# (nome, x, y, largura, altura, bloqueia)
FURNITURE = [
    ("cama", 1, 2, 3, 2, True),
    ("criado", 4, 2, 1, 1, True),
    ("lareira", 7, 2, 2, 1, True),
    ("estante", 9, 2, 2, 1, True),
    ("cozinha", 11, 2, 3, 1, True),
    ("armario", 14, 2, 2, 1, True),
    ("mesa", 6, 5, 2, 2, True),
    ("cadeira", 5, 6, 1, 1, True),
    ("cadeira", 8, 6, 1, 1, True),
    ("sofa", 11, 5, 3, 1, True),
    ("bau", 1, 8, 2, 1, True),
    ("planta", 0, 5, 1, 1, True),
    ("planta", 15, 8, 1, 1, True),
    ("tapete", 4, 4, 6, 4, False),
]
DOOR = (7, 9, 2, 1)            # (x, y, w, h) da porta na parede de baixo


def solid_rects():
    return [(x, y, w, h) for n, x, y, w, h, b in FURNITURE if b]


def blocked(px, py):
    """True se os pés do jogador em (px, py) batem em móvel ou parede."""
    for ox, oy in ((-0.28, -0.12), (0.28, -0.12), (-0.28, 0.2), (0.28, 0.2)):
        x, y = px + ox, py + oy
        if x < 0.1 or x > W - 0.1 or y < FLOOR_TOP or y > H - 0.02:
            return True
        for rx, ry, rw, rh in solid_rects():
            if rx <= x < rx + rw and ry <= y < ry + rh:
                return True
    return False


def at_door(px, py):
    x, y, w, h = DOOR
    return x - 0.3 <= px <= x + w + 0.3 and py >= y + 0.1


def _dist(px, py, cx, cy):
    return math.hypot(px - cx, py - cy)


def nearest(px, py):
    """Interação mais próxima: ("dormir"|"sair", rótulo) ou None."""
    if _dist(px, py, 2.5, 4.3) < 2.0:
        return "dormir"
    if _dist(px, py, 12.5, 3.4) < 2.0:
        return "cozinhar"
    if _dist(px, py, 7.0, 7.7) < 1.4:
        return "mesa"
    if _dist(px, py, DOOR[0] + DOOR[2] / 2, DOOR[1] + 0.5) < 1.6:
        return "sair"
    return None


def can_sleep(minutes):
    return minutes >= SLEEP_MINUTES


def sleep_message(minutes):
    if can_sleep(minutes):
        return None
    falta = SLEEP_MINUTES - minutes
    return f"Ainda está cedo para dormir. Só a partir das {SLEEP_HOUR}h (faltam {int(falta // 60)}h{int(falta % 60):02d})."

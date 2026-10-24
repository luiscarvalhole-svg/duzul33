"""A mina: andares gerados por (semente, dia, andar). Lógica pura, sem pygame.

Cada andar é uma grade de W x H blocos com paredes na borda. Dentro há pedras e minérios; uma das pedras esconde a
escada para o andar de baixo. A escada para cima (saída) fica no canto inferior esquerdo.
"""
import math
import random

from . import data

W, H = 28, 16
SPAWN = (2.5, 13.5)
LADDER = (1, 13)                    # bloco da escada de saída
SAFE = 3.2                          # raio livre em volta da entrada

# (item, andar mínimo, nível mínimo da picareta, vida, peso de sorteio)
ORES = [("carvao", 1, 0, 3, 6), ("minerio_cobre", 1, 0, 3, 6), ("minerio_ferro", 5, 1, 4, 5),
        ("minerio_ouro", 12, 2, 5, 3), ("diamante", 20, 2, 6, 1)]
ORE_NEED = {o[0]: o[2] for o in ORES}
ORE_HP = {o[0]: o[3] for o in ORES}
ROCK_HP = 2


class Floor:
    def __init__(self, floor):
        self.floor = floor
        self.cells = {}             # (x, y) -> {"k": "rock"|"ore", "ore": id|None, "hp": int, "stairs": bool}
        self.stairs = None          # (x, y) da escada, depois de revelada
        self.rails = set()          # trilhos decorativos (blocos livres)
        self.lanterns = []          # colunas (x) das lanternas penduradas na viga da parede de cima
        self.enemies = []           # {"k": "slime"|"morcego", "x", "y", "hp", "max", "cd", "hurt"}


def available_starts(best):
    """Andares em que o elevador deixa começar: 1 e cada múltiplo de 5 já alcançado."""
    return [1] + [f for f in range(5, best + 1, 5)]


def generate(seed, day, floor):
    rng = random.Random(seed * 1009 + day * 97 + floor * 13)
    fl = Floor(floor)
    ores = [o for o in ORES if o[1] <= floor]
    dens = min(0.34, 0.20 + floor * 0.004)
    r = rng.randint(4, 12)                                 # trilhos de carrinho de minério atravessando o andar
    x0, x1 = rng.randint(3, 8), rng.randint(18, 25)
    for x in range(x0, x1 + 1):
        fl.rails.add((x, r))
    bx, r2 = rng.randint(x0 + 2, x1 - 2), r + rng.choice((-1, 1)) * rng.randint(3, 5)
    for y in range(min(r, r2), max(r, r2) + 1):
        if 1 <= y <= H - 2:
            fl.rails.add((bx, y))
    fl.lanterns = [6, 14, 22]
    free = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if math.hypot(x + .5 - SPAWN[0], y + .5 - SPAWN[1]) < SAFE:
                continue
            free.append((x, y))
            if (x, y) in fl.rails or rng.random() > dens:
                continue
            if rng.random() < 0.28 + min(0.2, floor * 0.01):
                tot = sum(o[4] for o in ores)
                r, acc = rng.random() * tot, 0
                for o in ores:
                    acc += o[4]
                    if r <= acc:
                        fl.cells[(x, y)] = {"k": "ore", "ore": o[0], "hp": o[3], "stairs": False}
                        break
            else:
                fl.cells[(x, y)] = {"k": "rock", "ore": None, "hp": ROCK_HP, "stairs": False}
    rocks = [p for p, c in fl.cells.items() if c["k"] == "rock" and p[0] > W // 2]
    if not rocks:
        p = max(free, key=lambda q: q[0])
        fl.cells[p] = {"k": "rock", "ore": None, "hp": ROCK_HP, "stairs": False}
        rocks = [p]
    fl.cells[rng.choice(rocks)]["stairs"] = True
    far = [p for p in free if math.hypot(p[0] + .5 - SPAWN[0], p[1] + .5 - SPAWN[1]) > 7 and p not in fl.cells]
    for _ in range(min(len(far), min(10, 3 + floor // 3))):
        x, y = rng.choice(far)
        bat = floor >= 3 and rng.random() < 0.4
        hp = (3 + floor // 3) if bat else (4 + floor // 2)
        fl.enemies.append({"k": "morcego" if bat else "slime", "x": x + .5, "y": y + .5, "hp": hp, "max": hp, "cd": 0.0,
                           "hurt": 0.0, "vx": 0.0, "vy": 0.0})
    return fl


def blocked(fl, px, py):
    for ox, oy in ((-0.28, -0.12), (0.28, -0.12), (-0.28, 0.2), (0.28, 0.2)):
        x, y = px + ox, py + oy
        if x < 1 or y < 1 or x >= W - 1 or y >= H - 1:
            return True
        if (int(x), int(y)) in fl.cells:
            return True
    return False


def near_ladder(px, py):
    return math.hypot(px - (LADDER[0] + .5), py - (LADDER[1] + .5)) < 1.5


def near_stairs(fl, px, py):
    return fl.stairs is not None and math.hypot(px - (fl.stairs[0] + .5), py - (fl.stairs[1] + .5)) < 1.2


def _drops(state, cell, rng):
    mult = 2 if rng.random() < 0.05 * state.level("mineracao") else 1
    if cell["k"] == "ore":
        return [(cell["ore"], mult)]
    out = [("pedra", rng.randint(1, 2) * mult)]
    if rng.random() < 0.08:
        out.append(("carvao", 1))
    return out


def hit(state, fl, tx, ty, rng=random):
    """Bate com a picareta selecionada no bloco (tx, ty). Retorna dict {ok, msg, broke, stairs, ore}."""
    res = {"ok": False, "msg": "", "broke": False, "stairs": False, "ore": None}
    cell = fl.cells.get((tx, ty))
    if cell is None:
        return res
    slot = state.inv.slots[state.sel]
    it = data.ITEMS[slot["i"]] if slot else None
    if not it or it["kind"] != "tool" or it["tool"] != "picareta":
        res["msg"] = "Selecione a picareta na barra para minerar."
        return res
    nivel = it.get("nivel", 0)
    if cell["k"] == "ore" and nivel < ORE_NEED[cell["ore"]]:
        res["msg"] = f"Precisa de uma picareta de {data.TIER_NOME[ORE_NEED[cell['ore']]]} ou melhor."
        return res
    dmg = 1 + nivel
    drops = _drops(state, cell, rng) if cell["hp"] - dmg <= 0 else []
    if any(not state.inv.can_add(i, n) for i, n in drops):
        res["msg"] = "Inventário cheio!"
        return res
    if not state.spend_energy(it.get("energia", 1)):
        res["msg"] = "Você está exausto! Coma algo ou saia da mina."
        return res
    res["ok"] = True
    res["ore"] = cell["ore"]
    cell["hp"] -= dmg
    if cell["hp"] > 0:
        return res
    del fl.cells[(tx, ty)]
    res["broke"] = True
    msgs = []
    for i, n in drops:
        state.inv.add(i, n)
        msgs.append(f"+{n} {data.ITEMS[i]['nome']}")
    tier = ORE_NEED.get(cell["ore"], -1) + 1
    up = state.add_xp("mineracao", 2 if cell["k"] == "rock" else 5 + 3 * tier)
    if up:
        msgs.append("Nível de Mineração subiu!")
    if cell["stairs"]:
        fl.stairs = (tx, ty)
        res["stairs"] = True
        msgs.append("Você achou uma escada para baixo!")
    res["msg"] = "  ".join(msgs)
    return res


# ----------------------------------------------------------------- inimigos e espada
def enemy_damage(floor):
    return 6 + floor // 3


def update_enemies(fl, px, py, dt, floor, rng=random):
    """Move os inimigos e devolve o dano que o jogador levou neste instante."""
    dano = 0
    for e in fl.enemies:
        e["cd"] = max(0.0, e["cd"] - dt)
        e["hurt"] = max(0.0, e["hurt"] - dt)
        dx, dy = px - e["x"], (py - 0.3) - e["y"]
        d = math.hypot(dx, dy) or 1e-6
        bat = e["k"] == "morcego"
        if e["hurt"] > 0.12:                                   # empurrado ao levar um golpe
            vx, vy = e["vx"], e["vy"]
        elif d < (9 if bat else 7):
            sp = 2.4 if bat else 1.3
            if bat:                                            # voo ondulado
                sp *= 0.7 + 0.5 * math.sin(e["x"] * 3 + e["y"] * 2 + e["cd"])
            vx, vy = dx / d * sp, dy / d * sp
        else:
            vx = vy = 0.0
        nx, ny = e["x"] + vx * dt, e["y"] + vy * dt
        if 1.2 <= nx <= W - 1.2 and (bat or not blocked(fl, nx, e["y"] + .15)):
            e["x"] = nx
        if 1.2 <= ny <= H - 1.2 and (bat or not blocked(fl, e["x"], ny + .15)):
            e["y"] = ny
        if d < 0.65 and e["cd"] <= 0:
            e["cd"] = 1.1
            dano += enemy_damage(floor)
    return dano


def attack(state, fl, px, py, facing, floor, rng=random):
    """Golpe de espada à frente do jogador. Retorna {ok, msg, hit, kills}."""
    res = {"ok": False, "msg": "", "hit": 0, "kills": 0}
    slot = state.inv.slots[state.sel]
    it = data.ITEMS[slot["i"]] if slot else None
    if not it or it.get("tool") != "espada":
        return res
    if not state.spend_energy(it.get("energia", 1)):
        res["msg"] = "Você está exausto!"
        return res
    res["ok"] = True
    fx, fy = facing
    msgs = []
    for e in list(fl.enemies):
        dx, dy = e["x"] - px, e["y"] - (py - .3)
        d = math.hypot(dx, dy)
        if d > 1.7 or (d > 0.7 and (dx * fx + dy * fy) / (d or 1) < 0.2):
            continue
        e["hp"] -= it["dano"]
        e["hurt"] = 0.3
        e["vx"], e["vy"] = dx / (d or 1) * 5, dy / (d or 1) * 5
        res["hit"] += 1
        if e["hp"] <= 0:
            fl.enemies.remove(e)
            res["kills"] += 1
            loot = ("asa_morcego", 1) if e["k"] == "morcego" else ("gosma", rng.randint(1, 2))
            if state.inv.can_add(*loot):
                state.inv.add(*loot)
                msgs.append(f"+{loot[1]} {data.ITEMS[loot[0]]['nome']}")
            state.add_xp("mineracao", 6)
    res["msg"] = "  ".join(msgs)
    return res

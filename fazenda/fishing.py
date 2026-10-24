"""Pesca com rede e piscicultura (tanque). Lógica pura, sem pygame."""
import random

from . import data
from .config import DAY_MINUTES
from .world import WATER

NET_COOLDOWN = 90          # minutos de jogo para a rede secar
TANK_CAP = 8               # peixes por tanque
TANK_FEED_MAX = 60
FAT_WEIGHT = 5             # peso em que o peixe fica "gordo"

FISH = {                   # tabela de sorte por tipo de água: (item, peso)
    "lago": [("peixe_carpa", 40), ("peixe_tilapia", 35), ("peixe_bagre", 20), ("peixe_truta", 5)],
    "rio": [("peixe_truta", 40), ("peixe_bagre", 30), ("peixe_tilapia", 20), ("peixe_carpa", 10)],
    "mar": [("peixe_robalo", 50), ("peixe_tilapia", 25), ("peixe_bagre", 25)],
}
NOTHING = 0.2


def water_kind(world, x, y):
    if y >= 60:
        return "mar"
    if x >= 23 and y >= 46:
        return "rio"
    return "lago"


def now(state):
    return state.clock.day * DAY_MINUTES + state.clock.minutes


def net_wait(state):
    """Minutos que faltam para a rede secar (0 = pronta)."""
    return max(0, int(getattr(state, "net_ready", 0) - now(state) + 0.999))


def cast_net(state, tx, ty, rng=random):
    """Usa a rede no bloco (tx, ty). Retorna (ok, mensagem, [(item, qtd)])."""
    if not state.world.in_bounds(tx, ty) or state.world.ground[ty][tx] != WATER:
        return False, "A rede precisa ser jogada na água.", []
    wait = net_wait(state)
    if wait > 0:
        return False, f"A rede ainda está secando (faltam {wait} min).", []
    if not state.spend_energy(2):
        return False, "Você está exausto! Coma algo ou vá dormir.", []
    state.net_ready = now(state) + NET_COOLDOWN
    kind = water_kind(state.world, tx, ty)
    lvl = state.level("pesca")
    got = {}
    n = 1 + (1 if rng.random() < 0.35 + 0.05 * lvl else 0) + (1 if rng.random() < 0.1 + 0.03 * lvl else 0)
    table = FISH[kind]
    for _ in range(n):
        if rng.random() < NOTHING:
            continue
        item = rng.choices([i for i, _ in table], [w for _, w in table])[0]
        got[item] = got.get(item, 0) + 1
    out = []
    for item, q in got.items():
        q = _fit(state, item, q)
        if q:
            state.inv.add(item, q)
            out.append((item, q))
    state.add_xp("pesca", 4 + 2 * sum(q for _, q in out))
    if not out:
        return True, "A rede voltou vazia...", []
    txt = ", ".join(f"{q}x {data.ITEMS[i]['nome']}" for i, q in out)
    return True, f"Pescou: {txt}!", out


def _fit(state, item, q):
    while q > 0 and not state.inv.can_add(item, q):
        q -= 1
    return q


# ----------------------------------------------------------------- tanque
def tank(inst):
    d = inst["data"]
    d.setdefault("peixes", [])
    d.setdefault("racao", 0)
    return d


def fat_count(inst):
    return sum(1 for p in tank(inst)["peixes"] if p >= FAT_WEIGHT)


def add_fry(state, inst, qty):
    t = tank(inst)
    free = TANK_CAP - len(t["peixes"])
    qty = min(qty, free, state.inv.count("alevino"))
    if qty <= 0:
        return False, "Tanque cheio." if free <= 0 else "Você não tem alevinos."
    state.inv.remove("alevino", qty)
    t["peixes"].extend([1] * qty)
    return True, f"{qty} alevino(s) no tanque."


def add_feed(state, inst, qty):
    t = tank(inst)
    qty = min(qty, state.inv.count("racao_peixe"), TANK_FEED_MAX - t["racao"])
    if qty <= 0:
        return False, "Tanque de ração cheio." if t["racao"] >= TANK_FEED_MAX else "Você não tem ração de peixe."
    state.inv.remove("racao_peixe", qty)
    t["racao"] += qty
    return True, f"+{qty} de ração."


def harvest(state, inst):
    t = tank(inst)
    fat = [p for p in t["peixes"] if p >= FAT_WEIGHT]
    if not fat:
        return False, "Nenhum peixe gordo ainda."
    n = len(fat)
    while n > 0 and not state.inv.can_add("peixe_gordo", n):
        n -= 1
    if n <= 0:
        return False, "Inventário cheio."
    state.inv.add("peixe_gordo", n)
    left = n
    new = []
    for p in t["peixes"]:
        if p >= FAT_WEIGHT and left > 0:
            left -= 1
        else:
            new.append(p)
    t["peixes"] = new
    state.add_xp("pesca", 3 * n)
    return True, f"Colheu {n}x Peixe Gordo!"


def end_day(state):
    """Cada peixe com ração engorda 1 por dia. Retorna quantos ficaram gordos hoje."""
    novos = 0
    for inst in state.structs.by_id.values():
        if inst["s"] != "tanque":
            continue
        t = tank(inst)
        for i, p in enumerate(t["peixes"]):
            if p < FAT_WEIGHT and t["racao"] > 0:
                t["racao"] -= 1
                t["peixes"][i] = p + 1
                if p + 1 >= FAT_WEIGHT:
                    novos += 1
    return novos

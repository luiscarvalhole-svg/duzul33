"""Ferramentas de desenvolvedor: atalhos para testar o jogo (dinheiro, tempo, itens, animais, terrenos...).

Tudo aqui é lógica pura (sem pygame). Cada função devolve uma mensagem curta para mostrar na tela.
"""
from . import animals as an
from . import data
from .clock import weather_for
from .config import DAYS_PER_SEASON, MAX_ENERGY, SEASONS, WATER_CAPACITY, XP_LEVELS
from .state import level_for

SPEEDS = [1, 5, 20, 60]


def add_money(state, n):
    state.money = max(0, state.money + n)
    return f"Dinheiro: ${state.money}"


def refill(state):
    state.energy = float(MAX_ENERGY)
    state.water = state.water_cap()
    return "Energia e regador cheios."


def set_hour(state, hour):
    """Define a hora do dia (6 a 23). O dia do jogo vai de 06:00 até 24:00."""
    hour = max(6, min(23, int(hour)))
    state.clock.minutes = float((hour - 6) * 60)
    return f"Hora: {state.clock.hhmm()}"


def set_season(state, season):
    """Pula para o dia 1 da estação escolhida (no ano atual). Recalcula o clima."""
    year0 = (state.clock.day // (DAYS_PER_SEASON * 4)) * DAYS_PER_SEASON * 4
    state.clock.day = year0 + SEASONS.index(season) * DAYS_PER_SEASON
    state.clock.minutes = 0.0
    state.weather = weather_for(state.clock.day, state.seed)
    state.forecast = weather_for(state.clock.day + 1, state.seed)
    return f"Estação: {season} (dia {state.clock.day_of_season})"


def set_weather(state, kind):
    state.weather = kind
    return f"Clima de hoje: {kind}"


def add_levels(state, n):
    for sk in state.skills:
        lv = min(len(XP_LEVELS) - 1, level_for(state.skills[sk]) + n)
        state.skills[sk] = max(state.skills[sk], XP_LEVELS[lv])
    return f"Habilidades +{n} nível."


def max_skills(state):
    for sk in state.skills:
        state.skills[sk] = XP_LEVELS[-1]
    return "Todas as habilidades no nível máximo."


def grow_crops(state):
    n = 0
    for s in state.farm.soil.values():
        if s["crop"]:
            s["crop"]["prog"] = float(data.CROPS[s["crop"]["id"]]["dias"])
            n += 1
    return f"{n} planta(s) prontas para colher."


def water_all(state):
    for s in state.farm.soil.values():
        s["wet"] = True
    return f"{len(state.farm.soil)} bloco(s) de terra regados."


def animals_boost(state):
    for a in state.animals:
        a.update(amizade=1000, feliz=100, saude=100, fome=0, pronto=True, filhote=0)
    return f"{len(state.animals)} animal(is): amizade e bem-estar no máximo, produtos prontos."


def fill_troughs(state):
    n = 0
    for inst in state.structs.by_id.values():
        sd = data.STRUCTS[inst["s"]]
        if "feed_max" not in sd:
            continue
        inst["data"]["feed"] = sd["feed_max"]
        for tipo in sd.get("aceita", []):
            inst["data"].setdefault("racao", {})[an.racao_id(tipo)] = sd["feed_max"]
        n += 1
    return f"{n} cocho(s) cheios (feno e rações)."


def force_births(state):
    n = an.breed(state, chance=1.0)
    return f"{n} filhote(s) nasceram." if n else "Nenhum nasceu (precisa de 2 adultos da mesma espécie com amizade >= 500, humor >= 80, saúde >= 70 e vaga)."


def unlock_lands(state):
    state.owned = {l["id"] for l in state.world.lands} | {"inicial"}
    return "Todos os terrenos liberados."


def give_item(state, item_id, qty=1, quality=0):
    """Coloca itens no inventário (o que couber). Retorna a mensagem."""
    if item_id not in data.ITEMS:
        return "Item desconhecido."
    got = 0
    for _ in range(qty):
        if not state.inv.can_add(item_id, 1, quality):
            break
        state.inv.add(item_id, 1, quality)
        got += 1
    nome = data.ITEMS[item_id]["nome"]
    return f"+{got}x {nome}" + (" (inventário cheio)" if got < qty else "")


def spawn_animal(state, tipo):
    home = an.housing(state, tipo)
    if home is None:
        return f"Sem {data.STRUCTS[data.ANIMALS[tipo]['predio']]['nome']} com vaga para {data.ANIMALS[tipo]['nome']}."
    a = an.new_animal(state.next_animal, tipo, home["id"])
    state.next_animal += 1
    state.animals.append(a)
    return f"{a['nome']} ({data.ANIMALS[tipo]['nome']}) criado de graça."


def teleport_points(state):
    """Lista [(nome, x, y)] de lugares para o teleporte."""
    pts = [("Fazenda", 44.5, 36.5)]
    casa = next((i for i in state.structs.by_id.values() if i["s"] == "casa"), None)
    if casa:
        pts[0] = ("Casa", casa["x"] + 2.5, casa["y"] + 4.6)
    for f in state.world.fixed:
        dx, dy = f["door"]
        pts.append((data.SHOPS[f["shop"]]["nome"], dx + 0.5, dy + 1.6))
    return pts


def teleport(state, x, y):
    """Teleporta o jogador. Se o destino for obstáculo, procura o ponto livre mais próximo."""
    for r in range(0, 6):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if state.can_stand(x + dx * 0.5, y + dy * 0.5):
                    state.px, state.py = x + dx * 0.5, y + dy * 0.5
                    return f"Teleportado para ({state.px:.1f}, {state.py:.1f})."
    return "Não achei um lugar livre ali."

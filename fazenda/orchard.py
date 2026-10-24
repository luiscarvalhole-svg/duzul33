"""Pomar: mudas de árvores frutíferas e árvores comuns que crescem com os dias. Lógica pura."""
from . import data


def _d(inst):
    inst["data"].setdefault("idade", 0)
    inst["data"].setdefault("fruto", 0)
    inst["data"].setdefault("cd", 0)
    return inst["data"]


def is_fruit(inst):
    return "fruta" in data.STRUCTS[inst["s"]]


def adult(inst):
    return _d(inst)["idade"] >= data.STRUCTS[inst["s"]]["dias_adulta"]


def stage(inst):
    """0 = muda, 1 = jovem, 2 = adulta."""
    sd = data.STRUCTS[inst["s"]]
    idade = _d(inst)["idade"]
    if idade >= sd["dias_adulta"]:
        return 2
    return 1 if idade >= sd["dias_adulta"] // 2 else 0


def ready(inst):
    return is_fruit(inst) and adult(inst) and _d(inst)["fruto"] > 0


def info(inst):
    sd = data.STRUCTS[inst["s"]]
    d = _d(inst)
    if not adult(inst):
        return f"{sd['nome']}: crescendo ({d['idade']}/{sd['dias_adulta']} dias)."
    if d["fruto"] > 0:
        return f"{d['fruto']} fruta(s) prontas!"
    return "Sem frutas agora. Dá " + data.ITEMS[sd["fruta"]]["nome"].lower() + " em: " + ", ".join(sd["estacoes"]) + "."


def harvest(state, inst):
    if not is_fruit(inst):
        return False, "Esta árvore não dá frutas."
    d = _d(inst)
    if not adult(inst):
        return False, info(inst)
    if d["fruto"] <= 0:
        return False, info(inst)
    sd = data.STRUCTS[inst["s"]]
    n = d["fruto"]
    while n > 0 and not state.inv.can_add(sd["fruta"], n):
        n -= 1
    if n <= 0:
        return False, "Inventário cheio."
    state.inv.add(sd["fruta"], n)
    d["fruto"] -= n
    if d["fruto"] == 0:
        d["cd"] = sd["rebrota"]
    state.add_xp("coleta", 3 * n)
    return True, f"Colheu {n}x {data.ITEMS[sd['fruta']]['nome']}!"


def end_day(state):
    """Chamado depois de virar o dia. Retorna quantas árvores ficaram com frutas / viraram árvore."""
    season = state.clock.season
    novas = viraram = 0
    for inst in list(state.structs.by_id.values()):
        sd = data.STRUCTS[inst["s"]]
        if "dias_adulta" not in sd:
            continue
        d = _d(inst)
        d["idade"] += 1
        if is_fruit(inst):
            if d["idade"] >= sd["dias_adulta"] and season in sd["estacoes"] and d["fruto"] == 0:
                if d["cd"] > 0:
                    d["cd"] -= 1
                else:
                    d["fruto"] = 3 + d["idade"] % 3
                    novas += 1
        elif d["idade"] >= sd["dias_adulta"]:
            pos = (inst["x"], inst["y"])
            state.structs.remove(inst["id"])
            state.world.objects[pos] = {"k": "tree", "hp": 5, "v": (inst["x"] * 7 + inst["y"] * 3) % 4}
            viraram += 1
    return novas, viraram

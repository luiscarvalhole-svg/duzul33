"""Ações do jogador: usar o item selecionado na barra rápida sobre o bloco à frente.

Cada função devolve um dict: {"ok": bool, "msg": str, "fx": [...], "sfx": nome, "build": id_da_construção}
A camada gráfica usa "fx" para partículas e "sfx" para sons; a lógica não depende deles.
"""
import random

from . import data
from .world import FOREST, GRASS, WATER


def _res(ok=False, msg="", fx=None, sfx=None, build=None):
    return {"ok": ok, "msg": msg, "fx": fx or [], "sfx": sfx, "build": build}


def use_selected(state, rng=random):
    slot = state.inv.slots[state.sel]
    if not slot:
        return _res(False, "Slot vazio.")
    it = data.ITEMS[slot["i"]]
    kind = it["kind"]
    tx, ty = state.target_tile()
    if kind == "tool":
        if state.mounted and it["tool"] in ("enxada", "regador", "foice"):
            return _tool_wide(state, it, tx, ty, rng)
        return _tool(state, it, tx, ty, rng)
    if kind == "seed":
        return _plant(state, it, tx, ty)
    if kind == "fertilizer":
        return _fertilize(state, it, tx, ty)
    if kind == "food":
        if state.eat(state.sel):
            return _res(True, f"Você comeu {it['nome']}.", sfx="eat")
        return _res(False, "Você já está com a energia cheia.")
    if kind == "placeable":
        return _res(True, "", build=it["id"])
    return _res(False, "Este item não pode ser usado assim.")


def _tool_wide(state, it, tx, ty, rng):
    """No trator, enxada/regador/foice atingem 3 blocos de largura (gasta energia só uma vez)."""
    fx, fy = state.facing
    px, py = (0, 1) if fx else (1, 0)
    res = _tool(state, it, tx, ty, rng)
    if not res["ok"]:
        # se o bloco da frente não serve, tenta os dois lados (ex.: borda do campo)
        outros = [(tx + px, ty + py), (tx - px, ty - py)]
        for ox, oy in outros:
            res = _tool(state, it, ox, oy, rng)
            if res["ok"]:
                break
        else:
            return res
    energia = state.energy
    for ox, oy in ((tx + px, ty + py), (tx - px, ty - py)):
        if (ox, oy) == (tx, ty):
            continue
        extra = _tool(state, it, ox, oy, rng)
        if extra["ok"]:
            res["fx"] = list(res["fx"]) + list(extra["fx"])
            if extra["msg"] and res["msg"].startswith("+1"):
                res["msg"] += " " + extra["msg"]
    state.energy = energia
    return res


def _need_energy(state, it):
    n = it.get("energia", 1)
    if not state.spend_energy(n):
        return _res(False, "Você está exausto! Coma algo ou vá dormir.")
    return None


def _tool(state, it, tx, ty, rng):
    t = it["tool"]
    world, farm = state.world, state.farm
    if not world.in_bounds(tx, ty):
        return _res(False, "Não há nada ali.")
    if t == "enxada":
        return _hoe(state, it, tx, ty)
    if t == "rede":
        from . import fishing
        ok, msg, _ = fishing.cast_net(state, tx, ty, rng)
        return _res(ok, msg, fx=[("splash", tx, ty)] if ok else None, sfx="water" if ok else None)
    if t == "regador":
        inst = state.structs.at(tx, ty) if hasattr(state.structs, "at") else None
        if inst and inst["s"] == "torneira":
            state.water = state.water_cap()
            return _res(True, "Regador cheio!", fx=[("splash", tx, ty)], sfx="water")
        if world.ground[ty][tx] == WATER and state.settings.get("regador_lago"):
            state.water = state.water_cap()
            return _res(True, "Regador cheio!", fx=[("splash", tx, ty)], sfx="water")
        if (tx, ty) not in farm.soil:
            return _res(False, "Só dá para regar terra arada.")
        if state.water <= 0:
            return _res(False, "Regador vazio! Encha em uma torneira.")
        err = _need_energy(state, it)
        if err:
            return err
        state.water -= 1
        farm.water(tx, ty)
        return _res(True, "", fx=[("water", tx, ty)], sfx="water")
    if t == "foice":
        s = farm.soil.get((tx, ty))
        if not s or not s["crop"]:
            return _res(False, "Não há nada para colher aqui.")
        if not farm.ripe(tx, ty):
            return _res(False, "Ainda não está maduro!")
        crop = data.CROPS[s["crop"]["id"]]
        if not state.inv.can_add(crop["id"], 1, 2):
            return _res(False, "Inventário cheio!")
        err = _need_energy(state, it)
        if err:
            return err
        h = farm.harvest(tx, ty, state.level("agricultura"), rng)
        if not state.inv.can_add(h["item"], 1, h["q"]):
            return _res(False, "Inventário cheio!")
        state.inv.add(h["item"], h["qty"], h["q"])
        state.stats["colhidos"] = state.stats.get("colhidos", 0) + 1
        up = state.add_xp("agricultura", h["xp"])
        msg = f"+1 {crop['nome']}" + (" (nível de Agricultura subiu!)" if up else "")
        return _res(True, msg, fx=[("harvest", tx, ty, tuple(crop["cor"]))], sfx="harvest")
    if t in ("machado", "picareta"):
        return _chop(state, it, tx, ty, rng)
    return _res(False, "Ferramenta desconhecida.")


def _hoe(state, it, tx, ty):
    world, farm = state.world, state.farm
    if not state.owned_tile(tx, ty):
        return _res(False, "Este terreno ainda não é seu.")
    if farm.soil.get((tx, ty)):
        return _res(False, "Já tem planta aqui." if farm.soil[(tx, ty)]["crop"] else "A terra já está arada.")
    if world.ground[ty][tx] not in (GRASS, FOREST):
        return _res(False, "Só dá para arar grama.")
    if (tx, ty) in world.objects or state.structs.at(tx, ty) or (tx, ty) in world.fixed_tiles:
        return _res(False, "O local está ocupado.")
    err = _need_energy(state, it)
    if err:
        return err
    farm.till(tx, ty)
    return _res(True, "", fx=[("dirt", tx, ty)], sfx="hoe")


def _chop(state, it, tx, ty, rng):
    t = it["tool"]
    world, farm = state.world, state.farm
    obj = world.objects.get((tx, ty))
    if t == "picareta" and not obj:
        s = farm.soil.get((tx, ty))
        if s and not s["crop"]:
            err = _need_energy(state, it)
            if err:
                return err
            farm.untill(tx, ty)
            return _res(True, "A terra voltou a ser grama.", fx=[("dirt", tx, ty)], sfx="hoe")
        return _res(False, "Nada para quebrar aqui.")
    if not obj:
        return _res(False, "Não há nada para cortar aqui.")
    ok_tool = (t == "machado" and obj["k"] in ("tree", "bush")) or (t == "picareta" and obj["k"] == "rock")
    if not ok_tool:
        return _res(False, "Use o machado em árvores e arbustos, e a picareta em pedras.")
    drops = {"tree": ("madeira", 6), "bush": ("fibra", 2), "rock": ("pedra", 3)}[obj["k"]]
    if obj["hp"] <= 1 and not state.inv.can_add(*drops):
        return _res(False, "Inventário cheio!")
    err = _need_energy(state, it)
    if err:
        return err
    obj["hp"] -= 1 + it.get("nivel", 0)
    fx = [("chip", tx, ty, obj["k"])]
    if obj["hp"] <= 0:
        del world.objects[(tx, ty)]
        state.inv.add(*drops)
        up = state.add_xp("coleta", {"tree": 6, "bush": 3, "rock": 5}[obj["k"]])
        msg = f"+{drops[1]} {data.ITEMS[drops[0]]['nome']}" + (" (nível de Coleta subiu!)" if up else "")
        return _res(True, msg, fx=fx, sfx="break")
    return _res(True, "", fx=fx, sfx="chop")


def _plant(state, it, tx, ty):
    if not state.owned_tile(tx, ty):
        return _res(False, "Este terreno ainda não é seu.")
    ok, why = state.farm.plant(tx, ty, it["crop"], state.clock.season)
    if not ok:
        return _res(False, why)
    state.inv.remove_from_slot(state.sel, 1)
    return _res(True, "", fx=[("dirt", tx, ty)], sfx="plant")


def _fertilize(state, it, tx, ty):
    ok, why = state.farm.fertilize(tx, ty, it["fert"])
    if not ok:
        return _res(False, why)
    state.inv.remove_from_slot(state.sel, 1)
    return _res(True, "Solo adubado.", fx=[("dirt", tx, ty)], sfx="plant")

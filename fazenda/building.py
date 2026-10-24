"""Sistema de construção livre.

* Structures guarda as construções posicionadas (com índice por camada para colisões).
* validate_placement decide se uma posição é válida (e explica o motivo se não for).
* place/store/move aplicam a ação ligando inventário e mundo; History permite desfazer/refazer.
"""
import copy

from . import data
from .world import PLAZA, ROAD, WATER


class Structures:
    def __init__(self):
        self.by_id = {}
        self.next_id = 1
        self._layers = {"objeto": {}, "chao": {}}

    # ---- geometria
    @staticmethod
    def dims(sdef, rot=0):
        w, h = sdef["w"], sdef["h"]
        return (h, w) if (rot % 2 and sdef.get("rotacionavel")) else (w, h)

    @classmethod
    def footprint(cls, sdef, x, y, rot=0):
        w, h = cls.dims(sdef, rot)
        return [(x + i, y + j) for j in range(h) for i in range(w)]

    def layer(self, name):
        return self._layers[name]

    # ---- índice
    def _index(self, inst, add=True):
        sd = data.STRUCTS[inst["s"]]
        lay = self._layers[sd["camada"]]
        for t in self.footprint(sd, inst["x"], inst["y"], inst["rot"]):
            if add:
                lay[t] = inst["id"]
            elif lay.get(t) == inst["id"]:
                del lay[t]

    def add(self, sid, x, y, rot=0, data_=None, iid=None):
        if sid not in data.STRUCTS:
            raise KeyError(sid)
        if iid is None:
            iid = self.next_id
        self.next_id = max(self.next_id, iid + 1)
        inst = {"id": iid, "s": sid, "x": x, "y": y, "rot": rot % 2 if data.STRUCTS[sid].get("rotacionavel") else 0,
                "data": dict(data_ or {})}
        if sid == "portao":
            inst["data"].setdefault("aberto", False)
        if data.STRUCTS[sid].get("interage") == "animais":
            inst["data"].setdefault("feed", 0)
        self.by_id[iid] = inst
        self._index(inst, True)
        return inst

    def remove(self, iid):
        inst = self.by_id.pop(iid)
        self._index(inst, False)
        return inst

    def move(self, iid, x, y, rot):
        inst = self.by_id[iid]
        self._index(inst, False)
        inst["x"], inst["y"] = x, y
        inst["rot"] = rot % 2 if data.STRUCTS[inst["s"]].get("rotacionavel") else 0
        self._index(inst, True)

    def at(self, x, y):
        """Instância no bloco (objeto tem prioridade sobre piso)."""
        iid = self._layers["objeto"].get((x, y))
        if iid is None:
            iid = self._layers["chao"].get((x, y))
        return self.by_id.get(iid) if iid is not None else None

    def blocks(self, x, y):
        inst = self.at_layer(x, y, "objeto")
        if not inst:
            return False
        sd = data.STRUCTS[inst["s"]]
        if inst["s"] == "portao":
            return not inst["data"].get("aberto", False)
        return sd.get("bloqueia", True)

    def at_layer(self, x, y, camada):
        iid = self._layers[camada].get((x, y))
        return self.by_id.get(iid) if iid is not None else None

    def to_dict(self):
        return {"next": self.next_id, "list": [copy.deepcopy(i) for i in self.by_id.values()]}

    @classmethod
    def from_dict(cls, d):
        st = cls()
        for i in d.get("list", []):
            if i["s"] in data.STRUCTS:
                st.add(i["s"], int(i["x"]), int(i["y"]), int(i.get("rot", 0)), i.get("data"), iid=int(i["id"]))
        st.next_id = max(st.next_id, int(d.get("next", 1)))
        return st


# ----------------------------------------------------------------- validação
def validate_placement(state, sid, x, y, rot=0, ignore_id=None):
    """Retorna (ok, motivo). Impede água, estrada, terreno não comprado e sobreposições."""
    sd = data.STRUCTS[sid]
    world = state.world
    fp = Structures.footprint(sd, x, y, rot)
    ptile = (int(state.px), int(state.py))
    for tx, ty in fp:
        if not world.in_bounds(tx, ty):
            return False, "Fora do mapa."
        land = world.land_at(tx, ty)
        if land is None or land["id"] not in state.owned:
            return False, "Terreno não comprado."
        g = world.ground[ty][tx]
        if g == WATER:
            return False, "Não dá para construir na água."
        if g in (ROAD, PLAZA):
            return False, "Não dá para construir na estrada."
        if (tx, ty) in world.objects:
            return False, "Há um obstáculo aqui (use machado ou picareta)."
        if (tx, ty) in world.fixed_tiles:
            return False, "Local ocupado."
        if (tx, ty) in state.farm.soil:
            return False, "Há terra arada ou plantação aqui."
        occ = state.structs.layer(sd["camada"]).get((tx, ty))
        if occ is not None and occ != ignore_id:
            return False, "Sobreposição com outra construção."
        if sd.get("bloqueia", True) and ptile == (tx, ty):
            return False, "Você está parado neste local."
    if sd.get("interage") in ("animais", "casa"):               # precisa de acesso
        fps = set(fp)
        ring = {(tx + dx, ty + dy) for tx, ty in fp for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - fps
        if not any(world.in_bounds(a, b) and not world.static_blocked(a, b)
                   and state.structs.at_layer(a, b, "objeto") is None for a, b in ring):
            return False, "Sem acesso: deixe espaço livre ao redor."
    return True, ""


def can_store(state, inst):
    sd = data.STRUCTS[inst["s"]]
    if not sd.get("guardavel", True):
        return False, "Esta construção não pode ser guardada."
    if any(a["home"] == inst["id"] for a in state.animals):
        return False, "Retire os animais antes de guardar."
    if inst["data"].get("bau"):
        from . import storage
        if not storage.is_empty(inst):
            return False, "Esvazie o quartinho antes de guardar."
    if inst["s"] == "forno" and (inst["data"].get("estado", "desligado") != "desligado" or inst["data"].get("saida")):
        return False, "Esvazie o forno (termine a fundição e retire as barras) antes de guardar."
    feed = inst["data"].get("feed", 0)
    if feed and not state.inv.can_add("feno", feed):
        return False, "Sem espaço no inventário para devolver o feno."
    return True, ""


# ----------------------------------------------------------------- ações
def place(state, sid, x, y, rot=0, hist=None, iid=None, record=True):
    ok, why = validate_placement(state, sid, x, y, rot)
    if not ok:
        return False, why
    if state.inv.count(sid) < 1:
        return False, "Você não tem este item."
    state.inv.remove(sid, 1)
    inst = state.structs.add(sid, x, y, rot, iid=iid)
    if hist is not None and record:
        hist.push({"op": "place", "sid": sid, "iid": inst["id"], "x": x, "y": y, "rot": inst["rot"]})
    return True, inst["id"]


def store(state, iid, hist=None, record=True):
    inst = state.structs.by_id.get(iid)
    if inst is None:
        return False, "Construção não encontrada."
    ok, why = can_store(state, inst)
    if not ok:
        return False, why
    sid = inst["s"]
    if not state.inv.can_add(sid, 1):
        return False, "Inventário cheio."
    feed = inst["data"].get("feed", 0)
    state.structs.remove(iid)
    state.inv.add(sid, 1)
    if feed:
        state.inv.add("feno", feed)
    if hist is not None and record:
        hist.push({"op": "remove", "inst": copy.deepcopy(inst)})
    return True, ""


def move(state, iid, x, y, rot, hist=None, record=True):
    inst = state.structs.by_id.get(iid)
    if inst is None:
        return False, "Construção não encontrada."
    ok, why = validate_placement(state, inst["s"], x, y, rot, ignore_id=iid)
    if not ok:
        return False, why
    frm = (inst["x"], inst["y"], inst["rot"])
    state.structs.move(iid, x, y, rot)
    if hist is not None and record:
        hist.push({"op": "move", "iid": iid, "frm": frm, "to": (x, state.structs.by_id[iid]["y"], inst["rot"])})
    return True, ""


class History:
    def __init__(self, limit=50):
        self.undo_stack, self.redo_stack, self.limit = [], [], limit

    def push(self, cmd):
        self.undo_stack.append(cmd)
        self.undo_stack = self.undo_stack[-self.limit:]
        self.redo_stack.clear()

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def undo(self, state):
        if not self.undo_stack:
            return False, "Nada para desfazer."
        cmd = self.undo_stack[-1]
        ok, why = _revert(state, cmd)
        if ok:
            self.undo_stack.pop()
            self.redo_stack.append(cmd)
        return ok, why

    def redo(self, state):
        if not self.redo_stack:
            return False, "Nada para refazer."
        cmd = self.redo_stack[-1]
        ok, why = _apply(state, cmd)
        if ok:
            self.redo_stack.pop()
            self.undo_stack.append(cmd)
        return ok, why


def _revert(state, cmd):
    op = cmd["op"]
    if op == "place":
        return store(state, cmd["iid"], record=False)
    if op == "remove":
        inst = cmd["inst"]
        ok, why = validate_placement(state, inst["s"], inst["x"], inst["y"], inst["rot"])
        if not ok:
            return False, why
        if state.inv.count(inst["s"]) < 1:
            return False, "O item não está mais no inventário."
        if inst["data"].get("feed", 0) and state.inv.count("feno") < inst["data"]["feed"]:
            return False, "O feno devolvido não está mais no inventário."
        state.inv.remove(inst["s"], 1)
        if inst["data"].get("feed", 0):
            state.inv.remove("feno", inst["data"]["feed"])
        state.structs.add(inst["s"], inst["x"], inst["y"], inst["rot"], inst["data"], iid=inst["id"])
        return True, ""
    if op == "move":
        x, y, rot = cmd["frm"]
        return move(state, cmd["iid"], x, y, rot, record=False)
    return False, "Ação desconhecida."


def _apply(state, cmd):
    op = cmd["op"]
    if op == "place":
        return place(state, cmd["sid"], cmd["x"], cmd["y"], cmd["rot"], iid=cmd["iid"], record=False)
    if op == "remove":
        return store(state, cmd["inst"]["id"], record=False)
    if op == "move":
        x, y, rot = cmd["to"]
        return move(state, cmd["iid"], x, y, rot, record=False)
    return False, "Ação desconhecida."

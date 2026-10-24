"""Inventário: slots com pilhas. Os primeiros HOTBAR slots formam a barra rápida.

Cada slot é None ou um dict {"i": id_do_item, "n": quantidade, "q": qualidade}.
Pilhas só juntam itens iguais com a mesma qualidade.
"""
from . import data
from .config import INV_SIZE

CATEGORIAS = {
    "Tudo": None,
    "Ferramentas": ("tool",),
    "Sementes": ("seed", "fertilizer"),
    "Colheita": ("crop", "product", "food", "fish"),
    "Materiais": ("material", "ore", "bar", "gem", "loot"),
    "Construção": ("placeable",),
}


class Inventory:
    def __init__(self, size=INV_SIZE):
        self.slots = [None] * size

    @staticmethod
    def stack_max(item_id):
        return data.ITEMS[item_id].get("stack", 99)

    def count(self, item_id, q=None):
        return sum(s["n"] for s in self.slots
                   if s and s["i"] == item_id and (q is None or s["q"] == q))

    def room_for(self, item_id, q=0):
        m = self.stack_max(item_id)
        room = 0
        for s in self.slots:
            if s is None:
                room += m
            elif s["i"] == item_id and s["q"] == q:
                room += m - s["n"]
        return room

    def can_add(self, item_id, qty=1, q=0):
        return self.room_for(item_id, q) >= qty

    def add(self, item_id, qty=1, q=0):
        """Adiciona e devolve o que NÃO coube (0 = tudo guardado)."""
        if item_id not in data.ITEMS:
            raise KeyError(item_id)
        m = self.stack_max(item_id)
        for s in self.slots:
            if qty <= 0:
                break
            if s and s["i"] == item_id and s["q"] == q and s["n"] < m:
                t = min(m - s["n"], qty)
                s["n"] += t
                qty -= t
        for k, s in enumerate(self.slots):
            if qty <= 0:
                break
            if s is None:
                t = min(m, qty)
                self.slots[k] = {"i": item_id, "n": t, "q": q}
                qty -= t
        return qty

    def remove(self, item_id, qty=1, q=None):
        """Remove qty itens (menor qualidade primeiro). False se não houver o bastante."""
        if qty <= 0 or self.count(item_id, q) < qty:
            return False
        idx = [k for k, s in enumerate(self.slots)
               if s and s["i"] == item_id and (q is None or s["q"] == q)]
        idx.sort(key=lambda k: (self.slots[k]["q"], k))
        for k in idx:
            if qty <= 0:
                break
            s = self.slots[k]
            t = min(s["n"], qty)
            s["n"] -= t
            qty -= t
            if s["n"] <= 0:
                self.slots[k] = None
        return True

    def remove_from_slot(self, idx, qty=1):
        s = self.slots[idx]
        if not s or qty <= 0 or s["n"] < qty:
            return False
        s["n"] -= qty
        if s["n"] <= 0:
            self.slots[idx] = None
        return True

    def swap(self, a, b):
        """Troca dois slots; se forem do mesmo item, junta as pilhas."""
        if a == b:
            return
        sa, sb = self.slots[a], self.slots[b]
        if sa and sb and sa["i"] == sb["i"] and sa["q"] == sb["q"]:
            m = self.stack_max(sa["i"])
            t = min(m - sb["n"], sa["n"])
            sb["n"] += t
            sa["n"] -= t
            if sa["n"] <= 0:
                self.slots[a] = None
            return
        self.slots[a], self.slots[b] = sb, sa

    def total_items(self):
        return sum(s["n"] for s in self.slots if s)

    def to_list(self):
        return [dict(s) if s else None for s in self.slots]

    @classmethod
    def from_list(cls, lst, size=INV_SIZE):
        inv = cls(size)
        for k, s in enumerate(lst[:size]):
            if s and s.get("i") in data.ITEMS and int(s.get("n", 0)) > 0:
                inv.slots[k] = {"i": s["i"], "n": int(s["n"]), "q": int(s.get("q", 0))}
        return inv

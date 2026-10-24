"""Quartinho de Bagunça: armazenamento por construção, com espaço que se compra.

Os itens ficam em inst["data"]["bau"] (lista de slots, como o inventário) e "upg" conta as ampliações compradas.
"""
from .inventory import Inventory

BASE_SLOTS = 20
STEP_SLOTS = 10
MAX_UPGRADES = 6                      # 20 + 6*10 = 80 espaços


def capacity(inst):
    return BASE_SLOTS + STEP_SLOTS * inst["data"].get("upg", 0)


def inv(inst):
    """Visão do baú como um Inventory (do tamanho atual)."""
    return Inventory.from_list(inst["data"].get("bau", []), size=capacity(inst))


def _save(inst, box):
    inst["data"]["bau"] = box.to_list()


def used(inst):
    return sum(1 for s in inv(inst).slots if s)


def is_empty(inst):
    return not any(inst["data"].get("bau", []))


def upgrade_cost(inst):
    """Preço da próxima ampliação (None = já está no máximo)."""
    n = inst["data"].get("upg", 0)
    return None if n >= MAX_UPGRADES else 400 * (2 ** n)


def upgrade(state, inst):
    cost = upgrade_cost(inst)
    if cost is None:
        return False, "O quartinho já está no tamanho máximo."
    if state.money < cost:
        return False, f"Faltam ${cost - state.money}."
    state.money -= cost
    inst["data"]["upg"] = inst["data"].get("upg", 0) + 1
    return True, f"Mais {STEP_SLOTS} espaços! Total: {capacity(inst)}."


def deposit(state, inst, idx):
    """Move a pilha inteira do slot idx do inventário para o quartinho."""
    sl = state.inv.slots[idx]
    if not sl:
        return False, "Slot vazio."
    box = inv(inst)
    if not box.can_add(sl["i"], sl["n"], sl["q"]):
        return False, "Quartinho cheio. Compre mais espaço!"
    box.add(sl["i"], sl["n"], sl["q"])
    state.inv.slots[idx] = None
    _save(inst, box)
    return True, ""


def withdraw(state, inst, idx):
    """Move a pilha do slot idx do quartinho para o inventário."""
    box = inv(inst)
    sl = box.slots[idx] if 0 <= idx < len(box.slots) else None
    if not sl:
        return False, "Slot vazio."
    if not state.inv.can_add(sl["i"], sl["n"], sl["q"]):
        return False, "Inventário cheio."
    state.inv.add(sl["i"], sl["n"], sl["q"])
    box.slots[idx] = None
    _save(inst, box)
    return True, ""


def deposit_all(state, inst, skip=10):
    """Guarda tudo do inventário, menos a barra rápida (os primeiros `skip` slots). Retorna quantas pilhas moveu."""
    n = 0
    for idx in range(skip, len(state.inv.slots)):
        if state.inv.slots[idx] and deposit(state, inst, idx)[0]:
            n += 1
    return n

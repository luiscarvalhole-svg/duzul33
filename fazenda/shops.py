"""Lojas funcionais: estoque diário limitado, ofertas, requisitos, compra e venda."""
import random

from . import animals as an
from . import data
from .config import QUALITY_MULT


def _expand(state, shop_id):
    sh = data.SHOPS[shop_id]
    out = []
    for e in sh.get("estoque", []):
        if e.get("auto") == "seed":
            for cid, c in data.CROPS.items():
                if state.clock.season in c["estacoes"]:
                    out.append({"item": "semente_" + cid, "estoque": e.get("estoque")})
        elif e.get("auto") == "estruturas":
            for sid, s in data.STRUCTS.items():
                if s.get("loja") == shop_id:
                    out.append({"item": sid})
        elif "item" in e:
            out.append(dict(e))
    return out


def _base_price(item_id, entry):
    if entry.get("preco"):
        return entry["preco"]
    return data.ITEMS[item_id].get("compra", 0)


def _day_state(state, shop_id):
    st = state.shop_state.get(shop_id)
    if not st or st.get("day") != state.clock.day:
        st = {"day": state.clock.day, "bought": {}}
        state.shop_state[shop_id] = st
    return st


def shop_entries(state, shop_id):
    """Lista de ofertas do dia: item, preço, estoque restante, requisitos e oferta (-15%)."""
    st = _day_state(state, shop_id)
    entries = _expand(state, shop_id)
    rng = random.Random(state.clock.day * 31 + sum(ord(c) for c in shop_id))
    deal = rng.randrange(len(entries)) if entries else -1
    out = []
    for i, e in enumerate(entries):
        iid = e["item"]
        it = data.ITEMS[iid]
        req = {}
        if it["kind"] == "seed":
            lvl = data.CROPS[it["crop"]]["nivel"]
            if lvl:
                req = {"agricultura": lvl}
        price = _base_price(iid, e)
        offer = i == deal and price >= 10
        if offer:
            price = max(1, int(price * 0.85))
        lim = e.get("estoque")
        remaining = None if lim is None else max(0, lim - st["bought"].get(iid, 0))
        mats = {}
        sd = data.STRUCTS.get(iid)
        if sd:
            mats = dict(sd.get("custo", {}).get("materiais", {}))
        ok_req, _ = state.meets(req)
        out.append({"item": iid, "preco": price, "estoque": remaining, "req": req, "ok_req": ok_req,
                    "oferta": offer, "materiais": mats})
    return out


def buy(state, shop_id, item_id, qty=1):
    if qty < 1:
        return False, "Quantidade inválida."
    e = next((x for x in shop_entries(state, shop_id) if x["item"] == item_id), None)
    if e is None:
        return False, "Item não vendido aqui."
    if not e["ok_req"]:
        _, miss = state.meets(e["req"])
        return False, "Requer " + ", ".join(miss) + "."
    if e["estoque"] is not None and qty > e["estoque"]:
        return False, "Estoque insuficiente."
    total = e["preco"] * qty
    if state.money < total:
        return False, "Dinheiro insuficiente."
    for m, n in e["materiais"].items():
        if state.inv.count(m) < n * qty:
            return False, f"Faltam materiais: {data.ITEMS[m]['nome']} x{n * qty}."
    if not state.inv.can_add(item_id, qty):
        return False, "Inventário cheio."
    state.money -= total
    for m, n in e["materiais"].items():
        state.inv.remove(m, n * qty)
    state.inv.add(item_id, qty)
    st = _day_state(state, shop_id)
    st["bought"][item_id] = st["bought"].get(item_id, 0) + qty
    return True, f"Comprou {qty}x {data.ITEMS[item_id]['nome']}."


def sell_price_slot(slot):
    it = data.ITEMS[slot["i"]]
    return int(it.get("venda", 0) * QUALITY_MULT[slot["q"]])


def can_sell_here(shop_id, item_id):
    return data.ITEMS[item_id]["kind"] in data.SHOPS[shop_id].get("compra", []) and data.ITEMS[item_id].get("venda", 0) > 0


def sell(state, shop_id, slot_idx, qty=1):
    s = state.inv.slots[slot_idx]
    if not s:
        return False, "Slot vazio."
    if not can_sell_here(shop_id, s["i"]):
        return False, "Esta loja não compra isso."
    qty = min(qty, s["n"])
    price = sell_price_slot(s) * qty
    name = data.ITEMS[s["i"]]["nome"]
    state.inv.remove_from_slot(slot_idx, qty)
    state.money += price
    state.stats["vendas"] = state.stats.get("vendas", 0) + price
    return True, f"Vendeu {qty}x {name} por ${price}."


def sell_all_sellable(state, shop_id):
    total = 0
    for idx, s in enumerate(state.inv.slots):
        if s and can_sell_here(shop_id, s["i"]):
            total += sell_price_slot(s) * s["n"]
            state.inv.slots[idx] = None
    state.money += total
    state.stats["vendas"] = state.stats.get("vendas", 0) + total
    return total


# ----------------------------------------------------------------- animais
def animal_entries(state):
    out = []
    for tipo, a in data.ANIMALS.items():
        ok, miss = state.meets(a["req"])
        out.append({"tipo": tipo, "preco": a["preco"], "req": a["req"], "ok_req": ok, "faltam": miss,
                    "predio": a["predio"]})
    return out


def buy_animal(state, tipo):
    a = data.ANIMALS[tipo]
    ok, miss = state.meets(a["req"])
    if not ok:
        return False, "Requer " + ", ".join(miss) + "."
    if state.money < a["preco"]:
        return False, "Dinheiro insuficiente."
    home = an.housing(state, tipo)
    if home is None:
        return False, f"Você precisa de um {data.STRUCTS[a['predio']]['nome']} com vaga."
    state.money -= a["preco"]
    animal = an.new_animal(state.next_animal, tipo, home["id"])
    state.next_animal += 1
    state.animals.append(animal)
    return True, f"{animal['nome']} ({a['nome']}) chegou à fazenda!"


def sell_animal(state, animal_id):
    return an.sell(state, animal_id)

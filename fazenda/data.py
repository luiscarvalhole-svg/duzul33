"""Carrega os arquivos JSON de dados e monta os registros do jogo.

Itens de sementes, colheitas e construções são gerados automaticamente a partir
de crops.json e structures.json, para não duplicar informação.
"""
import json
import os

from . import config

ITEMS, CROPS, ANIMALS, STRUCTS, SHOPS = {}, {}, {}, {}, {}
LANDS = []
RECEITAS = {}
FERREIRO = {}
ROTINA = {}          # horários dos lojistas
FUNC = {}            # configuração do funcionário (tarefas, preços, taxa)
GUIA = []
RACOES = {}          # tipo de animal -> {"ingredientes": {...}, "rende": n}


def _read(name):
    with open(os.path.join(config.DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _add_item(item):
    if item["id"] in ITEMS:
        raise ValueError(f"Item duplicado: {item['id']}")
    ITEMS[item["id"]] = item


TIER_SUFIXO = ["", "_pedra", "_ferro", "_ouro"]
TIER_NOME = ["Madeira", "Pedra", "Ferro", "Ouro"]
TOOL_TIERS = {                      # ferramenta -> energia por nível e (regador) capacidade
    "picareta": {"energia": [3, 3, 2, 2]},
    "machado": {"energia": [3, 3, 2, 2]},
    "enxada": {"energia": [2, 2, 1, 1]},
    "regador": {"energia": [1, 1, 1, 1], "capacidade": [40, 60, 80, 120]},
    "espada": {"energia": [2, 2, 1, 1], "dano": [3, 5, 8, 12]},
}


def tool_id(base, nivel):
    return base + TIER_SUFIXO[nivel]


def _make_tool_tiers():
    """Cria as versões de pedra/ferro/ouro das ferramentas a partir do item base (nível 0)."""
    for base, t in TOOL_TIERS.items():
        b = ITEMS[base]
        nome0 = b["nome"]
        for n in range(4):
            it = dict(b, id=tool_id(base, n), nivel=n, energia=t["energia"][n])
            if "dano" in t:
                it["dano"] = t["dano"][n]
                it["nome"] = "Espada Velha" if n == 0 else f"{nome0} de {TIER_NOME[n]}"
                it["desc"] = f"Dano {t['dano'][n]}. " + b["desc"]
            elif "capacidade" in t:
                it["capacidade"] = t["capacidade"][n]
                it["nome"] = nome0 if n == 0 else f"{nome0} de {TIER_NOME[n]}"
                it["desc"] = f"Capacidade de água: {t['capacidade'][n]}. " + b["desc"]
            else:
                it["nome"] = f"{nome0} de {TIER_NOME[n]}"
                it["desc"] = f"Nível {n} ({TIER_NOME[n]}). " + b["desc"]
            ITEMS[it["id"]] = it


def load_all():
    for d in (ITEMS, CROPS, ANIMALS, STRUCTS, SHOPS):
        d.clear()
    LANDS.clear()
    RACOES.clear()
    RECEITAS.clear()
    FERREIRO.clear()
    FUNC.clear()
    ROTINA.clear()
    GUIA.clear()
    for k, v in _read("items.json").items():
        _add_item(dict(v, id=k))
    for c in _read("crops.json"):
        CROPS[c["id"]] = c
    for k, v in _read("animals.json").items():
        ANIMALS[k] = dict(v, id=k)
    for k, v in _read("structures.json").items():
        STRUCTS[k] = dict(v, id=k)
    for k, v in _read("shops.json").items():
        SHOPS[k] = dict(v, id=k)
    LANDS.extend(_read("lands.json"))
    RACOES.update(_read("racoes.json"))
    RECEITAS.update(_read("receitas.json"))
    FERREIRO.update(_read("ferreiro.json"))
    FUNC.update(_read("funcionario.json"))
    ROTINA.update(_read("rotina.json"))
    GUIA.extend(_read("guia.json"))
    _make_tool_tiers()

    for cid, c in CROPS.items():
        _add_item(dict(id="semente_" + cid, nome="Semente de " + c["nome"], kind="seed", crop=cid,
                       compra=c["semente"], venda=c["semente"] // 2, cor=c["cor"], stack=99,
                       desc="Cresce em: " + ", ".join(c["estacoes"]) + f" ({c['dias']} dias)."))
        _add_item(dict(id=cid, nome=c["nome"], kind="crop", crop=cid, venda=c["venda"], cor=c["cor"],
                       forma=c["forma"], stack=99, desc="Colheita fresca."))
    for sid, s in STRUCTS.items():
        preco = s.get("custo", {}).get("dinheiro", 0)
        _add_item(dict(id=sid, nome=s["nome"], kind="placeable", struct=sid, compra=preco,
                       venda=preco // 2, cor=s.get("cor", [150, 110, 70]), stack=s.get("stack", 1),
                       desc=s.get("desc", "")))


def item(item_id):
    return ITEMS[item_id]


def sell_price(item_id, quality=0):
    return int(ITEMS[item_id].get("venda", 0) * config.QUALITY_MULT[quality])


load_all()

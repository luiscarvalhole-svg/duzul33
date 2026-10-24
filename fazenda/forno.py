"""Forno de fundição: minério + carvão -> barras, com tempo de processamento. Lógica pura (sem pygame).

Estados: "desligado" (livre), "funcionando" (fundindo) e "pronto" (barras esperando retirada).
Os dados ficam em inst["data"] e entram no save junto com a construção:
  estado, receita (id da barra), lotes, restante (minutos de jogo), saida {barra: n},
  por ("jogador" | "funcionario"), reserva (dinheiro reservado para o funcionário), pagos (barras já pagas).
Receitas e tempos ficam em data/ferreiro.json ("fundicao").
"""
from . import data

DESLIGADO, FUNCIONANDO, PRONTO = "desligado", "funcionando", "pronto"
NOMES = {DESLIGADO: "Desligado", FUNCIONANDO: "Funcionando", PRONTO: "Pronto"}


def fornos(state):
    return [i for i in state.structs.by_id.values() if i["s"] == "forno"]


def dados(inst):
    d = inst["data"]
    d.setdefault("estado", DESLIGADO)
    d.setdefault("receita", None)
    d.setdefault("lotes", 0)
    d.setdefault("restante", 0.0)
    d.setdefault("saida", {})
    d.setdefault("por", "jogador")
    d.setdefault("reserva", 0)
    d.setdefault("pagos", 0)
    return d


def receitas():
    return data.FERREIRO["fundicao"]


def max_lotes():
    return int(data.FUNC.get("max_lotes_forno", 4))


def livre(inst):
    d = dados(inst)
    return d["estado"] == DESLIGADO and not d["saida"]


def max_possivel(inv, bar):
    """Quantos lotes dá para fazer com o que há no inventário `inv` (limitado ao máximo do forno)."""
    r = receitas()[bar]
    return max(0, min(max_lotes(), inv.count(r["minerio"]) // r["n"], inv.count("carvao") // r["carvao"]))


def faltando(inv, bar, lotes=1):
    r = receitas()[bar]
    falta = []
    if inv.count(r["minerio"]) < r["n"] * lotes:
        falta.append(f"{data.ITEMS[r['minerio']]['nome']} x{r['n'] * lotes - inv.count(r['minerio'])}")
    if inv.count("carvao") < r["carvao"] * lotes:
        falta.append(f"Carvão x{r['carvao'] * lotes - inv.count('carvao')}")
    return falta


def check_start(inv, inst, bar, lotes=1):
    if bar not in receitas():
        return False, "Receita desconhecida."
    if lotes < 1 or lotes > max_lotes():
        return False, f"Escolha de 1 a {max_lotes()} lote(s)."
    if not livre(inst):
        return False, "O forno está ocupado."
    falta = faltando(inv, bar, lotes)
    if falta:
        return False, "Faltam: " + ", ".join(falta) + "."
    return True, ""


def start(inv, inst, bar, lotes=1, por="jogador", reserva=0):
    """Valida e inicia. Os ingredientes saem de `inv` UMA vez só, agora. Retorna (ok, msg)."""
    ok, msg = check_start(inv, inst, bar, lotes)
    if not ok:
        return False, msg
    r = receitas()[bar]
    inv.remove(r["minerio"], r["n"] * lotes)
    inv.remove("carvao", r["carvao"] * lotes)
    d = dados(inst)
    d.update(estado=FUNCIONANDO, receita=bar, lotes=lotes, restante=float(r["minutos"] * lotes), saida={},
             por=por, reserva=int(reserva), pagos=0)
    return True, f"Fundindo {lotes}x {data.ITEMS[bar]['nome']}."


def tempo_restante(inst):
    d = dados(inst)
    return d["restante"] if d["estado"] == FUNCIONANDO else 0.0


def progresso(inst):
    d = dados(inst)
    if d["estado"] == PRONTO:
        return 1.0
    if d["estado"] != FUNCIONANDO or not d["receita"]:
        return 0.0
    total = receitas()[d["receita"]]["minutos"] * d["lotes"]
    return max(0.0, min(1.0, 1 - d["restante"] / total))


def update(state, minutos):
    """Passa `minutos` de tempo de jogo em todos os fornos acesos. Sem esperas bloqueantes."""
    for inst in fornos(state):
        d = dados(inst)
        if d["estado"] != FUNCIONANDO:
            continue
        d["restante"] -= minutos
        if d["restante"] <= 0:
            d["restante"] = 0.0
            d["estado"] = PRONTO
            d["saida"] = {d["receita"]: d["lotes"]}


def tem_saida(inst):
    return bool(dados(inst)["saida"])


def retirar(state, inst, inv):
    """Passa as barras prontas para `inv` (só o que couber; o resto fica no forno). Retorna {barra: n} retirado."""
    d = dados(inst)
    tirado = {}
    for bar, n in list(d["saida"].items()):
        k = n
        while k > 0 and not inv.can_add(bar, k):
            k -= 1
        if k > 0:
            inv.add(bar, k)
            tirado[bar] = tirado.get(bar, 0) + k
            if n - k > 0:
                d["saida"][bar] = n - k
            else:
                del d["saida"][bar]
    if d["estado"] == PRONTO and not d["saida"]:
        d.update(estado=DESLIGADO, receita=None, lotes=0, restante=0.0)
    return tirado

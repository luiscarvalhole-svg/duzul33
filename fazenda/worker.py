"""Funcionário contratável, pago por tarefa concluída (sem salário fixo e sem experiência). Lógica pura.

Tudo vem de data/funcionario.json: tarefas, preços, taxa de contratação. O funcionário só faz o que você contratou,
só cobra pelo que realmente terminou, e o dinheiro de uma operação longa (fundição) fica reservado até ela acabar.
Os dados dele ficam em state.worker; o histórico de dias fica em state.worker_hist (e vira o relatório na mesa da casa).
"""
import random

from . import animals as an
from . import crafting, data, forno, orchard, storage
from .inventory import Inventory

ORDEM = ["fundir", "plantar", "adubar", "regar", "colher", "racao", "animais", "frutas"]
TAREFAS = {k: v["nome"] for k, v in data.FUNC["tarefas"].items()}
NOMES = ["Zé", "Tião", "Lúcia", "Dona Rosa", "Beto", "Nilda"]


def cfg(t):
    return data.FUNC["tarefas"][t]


def preco(t):
    return int(cfg(t)["preco"])


def taxa():
    return int(data.FUNC.get("taxa_contratacao", 0))


def hired(state):
    return state.worker is not None


def estrutura_ok(state, t):
    """(ok, motivo): tarefas que dependem de construções só podem ser contratadas se elas existirem."""
    need = cfg(t).get("estruturas")
    if not need:
        return True, ""
    if any(i["s"] in need for i in state.structs.by_id.values()):
        return True, ""
    return False, cfg(t).get("motivo") or ("Precisa de: " + " ou ".join(data.STRUCTS[n]["nome"] for n in need))


def disponivel(state, t):
    return estrutura_ok(state, t)[0]


def novo_log(dia):
    return {"dia": dia, "tarefas": {}, "falhas": {}, "consumido": {}, "producao": {}, "fundidos": {}, "total": 0}


def normalizar(w, dia=0):
    """Deixa um dict de funcionário (inclusive de saves antigos) no formato atual."""
    if not isinstance(w, dict) or "tarefas" not in w:
        return None
    w = dict(w)
    w["tarefas"] = {k: bool(w["tarefas"].get(k, k != "fundir")) for k in TAREFAS}
    w.setdefault("nome", "Ajudante")
    w["dias"] = int(w.get("dias", 0))
    w["reservado"] = int(w.get("reservado", 0))
    w["taxa"] = int(w.get("taxa", 0))
    w["total_gasto"] = int(w.get("total_gasto", 0))
    w["bloq"] = dict(w["bloq"]) if isinstance(w.get("bloq"), dict) else {}
    w.setdefault("relatorio", "Ainda não trabalhou.")
    h = w.get("hoje")
    w["hoje"] = h if isinstance(h, dict) and "tarefas" in h else novo_log(dia)
    return w


def hire(state, tarefas=None):
    """Contrata com as tarefas escolhidas (padrão: todas as disponíveis). Cobra a taxa única de contratação."""
    if hired(state):
        return False, "Você já tem um funcionário."
    sel = list(tarefas) if tarefas is not None else [t for t in ORDEM if disponivel(state, t)]
    if any(t not in TAREFAS for t in sel):
        return False, "Tarefa inexistente."
    if not sel:
        return False, "Escolha pelo menos uma tarefa."
    for t in sel:
        ok, why = estrutura_ok(state, t)
        if not ok:
            return False, f"{TAREFAS[t]}: {why}."
    if state.money < taxa():
        return False, f"Faltam ${taxa() - state.money} para a taxa de contratação."
    state.money -= taxa()
    nome = NOMES[state.clock.day % len(NOMES)]
    state.worker = normalizar({"nome": nome, "dias": 0, "taxa": taxa(), "tarefas": {k: (k in sel) for k in TAREFAS}}, state.clock.day)
    return True, f"{nome} foi contratado! Taxa única: ${taxa()}. Você só paga pelo serviço feito."


def fire(state):
    if not hired(state):
        return False, "Você não tem funcionário."
    nome = state.worker["nome"]
    for inst in forno.fornos(state):          # lote em andamento não se perde: passa a ser seu, sem cobrança
        d = forno.dados(inst)
        if d["por"] == "funcionario":
            d["por"], d["reserva"] = "jogador", 0
    state.worker = None
    return True, f"{nome} foi dispensado."


def is_on(state, tarefa):
    return bool(state.worker and state.worker["tarefas"].get(tarefa, False))


def set_tarefa(state, t, on):
    """Liga/desliga uma tarefa a qualquer momento. Não cancela o que ele já está fazendo nem duplica pagamento."""
    if not hired(state):
        return False, "Você não tem funcionário."
    if t not in TAREFAS:
        return False, "Tarefa inexistente."
    if on:
        ok, why = estrutura_ok(state, t)
        if not ok:
            return False, why + "."
    state.worker["tarefas"][t] = bool(on)
    return True, f"{TAREFAS[t]}: {'ligada' if on else 'desligada'}."


def toggle(state, tarefa):
    if hired(state) and tarefa in TAREFAS:
        return set_tarefa(state, tarefa, not is_on(state, tarefa))
    return False, ""


class _View:
    """Faz de conta que o 'estado' tem como inventário o quartinho: assim as mesmas funções de sempre servem."""

    def __init__(self, state, inv):
        object.__setattr__(self, "_s", state)
        object.__setattr__(self, "inv", inv)

    def __getattr__(self, k):
        return getattr(self._s, k)

    def __setattr__(self, k, v):
        setattr(self._s, k, v)


def _boxes(state):
    return [i for i in state.structs.by_id.values() if i["s"] == "quartinho"]


def _open_pool(state):
    """Junta os quartinhos num inventário só. Sem quartinho, o funcionário usa o seu inventário."""
    boxes = _boxes(state)
    if not boxes:
        return None, state.inv
    pool = Inventory(sum(storage.capacity(b) for b in boxes))
    for b in boxes:
        for sl in storage.inv(b).slots:
            if sl:
                pool.add(sl["i"], sl["n"], sl["q"])
    return boxes, pool


def _close_pool(state, boxes, pool):
    if boxes is None:
        return
    novos = [Inventory(storage.capacity(b)) for b in boxes]
    for sl in pool.slots:
        if not sl:
            continue
        for nb in novos:
            if nb.can_add(sl["i"], sl["n"], sl["q"]):
                nb.add(sl["i"], sl["n"], sl["q"])
                break
        else:
            state.inv.add(sl["i"], sl["n"], sl["q"]) if state.inv.can_add(sl["i"], sl["n"], sl["q"]) else None
    for b, nb in zip(boxes, novos):
        b["data"]["bau"] = nb.to_list()


def _has_item(pool, kind):
    return [sl["i"] for sl in pool.slots if sl and data.ITEMS[sl["i"]]["kind"] == kind]


# ------------------------------------------------------------ dinheiro, reservas e registro do dia
def reservado(state):
    """Dinheiro separado para fundições em andamento (ainda não pago, mas já garantido)."""
    return sum(forno.dados(i)["reserva"] for i in forno.fornos(state) if forno.dados(i)["por"] == "funcionario")


def disponivel_dinheiro(state):
    return max(0, state.money - reservado(state))


def _hoje(state):
    w = state.worker
    if w["hoje"].get("dia") != state.clock.day:           # dia novo: começa um registro novo
        w["hoje"] = novo_log(state.clock.day)
    return w["hoje"]


def _soma(d, k, n=1):
    d[k] = d.get(k, 0) + n


def _conta(state, t, n=1, consumiu=None, produziu=None):
    h = _hoje(state)
    reg = h["tarefas"].setdefault(t, {"un": 0, "pago": 0})
    reg["un"] += n
    for it, q in (consumiu or {}).items():
        _soma(h["consumido"], it, q)
    for it, q in (produziu or {}).items():
        _soma(h["producao"], it, q)


def _falha(state, t, motivo):
    h = _hoje(state)
    h["falhas"].setdefault(t, motivo)                      # um motivo por tarefa por dia (sem spam)


def pagar(state, t, n):
    """Paga n unidades FEITAS da tarefa t. Nunca deixa o dinheiro negativo. Retorna o valor pago."""
    if n <= 0 or not hired(state):
        return 0
    valor = min(preco(t) * n, max(0, state.money))
    state.money -= valor
    h = _hoje(state)
    reg = h["tarefas"].setdefault(t, {"un": 0, "pago": 0})
    reg["pago"] += valor
    h["total"] += valor
    state.worker["total_gasto"] += valor
    if valor < preco(t) * n:
        _falha(state, t, "dinheiro acabou antes de pagar tudo")
    return valor


def pode_pagar(state, t, n=1):
    return disponivel_dinheiro(state) >= preco(t) * n


def _agora(state):
    return state.clock.day * 100000 + int(state.clock.minutes)


def _bloqueado(state, key):
    return state.worker["bloq"].get(key, -1) > _agora(state)


def _bloquear(state, key, minutos=90):
    """Depois de uma falha, não tenta o mesmo serviço de novo por um tempo (evita laço infinito)."""
    state.worker["bloq"][key] = _agora(state) + minutos


def _chave(job):
    return f"{job['t']}:{job.get('tile') or job.get('id') or job.get('tipo') or job.get('acao') or ''}"


def _tile_pos(x, y):
    return (x + .5, y + 1.15)


def _inst_pos(state, inst):
    w, h = _dims(inst)
    return (inst["x"] + w / 2, inst["y"] + h + .6)


def _dims(inst):
    from .building import Structures
    return Structures.dims(data.STRUCTS[inst["s"]], inst["rot"])


def _dist(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _estruturas_animais(state):
    return [i for i in state.structs.by_id.values() if "feed_max" in data.STRUCTS[i["s"]]]




# ------------------------------------------------------------ o que há para fazer
def _forno_pos(state, inst):
    return _inst_pos(state, inst)


def _receita_para(pool):
    """Melhor receita de fundição possível agora com o que está no quartinho: (barra, lotes) ou None."""
    for bar in ("barra_ferro", "barra_cobre", "barra_ouro"):
        if bar in forno.receitas():
            n = forno.max_possivel(pool, bar)
            if n >= 1:
                return bar, n
    return None


def _jobs_fundir(state, pool):
    out = []
    for inst in forno.fornos(state):
        d = forno.dados(inst)
        if d["por"] == "funcionario" and forno.tem_saida(inst):
            out.append({"t": "fundir", "acao": "coletar", "id": inst["id"], "pos": _inst_pos(state, inst)})
        elif forno.livre(inst):
            r = _receita_para(pool)
            if r:
                out.append({"t": "fundir", "acao": "carregar", "id": inst["id"], "bar": r[0], "lotes": r[1],
                            "pos": _inst_pos(state, inst)})
        # forno funcionando: ele espera sem travar e faz outras tarefas
    return out


def _jobs_of(state, tarefa, pool, season):
    """Todos os trabalhos possíveis de um tipo, no momento."""
    out = []
    soil = state.farm.soil
    if tarefa == "plantar":
        seeds = [sid for sid in _has_item(pool, "seed") if pool.count(sid) and season in data.CROPS[data.ITEMS[sid]["crop"]]["estacoes"]]
        if seeds:
            for (x, y), s in soil.items():
                if not s["crop"]:
                    out.append({"t": "plantar", "tile": (x, y), "seed": seeds[0], "pos": _tile_pos(x, y)})
    elif tarefa == "adubar":
        ferts = _has_item(pool, "fertilizer")
        if ferts:
            for (x, y), s in soil.items():
                if s["crop"] and not s["fert"] and not state.farm.ripe(x, y):
                    out.append({"t": "adubar", "tile": (x, y), "fert": ferts[0], "pos": _tile_pos(x, y)})
    elif tarefa == "regar":
        if any(data.ITEMS[sl["i"]].get("tool") == "regador" for sl in pool.slots if sl):
            for (x, y), s in soil.items():
                if s["crop"] and not s["wet"]:
                    out.append({"t": "regar", "tile": (x, y), "pos": _tile_pos(x, y)})
    elif tarefa == "colher":
        for (x, y), s in soil.items():
            if s["crop"] and state.farm.ripe(x, y) and pool.can_add(s["crop"]["id"], 1, 2):
                out.append({"t": "colher", "tile": (x, y), "pos": _tile_pos(x, y)})
    elif tarefa == "racao":
        est = _estruturas_animais(state)
        tipos = sorted({t for i in est for t in data.STRUCTS[i["s"]].get("aceita", []) if t in data.RACOES})
        v = _View(state, pool)
        mix = next((i for i in state.structs.by_id.values() if data.STRUCTS[i["s"]].get("interage") == "racao"), None)
        box = next(iter(_boxes(state)), None)
        alvo = mix or box
        for tipo in tipos:
            if pool.count(an.racao_id(tipo)) < 12 and crafting.can_craft(v, tipo, 1):
                out.append({"t": "racao", "tipo": tipo, "pos": _inst_pos(state, alvo) if alvo else None})
    elif tarefa == "animais":
        for inst in _estruturas_animais(state):
            sd = data.STRUCTS[inst["s"]]
            comidas = ["feno"] + [an.racao_id(t) for t in sd.get("aceita", [])]
            pode = any(pool.count(c) > 0 and an.stock(inst, c) < sd["feed_max"] for c in comidas)
            pronto = any(a["pronto"] for a in an.of_home(state.animals, inst["id"]))
            if pode or pronto:
                out.append({"t": "animais", "id": inst["id"], "pos": _inst_pos(state, inst)})
    elif tarefa == "fundir":
        out = _jobs_fundir(state, pool)
    elif tarefa == "frutas":
        for inst in state.structs.by_id.values():
            if orchard.ready(inst):
                out.append({"t": "frutas", "id": inst["id"], "pos": _inst_pos(state, inst)})
    return out



def next_job(state, near=(0.0, 0.0)):
    """Próximo trabalho: o mais perto, da primeira tarefa ligada que tenha o que fazer, que dê para pagar e não esteja bloqueado."""
    if state.worker is None:
        return None
    boxes, pool = _open_pool(state)
    season = state.clock.season
    for tarefa in ORDEM:
        if not is_on(state, tarefa) or not disponivel(state, tarefa):
            continue
        jobs = [j for j in _jobs_of(state, tarefa, pool, season) if not _bloqueado(state, _chave(j))]
        if not jobs:
            continue
        if not pode_pagar(state, tarefa, 1):                       # sem dinheiro para essa tarefa: tenta as outras
            _falha(state, tarefa, "sem dinheiro para pagar o serviço")
            continue
        for j in jobs:
            if j["pos"] is None:
                j["pos"] = tuple(near)
        return min(jobs, key=lambda j: _dist(j["pos"], near))
    return None


def do_job(state, job, rng=random):
    """Executa um trabalho. Só paga pelo que de fato foi feito. Retorna True se fez alguma coisa."""
    if state.worker is None:
        return False
    t = job["t"]
    if not is_on(state, t):                                         # você desligou a tarefa no meio: não faz nem cobra
        return False
    boxes, pool = _open_pool(state)
    v = _View(state, pool)
    ok = False
    soil = state.farm.soil
    if not pode_pagar(state, t, 1):
        _falha(state, t, "sem dinheiro para pagar o serviço")
        _bloquear(state, _chave(job))
        return False
    if t == "plantar":
        x, y = job["tile"]
        if pool.count(job["seed"]) and state.farm.plant(x, y, data.ITEMS[job["seed"]]["crop"], state.clock.season)[0]:
            pool.remove(job["seed"], 1)
            _conta(state, t, 1, {job["seed"]: 1})
            pagar(state, t, 1)
            ok = True
    elif t == "adubar":
        x, y = job["tile"]
        if pool.count(job["fert"]) and state.farm.fertilize(x, y, data.ITEMS[job["fert"]]["fert"])[0]:
            pool.remove(job["fert"], 1)
            _conta(state, t, 1, {job["fert"]: 1})
            pagar(state, t, 1)
            ok = True
    elif t == "regar":
        s = soil.get(tuple(job["tile"]))
        if s and s["crop"] and not s["wet"]:
            s["wet"] = True
            _conta(state, t, 1)
            pagar(state, t, 1)
            ok = True
    elif t == "colher":
        x, y = job["tile"]
        s = soil.get((x, y))
        if s and s["crop"] and state.farm.ripe(x, y) and pool.can_add(s["crop"]["id"], 1, 2):
            h = state.farm.harvest(x, y, 0, rng)
            pool.add(h["item"], h["qty"], h["q"])
            state.stats["colhidos"] = state.stats.get("colhidos", 0) + 1
            state.add_xp("agricultura", h["xp"])
            _conta(state, t, 1, None, {h["item"]: h["qty"]})
            pagar(state, t, 1)
            ok = True
    elif t == "racao":
        if crafting.can_craft(v, job["tipo"], 1):
            r = crafting.recipe(job["tipo"])
            crafting.craft(v, job["tipo"], 1)
            _conta(state, t, 1, r["ingredientes"], {r["item"]: r["rende"]})
            pagar(state, t, 1)
            ok = True
    elif t == "animais":
        inst = state.structs.by_id.get(job["id"])
        if inst:
            bichos = len(an.of_home(state.animals, inst["id"]))
            if bichos and not pode_pagar(state, t, bichos):
                _falha(state, t, "sem dinheiro para pagar o serviço")
                _bloquear(state, _chave(job))
                _close_pool(state, boxes, pool)
                return False
            n = an.add_feed(v, inst, None, "feno")
            for tipo in data.STRUCTS[inst["s"]].get("aceita", []):
                n += an.add_feed(v, inst, None, an.racao_id(tipo))
            got, xp = an.collect(v, inst["id"])
            if got:
                state.add_xp("pecuaria", xp)
            if n or got:
                _conta(state, t, bichos, None, None)
                pagar(state, t, bichos)
            ok = bool(n or got)
    elif t == "frutas":
        inst = state.structs.by_id.get(job["id"])
        if inst and orchard.ready(inst):
            good, _ = orchard.harvest(v, inst)
            if good:
                _conta(state, t, 1)
                pagar(state, t, 1)
                ok = True
    elif t == "fundir":
        ok = _fundir(state, job, pool)
    _close_pool(state, boxes, pool)
    if not ok:
        _bloquear(state, _chave(job), 60)
    return ok


def _fundir(state, job, pool):
    inst = state.structs.by_id.get(job["id"])
    if inst is None or inst["s"] != "forno":
        return False
    d = forno.dados(inst)
    if job["acao"] == "carregar":
        bar = job["bar"]
        lotes = min(forno.max_possivel(pool, bar), job["lotes"])
        lotes = min(lotes, disponivel_dinheiro(state) // preco("fundir"))      # só o que dá para pagar
        if lotes < 1:
            _falha(state, "fundir", "sem dinheiro para pagar a fundição")
            return False
        if not forno.livre(inst):
            _falha(state, "fundir", "forno ocupado")
            return False
        r = forno.receitas()[bar]
        ok, msg = forno.start(pool, inst, bar, lotes, "funcionario", preco("fundir") * lotes)
        if not ok:
            _falha(state, "fundir", msg)
            return False
        h = _hoje(state)
        _soma(h["consumido"], r["minerio"], r["n"] * lotes)
        _soma(h["consumido"], "carvao", r["carvao"] * lotes)
        _soma(h["fundidos"], r["minerio"], r["n"] * lotes)
        return True
    # coletar
    if not forno.tem_saida(inst) or d["por"] != "funcionario":
        return False
    cabe = forno.retirar(state, inst, pool)
    if not cabe:
        _falha(state, "fundir", "quartinho cheio: barras ficaram no forno")
        return False
    n = sum(cabe.values())
    por_barra = max(1, d["lotes"] and (d["reserva"] // max(1, d["lotes"])) or preco("fundir"))
    _conta(state, "fundir", n, None, cabe)
    pagar(state, "fundir", n)
    d["pagos"] += n
    d["reserva"] = max(0, d["reserva"] - por_barra * n)
    if not forno.tem_saida(inst):                                   # terminou tudo: libera a sobra da reserva
        d["reserva"], d["por"], d["pagos"] = 0, "jogador", 0
    return True


def liberar_forno(state, inst):
    """Chamado quando o jogador mesmo retira as barras de um lote do funcionário: nada é cobrado, a reserva é liberada."""
    d = forno.dados(inst)
    d["reserva"], d["por"], d["pagos"] = 0, "jogador", 0


def _avisos(state):
    boxes, pool = _open_pool(state)
    av = []
    soil = state.farm.soil
    if is_on(state, "plantar") and any(not s["crop"] for s in soil.values()) and not _has_item(pool, "seed"):
        av.append("sem sementes")
    if is_on(state, "regar") and any(s["crop"] and not s["wet"] for s in soil.values()) \
            and not any(data.ITEMS[sl["i"]].get("tool") == "regador" for sl in pool.slots if sl):
        av.append("sem regador" + (" no quartinho" if boxes else ""))
    if is_on(state, "colher") and any(s["crop"] and state.farm.ripe(x, y) for (x, y), s in soil.items()):
        av.append("quartinho cheio" if boxes else "inventário cheio")
    if is_on(state, "fundir") and not any(True for _ in forno.fornos(state)):
        av.append("sem forno")
    return av


def texto_log(log):
    partes = []
    for t in ORDEM:
        r = log["tarefas"].get(t)
        if r and r["un"]:
            partes.append(f"{TAREFAS[t]}: {r['un']} {cfg(t)['unidade']}(s) = ${r['pago']}")
    return partes


def work(state, rng=random):
    """Fim do dia: termina o que dava para fazer, fecha o registro do dia, guarda no histórico e põe o relatório na mesa.
    Não há salário: só o que foi feito foi pago. Retorna um resumo (ou None sem funcionário)."""
    w = state.worker
    if w is None:
        return None
    for _ in range(3000):
        job = next_job(state, (0.0, 0.0))
        if job is None:
            break
        do_job(state, job, rng)                 # se falhar, o serviço fica bloqueado e o laço segue para o próximo
    log = _hoje(state)
    log["problemas"] = list(dict.fromkeys(_avisos(state) + [f"{TAREFAS[t]}: {m}" for t, m in log["falhas"].items()]))
    log["nome"], log["data"] = w["nome"], _data_txt(state)
    w["dias"] += 1
    partes = texto_log(log)
    texto = ("; ".join(partes) if partes else "não teve o que fazer") + f". Total pago: ${log['total']}"
    if log["problemas"]:
        texto += " (" + "; ".join(log["problemas"]) + ")"
    w["relatorio"] = f"{w['nome']}: {texto}"
    hist = state.worker_hist
    hist.append(log)
    del hist[:-int(data.FUNC.get("historico_dias", 14))]
    state.worker_novo = True
    w["bloq"] = {}
    w["hoje"] = novo_log(state.clock.day + 1)
    return w["relatorio"]


def _data_txt(state):
    return f"Dia {state.clock.day_of_season} de {state.clock.season.capitalize()} (dia {state.clock.day + 1} do jogo)"


# ------------------------------------------------------------ informações para as telas
def estimativa(state, tarefas=None):
    """Quanto ele faria AGORA com o que existe na fazenda: {tarefa: (unidades, custo)}. Serve só para você se planejar."""
    boxes, pool = _open_pool(state)
    out = {}
    for t in (tarefas if tarefas is not None else ORDEM):
        if not disponivel(state, t):
            out[t] = (0, 0)
            continue
        jobs = _jobs_of(state, t, pool, state.clock.season)
        if t == "animais":
            un = sum(len(an.of_home(state.animals, j["id"])) for j in jobs)
        elif t == "fundir":
            un = sum(j.get("lotes", 0) for j in jobs if j.get("acao") == "carregar")
            un += sum(sum(forno.dados(state.structs.by_id[j["id"]])["saida"].values()) for j in jobs if j.get("acao") == "coletar")
        else:
            un = len(jobs)
        out[t] = (un, un * preco(t))
    return out


def em_andamento(state):
    """Linhas de texto sobre o que ele está fazendo/esperando agora (fornos acesos, etc.)."""
    out = []
    for inst in forno.fornos(state):
        d = forno.dados(inst)
        if d["por"] != "funcionario":
            continue
        if d["estado"] == forno.FUNCIONANDO:
            out.append(f"Forno: fundindo {d['lotes']}x {data.ITEMS[d['receita']]['nome']} (faltam {int(d['restante'])} min). Reservado: ${d['reserva']}")
        elif forno.tem_saida(inst):
            out.append(f"Forno: barras prontas esperando coleta. Reservado: ${d['reserva']}")
    return out


def custo_hoje(state):
    return _hoje(state)["total"] if hired(state) else 0

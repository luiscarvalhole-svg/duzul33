"""Rotina dos lojistas pelo relógio do jogo (lógica pura, sem pygame).

A posição de cada lojista é uma função do horário: ele sai de casa a pé e chega à loja na hora de abrir, trabalha até
fechar, volta andando para casa e dorme. Nada é teletransportado e nada precisa ser salvo: o save já guarda o relógio,
então a rotina volta exatamente ao ponto certo ao carregar. Horários e velocidade: data/rotina.json.
"""
import math

from . import data

TRABALHANDO, INDO_PARA_CASA, DORMINDO, INDO_PARA_LOJA = "TRABALHANDO", "INDO_PARA_CASA", "DORMINDO", "INDO_PARA_LOJA"


def posto(shop_id):
    """Onde ele fica atendendo (ao lado da porta da loja)."""
    sh = data.SHOPS[shop_id]
    x, y, w, h = sh["local"]
    return (x + w // 2 + 1.6, y + h + 0.6)


def caminho(shop_id):
    c = data.SHOPS[shop_id]["casa"]
    return [posto(shop_id)] + [tuple(p) for p in c["rota"]] + [tuple(c["porta"])]


def _comprimento(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def duracao(shop_id):
    """Minutos de jogo que a caminhada loja <-> casa leva."""
    return _comprimento(caminho(shop_id)) / float(data.ROTINA["velocidade"])


def _ao_longo(pts, frac):
    total = _comprimento(pts)
    alvo = max(0.0, min(1.0, frac)) * total
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if alvo <= seg and seg > 0:
            f = alvo / seg
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), (b[0] - a[0], b[1] - a[1])
        alvo -= seg
    return pts[-1], (0, 1)


def estado(shop_id, minutes):
    """(estado, (x, y), direção) do lojista. `minutes` = minutos desde as 06:00 do dia."""
    pts = caminho(shop_id)
    t = duracao(shop_id)
    abre = (data.ROTINA["abre"] - 6) * 60
    fecha = (data.ROTINA["fecha"] - 6) * 60
    sai = max(0.0, abre - t)
    if minutes < sai:
        return DORMINDO, pts[-1], (0, 1)
    if minutes < abre:
        pos, d = _ao_longo(list(reversed(pts)), (minutes - sai) / t)
        return INDO_PARA_LOJA, pos, d
    if minutes < fecha:
        return TRABALHANDO, pts[0], (0, 1)
    if minutes < fecha + t:
        pos, d = _ao_longo(pts, (minutes - fecha) / t)
        return INDO_PARA_CASA, pos, d
    return DORMINDO, pts[-1], (0, 1)


def aberta(shop_id, minutes):
    return estado(shop_id, minutes)[0] == TRABALHANDO


def motivo_fechada(shop_id, minutes):
    e = estado(shop_id, minutes)[0]
    if e == TRABALHANDO:
        return ""
    quando = f"{data.ROTINA['abre']}h"
    return {DORMINDO: "O lojista está dormindo.", INDO_PARA_CASA: "O lojista já fechou e está indo para casa.",
            INDO_PARA_LOJA: "O lojista ainda está a caminho da loja."}[e] + f" A loja abre às {quando} e fecha às {data.ROTINA['fecha']}h."

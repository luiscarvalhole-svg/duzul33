"""Salvar e carregar em JSON, com vários slots. A escrita é atômica (arquivo temporário + os.replace)
para que uma queda de energia no meio do salvamento não corrompa o save anterior."""
import json
import os
import time

from . import config
from .clock import Clock
from .config import SAVE_FILE
from .state import GameState


def slot_path(n):
    """Caminho do slot n (1, 2, 3...). O slot 1 é o mesmo arquivo dos saves antigos (slot1.json)."""
    return os.path.join(config.SAVE_DIR, f"slot{n}.json")


def save_game(state, path=SAVE_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False)
    os.replace(tmp, path)


def load_game(path=SAVE_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return GameState.from_dict(json.load(f))


def save_exists(path=SAVE_FILE):
    return os.path.isfile(path)


def slot_info(n):
    """Resumo do slot para mostrar no menu. None = vazio. {"erro": True} = arquivo ilegível."""
    path = slot_path(n)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        c = Clock.from_dict(d["clock"])
        return {"estacao": c.season, "dia": c.day_of_season, "ano": c.year, "hora": c.hhmm(),
                "dinheiro": int(d["money"]),
                "quando": time.strftime("%d/%m/%Y %H:%M", time.localtime(os.path.getmtime(path)))}
    except Exception:
        return {"erro": True}


def any_save():
    return any(slot_info(n) is not None for n in range(1, config.SAVE_SLOTS + 1))


def delete_slot(n):
    try:
        os.remove(slot_path(n))
        return True
    except OSError:
        return False

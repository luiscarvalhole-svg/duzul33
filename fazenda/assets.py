"""Carrega as imagens (pixel art em PNG) da pasta assets/. Se faltar o arquivo, devolve None e o jogo desenha por código."""
import os

import pygame

from .config import BASE_DIR

ASSETS = os.path.join(BASE_DIR, "assets")
_cache = {}


def load(rel, size=None):
    """rel: caminho dentro de assets/ (ex.: 'sprites/tools/picareta_1.png'). size: (w, h) opcional (ampliação sem suavizar)."""
    key = (rel, size)
    if key in _cache:
        return _cache[key]
    try:
        img = pygame.image.load(os.path.join(ASSETS, *rel.split("/"))).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
    except Exception:
        img = None
    _cache[key] = img
    return img


def tool_name(it):
    """Nome do arquivo (sem .png) da ferramenta: ex. 'picareta_2'. None se não for ferramenta com sprite."""
    if it.get("kind") != "tool":
        return None
    t = it.get("tool")
    if t in ("foice", "rede"):
        return f"{t}_0"
    return f"{t}_{it.get('nivel', 0)}" if t else None


def tool_sprite(name, size=None):
    return load(f"sprites/tools/{name}.png", size) if name else None


PLAYER_DIRS = {(0, -1): "cima", (0, 1): "baixo", (-1, 0): "esquerda", (1, 0): "direita"}


def player_frame(facing, moving, t):
    d = PLAYER_DIRS.get(tuple(facing), "baixo")
    name = f"{d}_{int(t * 8) % 4}" if moving else f"{d}_parado"
    return load(f"sprites/player/{name}.png", (50, 59))        # 44x52 original, um pouco maior (~15%)


def item_sprite(item_id, size=None):
    """Ícone em pixel art do item (assets/sprites/items/<id>.png): sementes, colheitas, comidas, minérios etc."""
    return load(f"sprites/items/{item_id}.png", size) if item_id else None


def plant_sprite(crop_id, stage):
    """Planta no canteiro (16x16 ampliada 2x -> 32x32, do tamanho de um bloco), estágios 0..3."""
    return load(f"sprites/plants/{crop_id}_{stage}.png", (32, 32))

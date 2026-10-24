"""Preferências do jogador que valem para TODOS os saves: teclas, modo de tela e zoom.

Ficam em saves/config.json (separado dos slots de salvamento).
"""
import json
import os

import pygame

from . import config

# (id da ação, nome na tela, tecla padrão)
ACTIONS = [
    ("cima", "Andar para cima", pygame.K_w),
    ("baixo", "Andar para baixo", pygame.K_s),
    ("esquerda", "Andar para a esquerda", pygame.K_a),
    ("direita", "Andar para a direita", pygame.K_d),
    ("usar", "Usar item / ferramenta", pygame.K_SPACE),
    ("interagir", "Interagir (lojas, casa...)", pygame.K_e),
    ("inventario", "Inventário", pygame.K_i),
    ("construir", "Modo construção", pygame.K_b),
    ("mapa", "Mapa e terrenos", pygame.K_m),
    ("ajuda", "Ajuda", pygame.K_h),
    ("salvar", "Salvar rápido", pygame.K_F5),
    ("girar", "Girar construção", pygame.K_r),
    ("grade", "Mostrar/ocultar grade", pygame.K_g),
    ("trator", "Montar/descer do trator", pygame.K_t),
    ("dev", "Menu de desenvolvedor", pygame.K_F10),
]
DEFAULT_KEYS = {a: k for a, _, k in ACTIONS}
LABELS = {a: n for a, n, _ in ACTIONS}

SCREEN_MODES = [("janela", "Janela"), ("redimensionavel", "Janela redimensionável"), ("cheia", "Tela cheia")]


def prefs_path():
    return os.path.join(config.SAVE_DIR, "config.json")


def _reserved(key):
    """Teclas que não podem ser trocadas: Esc (cancela) e os números (barra rápida)."""
    return key == pygame.K_ESCAPE or pygame.K_0 <= key <= pygame.K_9


class Prefs:
    def __init__(self):
        self.keys = dict(DEFAULT_KEYS)
        self.screen = "janela"
        self.zoom = 1.0

    # ------------------------------------------------------------ teclas
    def key(self, action):
        return self.keys[action]

    def key_name(self, action):
        n = pygame.key.name(self.keys[action])
        return (n or "?").upper()

    def rebind(self, action, key):
        """Troca a tecla de uma ação. Se outra ação já usa essa tecla, as duas trocam de lugar.
        Retorna (ok, mensagem)."""
        if action not in self.keys:
            return False, "Ação desconhecida."
        if _reserved(key):
            return False, "Esc e as teclas de número (barra rápida) não podem ser trocadas."
        old = self.keys[action]
        for other, k in self.keys.items():
            if other != action and k == key:
                self.keys[other] = old
                self.keys[action] = key
                self.save()
                return True, f"{LABELS[action]}: {self.key_name(action)}  (trocou com \"{LABELS[other]}\")"
        self.keys[action] = key
        self.save()
        return True, f"{LABELS[action]}: {self.key_name(action)}"

    def reset_keys(self):
        self.keys = dict(DEFAULT_KEYS)
        self.save()

    # ------------------------------------------------------------ tela
    def set_screen(self, mode):
        if mode in dict(SCREEN_MODES):
            self.screen = mode
            self.save()

    def set_zoom(self, z):
        self.zoom = max(config.ZOOM_MIN, min(config.ZOOM_MAX, round(z * 4) / 4))
        self.save()

    # ------------------------------------------------------------ arquivo
    def to_dict(self):
        return {"keys": dict(self.keys), "screen": self.screen, "zoom": self.zoom}

    def save(self):
        try:
            path = prefs_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f)
            os.replace(tmp, path)
        except OSError:
            pass          # preferências são "melhor esforço": nunca derrubam o jogo

    @classmethod
    def load(cls):
        p = cls()
        try:
            with open(prefs_path(), "r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            return p
        if not isinstance(d, dict):
            return p
        keys = d.get("keys")
        if isinstance(keys, dict):
            cand = dict(p.keys)
            for a, k in keys.items():
                if a in cand and isinstance(k, int) and not isinstance(k, bool) and not _reserved(k):
                    cand[a] = k
            if len(set(cand.values())) == len(cand):      # sem teclas repetidas
                p.keys = cand
        if d.get("screen") in dict(SCREEN_MODES):
            p.screen = d["screen"]
        z = d.get("zoom")
        if isinstance(z, (int, float)) and not isinstance(z, bool):
            p.zoom = max(config.ZOOM_MIN, min(config.ZOOM_MAX, round(float(z) * 4) / 4))
        return p

"""Efeitos sonoros sintetizados por código (sem arquivos de áudio). Sem placa de som, roda mudo."""
import math
import random
from array import array

import pygame

SR = 22050


def synth(segs, vol=0.4):
    """segs: lista de (freq_inicial, freq_final, duração_s, onda). Retorna amostras de 16 bits."""
    buf = array("h")
    for f0, f1, dur, wave in segs:
        n = max(1, int(SR * dur))
        ph = lp = 0.0
        for i in range(n):
            k = i / n
            ph += 2 * math.pi * (f0 + (f1 - f0) * k) / SR
            if wave == "sine":
                v = math.sin(ph)
            elif wave == "square":
                v = 0.6 if math.sin(ph) >= 0 else -0.6
            elif wave == "lownoise":
                lp += 0.07 * (random.uniform(-1, 1) - lp)
                v = lp * 5
            elif wave == "hinoise":
                v = random.uniform(-1, 1) * 0.7
            else:
                v = 0.0
            env = min(1.0, i / (SR * 0.004)) * (1 - k) ** 1.3
            buf.append(int(32767 * vol * max(-1.0, min(1.0, v)) * env))
    return buf


def _make():
    S = {
        "hoe": synth([(140, 80, 0.13, "lownoise")], 0.9),
        "water": synth([(0, 0, 0.22, "hinoise")], 0.2),
        "plant": synth([(300, 650, 0.09, "sine")], 0.5),
        "harvest": synth([(660, 660, 0.07, "sine"), (990, 990, 0.14, "sine")], 0.45),
        "chop": synth([(180, 90, 0.09, "lownoise")], 0.9),
        "break": synth([(120, 60, 0.2, "lownoise")], 1.0),
        "coin": synth([(1250, 1250, 0.06, "square"), (1700, 1700, 0.16, "square")], 0.16),
        "buy": synth([(900, 1100, 0.07, "square"), (1300, 1300, 0.1, "square")], 0.16),
        "error": synth([(170, 120, 0.18, "square")], 0.2),
        "eat": synth([(300, 200, 0.06, "lownoise"), (320, 220, 0.06, "lownoise")], 0.8),
        "cluck": synth([(650, 480, 0.05, "square"), (0, 0, 0.04, "none"), (560, 430, 0.07, "square")], 0.16),
        "moo": synth([(150, 105, 0.55, "sine")], 0.55),
        "sleep": synth([(440, 330, 0.25, "sine"), (330, 220, 0.4, "sine")], 0.4),
        "rooster": synth([(520, 760, 0.14, "sine"), (760, 560, 0.2, "sine")], 0.35),
        "click": synth([(800, 800, 0.03, "square")], 0.12),
        "build": synth([(220, 160, 0.08, "lownoise"), (330, 330, 0.06, "sine")], 0.7),
    }
    return {k: pygame.mixer.Sound(buffer=v.tobytes()) for k, v in S.items()}


class Audio:
    def __init__(self, enabled=True):
        self.ok, self.on, self.snd = False, enabled, {}
        try:
            if pygame.mixer.get_init() != (SR, -16, 1):
                pygame.mixer.quit()
                pygame.mixer.init(SR, -16, 1, 512)
            self.snd = _make()
            self.ok = True
        except Exception:
            self.ok = False

    def play(self, name):
        if self.ok and self.on and name in self.snd:
            self.snd[name].play()

    def toggle(self):
        self.on = not self.on
        if not self.on and self.ok:
            pygame.mixer.stop()
        return self.on

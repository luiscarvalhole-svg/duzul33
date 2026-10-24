"""Controles de toque na tela (para a versão web / celular). Sem toque ligado, não faz nada.

Botões: direcional (andar), USAR (segurar), E (interagir), Inv, Mapa, Obra, Trator e PAUSA.
Os toques viram as mesmas teclas que o jogo já usa (as do menu Configurações), então nada mais muda no jogo.
Ligue com `--touch` no comando, ou automaticamente na versão web / no primeiro toque na tela.
"""
import os
import sys
import time

import pygame

from .config import SCREEN_H as SH, SCREEN_W as SW

DIR = {"cima": (110, SH - 190), "baixo": (110, SH - 60), "esquerda": (45, SH - 125), "direita": (175, SH - 125)}
# nome: (centro, raio, rótulo, ação do jogo)
BOTOES = {
    "usar": ((SW - 100, SH - 110), 52, "USAR", "usar"),
    "interagir": ((SW - 225, SH - 175), 36, "E", "interagir"),
    "inventario": ((SW - 40, 250), 28, "Inv", "inventario"),
    "mapa": ((SW - 40, 312), 28, "Mapa", "mapa"),
    "construir": ((SW - 40, 374), 28, "Obra", "construir"),
    "trator": ((SW - 40, 436), 28, "Trat", "trator"),
    "pausa": ((SW - 40, 100), 28, "Esc", None),
}
for _n, _c in DIR.items():
    BOTOES[_n] = (_c, 34, {"cima": "^", "baixo": "v", "esquerda": "<", "direita": ">"}[_n], _n)
SEGURAR = {"cima", "baixo", "esquerda", "direita", "usar"}
MODOS_JOGO = ("play", "casa", "mina")


def post(key):
    for t in (pygame.KEYDOWN, pygame.KEYUP):
        pygame.event.post(pygame.event.Event(t, key=key, mod=0, unicode="", scancode=0))


class Touch:
    def __init__(self, prefs_key):
        self.key = prefs_key                       # função: nome da ação -> tecla
        self.enabled = (sys.platform == "emscripten" or "--touch" in sys.argv
                        or "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ)
        self.ativos = {}                           # id do dedo/mouse -> botão
        self.ultimo = {}                           # botão -> instante do último disparo (evita disparo duplo)
        self.fonte = None
        self._surf = None

    # ---------------------------------------------------------------- lógica
    def visiveis(self, modo):
        if modo in ("title", "slots", "settings"):
            return []
        if modo in MODOS_JOGO:
            return list(BOTOES)
        return ["pausa"]

    def botao_em(self, pos, modo):
        for nome in self.visiveis(modo):
            (cx, cy), r, _, _ = BOTOES[nome]
            if (pos[0] - cx) ** 2 + (pos[1] - cy) ** 2 <= (r + 8) ** 2:
                return nome
        return None

    def teclas_seguradas(self):
        """Teclas que estão 'apertadas' pelos toques neste instante."""
        out = set()
        for nome in set(self.ativos.values()):
            if nome in SEGURAR:
                out.add(self.key(BOTOES[nome][3]))
        return out

    def _disparar(self, nome):
        agora = time.time()
        if agora - self.ultimo.get(nome, 0) < 0.18:       # dedo + mouse emulado = o mesmo toque
            return
        self.ultimo[nome] = agora
        acao = BOTOES[nome][3]
        post(pygame.K_ESCAPE if nome == "pausa" else self.key(acao))

    def _apertar(self, ident, pos, modo):
        nome = self.botao_em(pos, modo)
        antigo = self.ativos.get(ident)
        if nome == antigo:
            return nome is not None
        if antigo is not None:
            del self.ativos[ident]
        if nome is not None:
            self.ativos[ident] = nome
            if not any(n == nome for i, n in self.ativos.items() if i != ident) or nome not in SEGURAR:
                self._disparar(nome)
        return nome is not None

    def handle(self, e, modo):
        """Retorna True se o evento era um toque num botão da tela (o jogo não deve usá-lo)."""
        if not self.enabled and getattr(pygame, "FINGERDOWN", None) is not None and e.type == pygame.FINGERDOWN:
            self.enabled = True
        if not self.enabled:
            return False
        fd, fu, fm = (getattr(pygame, n, None) for n in ("FINGERDOWN", "FINGERUP", "FINGERMOTION"))
        t = e.type
        if fd is not None and t in (fd, fu, fm):
            pos, ident = (e.x * SW, e.y * SH), ("f", getattr(e, "finger_id", 0))
            if t == fu:
                return self.ativos.pop(ident, None) is not None
            return self._apertar(ident, pos, modo)
        if t == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1:
            return self._apertar("m", e.pos, modo)
        if t == pygame.MOUSEMOTION and "m" in self.ativos:
            self._apertar("m", e.pos, modo)
            return True
        if t == pygame.MOUSEBUTTONUP and getattr(e, "button", 1) == 1:
            return self.ativos.pop("m", None) is not None
        return False

    # ---------------------------------------------------------------- desenho
    def draw(self, screen, modo):
        if not self.enabled:
            return
        vis = self.visiveis(modo)
        if not vis:
            return
        if self._surf is None:
            self._surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        s = self._surf
        s.fill((0, 0, 0, 0))
        down = set(self.ativos.values())
        for nome in vis:
            (cx, cy), r, rot, _ = BOTOES[nome]
            on = nome in down
            pygame.draw.circle(s, (255, 255, 255, 120 if on else 60), (cx, cy), r)
            pygame.draw.circle(s, (30, 20, 14, 170), (cx, cy), r, 3)
            fonte = self.fonte
            if fonte is not None:
                img = fonte.render(rot, True, (255, 255, 255))
                s.blit(img, img.get_rect(center=(cx, cy)))
        screen.blit(s, (0, 0))

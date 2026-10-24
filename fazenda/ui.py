"""Interfaces (tudo desenhado por código). Estilo imediato: os botões são registrados a cada quadro."""
import math

import pygame

from . import animals as an
from . import bank, cooking, forno, mine, smithing, crafting, data, dev, fishing, shops, sprites, stall, storage, worker
from .save import slot_info
from .config import (SCREEN_H, SCREEN_W, SEASON_LABEL, SKILL_LABEL, SKILLS, WEATHER_LABEL, XP_LEVELS, MAX_ENERGY,
                     HOTBAR, QUALITY_NAME, SAVE_SLOTS, WATER_CAPACITY, ZOOM_MAX, ZOOM_MIN)
from .inventory import CATEGORIAS
from .prefs import ACTIONS, SCREEN_MODES
from .state import level_for
from .world import FOREST, GRASS, PLAZA, ROAD, ROCK, SAND, WATER

INK, SUB = (70, 45, 25), (120, 88, 56)
PARCH, PARCH2 = (238, 222, 182), (222, 203, 158)


def _hoje_reg(w, s, t):
    h = w.get('hoje', {})
    if h.get('dia') != s.clock.day:
        return {'un': 0, 'pago': 0}
    return h['tarefas'].get(t, {'un': 0, 'pago': 0})


class UI:
    def __init__(self):
        mk = lambda n: pygame.font.SysFont("arial,helvetica,dejavusans", n, bold=True)
        self.f_xs, self.f_s, self.f_m, self.f_b, self.f_t = mk(13), mk(16), mk(21), mk(30), mk(46)
        self.buttons = []
        self.hotbar_rects = []
        self.inv_rects = []
        self.dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 150))
        self._mini = None

    # ------------------------------------------------------------ básicos
    def begin(self):
        self.buttons = []

    def click(self, pos):
        for rect, fn in reversed(self.buttons):
            if rect.collidepoint(pos):
                fn()
                return True
        return False

    def over_button(self, pos):
        return any(r.collidepoint(pos) for r, _ in self.buttons)

    def text(self, screen, s, font, color, pos, anchor="topleft", shadow=False):
        img = font.render(str(s), True, color)
        r = img.get_rect(**{anchor: pos})
        if shadow:
            borda = font.render(str(s), True, (24, 14, 8))               # contorno nítido de 1 pixel (mais legível que sombra borrada)
            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
                screen.blit(borda, (r.x + ox, r.y + oy))
        screen.blit(img, r)
        return r

    def _rivet(self, screen, x, y, r=3):
        pygame.draw.circle(screen, (40, 26, 16), (x, y), r + 1)
        pygame.draw.circle(screen, (226, 178, 90), (x, y), r)
        pygame.draw.circle(screen, (255, 236, 170), (x - 1, y - 1), max(1, r // 2))

    def frame(self, screen, r, fill=(44, 30, 22), alpha=None):
        """Moldura de bronze com cantos e rebites (estilo RPG medieval)."""
        r = pygame.Rect(r)
        pygame.draw.rect(screen, (30, 20, 14), r.inflate(4, 4), border_radius=9)
        pygame.draw.rect(screen, (150, 104, 52), r, border_radius=8)
        pygame.draw.rect(screen, (226, 178, 90), r.inflate(-2, -2), 1, border_radius=8)
        inner = r.inflate(-8, -8)
        pygame.draw.rect(screen, (58, 38, 24), inner, border_radius=5)
        pygame.draw.rect(screen, fill, inner.inflate(-4, -4), border_radius=4)
        for cx, cy in ((r.x + 5, r.y + 5), (r.right - 6, r.y + 5), (r.x + 5, r.bottom - 6), (r.right - 6, r.bottom - 6)):
            self._rivet(screen, cx, cy, 2)

    def panel(self, screen, rect, color=(30, 24, 18), alpha=190, radius=12, border=(255, 220, 140)):
        r = pygame.Rect(rect)
        tmp = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*color, 225), tmp.get_rect(), border_radius=8)
        screen.blit(tmp, r.topleft)
        if border:
            pygame.draw.rect(screen, (30, 20, 14), r.inflate(2, 2), 2, border_radius=9)
            pygame.draw.rect(screen, (170, 120, 58), r, 3, border_radius=8)
            pygame.draw.rect(screen, (232, 188, 100), r.inflate(-4, -4), 1, border_radius=6)
            for cx, cy in ((r.x + 2, r.y + 2), (r.right - 3, r.y + 2), (r.x + 2, r.bottom - 3), (r.right - 3, r.bottom - 3)):
                self._rivet(screen, cx, cy, 2)

    def window(self, screen, rect, title):
        r = pygame.Rect(rect)
        screen.blit(self.dim, (0, 0))
        pygame.draw.rect(screen, (24, 14, 8), r.inflate(22, 22).move(0, 5), border_radius=20)           # sombra
        pygame.draw.rect(screen, (30, 20, 14), r.inflate(18, 18), border_radius=17)
        pygame.draw.rect(screen, (150, 104, 52), r.inflate(14, 14), border_radius=15)
        pygame.draw.rect(screen, (226, 178, 90), r.inflate(10, 10), 2, border_radius=13)
        pygame.draw.rect(screen, (96, 64, 34), r.inflate(6, 6), border_radius=11)
        pygame.draw.rect(screen, PARCH, r, border_radius=8)
        for i in range(0, r.h, 6):                                                                      # fibras do pergaminho
            c = (232, 214, 172) if (i // 6) % 2 else (240, 224, 186)
            pygame.draw.line(screen, c, (r.x + 4, r.y + i), (r.right - 5, r.y + i), 1)
        pygame.draw.rect(screen, (196, 160, 104), r.inflate(-10, -10), 2, border_radius=6)
        for cx, cy in ((r.x - 4, r.y - 4), (r.right + 3, r.y - 4), (r.x - 4, r.bottom + 3), (r.right + 3, r.bottom + 3),
                       (r.centerx, r.y - 6), (r.centerx, r.bottom + 5), (r.x - 6, r.centery), (r.right + 5, r.centery)):
            self._rivet(screen, cx, cy, 4)
        tw = self.f_b.render(str(title), True, (0, 0, 0)).get_width()
        pw = max(220, tw + 100)
        px0, py0 = r.centerx - pw // 2, r.y - 14
        pts = [(px0 - 14, py0 + 24), (px0, py0), (px0 + pw, py0), (px0 + pw + 14, py0 + 24), (px0 + pw, py0 + 48), (px0, py0 + 48)]
        pygame.draw.polygon(screen, (30, 20, 14), [(a + (2 if a > r.centerx else -2), b) for a, b in pts])
        pygame.draw.polygon(screen, (170, 120, 58), pts)
        pygame.draw.polygon(screen, (52, 34, 22), [(px0 - 8, py0 + 24), (px0 + 3, py0 + 4), (px0 + pw - 3, py0 + 4), (px0 + pw + 8, py0 + 24),
                                                  (px0 + pw - 3, py0 + 44), (px0 + 3, py0 + 44)])
        pygame.draw.line(screen, (226, 178, 90), (px0 + 6, py0 + 5), (px0 + pw - 6, py0 + 5), 1)
        self.text(screen, title, self.f_b, (255, 226, 140), (r.centerx, py0 + 24), "center")
        return r

    def button(self, screen, rect, label, fn, enabled=True, base=(90, 150, 70), font=None, active=False):
        rect = pygame.Rect(rect)
        hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
        col = base if enabled else (150, 142, 128)
        if hover:
            col = tuple(min(255, v + 30) for v in col)
        hi = tuple(min(255, int(v * 1.28) + 10) for v in col)
        lo = tuple(int(v * .72) for v in col)
        pygame.draw.rect(screen, (30, 20, 14), rect.inflate(2, 2).move(0, 2), border_radius=9)         # contorno e sombra
        pygame.draw.rect(screen, lo, rect, border_radius=8)
        pygame.draw.rect(screen, col, (rect.x, rect.y, rect.w, rect.h - 4), border_radius=8)
        pygame.draw.rect(screen, hi, (rect.x + 3, rect.y + 2, rect.w - 6, max(2, rect.h // 3)), border_radius=6)   # brilho
        pygame.draw.rect(screen, (30, 20, 14), rect, 2, border_radius=8)
        if active:
            pygame.draw.rect(screen, (255, 230, 120), rect.inflate(4, 4), 2, border_radius=10)
        lum = 0.3 * col[0] + 0.59 * col[1] + 0.11 * col[2]                  # texto limpo, sem sombra: escuro em botão claro, branco em escuro
        cor = (45, 30, 20) if lum > 135 else (255, 255, 255)
        self.text(screen, label, font or self.f_s, cor if enabled else (70, 60, 50), rect.center, "center")
        if enabled:
            self.buttons.append((rect, fn))

    def bar(self, screen, rect, frac, col, bg=(70, 60, 50)):
        r = pygame.Rect(rect)
        pygame.draw.rect(screen, (30, 20, 14), r.inflate(4, 4), border_radius=6)
        pygame.draw.rect(screen, (150, 104, 52), r.inflate(2, 2), 1, border_radius=6)
        pygame.draw.rect(screen, (34, 26, 22), r, border_radius=4)
        w = int(r.w * max(0, min(1, frac)))
        if w > 0:
            pygame.draw.rect(screen, tuple(int(v * .75) for v in col), (r.x, r.y, w, r.h), border_radius=4)
            pygame.draw.rect(screen, col, (r.x, r.y, w, max(2, r.h - 4)), border_radius=4)
            pygame.draw.rect(screen, tuple(min(255, v + 70) for v in col), (r.x + 2, r.y + 1, max(0, w - 4), max(1, r.h // 4)), border_radius=2)

    def star(self, screen, x, y, q):
        col = (200, 204, 214) if q == 1 else (255, 205, 40)
        pts = [(x + math.cos(-math.pi / 2 + i * math.pi / 5) * (6 if i % 2 == 0 else 2.6),
                y + math.sin(-math.pi / 2 + i * math.pi / 5) * (6 if i % 2 == 0 else 2.6)) for i in range(10)]
        pygame.draw.polygon(screen, col, pts)
        pygame.draw.polygon(screen, (60, 40, 20), pts, 1)

    def slot(self, screen, rect, slot, selected=False, dim=False, gold=False, key=None):
        r = pygame.Rect(rect)
        pygame.draw.rect(screen, (28, 18, 12), r, border_radius=7)
        pygame.draw.rect(screen, (150, 104, 52) if not gold else (214, 164, 70), r.inflate(-2, -2), 2, border_radius=6)
        pygame.draw.rect(screen, (48, 36, 30), r.inflate(-8, -8), border_radius=4)
        pygame.draw.line(screen, (30, 22, 18), (r.x + 5, r.y + 5), (r.right - 6, r.y + 5), 2)
        pygame.draw.line(screen, (74, 58, 48), (r.x + 5, r.bottom - 6), (r.right - 6, r.bottom - 6), 1)
        if slot:
            it = data.ITEMS[slot["i"]]
            sprites.draw_icon(screen, it, r)
            if slot["n"] > 1:
                self.text(screen, slot["n"], self.f_xs, (255, 255, 255), (r.right - 4, r.bottom - 3), "bottomright", True)
            if slot["q"]:
                self.star(screen, r.x + 10, r.bottom - 10, slot["q"])
            if dim:
                d = pygame.Surface(r.size, pygame.SRCALPHA)
                d.fill((20, 14, 10, 170))
                screen.blit(d, r.topleft)
        if key is not None:
            kr = pygame.Rect(r.x + 2, r.y + 2, 16, 15)
            pygame.draw.rect(screen, (24, 18, 14), kr, border_radius=3)
            pygame.draw.rect(screen, (150, 104, 52), kr, 1, border_radius=3)
            self.text(screen, key, self.f_xs, (255, 240, 200), kr.center, "center")
        if selected:
            pygame.draw.rect(screen, (96, 170, 250), r.inflate(2, 2), 3, border_radius=8)
            pygame.draw.rect(screen, (190, 224, 255), r.inflate(-2, -2), 1, border_radius=7)

    # ------------------------------------------------------------ HUD
    def draw_hud(self, screen, g):
        s = g.state
        self.panel(screen, (12, 10, 150, 44))
        pygame.draw.circle(screen, (255, 208, 60), (36, 32), 12)
        pygame.draw.circle(screen, (200, 150, 20), (36, 32), 12, 2)
        self.text(screen, "$", self.f_s, (150, 100, 10), (36, 32), "center")
        self.text(screen, s.money, self.f_m, (255, 230, 120), (56, 32), "midleft", True)

        self.panel(screen, (172, 10, 330, 44))
        c = s.clock
        self.text(screen, f"{SEASON_LABEL[c.season]} {c.day_of_season}  -  Ano {c.year}", self.f_s, (255, 255, 255), (186, 20), shadow=True)
        self.text(screen, f"{c.hhmm()}   {WEATHER_LABEL[s.weather]}", self.f_s, (255, 230, 150), (186, 38), shadow=True)
        self._weather_icon(screen, 468, 32, s.weather, g.t)
        self.text(screen, "Amanhã: " + WEATHER_LABEL[s.forecast], self.f_xs, (210, 210, 220), (400, 40), "midtop")

        self.panel(screen, (SCREEN_W - 212, 10, 200, 44))
        self.text(screen, "Energia", self.f_xs, (255, 255, 255), (SCREEN_W - 202, 14), shadow=True)
        frac = s.energy / MAX_ENERGY
        self.bar(screen, (SCREEN_W - 202, 30, 180, 14), frac, (90, 200, 90) if frac > .3 else (220, 80, 60))

        # barra rápida
        total = HOTBAR * 54 + (HOTBAR - 1) * 4
        x0, y0 = (SCREEN_W - total) // 2, SCREEN_H - 66
        self.frame(screen, (x0 - 14, y0 - 8, total + 28, 70), (40, 28, 22))
        self.hotbar_rects = []
        for i in range(HOTBAR):
            r = pygame.Rect(x0 + i * 58, y0, 54, 54)
            self.hotbar_rects.append(r)
            self.slot(screen, r, s.inv.slots[i], selected=(i == s.sel), key=(i + 1) % 10)
        sl = s.inv.slots[s.sel]
        if sl:
            it = data.ITEMS[sl["i"]]
            label = it["nome"]
            if it.get("tool") == "regador":
                label += f"  ({s.water}/{s.water_cap()})"
            self.text(screen, label, self.f_s, (255, 255, 255), (SCREEN_W // 2, y0 - 6), "midbottom", True)
        if g.prompt:
            self.text(screen, g.prompt, self.f_m, (255, 240, 140), (SCREEN_W // 2, y0 - 30), "midbottom", True)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_m, g.msg_col, (SCREEN_W // 2, 70), "midtop", True)

    def _weather_icon(self, screen, x, y, kind, t):
        if kind == "sol":
            for i in range(8):
                a = i * math.pi / 4 + t
                pygame.draw.line(screen, (255, 220, 80), (x + math.cos(a) * 12, y + math.sin(a) * 12),
                                 (x + math.cos(a) * 17, y + math.sin(a) * 17), 2)
            pygame.draw.circle(screen, (255, 220, 60), (x, y), 10)
            return
        pygame.draw.circle(screen, (200, 206, 220), (x - 6, y), 8)
        pygame.draw.circle(screen, (225, 230, 240), (x + 3, y - 4), 9)
        pygame.draw.circle(screen, (200, 206, 220), (x + 9, y + 1), 7)
        for i in range(3):
            xx = x - 8 + i * 8
            if kind in ("chuva", "tempestade"):
                pygame.draw.line(screen, (100, 170, 240), (xx, y + 10), (xx - 2, y + 17), 2)
            else:
                pygame.draw.circle(screen, (255, 255, 255), (xx, y + 13), 2)
        if kind == "tempestade":
            pygame.draw.polygon(screen, (255, 230, 80), [(x + 2, y + 6), (x - 4, y + 16), (x, y + 16), (x - 2, y + 24), (x + 6, y + 13), (x + 2, y + 13)])

    # ------------------------------------------------------------ inventário
    def draw_inventory(self, screen, g):
        s = g.state
        R = self.window(screen, (40, 50, 944, 620), "Inventário")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        x = R.x + 24
        for i, name in enumerate(CATEGORIAS):
            self.button(screen, (x + i * 98, R.y + 62, 92, 30), name, lambda n=name: setattr(g, "inv_filter", n),
                        True, (150, 100, 50) if g.inv_filter == name else (186, 160, 118), self.f_xs)
        gx, gy = R.x + 24, R.y + 108
        self.inv_rects = []
        flt = CATEGORIAS[g.inv_filter]
        for i, sl in enumerate(s.inv.slots):
            r = pygame.Rect(gx + (i % 10) * 58, gy + (i // 10) * 58, 54, 54)
            self.inv_rects.append(r)
            dim = bool(sl and flt and data.ITEMS[sl["i"]]["kind"] not in flt)
            self.slot(screen, r, sl, selected=(g.inv_sel == i), dim=dim, gold=(i < HOTBAR))
            self.buttons.append((r, lambda i=i: g.inv_click(i)))
        self.text(screen, "Linha dourada = barra rápida (teclas 1-9 e 0). Clique em dois slots para trocar de lugar.",
                  self.f_xs, SUB, (gx, gy + 4 * 58 + 2))
        # detalhes
        dy = gy + 4 * 58 + 26
        pygame.draw.rect(screen, PARCH2, (gx, dy, 574, 100), border_radius=8)
        idx = g.inv_sel
        sl = s.inv.slots[idx] if idx is not None else None
        if sl:
            it = data.ITEMS[sl["i"]]
            sprites.draw_icon(screen, it, pygame.Rect(gx + 8, dy + 14, 64, 64))
            self.text(screen, it["nome"] + (f"  ({QUALITY_NAME[sl['q']]})" if sl["q"] else ""), self.f_m, INK, (gx + 84, dy + 8))
            self.text(screen, it.get("desc", ""), self.f_xs, SUB, (gx + 84, dy + 36))
            if it.get("venda"):
                self.text(screen, f"Valor de venda: ${shops.sell_price_slot(sl)}", self.f_xs, SUB, (gx + 84, dy + 56))
            if it["kind"] == "food":
                self.button(screen, (gx + 84, dy + 70, 90, 24), "Comer", lambda: g.eat(idx), True, (200, 130, 40), self.f_xs)
        else:
            self.text(screen, "Selecione um slot para ver os detalhes.", self.f_s, SUB, (gx + 12, dy + 36))
        # status e habilidades
        px = R.x + 24 + 574 + 24
        pw = R.right - px - 24
        pygame.draw.rect(screen, PARCH2, (px, gy, pw, 4 * 58 + 126), border_radius=8)
        self.text(screen, "Habilidades", self.f_m, INK, (px + 12, gy + 8))
        for i, sk in enumerate(SKILLS):
            y = gy + 44 + i * 46
            xp = s.skills[sk]
            lv = level_for(xp)
            self.text(screen, f"{SKILL_LABEL[sk]}  nv {lv}", self.f_s, INK, (px + 12, y))
            lo = XP_LEVELS[lv]
            hi = XP_LEVELS[lv + 1] if lv + 1 < len(XP_LEVELS) else lo
            self.bar(screen, (px + 12, y + 22, pw - 24, 10), (xp - lo) / (hi - lo) if hi > lo else 1, (90, 170, 220))
        y = gy + 44 + len(SKILLS) * 46 + 6
        self.text(screen, f"Dinheiro: ${s.money}", self.f_s, (30, 110, 40), (px + 12, y))
        self.text(screen, f"Colheitas: {s.stats.get('colhidos', 0)}", self.f_xs, SUB, (px + 12, y + 24))
        self.text(screen, f"Terrenos: {len(s.owned)}/{len(s.world.lands)}", self.f_xs, SUB, (px + 12, y + 42))

    # ------------------------------------------------------------ loja
    def draw_shop(self, screen, g):
        s = g.state
        sh = data.SHOPS[g.shop_id]
        animal = sh.get("tipo") == "animais"
        R = self.window(screen, (40, 40, 944, 640), sh["nome"])
        self.text(screen, f"Atendente: {sh['dono']}", self.f_xs, SUB, (R.x + 24, R.y + 18))
        self.text(screen, f"Dinheiro: ${s.money}", self.f_m, (30, 110, 40), (R.x + 24, R.y + 36))
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        tabs = ("Animais", "Vender produtos", "Seus animais") if animal else ("Comprar", "Vender")
        for i, lb in enumerate(tabs):
            self.button(screen, (R.x + 300 + i * 190, R.y + 62, 180, 30), lb, lambda i=i: g.shop_set_tab(i),
                        True, (150, 100, 50) if g.shop_tab == i else (186, 160, 118), self.f_s)
        lx, ly = R.x + 24, R.y + 108
        if g.shop_tab == 0:
            self._shop_buy(screen, g, R, lx, ly, animal)
        elif g.shop_tab == 2 and animal:
            self._shop_animals(screen, g, R, lx, ly)
        else:
            self._shop_sell(screen, g, R, lx, ly)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 22), "midbottom")

    def _list_rows(self, screen, g, rows, lx, ly, draw_row, row_h=46, visible=10):
        g.shop_scroll = max(0, min(g.shop_scroll, max(0, len(rows) - visible)))
        for k in range(visible):
            i = g.shop_scroll + k
            if i >= len(rows):
                break
            r = pygame.Rect(lx, ly + k * row_h, 520, row_h - 4)
            pygame.draw.rect(screen, (255, 240, 190) if i == g.shop_sel else PARCH2, r, border_radius=8)
            if i == g.shop_sel:
                pygame.draw.rect(screen, (200, 140, 40), r, 3, border_radius=8)
            draw_row(r, rows[i])
            self.buttons.append((r, lambda i=i: g.shop_select(i)))
        if len(rows) > visible:
            self.text(screen, f"Role com o mouse ({g.shop_scroll + 1}-{min(len(rows), g.shop_scroll + visible)} de {len(rows)})",
                      self.f_xs, SUB, (lx, ly + visible * row_h))

    def _qty(self, screen, g, x, y, maxq):
        self.button(screen, (x, y, 50, 32), "-10", lambda: g.shop_add_qty(-10), g.shop_qty > 1, (150, 110, 70), self.f_xs)
        self.button(screen, (x + 54, y, 36, 32), "-", lambda: g.shop_add_qty(-1), g.shop_qty > 1, (150, 110, 70))
        self.text(screen, g.shop_qty, self.f_m, INK, (x + 120, y + 16), "center")
        self.button(screen, (x + 150, y, 36, 32), "+", lambda: g.shop_add_qty(1), g.shop_qty < maxq, (150, 110, 70))
        self.button(screen, (x + 190, y, 50, 32), "+10", lambda: g.shop_add_qty(10), g.shop_qty < maxq, (150, 110, 70), self.f_xs)

    def _shop_buy(self, screen, g, R, lx, ly, animal):
        s = g.state
        px, pw = lx + 540, R.right - (lx + 540) - 24
        if animal:
            rows = shops.animal_entries(s)

            def row(r, e):
                a = data.ANIMALS[e["tipo"]]
                sprites.draw_face(screen, e["tipo"], r.x + 24, r.y + 22, 14)
                self.text(screen, a["nome"], self.f_s, INK, (r.x + 52, r.y + 4))
                self.text(screen, a["desc"] + f"  Requer: {data.STRUCTS[a['predio']]['nome']}", self.f_xs, SUB, (r.x + 52, r.y + 24))
                self.text(screen, f"${a['preco']}", self.f_m, (30, 110, 40) if e["ok_req"] else (160, 60, 40), (r.right - 12, r.centery), "midright")
            self._list_rows(screen, g, rows, lx, ly, row)
            if 0 <= g.shop_sel < len(rows):
                e = rows[g.shop_sel]
                a = data.ANIMALS[e["tipo"]]
                sprites.draw_face(screen, e["tipo"], px + pw - 30, ly + 22, 20)
                self.text(screen, a["nome"], self.f_b, INK, (px, ly))
                self.text(screen, a["desc"], self.f_s, SUB, (px, ly + 40))
                self.text(screen, f"Produz: {data.ITEMS[a['produto']]['nome']} a cada {a['periodo']} dia(s)", self.f_xs, SUB, (px, ly + 66))
                self.text(screen, f"Moradia: {data.STRUCTS[a['predio']]['nome']}", self.f_xs, SUB, (px, ly + 84))
                if e["faltam"]:
                    self.text(screen, "Requer " + ", ".join(e["faltam"]), self.f_xs, (160, 60, 40), (px, ly + 104))
                self.text(screen, f"Preço: ${a['preco']}", self.f_m, INK, (px, ly + 140))
                self.button(screen, (px, ly + 180, 170, 40), "Comprar", lambda t=e["tipo"]: g.buy_animal(t), s.money >= a["preco"], (90, 150, 70), self.f_m)
            return
        rows = shops.shop_entries(s, g.shop_id)

        def row(r, e):
            it = data.ITEMS[e["item"]]
            sprites.draw_icon(screen, it, pygame.Rect(r.x + 4, r.y + 2, 38, 38))
            self.text(screen, it["nome"], self.f_s, INK if e["ok_req"] else (150, 120, 110), (r.x + 50, r.y + 4))
            sub = "Estoque: " + ("ilimitado" if e["estoque"] is None else str(e["estoque"]))
            if not e["ok_req"]:
                sub = "Requer " + ", ".join(f"{SKILL_LABEL[k]} {v}" for k, v in e["req"].items())
            self.text(screen, sub, self.f_xs, SUB, (r.x + 50, r.y + 24))
            if e["oferta"]:
                self.text(screen, "OFERTA -15%", self.f_xs, (190, 50, 40), (r.right - 100, r.y + 6), "midtop")
            self.text(screen, f"${e['preco']}", self.f_m, (30, 110, 40), (r.right - 12, r.centery), "midright")
        self._list_rows(screen, g, rows, lx, ly, row)
        if 0 <= g.shop_sel < len(rows):
            e = rows[g.shop_sel]
            it = data.ITEMS[e["item"]]
            sprites.draw_icon(screen, it, pygame.Rect(px, ly, 72, 72))
            self.text(screen, it["nome"], self.f_m, INK, (px + 84, ly + 4))
            self.text(screen, it.get("desc", "")[:46], self.f_xs, SUB, (px + 84, ly + 32))
            self.text(screen, f"Você tem: {s.inv.count(e['item'])}", self.f_xs, SUB, (px + 84, ly + 52))
            y = ly + 90
            if e["materiais"]:
                self.text(screen, "Materiais (por unidade):", self.f_xs, INK, (px, y))
                for k, (m, n) in enumerate(e["materiais"].items()):
                    ok = s.inv.count(m) >= n * g.shop_qty
                    self.text(screen, f"{data.ITEMS[m]['nome']}: {n * g.shop_qty} (tem {s.inv.count(m)})", self.f_xs,
                              (30, 110, 40) if ok else (160, 60, 40), (px + 8, y + 18 + k * 16))
                y += 22 + len(e["materiais"]) * 16
            maxq = 99 if e["estoque"] is None else max(1, e["estoque"])
            self._qty(screen, g, px, y + 8, maxq)
            total = e["preco"] * g.shop_qty
            self.text(screen, f"Total: ${total}", self.f_m, INK, (px, y + 52))
            ok = e["ok_req"] and s.money >= total and (e["estoque"] is None or e["estoque"] >= g.shop_qty)
            self.button(screen, (px, y + 88, 170, 40), "Comprar", lambda: g.buy_item(e["item"]), ok, (90, 150, 70), self.f_m)

    def _shop_sell(self, screen, g, R, lx, ly):
        s = g.state
        rows = [(i, sl) for i, sl in enumerate(s.inv.slots) if sl and shops.can_sell_here(g.shop_id, sl["i"])]

        def row(r, e):
            i, sl = e
            it = data.ITEMS[sl["i"]]
            sprites.draw_icon(screen, it, pygame.Rect(r.x + 4, r.y + 2, 38, 38))
            self.text(screen, f"{it['nome']}  x{sl['n']}", self.f_s, INK, (r.x + 50, r.y + 4))
            if sl["q"]:
                self.star(screen, r.x + 60, r.y + 32, sl["q"])
                self.text(screen, QUALITY_NAME[sl["q"]], self.f_xs, SUB, (r.x + 72, r.y + 25))
            self.text(screen, f"${shops.sell_price_slot(sl)}", self.f_m, (30, 110, 40), (r.right - 12, r.centery), "midright")
        if not rows:
            self.text(screen, "Você não tem nada que esta loja compre.", self.f_s, SUB, (lx + 12, ly + 12))
        self._list_rows(screen, g, rows, lx, ly, row)
        px = lx + 540
        if 0 <= g.shop_sel < len(rows):
            i, sl = rows[g.shop_sel]
            it = data.ITEMS[sl["i"]]
            sprites.draw_icon(screen, it, pygame.Rect(px, ly, 72, 72))
            self.text(screen, it["nome"], self.f_m, INK, (px + 84, ly + 4))
            self.text(screen, f"Preço unitário: ${shops.sell_price_slot(sl)}", self.f_xs, SUB, (px + 84, ly + 34))
            q = min(g.shop_qty, sl["n"])
            self._qty(screen, g, px, ly + 90, sl["n"])
            self.text(screen, f"Receber: ${shops.sell_price_slot(sl) * q}", self.f_m, INK, (px, ly + 134))
            self.button(screen, (px, ly + 172, 170, 40), "Vender", lambda: g.sell_slot(i, q), True, (200, 130, 40), self.f_m)
        total = sum(shops.sell_price_slot(sl) * sl["n"] for _, sl in rows)
        self.button(screen, (px, ly + 300, 250, 40), f"Vender tudo: ${total}", g.sell_all, total > 0, (60, 140, 80), self.f_m)

    def _shop_animals(self, screen, g, R, lx, ly):
        s = g.state
        rows = list(s.animals)

        def row(r, a):
            info = data.ANIMALS[a["t"]]
            sprites.draw_face(screen, a["t"], r.x + 24, r.y + 22, 14)
            tag = "  (filhote)" if a.get("filhote", 0) > 0 else ""
            self.text(screen, f"{a['nome']} - {info['nome']}{tag}", self.f_s, INK, (r.x + 52, r.y + 4))
            self.text(screen, f"Amizade {a['amizade'] // 10}%   Humor {a['feliz']}%   Saúde {a['saude']}%", self.f_xs, SUB, (r.x + 52, r.y + 24))
            self.text(screen, f"${an.sell_value(a)}", self.f_m, (30, 110, 40), (r.right - 12, r.centery), "midright")
        if not rows:
            self.text(screen, "Você ainda não tem animais.", self.f_s, SUB, (lx + 12, ly + 12))
        self._list_rows(screen, g, rows, lx, ly, row)
        px = lx + 540
        if 0 <= g.shop_sel < len(rows):
            a = rows[g.shop_sel]
            info = data.ANIMALS[a["t"]]
            sprites.draw_face(screen, a["t"], px + 36, ly + 36, 30)
            self.text(screen, f"{a['nome']} ({info['nome']})", self.f_m, INK, (px + 84, ly + 4))
            self.text(screen, "Filhote: vale metade" if a.get("filhote", 0) > 0 else "Adulto", self.f_xs, SUB, (px + 84, ly + 34))
            for j, (lb, v, col) in enumerate((("Amizade", a["amizade"] / 1000, (230, 110, 170)), ("Humor", a["feliz"] / 100, (240, 200, 60)),
                                              ("Saúde", a["saude"] / 100, (220, 80, 80)))):
                self.text(screen, lb, self.f_xs, INK, (px, ly + 84 + j * 24))
                self.bar(screen, (px + 70, ly + 86 + j * 24, 200, 11), v, col)
            self.text(screen, "Quanto mais amizade, humor e saúde, mais a loja paga.", self.f_xs, SUB, (px, ly + 160))
            self.text(screen, f"Preço de venda: ${an.sell_value(a)}", self.f_m, INK, (px, ly + 186))
            armed = g.sell_armed == a["id"]
            self.button(screen, (px, ly + 226, 200, 40), "Certeza? Vender!" if armed else "Vender animal",
                        lambda aid=a["id"]: g.sell_animal(aid), True, (200, 70, 60) if armed else (200, 130, 40), self.f_m)

    # ------------------------------------------------------------ animais
    def draw_animals(self, screen, g):
        s = g.state
        inst = s.structs.by_id.get(g.animals_home)
        if inst is None:
            g.close_menu()
            return
        sd = data.STRUCTS[inst["s"]]
        R = self.window(screen, (60, 24, 904, 672), sd["nome"])
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        mine = [a for a in s.animals if a["home"] == inst["id"]]
        mx = sd["feed_max"]
        self.text(screen, f"Animais: {len(mine)}/{sd['capacidade']}", self.f_m, INK, (R.x + 24, R.y + 58))
        pronto = sum(1 for a in mine if a["pronto"])
        self.button(screen, (R.x + 560, R.y + 54, 150, 34), f"Coletar ({pronto})", g.collect_products, pronto > 0, (90, 150, 70))
        self.button(screen, (R.x + 720, R.y + 54, 110, 34), "Acariciar", g.pet_animals, bool(mine), (220, 120, 150))
        # estoques nos cochos: feno e uma ração por espécie aceita
        feno = an.stock(inst, "feno")
        self.text(screen, f"Feno no cocho: {feno}/{mx}  (no inventário: {s.inv.count('feno')})", self.f_xs, SUB, (R.x + 24, R.y + 92))
        self.bar(screen, (R.x + 24, R.y + 110, 250, 10), feno / mx, (222, 192, 92))
        for k, tipo in enumerate(sd["aceita"]):
            rid = an.racao_id(tipo)
            col, row = k % 2, k // 2
            bx, by = R.x + 300 + col * 290, R.y + 92 + row * 26
            self.text(screen, f"Ração de {data.ANIMALS[tipo]['nome']}: {an.stock(inst, rid)}/{mx}  (inv: {s.inv.count(rid)})", self.f_xs, SUB, (bx, by))
            self.bar(screen, (bx, by + 16, 240, 6), an.stock(inst, rid) / mx, (200, 160, 110))
        # quantidade a colocar + botões de comida
        qy = R.y + 152
        self.text(screen, "Quanto colocar:", self.f_s, INK, (R.x + 24, qy + 6))
        self.button(screen, (R.x + 170, qy, 50, 32), "-10", lambda: g.feed_add_qty(-10), g.feed_qty > 1, (150, 110, 70), self.f_xs)
        self.button(screen, (R.x + 224, qy, 36, 32), "-", lambda: g.feed_add_qty(-1), g.feed_qty > 1, (150, 110, 70))
        self.text(screen, g.feed_qty, self.f_m, INK, (R.x + 290, qy + 16), "center")
        self.button(screen, (R.x + 320, qy, 36, 32), "+", lambda: g.feed_add_qty(1), g.feed_qty < 99, (150, 110, 70))
        self.button(screen, (R.x + 360, qy, 50, 32), "+10", lambda: g.feed_add_qty(10), g.feed_qty < 99, (150, 110, 70), self.f_xs)
        self.button(screen, (R.x + 430, qy, 130, 32), "Colocar feno", lambda: g.feed_building("feno"),
                    s.inv.count("feno") > 0 and feno < mx, (200, 150, 50), self.f_xs)
        for k, tipo in enumerate(sd["aceita"]):
            rid = an.racao_id(tipo)
            self.button(screen, (R.x + 24 + k * 150, qy + 40, 142, 30), f"Ração {data.ANIMALS[tipo]['nome']}", lambda r=rid: g.feed_building(r),
                        s.inv.count(rid) > 0 and an.stock(inst, rid) < mx, (170, 120, 70), self.f_xs)
        self.text(screen, "Ração é fabricada no Misturador de Ração (Carpintaria). Dá mais saúde, humor e amizade.", self.f_xs, SUB, (R.x + 24, qy + 76))
        if not mine:
            self.text(screen, "Nenhum animal aqui. Compre animais na loja de animais.", self.f_s, SUB, (R.x + 24, R.y + 250))
        for k, a in enumerate(mine):
            y = R.y + 250 + k * 60
            r = pygame.Rect(R.x + 24, y, R.w - 48, 54)
            pygame.draw.rect(screen, PARCH2, r, border_radius=8)
            info = data.ANIMALS[a["t"]]
            sprites.draw_animal(screen, a["t"], r.x + 44, r.y + 48, 1, g.t, False, (255, 255, 255), baby=a.get("filhote", 0) > 0)
            tag = "  (filhote)" if a.get("filhote", 0) > 0 else ""
            self.text(screen, f"{a['nome']} ({info['nome']}){tag}", self.f_s, INK, (r.x + 90, r.y + 5))
            prod = data.ITEMS[info["produto"]]["nome"]
            if a.get("filhote", 0) > 0:
                txt, col = f"Crescendo: {a['filhote']} dia(s)", SUB
            else:
                txt, col = f"{prod}: " + ("PRONTO!" if a["pronto"] else f"{a['prog']}/{info['periodo']} dia(s)"), ((30, 130, 50) if a["pronto"] else SUB)
            self.text(screen, txt, self.f_xs, col, (r.x + 90, r.y + 30))
            for j, (lb, v, col) in enumerate((("Fome", 1 - min(a["fome"], 3) / 3, (230, 150, 60)), ("Humor", a["feliz"] / 100, (240, 200, 60)),
                                              ("Saúde", a["saude"] / 100, (220, 80, 80)), ("Amizade", a["amizade"] / 1000, (230, 110, 170)))):
                bx = r.x + 340 + (j % 2) * 240
                by = r.y + 6 + (j // 2) * 24
                self.text(screen, lb, self.f_xs, INK, (bx, by))
                self.bar(screen, (bx + 62, by + 2, 150, 11), v, col)

    # ------------------------------------------------------------ mapa e terrenos
    def minimap(self, world):
        if self._mini is None or self._mini[0] is not world:
            cols = {GRASS: (110, 180, 84), FOREST: (62, 126, 58), SAND: (226, 208, 152), WATER: (58, 128, 200),
                    ROCK: (130, 130, 138), ROAD: (160, 150, 136), PLAZA: (214, 200, 170)}
            surf = pygame.Surface((world.w, world.h))
            for y in range(world.h):
                for x in range(world.w):
                    surf.set_at((x, y), cols[world.ground[y][x]])
            self._mini = (world, pygame.transform.scale(surf, (world.w * 6, world.h * 6)))
        return self._mini[1]

    def draw_map(self, screen, g):
        s = g.state
        w = s.world
        R = self.window(screen, (40, 40, 944, 640), "Mapa e Terrenos")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        mx, my = R.x + 24, R.y + 70
        screen.blit(self.minimap(w), (mx, my))
        for l in w.lands:
            x, y, lw, lh = l["rect"]
            r = pygame.Rect(mx + x * 6, my + y * 6, lw * 6, lh * 6)
            tint = pygame.Surface(r.size, pygame.SRCALPHA)
            tint.fill((60, 200, 80, 70) if l["id"] in s.owned else (40, 40, 40, 110))
            screen.blit(tint, r.topleft)
            sel = g.map_sel == l["id"]
            pygame.draw.rect(screen, (255, 230, 80) if sel else ((90, 220, 100) if l["id"] in s.owned else (230, 230, 230)), r, 3 if sel else 1)
            self.buttons.append((r, lambda lid=l["id"]: setattr(g, "map_sel", lid)))
        for f in w.fixed:
            pygame.draw.rect(screen, (220, 70, 60), (mx + f["x"] * 6, my + f["y"] * 6, f["w"] * 6, f["h"] * 6))
        pygame.draw.circle(screen, (255, 255, 255), (int(mx + s.px * 6), int(my + s.py * 6)), 5)
        pygame.draw.circle(screen, (200, 40, 40), (int(mx + s.px * 6), int(my + s.py * 6)), 3)
        self.text(screen, "Branco = você  |  Vermelho = lojas  |  Verde = seus terrenos  |  Escuro = à venda", self.f_xs, SUB, (mx, my + 440))
        px = mx + 576 + 20
        pw = R.right - px - 20
        pygame.draw.rect(screen, PARCH2, (px, my, pw, 430), border_radius=8)
        land = w.land_by_id(g.map_sel) if g.map_sel else None
        if not land:
            self.text(screen, "Clique em um terreno no mapa", self.f_s, SUB, (px + 12, my + 16))
            return
        self.text(screen, land["nome"], self.f_m, INK, (px + 12, my + 10))
        self.text(screen, f"Tipo: {land['tipo']}   ({land['rect'][2]}x{land['rect'][3]} blocos)", self.f_xs, SUB, (px + 12, my + 40))
        words = land["desc"].split()
        line, y = "", my + 64
        for wd in words:
            if len(line) + len(wd) > 30:
                self.text(screen, line, self.f_xs, SUB, (px + 12, y))
                line, y = "", y + 16
            line += wd + " "
        self.text(screen, line, self.f_xs, SUB, (px + 12, y))
        y += 34
        if land["id"] in s.owned:
            self.text(screen, "VOCÊ JÁ POSSUI ESTE TERRENO", self.f_s, (30, 130, 50), (px + 12, y))
            return
        self.text(screen, f"Preço: ${land['preco']}", self.f_m, INK, (px + 12, y))
        y += 34
        self.text(screen, "Requisitos:", self.f_xs, INK, (px + 12, y))
        y += 18
        reqs = list(land.get("req", {}).items())
        for k, v in reqs:
            ok = s.level(k) >= v
            self.text(screen, f"{SKILL_LABEL[k]} nível {v} (você: {s.level(k)})", self.f_xs, (30, 130, 50) if ok else (160, 60, 40), (px + 12, y))
            y += 16
        if land.get("dia"):
            ok = s.clock.day >= land["dia"]
            self.text(screen, f"A partir do dia {land['dia'] + 1}", self.f_xs, (30, 130, 50) if ok else (160, 60, 40), (px + 12, y))
            y += 16
        ok, _ = s.land_status(land["id"])
        self.button(screen, (px + 12, y + 14, pw - 24, 40), "Comprar terreno", lambda: g.buy_land(land["id"]), ok, (90, 150, 70), self.f_m)

    # ------------------------------------------------------------ construção
    def draw_build_panel(self, screen, g):
        s = g.state
        b = g.build
        y0 = SCREEN_H - 150
        self.panel(screen, (8, y0, SCREEN_W - 16, 142), alpha=220)
        self.text(screen, "MODO CONSTRUÇÃO", self.f_s, (255, 230, 140), (20, y0 + 6), shadow=True)
        for i, (lb, key) in enumerate((("Colocar", "colocar"), ("Mover", "mover"), ("Guardar", "guardar"))):
            self.button(screen, (20 + i * 92, y0 + 30, 86, 28), lb, lambda k=key: g.build_set_mode(k), True,
                        (150, 100, 50), self.f_xs, active=(b["modo"] == key))
        self.button(screen, (20, y0 + 64, 86, 28), "Desfazer", g.build_undo, bool(g.hist.undo_stack), (80, 110, 170), self.f_xs)
        self.button(screen, (112, y0 + 64, 86, 28), "Refazer", g.build_redo, bool(g.hist.redo_stack), (80, 110, 170), self.f_xs)
        self.button(screen, (204, y0 + 64, 80, 28), "Girar [R]", g.build_rotate, True, (110, 90, 150), self.f_xs)
        self.button(screen, (20, y0 + 98, 130, 28), "Grade [G]: " + ("sim" if s.settings["grade"] else "não"), g.toggle_grid, True, (110, 130, 90), self.f_xs)
        self.button(screen, (156, y0 + 98, 128, 28), "Sair [B]", g.exit_build, True, (190, 70, 60), self.f_xs)
        items = g.placeables()
        self.text(screen, "Itens para construir (do inventário):" if items else "Você não tem itens de construção. Compre na Carpintaria!",
                  self.f_xs, (255, 255, 255), (310, y0 + 8))
        per = 14
        g.build_scroll = max(0, min(g.build_scroll, max(0, len(items) - per)))
        for k in range(per):
            i = g.build_scroll + k
            if i >= len(items):
                break
            sid, n = items[i]
            r = pygame.Rect(310 + k * 58, y0 + 28, 54, 54)
            self.slot(screen, r, {"i": sid, "n": n, "q": 0}, selected=(b["sid"] == sid and b["modo"] == "colocar"))
            self.buttons.append((r, lambda sid=sid: g.build_select(sid)))
        info = b.get("info", "")
        col = (120, 255, 140) if b.get("ok") else (255, 140, 120)
        self.text(screen, info, self.f_s, col, (310, y0 + 92))
        helps = {"colocar": "Clique para colocar. Botão direito/Esc cancela. R gira. Ctrl+Z/Ctrl+Y desfaz/refaz.",
                 "mover": "Clique numa construção, depois clique no novo local. Esc cancela.",
                 "guardar": "Clique numa construção para guardá-la no inventário."}
        self.text(screen, helps[b["modo"]], self.f_xs, (220, 220, 230), (310, y0 + 118))

    # ------------------------------------------------------------ menus simples
    def draw_pause(self, screen, g):
        R = self.window(screen, (SCREEN_W // 2 - 200, 80, 400, 600), "Pausado")
        opts = [("Continuar", g.close_menu, (90, 150, 70)), (f"Salvar jogo (slot {g.slot})", g.save, (80, 130, 200)),
                ("Slots: salvar / carregar", lambda: g.open_slots("salvar"), (80, 130, 200)),
                ("Guia do jogo (tutorial)", lambda: (setattr(g, "mode", "guia"), setattr(g, "guia_scroll", 0)), (214, 150, 60)),
                ("Funcionário (contratar / gerenciar)", lambda: (setattr(g, "mode", "quadro"), setattr(g, "contrata_conf", False)), (90, 150, 70)),
                ("Configurações", g.open_settings, (150, 110, 70)),
                ("Menu de desenvolvedor", lambda: setattr(g, "mode", "dev"), (110, 90, 150)),
                ("Menu principal", g.to_title, (200, 130, 40))]
        for i, (lb, fn, col) in enumerate(opts):
            self.button(screen, (R.x + 30, R.y + 70 + i * 60, 340, 50), lb, fn, True, col, self.f_s if len(lb) > 24 else self.f_m)
        if g.msg_t > 0:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 20), "midbottom")

    def draw_confirm(self, screen, g, title, yes):
        R = self.window(screen, (SCREEN_W // 2 - 220, 240, 440, 200), title)
        self.button(screen, (R.x + 50, R.y + 110, 150, 50), "Sim", yes, True, (90, 150, 70), self.f_m)
        self.button(screen, (R.x + 240, R.y + 110, 150, 50), "Não", g.close_menu, True, (190, 70, 60), self.f_m)

    def draw_title(self, screen, g):
        screen.blit(g.title_bg, (0, 0))
        self.text(screen, "FAZENDA RPG", self.f_t, (255, 240, 170), (SCREEN_W // 2, 110), "midtop", True)
        self.text(screen, "Etapa 1 - tudo desenhado por código", self.f_s, (255, 255, 255), (SCREEN_W // 2, 170), "midtop", True)
        opts = [("Novo jogo", lambda: g.open_slots("novo"), (90, 150, 70), True),
                ("Continuar", lambda: g.open_slots("carregar"), (80, 130, 200), g.has_save()),
                ("Configurações", g.open_settings, (110, 120, 140), True),
                ("Sair", g.quit, (190, 70, 60), True)]
        for i, (lb, fn, col, en) in enumerate(opts):
            self.button(screen, (SCREEN_W // 2 - 140, 240 + i * 66, 280, 54), lb, fn, en, col, self.f_m)
        if g.msg_t > 0:
            self.text(screen, g.msg, self.f_s, (255, 220, 160), (SCREEN_W // 2, 520), "midtop", True)

    def draw_help(self, screen, prefs):
        k = prefs.key_name
        mv = [k("cima"), k("esquerda"), k("baixo"), k("direita")]
        mv = "".join(mv) if all(len(x) == 1 for x in mv) else "/".join(mv)
        R = pygame.Rect(SCREEN_W // 2 - 330, 100, 660, 480)
        self.panel(screen, R, alpha=232)
        self.text(screen, "COMO JOGAR", self.f_b, (255, 230, 140), (R.centerx, R.y + 12), "midtop", True)
        lines = [f"{mv} / Setas ...... andar     {k('interagir')} ...... interagir (lojas, casa, animais, portão)",
                 f"{k('usar')} ...... usar o item da barra   |   1-9 e 0 / roda do mouse ...... trocar de item",
                 "MOUSE: clique esquerdo usa o item no bloco apontado (segure para repetir),",
                 "clique direito interage. Ctrl + roda do mouse aproxima/afasta a câmera.",
                 f"{k('inventario')} inventário   {k('construir')} construção   {k('mapa')} mapa e terrenos   Esc pausa   {k('salvar')} salvar   F11 tela cheia",
                 f"As teclas podem ser trocadas em Pausa > Configurações > Teclas.   {k('dev')}: menu de desenvolvedor.",
                 "1) Enxada ara  2) Semente planta  3) Regador rega (encha na torneira)  4) Foice colhe",
                 "Machado corta árvores e arbustos; picareta quebra pedras e desfaz terra arada.",
                 "Plantas só crescem se regadas (ou se chover / aspersor). Elas morrem ao trocar de estação!",
                 "Compre construções na Carpintaria e posicione com B. Durma na casa para passar o dia.",
                 "Compre novos terrenos no Mapa (M) para plantar e construir neles.",
                 "",
                 ">>> Aperte QUALQUER TECLA ou clique para começar <<<"]
        for i, ln in enumerate(lines):
            self.text(screen, ln, self.f_s, (255, 255, 255), (R.x + 22, R.y + 62 + i * 29), shadow=True)

    # ------------------------------------------------------------ slots de salvamento
    def draw_slots(self, screen, g):
        titulo = {"novo": "Novo jogo: escolha um slot", "carregar": "Continuar: escolha um slot",
                  "salvar": "Slots de salvamento"}[g.slot_purpose]
        R = self.window(screen, (SCREEN_W // 2 - 380, 80, 760, 560), titulo)
        if g.slot_purpose == "salvar":
            self.text(screen, "\"Salvar aqui\" grava o jogo atual no slot. \"Jogar\" carrega o que está salvo.", self.f_xs, SUB,
                      (R.x + 24, R.y + 58))
        for n in range(1, SAVE_SLOTS + 1):
            r = pygame.Rect(R.x + 24, R.y + 90 + (n - 1) * 124, R.w - 48, 112)
            pygame.draw.rect(screen, (255, 240, 190) if (g.state is not None and n == g.slot) else PARCH2, r, border_radius=10)
            info = slot_info(n)
            self.text(screen, f"Slot {n}", self.f_m, INK, (r.x + 16, r.y + 10))
            if info is None:
                self.text(screen, "Vazio", self.f_s, SUB, (r.x + 16, r.y + 46))
            elif info.get("erro"):
                self.text(screen, "Arquivo ilegível (pode ser apagado)", self.f_s, (160, 60, 40), (r.x + 16, r.y + 46))
            else:
                self.text(screen, f"{SEASON_LABEL[info['estacao']]} {info['dia']}, Ano {info['ano']}  -  {info['hora']}", self.f_s, INK, (r.x + 16, r.y + 44))
                self.text(screen, f"Dinheiro: ${info['dinheiro']}", self.f_s, (30, 110, 40), (r.x + 16, r.y + 68))
                self.text(screen, f"Salvo em {info['quando']}", self.f_xs, SUB, (r.x + 16, r.y + 92))
            ok = info is not None and not info.get("erro")
            arm_over = g.armed == ("sobrescrever", n)
            if g.slot_purpose == "carregar":
                self.button(screen, (r.right - 190, r.y + 14, 170, 40), "Jogar", lambda n=n: g.slot_click(n), ok, (90, 150, 70), self.f_m)
            elif g.slot_purpose == "novo":
                lb = "Sobrescrever?" if arm_over else ("Novo jogo" if info is None else "Novo aqui")
                self.button(screen, (r.right - 190, r.y + 14, 170, 40), lb, lambda n=n: g.slot_click(n), True,
                            (200, 130, 40) if arm_over else (90, 150, 70), self.f_m)
            else:
                lb = "Sobrescrever?" if arm_over else "Salvar aqui"
                self.button(screen, (r.right - 190, r.y + 14, 170, 40), lb, lambda n=n: g.slot_click(n), True,
                            (200, 130, 40) if arm_over else (80, 130, 200), self.f_m)
                if ok:
                    self.button(screen, (r.right - 190, r.y + 60, 80, 36), "Jogar", lambda n=n: g.load(n), True, (90, 150, 70), self.f_s)
            if info is not None:
                armed = g.armed == ("apagar", n)
                self.button(screen, (r.right - 100, r.y + 60, 80, 36), "Certeza?" if armed else "Apagar",
                            lambda n=n: g.slot_delete(n), True, (200, 70, 60) if armed else (150, 110, 90), self.f_xs)
        self.button(screen, (R.x + 24, R.bottom - 52, 140, 38), "Voltar", g.menu_exit, True, (150, 110, 70), self.f_s)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 14), "midbottom")

    # ------------------------------------------------------------ configurações
    def draw_settings(self, screen, g):
        R = self.window(screen, (SCREEN_W // 2 - 380, 70, 760, 580), "Configurações")
        for i, (key, lb) in enumerate((("jogo", "Jogo"), ("tela", "Tela"), ("teclas", "Teclas"))):
            self.button(screen, (R.x + 24 + i * 130, R.y + 64, 122, 32), lb, lambda k=key: setattr(g, "settings_tab", k) or setattr(g, "rebinding", None),
                        True, (150, 100, 50) if g.settings_tab == key else (186, 160, 118), self.f_s)
        x, y = R.x + 40, R.y + 124
        if g.settings_tab == "jogo":
            self.button(screen, (x, y, 360, 44), "Som: " + ("ligado" if g.audio.on else "desligado"), g.toggle_sound, True, (150, 110, 70), self.f_m)
            has = g.state is not None
            murchar = has and g.state.settings.get("murchar", True)
            self.button(screen, (x, y + 64, 360, 44), "Plantas morrem na troca de estação: " + ("SIM" if murchar else "NÃO"),
                        g.toggle_wither, has, (200, 130, 40) if murchar else (90, 150, 70), self.f_s)
            self.text(screen, "Desligado: plantas fora de época continuam vivas e crescendo depois da troca de estação.", self.f_xs, SUB, (x, y + 112))
            self.button(screen, (x, y + 140, 360, 44), "Grade na construção: " + ("sim" if has and g.state.settings["grade"] else "não"),
                        g.toggle_grid, has, (110, 130, 90), self.f_s)
            lago = has and g.state.settings.get("regador_lago", False)
            self.button(screen, (x, y + 200, 360, 44), "Encher regador no lago/rio: " + ("SIM" if lago else "NÃO"),
                        g.toggle_lake, has, (70, 130, 200) if lago else (150, 120, 90), self.f_s)
            self.text(screen, "Desligado: só a torneira (da carpintaria) enche o regador.", self.f_xs, SUB, (x, y + 248))
            if not has:
                self.text(screen, "Abra um jogo (Continuar ou Novo jogo) para mudar as opções acima que são de cada save.", self.f_xs, (160, 60, 40), (x, y + 284))
        elif g.settings_tab == "tela":
            self.text(screen, "Modo de tela", self.f_m, INK, (x, y - 4))
            for i, (mode, lb) in enumerate(SCREEN_MODES):
                self.button(screen, (x + i * 226, y + 30, 216, 44), lb, lambda m=mode: g.set_screen_mode(m), True,
                            (90, 150, 70) if g.prefs.screen == mode else (150, 120, 90), self.f_s, active=(g.prefs.screen == mode))
            self.text(screen, "F11 alterna entre janela e tela cheia a qualquer momento.", self.f_xs, SUB, (x, y + 84))
            self.text(screen, f"Zoom da câmera: {g.zoom:.2f}x", self.f_m, INK, (x, y + 124))
            self.button(screen, (x, y + 158, 60, 40), "-", lambda: g.zoom_by(-1), g.zoom > ZOOM_MIN, (150, 110, 70), self.f_m)
            self.button(screen, (x + 70, y + 158, 60, 40), "+", lambda: g.zoom_by(1), g.zoom < ZOOM_MAX, (150, 110, 70), self.f_m)
            self.text(screen, "Durante o jogo: segure Ctrl e gire a roda do mouse.", self.f_xs, SUB, (x + 150, y + 170))
        else:
            for i, (act, lb, _) in enumerate(ACTIONS):
                col, row = divmod(i, 8)
                bx, by = x + col * 340, y + row * 46
                self.text(screen, lb, self.f_xs, INK, (bx, by + 12))
                wait = g.rebinding == act
                self.button(screen, (bx + 190, by, 130, 34), "Pressione..." if wait else g.prefs.key_name(act),
                            lambda a=act: g.start_rebind(a), True, (200, 130, 40) if wait else (150, 110, 70), self.f_xs, active=wait)
            self.button(screen, (x, y + 7 * 46 + 10, 200, 38), "Restaurar padrão", g.reset_keys, True, (190, 70, 60), self.f_s)
            self.text(screen, "Clique numa tecla e aperte a nova. Se já estiver em uso, as duas trocam de lugar.", self.f_xs, SUB, (x + 220, y + 7 * 46 + 10))
            self.text(screen, "As setas sempre andam. Esc cancela. Números 1-9 e 0 são da barra rápida.", self.f_xs, SUB, (x + 220, y + 7 * 46 + 28))
        self.button(screen, (R.x + 24, R.bottom - 52, 140, 38), "Voltar", g.menu_exit, True, (150, 110, 70), self.f_s)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 14), "midbottom")

    # ------------------------------------------------------------ misturador de ração
    def draw_racao(self, screen, g):
        s = g.state
        R = self.window(screen, (80, 40, 864, 640), "Misturador de Ração")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        self.text(screen, "Cada animal tem a sua ração. Coloque nos cochos (tela dos animais): dá mais saúde, humor e amizade que o feno.",
                  self.f_xs, SUB, (R.x + 24, R.y + 58))
        for k, tipo in enumerate(data.ANIMALS):
            r_ = crafting.recipe(tipo)
            r = pygame.Rect(R.x + 24, R.y + 86 + k * 76, R.w - 48, 70)
            pygame.draw.rect(screen, PARCH2, r, border_radius=8)
            sprites.draw_icon(screen, data.ITEMS[r_["item"]], pygame.Rect(r.x + 6, r.y + 8, 54, 54))
            sprites.draw_face(screen, tipo, r.x + 82, r.y + 35, 16)
            self.text(screen, f"{data.ITEMS[r_['item']]['nome']}  (rende {r_['rende']})", self.f_s, INK, (r.x + 112, r.y + 6))
            self.text(screen, f"Você tem: {s.inv.count(r_['item'])}", self.f_xs, SUB, (r.x + 112, r.y + 46))
            for j, (ing, n) in enumerate(r_["ingredientes"].items()):
                have = s.inv.count(ing)
                self.text(screen, f"{data.ITEMS[ing]['nome']}: {n} (tem {have})", self.f_xs,
                          (30, 110, 40) if have >= n else (160, 60, 40), (r.x + 112 + j * 190, r.y + 28))
            self.button(screen, (r.right - 200, r.y + 18, 90, 34), "Fabricar", lambda t=tipo: g.craft_racao(t, 1),
                        crafting.can_craft(s, tipo, 1), (90, 150, 70), self.f_xs)
            self.button(screen, (r.right - 102, r.y + 18, 90, 34), "x5", lambda t=tipo: g.craft_racao(t, 5),
                        crafting.can_craft(s, tipo, 5), (80, 130, 200), self.f_xs)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 8), "midbottom")

    # ------------------------------------------------------------ elevador da mina
    def draw_mina_menu(self, screen, g):
        s = g.state
        R = self.window(screen, (SCREEN_W // 2 - 300, 140, 600, 420), "Mina")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        self.text(screen, f"Seu melhor andar: {s.mine_best}. Escolha onde começar:", self.f_s, SUB, (R.x + 30, R.y + 62))
        starts = mine.available_starts(s.mine_best)
        for i, f in enumerate(starts):
            x, y = R.x + 30 + (i % 4) * 140, R.y + 108 + (i // 4) * 64
            self.button(screen, (x, y, 128, 50), "Andar 1" if f == 1 else f"Andar {f}",
                        lambda f=f: (g.close_menu(), g.enter_mine(f)), True, (90, 150, 70) if f == 1 else (80, 130, 200), self.f_m)
        self.text(screen, "Dica: a picareta melhor quebra mais rápido e abre minérios mais raros.", self.f_xs, SUB, (R.x + 30, R.bottom - 40))

    # ------------------------------------------------------------ guia do jogo
    def _wrap(self, text, font, width):
        words, lines, cur = text.split(" "), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if cur and font.render(t, True, (0, 0, 0)).get_width() > width:
                lines.append(cur)
                cur = w
            else:
                cur = t
        if cur:
            lines.append(cur)
        return lines

    def _guia_text(self, g, raw):
        import re
        keys = g.prefs.keys
        return re.sub(r"\{(\w+)\}", lambda m: g.prefs.key_name(m.group(1)) if m.group(1) in keys else m.group(0), raw)

    def draw_guia(self, screen, g):
        R = self.window(screen, (SCREEN_W // 2 - 490, 50, 980, 630), "Guia do Jogo")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", lambda: setattr(g, "mode", "pause"), base=(190, 70, 60))
        topics = data.GUIA
        g.guia_topic = max(0, min(len(topics) - 1, g.guia_topic))
        for i, tp in enumerate(topics):
            self.button(screen, (R.x + 16, R.y + 54 + i * 30, 226, 27), tp["titulo"],
                        lambda i=i: (setattr(g, "guia_topic", i), setattr(g, "guia_scroll", 0)), True,
                        (160, 108, 50) if i == g.guia_topic else (186, 160, 118), self.f_xs)
        box = pygame.Rect(R.x + 256, R.y + 56, R.w - 256 - 20, R.h - 56 - 18)
        pygame.draw.rect(screen, PARCH2, box, border_radius=8)
        pygame.draw.rect(screen, (170, 130, 80), box, 2, border_radius=8)
        tp = topics[g.guia_topic]
        width = box.w - 56
        items = []                                        # (altura, função de desenho)
        items.append((40, lambda x, y: self.text(screen, tp["titulo"], self.f_b, INK, (x, y))))
        for ln in tp["linhas"]:
            txt = self._guia_text(g, ln)
            if txt.startswith("# "):
                items.append((34, lambda x, y, t=txt[2:]: (self.text(screen, t, self.f_m, (150, 82, 30), (x, y + 8)),
                                                          pygame.draw.line(screen, (190, 150, 100), (x, y + 32), (x + width, y + 32), 1))))
            elif txt.startswith("- "):
                for k, w in enumerate(self._wrap(txt[2:], self.f_s, width - 22)):
                    items.append((22, lambda x, y, w=w, k=k: (pygame.draw.circle(screen, (150, 82, 30), (x + 6, y + 10), 3) if k == 0 else None,
                                                             self.text(screen, w, self.f_s, INK, (x + 20, y)))))
            else:
                for w in self._wrap(txt, self.f_s, width):
                    items.append((22, lambda x, y, w=w: self.text(screen, w, self.f_s, INK, (x, y))))
        total = sum(h for h, _ in items) + 20
        view = box.h - 20
        g.guia_scroll = max(0, min(max(0, total - view), g.guia_scroll))
        y = box.y + 12 - g.guia_scroll
        for h, fn in items:
            if y >= box.y + 6 and y + h <= box.bottom - 6:
                fn(box.x + 20, y)
            y += h
        if total > view:                                   # barra de rolagem
            tr = pygame.Rect(box.right - 14, box.y + 8, 8, box.h - 16)
            pygame.draw.rect(screen, (190, 160, 120), tr, border_radius=4)
            th = max(30, int(tr.h * view / total))
            ty = tr.y + int((tr.h - th) * g.guia_scroll / max(1, total - view))
            pygame.draw.rect(screen, (150, 98, 46), (tr.x, ty, tr.w, th), border_radius=4)
            self.text(screen, "Role com o mouse (ou setas)", self.f_xs, SUB, (box.right - 24, box.bottom - 6), "bottomright")

    # ------------------------------------------------------------ ferraria
    def draw_ferreiro(self, screen, g):
        s = g.state
        R = self.window(screen, (SCREEN_W // 2 - 420, 40, 840, 640), "Ferraria do Aço")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        for i, (key, lb) in enumerate((("melhorar", "Melhorar ferramentas"), ("fundir", "Fundir minérios"), ("vender", "Vender"))):
            self.button(screen, (R.x + 24 + i * 200, R.y + 62, 192, 34), lb, lambda k=key: setattr(g, "smith_tab", k), True,
                        (150, 100, 50) if g.smith_tab == key else (186, 160, 118), self.f_xs)
        y0 = R.y + 112
        GOOD, BAD = (30, 110, 40), (160, 60, 40)
        if g.smith_tab == "melhorar":
            self.text(screen, "Pedra, Ferro e Ouro: ferramentas mais fortes e que gastam menos energia.",
                      self.f_xs, SUB, (R.x + 24, y0 - 6))
            for k, base in enumerate(smithing.BASES):
                r = pygame.Rect(R.x + 24, y0 + 24 + k * 96, R.w - 48, 88)
                pygame.draw.rect(screen, PARCH2, r, border_radius=8)
                f = smithing.find_tool(s, base)
                if f is None:
                    sprites.draw_icon(screen, data.ITEMS[base], pygame.Rect(r.x + 8, r.y + 12, 60, 60))
                    self.text(screen, f"Você não tem {data.ITEMS[base]['nome']}.", self.f_s, SUB, (r.x + 84, r.y + 16))
                    if base == "espada":
                        self.text(screen, "Necessária para enfrentar os inimigos da mina.", self.f_xs, SUB, (r.x + 84, r.y + 44))
                        self.button(screen, (r.right - 190, r.y + 24, 174, 40), f"Comprar ${data.ITEMS['espada']['compra']}",
                                    lambda: g.smith_do(smithing.buy_sword), s.money >= data.ITEMS["espada"]["compra"], (200, 130, 40), self.f_s)
                    continue
                it = data.ITEMS[s.inv.slots[f[0]]["i"]]
                sprites.draw_icon(screen, it, pygame.Rect(r.x + 8, r.y + 12, 60, 60))
                self.text(screen, it["nome"], self.f_m, INK, (r.x + 84, r.y + 4))
                self.text(screen, it.get("desc", "")[:90], self.f_xs, SUB, (r.x + 84, r.y + 30))
                c = smithing.cost(s, base)
                if c is None:
                    self.text(screen, "Nível máximo!", self.f_s, GOOD, (r.x + 84, r.y + 56))
                    continue
                nxt = data.ITEMS[data.tool_id(base, f[1] + 1)]
                mats = f"${c['dinheiro']}" + "".join(f"  +  {n} {data.ITEMS[m]['nome']}" for m, n in c["materiais"].items())
                falta = smithing.missing(s, base)
                self.text(screen, f"Próximo: {nxt['nome']}", self.f_xs, INK, (r.x + 84, r.y + 50))
                self.text(screen, "Custo: " + mats, self.f_xs, BAD if falta else GOOD, (r.x + 84, r.y + 66))
                self.button(screen, (r.right - 150, r.y + 24, 134, 40), "Melhorar", lambda b=base: g.smith_do(smithing.upgrade, b),
                            not falta, (90, 150, 70), self.f_s)
        elif g.smith_tab == "fundir":
            self.text(screen, "Minério + carvão viram barras (para melhorar ferramentas ou vender).",
                      self.f_xs, SUB, (R.x + 24, y0 - 6))
            for k, bar in enumerate(data.FERREIRO["fundicao"]):
                rc = data.FERREIRO["fundicao"][bar]
                r = pygame.Rect(R.x + 24, y0 + 24 + k * 92, R.w - 48, 82)
                pygame.draw.rect(screen, PARCH2, r, border_radius=8)
                sprites.draw_icon(screen, data.ITEMS[bar], pygame.Rect(r.x + 8, r.y + 12, 58, 58))
                self.text(screen, data.ITEMS[bar]["nome"], self.f_m, INK, (r.x + 78, r.y + 8))
                hv, hc = s.inv.count(rc["minerio"]), s.inv.count("carvao")
                self.text(screen, f"{rc['n']} {data.ITEMS[rc['minerio']]['nome']} (tem {hv})", self.f_xs,
                          GOOD if hv >= rc["n"] else BAD, (r.x + 78, r.y + 40))
                self.text(screen, f"{rc['carvao']} Carvão (tem {hc})", self.f_xs, GOOD if hc >= rc["carvao"] else BAD,
                          (r.x + 78, r.y + 58))
                self.button(screen, (r.right - 240, r.y + 22, 110, 38), "Fundir x1", lambda b=bar: g.smith_do(smithing.smelt, b, 1),
                            smithing.can_smelt(s, bar, 1), (90, 150, 70), self.f_xs)
                self.button(screen, (r.right - 122, r.y + 22, 106, 38), "x5", lambda b=bar: g.smith_do(smithing.smelt, b, 5),
                            smithing.can_smelt(s, bar, 5), (80, 130, 200), self.f_xs)
            y = y0 + 24 + 3 * 92 + 10
            sprites.draw_icon(screen, data.ITEMS["carvao"], pygame.Rect(R.x + 32, y, 50, 50))
            self.text(screen, f"Carvão: ${data.ITEMS['carvao']['compra']} cada  (você tem {s.inv.count('carvao')})",
                      self.f_s, INK, (R.x + 92, y + 14))
            self.button(screen, (R.right - 250, y + 6, 100, 38), "Comprar 1", lambda: g.smith_do(smithing.buy_coal, 1),
                        s.money >= data.ITEMS["carvao"]["compra"], (200, 130, 40), self.f_xs)
            self.button(screen, (R.right - 142, y + 6, 100, 38), "Comprar 10", lambda: g.smith_do(smithing.buy_coal, 10),
                        s.money >= data.ITEMS["carvao"]["compra"] * 10, (170, 100, 30), self.f_xs)
        else:
            sellable = [sl for sl in s.inv.slots if sl and shops.can_sell_here("ferreiro", sl["i"])]
            self.text(screen, "A Ferraria compra minérios, carvão, barras e gemas.", self.f_xs, SUB, (R.x + 24, y0 - 6))
            total = sum(shops.sell_price_slot(sl) * sl["n"] for sl in sellable)
            for k, sl in enumerate(sellable[:8]):
                r = pygame.Rect(R.x + 24, y0 + 24 + k * 50, R.w - 48, 44)
                pygame.draw.rect(screen, PARCH2, r, border_radius=6)
                sprites.draw_icon(screen, data.ITEMS[sl["i"]], pygame.Rect(r.x + 4, r.y + 2, 40, 40))
                self.text(screen, f"{data.ITEMS[sl['i']]['nome']} x{sl['n']}", self.f_s, INK, (r.x + 54, r.y + 12))
                self.text(screen, f"${shops.sell_price_slot(sl) * sl['n']}", self.f_s, GOOD, (r.right - 16, r.y + 12), "topright")
            if not sellable:
                self.text(screen, "Nada para vender. Vá minerar!", self.f_m, SUB, (R.x + 40, y0 + 50))
            self.button(screen, (R.x + 24, R.bottom - 74, 320, 48), f"Vender tudo (${total})", lambda: g.smith_do(smithing.sell_all),
                        total > 0, (90, 150, 70), self.f_s)

    # ------------------------------------------------------------ quadro de empregos
    def draw_quadro(self, screen, g):
        """Contratação (escolha das tarefas, preços, estimativa, taxa) e gerenciamento do funcionário."""
        s = g.state
        w = s.worker
        R = self.window(screen, (62, 40, 900, 650), "Quadro de Empregos" if w is None else "Seu Funcionário")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        X = R.x + 24
        est = worker.estimativa(s)
        if g.contrata_sel is None:
            g.contrata_sel = {t for t in worker.ORDEM if t != "fundir" and worker.disponivel(s, t)}
        if w is None:
            self.text(screen, data.FUNC["descricao"], self.f_xs, SUB, (X, R.y + 56))
            self.text(screen, "Marque só as tarefas que quer contratar. Sem salário fixo: você paga apenas por unidade realmente feita.",
                      self.f_xs, SUB, (X, R.y + 76))
        else:
            pygame.draw.rect(screen, PARCH2, (X, R.y + 52, R.w - 48, 62), border_radius=10)
            sprites.draw_person(screen, X + 40, R.y + 106, (0, 1), False, g.t, sprites.WORKER_COL)
            self.text(screen, f"{w['nome']}  -  trabalhando há {w['dias']} dia(s)", self.f_m, INK, (X + 84, R.y + 58))
            self.text(screen, f"Taxa de contratação paga: ${w['taxa']}   |   Gasto total em serviços: ${w['total_gasto']}   |   "
                              f"Gasto hoje: ${worker.custo_hoje(s)}", self.f_xs, SUB, (X + 84, R.y + 90))
        self.text(screen, "Tarefa (clique para ligar/desligar)", self.f_xs, INK, (X, R.y + 122))
        self.text(screen, "Preço", self.f_xs, INK, (X + 440, R.y + 122))
        self.text(screen, "Faria agora" if w is None else "Feito hoje", self.f_xs, INK, (X + 640, R.y + 122))
        for i, t in enumerate(worker.ORDEM):
            y = R.y + 142 + i * 36
            ok, why = worker.estrutura_ok(s, t)
            on = (t in g.contrata_sel) if w is None else worker.is_on(s, t)
            lb = ("[x] " if on and ok else "[  ] ") + worker.TAREFAS[t]
            if w is None:
                fn = (lambda t=t: g.contrata_sel.symmetric_difference_update({t}))
            else:
                fn = (lambda t=t: g.worker_do(worker.toggle, t))
            self.button(screen, (X, y, 420, 32), lb, fn, ok, (90, 150, 70) if on else (150, 120, 90), self.f_s)
            cfg = worker.cfg(t)
            self.text(screen, f"${cfg['preco']} / {cfg['unidade']}", self.f_xs, INK, (X + 440, y + 8))
            if not ok:
                self.text(screen, why, self.f_xs, (160, 60, 40), (X + 640, y + 8))
            elif w is None:
                un, custo = est[t]
                self.text(screen, f"{un} un = ${custo}" if un else "nada a fazer agora", self.f_xs, SUB, (X + 640, y + 8))
            else:
                r = _hoje_reg(w, s, t)
                self.text(screen, f"{r['un']} un = ${r['pago']}", self.f_xs, SUB, (X + 640, y + 8))
        yb = R.y + 142 + len(worker.ORDEM) * 36 + 6
        if w is None:
            marcadas = [t for t in worker.ORDEM if t in g.contrata_sel and worker.disponivel(s, t)]
            custo = sum(est[t][1] for t in marcadas)
            self.text(screen, f"Tarefas escolhidas: {len(marcadas)}   |   Custo estimado do que ele faria agora: ${custo} (só paga se fizer)",
                      self.f_s, INK, (X, yb))
            self.text(screen, f"Taxa única de contratação: ${worker.taxa()}   |   Seu dinheiro: ${s.money}",
                      self.f_s, (150, 40, 30) if s.money < worker.taxa() else INK, (X, yb + 28))
            self.text(screen, "Você pode mudar as tarefas e ver o gasto a qualquer momento depois. Não precisa de nível nem de experiência.",
                      self.f_xs, SUB, (X, yb + 58))
            if g.contrata_conf:
                self.text(screen, f"Confirmar contratação por ${worker.taxa()} (taxa única) com {len(marcadas)} tarefa(s)?", self.f_s, INK, (X, yb + 84))
                self.button(screen, (X, yb + 112, 220, 46), "Sim, contratar", g.contratar, bool(marcadas), (90, 150, 70), self.f_s)
                self.button(screen, (X + 240, yb + 112, 160, 46), "Cancelar", lambda: setattr(g, "contrata_conf", False), True, (190, 70, 60), self.f_s)
            else:
                self.button(screen, (X, yb + 90, 300, 54), "Contratar...", lambda: setattr(g, "contrata_conf", True),
                            bool(marcadas), (90, 150, 70), self.f_m)
        else:
            andam = worker.em_andamento(s)
            self.text(screen, "Em andamento: " + (" | ".join(andam) if andam else "nada esperando (forno livre ou sem forno)"), self.f_xs, SUB, (X, yb))
            h = [x for x in s.worker_hist][-3:]
            self.text(screen, "Últimos dias: " + ("   ".join(f"{x['data'].split(' (')[0]}: ${x['total']}" for x in h) if h else "ainda sem relatórios"),
                      self.f_xs, SUB, (X, yb + 22))
            self.text(screen, "Mudar uma tarefa não cancela o que ele já está fazendo e nunca cobra duas vezes. Ele nunca cobra por tempo parado.",
                      self.f_xs, SUB, (X, yb + 44))
            self.button(screen, (X, R.bottom - 62, 260, 46), "Ver relatórios (histórico)",
                        lambda: (setattr(g, "rel_idx", max(0, len(s.worker_hist) - 1)), setattr(g, "mode", "relatorio")), True, (80, 130, 200), self.f_s)
            self.button(screen, (R.right - 244, R.bottom - 62, 220, 46), "Dispensar", lambda: g.worker_do(worker.fire), True, (190, 70, 60), self.f_s)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 14), "midbottom")

    def draw_relatorio(self, screen, g):
        """Relatório diário do ajudante (o papel sobre a mesa) e histórico dos últimos dias."""
        s = g.state
        R = self.window(screen, (62, 40, 900, 650), "Relatório do Ajudante")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        hist = s.worker_hist
        if not hist:
            self.text(screen, "Ainda não há relatórios. Contrate um ajudante: toda manhã o relatório do dia anterior aparece na mesa.",
                      self.f_s, SUB, (R.x + 24, R.y + 80))
            return
        g.rel_idx = max(0, min(g.rel_idx, len(hist) - 1))
        for k, hh in enumerate(reversed(hist[-10:])):
            idx = len(hist) - 1 - k
            self.button(screen, (R.x + 20, R.y + 56 + k * 40, 210, 34), f"{hh['data'].split(' (')[0]}  ${hh['total']}",
                        lambda i=idx: setattr(g, "rel_idx", i), True, (214, 150, 60) if idx == g.rel_idx else (150, 120, 90), self.f_xs)
        h = hist[g.rel_idx]
        X, y = R.x + 250, R.y + 56
        self.text(screen, f"{h['data']}  -  {h.get('nome', 'Ajudante')}", self.f_m, INK, (X, y))
        y += 34
        self.text(screen, "Tarefas feitas e pagamento:", self.f_s, INK, (X, y))
        y += 26
        feitas = [(t, h["tarefas"][t]) for t in worker.ORDEM if t in h["tarefas"] and h["tarefas"][t]["un"]]
        for t, r in feitas:
            self.text(screen, f"- {worker.TAREFAS[t]}: {r['un']} {worker.cfg(t)['unidade']}(s) x ${worker.preco(t)} = ${r['pago']}", self.f_xs, SUB, (X + 8, y))
            y += 20
        if not feitas:
            self.text(screen, "- Nenhuma tarefa concluída.", self.f_xs, SUB, (X + 8, y))
            y += 20

        def linhas(titulo, dic):
            nonlocal y
            if dic:
                y += 6
                self.text(screen, titulo, self.f_s, INK, (X, y))
                y += 24
                txt = ", ".join(f"{data.ITEMS[i]['nome'] if i in data.ITEMS else i} x{n}" for i, n in dic.items())
                for ln in self._wrap(txt, self.f_xs, R.right - X - 24):
                    self.text(screen, ln, self.f_xs, SUB, (X + 8, y))
                    y += 18
        linhas("Materiais consumidos:", h.get("consumido", {}))
        linhas("Minérios fundidos:", h.get("fundidos", {}))
        linhas("Produção (colhido / barras / ração):", h.get("producao", {}))
        y += 8
        self.text(screen, f"Total pago neste dia: ${h['total']}", self.f_m, INK, (X, y))
        y += 34
        prob = h.get("problemas", [])
        self.text(screen, "Problemas / tarefas que falharam:" if prob else "Nenhum problema registrado.", self.f_s, (150, 60, 30) if prob else SUB, (X, y))
        y += 24
        for p_ in prob[:6]:
            self.text(screen, "- " + p_, self.f_xs, (150, 60, 30), (X + 8, y))
            y += 18

    def draw_forno(self, screen, g):
        s = g.state
        inst = g.box()
        if inst is None or inst["s"] != "forno":
            g.close_menu()
            return
        d = forno.dados(inst)
        R = self.window(screen, (62, 40, 900, 650), "Forno de Fundição")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        X = R.x + 24
        st = forno.NOMES[d["estado"]]
        quem = " (operado pelo ajudante)" if d["por"] == "funcionario" and d["estado"] != forno.DESLIGADO else ""
        self.text(screen, f"Estado: {st}{quem}", self.f_m, INK, (X, R.y + 56))
        if d["estado"] == forno.FUNCIONANDO:
            self.bar(screen, (X, R.y + 92, 500, 20), forno.progresso(inst), (230, 130, 40))
            self.text(screen, f"{data.ITEMS[d['receita']]['nome']} x{d['lotes']} - faltam {int(d['restante'])} min de jogo", self.f_xs, SUB, (X + 520, R.y + 94))
        elif d["saida"]:
            txt = ", ".join(f"{n}x {data.ITEMS[b]['nome']}" for b, n in d["saida"].items())
            self.text(screen, f"Prontas para retirar: {txt}", self.f_s, (30, 110, 40), (X, R.y + 92))
            self.button(screen, (X + 520, R.y + 84, 220, 40), "Retirar barras", lambda: g.forno_do("retirar"), True, (90, 150, 70), self.f_s)
        else:
            self.text(screen, "Forno livre. Escolha uma receita abaixo (usa o minério e o carvão do seu inventário).", self.f_xs, SUB, (X, R.y + 94))
        y = R.y + 140
        for bar, r in forno.receitas().items():
            rect = pygame.Rect(X, y, R.w - 48, 86)
            pygame.draw.rect(screen, PARCH2, rect, border_radius=8)
            sprites.draw_icon(screen, data.ITEMS[bar], pygame.Rect(rect.x + 8, rect.y + 16, 54, 54))
            self.text(screen, data.ITEMS[bar]["nome"], self.f_s, INK, (rect.x + 76, rect.y + 6))
            mi, ca = data.ITEMS[r["minerio"]]["nome"], data.ITEMS["carvao"]["nome"]
            tem_m, tem_c = s.inv.count(r["minerio"]), s.inv.count("carvao")
            self.text(screen, f"Por lote: {r['n']}x {mi} (tem {tem_m}) + {r['carvao']}x {ca} (tem {tem_c}) = 1 barra em {r['minutos']} min",
                      self.f_xs, (30, 110, 40) if tem_m >= r["n"] and tem_c >= r["carvao"] else (160, 60, 40), (rect.x + 76, rect.y + 34))
            mx = forno.max_possivel(s.inv, bar)
            livre = forno.livre(inst)
            self.text(screen, f"Dá para fazer até {mx} lote(s) agora (máx. {forno.max_lotes()} por vez)", self.f_xs, SUB, (rect.x + 76, rect.y + 58))
            self.button(screen, (rect.right - 250, rect.y + 24, 110, 38), "1 lote", lambda b=bar: g.forno_do("iniciar", b, 1),
                        livre and mx >= 1, (90, 150, 70), self.f_xs)
            self.button(screen, (rect.right - 130, rect.y + 24, 120, 38), f"Máximo ({mx})", lambda b=bar, n=mx: g.forno_do("iniciar", b, n),
                        livre and mx >= 1, (80, 130, 200), self.f_xs)
            y += 94
        self.text(screen, "O forno trabalha sozinho com o tempo do jogo (até de noite). Se você contratar a tarefa 'Operar o forno', o ajudante também usa o minério do quartinho.",
                  self.f_xs, SUB, (X, R.bottom - 40))
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 14), "midbottom")

    # ------------------------------------------------------------ barraca de vendas
    def draw_barraca(self, screen, g):
        s = g.state
        inst = g.box()
        if inst is None or inst["s"] != "barraca":
            g.close_menu()
            return
        R = self.window(screen, (20, 40, 984, 640), "Barraca de Vendas")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        self.text(screen, "Clique num item do inventário para pôr à venda; clique numa prateleira para retirar. "
                          "Os fregueses compram durante o dia e o dinheiro cai no caixa.", self.f_xs, SUB, (R.x + 24, R.y + 56))
        cell = 46
        gx, gy = R.x + 24, R.y + 110
        self.text(screen, "Seu inventário", self.f_m, INK, (gx, gy - 32))
        for i, sl in enumerate(s.inv.slots):
            r = pygame.Rect(gx + (i % 10) * cell, gy + (i // 10) * cell, cell - 2, cell - 2)
            ok = bool(sl) and stall.can_display(sl["i"])
            self.slot(screen, r, sl, dim=bool(sl) and not ok, gold=(i < HOTBAR))
            if ok:
                self.buttons.append((r, lambda i=i: g.stall_put(i)))
        bx = R.x + 24 + 10 * cell + 40
        self.text(screen, "Prateleiras", self.f_m, INK, (bx, gy - 32))
        box = stall.shelf(inst)
        for i in range(stall.N_SLOTS):
            r = pygame.Rect(bx + (i % 3) * 150, gy + (i // 3) * 108, 140, 98)
            pygame.draw.rect(screen, (120, 84, 50), r, border_radius=8)
            pygame.draw.rect(screen, (170, 124, 76), r.inflate(-8, -8), border_radius=6)
            sl = box.slots[i]
            if sl:
                self.slot(screen, pygame.Rect(r.x + 8, r.y + 8, 46, 46), sl)
                self.text(screen, f"${stall.price(sl)} cada", self.f_xs, (255, 255, 255), (r.x + 60, r.y + 14), shadow=True)
                self.text(screen, f"{sl['n']} un.", self.f_xs, (255, 240, 200), (r.x + 60, r.y + 36), shadow=True)
                self.buttons.append((r, lambda i=i: g.stall_take(i)))
            else:
                self.text(screen, "vazia", self.f_xs, (120, 84, 50), r.center, "center")
        cx_ = stall.caixa(inst)
        y = gy + 2 * 108 + 24
        pygame.draw.rect(screen, PARCH2, (bx, y, 440, 100), border_radius=10)
        self.text(screen, f"Caixa: ${cx_}", self.f_m, (30, 110, 40), (bx + 16, y + 12))
        self.text(screen, "Preço = valor de loja +30%. Chuva espanta fregueses.", self.f_xs, SUB, (bx + 16, y + 52))
        self.button(screen, (bx + 270, y + 12, 154, 40), "Recolher", g.stall_collect, cx_ > 0, (200, 130, 40), self.f_s)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 12), "midbottom")

    # ------------------------------------------------------------ cozinha
    def draw_cozinha(self, screen, g):
        s = g.state
        ids = cooking.recipes()
        R = self.window(screen, (40, 20, 944, 680), "Cozinha")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        self.text(screen, "Comidas recuperam energia (coma pelo inventário) e valem mais que os ingredientes soltos.",
                  self.f_xs, SUB, (R.x + 24, R.y + 56))
        rh = 92
        for k, rid in enumerate(ids):
            col, row = divmod(k, 4)
            r = pygame.Rect(R.x + 20 + col * 452, R.y + 84 + row * (rh + 8), 440, rh)
            pygame.draw.rect(screen, PARCH2, r, border_radius=8)
            it = data.ITEMS[rid]
            sprites.draw_icon(screen, it, pygame.Rect(r.x + 4, r.y + 14, 56, 56))
            self.text(screen, f"{it['nome']}  (+{it['energia']} energia, vale ${it['venda']})", self.f_xs, INK, (r.x + 66, r.y + 8))
            for j, (ing, n) in enumerate(data.RECEITAS[rid]["ingredientes"].items()):
                have = s.inv.count(ing)
                self.text(screen, f"{data.ITEMS[ing]['nome']} {have}/{n}", self.f_xs,
                          (30, 110, 40) if have >= n else (160, 60, 40), (r.x + 66 + j * 122, r.y + 32))
            self.button(screen, (r.right - 124, r.y + 56, 56, 28), "x1", lambda i=rid: g.cook(i, 1), cooking.can_cook(s, rid, 1),
                        (90, 150, 70), self.f_xs)
            self.button(screen, (r.right - 62, r.y + 56, 56, 28), "x5", lambda i=rid: g.cook(i, 5), cooking.can_cook(s, rid, 5),
                        (80, 130, 200), self.f_xs)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 14), "midbottom")

    # ------------------------------------------------------------ banco
    def draw_banco(self, screen, g):
        s = g.state
        R = self.window(screen, (SCREEN_W // 2 - 340, 90, 680, 520), "Banco da Vila")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        self.text(screen, f"Dona Clara: \"Seu dinheiro guardado rende 1% ao dia (até ${bank.MAX_INTEREST} por dia).\"",
                  self.f_xs, SUB, (R.x + 24, R.y + 58))
        pygame.draw.rect(screen, PARCH2, (R.x + 24, R.y + 90, R.w - 48, 110), border_radius=10)
        self.text(screen, f"Na carteira: ${s.money}", self.f_m, (30, 110, 40), (R.x + 44, R.y + 104))
        self.text(screen, f"No banco: ${s.bank}", self.f_m, (60, 90, 170), (R.x + 44, R.y + 140))
        self.text(screen, f"Rende amanhã: +${bank.interest(s)}", self.f_s, SUB, (R.x + 360, R.y + 144))
        y = R.y + 230
        self.text(screen, "Depositar", self.f_m, INK, (R.x + 24, y))
        for i, n in enumerate((100, 500, 1000)):
            self.button(screen, (R.x + 24 + i * 150, y + 36, 140, 40), f"${n}", lambda n=n: g.bank_do(bank.deposit, n),
                        s.money > 0, (90, 150, 70), self.f_s)
        self.button(screen, (R.x + 24 + 3 * 150, y + 36, 170, 40), "Tudo", lambda: g.bank_do(bank.deposit, s.money),
                    s.money > 0, (60, 120, 60), self.f_s)
        y += 110
        self.text(screen, "Sacar", self.f_m, INK, (R.x + 24, y))
        for i, n in enumerate((100, 500, 1000)):
            self.button(screen, (R.x + 24 + i * 150, y + 36, 140, 40), f"${n}", lambda n=n: g.bank_do(bank.withdraw, n),
                        s.bank > 0, (200, 130, 40), self.f_s)
        self.button(screen, (R.x + 24 + 3 * 150, y + 36, 170, 40), "Tudo", lambda: g.bank_do(bank.withdraw, s.bank),
                    s.bank > 0, (170, 100, 30), self.f_s)
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 14), "midbottom")

    # ------------------------------------------------------------ piscicultura
    def draw_tanque(self, screen, g):
        s = g.state
        inst = g.box()
        if inst is None or inst["s"] != "tanque":
            g.close_menu()
            return
        t = fishing.tank(inst)
        R = self.window(screen, (SCREEN_W // 2 - 400, 60, 800, 600), "Piscicultura")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        self.text(screen, f"Cada peixe come 1 ração por dia e engorda. Com peso {fishing.FAT_WEIGHT} fica gordo e vale muito mais.",
                  self.f_xs, SUB, (R.x + 24, R.y + 58))
        water = pygame.Rect(R.x + 24, R.y + 90, R.w - 48, 230)
        pygame.draw.rect(screen, (46, 32, 24), water.inflate(6, 6), border_radius=12)
        pygame.draw.rect(screen, (70, 144, 204), water, border_radius=10)
        pygame.draw.rect(screen, (100, 172, 226), (water.x, water.y, water.w, 24), border_radius=10)
        for i in range(fishing.TANK_CAP):
            fx = water.x + 60 + (i % 4) * 170 + math.sin(g.t * 1.3 + i) * 12
            fy = water.y + 70 + (i // 4) * 90 + math.cos(g.t + i * 1.7) * 6
            if i < len(t["peixes"]):
                p = t["peixes"][i]
                sprites.draw_fish(screen, int(fx), int(fy), 10 + p * 4, (250, 160 - p * 8, 70), flip=(i % 2 == 1))
                bar = pygame.Rect(int(fx) - 30, int(fy) + 30 + p * 2, 60, 6)
                pygame.draw.rect(screen, (30, 40, 70), bar, border_radius=3)
                pygame.draw.rect(screen, (240, 200, 60) if p < fishing.FAT_WEIGHT else (120, 230, 120),
                                 (bar.x, bar.y, int(bar.w * min(1, p / fishing.FAT_WEIGHT)), bar.h), border_radius=3)
            else:
                pygame.draw.circle(screen, (90, 160, 214), (int(fx), int(fy)), 10, 1)
        y = water.bottom + 20
        self.text(screen, f"Peixes: {len(t['peixes'])}/{fishing.TANK_CAP}    Gordos: {fishing.fat_count(inst)}    "
                          f"Ração no tanque: {t['racao']}/{fishing.TANK_FEED_MAX}", self.f_s, INK, (R.x + 24, y))
        y += 40
        self.text(screen, f"Alevinos no inventário: {s.inv.count('alevino')}", self.f_xs, SUB, (R.x + 24, y + 10))
        self.button(screen, (R.x + 250, y, 90, 36), "+1", lambda: g.tank_do(fishing.add_fry, 1), s.inv.count("alevino") > 0, (90, 150, 70), self.f_xs)
        self.button(screen, (R.x + 346, y, 90, 36), "+tudo", lambda: g.tank_do(fishing.add_fry, 99), s.inv.count("alevino") > 0, (60, 120, 60), self.f_xs)
        y += 46
        self.text(screen, f"Ração de peixe no inventário: {s.inv.count('racao_peixe')}", self.f_xs, SUB, (R.x + 24, y + 10))
        self.button(screen, (R.x + 250, y, 90, 36), "+10", lambda: g.tank_do(fishing.add_feed, 10), s.inv.count("racao_peixe") > 0, (200, 130, 40), self.f_xs)
        self.button(screen, (R.x + 346, y, 90, 36), "+tudo", lambda: g.tank_do(fishing.add_feed, 99), s.inv.count("racao_peixe") > 0, (170, 100, 30), self.f_xs)
        self.button(screen, (R.right - 280, y - 46, 250, 82), f"Colher peixes gordos ({fishing.fat_count(inst)})",
                    lambda: g.tank_do(fishing.harvest), fishing.fat_count(inst) > 0, (80, 130, 200), self.f_s)
        self.text(screen, "Alevinos e ração: Peixaria do Rio, na beira da estrada perto do lago.", self.f_xs, SUB, (R.x + 24, R.bottom - 40))
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 12), "midbottom")

    # ------------------------------------------------------------ quartinho de bagunça
    def draw_quartinho(self, screen, g):
        s = g.state
        inst = g.box()
        if inst is None:
            g.close_menu()
            return
        R = self.window(screen, (20, 24, 984, 672), "Quartinho de Bagunça")
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        box = storage.inv(inst)
        cap = storage.capacity(inst)
        self.text(screen, "Clique num item do inventário para guardar a pilha inteira; clique num item do quartinho para pegar de volta.",
                  self.f_xs, SUB, (R.x + 24, R.y + 56))
        cell = 46
        gx, gy = R.x + 24, R.y + 108
        self.text(screen, "Seu inventário", self.f_m, INK, (gx, gy - 32))
        for i, sl in enumerate(s.inv.slots):
            r = pygame.Rect(gx + (i % 10) * cell, gy + (i // 10) * cell, cell - 2, cell - 2)
            self.slot(screen, r, sl, gold=(i < HOTBAR))
            if sl:
                self.buttons.append((r, lambda i=i: g.box_deposit(i)))
        bx = R.x + 24 + 10 * cell + 40
        self.text(screen, f"Quartinho ({storage.used(inst)}/{cap})", self.f_m, INK, (bx, gy - 32))
        for i in range(cap):
            r = pygame.Rect(bx + (i % 10) * cell, gy + (i // 10) * cell, cell - 2, cell - 2)
            sl = box.slots[i]
            self.slot(screen, r, sl)
            if sl:
                self.buttons.append((r, lambda i=i: g.box_withdraw(i)))
        by = R.bottom - 90
        self.button(screen, (R.x + 24, by, 300, 40), "Guardar tudo (menos a barra rápida)", g.box_deposit_all,
                    True, (90, 150, 70), self.f_xs)
        cost = storage.upgrade_cost(inst)
        if cost is None:
            self.text(screen, "Tamanho máximo atingido!", self.f_s, (30, 110, 40), (bx, by + 8))
        else:
            self.button(screen, (bx, by, 320, 40), f"Ampliar +{storage.STEP_SLOTS} espaços  (${cost})", g.box_upgrade,
                        s.money >= cost, (200, 130, 40), self.f_xs)
        self.text(screen, f"Dinheiro: ${s.money}", self.f_s, (30, 110, 40), (R.right - 24, by + 8), "topright")
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (150, 60, 30), (R.centerx, R.bottom - 12), "midbottom")

    # ------------------------------------------------------------ menu de desenvolvedor
    def draw_dev(self, screen, g):
        s = g.state
        R = self.window(screen, (50, 30, 924, 660), "Menu de desenvolvedor")
        self.text(screen, "Só para testes. Nada aqui é salvo, exceto o que muda no jogo (dinheiro, itens, tempo...).", self.f_xs, SUB,
                  (R.x + 24, R.y + 56))
        self.button(screen, (R.right - 50, R.y + 12, 36, 32), "X", g.close_menu, base=(190, 70, 60))
        for i, (key, lb) in enumerate((("geral", "Geral"), ("tempo", "Tempo"), ("itens", "Itens"), ("mundo", "Mundo"))):
            self.button(screen, (R.x + 24 + i * 130, R.y + 78, 122, 32), lb, lambda k=key: setattr(g, "dev_tab", k), True,
                        (110, 90, 150) if g.dev_tab == key else (186, 160, 118), self.f_s)
        x, y = R.x + 24, R.y + 128
        B = lambda rect, lb, fn, en=True, col=(110, 90, 150), f=None: self.button(screen, rect, lb, fn, en, col, f or self.f_xs)
        if g.dev_tab == "geral":
            self.text(screen, f"Dinheiro: ${s.money}", self.f_m, (30, 110, 40), (x, y))
            for i, n in enumerate((100, 1000, 100000)):
                B((x + i * 140, y + 34, 130, 36), f"+${n}", lambda n=n: g.dev_do(dev.add_money, n))
            B((x + 420, y + 34, 130, 36), "Zerar dinheiro", lambda: g.dev_do(dev.add_money, -s.money), True, (190, 70, 60))
            B((x, y + 84, 270, 36), "Encher energia e regador", lambda: g.dev_do(dev.refill))
            B((x + 280, y + 84, 270, 36), "Energia infinita: " + ("SIM" if g.dev_god else "não"), lambda: g.dev_toggle("dev_god"), True,
              (90, 150, 70) if g.dev_god else (150, 120, 90))
            B((x, y + 130, 270, 36), "Atravessar paredes: " + ("SIM" if g.dev_noclip else "não"), lambda: g.dev_toggle("dev_noclip"), True,
              (90, 150, 70) if g.dev_noclip else (150, 120, 90))
            B((x + 280, y + 130, 270, 36), "Info de debug na tela: " + ("SIM" if g.dev_info else "não"), lambda: g.dev_toggle("dev_info"), True,
              (90, 150, 70) if g.dev_info else (150, 120, 90))
            self.text(screen, "Velocidade do tempo:", self.f_s, INK, (x, y + 188))
            for i, v in enumerate(dev.SPEEDS):
                B((x + 190 + i * 86, y + 180, 78, 36), f"x{v}", lambda v=v: g.dev_set_speed(v), True,
                  (90, 150, 70) if g.dev_speed == v else (150, 120, 90), self.f_s)
            self.text(screen, "Habilidades:", self.f_s, INK, (x, y + 244))
            B((x + 190, y + 236, 150, 36), "+1 nível em todas", lambda: g.dev_do(dev.add_levels, 1))
            B((x + 350, y + 236, 150, 36), "Tudo no máximo", lambda: g.dev_do(dev.max_skills))
        elif g.dev_tab == "tempo":
            self.text(screen, f"Agora: {s.clock.hhmm()}  -  {SEASON_LABEL[s.clock.season]} {s.clock.day_of_season}, Ano {s.clock.year}  -  {WEATHER_LABEL[s.weather]}",
                      self.f_m, INK, (x, y))
            self.text(screen, "Hora do dia (dormir só a partir das 19h):", self.f_s, INK, (x, y + 44))
            for i, h in enumerate((6, 9, 12, 15, 18, 19, 21, 23)):
                B((x + i * 100, y + 74, 92, 34), f"{h:02d}:00", lambda h=h: g.dev_do(dev.set_hour, h))
            B((x, y + 126, 260, 38), "Pular para o próximo dia", g.dev_next_day, True, (200, 130, 40), self.f_s)
            self.text(screen, "Ir para a estação (dia 1):", self.f_s, INK, (x, y + 184))
            for i, (k, lb) in enumerate(SEASON_LABEL.items()):
                B((x + i * 150, y + 214, 140, 36), lb, lambda k=k: g.dev_do(dev.set_season, k))
            self.text(screen, "Clima de hoje:", self.f_s, INK, (x, y + 272))
            for i, (k, lb) in enumerate(WEATHER_LABEL.items()):
                B((x + i * 150, y + 302, 140, 36), lb, lambda k=k: g.dev_do(dev.set_weather, k))
            self.text(screen, "Mudar a estação com plantas no chão pode fazê-las murchar na virada do dia.", self.f_xs, SUB, (x, y + 354))
        elif g.dev_tab == "itens":
            ids = [i for i, it in data.ITEMS.items() if CATEGORIAS[g.dev_filter] is None or it["kind"] in CATEGORIAS[g.dev_filter]]
            for i, name in enumerate(CATEGORIAS):
                B((x + i * 100, y - 6, 94, 28), name, lambda n=name: (setattr(g, "dev_filter", n), setattr(g, "dev_page", 0)), True,
                  (110, 90, 150) if g.dev_filter == name else (186, 160, 118))
            per, cols = 30, 6
            pages = max(1, (len(ids) + per - 1) // per)
            g.dev_page = max(0, min(g.dev_page, pages - 1))
            for k, iid in enumerate(ids[g.dev_page * per:(g.dev_page + 1) * per]):
                r = pygame.Rect(x + (k % cols) * 84, y + 32 + (k // cols) * 62, 78, 56)
                self.slot(screen, r, {"i": iid, "n": 1, "q": 0}, selected=(g.dev_item == iid))
                self.buttons.append((r, lambda iid=iid: setattr(g, "dev_item", iid)))
            B((x + 520, y + 32, 80, 30), "< pág.", lambda: setattr(g, "dev_page", g.dev_page - 1), g.dev_page > 0)
            B((x + 606, y + 32, 80, 30), "pág. >", lambda: setattr(g, "dev_page", g.dev_page + 1), g.dev_page < pages - 1)
            self.text(screen, f"{g.dev_page + 1}/{pages}", self.f_xs, SUB, (x + 700, y + 40))
            it = data.ITEMS[g.dev_item]
            sprites.draw_icon(screen, it, pygame.Rect(x + 520, y + 80, 64, 64))
            self.text(screen, it["nome"], self.f_m, INK, (x + 596, y + 84))
            self.text(screen, f"id: {g.dev_item}   tipo: {it['kind']}", self.f_xs, SUB, (x + 596, y + 112))
            self.text(screen, "Quantidade:", self.f_s, INK, (x + 520, y + 168))
            for i, n in enumerate((1, 10, 50, 99)):
                B((x + 520 + i * 70, y + 196, 64, 32), str(n), lambda n=n: setattr(g, "dev_qty", n), True,
                  (90, 150, 70) if g.dev_qty == n else (150, 120, 90))
            B((x + 520, y + 240, 220, 40), f"Dar {g.dev_qty}x", lambda: g.dev_do(dev.give_item, g.dev_item, g.dev_qty), True, (90, 150, 70), self.f_m)
            B((x + 520, y + 290, 220, 34), f"Dar {g.dev_qty}x (ouro)", lambda: g.dev_do(dev.give_item, g.dev_item, g.dev_qty, 2), True,
              (200, 150, 40), self.f_s)
        else:
            B((x, y, 270, 36), "Plantas: todas prontas", lambda: g.dev_do(dev.grow_crops))
            B((x + 280, y, 270, 36), "Regar toda a terra arada", lambda: g.dev_do(dev.water_all))
            B((x, y + 46, 270, 36), "Animais: amizade e bem-estar máx.", lambda: g.dev_do(dev.animals_boost))
            B((x + 280, y + 46, 270, 36), "Encher todos os cochos", lambda: g.dev_do(dev.fill_troughs))
            B((x, y + 92, 270, 36), "Forçar nascimento de filhotes", lambda: g.dev_do(dev.force_births))
            B((x + 280, y + 92, 270, 36), "Liberar todos os terrenos", lambda: g.dev_do(dev.unlock_lands))
            self.text(screen, "Criar animal de graça (precisa de construção com vaga):", self.f_s, INK, (x, y + 146))
            for i, tipo in enumerate(data.ANIMALS):
                sprites.draw_face(screen, tipo, x + 18 + i * 124, y + 192, 12)
                B((x + 36 + i * 124, y + 176, 82, 32), data.ANIMALS[tipo]["nome"], lambda t=tipo: g.dev_do(dev.spawn_animal, t))
            self.text(screen, "Teleporte:", self.f_s, INK, (x, y + 232))
            for i, (nome, px, py) in enumerate(dev.teleport_points(s)):
                B((x + (i % 3) * 290, y + 262 + (i // 3) * 42, 280, 34), nome, lambda px=px, py=py: g.dev_teleport(px, py))
        if g.msg_t > 0 and g.msg:
            self.text(screen, g.msg, self.f_s, (60, 60, 140), (R.centerx, R.bottom - 12), "midbottom")

    def draw_dev_overlay(self, screen, g):
        s = g.state
        lines = []
        if g.dev_info:
            lines += [f"FPS {g.clock.get_fps():.0f}   modo: {g.mode}   zoom {g.zoom:.2f}",
                      f"pos ({s.px:.2f}, {s.py:.2f})  bloco ({int(s.px)}, {int(s.py)})",
                      f"dia {s.clock.day}  min {s.clock.minutes:.0f}  escuro {s.clock.darkness():.2f}",
                      f"animais {len(s.animals)}  plantas {sum(1 for x in s.farm.soil.values() if x['crop'])}  construções {len(s.structs.by_id)}"]
        flags = [n for n, on in (("tempo x%d" % g.dev_speed, g.dev_speed != 1), ("energia infinita", g.dev_god), ("noclip", g.dev_noclip)) if on]
        if flags:
            lines.append("DEV: " + ", ".join(flags))
        for i, ln in enumerate(lines):
            self.text(screen, ln, self.f_xs, (190, 255, 190), (12, 62 + i * 16), shadow=True)

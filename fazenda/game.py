"""Loop principal: câmera, entrada, movimentação, modos (jogo, construção, menus) e renderização do mundo."""
import math
import os
import random
import sys

import pygame

from .touch import Touch
from . import actions, assets, bank, building, cooking, forno, routine, mine, orchard, smithing, stall, worker, fishing, crafting, data, dev, gfx, house, interior, shops, sprites, storage
from . import animals as an
from . import config
from .audio import Audio
from .config import (FPS, MAX_ENERGY, WATER_CAPACITY, PLAYER_SPEED, REACH, SAVE_SLOTS, SCREEN_H as SH, SCREEN_W as SW, TILE as T, ZOOM_STEP)
from .farming import crop_stage
from .prefs import Prefs
from .save import any_save, delete_slot, load_game, save_game, slot_info, slot_path
from .state import GameState
from .ui import UI

# As construções são desenhadas com a chave de ordem = base - BASE_BIAS. O jogador pode ficar até ~0,2 bloco
# "dentro" da linha da base (por causa da caixa de colisão dos pés); sem esse ajuste ele aparecia atrás da construção.
BASE_BIAS = 8

CUSTOMERS = [{"camisa": (90, 160, 120), "calca": (80, 70, 60), "cabelo": (60, 40, 30), "chapeu": (200, 160, 90)},
             {"camisa": (180, 100, 160), "calca": (60, 60, 100), "cabelo": (200, 150, 70)},
             {"camisa": (220, 170, 80), "calca": (70, 90, 70), "cabelo": (40, 40, 44), "chapeu": (150, 60, 60)},
             {"camisa": (100, 140, 200), "calca": (90, 70, 60), "cabelo": (150, 70, 40)}]
WORKER_COL = sprites.WORKER_COL
PLAYER_COL = {"camisa": (205, 70, 60), "calca": (50, 70, 140), "cabelo": (110, 70, 40), "chapeu": (232, 200, 92), "sheet": True}
TOOL_COL = {"enxada": (170, 170, 180), "regador": (90, 160, 230), "foice": (210, 210, 220),
            "machado": (190, 190, 200), "picareta": (170, 170, 180)}


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Fazenda RPG")
        try:                                                         # ícone da janela (assets/icon.png)
            pygame.display.set_icon(pygame.image.load(os.path.join(config.BASE_DIR, "assets", "icon.png")))
        except Exception:
            pass
        self.prefs = Prefs.load()
        self.screen = self._make_screen()
        self.zoom, self.vw, self.vh, self.view = 1.0, SW, SH, self.screen
        self.set_zoom(self.prefs.zoom, save=False)
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.touch = Touch(self.prefs.key)
        self.touch.fonte = self.ui.f_s
        self.audio = Audio()
        self.state = None
        self.mode = "title"
        self.t = 0.0
        self.cam = [0.0, 0.0]
        self.terrain, self.terrain_season = None, None
        self.parts, self.wps, self.wkind, self.flash = [], [], None, 0.0
        self.msg, self.msg_t, self.msg_col, self.prompt = "", 0.0, (255, 255, 255), ""
        self.fade, self.cd, self.tool_anim, self.tool_col = 0.0, 0.0, 0.0, (200, 200, 200)
        self.tool_icon = None
        self.guia_topic, self.guia_scroll = 0, 0
        self.contrata_sel, self.contrata_conf, self.rel_idx = None, False, 0
        self.wk = None                       # funcionário em ação durante o dia (posição, trabalho atual)
        self.moving, self.show_help = False, False
        self.night = pygame.Surface((SW, SH), pygame.SRCALPHA)
        self.black = pygame.Surface((SW, SH))
        self.black.fill((0, 0, 0))
        self.hist = building.History()
        self.inv_filter, self.inv_sel = "Tudo", None
        self.shop_id, self.shop_tab, self.shop_sel, self.shop_qty, self.shop_scroll = None, 0, 0, 1, 0
        self.animals_home, self.map_sel = None, None
        self.in_house, self.hx, self.hy = False, interior.SPAWN[0], interior.SPAWN[1]
        self.in_mine, self.mx, self.my, self.mfloor, self.mfl = False, 0.0, 0.0, 1, None
        self.mcache, self.mcache_day, self.mparts = {}, -1, []
        self.msurf, self.mine_bg, self.mine_bg_key = None, None, None
        self.mhp, self.mhit, self.mswing, self.mregen = 100, 0.0, 0.0, 0.0
        self.box_id = None
        self.trailer = 0
        self.smith_tab = "melhorar"
        self.room = None
        self.build_scroll = 0
        self.build = self._new_build()
        self.apos = {}
        self.title_bg = self._make_title_bg()
        # menus (slots / configurações) e entrada pelo mouse
        self.slot = 1
        self.slot_purpose, self.armed = "carregar", None
        self.menu_back = "title"
        self.settings_tab, self.rebinding = "jogo", None
        self.mouse_aim, self.mouse_hold = False, False
        self.feed_qty, self.sell_armed = 5, None
        self.dev_tab, self.dev_item, self.dev_qty, self.dev_page, self.dev_filter = "geral", "madeira", 10, 0, "Tudo"
        self.dev_speed, self.dev_god, self.dev_noclip, self.dev_info = 1, False, False, False

    # ------------------------------------------------------------ utilidades
    def say(self, msg, col=(255, 255, 255)):
        if msg:
            self.msg, self.msg_t, self.msg_col = msg, 2.6, col

    def err(self, msg):
        self.say(msg, (255, 170, 140))
        self.audio.play("error")

    def _make_title_bg(self):
        s = pygame.Surface((SW, SH))
        for y in range(SH):
            k = y / SH
            pygame.draw.line(s, (int(96 + 100 * k), int(170 + 62 * k), int(232 + 16 * k)), (0, y), (SW, y))
        pygame.draw.ellipse(s, (96, 170, 84), (-200, 500, 900, 400))
        pygame.draw.ellipse(s, (110, 184, 92), (300, 540, 1000, 360))
        sprites.draw_barn(s, 600, 400, 192, 160, "primavera")
        sprites.draw_house(s, 220, 420, 160, 128, "primavera")
        return s

    # ------------------------------------------------------------ tela e zoom
    def _make_screen(self):
        # SCALED em todos os modos: a janela e a tela cheia usam sempre a mesma lógica 1024x720, ampliada para o monitor.
        if sys.platform == "emscripten":                 # navegador: a página escala o canvas
            return pygame.display.set_mode((SW, SH))
        mode = self.prefs.screen
        flags = {"janela": pygame.SCALED, "redimensionavel": pygame.RESIZABLE | pygame.SCALED,
                 "cheia": pygame.FULLSCREEN | pygame.SCALED}.get(mode, pygame.SCALED)
        try:
            return pygame.display.set_mode((SW, SH), flags)
        except Exception:
            try:                                           # alguns sistemas só aceitam alternar pela função própria
                pygame.display.toggle_fullscreen()
                return pygame.display.get_surface() or pygame.display.set_mode((SW, SH))
            except Exception:
                self.prefs.screen = "janela"
                return pygame.display.set_mode((SW, SH))

    def set_screen_mode(self, mode):
        self.prefs.set_screen(mode)
        self.screen = self._make_screen()
        self.set_zoom(self.zoom, save=False)

    def _keys(self):
        """Teclas apertadas: as do teclado mais as dos botões de toque da tela."""
        class _K:
            def __init__(s_, real, extra):
                s_.real, s_.extra = real, extra

            def __getitem__(s_, k):
                return bool(s_.real[k]) or k in s_.extra
        return _K(pygame.key.get_pressed(), self.touch.teclas_seguradas())

    def toggle_fullscreen(self):
        self.set_screen_mode("janela" if self.prefs.screen == "cheia" else "cheia")

    def set_zoom(self, z, save=True):
        self.zoom = max(1.0, min(2.0, round(z * 4) / 4))
        self.vw, self.vh = int(SW / self.zoom), int(SH / self.zoom)
        self.view = self.screen if self.zoom == 1.0 else pygame.Surface((self.vw, self.vh))
        if save:
            self.prefs.set_zoom(self.zoom)

    def zoom_by(self, d):
        self.set_zoom(self.zoom + d * ZOOM_STEP)

    # ------------------------------------------------------------ slots de salvamento
    def has_save(self):
        return any_save()

    def open_slots(self, purpose):
        self.slot_purpose, self.armed = purpose, None
        self.menu_back = "pause" if (self.state is not None and self.mode == "pause") else "title"
        self.mode = "slots"

    def open_settings(self):
        self.menu_back = "pause" if (self.state is not None and self.mode == "pause") else "title"
        self.settings_tab, self.rebinding = "jogo", None
        self.mode = "settings"

    def menu_exit(self):
        self.rebinding, self.armed = None, None
        self.mode = self.menu_back

    def slot_click(self, n):
        info = slot_info(n)
        if self.slot_purpose == "carregar":
            if info and not info.get("erro"):
                self.load(n)
            else:
                self.err("Este slot não tem um jogo válido.")
            return
        salvando_no_atual = self.slot_purpose == "salvar" and n == self.slot and self.state is not None
        if info and not salvando_no_atual and self.armed != ("sobrescrever", n):
            self.armed = ("sobrescrever", n)
            self.say("Este slot já tem um jogo. Clique de novo para sobrescrever.", (255, 220, 160))
            return
        self.armed = None
        if self.slot_purpose == "novo":
            self.new_game(n)
        else:
            self.slot = n
            self.save()

    def slot_delete(self, n):
        if self.armed != ("apagar", n):
            self.armed = ("apagar", n)
            self.say("Clique em \"Certeza?\" para apagar este slot para sempre.", (255, 220, 160))
            return
        self.armed = None
        if delete_slot(n):
            self.say(f"Slot {n} apagado.", (200, 230, 255))
        else:
            self.err("Não foi possível apagar.")

    def new_game(self, slot=None):
        if slot:
            self.slot = slot
        self.state = GameState.new(random.randint(1, 999999))
        self.in_house = False
        self._start()
        self.show_help = True

    def load(self, slot=None):
        slot = slot or self.slot
        try:
            self.state = load_game(slot_path(slot))
            self.in_house = False
        except Exception as e:
            self.err(f"Não foi possível carregar: {e}")
            return
        self.slot = slot
        self._start()
        self.say("Jogo carregado!", (150, 255, 150))

    def _start(self):
        self.mode = "play"
        self.in_mine = False
        self.mcache, self.mcache_day = {}, -1
        self.hist.clear()
        self.apos = {}
        self.parts = []
        self.build = self._new_build()
        self.audio.on = self.state.settings.get("som", True)
        self.terrain_season = None
        self._refresh_terrain()
        w = self.state.world
        self.cam = [max(0, min(w.w * T - self.vw, self.state.px * T - self.vw / 2)),
                    max(0, min(w.h * T - self.vh, self.state.py * T - self.vh / 2))]
        self.mouse_aim = self.mouse_hold = False
        self.show_help = False

    def save(self, silent=False):
        if self.state is None:
            return
        try:
            self.state.settings["som"] = self.audio.on
            save_game(self.state, slot_path(self.slot))
            if not silent:
                self.say(f"Jogo salvo no slot {self.slot}!", (150, 255, 150))
        except Exception as e:
            self.err(f"Erro ao salvar: {e}")

    def to_title(self):
        self.save(silent=True)
        self.menu_back = "title"
        self.mode = "title"

    def quit(self):
        if self.state is not None and self.mode != "title":
            self.save(silent=True)
        pygame.quit()
        sys.exit()

    def toggle_sound(self):
        self.audio.toggle()

    def toggle_wither(self):
        if self.state is None:
            return
        st = self.state.settings
        st["murchar"] = not st.get("murchar", True)
        self.say("As plantas vão murchar ao trocar de estação." if st["murchar"]
                 else "As plantas fora de época sobrevivem à troca de estação.", (255, 240, 170))

    def toggle_lake(self):
        if self.state is None:
            return
        st = self.state.settings
        st["regador_lago"] = not st.get("regador_lago", False)
        self.say("Agora o regador também enche no lago e no rio." if st["regador_lago"]
                 else "O regador só enche na torneira.", (255, 240, 170))

    def start_rebind(self, action):
        self.rebinding = action

    def _capture_key(self, e):
        """Se estamos esperando uma tecla nova para uma ação, consome o evento. Retorna True se consumiu."""
        if self.rebinding is None:
            return False
        act, self.rebinding = self.rebinding, None
        if e.key == pygame.K_ESCAPE:
            self.say("Troca de tecla cancelada.")
            return True
        ok, msg = self.prefs.rebind(act, e.key)
        if ok:
            self.say(msg, (150, 255, 150))
        else:
            self.err(msg)
        return True

    # ------------------------------------------------------------ menu de desenvolvedor
    def dev_do(self, fn, *args):
        """Roda uma função do módulo dev sobre o estado do jogo e mostra a mensagem que ela devolve."""
        msg = fn(self.state, *args)
        self.say(str(msg), (190, 230, 255))
        self._refresh_terrain()
        self.audio.play("click")

    def dev_next_day(self):
        summary = self.state.end_day(forced=False)
        self.after_new_day(summary, slept=True)
        self.mode = "dev"

    def dev_toggle(self, name):
        setattr(self, name, not getattr(self, name))

    def dev_set_speed(self, v):
        self.dev_speed = v
        self.say(f"Tempo x{v}", (190, 230, 255))

    def dev_teleport(self, x, y):
        self.say(dev.teleport(self.state, x, y), (190, 230, 255))
        w = self.state.world
        self.cam = [max(0, min(w.w * T - self.vw, self.state.px * T - self.vw / 2)),
                    max(0, min(w.h * T - self.vh, self.state.py * T - self.vh / 2))]

    def reset_keys(self):
        self.prefs.reset_keys()
        self.rebinding = None
        self.say("Teclas restauradas para o padrão.", (150, 255, 150))

    def _refresh_terrain(self):
        season = self.state.clock.season
        if season != self.terrain_season:
            self.terrain = gfx.render_terrain(self.state.world, season)
            self.terrain_season = season

    def close_menu(self):
        self.mode = "casa" if self.in_house else "mina" if self.in_mine else "play"
        self.inv_sel = None

    def _new_build(self):
        return {"modo": "colocar", "sid": None, "rot": 0, "ok": False, "info": "", "picked": None, "pos": (0, 0)}

    # ------------------------------------------------------------ callbacks da interface
    def inv_click(self, i):
        if self.inv_sel is None or self.inv_sel == i:
            self.inv_sel = None if self.inv_sel == i else i
            return
        self.state.inv.swap(self.inv_sel, i)
        self.inv_sel = i
        self.audio.play("click")

    def eat(self, idx):
        if self.state.eat(idx):
            self.audio.play("eat")
        else:
            self.err("Você não pode comer isso agora.")

    def shop_set_tab(self, i):
        self.shop_tab, self.shop_sel, self.shop_qty, self.shop_scroll = i, 0, 1, 0
        self.sell_armed = None

    def shop_select(self, i):
        self.shop_sel, self.shop_qty = i, 1
        self.sell_armed = None

    def shop_add_qty(self, d):
        self.shop_qty = max(1, min(99, self.shop_qty + d))

    def _shop_result(self, ok, msg, sfx):
        if ok:
            self.say(msg, (255, 240, 170))
            self.audio.play(sfx)
        else:
            self.err(msg)

    def buy_item(self, item_id):
        ok, msg = shops.buy(self.state, self.shop_id, item_id, self.shop_qty)
        self._shop_result(ok, msg, "buy")
        if ok:
            self.shop_qty = 1

    def sell_slot(self, idx, q):
        ok, msg = shops.sell(self.state, self.shop_id, idx, q)
        self._shop_result(ok, msg, "coin")
        self.shop_qty = 1

    def sell_all(self):
        total = shops.sell_all_sellable(self.state, self.shop_id)
        self._shop_result(total > 0, f"Vendeu tudo por ${total}!" if total else "Nada para vender.", "coin")

    def buy_animal(self, tipo):
        ok, msg = shops.buy_animal(self.state, tipo)
        self._shop_result(ok, msg, "moo" if tipo in ("vaca", "porco") else "cluck")

    def _home(self):
        return self.state.structs.by_id.get(self.animals_home)

    def feed_add_qty(self, d):
        self.feed_qty = max(1, min(99, self.feed_qty + d))

    def feed_building(self, kind="feno"):
        """Coloca no cocho a quantidade escolhida (feed_qty) de feno ou de ração de um animal."""
        inst = self._home()
        n = an.add_feed(self.state, inst, self.feed_qty, kind) if inst else 0
        nome = data.ITEMS[kind]["nome"].lower()
        self._shop_result(n > 0, f"Colocou {n} de {nome} no cocho." if n else f"Sem {nome} no inventário ou cocho cheio.", "eat")

    def sell_animal(self, aid):
        """Vende um animal. O primeiro clique só pede confirmação."""
        a = next((x for x in self.state.animals if x["id"] == aid), None)
        if a is None:
            return
        if self.sell_armed != aid:
            self.sell_armed = aid
            self.say(f"Clique de novo para vender {a['nome']} por ${an.sell_value(a)}.", (255, 220, 160))
            return
        self.sell_armed = None
        ok, msg = shops.sell_animal(self.state, aid)
        self.apos.pop(aid, None)
        self._shop_result(ok, msg, "coin")
        self.shop_sel = 0

    def craft_racao(self, tipo, lotes=1):
        ok, msg = crafting.craft(self.state, tipo, lotes)
        self._shop_result(ok, msg, "buy")

    def collect_products(self):
        got, xp = an.collect(self.state, self.animals_home)
        if got:
            up = self.state.add_xp("pecuaria", xp)
            self.say(f"Coletou {got} produto(s)!" + (" (Pecuária subiu de nível!)" if up else ""), (255, 240, 170))
            self.audio.play("harvest")
        else:
            self.err("Nada para coletar (ou inventário cheio).")

    def pet_animals(self):
        n = an.pet_all(self.state.animals, self.animals_home)
        self._shop_result(n > 0, f"Você acariciou {n} animal(is)." if n else "Todos já foram acariciados hoje.", "cluck")

    def buy_land(self, land_id):
        ok, msg = self.state.buy_land(land_id)
        self._shop_result(ok, msg, "buy")
        if ok:
            self.save(silent=True)

    # ------------------------------------------------------------ construção
    def placeables(self):
        out, seen = [], set()
        for s in self.state.inv.slots:
            if s and data.ITEMS[s["i"]]["kind"] == "placeable" and s["i"] not in seen:
                seen.add(s["i"])
                out.append((s["i"], self.state.inv.count(s["i"])))
        return out

    def enter_build(self, sid=None):
        self.mode = "build"
        self.build = self._new_build()
        if sid:
            self.build["sid"] = sid
        else:
            items = self.placeables()
            self.build["sid"] = items[0][0] if items else None
        self.say("Modo construção: escolha um item e clique no mapa.", (200, 230, 255))

    def exit_build(self):
        self.mode = "play"
        self.build = self._new_build()

    def build_set_mode(self, m):
        self.build.update(modo=m, picked=None)
        if m != "colocar":
            self.build["rot"] = 0

    def build_select(self, sid):
        self.build.update(sid=sid, modo="colocar", picked=None, rot=0)

    def build_rotate(self):
        b = self.build
        sid = b["sid"] if b["modo"] == "colocar" else (self.state.structs.by_id[b["picked"]]["s"] if b["picked"] else None)
        if sid and data.STRUCTS[sid].get("rotacionavel"):
            b["rot"] = (b["rot"] + 1) % 2
            self.audio.play("click")
        elif sid:
            self.say("Esta construção não gira.")

    def toggle_grid(self):
        self.state.settings["grade"] = not self.state.settings["grade"]

    def build_undo(self):
        ok, msg = self.hist.undo(self.state)
        self.say("Desfeito." if ok else msg, (200, 230, 255) if ok else (255, 170, 140))

    def build_redo(self):
        ok, msg = self.hist.redo(self.state)
        self.say("Refeito." if ok else msg, (200, 230, 255) if ok else (255, 170, 140))

    def _mouse_tile(self):
        mx, my = pygame.mouse.get_pos()
        return int((mx / self.zoom + self.cam[0]) // T), int((my / self.zoom + self.cam[1]) // T)

    def _over_hotbar(self, pos):
        return any(r.collidepoint(pos) for r in self.ui.hotbar_rects)

    def _reach_ok(self, tx, ty):
        s = self.state
        return math.hypot(tx + .5 - s.px, ty + .5 - s.py) <= REACH

    def _aim_tile(self):
        """Bloco destacado no modo jogo: o do mouse (se ele foi o último a ser usado) ou o da frente do jogador.
        Retorna (x, y, alcançável)."""
        s = self.state
        if self.mouse_aim and not self._over_hotbar(pygame.mouse.get_pos()):
            tx, ty = self._mouse_tile()
            return tx, ty, self._reach_ok(tx, ty)
        tx, ty = s.target_tile()
        return tx, ty, True

    def _mouse_use(self, quiet=False):
        """Usa o item selecionado no bloco sob o mouse (precisa estar ao alcance do jogador)."""
        s = self.state
        tx, ty = self._mouse_tile()
        if not self._reach_ok(tx, ty):
            if not quiet:
                self.err("Longe demais! Chegue mais perto.")
            return
        dx, dy = tx + .5 - s.px, ty + .5 - s.py
        s.facing = ((1 if dx >= 0 else -1), 0) if abs(dx) >= abs(dy) else (0, (1 if dy >= 0 else -1))
        s.aim = (tx, ty)
        try:
            self._use_tool()
        finally:
            s.aim = None

    def _build_origin(self, sid, rot, tx, ty):
        w, h = building.Structures.dims(data.STRUCTS[sid], rot)
        return tx - w // 2, ty - h // 2

    def _update_build_preview(self):
        b, s = self.build, self.state
        tx, ty = self._mouse_tile()
        modo = b["modo"]
        b["ok"], b["info"] = False, ""
        if modo == "colocar" and b["sid"]:
            if s.inv.count(b["sid"]) < 1:
                b["info"] = "Você não tem mais deste item."
                return
            x, y = self._build_origin(b["sid"], b["rot"], tx, ty)
            b["pos"] = (x, y)
            b["ok"], b["info"] = building.validate_placement(s, b["sid"], x, y, b["rot"])
            if b["ok"]:
                b["info"] = "Local válido."
        elif modo == "mover" and b["picked"] is not None:
            inst = s.structs.by_id.get(b["picked"])
            if inst:
                x, y = self._build_origin(inst["s"], b["rot"], tx, ty)
                b["pos"] = (x, y)
                b["ok"], b["info"] = building.validate_placement(s, inst["s"], x, y, b["rot"], ignore_id=inst["id"])
                if b["ok"]:
                    b["info"] = "Local válido. Clique para confirmar."
        elif modo == "mover":
            inst = s.structs.at(tx, ty)
            b["info"] = f"Clique para pegar: {data.STRUCTS[inst['s']]['nome']}" if inst else "Passe o mouse sobre uma construção."
            b["ok"] = bool(inst)
        elif modo == "guardar":
            inst = s.structs.at(tx, ty)
            if inst:
                b["ok"], why = building.can_store(s, inst)
                b["info"] = f"Guardar {data.STRUCTS[inst['s']]['nome']}" if b["ok"] else why
            else:
                b["info"] = "Passe o mouse sobre uma construção."

    def _build_click(self):
        b, s = self.build, self.state
        tx, ty = self._mouse_tile()
        if b["modo"] == "colocar":
            if not b["sid"]:
                return
            ok, res = building.place(s, b["sid"], *b["pos"], b["rot"], hist=self.hist)
            if ok:
                self.audio.play("build")
                if s.inv.count(b["sid"]) < 1:
                    items = self.placeables()
                    b["sid"] = items[0][0] if items else None
            else:
                self.err(res)
        elif b["modo"] == "mover":
            if b["picked"] is None:
                inst = s.structs.at(tx, ty)
                if inst:
                    b["picked"], b["rot"] = inst["id"], inst["rot"]
                    self.audio.play("click")
            else:
                ok, why = building.move(s, b["picked"], *b["pos"], b["rot"], hist=self.hist)
                if ok:
                    self.audio.play("build")
                    b["picked"] = None
                else:
                    self.err(why)
        else:
            inst = s.structs.at(tx, ty)
            if inst:
                ok, why = building.store(s, inst["id"], hist=self.hist)
                if ok:
                    self.audio.play("build")
                    self.say("Guardado no inventário.", (200, 230, 255))
                else:
                    self.err(why)

    def _build_cancel(self):
        b = self.build
        if b["picked"] is not None:
            b["picked"] = None
        elif b["modo"] == "colocar" and b["sid"]:
            b["sid"] = None
        else:
            self.exit_build()

    # ------------------------------------------------------------ interação
    def find_interactable(self):
        s = self.state
        ptx, pty = int(s.px), int(s.py)
        best, bd = None, 1e9
        for f in s.world.fixed:
            dx, dy = f["door"]
            d = math.hypot(s.px - (dx + .5), s.py - (dy + .5))
            if d < 2.2 and d < bd:
                aberta = routine.aberta(f["shop"], s.clock.minutes)
                best, bd = ("loja", f["shop"], f"[{self.prefs.key_name('interagir')}] " + ("Entrar em " if aberta else "Fechada: ") + data.SHOPS[f["shop"]]["nome"]), d
        for inst in s.structs.by_id.values():
            sd = data.STRUCTS[inst["s"]]
            kind = sd.get("interage")
            if not kind:
                continue
            w, h = building.Structures.dims(sd, inst["rot"])
            if inst["x"] - 1 <= ptx <= inst["x"] + w and inst["y"] - 1 <= pty <= inst["y"] + h:
                d = math.hypot(s.px - (inst["x"] + w / 2), s.py - (inst["y"] + h / 2))
                if d < bd:
                    k = self.prefs.key_name("interagir")
                    label = {"casa": f"[{k}] Entrar em casa", "torneira": f"[{k}] Encher o regador",
                             "quartinho": f"[{k}] Abrir o quartinho", "tanque": f"[{k}] Cuidar do tanque de peixes",
                             "fruteira": self._fruit_label(inst), "barraca": f"[{k}] Barraca de vendas", "animais": f"[{k}] Cuidar dos animais ({sd['nome']})",
                             "portao": f"[{k}] Abrir/fechar portão", "racao": f"[{k}] Fabricar ração",
                             "forno": f"[{k}] Usar o forno de fundição"}[kind]
                    best, bd = (kind, inst["id"], label), d
        for kind, dx_, dy_, dw_, dh_ in s.world.decor:
            if kind == "quadro":
                d = math.hypot(s.px - (dx_ + dw_ / 2), s.py - (dy_ + dh_ / 2 + .4))
                if d < 2.4 and d < bd:
                    best, bd = ("quadro", None, f"[{self.prefs.key_name('interagir')}] Quadro de empregos"), d
            elif kind == "mina":
                d = math.hypot(s.px - (dx_ + dw_ / 2), s.py - (dy_ + dh_ + .3))
                if d < 2.6 and d < bd:
                    best, bd = ("mina", None, f"[{self.prefs.key_name('interagir')}] Entrar na mina"), d
        return best

    def _fruit_label(self, inst):
        k = self.prefs.key_name("interagir")
        return f"[{k}] Colher frutas" if orchard.ready(inst) else f"[{k}] Ver árvore"

    def interact(self):
        it = self.find_interactable()
        if not it:
            return
        kind, ref, _ = it
        if kind == "loja" and not routine.aberta(ref, self.state.clock.minutes) and not self.dev_god:
            self.err(routine.motivo_fechada(ref, self.state.clock.minutes))
            return
        if kind == "loja" and data.SHOPS[ref].get("tipo") == "banco":
            self.mode = "banco"
            self.audio.play("coin")
        elif kind == "loja" and data.SHOPS[ref].get("tipo") == "ferreiro":
            self.mode = "ferreiro"
            self.smith_tab = "melhorar"
            self.audio.play("coin")
        elif kind == "mina":
            if self.state.mine_best >= 5:
                self.mode = "mina_menu"
                self.audio.play("click")
            else:
                self.enter_mine(1)
        elif kind == "quadro":
            self.mode = "quadro"
            self.audio.play("click")
        elif kind == "barraca":
            self.box_id = ref
            self.mode = "barraca"
            self.audio.play("click")
        elif kind == "fruteira":
            ok, msg = orchard.harvest(self.state, self.state.structs.by_id[ref])
            self.say(msg, (150, 255, 150)) if ok else self.err(msg)
            self.audio.play("coin" if ok else "error")
        elif kind == "tanque":
            self.box_id = ref
            self.mode = "tanque"
            self.audio.play("click")
        elif kind == "loja":
            self.shop_id = ref
            self.shop_set_tab(0)
            self.mode = "shop"
            self.audio.play("coin")
        elif kind == "casa":
            self.enter_house()
        elif kind == "torneira":
            self.state.water = self.state.water_cap()
            self.say("Regador cheio!", (150, 210, 255))
            self.audio.play("water")
        elif kind == "quartinho":
            self.box_id = ref
            self.mode = "quartinho"
            self.audio.play("click")
        elif kind == "animais":
            self.animals_home = ref
            self.mode = "animals"
        elif kind == "racao":
            self.mode = "racao"
        elif kind == "forno":
            self.box_id = ref
            self.mode = "forno"
            self.audio.play("click")
        elif kind == "portao":
            inst = self.state.structs.by_id[ref]
            inst["data"]["aberto"] = not inst["data"].get("aberto", False)
            self.audio.play("click")

    def do_sleep(self):
        summary = self.state.end_day(forced=False)
        self.audio.play("sleep")
        self.after_new_day(summary, slept=True)
        self.mode = "casa" if self.in_house else "play"

    # ------------------------------------------------------------ dentro de casa
    def enter_house(self):
        self.state.mounted = False
        self.in_house = True
        self.hx, self.hy = interior.SPAWN
        self.mode = "casa"
        self.mouse_hold = False
        self.audio.play("click")

    def leave_house(self):
        s = self.state
        casa = next((i for i in s.structs.by_id.values() if i["s"] == "casa"), None)
        x, y = (casa["x"] + 2.5, casa["y"] + 4.6) if casa else (44.5, 36.5)
        self.in_house = False
        self.mode = "play"
        self.dev_teleport(x, y)
        s.facing = (0, 1)
        self.audio.play("click")

    def house_interact(self):
        what = interior.nearest(self.hx, self.hy)
        if what == "sair":
            self.leave_house()
        elif what == "cozinhar":
            self.mode = "cozinha"
            self.audio.play("click")
        elif what == "mesa":
            self.rel_idx = max(0, len(self.state.worker_hist) - 1)
            self.state.worker_novo = False
            self.mode = "relatorio"
            self.audio.play("click")
        elif what == "dormir":
            minutes = self.state.clock.minutes
            if interior.can_sleep(minutes) or self.dev_god:
                self.mode = "confirm_sleep"
            else:
                self.err(interior.sleep_message(minutes))

    def _house_prompt(self):
        k = self.prefs.key_name("interagir")
        what = interior.nearest(self.hx, self.hy)
        if what == "sair":
            return f"[{k}] Sair de casa"
        if what == "cozinhar":
            return f"[{k}] Cozinhar"
        if what == "mesa":
            return f"[{k}] Ler o relatório do ajudante" + (" (novo!)" if self.state.worker_novo else "")
        if what == "dormir":
            return f"[{k}] Dormir até amanhã" if interior.can_sleep(self.state.clock.minutes) or self.dev_god \
                else f"[{k}] Cama (só dá para dormir a partir das {interior.SLEEP_HOUR}h)"
        return ""

    def _update_house(self, dt):
        s = self.state
        keys = self._keys()
        kb = self.prefs.key
        vx = int(keys[kb("direita")] or keys[pygame.K_RIGHT]) - int(keys[kb("esquerda")] or keys[pygame.K_LEFT])
        vy = int(keys[kb("baixo")] or keys[pygame.K_DOWN]) - int(keys[kb("cima")] or keys[pygame.K_UP])
        self.moving = bool(vx or vy)
        if self.moving:
            s.facing = (vx, 0) if vx else (0, vy)
            n = math.hypot(vx, vy)
            dx, dy = vx / n * PLAYER_SPEED * dt, vy / n * PLAYER_SPEED * dt
            if not interior.blocked(self.hx + dx, self.hy):
                self.hx += dx
            if not interior.blocked(self.hx, self.hy + dy):
                self.hy += dy
        summary = s.tick(dt * self.dev_speed)
        if self.dev_god:
            s.energy = float(MAX_ENERGY)
        if summary:
            self.after_new_day(summary, slept=False)
            self.hx, self.hy = interior.SPAWN
        self.prompt = self._house_prompt()
        if self.tool_anim > 0:
            self.tool_anim -= dt

    def _handle_house(self, e):
        kb = self.prefs.key
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k == pygame.K_ESCAPE:
                self.mode = "pause"
            elif k == kb("interagir"):
                self.house_interact()
            elif k == kb("inventario"):
                self.mode, self.inv_sel = "inv", None
            elif k == kb("ajuda"):
                self.show_help = True
            elif k == kb("salvar"):
                self.save()
            elif k == kb("dev"):
                self.mode = "dev"
            elif k == pygame.K_0:
                self.state.sel = 9
            elif pygame.K_1 <= k <= pygame.K_9:
                self.state.sel = k - pygame.K_1
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            self.house_interact()

    # ------------------------------------------------------------ mina
    MINE_DOOR = (50.0, 13.7)
    MINE_OX, MINE_OY = (SW - mine.W * T) // 2, 112

    def _mine_floor(self, floor):
        day = self.state.clock.day
        if self.mcache_day != day:
            self.mcache, self.mcache_day = {}, day
        if floor not in self.mcache:
            self.mcache[floor] = mine.generate(self.state.seed, day, floor)
        return self.mcache[floor]

    def enter_mine(self, floor=1):
        s = self.state
        s.mounted = False
        self.in_mine = True
        self.mfloor = floor
        self.mfl = self._mine_floor(floor)
        self.mx, self.my = mine.SPAWN
        self.mparts = []
        self.mhp, self.mhit, self.mswing = 100, 0.0, 0.0
        self.mode = "mina"
        self.mouse_hold = False
        s.mine_best = max(s.mine_best, floor)
        self.dev_teleport(*self.MINE_DOOR)         # se salvar lá dentro, volta pela porta da mina
        self.audio.play("click")
        self.say(f"Andar {floor}", (220, 220, 255))

    def leave_mine(self):
        self.in_mine = False
        self.mode = "play"
        self.dev_teleport(*self.MINE_DOOR)
        self.state.facing = (0, 1)
        self.audio.play("click")

    def mine_descend(self):
        self.mfloor += 1
        self.mfl = self._mine_floor(self.mfloor)
        self.mx, self.my = mine.SPAWN
        self.mparts = []
        s = self.state
        if self.mfloor > s.mine_best:
            s.mine_best = self.mfloor
            if self.mfloor % 5 == 0:
                self.say(f"Andar {self.mfloor}! Agora o elevador da entrada leva até aqui.", (255, 240, 150))
            else:
                self.say(f"Andar {self.mfloor}", (220, 220, 255))
        else:
            self.say(f"Andar {self.mfloor}", (220, 220, 255))
        self.audio.play("click")

    def mine_interact(self):
        if mine.near_stairs(self.mfl, self.mx, self.my):
            self.mine_descend()
        elif self.mfloor == 1 and mine.near_ladder(self.mx, self.my):
            self.leave_mine()
        elif mine.near_ladder(self.mx, self.my):
            self.mfloor -= 1                      # a escada de saída sobe um andar
            self.mfl = self._mine_floor(self.mfloor)
            st = self.mfl.stairs
            self.mx, self.my = (st[0] + .5, st[1] + .9) if st else mine.SPAWN
            self.say(f"Andar {self.mfloor}", (220, 220, 255))
            self.audio.play("click")

    def _mine_prompt(self):
        k = self.prefs.key_name("interagir")
        if mine.near_stairs(self.mfl, self.mx, self.my):
            return f"[{k}] Descer a escada"
        if mine.near_ladder(self.mx, self.my):
            return f"[{k}] Sair da mina" if self.mfloor == 1 else f"[{k}] Subir para o andar {self.mfloor - 1}"
        return ""

    def _set_tool_icon(self):
        slot = self.state.inv.slots[self.state.sel]
        self.tool_icon = assets.tool_name(data.ITEMS[slot["i"]]) if slot else None

    def mine_act(self, tx, ty):
        slot = self.state.inv.slots[self.state.sel]
        if slot and data.ITEMS[slot["i"]].get("tool") == "espada":
            res = mine.attack(self.state, self.mfl, self.mx, self.my, self.state.facing, self.mfloor)
            if res["ok"]:
                self.tool_anim = 0.25
                self.tool_col = (220, 226, 240)
                self._set_tool_icon()
                self.mswing = 0.22
                self.audio.play("chop" if res["hit"] else "click")
                if res["kills"]:
                    for _ in range(12):
                        a = random.uniform(0, math.tau)
                        self.mparts.append([self.mx * T, self.my * T - 16, math.cos(a) * 90, math.sin(a) * 90 - 50, .5, (120, 220, 110)])
                if res["msg"]:
                    self.say(res["msg"], (255, 240, 170))
            elif res["msg"]:
                self.err(res["msg"])
            return
        self.mine_hit(tx, ty)

    def mine_hurt(self, dano):
        self.mhp -= dano
        self.mhit = 1.0
        self.audio.play("error")
        self.say(f"Ai! -{dano} de vida", (255, 150, 150))
        if self.mhp <= 0:
            s = self.state
            perda = min(300, s.money // 10)
            s.money -= perda
            self.mhp = 100
            self.leave_mine()
            self.say(f"Você desmaiou na mina e perdeu ${perda}.", (255, 170, 140))

    def mine_hit(self, tx, ty):
        res = mine.hit(self.state, self.mfl, tx, ty)
        if res["ok"]:
            self.tool_anim = 0.25
            self.tool_col = TOOL_COL["picareta"]
            self._set_tool_icon()
            self.audio.play("chop")
            col = sprites.ORE_COL.get(res["ore"], (170, 168, 178))
            for _ in range(10 if res["broke"] else 5):
                a = random.uniform(0, math.tau)
                sp = random.uniform(30, 110)
                self.mparts.append([tx * T + T / 2, ty * T + T / 2, math.cos(a) * sp, math.sin(a) * sp - 70,
                                    random.uniform(.35, .7), col])
            if res["msg"]:
                self.say(res["msg"], (255, 240, 170))
        elif res["msg"]:
            self.err(res["msg"])

    def _mine_facing_tile(self):
        fx, fy = self.state.facing
        return int(self.mx + fx * 0.8), int(self.my - 0.2 + fy * 0.8)

    def _mine_mouse_tile(self):
        mx, my = pygame.mouse.get_pos()
        return (mx - self.MINE_OX) // T, (my - self.MINE_OY) // T

    def _mine_click(self):
        tx, ty = self._mine_mouse_tile()
        ddx, ddy = tx + .5 - self.mx, ty + .5 - (self.my - .3)
        if abs(ddx) > 0.2 or abs(ddy) > 0.2:                          # o personagem vira para onde você clicou
            self.state.facing = (1 if ddx > 0 else -1, 0) if abs(ddx) >= abs(ddy) else (0, 1 if ddy > 0 else -1)
        if math.hypot(ddx, ddy) <= 2.6:
            self.mine_act(tx, ty)
        else:
            self.mine_act(*self._mine_facing_tile())

    def _update_mine(self, dt):
        s = self.state
        keys = self._keys()
        kb = self.prefs.key
        vx = int(keys[kb("direita")] or keys[pygame.K_RIGHT]) - int(keys[kb("esquerda")] or keys[pygame.K_LEFT])
        vy = int(keys[kb("baixo")] or keys[pygame.K_DOWN]) - int(keys[kb("cima")] or keys[pygame.K_UP])
        self.moving = bool(vx or vy)
        if self.moving:
            s.facing = (vx, 0) if vx else (0, vy)
            n = math.hypot(vx, vy)
            dx, dy = vx / n * PLAYER_SPEED * dt, vy / n * PLAYER_SPEED * dt
            if not mine.blocked(self.mfl, self.mx + dx, self.my):
                self.mx += dx
            if not mine.blocked(self.mfl, self.mx, self.my + dy):
                self.my += dy
        summary = s.tick(dt * self.dev_speed)
        if self.dev_god:
            s.energy = float(MAX_ENERGY)
        if summary:
            self.after_new_day(summary, slept=False)
            self.leave_mine()
            return
        dano = mine.update_enemies(self.mfl, self.mx, self.my, dt, self.mfloor)
        self.mhit = max(0.0, self.mhit - dt)
        self.mswing = max(0.0, self.mswing - dt)
        if dano and self.mhit <= 0:
            self.mine_hurt(dano)
            if not self.in_mine:
                return
        elif self.mhit <= 0 and self.mhp < 100:
            self.mregen += dt
            if self.mregen >= 1.0:
                self.mregen = 0.0
                self.mhp = min(100, self.mhp + 2)
        self.cd -= dt
        if self.cd <= 0:
            if keys[kb("usar")]:
                self.mine_act(*self._mine_facing_tile())
                self.cd = 0.35
            elif self.mouse_hold and not self._over_hotbar(pygame.mouse.get_pos()):
                self._mine_click()
                self.cd = 0.35
        if self.tool_anim > 0:
            self.tool_anim -= dt
        for p in self.mparts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 260 * dt
            p[4] -= dt
        self.mparts = [p for p in self.mparts if p[4] > 0]
        self.prompt = self._mine_prompt()

    def _handle_mine(self, e):
        kb = self.prefs.key
        s = self.state
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k == pygame.K_ESCAPE:
                self.mode = "pause"
            elif k == kb("interagir"):
                self.mine_interact()
            elif k == kb("inventario"):
                self.mode, self.inv_sel = "inv", None
            elif k == kb("ajuda"):
                self.show_help = True
            elif k == kb("salvar"):
                self.save()
            elif k == kb("dev"):
                self.mode = "dev"
            elif k == pygame.K_0:
                s.sel = 9
            elif pygame.K_1 <= k <= pygame.K_9:
                s.sel = k - pygame.K_1
        elif e.type == pygame.MOUSEWHEEL:
            s.sel = (s.sel - e.y) % 10
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                hit = [i for i, r in enumerate(self.ui.hotbar_rects) if r.collidepoint(e.pos)]
                if hit:
                    s.sel = hit[0]
                elif self.cd <= 0:
                    self._mine_click()
                    self.cd = 0.35
                    self.mouse_hold = True
            elif e.button == 3:
                self.mine_interact()
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.mouse_hold = False

    def draw_mine_scene(self):
        scr, s = self.screen, self.state
        if self.msurf is None:
            self.msurf = pygame.Surface((mine.W * T, mine.H * T))
        fl, surf = self.mfl, self.msurf
        key = (s.clock.day, self.mfloor)
        if self.mine_bg_key != key:
            self.mine_bg = pygame.Surface((mine.W * T, mine.H * T))
            sprites.draw_mine_floor(self.mine_bg, mine.W, mine.H, T, s.seed + self.mfloor * 31 + s.clock.day, fl.rails, fl.lanterns)
            self.mine_bg_key = key
        surf.blit(self.mine_bg, (0, 0))
        sprites.draw_mine_ladder(surf, mine.LADDER[0], mine.LADDER[1], T)
        if fl.stairs:
            sprites.draw_mine_stairs(surf, fl.stairs[0], fl.stairs[1], T)
        tool = {"k": self.tool_anim / 0.25, "cor": self.tool_col, "icon": self.tool_icon} if self.tool_anim > 0 else None
        items = []
        for (x, y), c in fl.cells.items():
            items.append(((y + 1) * T, lambda x=x, y=y, c=c: sprites.draw_mine_cell(surf, x, y, T, c, mine.ORE_HP.get(c["ore"], mine.ROCK_HP))))
        for e in fl.enemies:
            items.append((e["y"] * T, lambda e=e: sprites.draw_mine_enemy(surf, e["k"], e["x"] * T, e["y"] * T, self.t, e["hurt"] > 0,
                                                                     e["hp"] / e["max"])))
        blink = self.mhit > 0 and int(self.t * 20) % 2 == 0
        if not blink:
            items.append((self.my * T, lambda: sprites.draw_person(surf, self.mx * T, self.my * T, s.facing, self.moving, self.t, PLAYER_COL, tool)))
        for _, fn in sorted(items, key=lambda it: it[0]):
            fn()
        if self.mswing > 0:                                           # arco do golpe de espada
            fx, fy = s.facing
            cxp, cyp = self.mx * T + fx * 26, self.my * T - 16 + fy * 24
            ang = math.atan2(fy, fx)
            pygame.draw.arc(surf, (240, 246, 255), (cxp - 24, cyp - 24, 48, 48), -ang - 1.0, -ang + 1.0, 4)
        for p in self.mparts:
            pygame.draw.rect(surf, p[5], (int(p[0]), int(p[1]), 4, 4))
        scr.fill((10, 8, 12))
        scr.blit(surf, (self.MINE_OX, self.MINE_OY))
        px, py = self.MINE_OX + self.mx * T, self.MINE_OY + self.my * T - 24
        glows = [(px, py), (px, py), (self.MINE_OX + (mine.LADDER[0] + .5) * T, self.MINE_OY + (mine.LADDER[1] + .5) * T)]
        glows += [(self.MINE_OX + lx * T + 16, self.MINE_OY + 36) for lx in fl.lanterns]
        gfx.draw_night(scr, self.night, 0.5, glows)
        self.ui.text(scr, f"Andar {self.mfloor}", self.ui.f_m, (235, 235, 255), (SW // 2, 72), "midtop", True)
        self.ui.bar(scr, (24, 76, 200, 16), self.mhp / 100, (214, 60, 60))
        self.ui.text(scr, f"Vida {int(self.mhp)}/100", self.ui.f_xs, (255, 255, 255), (124, 84), "center", True)

    # ------------------------------------------------------------ quartinho
    def box(self):
        return self.state.structs.by_id.get(self.box_id)

    # ------------------------------------------------------------ banco e piscicultura
    def bank_do(self, fn, n):
        ok, msg = fn(self.state, n)
        self.audio.play("coin") if ok else self.err(msg)
        if ok:
            self.say(msg, (150, 255, 150))

    def tank_do(self, fn, qty=None):
        inst = self.box()
        if not inst:
            return
        ok, msg = fn(self.state, inst) if qty is None else fn(self.state, inst, qty)
        if ok:
            self.audio.play("click")
            self.say(msg, (150, 255, 150))
        else:
            self.err(msg)

    def toggle_tractor(self):
        s = self.state
        if s.mounted:
            s.mounted = False
            self.say("Você desceu do trator.", (255, 240, 170))
        elif s.inv.count("chave_trator") > 0:
            s.mounted = True
            self.trailer = 0
            self.say("No trator! Mais rápido e ferramentas de 3 blocos. [%s] para descer." % self.prefs.key_name("trator"), (255, 240, 170))
            self.audio.play("click")
        else:
            self.err("Você precisa da Chave do Trator (Carpintaria).")

    def smith_do(self, fn, *a):
        ok, msg = fn(self.state, *a)
        if ok:
            self.audio.play("coin")
            self.say(msg, (150, 255, 150))
        else:
            self.err(msg)

    def worker_do(self, fn, *a):
        ok, msg = fn(self.state, *a)
        if ok:
            self.audio.play("coin")
            self.say(msg, (150, 255, 150))
        else:
            self.err(msg)

    def contratar(self):
        sel = [t for t in worker.ORDEM if self.contrata_sel and t in self.contrata_sel]
        ok, msg = worker.hire(self.state, sel)
        self.contrata_conf = False
        if ok:
            self.contrata_sel = None
        self.audio.play("coin") if ok else self.audio.play("error")
        self.say(msg, (150, 255, 150)) if ok else self.err(msg)

    def forno_do(self, acao, bar=None, lotes=1):
        s = self.state
        inst = self.box()
        if inst is None or inst["s"] != "forno":
            return
        if acao == "iniciar":
            ok, msg = forno.start(s.inv, inst, bar, lotes)
        else:
            d = forno.dados(inst)
            if d["por"] == "funcionario" and forno.tem_saida(inst):
                worker.liberar_forno(s, inst)            # você mesmo retirou: ele não cobra por isso
            got = forno.retirar(s, inst, s.inv)
            ok = bool(got)
            msg = ("Retirou: " + ", ".join(f"{n}x {data.ITEMS[b]['nome']}" for b, n in got.items())) if got \
                else "Sem barras ou sem espaço no inventário."
        self.audio.play("coin" if ok else "error")
        self.say(msg, (150, 255, 150)) if ok else self.err(msg)

    def stall_put(self, i):
        inst = self.box()
        if inst:
            ok, why = stall.put(self.state, inst, i)
            self.audio.play("click") if ok else self.err(why)

    def stall_take(self, i):
        inst = self.box()
        if inst:
            ok, why = stall.take(self.state, inst, i)
            self.audio.play("click") if ok else self.err(why)

    def stall_collect(self):
        inst = self.box()
        if inst:
            ok, msg = stall.collect(self.state, inst)
            if ok:
                self.audio.play("coin")
                self.say(msg, (150, 255, 150))
            else:
                self.err(msg)

    def cook(self, rid, lotes=1):
        ok, msg = cooking.cook(self.state, rid, lotes)
        if ok:
            self.audio.play("coin")
            self.say(msg, (150, 255, 150))
        else:
            self.err(msg)

    def box_deposit(self, i):
        inst = self.box()
        if inst:
            ok, why = storage.deposit(self.state, inst, i)
            self.audio.play("click") if ok else self.err(why)

    def box_withdraw(self, i):
        inst = self.box()
        if inst:
            ok, why = storage.withdraw(self.state, inst, i)
            self.audio.play("click") if ok else self.err(why)

    def box_deposit_all(self):
        inst = self.box()
        if inst:
            n = storage.deposit_all(self.state, inst)
            self.say(f"{n} pilha(s) guardada(s)." if n else "Nada para guardar (a barra rápida fica com você).", (255, 240, 170))

    def box_upgrade(self):
        inst = self.box()
        if inst:
            ok, msg = storage.upgrade(self.state, inst)
            if ok:
                self.audio.play("coin")
                self.say(msg, (150, 255, 150))
            else:
                self.err(msg)

    def after_new_day(self, summary, slept=False):
        self._refresh_terrain()
        self.fade = 1.0
        self.hist.clear()
        self.save(silent=True)
        extra = []
        if summary["murchas"]:
            extra.append(f"{summary['murchas']} planta(s) murcharam com a nova estação")
        if summary["produtos"]:
            extra.append(f"{summary['produtos']} produto(s) animal prontos")
        if summary.get("nascidos"):
            extra.append(f"{summary['nascidos']} filhote(s) nasceram!")
        if summary.get("funcionario"):
            extra.append(summary["funcionario"].rstrip("."))
            extra.append("o relatório do ajudante está sobre a mesa da casa")
        if summary.get("barraca"):
            extra.append(f"a barraca vendeu {summary['barraca_itens']} item(ns) (${summary['barraca']} no caixa)")
        if summary.get("frutas"):
            extra.append(f"{summary['frutas']} árvore(s) com frutas")
        if summary.get("arvores"):
            extra.append(f"{summary['arvores']} muda(s) viraram árvore")
        if summary.get("gordos"):
            extra.append(f"{summary['gordos']} peixe(s) ficaram gordos")
        if summary.get("juros"):
            extra.append(f"o banco rendeu ${summary['juros']}")
        head = "Você dormiu bem." if slept else "Você desmaiou de cansaço..."
        self.say(head + (" " + "; ".join(extra) + "." if extra else ""), (200, 230, 255))
        self.audio.play("rooster")

    # ------------------------------------------------------------ eventos
    def _on_title(self):
        return (self.state is None or self.mode == "title"
                or (self.mode in ("slots", "settings") and self.menu_back == "title"))

    def _handle_title(self, e):
        if e.type == pygame.KEYDOWN:
            if self._capture_key(e):
                return
            if e.key == pygame.K_ESCAPE and self.mode in ("slots", "settings"):
                self.menu_exit()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.rebinding = None
            self.ui.click(e.pos)

    def handle(self, e):
        if self.touch.handle(e, self.mode):
            return
        if e.type == pygame.QUIT:
            self.quit()
        if e.type == pygame.KEYDOWN and self.rebinding is None and (
                e.key == pygame.K_F11 or (e.key == pygame.K_RETURN and e.mod & pygame.KMOD_ALT)):
            self.toggle_fullscreen()
            return
        m = self.mode
        if self._on_title():
            self._handle_title(e)
            return
        if self.show_help and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.show_help = False
            return
        if m == "play":
            self._handle_play(e)
        elif m == "casa":
            self._handle_house(e)
        elif m == "mina":
            self._handle_mine(e)
        elif m == "build":
            self._handle_build(e)
        else:
            self._handle_menu(e)

    def _handle_play(self, e):
        s = self.state
        kb = self.prefs.key
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k in (kb("cima"), kb("baixo"), kb("esquerda"), kb("direita"), kb("usar"),
                     pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                self.mouse_aim = False            # voltou para o teclado: o destaque segue o personagem
            if k == pygame.K_ESCAPE:
                self.mode = "pause"
            elif k == kb("inventario"):
                self.mode, self.inv_sel = "inv", None
            elif k == kb("mapa"):
                self.mode = "map"
            elif k == kb("construir"):
                self.enter_build()
            elif k == kb("interagir"):
                self.interact()
            elif k == kb("trator"):
                self.toggle_tractor()
            elif k == kb("ajuda"):
                self.show_help = True
            elif k == kb("salvar"):
                self.save()
            elif k == kb("dev"):
                self.mode = "dev"
            elif k == pygame.K_0:
                s.sel = 9
            elif pygame.K_1 <= k <= pygame.K_9:
                s.sel = k - pygame.K_1
        elif e.type == pygame.MOUSEMOTION:
            self.mouse_aim = True
        elif e.type == pygame.MOUSEWHEEL:
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.zoom_by(e.y)
            else:
                s.sel = (s.sel - e.y) % 10
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                self.mouse_aim = True
                hit = [i for i, r in enumerate(self.ui.hotbar_rects) if r.collidepoint(e.pos)]
                if hit:
                    s.sel = hit[0]
                elif self.cd <= 0:
                    self._mouse_use()
                    self.cd = 0.3
                    self.mouse_hold = True
            elif e.button == 3:
                self.interact()
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.mouse_hold = False

    def _handle_build(self, e):
        if e.type == pygame.KEYDOWN:
            k = e.key
            ctrl = e.mod & pygame.KMOD_CTRL
            kb = self.prefs.key
            if k in (pygame.K_ESCAPE,):
                self._build_cancel()
            elif k == kb("construir"):
                self.exit_build()
            elif k == kb("girar"):
                self.build_rotate()
            elif k == kb("grade"):
                self.toggle_grid()
            elif k == pygame.K_z and ctrl:
                self.build_undo()
            elif k == pygame.K_y and ctrl:
                self.build_redo()
            elif k == pygame.K_TAB:
                modes = ["colocar", "mover", "guardar"]
                self.build_set_mode(modes[(modes.index(self.build["modo"]) + 1) % 3])
        elif e.type == pygame.MOUSEWHEEL:
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.zoom_by(e.y)
            else:
                self.build_scroll -= e.y
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                if not self.ui.click(e.pos):
                    self._build_click()
            elif e.button == 3:
                self._build_cancel()

    def _handle_menu(self, e):
        m = self.mode
        kb = self.prefs.key
        if e.type == pygame.KEYDOWN:
            if self._capture_key(e):
                return
            if m in ("slots", "settings"):
                if e.key == pygame.K_ESCAPE:
                    self.menu_exit()
                return
            if m == "guia":
                if e.key == pygame.K_ESCAPE:
                    self.mode = "pause"
                elif e.key == pygame.K_DOWN:
                    self.guia_scroll += 44
                elif e.key == pygame.K_UP:
                    self.guia_scroll -= 44
                return
            if m == "dev" and e.key == kb("dev"):
                self.close_menu()
                return
            if e.key == pygame.K_ESCAPE or (m == "inv" and e.key == kb("inventario")) or (m == "map" and e.key == kb("mapa")) \
                    or (m == "shop" and e.key == kb("interagir")):
                self.close_menu()
            elif m == "shop":
                if e.key == pygame.K_DOWN:
                    self.shop_select(self.shop_sel + 1)
                elif e.key == pygame.K_UP:
                    self.shop_select(max(0, self.shop_sel - 1))
                elif e.key in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_EQUALS):
                    self.shop_add_qty(1)
                elif e.key in (pygame.K_LEFT, pygame.K_MINUS):
                    self.shop_add_qty(-1)
            elif m == "confirm_sleep" and e.key in (pygame.K_RETURN, pygame.K_y):
                self.do_sleep()
        elif e.type == pygame.MOUSEWHEEL and m == "shop":
            self.shop_scroll -= e.y
        elif e.type == pygame.MOUSEWHEEL and m == "guia":
            self.guia_scroll -= e.y * 44
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.rebinding = None
            self.ui.click(e.pos)

    # ------------------------------------------------------------ atualização
    def update(self, dt):
        self.t += dt
        if self.msg_t > 0:
            self.msg_t -= dt
        if self.fade > 0:
            self.fade = max(0.0, self.fade - dt * 0.7)
        if self._on_title():
            return
        if self.mode != "play":
            self.mouse_hold = False
        if self.mode in ("play", "build"):
            self._update_world(dt)
            if self.mode == "build":
                self._update_build_preview()
        elif self.mode == "casa":
            self._update_house(dt)
        elif self.mode == "mina":
            self._update_mine(dt)
        # a câmera sempre acompanha o jogador
        s = self.state
        tx, ty = s.px * T - self.vw / 2, s.py * T - self.vh / 2
        mx, my = s.world.w * T - self.vw, s.world.h * T - self.vh
        k = min(1.0, dt * 8)
        self.cam[0] += (max(0, min(mx, tx)) - self.cam[0]) * k
        self.cam[1] += (max(0, min(my, ty)) - self.cam[1]) * k

    def _update_world(self, dt):
        s = self.state
        keys = self._keys()
        kb = self.prefs.key
        vx = int(keys[kb("direita")] or keys[pygame.K_RIGHT]) - int(keys[kb("esquerda")] or keys[pygame.K_LEFT])
        vy = int(keys[kb("baixo")] or keys[pygame.K_DOWN]) - int(keys[kb("cima")] or keys[pygame.K_UP])
        self.moving = bool(vx or vy)
        if self.moving:
            if vx and not vy:
                s.facing = (vx, 0)
            elif vy and not vx:
                s.facing = (0, vy)
            else:
                s.facing = (vx, 0)
            n = math.hypot(vx, vy)
            sp = PLAYER_SPEED * (0.85 if s.weather == "neve" else 1.0) * (1.9 if s.mounted else 1.0)
            dx, dy = vx / n * sp * dt, vy / n * sp * dt
            if self.dev_noclip:                                   # modo desenvolvedor: atravessa tudo
                s.px = max(0.5, min(s.world.w - 0.5, s.px + dx * 1.6))
                s.py = max(0.5, min(s.world.h - 0.5, s.py + dy * 1.6))
            else:
                if s.can_stand(s.px + dx, s.py):
                    s.px += dx
                if s.can_stand(s.px, s.py + dy):
                    s.py += dy
        summary = s.tick(dt * self.dev_speed)
        if self.dev_god:
            s.energy = float(MAX_ENERGY)
        if summary:
            self.after_new_day(summary, slept=False)
        self._update_weather(dt)
        self._update_animals(dt)
        self._update_worker(dt)
        it = self.find_interactable()
        self.prompt = it[2] if it and self.mode == "play" else ""
        self.cd -= dt
        if self.mode == "play" and self.cd <= 0:
            if keys[kb("usar")]:
                self._use_tool()
                self.cd = 0.3
            elif self.mouse_hold and self.mouse_aim and not self._over_hotbar(pygame.mouse.get_pos()):
                self._mouse_use(quiet=True)       # segurar o botão do mouse repete a ação
                self.cd = 0.3
        if self.tool_anim > 0:
            self.tool_anim -= dt
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 260 * dt
            p[4] -= dt
        self.parts = [p for p in self.parts if p[4] > 0]

    def _use_tool(self):
        s = self.state
        res = actions.use_selected(s)
        if res["build"]:
            self.enter_build(res["build"])
            return
        if res["ok"]:
            slot = s.inv.slots[s.sel]
            it = data.ITEMS[slot["i"]] if slot else None
            self.tool_anim = 0.25
            self.tool_col = TOOL_COL.get(it.get("tool") if it else "", (150, 108, 66))
            self._set_tool_icon()
            if res["sfx"]:
                self.audio.play(res["sfx"])
            self.say(res["msg"], (255, 240, 170))
            for fx in res["fx"]:
                self._spawn_fx(fx)
                if fx[0] == "harvest" and s.mounted:
                    self.trailer = min(6, self.trailer + 1)
        else:
            self.err(res["msg"])

    def _spawn_fx(self, fx):
        kind, tx, ty = fx[0], fx[1], fx[2]
        col = {"dirt": (120, 84, 50), "water": (110, 180, 250), "splash": (130, 190, 250), "harvest": fx[3] if len(fx) > 3 else (255, 255, 255),
               "chip": (150, 110, 70)}[kind]
        if kind == "chip" and fx[3] == "rock":
            col = (160, 160, 168)
        elif kind == "chip" and fx[3] == "bush":
            col = (90, 170, 70)
        for _ in range(10):
            a = random.uniform(0, math.tau)
            sp = random.uniform(30, 110)
            self.parts.append([tx * T + T / 2, ty * T + T / 2, math.cos(a) * sp, math.sin(a) * sp - 70, random.uniform(.35, .7), col])

    def _update_weather(self, dt):
        s = self.state
        if s.weather != self.wkind:
            self.wkind = s.weather
            self.wps = gfx.new_weather_particles(s.weather, SW, SH)
        gfx.update_weather_particles(self.wps, s.weather, dt, SW, SH)
        if s.weather == "tempestade" and random.random() < dt * 0.12:
            self.flash = 1.0
        self.flash = max(0.0, self.flash - dt * 2.5)

    WORK_LABEL = {"plantar": "Plantando", "adubar": "Adubando", "regar": "Regando", "colher": "Colhendo", "racao": "Fazendo ração",
                  "animais": "Cuidando dos animais", "frutas": "Colhendo frutas", "fundir": "Operando o forno"}

    def _update_worker(self, dt):
        """O funcionário anda pela fazenda das 7h às 18h e vai fazendo uma tarefa de cada vez (veja worker.py)."""
        s = self.state
        if not s.worker or not (data.FUNC['hora_inicio'] <= s.clock.hour < data.FUNC['hora_fim']):
            self.wk = None
            return
        wk = self.wk
        if wk is None or wk["day"] != s.clock.day:
            casa = next((i for i in s.structs.by_id.values() if i["s"] == "casa"), None)
            x, y = (casa["x"] + 2.5, casa["y"] + 4.6) if casa else (44.5, 36.5)
            wk = self.wk = {"x": x, "y": y, "job": None, "doing": 0.0, "cool": 1.0, "face": (0, 1), "day": s.clock.day, "dest": None}
        if wk["doing"] > 0:
            wk["doing"] -= dt
            if wk["doing"] <= 0:
                ok = worker.do_job(s, wk["job"])
                if ok and wk["job"]["t"] in ("plantar", "adubar", "colher"):
                    self.audio.play("plant" if wk["job"]["t"] != "colher" else "harvest")
                wk["job"], wk["cool"] = None, (0.4 if ok else 3.0)
            return
        if wk["job"] is None:
            wk["cool"] -= dt
            if wk["cool"] > 0 and wk["dest"] is None:
                return
            if wk["dest"] is None:
                job = worker.next_job(s, (wk["x"], wk["y"]))
                if job:
                    wk["job"] = job
                else:                                                         # nada a fazer: passeia um pouco
                    wk["dest"] = (random.uniform(42, 52), random.uniform(34, 41))
                    wk["cool"] = 3.0
        target = wk["job"]["pos"] if wk["job"] else wk["dest"]
        dx, dy = target[0] - wk["x"], target[1] - wk["y"]
        d = math.hypot(dx, dy)
        if d < 0.15:
            if wk["job"]:
                wk["doing"] = 0.9
                wk["tool_phase"] = 0.9
            else:
                wk["dest"] = None
            return
        sp = 3.0 * dt
        wk["x"] += dx / d * min(sp, d)
        wk["y"] += dy / d * min(sp, d)
        wk["face"] = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)

    def _update_animals(self, dt):
        s = self.state
        for a in s.animals:
            inst = s.structs.by_id.get(a["home"])
            if not inst:
                continue
            cx, cy, cw, ch = data.STRUCTS[inst["s"]]["curral"]
            x0, x1 = inst["x"] + cx + .45, inst["x"] + cx + cw - .45
            y0, y1 = inst["y"] + cy + .8, inst["y"] + cy + ch - .15
            p = self.apos.get(a["id"])
            if p is None or not (x0 - 4 <= p["x"] <= x1 + 4 and y0 - 4 <= p["y"] <= y1 + 4):
                p = {"x": random.uniform(x0, x1), "y": random.uniform(y0, y1), "tx": 0, "ty": 0, "wait": random.uniform(0, 2), "dir": 1, "walk": False}
                p["tx"], p["ty"] = p["x"], p["y"]
                self.apos[a["id"]] = p
            p["x"], p["y"] = min(max(p["x"], x0), x1), min(max(p["y"], y0), y1)
            if p["wait"] > 0:
                p["wait"] -= dt
                p["walk"] = False
                continue
            dx, dy = p["tx"] - p["x"], p["ty"] - p["y"]
            d = math.hypot(dx, dy)
            sp = (0.55 if a["t"] in ("vaca", "porco") else 0.9) * dt
            if d < 0.08:
                p["wait"] = random.uniform(1, 4)
                p["tx"], p["ty"] = random.uniform(x0, x1), random.uniform(y0, y1)
            else:
                p["walk"] = True
                p["x"] += dx / d * sp
                p["y"] += dy / d * sp
                if abs(dx) > .02:
                    p["dir"] = 1 if dx > 0 else -1

    # ------------------------------------------------------------ desenho do mundo
    def _fence_conn(self, inst):
        st = self.state.structs

        def c(x, y):
            o = st.at_layer(x, y, "objeto")
            return int(bool(o and data.STRUCTS[o["s"]].get("conecta")))
        x, y = inst["x"], inst["y"]
        return (c(x - 1, y), c(x + 1, y), c(x, y - 1), c(x, y + 1))

    def draw_world(self):
        s, scr = self.state, self.view
        VW, VH = self.vw, self.vh
        cx, cy = int(self.cam[0]), int(self.cam[1])
        season, t = s.clock.season, self.t
        scr.blit(self.terrain, (0, 0), (cx, cy, VW, VH))
        x0, y0 = max(0, cx // T), max(0, cy // T)
        x1, y1 = min(s.world.w, (cx + VW) // T + 2), min(s.world.h, (cy + VH) // T + 2)
        gfx.draw_water_shimmer(scr, s.world, (cx, cy), t, (x0, y0, x1, y1))
        for (x, y), soil in s.farm.soil.items():
            if x0 <= x < x1 and y0 <= y < y1:
                gfx.draw_soil(scr, x * T - cx, y * T - cy, soil["wet"], soil["fert"])
        picked = self.build["picked"] if self.mode == "build" else None
        for inst in s.structs.by_id.values():
            sd = data.STRUCTS[inst["s"]]
            if sd["camada"] == "chao" and inst["id"] != picked:
                w, h = building.Structures.dims(sd, inst["rot"])
                sprites.draw_structure(scr, inst["s"], inst, inst["x"] * T - cx, inst["y"] * T - cy, w * T, h * T, season, t)
        self._draw_locked(cx, cy)

        draw = []
        for y in range(y0, y1):
            for x in range(x0, x1):
                o = s.world.objects.get((x, y))
                if o:
                    px, by = x * T + T // 2 - cx, (y + 1) * T - 5 - cy
                    fn = {"tree": lambda px=px, by=by, o=o: gfx.draw_tree(scr, px, by, season, o["v"], t),
                          "rock": lambda px=px, by=by, o=o: gfx.draw_rock(scr, px, by, season, o["v"]),
                          "bush": lambda px=px, by=by, o=o: gfx.draw_bush(scr, px, by, season, o["v"], t)}[o["k"]]
                    draw.append(((y + 1) * T, fn))
        for (x, y), soil in s.farm.soil.items():
            cr = soil["crop"]
            if cr and x0 <= x < x1 and y0 <= y < y1:
                c = data.CROPS[cr["id"]]
                st = crop_stage(c, cr["prog"])
                px, by = x * T + T // 2 - cx, (y + 1) * T - 6 - cy
                draw.append(((y + 1) * T - 1, lambda c=c, st=st, px=px, by=by: gfx.draw_crop(scr, c, st, px, by, t)))
                if st < 3 and not soil["wet"] and s.weather not in ("chuva", "tempestade") and self.mode == "play":
                    wy = by - 38 + math.sin(t * 4 + x) * 2
                    draw.append((9999999, lambda px=px, wy=wy: (pygame.draw.polygon(scr, (90, 170, 240), [(px, wy - 9), (px - 5, wy), (px + 5, wy)]),
                                                               pygame.draw.circle(scr, (90, 170, 240), (px, int(wy) + 1), 5))))
        for inst in s.structs.by_id.values():
            sd = data.STRUCTS[inst["s"]]
            if sd["camada"] == "objeto" and inst["id"] != picked:
                w, h = building.Structures.dims(sd, inst["rot"])
                if inst["x"] + w < x0 or inst["x"] > x1 or inst["y"] + h < y0 or inst["y"] > y1:
                    continue
                conn = self._fence_conn(inst) if sd.get("conecta") else None
                draw.append(((inst["y"] + h) * T - BASE_BIAS, lambda inst=inst, w=w, h=h, conn=conn: sprites.draw_structure(
                    scr, inst["s"], inst, inst["x"] * T - cx, inst["y"] * T - cy, w * T, h * T, season, t, conn)))
        awake = s.clock.darkness() < 0.5            # à noite os bichos dormem lá dentro
        for a in (s.animals if awake else []):
            p = self.apos.get(a["id"])
            inst = s.structs.by_id.get(a["home"])
            if p and inst and inst["id"] != picked:
                prod = data.ITEMS[data.ANIMALS[a["t"]]["produto"]]["cor"]
                # o curral fica dentro da área da construção: o bicho é desenhado DEPOIS da construção
                # (que usa a base como chave), mas ainda antes do jogador que esteja na frente dela
                base = (inst["y"] + building.Structures.dims(data.STRUCTS[inst["s"]], inst["rot"])[1]) * T - BASE_BIAS
                draw.append((base + 0.5 + p["y"] * 0.001, lambda a=a, p=p, prod=prod: sprites.draw_animal(
                    scr, a["t"], p["x"] * T - cx, p["y"] * T - cy, p["dir"], t, a["pronto"], prod,
                    walk=p.get("walk", False), baby=a.get("filhote", 0) > 0)))
        if 7 <= s.clock.hour < 19 and s.weather not in ("tempestade",):      # fregueses passeando perto das barracas
            for inst in s.structs.by_id.values():
                if inst["s"] == "barraca" and not stall.is_empty(inst) and x0 - 6 <= inst["x"] <= x1 + 3 and y0 - 6 <= inst["y"] <= y1 + 3:
                    for k in range(2):
                        ph = t * 0.35 + inst["id"] * 2.0 + k * 3.1
                        fx = inst["x"] + 1.5 + math.sin(ph) * 2.6
                        fy = inst["y"] + 2 + 0.8 + k * 0.7
                        pal = CUSTOMERS[(inst["id"] + k) % len(CUSTOMERS)]
                        face = (1 if math.cos(ph) > 0 else -1, 0)
                        draw.append((fy * T, lambda fx=fx, fy=fy, pal=pal, face=face: sprites.draw_person(
                            scr, fx * T - cx, fy * T - cy, face, True, t, pal)))
        wk = self.wk
        if s.worker and wk:                                                    # o funcionário trabalhando pela fazenda
            fazendo = wk["doing"] > 0
            ferr = {"k": (wk["doing"] / 0.9) % 0.5 * 2, "cor": (190, 190, 200)} if fazendo else None
            draw.append((wk["y"] * T, lambda: sprites.draw_person(
                scr, wk["x"] * T - cx, wk["y"] * T - cy, wk["face"], not fazendo and (wk["job"] is not None or wk["dest"] is not None), t, WORKER_COL, ferr)))
            if fazendo and wk["job"]:
                lab = self.WORK_LABEL.get(wk["job"]["t"], "")
                draw.append((wk["y"] * T + 1, lambda lab=lab: self.ui.text(
                    scr, lab, self.ui.f_xs, (255, 255, 255), (wk["x"] * T - cx, wk["y"] * T - cy - 56), "midbottom", True)))
        for kind, dx_, dy_, dw_, dh_ in s.world.decor:
            if x0 - 3 <= dx_ <= x1 and y0 - 3 <= dy_ <= y1:
                draw.append(((dy_ + dh_) * T - BASE_BIAS, lambda k=kind, a=dx_, b=dy_, c=dw_, d=dh_: sprites.draw_decor(
                    scr, k, a * T - cx, b * T - cy, c * T, d * T, season, t)))
        for f in s.world.fixed:
            sh = data.SHOPS[f["shop"]]
            draw.append(((f["y"] + f["h"]) * T - BASE_BIAS, lambda f=f, sh=sh: sprites.draw_shop_building(
                scr, sh, f["x"] * T - cx, f["y"] * T - cy, f["w"] * T, f["h"] * T, season, self.ui.f_xs)))
            npc = sh["npc"]
            est, (nx, ny), nd = routine.estado(f["shop"], s.clock.minutes)
            if est == routine.TRABALHANDO:
                draw.append(((ny) * T, lambda nx=nx, ny=ny, npc=npc: sprites.draw_person(
                    scr, nx * T - cx, ny * T - cy, (0, 1), False, t, npc)))
            elif est != routine.DORMINDO:                                    # a caminho da loja / de casa (a pé)
                face = (1 if nd[0] > 0 else -1, 0) if abs(nd[0]) >= abs(nd[1]) else (0, 1 if nd[1] > 0 else -1)
                draw.append((ny * T, lambda nx=nx, ny=ny, npc=npc, face=face: sprites.draw_person(
                    scr, nx * T - cx, ny * T - cy, face, True, t, npc)))
            else:
                dx, dy = f["door"]
                draw.append(((dy + 0.2) * T, lambda dx=dx, dy=dy: self.ui.text(
                    scr, "Fechado", self.ui.f_xs, (255, 220, 160), ((dx + .5) * T - cx, (dy - .2) * T - cy), "midbottom", True)))
        for hm in s.world.homes:
            if x0 - 4 <= hm["x"] <= x1 + 1 and y0 - 4 <= hm["y"] <= y1 + 1:
                sh_ = data.SHOPS[hm["shop"]]
                lit = routine.estado(hm["shop"], s.clock.minutes)[0] == routine.DORMINDO and s.clock.darkness() > .3 \
                    and s.clock.minutes < 900
                draw.append(((hm["y"] + hm["h"]) * T - BASE_BIAS, lambda hm=hm, sh_=sh_, lit=lit: sprites.draw_home(
                    scr, sh_, hm["x"] * T - cx, hm["y"] * T - cy, hm["w"] * T, hm["h"] * T, lit)))
        tool = {"k": self.tool_anim / 0.25, "cor": self.tool_col, "icon": self.tool_icon} if self.tool_anim > 0 else None
        if s.mounted:
            draw.append((s.py * T, lambda: sprites.draw_tractor(
                scr, s.px * T - cx, s.py * T - cy, s.facing, self.moving, t, self.trailer,
                lambda px_, py_: sprites.draw_person(scr, px_, py_, s.facing, False, t, PLAYER_COL, tool))))
        else:
            draw.append((s.py * T, lambda: sprites.draw_person(scr, s.px * T - cx, s.py * T - cy, s.facing, self.moving, t, PLAYER_COL, tool)))
        draw.sort(key=lambda d: d[0])
        for _, fn in draw:
            fn()

        if self.mode == "play":
            tx, ty, reach = self._aim_tile()
            pulse = .5 + .5 * math.sin(t * 7)
            col = (255, int(215 + 40 * pulse), 90) if reach else (230, 90, 80)
            pygame.draw.rect(scr, col, (tx * T - cx + 2, ty * T - cy + 2, T - 4, T - 4), 2, border_radius=4)
        for p in self.parts:
            pygame.draw.circle(scr, p[5], (int(p[0] - cx), int(p[1] - cy)), 3)
        if self.mode == "build":
            self._draw_build_overlay(cx, cy)

    def _draw_locked(self, cx, cy):
        s, scr = self.state, self.view
        for l in s.world.lands:
            if l["id"] in s.owned:
                continue
            x, y, w, h = l["rect"]
            r = pygame.Rect(x * T - cx, y * T - cy, w * T, h * T)
            if not r.colliderect((0, 0, self.vw, self.vh)):
                continue
            tint = pygame.Surface(r.size, pygame.SRCALPHA)
            tint.fill((30, 30, 30, 70))
            scr.blit(tint, r.topleft)
            sprites.rail(scr, r.x, r.y, r.right, r.y)
            sprites.rail(scr, r.x, r.bottom, r.right, r.bottom)
            sprites.rail(scr, r.x, r.y, r.x, r.bottom)
            sprites.rail(scr, r.right, r.y, r.right, r.bottom)
            c = r.center
            board = pygame.Rect(c[0] - 62, c[1] - 24, 124, 44)
            pygame.draw.rect(scr, (110, 76, 44), (c[0] - 40, c[1] + 14, 6, 22))
            pygame.draw.rect(scr, (110, 76, 44), (c[0] + 34, c[1] + 14, 6, 22))
            pygame.draw.rect(scr, (214, 178, 116), board, border_radius=5)
            pygame.draw.rect(scr, (110, 76, 44), board, 3, border_radius=5)
            self.ui.text(scr, "À VENDA", self.ui.f_s, (110, 50, 30), (c[0], board.y + 4), "midtop")
            self.ui.text(scr, f"${l['preco']}  (M: mapa)", self.ui.f_xs, (110, 50, 30), (c[0], board.y + 24), "midtop")

    def _draw_build_overlay(self, cx, cy):
        s, b, scr = self.state, self.build, self.view
        VW, VH = self.vw, self.vh
        if s.settings["grade"]:
            grid = pygame.Surface((VW, VH), pygame.SRCALPHA)
            for x in range(-(cx % T), VW, T):
                pygame.draw.line(grid, (255, 255, 255, 38), (x, 0), (x, VH))
            for y in range(-(cy % T), VH, T):
                pygame.draw.line(grid, (255, 255, 255, 38), (0, y), (VW, y))
            scr.blit(grid, (0, 0))
        modo = b["modo"]
        tx, ty = self._mouse_tile()
        if modo in ("mover", "guardar") and b["picked"] is None:
            inst = s.structs.at(tx, ty)
            if inst:
                sd = data.STRUCTS[inst["s"]]
                w, h = building.Structures.dims(sd, inst["rot"])
                col = (60, 220, 90, 90) if b["ok"] else (230, 60, 50, 90)
                ov = pygame.Surface((w * T, h * T), pygame.SRCALPHA)
                ov.fill(col)
                scr.blit(ov, (inst["x"] * T - cx, inst["y"] * T - cy))
            return
        sid = b["sid"] if modo == "colocar" else (s.structs.by_id[b["picked"]]["s"] if b["picked"] in s.structs.by_id else None)
        if not sid or modo == "guardar":
            return
        x, y = b["pos"]
        sd = data.STRUCTS[sid]
        w, h = building.Structures.dims(sd, b["rot"])
        spr = pygame.Surface((w * T, h * T), pygame.SRCALPHA)
        conn = (0, 0, 0, 0) if sd.get("conecta") else None
        sprites.draw_structure(spr, sid, None, 0, 0, w * T, h * T, s.clock.season, self.t, conn)
        spr.set_alpha(170)
        scr.blit(spr, (x * T - cx, y * T - cy))
        col = (60, 220, 90, 95) if b["ok"] else (230, 60, 50, 95)
        for fx, fy in building.Structures.footprint(sd, x, y, b["rot"]):
            ov = pygame.Surface((T, T), pygame.SRCALPHA)
            ov.fill(col)
            scr.blit(ov, (fx * T - cx, fy * T - cy))
        pygame.draw.rect(scr, (120, 255, 140) if b["ok"] else (255, 110, 100), (x * T - cx, y * T - cy, w * T, h * T), 2)

    def _lamp_glows(self, cx, cy):
        s = self.state
        out = []
        for inst in s.structs.by_id.values():
            if inst["s"] == "lampada":
                out.append((inst["x"] * T - cx + T // 2, inst["y"] * T - cy + 8))
            elif inst["s"] == "casa":
                out.append((inst["x"] * T - cx + 80, inst["y"] * T - cy + 100))
        for f in s.world.fixed:
            out.append((f["door"][0] * T - cx + T // 2, f["door"][1] * T - cy - 10))
        for kind, dx_, dy_, dw_, dh_ in s.world.decor:
            if kind == "poste":
                out.append((dx_ * T - cx + T // 2, dy_ * T - cy + 4))
        z = self.zoom        # os brilhos são desenhados na tela (já ampliada), então convertemos as posições
        return [(g[0] * z, g[1] * z) for g in out if -60 < g[0] * z < SW + 60 and -60 < g[1] * z < SH + 60]

    # ------------------------------------------------------------ desenho geral
    def draw(self):
        scr, ui = self.screen, self.ui
        ui.begin()
        if self._on_title():
            if self.mode == "slots":
                scr.blit(self.title_bg, (0, 0))
                ui.draw_slots(scr, self)
            elif self.mode == "settings":
                scr.blit(self.title_bg, (0, 0))
                ui.draw_settings(scr, self)
            else:
                ui.draw_title(scr, self)
            return
        s = self.state
        if self.in_house:
            self.draw_house_scene()
            self._draw_menus()
            return
        if self.in_mine:
            self.draw_mine_scene()
            self._draw_menus()
            return
        self.draw_world()
        if self.view is not self.screen:
            try:
                pygame.transform.scale(self.view, (SW, SH), self.screen)
            except (ValueError, TypeError):       # formatos de pixel diferentes: usa o caminho mais lento
                self.screen.blit(pygame.transform.scale(self.view, (SW, SH)), (0, 0))
        gfx.draw_weather(scr, s.weather, self.wps, self.flash)
        cx, cy = int(self.cam[0]), int(self.cam[1])
        gfx.draw_night(scr, self.night, s.clock.darkness(), self._lamp_glows(cx, cy))
        self._draw_menus()

    def draw_house_scene(self):
        scr, s = self.screen, self.state
        if self.room is None:
            self.room = pygame.Surface((house.ROOM_W, house.ROOM_H))
        dark = s.clock.darkness()
        t = self.t

        def player(surf):
            sprites.draw_person(surf, self.hx * T, self.hy * T, s.facing, self.moving, t, PLAYER_COL)
        player.sort_y = self.hy * T
        house.draw_room(self.room, t, dark, s.weather, player, papel=s.worker_novo)
        scr.fill((14, 10, 8))
        big = pygame.transform.scale(self.room, (house.ROOM_W * 2, house.ROOM_H * 2))
        oy = 40
        scr.blit(big, (0, oy))
        if dark > 0.01:
            glows = [(gx * 2, gy * 2 + oy) for gx, gy in house.glows()]
            gfx.draw_night(scr, self.night, dark * 0.7, glows)

    def _draw_menus(self):
        scr, ui, s = self.screen, self.ui, self.state
        ui.draw_hud(scr, self)
        if self.dev_info or self.dev_speed != 1 or self.dev_god or self.dev_noclip:
            ui.draw_dev_overlay(scr, self)
        m = self.mode
        if m == "quartinho":
            ui.draw_quartinho(scr, self)
        elif m == "banco":
            ui.draw_banco(scr, self)
        elif m == "cozinha":
            ui.draw_cozinha(scr, self)
        elif m == "barraca":
            ui.draw_barraca(scr, self)
        elif m == "quadro":
            ui.draw_quadro(scr, self)
        elif m == "ferreiro":
            ui.draw_ferreiro(scr, self)
        elif m == "guia":
            ui.draw_guia(scr, self)
        elif m == "mina_menu":
            ui.draw_mina_menu(scr, self)
        elif m == "tanque":
            ui.draw_tanque(scr, self)
        elif m == "build":
            ui.draw_build_panel(scr, self)
        elif m == "inv":
            ui.draw_inventory(scr, self)
        elif m == "shop":
            ui.draw_shop(scr, self)
        elif m == "animals":
            ui.draw_animals(scr, self)
        elif m == "map":
            ui.draw_map(scr, self)
        elif m == "pause":
            ui.draw_pause(scr, self)
        elif m == "racao":
            ui.draw_racao(scr, self)
        elif m == "forno":
            ui.draw_forno(scr, self)
        elif m == "relatorio":
            ui.draw_relatorio(scr, self)
        elif m == "dev":
            ui.draw_dev(scr, self)
        elif m == "slots":
            ui.draw_slots(scr, self)
        elif m == "settings":
            ui.draw_settings(scr, self)
        elif m == "confirm_sleep":
            ui.draw_confirm(scr, self, "Dormir até amanhã?", self.do_sleep)
        self.touch.draw(scr, m)
        if self.show_help and m in ("play", "casa"):
            ui.draw_help(scr, self.prefs)
        if self.fade > 0:
            self.black.set_alpha(int(255 * min(1.0, self.fade)))
            scr.blit(self.black, (0, 0))

    async def run_async(self):
        """Mesmo laço do run(), mas cedendo tempo ao navegador a cada quadro (necessário na versão web)."""
        import asyncio
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                self.handle(e)
            self.update(dt)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                self.handle(e)
            self.update(dt)
            self.draw()
            pygame.display.flip()

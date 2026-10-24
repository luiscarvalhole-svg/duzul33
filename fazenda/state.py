"""GameState: reúne mundo, inventário, fazenda, construções, animais, tempo e economia.

Nada aqui depende do pygame, então tudo pode ser testado sem abrir janela.
"""
from . import animals as an
from . import bank, data, fishing, forno, orchard, stall, worker
from .building import Structures
from .clock import Clock, season_of, weather_for
from .config import (DAY_MINUTES, GAME_MIN_PER_SEC, MAX_ENERGY, SAVE_VERSION, SKILLS, START_MONEY, WATER_CAPACITY, XP_LEVELS)
from .farming import Farm
from .inventory import Inventory
from .world import World


def level_for(xp):
    lvl = 0
    for i, t in enumerate(XP_LEVELS):
        if xp >= t:
            lvl = i
    return lvl


class GameState:
    def __init__(self, seed=1):
        self.seed = seed
        self.world = World(seed)
        self.clock = Clock()
        self.inv = Inventory()
        self.farm = Farm()
        self.structs = Structures()
        self.animals = []
        self.next_animal = 1
        self.money = START_MONEY
        self.energy = float(MAX_ENERGY)
        self.skills = {k: 0 for k in SKILLS}
        self.px, self.py = 44.5, 36.5
        self.facing = (0, 1)
        self.sel = 0
        self.owned = {"inicial"}
        self.shop_state = {}
        self.water = WATER_CAPACITY
        self.mine_best = 0
        self.settings = {"grade": True, "som": True, "murchar": True, "regador_lago": False, "torneira_ok": False}
        self.aim = None            # bloco apontado pelo mouse (None = usa o bloco à frente do jogador)
        self.weather = weather_for(0, seed)
        self.forecast = weather_for(1, seed)
        self.stats = {"colhidos": 0, "vendas": 0}
        self.mounted = False        # montado no trator (não é salvo)
        self.bank = 0              # saldo no banco da vila
        self.worker = None          # funcionário contratado (dict) ou None
        self.worker_hist = []       # relatórios dos últimos dias (mais novo no fim)
        self.worker_novo = False    # há um relatório novo sobre a mesa da casa
        self.net_ready = 0         # minuto absoluto em que a rede de pesca seca

    @classmethod
    def new(cls, seed=1):
        s = cls(seed)
        for it, n in (("enxada", 1), ("regador", 1), ("foice", 1), ("machado", 1), ("picareta", 1),
                      ("semente_cenoura", 10), ("semente_rabanete", 8), ("pao", 3), ("madeira", 20), ("pedra", 10)):
            s.inv.add(it, n)
        s.structs.add("casa", 42, 31)
        s.structs.add("torneira", 47, 34)
        s.settings["torneira_ok"] = True
        return s

    def water_cap(self):
        """Capacidade do regador: depende do melhor regador que você carrega."""
        cap = WATER_CAPACITY
        for sl in self.inv.slots:
            if sl:
                cap = max(cap, data.ITEMS[sl["i"]].get("capacidade", 0))
        return cap

    # ------------------------------------------------------------ habilidades
    def level(self, skill):
        return level_for(self.skills[skill])

    def add_xp(self, skill, n):
        before = self.level(skill)
        self.skills[skill] += n
        return self.level(skill) > before

    def meets(self, req):
        """req: {"agricultura": 2, ...}. Retorna (ok, lista de pendências)."""
        missing = [f"{k} nível {v}" for k, v in req.items() if self.level(k) < v]
        return not missing, missing

    # ------------------------------------------------------------ mapa e colisão
    def owned_tile(self, x, y):
        land = self.world.land_at(x, y)
        return land is not None and land["id"] in self.owned

    def blocked(self, x, y):
        w = self.world
        if w.static_blocked(x, y):
            return True
        land = w.land_at(x, y)
        if land is not None and land["id"] not in self.owned:
            return True
        return self.structs.blocks(x, y)

    def can_stand(self, px, py):
        for ox, oy in ((-0.28, -0.12), (0.28, -0.12), (-0.28, 0.2), (0.28, 0.2)):
            if self.blocked(int((px + ox) // 1), int((py + oy) // 1)):
                return False
        return True

    def target_tile(self):
        if self.aim is not None:
            return self.aim
        fx, fy = self.facing
        return int((self.px + fx * 0.9) // 1), int((self.py + fy * 0.9) // 1)

    def sprinkler_tiles(self):
        out = set()
        for inst in self.structs.by_id.values():
            r = data.STRUCTS[inst["s"]].get("irriga")
            if r:
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        out.add((inst["x"] + dx, inst["y"] + dy))
        return out

    # ------------------------------------------------------------ energia
    def spend_energy(self, n):
        if self.energy < n:
            return False
        self.energy -= n
        return True

    def eat(self, slot_idx):
        s = self.inv.slots[slot_idx]
        if not s or data.ITEMS[s["i"]]["kind"] != "food":
            return False
        if self.energy >= MAX_ENERGY:
            return False
        self.energy = min(MAX_ENERGY, self.energy + data.ITEMS[s["i"]]["energia"])
        self.inv.remove_from_slot(slot_idx, 1)
        return True

    # ------------------------------------------------------------ tempo
    def tick(self, dt):
        """Avança o relógio. Se passar da meia-noite, o jogador desmaia. Retorna o resumo do dia ou None."""
        self.clock.tick(dt)
        forno.update(self, dt * GAME_MIN_PER_SEC)
        if self.clock.minutes >= DAY_MINUTES:
            return self.end_day(forced=True)
        return None

    def end_day(self, forced=False):
        forno.update(self, max(0.0, DAY_MINUTES - self.clock.minutes))     # o forno segue aceso até o fim do dia
        relatorio = worker.work(self)
        raining = self.weather in ("chuva", "tempestade")
        next_season = season_of(self.clock.day + 1)
        crops = self.farm.end_day(raining, self.sprinkler_tiles(), next_season, self.settings.get("murchar", True))
        vend_itens, vend_total = stall.end_day(self)
        born = an.end_day(self)
        gordos = fishing.end_day(self)
        juros = bank.end_day(self)
        self.clock.next_day()
        frutas, arvores = orchard.end_day(self)
        self.weather = weather_for(self.clock.day, self.seed)
        self.forecast = weather_for(self.clock.day + 1, self.seed)
        # aspersores deixam a terra ao redor visivelmente molhada logo de manhã
        for pos in self.sprinkler_tiles():
            if pos in self.farm.soil:
                self.farm.soil[pos]["wet"] = True
        self.energy = MAX_ENERGY * (0.5 if forced else 1.0)
        self.water = self.water_cap()
        ready = sum(1 for a in self.animals if a["pronto"])
        return {"forced": forced, "crescidas": crops["grown"], "murchas": crops["withered"],
                "produtos": ready, "nascidos": born, "gordos": gordos, "funcionario": relatorio, "barraca": vend_total, "barraca_itens": vend_itens, "frutas": frutas, "arvores": arvores, "juros": juros, "clima": self.weather, "estacao": self.clock.season, "dia": self.clock.day}

    # ------------------------------------------------------------ terrenos
    def land_status(self, land_id):
        """Retorna (pode_comprar, motivos)."""
        land = self.world.land_by_id(land_id)
        if land is None:
            return False, ["Terreno inexistente."]
        if land_id in self.owned:
            return False, ["Você já possui este terreno."]
        _, missing = self.meets(land.get("req", {}))
        why = [f"Requer {m}" for m in missing]
        if self.clock.day < land.get("dia", 0):
            why.append(f"Disponível a partir do dia {land['dia'] + 1}")
        if self.money < land["preco"]:
            why.append(f"Faltam ${land['preco'] - self.money}")
        return not why, why

    def buy_land(self, land_id):
        ok, why = self.land_status(land_id)
        if not ok:
            return False, "; ".join(why)
        land = self.world.land_by_id(land_id)
        self.money -= land["preco"]
        self.owned.add(land_id)
        return True, f"{land['nome']} é sua!"

    # ------------------------------------------------------------ save / load
    def to_dict(self):
        return {
            "version": SAVE_VERSION, "seed": self.seed, "money": self.money, "energy": self.energy,
            "skills": dict(self.skills), "px": self.px, "py": self.py, "facing": list(self.facing),
            "sel": self.sel, "clock": self.clock.to_dict(), "weather": self.weather, "forecast": self.forecast,
            "inv": self.inv.to_list(), "farm": self.farm.to_dict(), "structs": self.structs.to_dict(),
            "animals": [dict(a) for a in self.animals], "next_animal": self.next_animal,
            "owned": sorted(self.owned), "objects": self.world.objects_to_list(),
            "shop_state": self.shop_state, "water": self.water, "settings": dict(self.settings),
            "stats": dict(self.stats), "bank": self.bank, "worker": self.worker, "worker_hist": [dict(h) for h in self.worker_hist], "worker_novo": self.worker_novo, "net_ready": self.net_ready, "mine_best": self.mine_best,
        }

    @classmethod
    def from_dict(cls, d):
        if d.get("version") != SAVE_VERSION:
            raise ValueError("Versão de save incompatível.")
        s = cls(int(d["seed"]))
        s.money, s.energy = int(d["money"]), float(d["energy"])
        s.skills = {k: int(d["skills"].get(k, 0)) for k in SKILLS}
        s.px, s.py = float(d["px"]), float(d["py"])
        s.facing = tuple(d.get("facing", (0, 1)))
        s.clock = Clock.from_dict(d["clock"])
        s.weather, s.forecast = d["weather"], d["forecast"]
        s.inv = Inventory.from_list(d["inv"])
        s.sel = int(d.get("sel", 0)) % 10
        s.farm = Farm.from_dict(d["farm"])
        s.structs = Structures.from_dict(d["structs"])
        s.animals = [dict(a) for a in d.get("animals", []) if a.get("t") in data.ANIMALS]
        s.next_animal = int(d.get("next_animal", len(s.animals) + 1))
        ids = {l["id"] for l in s.world.lands}
        s.owned = {o for o in d.get("owned", ["inicial"]) if o in ids} | {"inicial"}
        s.world.objects_from_list(d["objects"])
        s.shop_state = d.get("shop_state", {})
        s.water = int(d.get("water", WATER_CAPACITY))
        s.settings.update(d.get("settings", {}))
        s.stats.update(d.get("stats", {}))
        s.bank = int(d.get("bank", 0))
        w = d.get("worker")
        s.worker = worker.normalizar(w, s.clock.day)
        s.worker_hist = [h for h in d.get("worker_hist", []) if isinstance(h, dict)]
        s.worker_novo = bool(d.get("worker_novo", False))
        s.net_ready = d.get("net_ready", 0)
        s.mine_best = int(d.get("mine_best", 0))
        if not s.settings.get("torneira_ok"):          # save antigo: ganha uma torneira no inventário (uma vez só)
            s.settings["torneira_ok"] = True
            if not any(i["s"] == "torneira" for i in s.structs.by_id.values()):
                s.inv.add("torneira", 1)
        if not s.can_stand(s.px, s.py):             # segurança: nunca nascer dentro de um obstáculo
            s.px, s.py = 44.5, 36.5
        return s

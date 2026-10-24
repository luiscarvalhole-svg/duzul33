"""Geração procedural do mundo (determinística a partir de uma semente).

Regiões: montanhas ao norte, floresta a noroeste, lago e rio a oeste, praia e mar ao sul,
estrada, vila (lojas) a leste e a fazenda no centro, dividida em terrenos compráveis.
"""
import random

from . import data
from .config import WORLD_H, WORLD_W

GRASS, SAND, WATER, ROCK, ROAD, FOREST, PLAZA = range(7)
HP = {"tree": 5, "rock": 4, "bush": 2}

# probabilidades (arvore, pedra, arbusto) por tipo de terreno
_PROBS_TERRENO = {
    "campo": (0.012, 0.03, 0.02), "floresta": (0.30, 0.01, 0.06), "pasto": (0.01, 0.01, 0.05),
    "rochoso": (0.02, 0.18, 0.01), "agua": (0.04, 0.03, 0.03), "especial": (0.08, 0.06, 0.05),
}
_PROBS_GROUND = {
    ROCK: (0.0, 0.10, 0.0), FOREST: (0.28, 0.01, 0.05), GRASS: (0.02, 0.006, 0.012), SAND: (0.0, 0.01, 0.0),
}


def _noise(rng, n, scale):
    pts = [rng.random() for _ in range(n // scale + 3)]
    out = []
    for i in range(n):
        a, b, f = pts[i // scale], pts[i // scale + 1], (i % scale) / scale
        out.append(a + (b - a) * f)
    return out


# Vila: lojas ao norte e ao sul de uma praça de pedra com fonte; a avenida central desce até a rua principal.
PLAZA_RECTS = [(68, 33, 24, 6),        # praça (logo abaixo das portas das lojas do norte)
               (77, 39, 4, 5),         # avenida central entre as lojas do sul
               (70, 43, 23, 1)]        # calçada em frente às lojas do sul

# (tipo, x, y, largura, altura, bloqueia)
PRACA = [("fonte", 77, 35, 3, 3, True),
         ("banco", 73, 36, 2, 1, True), ("banco", 82, 36, 2, 1, True),
         ("poste", 69, 34, 1, 1, True), ("poste", 88, 34, 1, 1, True), ("poste", 75, 38, 1, 1, True), ("poste", 81, 38, 1, 1, True),
         ("arvore", 68, 37, 1, 1, True), ("arvore", 89, 37, 1, 1, True),
         ("canteiro", 71, 38, 2, 1, True), ("canteiro", 85, 38, 2, 1, True),
         ("quadro", 86, 35, 2, 1, True),
         ("mina", 47, 9, 6, 4, True)]       # entrada da mina, na montanha


class World:
    def __init__(self, seed=1):
        self.seed = seed
        self.w, self.h = WORLD_W, WORLD_H
        self.ground = [[GRASS] * self.w for _ in range(self.h)]
        self.objects = {}            # (x,y) -> {"k": "tree"|"rock"|"bush", "hp": int, "v": int}
        self.fixed = []              # lojas da vila
        self.fixed_tiles = set()
        self.homes = []              # casas dos lojistas: {"shop", "x", "y", "w", "h"}
        self.decor = []              # praça da vila: (tipo, x, y, w, h)
        self.lands = [dict(l) for l in data.LANDS]
        self.land_grid = [[0] * self.w for _ in range(self.h)]   # 0 = sem terreno; senão índice+1
        self._generate()

    # ------------------------------------------------------------ consultas
    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def land_at(self, x, y):
        if not self.in_bounds(x, y):
            return None
        i = self.land_grid[y][x]
        return self.lands[i - 1] if i else None

    def land_by_id(self, land_id):
        for l in self.lands:
            if l["id"] == land_id:
                return l
        return None

    def static_blocked(self, x, y):
        """Bloqueios que não dependem do estado do jogador (água, objetos, lojas)."""
        if not self.in_bounds(x, y):
            return True
        return (self.ground[y][x] == WATER or (x, y) in self.objects or (x, y) in self.fixed_tiles)

    # ------------------------------------------------------------ geração
    def _fill(self, rect, tile, only=None):
        x, y, w, h = rect
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if only is None or self.ground[yy][xx] in only:
                    self.ground[yy][xx] = tile

    def _generate(self):
        rng = random.Random(self.seed)
        w, h = self.w, self.h
        for i, l in enumerate(self.lands, 1):
            x, y, lw, lh = l["rect"]
            for yy in range(y, y + lh):
                for xx in range(x, x + lw):
                    self.land_grid[yy][xx] = i

        nx = _noise(rng, w, 6)                       # montanhas ao norte
        for x in range(w):
            for y in range(int(10 + nx[x] * 5)):
                self.ground[y][x] = ROCK
        ny = _noise(rng, w, 5)                       # praia e mar ao sul
        for x in range(w):
            s0 = int(61 + ny[x] * 3)
            for y in range(s0, h):
                self.ground[y][x] = SAND if y < s0 + 4 else WATER
        cx, cy, rx, ry = 14, 40, 9, 7                # lago a oeste
        for y in range(h):
            for x in range(w):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1:
                    self.ground[y][x] = WATER
                elif d <= 1.35 and self.ground[y][x] == GRASS:
                    self.ground[y][x] = SAND
        for y in range(46, h):                       # rio até o mar
            for x in (23, 24):
                self.ground[y][x] = WATER
            for x in (22, 25):
                if self.ground[y][x] in (GRASS, FOREST):
                    self.ground[y][x] = SAND
        self._fill((2, 13, 34, 18), FOREST, only=(GRASS,))    # floresta noroeste

        for l in self.lands:                          # aparência de cada terreno
            x, y, lw, lh = l["rect"]
            t = l["tipo"]
            if t == "floresta":
                self._fill(l["rect"], FOREST)
            elif t == "rochoso":
                self._fill(l["rect"], ROCK)
            elif t == "agua":
                self._fill(l["rect"], GRASS)
                pcx, pcy = x + lw * 0.35, y + lh * 0.5
                for yy in range(y, y + lh):
                    for xx in range(x, x + lw):
                        d = ((xx + 0.5 - pcx) / 3.6) ** 2 + ((yy + 0.5 - pcy) / 2.6) ** 2
                        if d <= 1:
                            self.ground[yy][xx] = WATER
                        elif d <= 1.5:
                            self.ground[yy][xx] = SAND
            else:
                self._fill(l["rect"], GRASS)

        self._fill((24, 44, 69, 2), ROAD)             # estrada
        for r in PLAZA_RECTS:                         # praça e calçadas da vila
            self._fill(r, PLAZA)

        for sid, sh in data.SHOPS.items():            # lojas
            x, y, sw, sh_h = sh["local"]
            self.fixed.append({"id": sid, "shop": sid, "x": x, "y": y, "w": sw, "h": sh_h,
                               "door": (x + sw // 2, y + sh_h)})
            for yy in range(y, y + sh_h):
                for xx in range(x, x + sw):
                    self.fixed_tiles.add((xx, yy))

        for sid, sh in data.SHOPS.items():            # casas dos lojistas (a rotina deles está em routine.py)
            c = sh.get("casa")
            if c:
                hx, hy, hw, hh = c["rect"]
                self.homes.append({"shop": sid, "x": hx, "y": hy, "w": hw, "h": hh})
                for yy in range(hy, hy + hh):
                    for xx in range(hx, hx + hw):
                        self.fixed_tiles.add((xx, yy))

        for kind, x, y, dw, dh, solid in PRACA:       # praça: fonte, bancos e canteiros
            self.decor.append((kind, x, y, dw, dh))
            if solid:
                for yy in range(y, y + dh):
                    for xx in range(x, x + dw):
                        self.fixed_tiles.add((xx, yy))

        self._scatter_objects(rng)
        for hm in self.homes:                          # limpa árvores/pedras em volta das casas e dos caminhos dos lojistas
            for yy in range(hm["y"] - 1, hm["y"] + hm["h"] + 2):
                for xx in range(hm["x"] - 1, hm["x"] + hm["w"] + 2):
                    self.objects.pop((xx, yy), None)
        for yy, x0, x1 in ((28, 68, 93), (46, 71, 92)):
            for xx in range(x0, x1):
                self.objects.pop((xx, yy), None)

    def _scatter_objects(self, rng):
        for y in range(self.h):
            for x in range(self.w):
                g = self.ground[y][x]
                if g in (WATER, ROAD, PLAZA) or (x, y) in self.fixed_tiles:
                    continue
                if any(f["x"] - 1 <= x <= f["x"] + f["w"] and f["y"] + f["h"] <= y <= f["y"] + f["h"] + 2 for f in self.fixed):
                    continue                                   # a frente das lojas fica livre
                if 45 <= x <= 54 and 8 <= y <= 16:                    # entrada da mina
                    continue
                if 42 <= x <= 48 and 30 <= y <= 43:          # corredor livre casa -> estrada
                    continue
                lid = self.land_grid[y][x]
                land = self.lands[lid - 1] if lid else None
                if land:
                    if land["id"] == "inicial":
                        if 40 <= x <= 52 and 30 <= y <= 41:
                            continue
                        probs = (0.012, 0.02, 0.01)
                    else:
                        probs = _PROBS_TERRENO[land["tipo"]]
                else:
                    probs = _PROBS_GROUND.get(g, (0, 0, 0))
                t, r_, b = probs
                roll = rng.random()
                kind = "tree" if roll < t else "rock" if roll < t + r_ else "bush" if roll < t + r_ + b else None
                if kind:
                    self.objects[(x, y)] = {"k": kind, "hp": HP[kind], "v": rng.randint(0, 3)}

    # ------------------------------------------------------------ serialização dos objetos
    def objects_to_list(self):
        return [[x, y, o["k"], o["hp"], o["v"]] for (x, y), o in sorted(self.objects.items())]

    def objects_from_list(self, lst):
        self.objects = {(int(x), int(y)): {"k": k, "hp": int(hp), "v": int(v)} for x, y, k, hp, v in lst}

"""Solo e plantações. Crescimento por dias: só cresce se a terra foi regada (ou choveu/aspersor)."""
import random

from . import data


def crop_stage(crop, prog):
    r = prog / crop["dias"]
    return 0 if r < 0.25 else 1 if r < 0.5 else 2 if r < 1 else 3


class Farm:
    def __init__(self):
        self.soil = {}     # (x,y) -> {"wet": bool, "fert": None|"adubo"|"rapido", "crop": None|{"id","prog"}}

    def till(self, x, y):
        if (x, y) in self.soil:
            return False
        self.soil[(x, y)] = {"wet": False, "fert": None, "crop": None}
        return True

    def untill(self, x, y):
        s = self.soil.get((x, y))
        if s is None or s["crop"]:
            return False
        del self.soil[(x, y)]
        return True

    def water(self, x, y):
        s = self.soil.get((x, y))
        if s is None:
            return False
        s["wet"] = True
        return True

    def plant(self, x, y, crop_id, season):
        s = self.soil.get((x, y))
        if s is None:
            return False, "Ara a terra primeiro."
        if s["crop"]:
            return False, "Já existe uma planta aqui."
        c = data.CROPS[crop_id]
        if season not in c["estacoes"]:
            return False, f"{c['nome']} não cresce nesta estação."
        s["crop"] = {"id": crop_id, "prog": 0.0}
        return True, ""

    def fertilize(self, x, y, kind):
        s = self.soil.get((x, y))
        if s is None:
            return False, "Ara a terra primeiro."
        if s["fert"]:
            return False, "Este solo já está adubado."
        s["fert"] = kind
        return True, ""

    def stage(self, x, y):
        s = self.soil.get((x, y))
        if not s or not s["crop"]:
            return None
        return crop_stage(data.CROPS[s["crop"]["id"]], s["crop"]["prog"])

    def ripe(self, x, y):
        return self.stage(x, y) == 3

    @staticmethod
    def _quality(fert, level, rng):
        gold = 0.04 + 0.03 * level + (0.12 if fert == "adubo" else 0.0)
        silver = 0.12 + 0.04 * level + (0.18 if fert == "adubo" else 0.0)
        r = rng.random()
        return 2 if r < gold else 1 if r < gold + silver else 0

    def harvest(self, x, y, level=0, rng=random):
        s = self.soil.get((x, y))
        if not s or not s["crop"]:
            return None
        c = data.CROPS[s["crop"]["id"]]
        if s["crop"]["prog"] < c["dias"]:
            return None
        q = self._quality(s["fert"], level, rng)
        regrow = c.get("regrow")
        if regrow:
            s["crop"]["prog"] = max(0.0, c["dias"] - regrow)
        else:
            s["crop"] = None
            s["fert"] = None
        return {"item": c["id"], "qty": 1, "q": q, "xp": c["xp"], "regrow": bool(regrow)}

    def end_day(self, raining, extra_wet, next_season, wither=True):
        grown = withered = 0
        for pos, s in list(self.soil.items()):
            cr = s["crop"]
            if cr:
                c = data.CROPS[cr["id"]]
                if s["wet"] or raining or pos in extra_wet:
                    cr["prog"] = min(float(c["dias"]), cr["prog"] + (1.25 if s["fert"] == "rapido" else 1.0))
                    grown += 1
                if wither and next_season not in c["estacoes"]:
                    s["crop"], s["fert"] = None, None
                    withered += 1
            s["wet"] = False
        return {"grown": grown, "withered": withered}

    def to_dict(self):
        return {f"{x},{y}": {"wet": s["wet"], "fert": s["fert"],
                             "crop": dict(s["crop"]) if s["crop"] else None}
                for (x, y), s in self.soil.items()}

    @classmethod
    def from_dict(cls, d):
        f = cls()
        for k, s in d.items():
            x, y = (int(v) for v in k.split(","))
            crop = s.get("crop")
            if crop and crop.get("id") not in data.CROPS:
                crop = None
            f.soil[(x, y)] = {"wet": bool(s.get("wet")), "fert": s.get("fert"),
                              "crop": {"id": crop["id"], "prog": float(crop["prog"])} if crop else None}
        return f

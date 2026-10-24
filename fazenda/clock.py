"""Tempo do jogo: hora, dia, estação, ano e clima."""
import random

from .config import DAY_MINUTES, DAYS_PER_SEASON, GAME_MIN_PER_SEC, SEASONS

_TABELA = {
    "primavera": [("sol", 0.62), ("chuva", 0.30), ("tempestade", 0.08)],
    "verao":     [("sol", 0.68), ("chuva", 0.14), ("tempestade", 0.18)],
    "outono":    [("sol", 0.58), ("chuva", 0.32), ("tempestade", 0.10)],
    "inverno":   [("sol", 0.50), ("neve", 0.50)],
}


def season_of(day):
    return SEASONS[(day // DAYS_PER_SEASON) % 4]


def weather_for(day, seed):
    """Clima de um dia: determinístico (mesma semente + dia = mesmo clima)."""
    if day == 0:
        return "sol"
    rng = random.Random(seed * 100003 + day * 7919 + 13)
    r, acc = rng.random(), 0.0
    for nome, p in _TABELA[season_of(day)]:
        acc += p
        if r < acc:
            return nome
    return "sol"


class Clock:
    def __init__(self, day=0, minutes=0.0):
        self.day = day            # dias desde o começo (0 = primeiro dia)
        self.minutes = minutes    # minutos desde as 06:00

    @property
    def season(self):
        return season_of(self.day)

    @property
    def day_of_season(self):
        return self.day % DAYS_PER_SEASON + 1

    @property
    def year(self):
        return self.day // (DAYS_PER_SEASON * 4) + 1

    def tick(self, dt):
        self.minutes += dt * GAME_MIN_PER_SEC

    @property
    def hour(self):
        return 6 + int(self.minutes // 60)

    def day_over(self):
        return self.minutes >= DAY_MINUTES

    def next_day(self):
        self.day += 1
        self.minutes = 0.0

    def hhmm(self):
        total = 360 + int(self.minutes)
        return f"{(total // 60) % 24:02d}:{(total % 60) // 10 * 10:02d}"

    def darkness(self):
        """0 = dia claro, 1 = noite escura."""
        m = self.minutes
        if m < 30:
            return 0.35 * (1 - m / 30)
        if m < 660:
            return 0.0
        if m < 840:
            return 0.75 * (m - 660) / 180
        return 0.75

    def to_dict(self):
        return {"day": self.day, "minutes": self.minutes}

    @classmethod
    def from_dict(cls, d):
        return cls(int(d["day"]), float(d["minutes"]))

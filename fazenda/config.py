"""Constantes globais do jogo."""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
# Como .exe (PyInstaller) os saves ficam numa pasta "saves" ao lado do jogo, não na pasta temporária.
SAVE_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else BASE_DIR, "saves")
SAVE_FILE = os.path.join(SAVE_DIR, "slot1.json")
SAVE_SLOTS = 3                # quantidade de slots de salvamento (slot1.json, slot2.json, ...)

TILE = 32
WORLD_W, WORLD_H = 96, 72
SCREEN_W, SCREEN_H = 1024, 720
FPS = 60

DAY_MINUTES = 1080            # 06:00 -> 24:00
GAME_MIN_PER_SEC = 4.0        # um dia dura ~270 segundos reais
DAYS_PER_SEASON = 28
SEASONS = ["primavera", "verao", "outono", "inverno"]
SEASON_LABEL = {"primavera": "Primavera", "verao": "Verão", "outono": "Outono", "inverno": "Inverno"}
WEATHER_LABEL = {"sol": "Ensolarado", "chuva": "Chuva", "tempestade": "Tempestade", "neve": "Neve"}

INV_SIZE = 36
HOTBAR = 10
MAX_ENERGY = 100
START_MONEY = 600
SAVE_VERSION = 1

SKILLS = ["agricultura", "pecuaria", "mineracao", "pesca", "coleta"]
SKILL_LABEL = {"agricultura": "Agricultura", "pecuaria": "Pecuária", "mineracao": "Mineração",
               "pesca": "Pesca", "coleta": "Coleta"}
XP_LEVELS = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200, 4000]   # nivel 0..10

QUALITY_MULT = [1.0, 1.25, 1.5]
QUALITY_NAME = ["Normal", "Prata", "Ouro"]

PLAYER_SPEED = 4.4            # blocos por segundo
WATER_CAPACITY = 40

REACH = 2.6                   # alcance (em blocos) para usar ferramentas com o mouse
ZOOM_MIN, ZOOM_MAX, ZOOM_STEP = 1.0, 2.0, 0.25

#!/usr/bin/env python3
"""Fazenda RPG - ponto de entrada.  Uso: python main.py   (controles de toque: python main.py --touch)
Na versão web (pygbag) este mesmo arquivo roda no navegador. Se algo der errado ao carregar, o erro aparece na tela."""
import asyncio
import sys
import traceback

import pygame


def _tela(texto, cor=(255, 255, 255), fundo=(30, 24, 20)):
    """Mostra linhas de texto na tela (mensagens de carregamento e erros)."""
    scr = pygame.display.get_surface()
    scr.fill(fundo)
    fonte = pygame.font.Font(None, 26)
    y = 20
    for ln in texto:
        for i in range(0, max(1, len(ln)), 95):                       # quebra linhas longas
            scr.blit(fonte.render(ln[i:i + 95], True, cor), (20, y))
            y += 24
    pygame.display.flip()


async def main():
    pygame.init()
    pygame.display.set_mode((1024, 720))
    pygame.display.set_caption("Fazenda RPG")
    _tela(["Fazenda RPG", "", "Carregando o jogo..."])
    await asyncio.sleep(0)
    try:
        from fazenda.game import Game
        _tela(["Fazenda RPG", "", "Montando o mundo e os sons (pode levar alguns segundos)..."])
        await asyncio.sleep(0)
        jogo = Game()
        await jogo.run_async()
    except BaseException:                                              # mostra o erro na tela para podermos corrigir
        erro = traceback.format_exc()
        print(erro)
        linhas = ["ERRO NO JOGO - tire um print desta tela e envie:", ""] + erro.splitlines()[-22:]
        while True:
            _tela(linhas, (255, 190, 170), (50, 20, 20))
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())

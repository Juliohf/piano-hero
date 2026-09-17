# Moonlight Rhythm

Jogo de ritmo 2D em Python/Pygame.

## Rodar
```
pip install pygame
python main.py
```

## Gerar o executavel (Windows)
```
pip install pygame pyinstaller
pyinstaller --noconfirm --onefile --windowed --name MoonlightRhythm --add-data "assets;assets" main.py
```
Resultado em `dist\MoonlightRhythm.exe`.

## Controles
- Setas (esquerda, baixo, cima, direita): acertar as setas
- ENTER: comecar / jogar de novo
- P: pausar
- ESC: sair / voltar ao menu

Vitoria: terminar a musica com a barra de PRECISAO acima de zero.
Derrota: a barra de PRECISAO chegar a zero.

## Imagens
A pasta `assets/img/` aceita estes arquivos (todos opcionais):
- `menu_bg.png` (900x640)
- `background.png` (900x640)
- `arrow_left.png`, `arrow_down.png`, `arrow_up.png`, `arrow_right.png` (PNG quadrado com transparencia)

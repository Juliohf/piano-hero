# Moonlight Rhythm

Demo de um jogo de **ritmo 2D** feito em Python com **Pygame**. As setas
(`←  ↓  ↑  →`) descem no compasso do **1º movimento da Sonata ao Luar**
(Beethoven) e você precisa acertar cada uma no momento em que ela cruza a
linha de julgamento.

Atende a todos os requisitos do demo: tem **menu** (com os controles escritos
na própria tela), **controle do jogador**, **desafio**, **condição de vitória**
e **condição de derrota**. Não é jogo de console — abre em janela gráfica 2D.

---

## Como jogar

| Tecla            | Ação                              |
|------------------|-----------------------------------|
| `←  ↓  ↑  →`     | acertar as setas no tempo certo   |
| `ENTER`          | começar / jogar de novo           |
| `P`              | pausar / continuar                |
| `ESC`            | sair / voltar ao menu             |

- **Vitória:** sobreviver até o fim da música com a barra de **PRECISÃO** acima de 0.
- **Derrota:** errar setas demais até a barra de **PRECISÃO** zerar.

Acertos no tempo exato valem **PERFEITO**; um pouco fora, **BOM**; deixar passar, **ERRO**.

---

## Rodando pelo VSCode (sem compilar)

1. Tenha o **Python 3.10+** instalado.
2. Abra a pasta do projeto no VSCode.
3. No terminal:
   ```
   pip install pygame
   python main.py
   ```
   (No Windows também dá pra dar duplo-clique em **`run.bat`**.)

---

## Gerando o executável do Windows (.exe)

No Windows, com o projeto aberto no VSCode:

1. Dê duplo-clique em **`build.bat`** (ou rode no terminal).
2. Ele instala o PyInstaller e compila tudo.
3. O executável final fica em **`dist\MoonlightRhythm.exe`** — os assets já
   ficam embutidos dentro do próprio `.exe`.

O comando que o `build.bat` executa, caso queira rodar na mão:
```
pyinstaller --noconfirm --onefile --windowed --name MoonlightRhythm --add-data "assets;assets" main.py
```
> Dica: se quiser ver mensagens de erro durante o desenvolvimento, troque
> `--windowed` por `--console`.

---

## Estrutura do projeto

```
moonlight_rhythm/
├── main.py                 # o jogo (menu, gameplay, telas de vitória/derrota)
├── assets/
│   ├── music.wav           # 1º minuto da sonata, renderizado a partir do MIDI
│   ├── chart.json          # a "grade" de setas (tempo + coluna de cada uma)
│   ├── hit.wav             # som de acerto
│   └── miss.wav            # som de erro
├── tools/
│   ├── generate_assets.py  # regenera music.wav + chart.json a partir do MIDI
│   └── moonlight.mid       # MIDI de origem (1º movimento)
├── build.bat               # compila o .exe (Windows)
├── run.bat                 # roda o jogo direto (Windows)
└── requirements.txt
```

### Como o áudio e as setas ficam sincronizados
O áudio (`music.wav`) **e** a chart (`chart.json`) são gerados a partir das
**mesmas notas** do MIDI (`tools/generate_assets.py`). Como os dois saem da
mesma fonte de tempo, as setas caem exatamente junto com o som — sem
desalinhamento. Para regerar os assets:
```
pip install numpy mido
python tools/generate_assets.py
```

---

## Sobre os assets e licença
- A **composição** da Sonata ao Luar é **domínio público** (Beethoven, 1801).
- O `music.wav` foi **renderizado por síntese** a partir de um arquivo MIDI
  (apenas dados de nota, não uma gravação), então não há direitos de intérprete
  ou gravadora envolvidos.
- Os sons de acerto/erro e toda a parte gráfica (setas, fundo noturno, lua,
  estrelas) são **gerados pelo próprio código** — nenhuma imagem ou trilha de
  terceiros foi incluída.

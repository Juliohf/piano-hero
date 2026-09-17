import json
import math
import os
import sys

import pygame


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


ASSET_DIR = resource_path("assets")
IMG_DIR = os.path.join(ASSET_DIR, "img")

WIDTH, HEIGHT = 900, 640
FPS = 120

LANES = 4
LANE_KEYS = [pygame.K_LEFT, pygame.K_DOWN, pygame.K_UP, pygame.K_RIGHT]
LANE_DIRS = ["left", "down", "up", "right"]
LANE_COLORS = [
    (236, 110, 173),
    (104, 198, 255),
    (122, 226, 150),
    (245, 206, 110),
]

PLAYFIELD_W = 460
LANE_W = PLAYFIELD_W // LANES
FIELD_X = (WIDTH - PLAYFIELD_W) // 2
JUDGE_Y = HEIGHT - 110
SPAWN_Y = -40
ARROW_SIZE = 34
ARROW_PX = 74

APPROACH = 1.8
LEAD_IN = 2.0

PERFECT_WINDOW = 0.055
GOOD_WINDOW = 0.13

HP_START = 100.0
HP_PERFECT = +1.1
HP_GOOD = +0.55
HP_MISS = -8.0

SCORE_PERFECT = 100
SCORE_GOOD = 50

MENU_OVERLAY = True

BG_TOP = (10, 14, 34)
BG_BOTTOM = (3, 4, 12)
WHITE = (240, 244, 255)
DIM = (150, 160, 190)
MOON = (235, 238, 220)


def rotate_point(x, y, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (x * c - y * s, x * s + y * c)


_ARROW_UP = [(0, -1), (0.85, -0.05), (0.38, -0.05),
             (0.38, 0.9), (-0.38, 0.9), (-0.38, -0.05), (-0.85, -0.05)]
_DIR_ANGLE = {"up": 0, "right": 90, "down": 180, "left": 270}


def arrow_points(cx, cy, size, direction):
    ang = _DIR_ANGLE[direction]
    pts = []
    for x, y in _ARROW_UP:
        rx, ry = rotate_point(x * size, y * size, ang)
        pts.append((cx + rx, cy + ry))
    return pts


def draw_poly_arrow(surf, cx, cy, size, direction, color, outline=False):
    pts = arrow_points(cx, cy, size, direction)
    if outline:
        pygame.draw.polygon(surf, color, pts, width=3)
    else:
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, (255, 255, 255), pts, width=2)


def lane_center_x(lane):
    return FIELD_X + lane * LANE_W + LANE_W // 2


def load_image(name, size=None):
    path = os.path.join(IMG_DIR, name)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.smoothscale(img, size)
            return img
        except Exception:
            return None
    return None


def make_night_sky():
    import random
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        col = [int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)]
        pygame.draw.line(bg, col, (0, y), (WIDTH, y))
    rnd = random.Random(7)
    for _ in range(140):
        x = rnd.randint(0, WIDTH)
        y = rnd.randint(0, HEIGHT - 120)
        r = rnd.choice([1, 1, 1, 2])
        b = rnd.randint(120, 230)
        pygame.draw.circle(bg, (b, b, min(255, b + 20)), (x, y), r)
    mx, my = WIDTH - 130, 110
    glow = pygame.Surface((260, 260), pygame.SRCALPHA)
    for rr in range(120, 0, -1):
        a = int(60 * (1 - rr / 120))
        pygame.draw.circle(glow, (220, 225, 200, a), (130, 130), rr)
    bg.blit(glow, (mx - 130, my - 130))
    pygame.draw.circle(bg, MOON, (mx, my), 60)
    pygame.draw.circle(bg, (218, 222, 205), (mx + 18, my - 12), 12)
    pygame.draw.circle(bg, (218, 222, 205), (mx - 22, my + 16), 9)
    pygame.draw.circle(bg, (218, 222, 205), (mx + 6, my + 26), 7)
    return bg


class Game:
    STATE_MENU = "menu"
    STATE_PLAY = "play"
    STATE_WIN = "win"
    STATE_OVER = "over"

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Moonlight Rhythm")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.night_sky = make_night_sky()
        self.img_menu = load_image("menu_bg.png", (WIDTH, HEIGHT))
        self.img_bg = load_image("background.png", (WIDTH, HEIGHT))
        self.arrow_imgs = {}
        self.receptor_imgs = {}
        for d in LANE_DIRS:
            img = load_image("arrow_%s.png" % d, (ARROW_PX, ARROW_PX))
            self.arrow_imgs[d] = img
            if img is not None:
                rec = img.copy()
                rec.set_alpha(120)
                self.receptor_imgs[d] = rec
            else:
                self.receptor_imgs[d] = None

        self.font_xl = pygame.font.Font(None, 78)
        self.font_lg = pygame.font.Font(None, 46)
        self.font_md = pygame.font.Font(None, 30)
        self.font_sm = pygame.font.Font(None, 24)

        try:
            self.snd_hit = pygame.mixer.Sound(os.path.join(ASSET_DIR, "hit.wav"))
            self.snd_miss = pygame.mixer.Sound(os.path.join(ASSET_DIR, "miss.wav"))
            self.snd_hit.set_volume(0.4)
            self.snd_miss.set_volume(0.5)
        except Exception:
            self.snd_hit = self.snd_miss = None
        self.music_path = os.path.join(ASSET_DIR, "music.wav")

        with open(os.path.join(ASSET_DIR, "chart.json"), encoding="utf-8") as f:
            self.chart = json.load(f)
        self.song_title = self.chart.get("title", "")
        self.duration = float(self.chart.get("duration", 60))

        self.state = self.STATE_MENU
        self.flash = [0.0] * LANES
        self._pause_start = 0

    def note_arrow(self, lane, cx, cy):
        d = LANE_DIRS[lane]
        img = self.arrow_imgs.get(d)
        if img is not None:
            self.screen.blit(img, (cx - ARROW_PX // 2, cy - ARROW_PX // 2))
        else:
            draw_poly_arrow(self.screen, cx, cy, ARROW_SIZE, d, LANE_COLORS[lane])

    def receptor_arrow(self, lane, cx, cy):
        d = LANE_DIRS[lane]
        rec = self.receptor_imgs.get(d)
        if rec is not None:
            self.screen.blit(rec, (cx - ARROW_PX // 2, cy - ARROW_PX // 2))
        else:
            draw_poly_arrow(self.screen, cx, cy, ARROW_SIZE, d, LANE_COLORS[lane],
                            outline=True)

    def menu_arrow(self, lane, cx, cy):
        d = LANE_DIRS[lane]
        img = self.arrow_imgs.get(d)
        if img is not None:
            small = pygame.transform.smoothscale(img, (52, 52))
            self.screen.blit(small, (cx - 26, cy - 26))
        else:
            draw_poly_arrow(self.screen, cx, cy, 26, d, LANE_COLORS[lane], outline=True)

    def start_run(self):
        self.notes = [{"t": n["t"], "lane": n["lane"], "judged": False}
                      for n in self.chart["notes"]]
        self.hp = HP_START
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.count_perfect = 0
        self.count_good = 0
        self.count_miss = 0
        self.popups = []
        self.start_ticks = pygame.time.get_ticks()
        self.music_started = False
        self.paused = False
        self.pause_offset = 0
        self.state = self.STATE_PLAY

    def song_time(self):
        ms = pygame.time.get_ticks() - self.start_ticks - self.pause_offset
        return ms / 1000.0 - LEAD_IN

    def add_popup(self, lane, text, color):
        self.popups.append({"x": lane_center_x(lane), "y": JUDGE_Y - 40,
                            "text": text, "color": color, "life": 0.6})

    def judge_key(self, lane):
        t = self.song_time()
        self.flash[lane] = 0.18
        best = None
        best_dt = GOOD_WINDOW + 1
        for n in self.notes:
            if n["judged"] or n["lane"] != lane:
                continue
            dt = abs(n["t"] - t)
            if dt <= GOOD_WINDOW and dt < best_dt:
                best, best_dt = n, dt
        if best is None:
            return
        best["judged"] = True
        if best_dt <= PERFECT_WINDOW:
            self.count_perfect += 1
            self.combo += 1
            self.score += SCORE_PERFECT + self.combo
            self.hp = min(100.0, self.hp + HP_PERFECT)
            self.add_popup(lane, "PERFEITO", (255, 240, 150))
        else:
            self.count_good += 1
            self.combo += 1
            self.score += SCORE_GOOD + self.combo // 2
            self.hp = min(100.0, self.hp + HP_GOOD)
            self.add_popup(lane, "BOM", (160, 230, 255))
        self.max_combo = max(self.max_combo, self.combo)
        if self.snd_hit:
            self.snd_hit.play()

    def update_play(self, dt):
        if self.paused:
            return
        t = self.song_time()
        if not self.music_started and t >= 0:
            try:
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.set_volume(0.85)
                pygame.mixer.music.play()
            except Exception:
                pass
            self.music_started = True
        for n in self.notes:
            if not n["judged"] and t - n["t"] > GOOD_WINDOW:
                n["judged"] = True
                self.count_miss += 1
                self.combo = 0
                self.hp += HP_MISS
                self.add_popup(n["lane"], "ERRO", (255, 120, 120))
                if self.snd_miss:
                    self.snd_miss.play()
        for p in self.popups:
            p["y"] -= 30 * dt
            p["life"] -= dt
        self.popups = [p for p in self.popups if p["life"] > 0]
        for i in range(LANES):
            self.flash[i] = max(0.0, self.flash[i] - dt)
        if self.hp <= 0:
            self.hp = 0
            pygame.mixer.music.stop()
            self.state = self.STATE_OVER
            return
        if (t > self.duration + 0.5 or all(n["judged"] for n in self.notes)) and t > 1:
            pygame.mixer.music.stop()
            self.state = self.STATE_WIN

    def gameplay_background(self):
        if self.img_bg is not None:
            self.screen.blit(self.img_bg, (0, 0))
        else:
            self.screen.blit(self.night_sky, (0, 0))

    def draw_playfield(self):
        s = self.screen
        field = pygame.Surface((PLAYFIELD_W, HEIGHT), pygame.SRCALPHA)
        field.fill((255, 255, 255, 14))
        s.blit(field, (FIELD_X, 0))
        for i in range(LANES + 1):
            x = FIELD_X + i * LANE_W
            pygame.draw.line(s, (255, 255, 255), (x, 0), (x, HEIGHT), 1)
        pygame.draw.line(s, (255, 255, 255), (FIELD_X, JUDGE_Y),
                         (FIELD_X + PLAYFIELD_W, JUDGE_Y), 2)
        for lane in range(LANES):
            cx = lane_center_x(lane)
            if self.flash[lane] > 0:
                glow = int(120 * (self.flash[lane] / 0.18))
                gs = pygame.Surface((LANE_W, 80), pygame.SRCALPHA)
                pygame.draw.circle(gs, (*LANE_COLORS[lane], glow),
                                   (LANE_W // 2, 40), 36)
                s.blit(gs, (cx - LANE_W // 2, JUDGE_Y - 40))
            self.receptor_arrow(lane, cx, JUDGE_Y)

    def draw_notes(self):
        t = self.song_time()
        for n in self.notes:
            if n["judged"]:
                continue
            appear = n["t"] - APPROACH
            if t < appear:
                continue
            frac = (t - appear) / APPROACH
            y = SPAWN_Y + frac * (JUDGE_Y - SPAWN_Y)
            if y > HEIGHT + 40:
                continue
            self.note_arrow(n["lane"], lane_center_x(n["lane"]), int(y))

    def draw_hud(self):
        s = self.screen
        bx, by, bw, bh = 30, 24, 320, 22
        bg_bar = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg_bar.fill((255, 255, 255, 35))
        s.blit(bg_bar, (bx, by))
        frac = self.hp / 100.0
        if self.hp > 55:
            c = (120, 220, 150)
        elif self.hp > 25:
            c = (240, 210, 120)
        else:
            c = (240, 110, 110)
        if frac > 0:
            pygame.draw.rect(s, c, (bx, by, int(bw * frac), bh), border_radius=8)
        pygame.draw.rect(s, WHITE, (bx, by, bw, bh), width=2, border_radius=8)
        s.blit(self.font_sm.render("PRECISAO", True, WHITE), (bx, by + 28))
        scrim = pygame.Surface((230, 92), pygame.SRCALPHA)
        for i in range(92):
            a = int(120 * (1 - i / 92))
            pygame.draw.line(scrim, (0, 0, 0, a), (0, i), (230, i))
        s.blit(scrim, (WIDTH - 230, 0))
        sc = self.font_lg.render(str(self.score), True, WHITE)
        s.blit(sc, (WIDTH - 30 - sc.get_width(), 22))
        if self.combo >= 3:
            cb = self.font_md.render("combo x%d" % self.combo, True, (255, 230, 160))
            s.blit(cb, (WIDTH - 30 - cb.get_width(), 66))
        for p in self.popups:
            a = max(0, min(255, int(255 * (p["life"] / 0.6))))
            surf = self.font_md.render(p["text"], True, p["color"])
            surf.set_alpha(a)
            s.blit(surf, (p["x"] - surf.get_width() // 2, int(p["y"])))
        if self.paused:
            self.center_text("PAUSADO", self.font_xl, WHITE, HEIGHT // 2 - 30)
            self.center_text("P para continuar  -  ESC para o menu",
                             self.font_md, DIM, HEIGHT // 2 + 30)

    def center_text(self, text, font, color, y):
        surf = font.render(text, True, color)
        self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))

    def draw_menu(self):
        s = self.screen
        if self.img_menu is not None:
            s.blit(self.img_menu, (0, 0))
        else:
            s.blit(self.night_sky, (0, 0))
        if not MENU_OVERLAY:
            pulse = 180 + int(60 * math.sin(pygame.time.get_ticks() / 300))
            self.center_text("Pressione ENTER para comecar",
                             self.font_lg, (pulse, pulse, 255), 576)
            return
        self.center_text("MOONLIGHT  RHYTHM", self.font_xl, WHITE, 92)
        self.center_text(self.song_title, self.font_sm, DIM, 166)
        for i in range(LANES):
            self.menu_arrow(i, WIDTH // 2 - 90 + i * 60, 226)
        box = pygame.Surface((520, 196), pygame.SRCALPHA)
        box.fill((255, 255, 255, 18))
        pygame.draw.rect(box, (255, 255, 255), box.get_rect(), 2, border_radius=14)
        s.blit(box, (WIDTH // 2 - 260, 284))
        lines = [
            ("<-  v  ^  ->", "acertar as setas no tempo certo"),
            ("ENTER", "comecar"),
            ("P", "pausar / continuar"),
            ("ESC", "sair / voltar ao menu"),
        ]
        y = 306
        for key, desc in lines:
            ks = self.font_md.render(key, True, (255, 230, 160))
            s.blit(ks, (WIDTH // 2 - 232, y))
            ds = self.font_md.render("-  " + desc, True, WHITE)
            s.blit(ds, (WIDTH // 2 - 66, y))
            y += 40
        self.center_text("Vitoria: sobreviva ate o fim da musica",
                         self.font_sm, DIM, 510)
        self.center_text("Derrota: deixe a barra de PRECISAO zerar",
                         self.font_sm, DIM, 534)
        pulse = 180 + int(60 * math.sin(pygame.time.get_ticks() / 300))
        self.center_text("Pressione ENTER para comecar",
                         self.font_lg, (pulse, pulse, 255), 576)

    def draw_end(self, won):
        s = self.screen
        self.gameplay_background()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        s.blit(overlay, (0, 0))
        if won:
            self.center_text("VOCE VENCEU!", self.font_xl, (180, 240, 190), 120)
        else:
            self.center_text("GAME OVER", self.font_xl, (240, 140, 140), 120)
        total = self.count_perfect + self.count_good + self.count_miss
        acc = (self.count_perfect + self.count_good) / total * 100 if total else 0
        rows = [
            "Pontuacao: %d" % self.score,
            "Combo maximo: %d" % self.max_combo,
            "Perfeito: %d   Bom: %d   Erro: %d" % (
                self.count_perfect, self.count_good, self.count_miss),
            "Precisao: %.1f%%" % acc,
        ]
        y = 230
        for r in rows:
            self.center_text(r, self.font_md, WHITE, y)
            y += 44
        self.center_text("ENTER - jogar de novo      ESC - menu",
                         self.font_md, (255, 230, 160), 470)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    running = self.handle_key(e.key)
            if self.state == self.STATE_PLAY:
                self.update_play(dt)
                self.gameplay_background()
                self.draw_playfield()
                self.draw_notes()
                self.draw_hud()
                self.center_text(self.song_title, self.font_sm, DIM, HEIGHT - 26)
            elif self.state == self.STATE_MENU:
                self.draw_menu()
            elif self.state == self.STATE_WIN:
                self.draw_end(True)
            elif self.state == self.STATE_OVER:
                self.draw_end(False)
            pygame.display.flip()
        pygame.quit()

    def handle_key(self, key):
        if self.state == self.STATE_MENU:
            if key == pygame.K_RETURN:
                self.start_run()
            elif key == pygame.K_ESCAPE:
                return False
        elif self.state == self.STATE_PLAY:
            if key == pygame.K_ESCAPE:
                pygame.mixer.music.stop()
                self.state = self.STATE_MENU
            elif key == pygame.K_p:
                self.toggle_pause()
            elif not self.paused and key in LANE_KEYS:
                self.judge_key(LANE_KEYS.index(key))
        elif self.state in (self.STATE_WIN, self.STATE_OVER):
            if key == pygame.K_RETURN:
                self.start_run()
            elif key == pygame.K_ESCAPE:
                self.state = self.STATE_MENU
        return True

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            pygame.mixer.music.pause()
            self._pause_start = pygame.time.get_ticks()
        else:
            pygame.mixer.music.unpause()
            self.pause_offset += pygame.time.get_ticks() - self._pause_start


if __name__ == "__main__":
    Game().run()

#!/usr/bin/env python3
import pygame, random, os

pygame.init()
info = pygame.display.Info()
W, H = info.current_w, info.current_h
COLS, ROWS, SIZE = 14, 20, H // 22
GW, PANEL = COLS * SIZE, 300
SX, SY = (W - (GW + PANEL)) // 2, (H - (ROWS * SIZE)) // 2

BLACK, BG, TEXT, COLORS = (0, 0, 0), (15, 15, 20), (240, 240, 250), [
    (0, 255, 255), (0, 0, 255), (255, 165, 0), (255, 255, 0), (0, 255, 0), (128, 0, 128), (255, 0, 0)
]

# Настройки уровней сложности (интервал падения в кадрах)
DIFFICULTIES = [
    ("Лёгкий", 35),
    ("Средний", 22),
    ("Сложный", 10)
]

RAW_SHAPES = [[4,5,6,7], [1,5,9,10], [1,5,9,8], [1,2,5,6], [5,6,8,9], [1,4,5,6], [4,5,9,10]]
SHAPES = []
for s in RAW_SHAPES:
    rot = [s]
    for _ in range(3):
        prev = rot[-1]
        rot.append([(3 - (idx % 4)) * 4 + (idx // 4) for idx in prev])
    SHAPES.append(rot)

class Figure:
    def __init__(self):
        self.type = random.randint(0, 6)
        self.color, self.rotation, self.x, self.y = COLORS[self.type], 0, COLS // 2 - 2, 0
    def matrix(self): return SHAPES[self.type][self.rotation]
    def rotate(self): self.rotation = (self.rotation + 1) % 4

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.SCALED)
        self.clock = pygame.time.Clock()
        
        # Настройка автоповтора клавиш для плавного управления вбок
        pygame.key.set_repeat(200, 50)
        
        self.f48 = pygame.font.SysFont("Arial", 48, 1)
        self.f32 = pygame.font.SysFont("Arial", 32, 1)
        self.f24 = pygame.font.SysFont("Arial", 24, 1)
        self.f18 = pygame.font.SysFont("Arial", 18)

        # Сохранение рекорда в ~/.config/tetris/
        config_dir = os.path.expanduser("~/.config/tetris")
        os.makedirs(config_dir, exist_ok=True)
        self.file = os.path.join(config_dir, "highscore.txt")
        self.record = int(open(self.file).read().strip()) if os.path.exists(self.file) else 0

        # Игровые состояния: "MENU", "PLAYING", "PAUSED", "GAME_OVER"
        self.state = "MENU"
        self.diff_index = 1  # По умолчанию «Средний»
        
        self.reset()

    def reset(self):
        self.grid = [[0]*COLS for _ in range(ROWS)]
        self.fig, self.score = Figure(), 0

    def collide(self, dx=0, dy=0, mat=None):
        m = mat if mat else self.fig.matrix()
        for idx in m:
            bx, by = (idx % 4) + self.fig.x + dx, (idx // 4) + self.fig.y + dy
            if bx < 0 or bx >= COLS or by >= ROWS or (by >= 0 and self.grid[by][bx]):
                return True
        return False

    def freeze(self):
        for idx in self.fig.matrix():
            self.grid[(idx // 4) + self.fig.y][(idx % 4) + self.fig.x] = self.fig.color
        cleared = 0
        for r in range(ROWS):
            if 0 not in self.grid[r]:
                cleared += 1
                del self.grid[r]
                self.grid.insert(0, [0]*COLS)
        self.score += (cleared ** 2) * 100
        if self.score > self.record:
            self.record = self.score
            try:
                with open(self.file, "w") as f: f.write(str(self.record))
            except Exception: pass

        self.fig = Figure()
        if self.collide():
            self.state = "GAME_OVER"

    def step(self):
        if not self.collide(dy=1):
            self.fig.y += 1
        else:
            self.freeze()

    def draw_menu(self):
        self.screen.fill(BG)
        title = self.f48.render("Т Е Т Р И С", 1, (0, 255, 255))
        self.screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 200))

        m = pygame.mouse.get_pos()
        
        # Кнопка "Играть"
        self.btn_play = pygame.Rect(W // 2 - 130, H // 2 - 80, 260, 50)
        p_col = (40, 200, 40) if self.btn_play.collidepoint(m) else (30, 140, 30)
        pygame.draw.rect(self.screen, p_col, self.btn_play, border_radius=8)
        txt_play = self.f24.render("Играть", 1, TEXT)
        self.screen.blit(txt_play, (self.btn_play.centerx - txt_play.get_width() // 2, self.btn_play.centery - 12))

        # Кнопка "Сложность"
        self.btn_diff = pygame.Rect(W // 2 - 130, H // 2, 260, 50)
        d_col = (70, 130, 240) if self.btn_diff.collidepoint(m) else (40, 80, 180)
        pygame.draw.rect(self.screen, d_col, self.btn_diff, border_radius=8)
        diff_name = DIFFICULTIES[self.diff_index][0]
        txt_diff = self.f24.render(f"Сложность: {diff_name}", 1, TEXT)
        self.screen.blit(txt_diff, (self.btn_diff.centerx - txt_diff.get_width() // 2, self.btn_diff.centery - 12))

        # Кнопка "Выход"
        self.btn_exit = pygame.Rect(W // 2 - 130, H // 2 + 80, 260, 50)
        e_col = (200, 40, 40) if self.btn_exit.collidepoint(m) else (140, 30, 30)
        pygame.draw.rect(self.screen, e_col, self.btn_exit, border_radius=8)
        txt_exit = self.f24.render("Выход", 1, TEXT)
        self.screen.blit(txt_exit, (self.btn_exit.centerx - txt_exit.get_width() // 2, self.btn_exit.centery - 12))

    def draw_game(self):
        self.screen.fill(BG)
        # Стакан
        pygame.draw.rect(self.screen, BLACK, [SX, SY, GW, ROWS * SIZE])
        for r in range(ROWS):
            for c in range(COLS):
                pygame.draw.rect(self.screen, (45,45,55), [SX + c*SIZE, SY + r*SIZE, SIZE, SIZE], 1)
                if self.grid[r][c]:
                    pygame.draw.rect(self.screen, self.grid[r][c], [SX + c*SIZE+1, SY + r*SIZE+1, SIZE-2, SIZE-2])
        
        # Падающая фигура
        if self.state in ["PLAYING", "PAUSED"]:
            for idx in self.fig.matrix():
                pygame.draw.rect(self.screen, self.fig.color, [SX + ((idx % 4) + self.fig.x)*SIZE+1, SY + ((idx // 4) + self.fig.y)*SIZE+1, SIZE-2, SIZE-2])
        
        # Правая панель
        PX = SX + GW
        pygame.draw.line(self.screen, (100,100,100), (PX, SY), (PX, SY + ROWS * SIZE), 3)
        self.screen.blit(self.f32.render("ОЧКИ:", 1, TEXT), (PX + 40, SY + 20))
        self.screen.blit(self.f32.render(str(self.score), 1, (0,255,0)), (PX + 40, SY + 60))
        self.screen.blit(self.f32.render("РЕКОРД:", 1, TEXT), (PX + 40, SY + 110))
        self.screen.blit(self.f32.render(str(self.record), 1, (255,215,0)), (PX + 40, SY + 150))

        m = pygame.mouse.get_pos()
        
        # Кнопка «Пауза» во время игры
        self.btn_pause = pygame.Rect(PX + 40, SY + 200, 220, 35)
        p_col = (200, 200, 40) if self.btn_pause.collidepoint(m) else (140, 140, 30)
        pygame.draw.rect(self.screen, p_col, self.btn_pause, border_radius=6)
        txt_pause = self.f18.render("Пауза (P / Space)", 1, BLACK if self.btn_pause.collidepoint(m) else TEXT)
        self.screen.blit(txt_pause, (self.btn_pause.centerx - txt_pause.get_width() // 2, self.btn_pause.centery - 9))

        # Кнопка «Главное меню» во время игры
        self.btn_main_menu = pygame.Rect(PX + 40, SY + 245, 220, 35)
        m_col = (70, 130, 240) if self.btn_main_menu.collidepoint(m) else (40, 80, 180)
        pygame.draw.rect(self.screen, m_col, self.btn_main_menu, border_radius=6)
        txt_menu = self.f18.render("Главное меню", 1, TEXT)
        self.screen.blit(txt_menu, (self.btn_main_menu.centerx - txt_menu.get_width() // 2, self.btn_main_menu.centery - 9))

        # Кнопка «Начать заново» во время игры
        self.btn_restart = pygame.Rect(PX + 40, SY + 290, 220, 35)
        r_col = (220, 140, 30) if self.btn_restart.collidepoint(m) else (160, 90, 20)
        pygame.draw.rect(self.screen, r_col, self.btn_restart, border_radius=6)
        txt_rst = self.f18.render("Начать заново", 1, TEXT)
        self.screen.blit(txt_rst, (self.btn_restart.centerx - txt_rst.get_width() // 2, self.btn_restart.centery - 9))

        # Подсказки
        self.screen.blit(self.f32.render("УПРАВЛЕНИЕ:", 1, TEXT), (PX + 40, SY + 340))
        hints = [
            ("Esc — Выйти в меню", (255,100,100)),
            ("P / Space — Пауза", (255,255,100)),
            ("Вверх — Поворот фигуры", (150,150,160)),
            ("Влево / Вправо — Движение", (150,150,160)),
            ("Вниз — Ускорить падение", (150,150,160))
        ]
        for i, (text, col) in enumerate(hints):
            self.screen.blit(self.f18.render(text, 1, col), (PX + 40, SY + 380 + i*25))

        # Оверлей PAUSED
        if self.state == "PAUSED":
            overlay = pygame.Surface((GW, ROWS * SIZE), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (SX, SY))
            txt = self.f48.render("ПАУЗА", 1, (255, 255, 0))
            self.screen.blit(txt, (SX + GW // 2 - txt.get_width() // 2, SY + 150))
            
            self.btn_resume = pygame.Rect(SX + GW // 2 - 110, SY + 250, 220, 50)
            pygame.draw.rect(self.screen, (40,200,40) if self.btn_resume.collidepoint(m) else (30,140,30), self.btn_resume, border_radius=7)
            t_res = self.f24.render("Продолжить", 1, TEXT)
            self.screen.blit(t_res, (self.btn_resume.centerx - t_res.get_width() // 2, self.btn_resume.centery - 12))

        # Оверлей Game Over
        if self.state == "GAME_OVER":
            overlay = pygame.Surface((GW, ROWS * SIZE), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (SX, SY))
            txt = self.f48.render("ИГРА ОКОНЧЕНА", 1, (255,50,50))
            self.screen.blit(txt, (SX + GW // 2 - txt.get_width() // 2, SY + 120))
            
            self.go_retry = pygame.Rect(SX + GW // 2 - 110, SY + 220, 220, 45)
            self.go_menu = pygame.Rect(SX + GW // 2 - 110, SY + 280, 220, 45)
            self.go_exit = pygame.Rect(SX + GW // 2 - 110, SY + 340, 220, 45)
            
            pygame.draw.rect(self.screen, (40,200,40) if self.go_retry.collidepoint(m) else (30,140,30), self.go_retry, border_radius=7)
            pygame.draw.rect(self.screen, (70,130,240) if self.go_menu.collidepoint(m) else (40,80,180), self.go_menu, border_radius=7)
            pygame.draw.rect(self.screen, (200,40,40) if self.go_exit.collidepoint(m) else (140,30,30), self.go_exit, border_radius=7)
            
            t_retry = self.f24.render("Заново", 1, TEXT)
            t_menu = self.f24.render("Главное меню", 1, TEXT)
            t_exit = self.f24.render("Выйти из игры", 1, TEXT)
            
            self.screen.blit(t_retry, (self.go_retry.centerx - t_retry.get_width() // 2, self.go_retry.centery - 12))
            self.screen.blit(t_menu, (self.go_menu.centerx - t_menu.get_width() // 2, self.go_menu.centery - 12))
            self.screen.blit(t_exit, (self.go_exit.centerx - t_exit.get_width() // 2, self.go_exit.centery - 12))

    def play(self):
        cnt, loop = 0, True
        while loop:
            self.clock.tick(60)

            if self.state == "PLAYING":
                cnt += 1
                speed = DIFFICULTIES[self.diff_index][1]
                drop_speed = 2 if pygame.key.get_pressed()[pygame.K_DOWN] else speed
                if cnt >= drop_speed:
                    cnt = 0
                    self.step()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    loop = False

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.state in ["PLAYING", "PAUSED", "GAME_OVER"]:
                            self.state = "MENU"
                        elif self.state == "MENU":
                            loop = False
                    
                    # Горячая клавиша для паузы (P или Пробел)
                    if e.key in [pygame.K_p, pygame.K_SPACE]:
                        if self.state == "PLAYING":
                            self.state = "PAUSED"
                        elif self.state == "PAUSED":
                            self.state = "PLAYING"

                # Обработка кликов мыши
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.state == "MENU":
                        if self.btn_play.collidepoint(e.pos):
                            self.reset()
                            self.state = "PLAYING"
                        elif self.btn_diff.collidepoint(e.pos):
                            self.diff_index = (self.diff_index + 1) % len(DIFFICULTIES)
                        elif self.btn_exit.collidepoint(e.pos):
                            loop = False

                    elif self.state in ["PLAYING", "PAUSED"]:
                        if self.btn_pause.collidepoint(e.pos):
                            self.state = "PLAYING" if self.state == "PAUSED" else "PAUSED"
                        elif self.btn_main_menu.collidepoint(e.pos):
                            self.state = "MENU"
                        elif self.btn_restart.collidepoint(e.pos):
                            self.reset()
                            self.state = "PLAYING"
                        elif self.state == "PAUSED" and self.btn_resume.collidepoint(e.pos):
                            self.state = "PLAYING"

                    elif self.state == "GAME_OVER":
                        if self.go_retry.collidepoint(e.pos):
                            self.reset()
                            self.state = "PLAYING"
                        elif self.go_menu.collidepoint(e.pos):
                            self.state = "MENU"
                        elif self.go_exit.collidepoint(e.pos):
                            loop = False

                # Клавиатура во время игры
                if self.state == "PLAYING" and e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_LEFT and not self.collide(dx=-1):
                        self.fig.x -= 1
                    if e.key == pygame.K_RIGHT and not self.collide(dx=1):
                        self.fig.x += 1
                    if e.key == pygame.K_UP:
                        self.fig.rotate()
                        if self.collide():
                            for _ in range(3): self.fig.rotate()

            # Отрисовка
            if self.state == "MENU":
                self.draw_menu()
            else:
                self.draw_game()

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    Tetris().play()

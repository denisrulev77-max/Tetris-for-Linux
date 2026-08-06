import pygame
import random
import json
import os

pygame.init()
pygame.font.init()

# Размеры экрана
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Увеличенная арена тетриса (14x22)
GRID_WIDTH = 14
GRID_HEIGHT = 22
BLOCK_SIZE = (SCREEN_HEIGHT - 100) // GRID_HEIGHT
SIDEBAR_WIDTH = 300

BOARD_WIDTH = GRID_WIDTH * BLOCK_SIZE
TOTAL_GAME_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
START_X = (SCREEN_WIDTH - TOTAL_GAME_WIDTH) // 2
START_Y = (SCREEN_HEIGHT - (GRID_HEIGHT * BLOCK_SIZE)) // 2

# Оттенки фона и графики из версии 2.0
BACKGROUND = (18, 18, 24)    # Приятный тёмно-серый/графитовый фон всего экрана
BOARD_BG = (0, 0, 0)         # Глубокий чёрный фон самого игрового стакана
GRID_LINE = (35, 35, 40)     # Четкая, но ненавязчивая сетка
BORDER_COLOR = (70, 70, 80)  # Граница стакана

WHITE = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)

# Цвета очков и рекорда
BLUE_SCORE = (52, 152, 219)   # Синий цвет для очков
GOLD_RECORD = (241, 196, 15)  # Золотой цвет для рекорда

# Цвета кнопок
BLUE_TITLE = (52, 152, 219)
GREEN_BTN = (46, 204, 113)
DARK_GREEN_BTN = (39, 174, 96)
BLUE_BTN = (41, 128, 185)
RED_BTN = (231, 76, 60)
ORANGE_BTN = (230, 126, 34)

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 0], [0, 1, 1]]
]

SHAPE_COLORS = [
    (0, 240, 240),
    (240, 240, 0),
    (160, 0, 240),
    (240, 160, 0),
    (0, 0, 240),
    (0, 240, 0),
    (240, 0, 0)
]

DIFFICULTIES = {
    "Легкий": 700,
    "Нормальный": 450,
    "Хард": 180,
    "Супермен": 35
}

SAVE_FILE = "tetris_save.json"

class Piece:
    def __init__(self, x, y, shape_idx=None):
        self.x = x
        self.y = y
        self.shape_idx = shape_idx if shape_idx is not None else random.randint(0, len(SHAPES) - 1)
        self.shape = SHAPES[self.shape_idx]
        self.color = SHAPE_COLORS[self.shape_idx]

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.title_font = pygame.font.SysFont("arial", 60, bold=True)
        
        self.difficulty_keys = list(DIFFICULTIES.keys())
        self.difficulty_idx = 1
        
        self.game_btns = {}
        self.game_over_btns = {}
        self.btns = {}
        
        # Задержка для ускоренного падения при зажатии клавиш ВНИЗ / S (уменьшена до 20 мс)
        self.soft_drop_delay = 20
        self.last_soft_drop_time = 0
        
        self.high_score = 0
        self.reset_game()
        self.state = "MENU"

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.high_score = 0
        self.lines = 0
        self.level = 1
        start_spawn_x = (GRID_WIDTH // 2) - 1
        self.current_piece = Piece(start_spawn_x, 0)
        self.next_piece = Piece(start_spawn_x, 0)
        self.last_fall_time = pygame.time.get_ticks()

    def save_game(self):
        data = {
            "grid": self.grid,
            "score": self.score,
            "high_score": self.high_score,
            "lines": self.lines,
            "level": self.level,
            "difficulty_idx": self.difficulty_idx,
            "current_piece": {
                "x": self.current_piece.x,
                "y": self.current_piece.y,
                "shape_idx": self.current_piece.shape_idx,
                "shape": self.current_piece.shape
            },
            "next_piece": {
                "shape_idx": self.next_piece.shape_idx
            }
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            self.grid = data["grid"]
            self.score = data["score"]
            self.high_score = data.get("high_score", self.score)
            self.lines = data["lines"]
            self.level = data["level"]
            self.difficulty_idx = data.get("difficulty_idx", 1)
            
            cp = data["current_piece"]
            self.current_piece = Piece(cp["x"], cp["y"], cp["shape_idx"])
            self.current_piece.shape = cp["shape"]
            
            np = data["next_piece"]
            start_spawn_x = (GRID_WIDTH // 2) - 1
            self.next_piece = Piece(start_spawn_x, 0, np["shape_idx"])
            return True
        except Exception:
            return False

    def delete_save(self):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)

    def valid_move(self, piece, offset_x=0, offset_y=0):
        for r, row in enumerate(piece.shape):
            for c, val in enumerate(row):
                if val:
                    new_x = piece.x + c + offset_x
                    new_y = piece.y + r + offset_y
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True

    def lock_piece(self):
        for r, row in enumerate(self.current_piece.shape):
            for c, val in enumerate(row):
                if val:
                    y = self.current_piece.y + r
                    x = self.current_piece.x + c
                    if y >= 0:
                        self.grid[y][x] = self.current_piece.color
        self.clear_lines()
        self.current_piece = self.next_piece
        start_spawn_x = (GRID_WIDTH // 2) - 1
        self.next_piece = Piece(start_spawn_x, 0)
        
        if not self.valid_move(self.current_piece):
            self.state = "GAME_OVER"
            self.delete_save()

    def clear_lines(self):
        full_rows = [i for i, row in enumerate(self.grid) if all(row)]
        lines_cleared = len(full_rows)
        if lines_cleared > 0:
            for row_idx in full_rows:
                del self.grid[row_idx]
                self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])
            self.lines += lines_cleared
            self.score += (lines_cleared ** 2) * 100
            if self.score > self.high_score:
                self.high_score = self.score
            self.level = (self.lines // 10) + 1

    def move_down(self):
        if self.valid_move(self.current_piece, offset_y=1):
            self.current_piece.y += 1
        else:
            self.lock_piece()

    def draw_button(self, text, x, y, w, h, bg_color):
        pygame.draw.rect(self.screen, bg_color, (x, y, w, h), border_radius=6)
        txt = self.font.render(text, True, WHITE)
        self.screen.blit(txt, (x + (w - txt.get_width()) // 2, y + (h - txt.get_height()) // 2))
        return pygame.Rect(x, y, w, h)

    def draw(self):
        self.screen.fill(BACKGROUND)
        
        if self.state != "MENU":
            pygame.draw.rect(self.screen, BOARD_BG, (START_X, START_Y, BOARD_WIDTH, GRID_HEIGHT * BLOCK_SIZE))

            for r in range(GRID_HEIGHT):
                for c in range(GRID_WIDTH):
                    color = self.grid[r][c]
                    rx = START_X + c * BLOCK_SIZE
                    ry = START_Y + r * BLOCK_SIZE
                    rect = (rx, ry, BLOCK_SIZE, BLOCK_SIZE)
                    if color:
                        pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, GRID_LINE, rect, 1)

            pygame.draw.rect(self.screen, BORDER_COLOR, (START_X, START_Y, BOARD_WIDTH, GRID_HEIGHT * BLOCK_SIZE), 2)

            if self.current_piece and self.state != "GAME_OVER":
                for r, row in enumerate(self.current_piece.shape):
                    for c, val in enumerate(row):
                        if val:
                            px = START_X + (self.current_piece.x + c) * BLOCK_SIZE
                            py = START_Y + (self.current_piece.y + r) * BLOCK_SIZE
                            pygame.draw.rect(self.screen, self.current_piece.color, (px, py, BLOCK_SIZE, BLOCK_SIZE))
                            pygame.draw.rect(self.screen, GRID_LINE, (px, py, BLOCK_SIZE, BLOCK_SIZE), 1)

            sidebar_x = START_X + BOARD_WIDTH + 30
            info_y = START_Y
            
            diff_name = self.difficulty_keys[self.difficulty_idx]
            texts = [
                (f"Очки: {self.score}", BLUE_SCORE),
                (f"Рекорд: {self.high_score}", GOLD_RECORD),
                (f"Линии: {self.lines}", WHITE),
                (f"Уровень: {self.level}", WHITE),
                (f"Сложность: {diff_name}", WHITE)
            ]
            for txt, t_color in texts:
                t_surf = self.font.render(txt, True, t_color)
                self.screen.blit(t_surf, (sidebar_x, info_y))
                info_y += 35

            lbl = self.font.render("Следующая:", True, LIGHT_GRAY)
            self.screen.blit(lbl, (sidebar_x, info_y + 5))
            info_y += 35
            
            if self.next_piece:
                for r, row in enumerate(self.next_piece.shape):
                    for c, val in enumerate(row):
                        if val:
                            nx = sidebar_x + c * BLOCK_SIZE
                            ny = info_y + r * BLOCK_SIZE
                            pygame.draw.rect(self.screen, self.next_piece.color, (nx, ny, BLOCK_SIZE, BLOCK_SIZE))
                            pygame.draw.rect(self.screen, GRID_LINE, (nx, ny, BLOCK_SIZE, BLOCK_SIZE), 1)

            btn_y = info_y + 110
            pause_label = "Продолжить" if self.state == "PAUSED" else "Пауза"
            
            self.game_btns["PAUSE"] = self.draw_button(pause_label, sidebar_x, btn_y, 200, 40, BLUE_BTN)
            self.game_btns["RESTART"] = self.draw_button("Заново", sidebar_x, btn_y + 50, 200, 40, ORANGE_BTN)
            self.game_btns["MENU"] = self.draw_button("Главное меню", sidebar_x, btn_y + 100, 200, 40, RED_BTN)

            help_y = btn_y + 160
            helps = [
                ("Управление:", LIGHT_GRAY),
                ("← / A | → / D : Влево / Вправо", LIGHT_GRAY),
                ("↑ / W : Поворот", LIGHT_GRAY),
                ("↓ / S (зажать) : Ускорить падение", LIGHT_GRAY),
                ("ESC : Главное меню / Выход", RED_BTN)
            ]
            for h_txt, h_color in helps:
                h_surf = self.small_font.render(h_txt, True, h_color)
                self.screen.blit(h_surf, (sidebar_x, help_y))
                help_y += 22

        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PAUSED":
            self.draw_overlay("ПАУЗА", "Игра приостановлена")
        elif self.state == "GAME_OVER":
            self.draw_game_over()

        pygame.display.flip()

    def draw_menu(self):
        title = self.title_font.render("ТЕТРИС", True, BLUE_TITLE)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, SCREEN_HEIGHT // 4))

        has_save = os.path.exists(SAVE_FILE)
        btn_w, btn_h = 300, 50
        start_y = SCREEN_HEIGHT // 2 - 50
        
        self.btns = {}
        
        if has_save:
            self.btns["CONTINUE"] = self.draw_button("Продолжить", (SCREEN_WIDTH - btn_w)//2, start_y, btn_w, btn_h, DARK_GREEN_BTN)
            start_y += 65
            
        self.btns["NEW_GAME"] = self.draw_button("Новая игра", (SCREEN_WIDTH - btn_w)//2, start_y, btn_w, btn_h, GREEN_BTN)
        start_y += 65
        
        diff_text = f"Сложность: {self.difficulty_keys[self.difficulty_idx]}"
        self.btns["DIFF"] = self.draw_button(diff_text, (SCREEN_WIDTH - btn_w)//2, start_y, btn_w, btn_h, BLUE_BTN)
        start_y += 65
        
        self.btns["EXIT"] = self.draw_button("Выход", (SCREEN_WIDTH - btn_w)//2, start_y, btn_w, btn_h, RED_BTN)

    def draw_overlay(self, title_text, sub_text):
        t = self.title_font.render(title_text, True, WHITE)
        st = self.font.render(sub_text, True, LIGHT_GRAY)
        self.screen.blit(t, ((SCREEN_WIDTH - t.get_width()) // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(st, ((SCREEN_WIDTH - st.get_width()) // 2, SCREEN_HEIGHT // 3 + 70))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("ИГРА ОКОНЧЕНА", True, RED_BTN)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, SCREEN_HEIGHT // 4))

        btn_w, btn_h = 300, 50
        start_y = SCREEN_HEIGHT // 2 - 30
        
        self.game_over_btns = {}
        self.game_over_btns["RESTART"] = self.draw_button("Новая игра", (SCREEN_WIDTH - btn_w)//2, start_y, btn_w, btn_h, GREEN_BTN)
        start_y += 65
        self.game_over_btns["MENU"] = self.draw_button("Главное меню", (SCREEN_WIDTH - btn_w)//2, start_y, btn_w, btn_h, BLUE_BTN)
        start_y += 65
        self.game_over_btns["EXIT"] = self.draw_button("Выход из игры", (SCREEN_WIDTH - btn_w)//2, start_y, btn_w, btn_h, RED_BTN)

    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            fall_speed = DIFFICULTIES[self.difficulty_keys[self.difficulty_idx]]

            if self.state == "PLAYING":
                if current_time - self.last_fall_time > fall_speed:
                    self.move_down()
                    self.last_fall_time = current_time

                keys = pygame.key.get_pressed()
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    if current_time - self.last_soft_drop_time > self.soft_drop_delay:
                        self.move_down()
                        self.last_soft_drop_time = current_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.state == "PLAYING":
                        self.save_game()
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if self.state == "MENU":
                        if "CONTINUE" in self.btns and self.btns["CONTINUE"].collidepoint(pos):
                            if self.load_game():
                                self.state = "PLAYING"
                        elif "NEW_GAME" in self.btns and self.btns["NEW_GAME"].collidepoint(pos):
                            self.delete_save()
                            self.reset_game()
                            self.state = "PLAYING"
                        elif "DIFF" in self.btns and self.btns["DIFF"].collidepoint(pos):
                            self.difficulty_idx = (self.difficulty_idx + 1) % len(self.difficulty_keys)
                            self.delete_save()
                        elif "EXIT" in self.btns and self.btns["EXIT"].collidepoint(pos):
                            running = False

                    elif self.state in ["PLAYING", "PAUSED"]:
                        if "PAUSE" in self.game_btns and self.game_btns["PAUSE"].collidepoint(pos):
                            if self.state == "PLAYING":
                                self.state = "PAUSED"
                                self.save_game()
                            else:
                                self.state = "PLAYING"
                        elif "RESTART" in self.game_btns and self.game_btns["RESTART"].collidepoint(pos):
                            self.delete_save()
                            self.reset_game()
                            self.state = "PLAYING"
                        elif "MENU" in self.game_btns and self.game_btns["MENU"].collidepoint(pos):
                            if self.state == "PLAYING":
                                self.save_game()
                            self.state = "MENU"

                    elif self.state == "GAME_OVER":
                        if "RESTART" in self.game_over_btns and self.game_over_btns["RESTART"].collidepoint(pos):
                            self.reset_game()
                            self.state = "PLAYING"
                        elif "MENU" in self.game_over_btns and self.game_over_btns["MENU"].collidepoint(pos):
                            self.state = "MENU"
                        elif "EXIT" in self.game_over_btns and self.game_over_btns["EXIT"].collidepoint(pos):
                            running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state in ["PLAYING", "PAUSED", "GAME_OVER"]:
                            if self.state == "PLAYING":
                                self.save_game()
                            self.state = "MENU"
                        elif self.state == "MENU":
                            running = False

                    if self.state == "PLAYING":
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            if self.valid_move(self.current_piece, offset_x=-1):
                                self.current_piece.x -= 1
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            if self.valid_move(self.current_piece, offset_x=1):
                                self.current_piece.x += 1
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            old_shape = [r[:] for r in self.current_piece.shape]
                            self.current_piece.rotate()
                            if not self.valid_move(self.current_piece):
                                self.current_piece.shape = old_shape

            self.draw()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Tetris()
    game.run()

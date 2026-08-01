import pygame, random, os

pygame.init()
info = pygame.display.Info()
W, H = info.current_w, info.current_h
COLS, ROWS, SIZE = 14, 20, H // 22
GW, PANEL = COLS * SIZE, 300
SX, SY = (W - (GW + PANEL)) // 2, (H - (ROWS * SIZE)) // 2

BLACK, BG, TEXT, COLORS = (0,0,0), (15,15,20), (240,240,250), [
    (0,255,255), (0,0,255), (255,165,0), (255,255,0), (0,255,0), (128,0,128), (255,0,0)
]

# Компактное математическое описание базовых фигур Тетриса
RAW_SHAPES = [[4,5,6,7], [1,5,9,10], [1,5,9,8], [1,2,5,6], [5,6,8,9], [1,4,5,6], [4,5,9,10]]
SHAPES = []
for s in RAW_SHAPES:
    rot = [s]
    for _ in range(3):
        # Математический поворот матрицы 4х4 на 90 градусов
        prev = rot[-1]
        rot.append([ (3 - (idx % 4)) * 4 + (idx // 4) for idx in prev ])
    SHAPES.append(rot)

class Figure:
    def __init__(self):
        self.type = random.randint(0, 6)
        self.color, self.rotation, self.x, self.y = COLORS[self.type], 0, COLS // 2 - 2, 0
    def matrix(self): return SHAPES[self.type][self.rotation]
    def rotate(self): self.rotation = (self.rotation + 1) % 4

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.f32, self.f24, self.f18 = pygame.font.SysFont("Arial", 32, 1), pygame.font.SysFont("Arial", 24, 1), pygame.font.SysFont("Arial", 18)
        self.file = "highscore.txt"
        self.record = int(open(self.file).read().strip()) if os.path.exists(self.file) else 0
        self.reset()

    def reset(self):
        self.grid = [[0]*COLS for _ in range(ROWS)]
        self.fig, self.over, self.score = Figure(), False, 0

    def collide(self, dx=0, dy=0, mat=None):
        m = mat if mat else self.fig.matrix()
        for idx in m:
            bx, by = (idx % 4) + self.fig.x + dx, (idx // 4) + self.fig.y + dy
            if bx < 0 or bx >= COLS or by >= ROWS or (by >= 0 and self.grid[by][bx]): return True
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
        if self.score > self.record: self.record = self.score
        self.fig = Figure()
        if self.collide():
            self.over = True
            with open(self.file, "w") as f: f.write(str(self.record))

    def step(self):
        if not self.collide(dy=1): self.fig.y += 1
        else: self.freeze()

    def draw(self):
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, BLACK, [SX, SY, GW, ROWS * SIZE])
        for r in range(ROWS):
            for c in range(COLS):
                pygame.draw.rect(self.screen, (45,45,55), [SX + c*SIZE, SY + r*SIZE, SIZE, SIZE], 1)
                if self.grid[r][c]: pygame.draw.rect(self.screen, self.grid[r][c], [SX + c*SIZE+1, SY + r*SIZE+1, SIZE-2, SIZE-2])
        if not self.over:
            for idx in self.fig.matrix():
                pygame.draw.rect(self.screen, self.fig.color, [SX + ((idx % 4) + self.fig.x)*SIZE+1, SY + ((idx // 4) + self.fig.y)*SIZE+1, SIZE-2, SIZE-2])
        
        PX = SX + GW
        pygame.draw.line(self.screen, (100,100,100), (PX, SY), (PX, SY + ROWS * SIZE), 3)
        self.screen.blit(self.f32.render("ОЧКИ:", 1, TEXT), (PX + 40, SY + 40))
        self.screen.blit(self.f32.render(str(self.score), 1, (0,255,0)), (PX + 40, SY + 85))
        self.screen.blit(self.f32.render("РЕКОРД:", 1, TEXT), (PX + 40, SY + 170))
        self.screen.blit(self.f32.render(str(self.record), 1, (255,215,0)), (PX + 40, SY + 215))
        
        self.screen.blit(self.f32.render("УПРАВЛЕНИЕ:", 1, TEXT), (PX + 40, SY + 320))
        hints = [("Esc — Выйти из игры", (255,100,100)), ("Вверх — Поворот фигуры", (150,150,160)), ("Влево / Вправо — Движение", (150,150,160)), ("Вниз — Ускорить падение", (150,150,160))]
        for i, (text, col) in enumerate(hints): self.screen.blit(self.f18.render(text, 1, col), (PX + 40, SY + 370 + i*30))

        if self.over:
            overlay = pygame.Surface((GW, ROWS * SIZE), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (SX, SY))
            txt = pygame.font.SysFont("Arial", 48, 1).render("ИГРА ОКОНЧЕНА", 1, (255,50,50))
            self.screen.blit(txt, (SX + GW // 2 - txt.get_width() // 2, SY + 150))
            self.br = pygame.Rect(SX + GW // 2 - 110, SY + 260, 220, 50)
            self.be = pygame.Rect(SX + GW // 2 - 110, SY + 340, 220, 50)
            m = pygame.mouse.get_pos()
            pygame.draw.rect(self.screen, (40,200,40) if self.br.collidepoint(m) else (30,140,30), self.br, border_radius=7)
            pygame.draw.rect(self.screen, (200,40,40) if self.be.collidepoint(m) else (140,30,30), self.be, border_radius=7)
            self.screen.blit(self.f24.render("Заново", 1, TEXT), (self.br.centerx - 35, self.br.centery - 12))
            self.screen.blit(self.f24.render("Выйти", 1, TEXT), (self.be.centerx - 30, self.be.centery - 12))
        pygame.display.flip()

    def play(self):
        cnt, loop = 0, True
        while loop:
            self.clock.tick(60)
            if not self.over:
                cnt += 1
                if cnt >= (2 if pygame.key.get_pressed()[pygame.K_DOWN] else 25):
                    cnt = 0
                    self.step()
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): loop = False
                if self.over and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.br.collidepoint(e.pos): self.reset()
                    elif self.be.collidepoint(e.pos): loop = False
                if not self.over and e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_LEFT and not self.collide(dx=-1): self.fig.x -= 1
                    if e.key == pygame.K_RIGHT and not self.collide(dx=1): self.fig.x += 1
                    if e.key == pygame.K_UP:
                        self.fig.rotate()
                        if self.collide():
                            for _ in range(3): self.fig.rotate()
            self.draw()
        pygame.quit()

if __name__ == "__main__":
    Tetris().play()

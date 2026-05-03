import pygame
import random
import json
import os

# --- Configuration ---
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
GRID_SIZE = 20
FPS = 60            # render frames per second
BASE_SPEED = 8      # grid cells per second

BG_COLOR = (10, 20, 30)
GRID_COLOR = (20, 30, 40)
SNAKE_HEAD_COLOR = (70, 200, 120)
SNAKE_BODY_COLOR = (50, 150, 100)
FOOD_COLOR = (220, 30, 40)
TEXT_COLOR = (240, 240, 240)
PAUSE_COLOR = (200, 150, 40)

HS_FILE = "snake_highscore.json"

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()      # for FPS (render)


class Game:
    def __init__(self):
        self.state = "start"
        self.running = True
        self.paused = False

        self.score = 0
        self.high_score = self.load_high_score()

        # Speed in grid cells per second; logic is separate from FPS
        self.speed = BASE_SPEED
        self.last_move = 0  # ms

        self.grid_width = WINDOW_WIDTH // GRID_SIZE
        self.grid_height = WINDOW_HEIGHT // GRID_SIZE

        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.food = self.generate_food()

        self.font_small = pygame.font.SysFont("Arial", 20)
        self.font_medium = pygame.font.SysFont("Arial", 32)
        self.font_large = pygame.font.SysFont("Arial", 48)

    def load_high_score(self):
        if os.path.exists(HS_FILE):
            with open(HS_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        return 0

    def save_high_score(self):
        with open(HS_FILE, "w") as f:
            json.dump({"high_score": self.high_score}, f)

    def generate_food(self):
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            pos = (x, y)
            if pos not in self.snake:
                return pos

    def reset_game(self):
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.speed = BASE_SPEED
        self.last_move = 0
        self.food = self.generate_food()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if self.state == "start":
                    self.state = "playing"

                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = "playing"
                    elif event.key == pygame.K_q:
                        self.running = False

                elif self.state == "playing":
                    if event.key == pygame.K_UP and self.direction != (0, 1):
                        self.next_direction = (0, -1)
                    elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                        self.next_direction = (0, 1)
                    elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                        self.next_direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                        self.next_direction = (1, 0)
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused

    def update_logic(self, current_time):
        """Run snake movement logic at game speed, not at FPS."""
        if self.state != "playing" or self.paused:
            return

        # Time interval between moves in milliseconds
        interval = 1000 // max(1, int(self.speed))

        if current_time - self.last_move >= interval:
            self.direction = self.next_direction

            hx, hy = self.snake[0]
            dx, dy = self.direction
            nx, ny = hx + dx, hy + dy

            # Wall collision
            if nx < 0 or nx >= self.grid_width or ny < 0 or ny >= self.grid_height:
                self.state = "game_over"
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                return

            # Self collision
            new_head = (nx, ny)
            if new_head in self.snake:
                self.state = "game_over"
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                return

            self.snake.insert(0, new_head)

            if new_head == self.food:
                self.score += 1
                self.speed = min(30, BASE_SPEED + self.score)  # smoothly increase
                self.food = self.generate_food()
            else:
                self.snake.pop()

            self.last_move = current_time

    def draw_grid(self):
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (WINDOW_WIDTH, y), 1)

    def draw_snake(self):
        for i, (x, y) in enumerate(self.snake):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if i == 0:
                pygame.draw.rect(screen, SNAKE_HEAD_COLOR, rect, border_radius=3)
            else:
                pygame.draw.rect(screen, SNAKE_BODY_COLOR, rect, border_radius=2)
                inner = pygame.Rect(
                    x * GRID_SIZE + 3, y * GRID_SIZE + 3,
                    GRID_SIZE - 6, GRID_SIZE - 6
                )
                pygame.draw.rect(screen, (60, 180, 130), inner, border_radius=2)

    def draw_food(self):
        x, y = self.food
        center = (
            x * GRID_SIZE + GRID_SIZE // 2,
            y * GRID_SIZE + GRID_SIZE // 2
        )
        radius = GRID_SIZE // 2 - 2
        pygame.draw.circle(screen, FOOD_COLOR, center, radius)

    def draw_text(self, text, font, color, x, y, center=False):
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        screen.blit(surf, rect)

    def draw_ui(self):
        if self.state == "playing":
            self.draw_text(f"Score: {self.score}", self.font_small, TEXT_COLOR, 10, 10)
            self.draw_text(f"High: {self.high_score}", self.font_small, TEXT_COLOR, 10, 40)
            if self.paused:
                self.draw_text(
                    "PAUSED", self.font_medium, PAUSE_COLOR,
                    WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
                    center=True
                )

    def draw_start_screen(self):
        screen.fill(BG_COLOR)
        self.draw_text("SNAKE GAME", self.font_large, TEXT_COLOR,
                       WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3, center=True)
        self.draw_text("Press any key to start", self.font_small, TEXT_COLOR,
                       WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, center=True)
        self.draw_text("High Score: " + str(self.high_score), self.font_small, TEXT_COLOR,
                       WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40, center=True)

    def draw_game_over_screen(self):
        self.draw_text("GAME OVER", self.font_large, TEXT_COLOR,
                       WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3, center=True)
        self.draw_text(f"Score: {self.score}", self.font_small, TEXT_COLOR,
                       WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, center=True)
        self.draw_text("Press R to Restart, Q to Quit", self.font_small, TEXT_COLOR,
                       WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40, center=True)

    def render(self):
        screen.fill(BG_COLOR)

        if self.state == "playing":
            self.draw_grid()
            self.draw_snake()
            self.draw_food()
        elif self.state == "start":
            self.draw_start_screen()
        elif self.state == "game_over":
            self.draw_game_over_screen()

        self.draw_ui()
        pygame.display.flip()

    def run(self):
        """
        Main game loop: draw at FPS, update logic at game speed.
        """
        current_time = pygame.time.get_ticks()
        while self.running:
            self.handle_events()
            current_time = pygame.time.get_ticks()
            self.update_logic(current_time)
            self.render()
            clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()
import pygame
import random
import sys
import json
import os

pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 400, 600
BLOCK_HEIGHT = 35
FPS = 60
FONT = pygame.font.SysFont("arial", 24)
MAX_VISIBLE_Y = 200
PR_FILE = "pr.json"

# --- Colors ---
BLACK = (0, 0, 0)
SPARKLE_COLOR = (255, 215, 0)
GREY = (180, 180, 180)
BLUE = (70, 130, 180)
BG_FILL_COLOR = (165, 210, 140)
COLORS = [GREY, BLUE]

# --- Pygame Setup ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stack")
clock = pygame.time.Clock()

# --- Load and Scale Background Image ---
bg_image = pygame.image.load("image.png").convert()
# Keep original width, scale height to actual image height
bg_height = bg_image.get_height()

# --- Load Personal Best ---
def load_personal_record():
    if os.path.exists(PR_FILE):
        with open(PR_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("best", 0)
            except json.JSONDecodeError:
                return 0
    return 0

def save_personal_record(best_score):
    with open(PR_FILE, "w") as f:
        json.dump({"best": best_score}, f)

personal_best = load_personal_record()

# --- Block Class ---
class Block:
    def __init__(self, x, y, width, height=BLOCK_HEIGHT, moving=True, direction=1, color=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.moving = moving
        self.direction = direction
        self.speed = 4
        self.color = color

    def move(self):
        if self.moving:
            self.x += self.speed * self.direction
            if self.x <= 0 or self.x + self.width >= WIDTH:
                self.direction *= -1

    def draw(self, surface, offset_y):
        rect = pygame.Rect(self.x, self.y - offset_y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface,BLACK, rect, width=3)

# --- Sparkle Effect ---
class Sparkle:
    def __init__(self, x, y):
        self.particles = [[x, y, random.randint(1, 3), random.choice([-1, 1]), random.randint(-3, -1)] for _ in range(10)]

    def update(self):
        for p in self.particles:
            p[0] += p[3]
            p[1] += p[4]
            p[2] -= 0.1
        self.particles = [p for p in self.particles if p[2] > 0]

    def draw(self, surface, offset_y):
        for p in self.particles:
            pygame.draw.circle(surface, SPARKLE_COLOR, (int(p[0]), int(p[1] - offset_y)), int(p[2]))

# --- Main Game Class ---
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.blocks = []
        self.offset_y = 0
        self.current_direction = 1
        self.score = 0
        self.sparkles = []

        color_index = self.score % 2
        self.current_block = Block(
            x=0, y=HEIGHT - BLOCK_HEIGHT * 2, width=WIDTH // 3,
            direction=self.current_direction, color=COLORS[color_index]
        )

        base_block = Block(
            WIDTH // 2 - WIDTH // 6, HEIGHT - BLOCK_HEIGHT,
            WIDTH // 3, moving=False, color=COLORS[1]
        )

        self.blocks.append(base_block)
        self.running = True

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.running:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.running:
                self.drop_block()
            else:
                self.reset()

    def drop_block(self):
        if not self.blocks:
            return

        last_block = self.blocks[-1]
        overlap_x = max(self.current_block.x, last_block.x)
        overlap_end = min(self.current_block.x + self.current_block.width, last_block.x + last_block.width)
        overlap_width = overlap_end - overlap_x

        if overlap_width <= 0:
            self.running = False
            return

        if overlap_width == self.current_block.width and self.current_block.x == last_block.x:
            self.sparkles.append(Sparkle(
                self.current_block.x + self.current_block.width // 2, self.current_block.y
            ))

        new_block = Block(
            overlap_x, self.current_block.y, overlap_width,
            moving=False, color=self.current_block.color
        )

        self.blocks.append(new_block)
        self.score += 1

        global personal_best
        if self.score > personal_best:
            personal_best = self.score
            save_personal_record(personal_best)

        # Move the new block UP to simulate building going up
        new_y = self.current_block.y - BLOCK_HEIGHT

        # Adjust offset to scroll the screen UP as building grows
        if new_y - self.offset_y <= MAX_VISIBLE_Y:
            self.offset_y -= BLOCK_HEIGHT

        self.current_direction *= -1
        start_x = 0 if self.current_direction == 1 else WIDTH - overlap_width
        color_index = self.score % 2
        self.current_block = Block(
            start_x, new_y, overlap_width,
            direction=self.current_direction, color=COLORS[color_index]
        )

    def update(self):
        if self.running:
            self.current_block.move()

        for sparkle in self.sparkles:
            sparkle.update()
        self.sparkles = [s for s in self.sparkles if s.particles]

    def draw(self, surface):
        # Calculate which part of bg_image to draw to simulate scrolling UP starting from bottom
        scroll_y = bg_height - HEIGHT + self.offset_y  # offset_y is negative or zero
        if scroll_y < 0:
            scroll_y = 0
        if scroll_y + HEIGHT > bg_height:
            scroll_y = bg_height - HEIGHT

        visible_rect = pygame.Rect(0, scroll_y, WIDTH, HEIGHT)
        surface.blit(bg_image.subsurface(visible_rect), (0, 0))

        # Draw blocks and sparkles
        for block in self.blocks:
            block.draw(surface, self.offset_y)

        if self.running:
            self.current_block.draw(surface, self.offset_y)

        for sparkle in self.sparkles:
            sparkle.draw(surface, self.offset_y)

        # Draw score background and text
        score_bg_rect = pygame.Rect(8, 8, 220, 30)
        pygame.draw.rect(surface, (255, 255, 255), score_bg_rect)
        pygame.draw.rect(surface, BLACK, score_bg_rect, 2)

        score_text = FONT.render(f"Score: {self.score} | Best: {personal_best}", True, BLACK)
        surface.blit(score_text, (score_bg_rect.x + 10, score_bg_rect.y + 5))

        # Game over message
        if not self.running:
            msg = FONT.render("Game Over! Click to Restart", True, BLACK)
            surface.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))

# --- Main Loop ---
def main():
    game = Game()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_personal_record(personal_best)
                pygame.quit()
                sys.exit()
            game.handle_input(event)

        game.update()
        game.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()

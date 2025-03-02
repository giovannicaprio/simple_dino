import pygame
import random
import os
from jump_detection import JumpDetector

# Initialize Pygame and its mixer
pygame.init()
pygame.mixer.init()

# Set up the game window
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dino Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Pre-load and scale images efficiently
def load_and_scale(path, size):
    image = pygame.image.load(path)
    return pygame.transform.scale(image, size)

# Load and scale images once
SKY_IMAGE = load_and_scale(os.path.join('art', 'sky.png'), (SCREEN_WIDTH, SCREEN_HEIGHT))
DINO_IMAGES = [load_and_scale(os.path.join('art', f'dino_run({i}).png'), (90, 90)) for i in range(1, 8)]
FLYING_DINO_IMAGES = [
    load_and_scale(os.path.join('art', 'fly_dino0.png'), (80, 80)),
    load_and_scale(os.path.join('art', 'fly_dino1.png'), (80, 80))
]
OBSTACLE_IMAGES = [
    load_and_scale(os.path.join('art', 'obstacles', f'obstacle{i}.png'), (60, 80))
    for i in range(2)  # Load obstacle0.png and obstacle1.png
]
FLOOR_IMAGE = load_and_scale(os.path.join('art', 'floor.png'), (94, 94))
CLOUD_IMAGE = load_and_scale(os.path.join('art', 'clouds.png'), (128, 71))

# Load sounds with lower quality for better performance
pygame.mixer.init(frequency=22050, size=-16, channels=1)
DEATH_SOUND = pygame.mixer.Sound(os.path.join('art', 'death_sound.wav'))
JUMP_SOUND = pygame.mixer.Sound(os.path.join('art', 'jump_sound.wav'))
DEATH_SOUND.set_volume(0.5)
JUMP_SOUND.set_volume(0.5)

class GameState:
    def __init__(self):
        self.score = 0
        self.jumps = 0
        self.game_over = False
        self.game_speed = 6

    def reset(self):
        self.score = 0
        self.jumps = 0
        self.game_over = False
        self.game_speed = 6

# Game state
game_state = GameState()
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Animation constants
ANIMATION_SPEED = 6  # Lower number = slower animation
ANIMATION_COOLDOWN = 60 // ANIMATION_SPEED  # Number of frames between animation updates

class FlyingDino(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.images = FLYING_DINO_IMAGES
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = random.randint(50, 200)  # Random height like clouds
        self.animation_timer = 0
        self.animation_cooldown = ANIMATION_COOLDOWN

    def update(self):
        # Move like clouds
        self.rect.x -= game_state.game_speed * 0.5
        if self.rect.right < 0:
            self.rect.x = SCREEN_WIDTH
            self.rect.y = random.randint(50, 200)

        # Animate wings
        self.animation_timer += 1
        if self.animation_timer >= self.animation_cooldown:
            self.animation_timer = 0
            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]

class Cloud(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = CLOUD_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = random.randint(50, 200)  # Random height for variety

    def update(self):
        self.rect.x -= game_state.game_speed * 0.5  # Clouds move slower than the ground
        if self.rect.right < 0:
            self.rect.x = SCREEN_WIDTH
            self.rect.y = random.randint(50, 200)  # New random height when recycling

class Dino(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = DINO_IMAGES
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = 50
        self.rect.y = SCREEN_HEIGHT - 100
        self.jump_speed = -15
        self.gravity = 0.8
        self.velocity = 0
        self.is_jumping = False
        self.mask = pygame.mask.from_surface(self.image)
        # Animation variables
        self.animation_timer = 0
        self.animation_cooldown = ANIMATION_COOLDOWN

    def jump(self):
        if not self.is_jumping:
            JUMP_SOUND.play()  # Play jump sound when dinosaur jumps
            self.velocity = self.jump_speed
            self.is_jumping = True

    def update(self):
        if self.is_jumping:
            self.rect.y += self.velocity
            self.velocity += self.gravity
            
            if self.rect.y >= SCREEN_HEIGHT - 100:
                self.rect.y = SCREEN_HEIGHT - 100
                self.is_jumping = False
                self.velocity = 0
        else:
            # Update the animation timer
            self.animation_timer += 1
            if self.animation_timer >= self.animation_cooldown:
                self.animation_timer = 0
                # Update the dinosaur's image for running animation
                self.index = (self.index + 1) % len(self.images)
                self.image = self.images[self.index]
                # Update mask for the new image
                self.mask = pygame.mask.from_surface(self.image)

class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = 60
        self.height = 80
        self.images = OBSTACLE_IMAGES
        self.set_random_image()
        self.set_position(SCREEN_WIDTH, SCREEN_HEIGHT - 100)

    def set_random_image(self):
        self.image = random.choice(self.images)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= game_state.game_speed
        if self.rect.right < 0:
            self.set_random_image()  # Choose new random obstacle
            self.set_position(SCREEN_WIDTH, SCREEN_HEIGHT - 100)
            return True
        return False

class Floor(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = FLOOR_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = SCREEN_HEIGHT - 94

    def update(self):
        self.rect.x -= game_state.game_speed
        if self.rect.right < 0:
            self.rect.x = SCREEN_WIDTH

# Create sprite groups
all_sprites = pygame.sprite.Group()
cloud_group = pygame.sprite.Group()
flying_dino_group = pygame.sprite.Group()
obstacle_group = pygame.sprite.Group()
floor_group = pygame.sprite.Group()

# Create a limited number of clouds, flying dinos, and floor tiles for better performance
for x in range(0, SCREEN_WIDTH + 300, 3000):  # Reduced number of clouds
    cloud = Cloud(x)
    all_sprites.add(cloud)
    cloud_group.add(cloud)

# Add flying dinos at different positions than clouds
for x in range(150, SCREEN_WIDTH + 300, 3000):  # Offset from clouds
    flying_dino = FlyingDino(x)
    all_sprites.add(flying_dino)
    flying_dino_group.add(flying_dino)

for x in range(0, SCREEN_WIDTH + 128, 64):  # Only create visible floor tiles
    floor = Floor(x)
    all_sprites.add(floor)
    floor_group.add(floor)

# Create the dino
dino = Dino()
all_sprites.add(dino)

# Create the first obstacle
obstacle = Obstacle()
all_sprites.add(obstacle)
obstacle_group.add(obstacle)

def check_collision(dino, obstacle):
    # Use mask collision for more precise hit detection with sprites
    offset_x = obstacle.rect.x - dino.rect.x
    offset_y = obstacle.rect.y - dino.rect.y
    return dino.mask.overlap(obstacle.mask, (offset_x, offset_y)) is not None

def reset_game():
    game_state.reset()
    dino.rect.y = SCREEN_HEIGHT - 100
    dino.velocity = 0
    dino.is_jumping = False
    obstacle.set_random_image()  # Choose new random obstacle
    obstacle.set_position(SCREEN_WIDTH, SCREEN_HEIGHT - 100)
    
    # Reset floor positions
    for i, floor in enumerate(floor_group):
        floor.rect.x = i * 64
    
    # Reset cloud positions
    for i, cloud in enumerate(cloud_group):
        cloud.rect.x = i * 300
        cloud.rect.y = random.randint(50, 200)
        
    # Reset flying dino positions
    for i, flying_dino in enumerate(flying_dino_group):
        flying_dino.rect.x = 150 + (i * 300)  # Offset from clouds
        flying_dino.rect.y = random.randint(50, 200)

# Initialize jump detector
jump_detector = JumpDetector()

# Performance settings
MAX_FPS = 60
MIN_UPDATE_TIME = 1000 // MAX_FPS  # Minimum time between updates in milliseconds

# Game loop
running = True
last_update = pygame.time.get_ticks()
while running:
    # Control frame rate
    current_time = pygame.time.get_ticks()
    if current_time - last_update < MIN_UPDATE_TIME:
        continue
    last_update = current_time
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            jump_detector.release()  # Clean up camera resources
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_state.game_over:
                reset_game()
    
    # Check for jump detection
    if jump_detector.is_jumping():
        if game_state.game_over:
            reset_game()  # Reset game if jump detected during game over
        elif not dino.is_jumping:
            game_state.jumps += 1
            dino.jump()

    if not game_state.game_over:
        # Update
        all_sprites.update()
        
        # Check for collision using mask collision detection
        if check_collision(dino, obstacle):
            DEATH_SOUND.play()  # Play death sound when collision occurs
            game_state.game_over = True
        
        # Update score and speed
        if obstacle.update():
            game_state.score += 1
            if game_state.score % 5 == 0:
                game_state.game_speed += 0.5

    # Draw
    screen.blit(SKY_IMAGE, (0, 0))  # Draw sky background
    all_sprites.draw(screen)
    
    # Draw score and jumps
    score_text = font.render(f'Score: {game_state.score}  Jumps: {game_state.jumps}', True, BLACK)
    screen.blit(score_text, (10, 10))

    # Draw game over message
    if game_state.game_over:
        game_over_text = font.render('Game Over! Press R to restart', True, BLACK)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2))

    # Update display
    pygame.display.flip()
    clock.tick(60)

# Clean up resources
jump_detector.release()
pygame.quit()

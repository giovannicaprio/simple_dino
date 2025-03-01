import pygame
import random
import os

# Initialize Pygame and its mixer
pygame.init()
pygame.mixer.init()

# Set up the game window
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dino Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Load images
DINO_IMAGES = [pygame.image.load(os.path.join('art', f'dino_run({i}).png')) for i in range(1, 8)]
OBSTACLE_IMAGE = pygame.image.load(os.path.join('art', 'obstacle.png'))
FLOOR_IMAGE = pygame.image.load(os.path.join('art', 'floor.png'))
CLOUD_IMAGE = pygame.image.load(os.path.join('art', 'clouds.png'))

# Load sounds
DEATH_SOUND = pygame.mixer.Sound(os.path.join('art', 'death_sound.wav'))
JUMP_SOUND = pygame.mixer.Sound(os.path.join('art', 'jump_sound.wav'))
# Set sound volumes
DEATH_SOUND.set_volume(0.5)
JUMP_SOUND.set_volume(0.5)

# Scale images
DINO_IMAGES = [pygame.transform.scale(image, (60, 60)) for image in DINO_IMAGES]
OBSTACLE_IMAGE = pygame.transform.scale(OBSTACLE_IMAGE, (40, 60))
FLOOR_IMAGE = pygame.transform.scale(FLOOR_IMAGE, (64, 64))
CLOUD_IMAGE = pygame.transform.scale(CLOUD_IMAGE, (128, 71))

# Game variables
GAME_SPEED = 6
score = 0
game_over = False
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Animation constants
ANIMATION_SPEED = 6  # Lower number = slower animation
ANIMATION_COOLDOWN = 60 // ANIMATION_SPEED  # Number of frames between animation updates

class Cloud(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = CLOUD_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = random.randint(50, 200)  # Random height for variety

    def update(self):
        self.rect.x -= GAME_SPEED * 0.5  # Clouds move slower than the ground
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
        self.rect.y = SCREEN_HEIGHT - 70
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
            
            if self.rect.y >= SCREEN_HEIGHT - 70:
                self.rect.y = SCREEN_HEIGHT - 70
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

class Cactus(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = 40
        self.height = 60
        self.image = OBSTACLE_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = SCREEN_HEIGHT - 75
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.x -= GAME_SPEED
        if self.rect.right < 0:
            self.rect.x = SCREEN_WIDTH
            return True
        return False

class Floor(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = FLOOR_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = SCREEN_HEIGHT - 64

    def update(self):
        self.rect.x -= GAME_SPEED
        if self.rect.right < 0:
            self.rect.x = SCREEN_WIDTH

# Create sprite groups
all_sprites = pygame.sprite.Group()
cloud_group = pygame.sprite.Group()
cactus_group = pygame.sprite.Group()
floor_group = pygame.sprite.Group()

# Create clouds
for x in range(0, SCREEN_WIDTH * 2, 300):  # Space clouds apart
    cloud = Cloud(x)
    all_sprites.add(cloud)
    cloud_group.add(cloud)

# Create floor tiles
for x in range(0, SCREEN_WIDTH + 64, 64):  # +64 to prevent gaps
    floor = Floor(x)
    all_sprites.add(floor)
    floor_group.add(floor)

# Create the dino
dino = Dino()
all_sprites.add(dino)

# Create the first cactus
cactus = Cactus()
all_sprites.add(cactus)
cactus_group.add(cactus)

def check_collision(dino, cactus):
    # Use mask collision for more precise hit detection with sprites
    offset_x = cactus.rect.x - dino.rect.x
    offset_y = cactus.rect.y - dino.rect.y
    return dino.mask.overlap(cactus.mask, (offset_x, offset_y)) is not None

def reset_game():
    global score, game_over, GAME_SPEED
    score = 0
    game_over = False
    GAME_SPEED = 6
    dino.rect.y = SCREEN_HEIGHT - 70
    dino.velocity = 0
    dino.is_jumping = False
    cactus.rect.x = SCREEN_WIDTH
    
    # Reset floor positions
    for i, floor in enumerate(floor_group):
        floor.rect.x = i * 64
    
    # Reset cloud positions
    for i, cloud in enumerate(cloud_group):
        cloud.rect.x = i * 300
        cloud.rect.y = random.randint(50, 200)

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                dino.jump()
            if event.key == pygame.K_r and game_over:
                reset_game()

    if not game_over:
        # Update
        all_sprites.update()
        
        # Check for collision using mask collision detection
        if check_collision(dino, cactus):
            DEATH_SOUND.play()  # Play death sound when collision occurs
            game_over = True
        
        # Update score and speed
        if cactus.update():
            score += 1
            if score % 5 == 0:
                GAME_SPEED += 0.5

    # Draw
    screen.fill(WHITE)
    all_sprites.draw(screen)
    
    # Draw score
    score_text = font.render(f'Score: {score}', True, BLACK)
    screen.blit(score_text, (10, 10))

    # Draw game over message
    if game_over:
        game_over_text = font.render('Game Over! Press R to restart', True, BLACK)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2))

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

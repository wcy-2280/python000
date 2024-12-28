import pygame
from settings import *
from random import randint, choice
from timer import Timer

# 通用类
class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z = LAYERS['main']):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = z
        # hitbox设定，大幅缩小高度值以增加y轴重叠遮蔽
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.2, -self.rect.height * 0.75)

# 交互类
class Interaction(Generic):
    def __init__(self, pos, size, groups, name):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.name = name

class Water(Generic):
    def __init__(self, pos, frames, groups):

        # animation setup
        self.frames = frames # 图片列表
        self.frame_index = 0 # 图片索引

        # sprite_setup
        super().__init__(
            pos = pos, 
            surf = self.frames[self.frame_index], 
            groups = groups, 
            z = LAYERS['water'])
        
    def animate(self, dt):
        # 归零，循环
        self.frame_index += 5 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        # 图片更新
        self.image = self.frames[int(self.frame_index)]

    def update(self,dt):
        self.animate(dt)

class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        # 单独设置花的碰撞箱
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)

# 粒子效果
class Particale(Generic):
    def __init__(self, pos, surf, groups, z, duration = 200):
        super().__init__(pos, surf, groups, z)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration

        # white surface
        mask_surf = pygame.mask.from_surface(self.image) # 得到黑白图片，有色像素为白，透明像素为黑
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0,0,0)) # 将黑色换成透明色
        self.image = new_surf # 更新图片

    def update(self,dt):
        current_time = pygame.time.get_ticks()
        # 计时
        if current_time - self.start_time > self.duration:
            self.kill()


class Tree(Generic):
    def __init__(self, pos, surf, groups, all_sprites, name, player_add):
        super().__init__(pos, surf, groups)

        # tree attributes
        self.health = 5
        self.alive = True
        # 树桩
        stump_path = f'../graphics/stumps/{"small" if name == "Small" else "large"}.png'
        self.stump_surf = pygame.image.load(stump_path).convert_alpha()

        # apples
        self.apple_surf = pygame.image.load('../graphics/fruit/apple.png')
        self.apple_pos = APPLE_POS[name]
        self.apple_sprites = pygame.sprite.Group()
        self.all_sprites = all_sprites
        self.create_fruit()

        # player add
        self.player_add = player_add

        # sounds
        self.axe_sound = pygame.mixer.Sound('../audio/axe.mp3')

    def damage(self):

        # damaging the tree
        self.health -= 1

        # play sound
        self.axe_sound.play() # 播放音效

        # remove an apple
        if len(self.apple_sprites.sprites()) > 0: # 树上苹果数量大于0
                random_apple = choice(self.apple_sprites.sprites()) # 随机选择一个苹果
                Particale(
                    pos = random_apple.rect.topleft,
                    surf = random_apple.image,
                    groups = self.all_sprites,
                    z = LAYERS['fruit'])
                self.player_add('apple') # 获得苹果
                random_apple.kill() # kill

    def check_death(self):
        if self.health <= 0:
            Particale(self.rect.topleft, self.image, self.all_sprites, LAYERS['fruit'], 300)
            self.image = self.stump_surf # 更新树为木桩
            self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height * 0.6)
            self.alive = False
            self.player_add('wood') # 获得木材

    def update(self, dt):
        if self.alive:
            self.check_death()

    # 创建苹果
    def create_fruit(self):
        for pos in self.apple_pos:
            if randint(0,10) < 2:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                # 通过访问class即Tree所在的组，来得到all_sprites，使得苹果能够被描绘
                Generic(
                    pos = (x,y),
                    surf =  self.apple_surf,
                    groups = [self.apple_sprites, self.all_sprites],
                    z = LAYERS['fruit'])
    
    
        
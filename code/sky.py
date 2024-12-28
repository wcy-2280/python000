import pygame
from settings import *
from support import import_folder
from sprites import Generic
from random import randint, choice

# 白天夜晚过渡
class Sky:
    def __init__(self):
        self.display_suface = pygame.display.get_surface()
        self.full_surf = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
        self.start_color = [255,255,255]
        self.end_color = (38,101,189) # 夜晚颜色值

    def display(self,dt):
        for index, value in enumerate(self.end_color):
            if self.start_color[index] > value: # 变暗
                self.start_color[index] -= 2 *dt

        self.full_surf.fill(self.start_color)
        self.display_suface.blit(self.full_surf, (0,0), special_flags = pygame.BLEND_RGBA_MULT)

# 落雨
class Drop(Generic):
    def __init__(self, surf, pos, moving, groups, z):

        # general setup
        super().__init__(pos, surf, groups, z)
        self.lifetime = randint(400,500) # 生存时间
        self.start_time = pygame.time.get_ticks() # 起始时间

        # moving
        self.moving = moving
        if self.moving:
            # movement attributes
            self.pos = pygame.math.Vector2(self.rect.topleft)
            self.direction = pygame.math.Vector2(-2,4)
            self.speed = randint(200,250)
        
    def update(self,dt):
        # movement
        if self.moving:
            self.pos += self.direction * self.speed * dt
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        # timer
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()

# 雨
class Rain:
    def __init__(self, all_sprites):

        self.all_sprites = all_sprites
        self.rain_drops = import_folder('../graphics/rain/drops/')
        self.rain_floor = import_folder('../graphics/rain/floor/')
        self.floor_w, self.floor_h = pygame.image.load('../graphics/world/ground.png').get_size()

    # 创造落雨水花
    def create_floor(self):
        Drop(
            surf = choice(self.rain_floor), # 随机图片
            pos = (randint(0,self.floor_w),randint(0,self.floor_h)), # 随机位置
            moving = False,
            groups = self.all_sprites,
            z = LAYERS['rain floor'])

    # 创造落雨
    def create_drops(self):
        Drop(
            surf = choice(self.rain_drops), # 随机图片
            pos = (randint(0,self.floor_w),randint(0,self.floor_h)), # 随机位置
            moving = True,
            groups = self.all_sprites,
            z = LAYERS['rain drops'])

    # 更新
    def update(self):
        self.create_floor()
        self.create_drops()


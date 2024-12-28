import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
from random import choice

# 耕地类
class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil']

# 浇水的耕地
class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil water']

# 植物类
class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)
        
        # set up
        self.plant_type = plant_type
        self.frames = import_folder(f'../graphics/fruit/{plant_type}')
        self.soil = soil
        self.check_watered = check_watered

        # plant growing
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        # sprite setup
        self.image = self.frames[self.age]
        # self.y_offset = -16 if plant_type == 'corn' else -8
        # self.rect = self.image.get_rect(midbottom = soil.rect.midbottom + pygame.math.Vector2(0,self.y_offset))
        self.rect = self.image.get_rect(center = soil.rect.center)
        self.z = LAYERS['ground plant']

    # 生长
    def grow(self):
        if self.check_watered(self.rect.center): # 检测是否浇水
            self.age += self.grow_speed # 生长

            if int(self.age) > 0:
                self.z = LAYERS['main'] # 成长后可遮蔽
                # 成长后可碰撞
                self.hitbox = self.rect.copy().inflate(-26,-self.rect.height * 0.4)
            
            if self.age >= self.max_age: # 是否成熟
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)] # 更新图片 
            self.rect = self.image.get_rect(center = self.soil.rect.center)


# 土壤层
class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):

        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # graphics
        self.soil_surfs = import_folder_dict('../graphics/soil')
        self.water_surfs = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

        # sounds
        self.hoe_sound = pygame.mixer.Sound('../audio/hoe.wav')
        self.hoe_sound.set_volume(0.1)

        self.plant_sound = pygame.mixer.Sound('../audio/plant.wav')
        self.plant_sound.set_volume(0.1)

    # 创建土壤图格
    def create_soil_grid(self):
        # 加载背景
        ground = pygame.image.load('../graphics/world/ground.png')
        # 水平、垂直图格数
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE
        # 二维列表
        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')
        
    # 可耕地图格列表
    def create_hit_rects(self):
        self.hit_rect = [] # 创建列表
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell: # 可耕地图格
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rect.append(rect)

    # 耕地
    def get_hit(self, point):
        for rect in self.hit_rect:
            if rect.collidepoint(point):
                self.hoe_sound.play() # 播放音效
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X') # 图格添加耕地标识
                    self.create_soil_tiles() # 调用创建耕地函数
                    if self.raining:
                        self.water_all()

    # 浇水
    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                
                # add an entry to the soil grid -> 'w'
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')

                # create the watered soil
                WaterTile(
                    pos = soil_sprite.rect.topleft,
                    surf = choice(self.water_surfs),
                    groups = [self.all_sprites, self.water_sprites])

    # 雨水灌溉 water all
    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    WaterTile(
                    pos = (index_col * TILE_SIZE, index_row * TILE_SIZE),
                    surf = choice(self.water_surfs),
                    groups = [self.all_sprites, self.water_sprites])

    # 移除浇水
    def remove_water(self):

        # destroy all water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # clean up the grid
        for row in self.grid:
            # for cell in row:
            #     if 'W' in cell:
            #         cell.remove('W')
            for i, cell in enumerate(row): # 过滤掉所有的 'W'，保留其他内容
                row[i] = [element for element in cell if element != 'W']

    # 检测浇水
    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered
    
    # 播种
    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                self.plant_sound.play() # 播放音效

                # add an entry to the soil grid -> 'P'
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                
                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(
                        plant_type = seed,
                        groups = [self.all_sprites, self.plant_sprites, self.collision_sprites], 
                        soil = soil_sprite, 
                        check_watered = self.check_watered)

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    # 创建耕地
    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell: # 图格是耕地

                    # tile options
                    t = 'X' in self.grid[index_row -1][index_col]
                    b = 'X' in self.grid[index_row +1][index_col]
                    r = 'X' in self.grid[index_row][index_col + 1]
                    l = 'X' in self.grid[index_row][index_col - 1]

                    tile_type = 'o'

                    # all sides
                    if all((t,b,r,l)): tile_type = 'x'

                    # horizontal tiles only
                    if l and not any((t,b,r)): tile_type = 'r'
                    if r and not any((t,b,l)): tile_type = 'l'
                    if l and r and not any((t,b)): tile_type = 'lr'

                    # vertical only
                    if t and not any((b,r,l)): tile_type = 'b'
                    if b and not any((t,r,l)): tile_type = 't'
                    if t and b and not any((r,l)): tile_type = 'tb'

                    # corners
                    if b and l and not any((t,r)): tile_type = 'tr'
                    if b and r and not any((t,l)): tile_type = 'tl'
                    if t and l and not any((b,r)): tile_type = 'br'
                    if t and r and not any((b,l)): tile_type = 'bl'

                    # T shapes
                    if all((t,b,r)) and not l: tile_type = 'tbr'
                    if all((t,b,l)) and not r: tile_type = 'tbl'
                    if all((l,r,t)) and not b: tile_type = 'lrt'
                    if all((l,r,b)) and not t: tile_type = 'lrb'

                    SoilTile(
                        pos = (index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surf = self.soil_surfs[tile_type],
                        groups = [self.all_sprites, self.soil_sprites])

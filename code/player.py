import pygame
from settings import *
from support import *
from timer import Timer

class Player(pygame.sprite.Sprite): # Player继承Sprite的功能
    def __init__(self, pos, group, collision_sprites, tree_sprites, interaction, soil_layer, toggle_shop):
        # 调用父类__init__方法，初始化并将Player添加到指定的sprite组中
        super().__init__(group)

        self.import_assets()
        self.status = 'down_idle' # 玩家状态
        self.frame_index = 0 # 动画帧


        # general setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS['main']

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 400

        # collision
        self.hitbox = self.rect.copy().inflate((-126, -70))
        self.collision_sprites = collision_sprites

        # timers
        self.timers = {
            'tool use': Timer(350,self.use_tool),
            'seed use': Timer(100,self.use_seed),
            'switch': Timer(200),
        }

        # tools
        self.tools = ['hoe','axe','water']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]

        # seeds
        self.seeds = ['corn','tomato']
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]

        # 手持物
        self.hand = 'tool'

        # inventory 库存
        self.item_inventory = {
            'wood':   0,
            'apple':  0,
            'corn':   0,
            'tomato': 0
        }
        self.seed_inventory = {
            'corn': 5,
            'tomato': 5
        }
        self.money = 200

        # interaction
        self.tree_sprites = tree_sprites
        self.interaction = interaction
        self.sleep = False
        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop

        # sound
        self.watering = pygame.mixer.Sound('../audio/water.mp3')
        self.watering.set_volume(0.2)

    # 使用工具
    def use_tool(self):
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)
        
        if self.selected_tool == 'axe': # 斧子
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos): # 树在工具目标点处
                    tree.damage()

        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_pos)
            self.watering.play() # 播放音效

    # 获取工具目标
    def get_target_pos(self):

        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]
    
    # 播种
    def use_seed(self):
        if self.seed_inventory[self.selected_seed] > 0:
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed)
            self.seed_inventory[self.selected_seed] -= 1

    # 导入玩家图形
    def import_assets(self):
        self.animations = {'up': [],'down': [],'left': [],'right': [],
                            'right_idle':[],'left_idle':[],'up_idle':[],'down_idle':[],
                            'right_hoe':[],'left_hoe':[],'up_hoe':[],'down_hoe':[],
                            'right_axe':[],'left_axe':[],'up_axe':[],'down_axe':[],
                            'right_water':[],'left_water':[],'up_water':[],'down_water':[]}
        for animations in self.animations.keys():
            full_path = '../graphics/character/' + animations
            self.animations[animations] = import_folder(full_path) # 加载字典键值

    # 动画循环
    def animate(self,dt):
        # 归零，循环
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        # 图片更新
        self.image = self.animations[self.status][int(self.frame_index)]

    # 按键输入
    def input(self):
        keys = pygame.key.get_pressed()
    
        if not self.timers['tool use'].active and not self.sleep: # 使用工具时不可移动
            # directions
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            if keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            elif keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            else:
                self.direction.x = 0

            # 手持物品使用
            if keys[pygame.K_SPACE]:
                if self.hand == 'tool':
                    self.timers['tool use'].activate()
                if self.hand == 'seed':
                    self.timers['seed use'].activate()
                self.direction = pygame.math.Vector2() # 使用工具后停止移动
                self.frame_index = 0 # 动画帧归零
            
            # 手持物品切换
            for i, key in enumerate([pygame.K_1, pygame.K_2, pygame.K_3]):
                if keys[key] and not self.timers['switch'].active:
                    self.timers['switch'].activate()  # 激活定时器
                    self.tool_index = i  # 设置tool_index为当前循环的索引（0, 1, 2）
                    self.selected_tool = self.tools[self.tool_index]  # 更新选中的工具
                    self.hand = 'tool'
            for i, key in enumerate([pygame.K_4, pygame.K_5]):
                if keys[key] and not self.timers['switch'].active:
                    self.timers['switch'].activate()  # 激活定时器
                    self.seed_index = i  # 设置seed_index为当前循环的索引（0, 1,）
                    self.selected_seed = self.seeds[self.seed_index]  # 更新选中的种子
                    self.hand = 'seed'
            
            if keys[pygame.K_RETURN]:
                # 检测是否产生碰撞，即玩家在交互区；并返回由碰撞的精灵组成的列表
                collided_interaction_sprite = pygame.sprite.spritecollide(self,self.interaction,False)
                if collided_interaction_sprite:
                    if collided_interaction_sprite[0].name == 'Trader':
                        self.toggle_shop() # 打开/关闭商店

                    else:
                        self.status = 'left_idle'
                        self.sleep = True

    # 玩家状态检测
    def get_status(self):
        # if the player is not moving
        if self.direction.magnitude() == 0:
            # 玩家状态设为待机
            self.status = self.status.split('_')[0] + '_idle'

        # tool use
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    # 定时器更新
    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    # 碰撞
    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                # 检测到碰撞（玩家与物体碰撞箱有重叠）
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0: # moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0: # moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        if self.direction.y > 0: # moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0: # moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery
                
    # 移动
    def move(self, dt):
        
        # normalizing a vector
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    # update
    def update(self, dt):
        self.input()
        self.get_status()
        self.update_timers()
        self.get_target_pos()

        self.move(dt)
        self.animate(dt)
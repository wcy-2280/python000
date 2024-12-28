import pygame 
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particale
from pytmx.util_pygame import load_pygame # 加载基于 Tiled 编辑器创建的 .tmx 地图文件的模块
from support import *
from transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from random import randint
from memu import Menu

class Level:
	def __init__(self):

		# get the display surface
		self.display_surface = pygame.display.get_surface()

		# sprite groups
		self.all_sprites = CameraGroup() # 摄像组
		self.collision_sprites = pygame.sprite.Group() # 可碰撞sprite组
		self.tree_sprites = pygame.sprite.Group() # 树组
		self.interaction_sprites = pygame.sprite.Group() # 交互组

		self.soil_layer = SoilLayer(self.all_sprites,self.collision_sprites) # 土壤层
		self.setup() # 创建实例
		self.overlay = Overlay(self.player) # 叠加层
		self.transition = Transition(self.reset, self.player) # 过渡

		# sky
		self.rain = Rain(self.all_sprites)
		self.raining = randint(0,10) > 7 # 是否下雨
		self.soil_layer.raining = self.raining
		self.sky = Sky()

		# shop
		self.menu = Menu(self.player, self.toggle_shop)
		self.shop_active = False

		# music
		self.success = pygame.mixer.Sound('../audio/success.wav')
		self.success.set_volume(0.2)

		self.music = pygame.mixer.Sound('../audio/music.mp3')
		self.music.set_volume(0.1)
		self.music.play(loops = -1)

	# 创建实例
	def setup(self):
		# 加载 .tmx 地图文件
		tmx_data = load_pygame('../data/map.tmx')

		# house: 加载 house bottom 和 house top 中的图块
		for layer in ['HouseFloor', 'HouseFurnitureBottom']:
			for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
				Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])
		for layer in ['HouseWalls', 'HouseFurnitureTop']:
			for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
				Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites)

		# Fence 栅栏
		for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
			Generic((x * TILE_SIZE, y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])

		# water
		water_frames = import_folder('../graphics/water')
		for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
			Water((x * TILE_SIZE, y * TILE_SIZE), water_frames, self.all_sprites)
		
		# trees
		for obj in tmx_data.get_layer_by_name('Trees'):
			Tree(
				pos = (obj.x, obj.y),
				surf = obj.image,
				groups = [self.all_sprites, self.collision_sprites, self.tree_sprites],
				all_sprites =self.all_sprites,
				name = obj.name,
				player_add = self.player_add)

		# wildflowers
		for obj in tmx_data.get_layer_by_name('Decoration'):
			WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

		# collion tiles
		for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
			# Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE,TILE_SIZE)), self.collision_sprites)
			Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.collision_sprites)

		# Player
		for obj in tmx_data.get_layer_by_name('Player'):
			if obj.name == 'Start': # 初始化玩家位置
				self.player = Player(
					pos = (obj.x, obj.y),
					group = self.all_sprites,
					collision_sprites = self.collision_sprites,
					tree_sprites = self.tree_sprites,
					interaction = self.interaction_sprites,
					soil_layer = self.soil_layer,
					toggle_shop = self.toggle_shop)
			if 	obj.name == 'Bed':
				Interaction((obj.x, obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)

			if obj.name == 'Trader':
				Interaction((obj.x, obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)

		# 导入地板
		Generic(
			pos = (0,0),
			surf = pygame.image.load('../graphics/world/ground.png').convert_alpha(),
			groups = self.all_sprites,
			z = LAYERS['ground']
		)

	# 获得物品
	def player_add(self, item):

		self.player.item_inventory[item] += 1
		self.success.play()

	# 打开商店
	def toggle_shop(self):
		self.shop_active = not self.shop_active

	# 重置
	def reset(self):

		# plants
		self.soil_layer.update_plants()

		# soil
		self.soil_layer.remove_water()
		# randomize the rain
		self.raining = randint(0,10) > 7
		self.soil_layer.raining = self.raining
		if self.raining:
			self.soil_layer.water_all()

		# apple on the trees
		for tree in self.tree_sprites.sprites():
			for apple in tree.apple_sprites.sprites(): # 清除现有的苹果
				apple.kill()
			tree.create_fruit() # 创建新的苹果

		# sky
		self.sky.start_color = [255,255,255]

	# 收获
	def plant_collision(self):
		if self.soil_layer.plant_sprites:
			for plant in self.soil_layer.plant_sprites.sprites():
				if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
					self.player_add(plant.plant_type) # 获得植物
					plant.kill() # 删除植物
					# 粒子效果
					Particale(plant.rect.topleft, plant.image, self.all_sprites, z = LAYERS['main'])
					self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

	# 运行
	def run(self,dt):

		# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player) # 自定义描绘组内sprites
		
		# updates
		if self.shop_active: # 显示商店
			self.menu.update() 
		else:
			self.all_sprites.update(dt) # 更新组内所有sprites
			self.plant_collision()
		
		# 叠加层显示
		self.overlay.display()

		# rain
		if self.raining and not self.shop_active:
			self.rain.update()

		# daytime
		if not self.shop_active:
			self.sky.display(dt)

		# transition overlay
		if self.player.sleep: # 睡觉
			self.transition.play() # 播放过渡

# 相机组
class CameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__() # 父类__init__初始化
		self.display_surface = pygame.display.get_surface()
		# 相机偏移量
		self.offset = pygame.math.Vector2()

	# 自定义绘图
	def custom_draw(self, player):
		# 偏移量设置：确保玩家在屏幕中心
		self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
		self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

		# 遍历每一层，分层顺序描绘
		for layer in LAYERS.values():
			for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
				if sprite.z == layer:
					offset_rect = sprite.rect.copy()
					offset_rect.center -= self.offset
					self.display_surface.blit(sprite.image, offset_rect)

					# # anaytics
					# if sprite == player:
					# 	pygame.draw.rect(self.display_surface,'red',offset_rect,5)
					# 	hitbox_rect = player.hitbox.copy()
					# 	hitbox_rect.center = offset_rect.center
					# 	pygame.draw.rect(self.display_surface,'green',hitbox_rect,5)
					# 	target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
					# 	pygame.draw.circle(self.display_surface,'blue',target_pos,5)
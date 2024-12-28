import pygame, sys
from settings import *
from level import Level

class Game:
	def __init__(self):
		pygame.init() # 初始化pygame
		self.screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
		pygame.display.set_caption('Silk Song') # 设置游戏窗口标题
		self.clock = pygame.time.Clock() # 创建时钟对象
		self.level = Level()

	# 游戏主循环
	def run(self):
		while True:
			for event in pygame.event.get():
				# 检测游戏退出
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
  
			dt = self.clock.tick(120) / 1000 # 控制帧率
			self.level.run(dt) # 关卡运行
			pygame.display.update()

if __name__ == '__main__':
	game = Game()
	game.run()

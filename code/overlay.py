import pygame
from settings import *

class Overlay:
    def __init__(self,player):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = player

        # imports
        overlay_path = '../graphics/overlay/'
        self.tools_surf = {tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in self.player.tools}
        self.seeds_surf = {seed: pygame.image.load(f'{overlay_path}{seed}.png').convert_alpha() for seed in self.player.seeds}

    def display(self):

        self_frame = pygame.Rect(0, 0, 75, 75) # 选中边框
        # tool
        for all_tools in self.player.tools:
            tool_surf = self.tools_surf[all_tools]
            tool_rect = tool_surf.get_rect(center = OVERLAY_POSITIONS[all_tools])
            # 选中图标变化
            if all_tools == self.player.selected_tool and self.player.hand == 'tool':
                tool_surf = pygame.transform.scale_by(tool_surf,(1.05, 1.05)) # 放大选中工具
                self_frame.center = tool_rect.center
                pygame.draw.rect(self.display_surface, (255, 0, 0), self_frame, 2) # 选中图标边框
            self.display_surface.blit(tool_surf,tool_rect)
        
        # seeds
        for all_seeds in self.player.seeds:
            seed_surf = self.seeds_surf[all_seeds]
            seed_rect = seed_surf.get_rect(center = OVERLAY_POSITIONS[all_seeds])
            # 选中图标变化
            if all_seeds == self.player.selected_seed and self.player.hand == 'seed':
                seed_surf = pygame.transform.scale_by(seed_surf,(1.05, 1.05)) # 放大选中种子
                self_frame.center = seed_rect.center
                pygame.draw.rect(self.display_surface, (255, 0, 0), self_frame, 2) # 选中图标边框 
            self.display_surface.blit(seed_surf,seed_rect)


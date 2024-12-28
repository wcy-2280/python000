from os import walk
import pygame

# 得到并返回surface_list,列表中元素即图片循环形成动画
def import_folder(path):
    surface_list = []
    
    for _, _, img_files in walk(path):
        for image in img_files: # 图片名
            full_path = path + '/' + image # 组合成完整路径
            image_surf = pygame.image.load(full_path).convert_alpha() # 由路径加载图片
            surface_list.append(image_surf)

    return surface_list

def import_folder_dict(path):
    surface_dict = {}

    for _, _, img_files in walk(path):
        for image in img_files: # 图片名
            full_path = path + '/' + image # 组合成完整路径
            image_surf = pygame.image.load(full_path).convert_alpha() # 由路径加载图片
            surface_dict[image.split('.')[0]] = image_surf # 键 = 值，图片名去除.png
    
    return surface_dict        
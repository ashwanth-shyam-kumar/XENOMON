import pygame

from settings import *
from os.path import join
from os import walk
from pytmx.util_pygame import load_pygame

# import functions
def import_image(*path, alpha = True, format = 'png'): #when alpha=True each pixel can have own transparency
	full_path = join(*path) + f'.{format}' #*path unpacks the tuple of directories for formatting by join
	surf = pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()
	return surf

def import_folder(*path):
	frames = []
	for folder_path, sub_folders, image_names in walk(join(*path)): #walk traverses a path
		for image_name in sorted(image_names, key = lambda name: int(name.split('.')[0])):
			full_path = join(folder_path, image_name) #lambda is just a quick way to use a function without def
			surf = pygame.image.load(full_path).convert_alpha()
			frames.append(surf) #stores each frame in the surface
	return frames #frames are returned in correct order due to sorting

def import_folder_dict(*path):
	frames = {}
	for folder_path, sub_folders, image_names in walk(join(*path)):
		for image_name in image_names:
			full_path = join(folder_path, image_name)
			surf = pygame.image.load(full_path).convert_alpha()
			frames[image_name.split('.')[0]] = surf #maps names to their image surfaces
	return frames

def import_sub_folders(*path):
	frames = {}
	for _, sub_folders, __ in walk(join(*path)):
		if sub_folders:
			for sub_folder in sub_folders:
				frames[sub_folder] = import_folder(*path, sub_folder)
	return frames

def import_tilemap(cols, rows, *path):
	frames = {}
	surf = import_image(*path) #loads the tilemap onto a surface
	cell_width, cell_height = surf.get_width() / cols, surf.get_height() / rows
	for col in range(cols):
		for row in range(rows):
			cutout_rect = pygame.Rect(col * cell_width, row * cell_height,cell_width,cell_height)#represents one tile
			cutout_surf = pygame.Surface((cell_width, cell_height))
			cutout_surf.fill('green')
			cutout_surf.set_colorkey('green') #transparent
			cutout_surf.blit(surf, (0,0), cutout_rect) #copies the rect onto a surface
			frames[(col, row)] = cutout_surf
	return frames
def c_importer(cols, rows, *path):
	frame_dict = import_tilemap(cols, rows, *path)
	new_dict = {}
	for row, direction in enumerate(('down', 'left', 'right', 'up')): #adds an index to each element, we need both itam and index
		new_dict[direction] = [frame_dict[(col, row)] for col in range(cols)]
		new_dict[f'{direction}_idle'] = [frame_dict[(0, row)]]
	return new_dict #returns the directional animation

def character_import(*path):
	new_dict={}
	for folder_path, sub_folders, image_names in walk(join(*path)):
		for image in image_names:
			image_name=image.split('.')[0]
			new_dict[image_name]=c_importer(4,4,*path,image_name)
	return new_dict #returns dict for each character containing their animations

def coast_importer(cols, rows, *path):
	frame_dict = import_tilemap(cols, rows, *path)
	new_dict = {}
	terrains = ['grass', 'grass_i', 'sand_i', 'sand', 'rock', 'rock_i', 'ice', 'ice_i']
	sides = {
		'topleft': (0,0), 'top': (1,0), 'topright': (2,0),
		'left': (0,1), 'right': (2,1), 'bottomleft': (0,2),
		'bottom': (1,2), 'bottomright': (2,2)}
	for index, terrain in enumerate(terrains):
		new_dict[terrain] = {} #hold tiles of each terrain
		for key, pos in sides.items():
			new_dict[terrain][key] = [frame_dict[(pos[0] + index * 3, pos[1] + row)] for row in range(0,rows, 3)]
	return new_dict

def monster_importer(cols,rows,*path):
	monster_dict={}
	for folder_path,sub_folder,image_names in walk(join(*path)):
		for image in image_names:
			image_name=image.split('.')[0]
			monster_dict[image_name]={}
			frame_dict=import_tilemap(cols,rows,*path,image_name)
			for row,key in enumerate(('idle',"attack")):   #gives index and value
				monster_dict[image_name][key]=[frame_dict[(col,row)] for col in range(cols)] #stores animation frames
	return monster_dict

#interaction
def check(radius,entity,target,tolerance=30):
	relation=vector(target.rect.center)-vector(entity.rect.center)
	if relation.length()<radius: #magnitude of vector
		if entity.facing_direction == 'left' and relation.x<0 and abs(relation.y)<tolerance or\
			entity.facing_direction == 'right' and relation.x>0 and abs(relation.y)<tolerance or\
			entity.facing_direction == 'up' and relation.y<0 and abs(relation.x)<tolerance or\
			entity.facing_direction == 'down' and relation.y>0 and abs(relation.x)<tolerance:
			return True

def map_importer(*path):
	tmx_dict={}
	for folder_path,sub_folders,file_names in walk(join(*path)):
		for file in file_names:
			tmx_dict[file.split('.')[0]]=load_pygame(join(folder_path,file)) #from pytmx
	return tmx_dict

def outline(frame_dict,width):
	outline_frame_dict={}
	for monster,monster_frames in frame_dict.items():
		outline_frame_dict[monster]={} #outline for each monster
		for state,frames in monster_frames.items():
			outline_frame_dict[monster][state]=[] #idle or active
			for frame in frames:
				new_surf=pygame.Surface(vector(frame.get_size()+vector(width*2)),pygame.SRCALPHA) #enables transparency
				new_surf.fill((0,0,0,0)) #since black is removed, that area is void, so we make it transparent
				white_frame=pygame.mask.from_surface(frame).to_surface()  #if there are pixels, white. no pixels, black
				white_frame.set_colorkey('black')  #getting rid of black pixels
				new_surf.blit(white_frame,(0,0))     #to cover all 8 directions
				new_surf.blit(white_frame,(width,0))
				new_surf.blit(white_frame,(width*2,0))
				new_surf.blit(white_frame,(width*2,width))
				new_surf.blit(white_frame,(width*2,width*2))
				new_surf.blit(white_frame,(width,width*2))
				new_surf.blit(white_frame,(0,width*2))
				new_surf.blit(white_frame,(0,width))
				outline_frame_dict[monster][state].append(new_surf)
	return outline_frame_dict

def bar(surface,rect,value,max_value,colour,bg_colour,radius=1):
	ratio=rect.width/max_value
	bg_rect=rect.copy()
	progress=max(0,min(rect.width,value*ratio))
	progress_rect=pygame.FRect(rect.topleft,(progress,rect.height))
	pygame.draw.rect(surface,bg_colour,bg_rect,0,radius)
	pygame.draw.rect(surface,colour,progress_rect,0,radius) #essentially one rect on top of another

def attack_importer(*path):
	attack_dict={}
	for folder_path,_,image_names in walk(join(*path)):
		for image in image_names:
			image_name=image.split('.')[0]
			attack_dict[image_name]=list(import_tilemap(4,1,folder_path,image_name).values())
	return attack_dict

def audio_importer(*path):
	files={}
	for folder_path,_,file_names in walk(join(*path)):
		for file_name in file_names:
			full_path=join(folder_path,file_name)
			files[file_name.split('.')[0]]=pygame.mixer.Sound(full_path)
	return files #maps file names to audio







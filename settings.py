import pygame
from pygame.math import Vector2 as vector
from sys import exit
WIDTH,HEIGHT=1200,680
TILE_SIZE=64
Animation_speed=6
BATTLE_WIDTH=4
COLOURS = {
	'white': '#f4fefa',
	'pure white': '#ffffff',
	'dark': '#2b292c',
	'light': '#c8c8c8',
	'gray': '#3a373b',
	'gold': '#ffd700',
	'light-gray': '#4b484d',
	'Fire':'#f8a060',
	'Water':'#50b0d8',
	'Grass': '#64a990',
	'black': '#000000',
	'red': '#f03131',
	'blue': '#66d7ee',
	'Normal': '#ffffff',
	'dark white': '#f0f0f0'
}
WORLD_LAYERS = {
	'water': 0,
	'background': 1,
	'shadow': 2,
	'main': 3,
	'top': 4
}
BATTLE_POSITIONS = {
	'left': {'top': (360, 320),'bottom': (360, 520)},
	'right': {'top': (830, 320),'bottom': (830, 520)}
}

BATTLE_LAYERS =  {
	'outline': 0,
	'name': 1,
	'monster': 2,
	'effects': 3,
	'overlay': 4
}

BATTLE_CHOICES = {
	'full': {
		'fight':  {'pos' : vector(30, -60), 'icon': 'sword'},
		'defend': {'pos' : vector(40, -20), 'icon': 'shield'},
		'switch': {'pos' : vector(40, 20), 'icon': 'arrows'},
		'catch':  {'pos' : vector(30, 60), 'icon': 'hand'}},

	'limited': {
		'fight':  {'pos' : vector(30, -40), 'icon': 'sword'},
		'defend': {'pos' : vector(40, 0), 'icon': 'shield'},
		'switch': {'pos' : vector(30, 40), 'icon': 'arrows'}}
}

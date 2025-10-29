import sprites
from settings import *
from entities import entity
from support import import_image
class Allsprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface=pygame.display.get_surface()
        self.offset=vector()
        self.shadow_surf=import_image('graphics','shadow')
        self.notice_surf=import_image('graphics','ui','notice')
    def draw(self,player):
        self.offset.x=-(player.rect.centerx-WIDTH/2)
        self.offset.y=-(player.rect.centery-HEIGHT/2)

        background_sprites=[sprite for sprite in self if sprite.z<WORLD_LAYERS['main']]
        main_sprites=sorted([sprite for sprite in self if sprite.z==WORLD_LAYERS['main']],key=lambda sprite:sprite.y_sorted)
        foreground_sprites=[sprite for sprite in self if sprite.z>WORLD_LAYERS['main']]
        for layer in (background_sprites,main_sprites,foreground_sprites):
            for sprite in layer:
                self.shadow_surf_rect=self.shadow_surf.get_frect(center=sprite.rect.midbottom)
                if isinstance(sprite,entity):                                     #detects whether the object is entity
                    self.display_surface.blit(self.shadow_surf,self.shadow_surf_rect.topleft+self.offset)
                self.display_surface.blit(sprite.image,sprite.rect.topleft+self.offset)
                if sprite == player and player.noticed:
                    rect = self.notice_surf.get_frect(midbottom = sprite.rect.midtop)
                    self.display_surface.blit(self.notice_surf, rect.topleft + self.offset)
class BattleSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface=pygame.display.get_surface()
    def draw(self,current_monster_sprite,side,mode,target_index,player_sprites,opponent_sprites):
        #get pos
        sprite_group=opponent_sprites if side=='opponent' else player_sprites
        sprites={sprite.pos_index:sprite for sprite in sprite_group}
        monster_sprite=sprites[list(sprites.keys())[target_index]] if sprites else None

        for sprite in sorted(self,key=lambda sprite:sprite.z):
            if sprite.z==BATTLE_LAYERS['outline']:
                if sprite.monster_sprite==current_monster_sprite and not(mode=='target' and side =='player') or\
                        sprite.monster_sprite==monster_sprite and sprite.monster_sprite.entity==side and mode and mode=='target':
                    self.display_surface.blit(sprite.image,sprite.rect)
            else:
                self.display_surface.blit(sprite.image,sprite.rect)



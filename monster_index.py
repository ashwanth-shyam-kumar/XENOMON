import pygame.display
from support import bar
from settings import *
from game_data import MONSTER_DATA,ATTACK_DATA
class MonsterIndex:
    def __init__(self,monsters,fonts,monster_frames):
        self.display_surface=pygame.display.get_surface()
        self.fonts=fonts
        self.monsters=monsters
        self.frame_index=0

        #frames
        self.icon_frames=monster_frames['icons']
        self.monster_frames=monster_frames['monsters']
        self.ui_frames=monster_frames['ui']

        #tint surf
        self.tint_surf=pygame.Surface((WIDTH,HEIGHT))
        self.tint_surf.set_alpha(200)

        #dimensions
        self.main_rect=pygame.FRect(0,0,WIDTH*0.7,HEIGHT*0.8).move_to(center=(WIDTH/2,HEIGHT/2))

        #list
        self.visible_items=6                 #how many monsters at a time
        self.list_width=self.main_rect.width*0.35
        self.item_height=self.main_rect.height/self.visible_items
        self.index=0
        self.selected_index=None

        #max values
        self.max_stats={}
        for data in MONSTER_DATA.values():
            for stat,value in data['stats'].items():
                if stat!='element':
                    if stat not in self.max_stats:
                        self.max_stats[stat]=value
                    else:
                        self.max_stats[stat]=value if value>self.max_stats[stat] else self.max_stats[stat]
        self.max_stats['Health']=self.max_stats.pop('max_health')   #to remove max part
        self.max_stats['Energy']=self.max_stats.pop('max_energy')

    def input(self):
        keys=pygame.key.get_just_pressed()
        if keys[pygame.K_UP]:
            self.index-=1
        if keys[pygame.K_DOWN]:
            self.index+=1
        if keys[pygame.K_SPACE]:
            if self.selected_index!=None:
                selected_monster=self.monsters[self.selected_index]
                current_monster=self.monsters[self.index]
                self.monsters[self.index]=selected_monster
                self.monsters[self.selected_index]=current_monster
                self.selected_index=None
            else:
                self.selected_index=self.index

        self.index=self.index%len(self.monsters)
    def display_list(self):
        bg_rect=pygame.FRect(self.main_rect.topleft,(self.list_width,self.main_rect.height))
        pygame.draw.rect(self.display_surface,COLOURS['gray'],bg_rect,0,0,12,0,12,0)
        v_offset=0 if self.index<self.visible_items else -(self.index-self.visible_items+1)*self.item_height
        for index,monster in self.monsters.items():
            #colours
            bg_colour=COLOURS['gray'] if self.index!=index else COLOURS['light']   #to show selection
            text_colour=COLOURS['white'] if self.selected_index!=index else COLOURS['gold']
            top=self.main_rect.top+index*self.item_height+v_offset
            item_rect=pygame.FRect(self.main_rect.left,top,self.list_width,self.item_height)

            text_surf=self.fonts['regular'].render(monster.name,False,text_colour)
            text_rect=text_surf.get_frect(midleft=item_rect.midleft+vector(90,0))

            icon_surf=self.icon_frames[monster.name]
            icon_rect=icon_surf.get_frect(center=item_rect.midleft+vector(45,0))

            if item_rect.colliderect(self.main_rect):
                #check corners
                if item_rect.collidepoint(self.main_rect.topleft):
                    pygame.draw.rect(self.display_surface,bg_colour,item_rect,0,0,12)
                elif item_rect.collidepoint(self.main_rect.bottomleft+vector(1,-1)):
                    pygame.draw.rect(self.display_surface,bg_colour,item_rect,0,0,0,0,12,0)
                else:
                    pygame.draw.rect(self.display_surface,bg_colour,item_rect)

                self.display_surface.blit(text_surf,text_rect)
                self.display_surface.blit(icon_surf,icon_rect)

        #lines
        for i in range(1,min(self.visible_items,len(self.monsters))):
            left=self.main_rect.left
            right=self.main_rect.left+self.list_width
            y=self.main_rect.top+self.item_height*i
            pygame.draw.line(self.display_surface,COLOURS['light-gray'],(left,y),(right,y))
        #shadow
        shadow_surf=pygame.Surface((4,self.main_rect.height))
        shadow_surf.set_alpha(100)
        self.display_surface.blit(shadow_surf,(self.main_rect.left+self.list_width-4,self.main_rect.top))

    def display_main(self,dt):
        #data
        monster=self.monsters[self.index]
        #main bg
        rect=pygame.FRect(self.main_rect.left+self.list_width,self.main_rect.top,self.main_rect.width-self.list_width,self.main_rect.height)
        pygame.draw.rect(self.display_surface,COLOURS['dark'],rect,0,12,0,12,0)

        #monster display
        top_rect=pygame.FRect(rect.topleft,(rect.width,rect.height*0.4))
        pygame.draw.rect(self.display_surface,COLOURS[monster.element],top_rect,0,0,0,12)

        #animation
        self.frame_index+=Animation_speed*dt
        monster_surf=self.monster_frames[monster.name]['idle'][int(self.frame_index)%len(self.monster_frames[monster.name]['idle'])]
        monster_rect=monster_surf.get_frect(center=top_rect.center)
        self.display_surface.blit(monster_surf,monster_rect)

        #name
        name_surf=self.fonts['bold'].render(monster.name,False,COLOURS['white'])
        name_rect=name_surf.get_frect(topleft=top_rect.topleft+vector(10,10))
        self.display_surface.blit(name_surf,name_rect)

        #level
        level_surf=self.fonts['regular'].render(f'Lvl: {monster.level}',False,COLOURS['white'])
        level_rect=level_surf.get_frect(bottomleft=top_rect.bottomleft+vector(10,-16))
        self.display_surface.blit(level_surf,level_rect)

        #xp bar
        bar(
            surface=self.display_surface,
            rect=pygame.FRect(level_rect.bottomleft,(100,4)),
            value=monster.xp,
            max_value=monster.level_up,
            colour=COLOURS['white'],
            bg_colour=COLOURS['dark']
        )

        #element
        element_surf=self.fonts['regular'].render(monster.element,False,COLOURS['white'])
        element_rect=element_surf.get_frect(bottomright=top_rect.bottomright+vector(-10,-10))
        self.display_surface.blit(element_surf,element_rect)

        #health,energy
        bar_data={
            'width':rect.width*0.45,
            'height':30,
            'top':top_rect.bottom+rect.width*0.03,
            'left':rect.left+rect.width/4,
            'right':rect.left+rect.width*3/4
        }
        health_rect=pygame.FRect((0,0),(bar_data['width'],bar_data['height'])).move_to(midtop=(bar_data['left'],bar_data['top']))
        bar(
            surface=self.display_surface,
            rect=health_rect,
            value=monster.health,
            max_value=monster.get_stat('max_health'),
            colour=COLOURS['red'],
            bg_colour=COLOURS['black'],
            radius=2
        )
        hp_text = self.fonts['regular'].render(f"HP: {int(monster.health)}/{int(monster.get_stat('max_health'))}", False, COLOURS['white'])
        hp_rect=hp_text.get_frect(midleft=health_rect.midleft+vector(10,0))
        self.display_surface.blit(hp_text,hp_rect)

        energy_rect=pygame.FRect((0,0),(bar_data['width'],bar_data['height'])).move_to(midtop=(bar_data['right'],bar_data['top']))
        bar(
            surface=self.display_surface,
            rect=energy_rect,
            value=monster.energy,
            max_value=monster.get_stat('max_energy'),
            colour=COLOURS['blue'],
            bg_colour=COLOURS['black'],
            radius=2
        )
        ep_text = self.fonts['regular'].render(f"EP: {int(monster.energy)}/{int(monster.get_stat('max_energy'))}", False, COLOURS['white'])
        ep_rect=ep_text.get_frect(midleft=energy_rect.midleft+vector(10,0))
        self.display_surface.blit(ep_text,ep_rect)

        #info
        sides={'left':health_rect.left,'right':energy_rect.left}
        info_height=rect.bottom-health_rect.bottom

        #stats
        stats_rect=pygame.FRect(sides['left'],health_rect.bottom,health_rect.width,info_height).inflate(0,-60).move(0,15)
        stats_text_surf=self.fonts['regular'].render('Stats',False,COLOURS['white'])
        stats_text_rect=stats_text_surf.get_frect(bottomleft=stats_rect.topleft)
        self.display_surface.blit(stats_text_surf,stats_text_rect)

        monster_stats=monster.get_stats()
        stat_height=stats_rect.height/len(monster_stats)
        for index,(stat,value) in enumerate(monster_stats.items()):
            single_stat_rect = pygame.FRect(stats_text_rect.left, stats_rect.top + index * stat_height, stats_rect.width, stat_height)
            #icon
            icon_surf=self.ui_frames[stat]
            icon_rect=icon_surf.get_frect(midleft=single_stat_rect.midleft+vector(5,0))
            self.display_surface.blit(icon_surf,icon_rect)

            #text
            text_surf=self.fonts['regular'].render(stat,False,COLOURS['white'])
            text_rect=text_surf.get_frect(topleft=icon_rect.topleft+vector(30,-10))
            self.display_surface.blit(text_surf,text_rect)

            #bar
            bar_rect=pygame.FRect((text_rect.left,text_rect.bottom+2),(single_stat_rect.width-(text_rect.left-single_stat_rect.left),4))
            bar(
                surface=self.display_surface,
                rect=bar_rect,
                value=value,
                max_value=self.max_stats[stat]*monster.level,
                colour=COLOURS['white'],
                bg_colour=COLOURS['black']
            )
        #abilities
        ability_rect=stats_rect.copy().move_to(left=sides['right'])
        ability_text_surf=self.fonts['regular'].render('Abilities',False,COLOURS['white'])
        ability_text_rect=ability_text_surf.get_frect(bottomleft=ability_rect.topleft)
        self.display_surface.blit(ability_text_surf,ability_text_rect)

        for index,ability in enumerate(monster.get_abilities()):
            element=ATTACK_DATA[ability]['element']
            text_surf=self.fonts['regular'].render(ability,False,COLOURS['black'])
            x=ability_rect.left+index%2*ability_rect.width/2
            y=ability_rect.top+20+int(index/2)*(text_surf.get_height()+20)
            rect=text_surf.get_frect(topleft=(x,y))
            pygame.draw.rect(self.display_surface,COLOURS[element],rect.inflate(10,10),0,4)
            self.display_surface.blit(text_surf,rect)

    def update(self,dt):
        self.input()
        self.display_surface.blit(self.tint_surf,(0,0))
        self.display_list()
        self.display_main(dt)

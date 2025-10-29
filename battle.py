import pygame

from settings import *
from sprites import MonsterSprite,MonsterNameSprite,MonsterLevelSprite,MonsterStatsSprite,MonsterOutlineSprite,AttackSprite,TimedSprite
from groups import BattleSprites
from game_data import ATTACK_DATA
from support import bar
from timer import Timer
from random import choice

class Battle:
    def __init__(self,player_monsters,opponent_monsters,monster_frames,bg_surf,fonts,end_battle,character,sounds):
        self.display_surface=pygame.display.get_surface()
        self.bg_surf=bg_surf
        self.monster_frames=monster_frames
        self.fonts=fonts
        self.monster_data={'player':player_monsters,'opponent':opponent_monsters}
        self.battle_over=False
        self.end_battle=end_battle
        self.character=character
        self.sounds=sounds
        #timers
        self.timers={
            'opponent delay':Timer(600,func=self.opponent_attack)
        }

        #GROUPS
        self.battle_sprites=BattleSprites()
        self.player_sprites=pygame.sprite.Group()
        self.opponent_sprites=pygame.sprite.Group()

        #control
        self.current_monster=None
        self.selection_mode=None
        self.selected_attack=None
        self.selection_side='player'
        self.indices={
            'general':0,
            'monster':0,
            'attacks':0,
            'switch':0,
            'target':0
        }

        self.setup()

    def setup(self):
       for entity, monster_dict in self.monster_data.items():
           # Add up to 2 monsters per side
          active_count = 0
          pos_index = 0

          for index in sorted(monster_dict.keys()):
             monster = monster_dict[index]
             monster.fainted = False
             if monster.health <= 0:
                continue  # Skip dead monsters

             self.create_monster(monster, index, pos_index, entity)
             pos_index += 1
             active_count += 1

             if active_count >= 2:
                break

        #  Clean up dead opponent monsters with index <= 1
          if entity == 'opponent':
             for k in list(self.monster_data['opponent'].keys()):
                if k <= 1:
                    del self.monster_data['opponent'][k]

    def create_monster(self,monster,index,pos_index,entity):  #pos index indicates order in battle
        monster.paused=False
        frames=self.monster_frames['monsters'][monster.name]
        outline_frames=self.monster_frames['outlines'][monster.name]
        if entity=='player':
            pos=list(BATTLE_POSITIONS['left'].values())[pos_index]
            groups=(self.battle_sprites,self.player_sprites)
            frames={state:[pygame.transform.flip(frame,True,False) for frame in frames] for state,frames in frames.items()}
            outline_frames = {state: [pygame.transform.flip(frame, True, False) for frame in frames] for state, frames in outline_frames.items()}
        #above line for flipping images
        else:
            pos=list(BATTLE_POSITIONS['right'].values())[pos_index]
            groups=(self.battle_sprites,self.opponent_sprites)

        monster_sprite=MonsterSprite(pos,frames,groups,monster,index,pos_index,entity,self.apply_attack,self.create_monster)
        MonsterOutlineSprite(monster_sprite,self.battle_sprites,outline_frames)


        #ui
        name_pos=monster_sprite.rect.midleft+vector(16,-70) if entity=='player' else monster_sprite.rect.midright+vector(-40,-70)
        name_sprite=MonsterNameSprite(name_pos,monster_sprite,self.battle_sprites,self.fonts['regular'])
        level_pos=name_sprite.rect.bottomleft if entity=='player' else name_sprite.rect.bottomright
        MonsterLevelSprite(entity,level_pos,monster_sprite,self.battle_sprites,self.fonts['small'])
        MonsterStatsSprite(monster_sprite.rect.midbottom+vector(0,20),monster_sprite,(150,48),self.battle_sprites,self.fonts['small'])

    def input(self):
        if self.selection_mode and self.current_monster:
            keys = pygame.key.get_just_pressed()
            match self.selection_mode:
                case 'general': limiter = len(BATTLE_CHOICES['full'])
                case 'attacks': limiter = len(self.current_monster.monster.get_abilities(all = False))
                case 'switch': limiter = len(self.available_monsters)
                case 'target': limiter = len(self.opponent_sprites) if self.selection_side == 'opponent' else len(self.player_sprites)
            if limiter == 0:
                return  #Nothing to choose, skip input processing this frame

            if keys[pygame.K_DOWN]:
                self.indices[self.selection_mode] = (self.indices[self.selection_mode] + 1) % limiter
            if keys[pygame.K_UP]:
                self.indices[self.selection_mode] = (self.indices[self.selection_mode] - 1) % limiter
            if keys[pygame.K_SPACE]:
                if self.selection_mode == 'switch':
                    index, new_monster = list(self.available_monsters.items())[self.indices['switch']]
                    self.current_monster.kill()
                    self.create_monster(new_monster, index, self.current_monster.pos_index, 'player')
                    self.selection_mode = None
                    self.update_all('resume')

                if self.selection_mode == 'target':
                    sprite_group = self.opponent_sprites if self.selection_side == 'opponent' else self.player_sprites
                    sprites = {sprite.pos_index: sprite for sprite in sprite_group}
                    monster_sprite = sprites[list(sprites.keys())[self.indices['target']]]

                    if self.selected_attack:
                        self.current_monster.activate_attack(monster_sprite, self.selected_attack)
                        self.selected_attack, self.current_monster, self.selection_mode = None, None, None
                    else:
                        if not self.character:  #Only allow catching in wild battles
                           if monster_sprite.monster.health < monster_sprite.monster.get_stat('max_health') * 0.3:
                               self.monster_data['player'][len(self.monster_data['player'])] = monster_sprite.monster
                               monster_sprite.delayed_kill(None)
                               self.current_monster = None
                               self.selection_mode = None
                               self.update_all('resume')
                           else:
                               TimedSprite(monster_sprite.rect.center, self.monster_frames['ui']['cross'], self.battle_sprites, 1000)
                               self.current_monster = None
                               self.selection_mode = None
                               self.update_all('resume')
                if self.selection_mode == 'attacks':
                    self.selection_mode = 'target'
                    self.selected_attack = self.current_monster.monster.get_abilities(all = False)[self.indices['attacks']]
                    self.selection_side = ATTACK_DATA[self.selected_attack]['target']

                if self.selection_mode == 'general':
                    if self.indices['general'] == 0:
                        self.selection_mode = 'attacks'

                    if self.indices['general'] == 1:
                        self.current_monster.monster.defending = True
                        self.update_all('resume')
                        self.current_monster, self.selection_mode = None, None
                        self.indices['general'] = 0

                    if self.indices['general'] == 2:
                        self.selection_mode = 'switch'

                    if self.indices['general'] == 3:
                        self.selection_mode = 'target'
                        self.selection_side = 'opponent'

                self.indices = {k: 0 for k in self.indices}

            if keys[pygame.K_ESCAPE]:
                if self.selection_mode in ('attacks', 'switch', 'target'):
                    self.selection_mode = 'general'

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def check_active(self):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if monster_sprite.monster.health <= 0:
                  continue  # Don't give turn to dead monsters
            if monster_sprite.monster.initiative >= 100:
                monster_sprite.monster.defending = False
                self.update_all('pause')
                monster_sprite.monster.initiative = 0
                monster_sprite.set_highlight(True)
                self.current_monster = monster_sprite
                if self.player_sprites in monster_sprite.groups():
                    self.selection_mode = 'general'
                else:
                    self.timers['opponent delay'].activate()
                break

    def update_all(self,option):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            monster_sprite.monster.paused=True if option=='pause' else False

    def apply_attack(self,target_sprite,attack,amount):
        AttackSprite(target_sprite.rect.center,self.monster_frames['attacks'][ATTACK_DATA[attack]['animation']],self.battle_sprites)
        self.sounds[ATTACK_DATA[attack]['animation']].play()

        attack_element=ATTACK_DATA[attack]['element']
        target_element=target_sprite.monster.element

        #Super effective
        if attack_element=='Fire' and target_element=='Grass' or\
           attack_element=='Grass' and target_element=='Water' or\
           attack_element=='Water' and target_element=='Fire':
            amount*=2

        #Resistance
        if attack_element=='Fire' and target_element=='Water' or\
           attack_element=='Grass' and target_element=='Fire' or\
           attack_element=='Water' and target_element=='Grass':
            amount*=0.5

        target_defense=1-target_sprite.monster.get_stat('Defense')/1750
        if target_sprite.monster.defending:
            target_defense-=0.2
        target_defense=max(0,min(1,target_defense))

        target_sprite.monster.health-=amount*target_defense
        self.check_death()
        if self.battle_over:
            return  # Don't resume or give turns
        self.current_monster = None
        self.selection_mode = None
        self.update_all('resume')



    def check_death(self):
       death_occurred = False

       for monster_sprite in self.opponent_sprites.sprites() + self.player_sprites.sprites():
           monster = monster_sprite.monster

           if monster.health <= 0 and not getattr(monster, 'fainted', False):
               death_occurred = True
               monster.fainted = True  # Mark this monster so it doesn't get XP again

            # Determine replacement
               if self.player_sprites in monster_sprite.groups():
                   active_monsters = [(sprite.index, sprite.monster) for sprite in self.player_sprites.sprites()]
                   available_monsters = [(index, m) for index, m in self.monster_data['player'].items()
                                      if m.health > 0 and (index, m) not in active_monsters]

                   new_monster_data = (available_monsters[0][1], available_monsters[0][0],
                                    monster_sprite.pos_index, 'player') if available_monsters else None
               else:
                   if self.monster_data['opponent']:
                       new_monster = self.monster_data['opponent'][min(self.monster_data['opponent'])]
                       new_monster_data = (new_monster, monster_sprite.index,
                                        monster_sprite.pos_index, 'opponent')
                       del self.monster_data['opponent'][min(self.monster_data['opponent'])]
                   else:
                       new_monster_data = None

            # XP gain — once per monster death
               xp_amount = monster.level * 100 / max(1, len(self.player_sprites))
               for player_sprite in self.player_sprites:
                  player_sprite.monster.update_xp(xp_amount)

               self.current_monster = None
               self.selection_mode = None

               if new_monster_data is None:
                   monster_sprite.kill()
               else:
                   monster_sprite.delayed_kill(new_monster_data)

       return death_occurred


    def opponent_attack(self):
        if not self.current_monster or self.current_monster.monster.health <= 0:
            return  # no monster to act — skip safely
        ability = choice(self.current_monster.monster.get_abilities())
        if ATTACK_DATA[ability]['target'] == 'player':
            targets = self.opponent_sprites.sprites()
        else:
            targets = self.player_sprites.sprites()
        if not targets:
            return  # no one to attack

        random_target = choice(targets)
        if self.current_monster.monster.energy>ATTACK_DATA[ability]['cost']:
            self.current_monster.activate_attack(random_target, ability)
        else:
            return

    def check_end_battle(self):
        #opponents have been defeated
        if len(self.opponent_sprites)==0 and not self.battle_over:
            self.battle_over=True
            self.end_battle(self.character)
            for monster in self.monster_data['player'].values():
                monster.initiative=0

        #player
        if len(self.player_sprites)==0 and not self.battle_over:
            self.battle_over = True
            self.end_battle(self.character, player_lost=True)  # call with player_lost



    #ui
    def draw_ui(self):
        if self.current_monster and self.current_monster.entity == 'player':
            if self.selection_mode=='general':
                self.draw_general()
            if self.selection_mode=='attacks':
                self.draw_attacks()
            if self.selection_mode=='switch':
                self.draw_switch()
    def draw_general(self):
        for index,(option,data_dict) in enumerate(BATTLE_CHOICES['full'].items()):
            if index==self.indices['general']:
                surf=self.monster_frames['ui'][f"{data_dict['icon']}_highlight"]
            else:
                surf=pygame.transform.grayscale(self.monster_frames['ui'][data_dict['icon']]) #for graying out
            rect=surf.get_frect(center=self.current_monster.rect.midright+data_dict['pos'])
            self.display_surface.blit(surf,rect)

    def draw_attacks(self):
        # data
        abilities = self.current_monster.monster.get_abilities(all = False)
        width, height = 150, 200
        visible_attacks = 4
        item_height = height / visible_attacks
        v_offset = 0 if self.indices['attacks'] < visible_attacks else -(self.indices['attacks'] - visible_attacks + 1) * item_height

        # bg
        bg_rect = pygame.FRect((0,0), (width,height)).move_to(midleft = self.current_monster.rect.midright + vector(20,0))
        pygame.draw.rect(self.display_surface, COLOURS['white'], bg_rect, 0, 5)

        for index, ability in enumerate(abilities):
            selected = index == self.indices['attacks']

            # text
            if selected:
                element = ATTACK_DATA[ability]['element']
                text_color = COLOURS[element] if element!= 'Normal' else COLOURS['black']
            else:
                text_color = COLOURS['light']
            text_surf  = self.fonts['regular'].render(ability, False, text_color)

            # rect
            text_rect = text_surf.get_frect(center = bg_rect.midtop + vector(0, item_height / 2 + index * item_height + v_offset))
            text_bg_rect = pygame.FRect((0,0), (width, item_height)).move_to(center = text_rect.center)

            # draw
            if bg_rect.collidepoint(text_rect.center):
                if selected:
                    if text_bg_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(self.display_surface, COLOURS['dark white'], text_bg_rect,0,0,5,5)
                    elif text_bg_rect.collidepoint(bg_rect.midbottom + vector(0,-1)):
                        pygame.draw.rect(self.display_surface, COLOURS['dark white'], text_bg_rect,0,0,0,0,5,5)
                    else:
                        pygame.draw.rect(self.display_surface, COLOURS['dark white'], text_bg_rect)

                self.display_surface.blit(text_surf, text_rect)

    def draw_switch(self):
        #data
        width,height=300,320
        visible_monsters=4
        item_height=height/visible_monsters
        v_offset=0 if self.indices['switch']<visible_monsters else -(self.indices['switch']-visible_monsters+1)*item_height
        bg_rect=pygame.FRect((0,0),(width,height)).move_to(midleft=self.current_monster.rect.midright+vector(20,0))

        pygame.draw.rect(self.display_surface,COLOURS['white'],bg_rect,0,5)

        #monsters
        active_monsters=[(monster_sprite.index,monster_sprite.monster) for monster_sprite in self.player_sprites]
        self.available_monsters={index:monster for index, monster in self.monster_data['player'].items() if (index,monster) not in active_monsters and monster.health>0}
        for index,monster in enumerate(self.available_monsters.values()):
            selected=index==self.indices['switch']
            item_bg_rect=pygame.FRect((0,0),(width,item_height)).move_to(midleft=(bg_rect.left,bg_rect.top+item_height/2+index*item_height+v_offset))

            icon_surf=self.monster_frames['icons'][monster.name]
            icon_rect=icon_surf.get_frect(midleft=bg_rect.topleft+vector(10,item_height/2+index*item_height+v_offset))
            text_surf=self.fonts['regular'].render(f'{monster.name} ({monster.level})',False,COLOURS['red'] if selected else COLOURS['black'])
            text_rect=text_surf.get_frect(topleft=(bg_rect.left+90,icon_rect.top))

            if selected:
                if item_bg_rect.collidepoint(bg_rect.topleft):
                    pygame.draw.rect(self.display_surface,COLOURS['dark white'],item_bg_rect,0,0,5,5)
                elif item_bg_rect.collidepoint(bg_rect.midbottom+vector(0,-1)):
                    pygame.draw.rect(self.display_surface,COLOURS['dark white'],item_bg_rect,0,0,0,0,5,5)
                else:
                    pygame.draw.rect(self.display_surface,COLOURS['dark white'],item_bg_rect)

            if bg_rect.collidepoint(item_bg_rect.center):
                for surf,rect in ((icon_surf,icon_rect),(text_surf,text_rect)):
                    self.display_surface.blit(surf,rect)
                health_rect=pygame.FRect((text_rect.bottomleft+vector(0,4)),(100,4))
                energy_rect=pygame.FRect((health_rect.bottomleft+vector(0,2)),(100,4))
                bar(self.display_surface,health_rect,monster.health,monster.get_stat('max_health'),COLOURS['red'],COLOURS['black'])
                bar(self.display_surface,energy_rect,monster.energy,monster.get_stat('max_energy'),COLOURS['blue'],COLOURS['black'])
    def update(self,dt):
        self.input()
        self.update_timers()
        self.battle_sprites.update(dt)

        death_happened = self.check_death()
        if death_happened:
           self.update_all('resume')

        self.check_active()
        self.check_end_battle()

        self.display_surface.blit(self.bg_surf,(0,0))
        self.battle_sprites.draw(self.current_monster,self.selection_side,self.selection_mode,self.indices['target'],self.player_sprites,self.opponent_sprites)
        self.draw_ui()

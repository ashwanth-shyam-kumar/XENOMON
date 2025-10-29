import pygame.display
from game_data import *
from pytmx.util_pygame import load_pygame
from os.path import join
from entities import Player,Character
from settings import *
from sprites import Sprite, AnimatedSprite,GrassSprite,BorderSprite,CollidableSprite,TransitionSprite
from groups import Allsprites
from support import *
from dialog import DialogTree
from monster import Monster
from monster_index import MonsterIndex
from battle import Battle
from timer import Timer
from random import randint
from evolution import Evolution
from database import DBManager

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption('XENOMON')
        self.clock=pygame.time.Clock()

        self.db_manager = DBManager(
            host='Localhost',
            user='root',
            password='sangeetha',
            database='xenomon_game')
        self.player_id = 1
        self.pre_battle_snapshot = None #Hold monsters & position before battle
        self.pre_battle_position = None
        # ------------------------------------------ #
        self.encounter_timer=Timer(2000,func=self.monster_encounter)

        self.player_monsters = self.load_player_progress()
        #groups
        self.all_sprites=Allsprites()
        self.collidable_sprites=pygame.sprite.Group()
        self.trainer_sprites=pygame.sprite.Group()
        self.transition_sprite=pygame.sprite.Group()
        self.grass_sprites=pygame.sprite.Group()

        #screen tint
        self.transition_target=None
        self.tint_surf=pygame.Surface((WIDTH,HEIGHT))
        self.tint_mode='untint'
        self.tint_progress=0
        self.tint_direction=-1
        self.tint_speed=600

        self.import_assets()
        saved_pos = self.load_player_position()
        start_pos = 'saved' if saved_pos else 'house'
        self.trainer_defeat_status = self.db_manager.load_trainer_status(self.player_id)

        self.setup(self.tmx_maps['world'], start_pos)

        self.audio['overworld'].play(-1)  #to play continuously

        #overlays
        self.dialog_tree=None
        self.monster_index=MonsterIndex(self.player_monsters,self.fonts,self.monster_frames)
        self.index_open=False
        self.battle=None
        self.evolution=None

    def load_player_progress(self):
        try:
            pos, monsters_data = self.db_manager.load_player_progress(self.player_id)
            print(f"DEBUG: Loaded position: {pos}")
            print(f"DEBUG: Loaded monsters: {monsters_data}")
            if monsters_data:
                player_monsters = {}
                for i, (name, level, xp, fainted, health, energy) in enumerate(monsters_data):
                    monster = Monster(name, level)
                    monster.xp = xp
                    monster.fainted = fainted
                    max_health = monster.get_stat('max_health')
                    max_energy = monster.get_stat('max_energy')
                    monster.health = max(0, min(health, max_health))  # Clamp between 0 and max
                    monster.energy = max(0, min(energy, max_energy))  # Clamp between 0 and max
                    player_monsters[i] = monster
                return player_monsters
            else:
                # No previous save, use defaults
                return {0: Monster('Emberillo', 7), 1: Monster('Bramblet', 7), 2: Monster('Finlet', 7)}
        except Exception as e:
            print(f"DEBUG: Error loading progress: {e}")
            return {0: Monster('Emberillo', 7), 1: Monster('Bramblet', 7), 2: Monster('Finlet', 7)}

    def load_player_position(self):
        try:
            pos, _ = self.db_manager.load_player_progress(self.player_id)
            return pos
        except Exception as e:
            print(f"DEBUG: Error loading position: {e}")
            return None

    def import_assets(self):
        self.tmx_maps=map_importer('data')
        self.overworld_frames={
            'water':import_folder('Graphics','water'),
            'coast':coast_importer(24,12,'Graphics','coast'),
            'characters':character_import('Graphics','characters')
        }
        self.monster_frames={
            'icons':import_folder_dict('graphics','icons'),
            'monsters':monster_importer(4,2,'graphics','monsters'),
            'ui':import_folder_dict('graphics','ui'),
            'attacks':attack_importer('graphics','attacks')
        }
        self.monster_frames['outlines']=outline(self.monster_frames['monsters'],4)
        self.fonts={
            'dialog':pygame.font.Font(join('Graphics','fonts','PixeloidSans.ttf'),30),
            'regular':pygame.font.Font(join('Graphics','fonts','PixeloidSans.ttf'),18),
            'small':pygame.font.Font(join('Graphics','fonts','PixeloidSans.ttf'),14),
            'bold':pygame.font.Font(join('Graphics','fonts','dogicapixelbold.otf'),20)
        }
        self.bg_frames=import_folder_dict('graphics','bg')
        self.star_animation_frames=import_folder('graphics','other')

        self.audio=audio_importer('Audio')

    def create_pre_battle_snapshot(self):
        # Deep-copy all relevant player monster and position data
        import copy
        self.pre_battle_snapshot = copy.deepcopy(self.player_monsters)
        self.pre_battle_position = (self.player.rect.centerx, self.player.rect.centery)


    def setup(self,tmx_map,player_start_pos):
        #clear
        for group in (self.all_sprites,self.collidable_sprites,self.transition_sprite,self.trainer_sprites):
            group.empty()
        #terrain
        for x,y,surf in tmx_map.get_layer_by_name('terrain').tiles():
            Sprite((x*TILE_SIZE,y*TILE_SIZE),surf,self.all_sprites,WORLD_LAYERS['background'])
        for x,y,surf in tmx_map.get_layer_by_name('terrain top').tiles():
            Sprite((x*TILE_SIZE,y*TILE_SIZE),surf,self.all_sprites)
        #objects
        for obj in tmx_map.get_layer_by_name('objects'):
            CollidableSprite((obj.x,obj.y),obj.image,(self.all_sprites,self.collidable_sprites))
        #transitions
        for obj in tmx_map.get_layer_by_name('transition'):
            TransitionSprite((obj.x,obj.y),(obj.width,obj.height),(obj.properties['target'],obj.properties['pos']),self.transition_sprite)

        #grass
        for obj in tmx_map.get_layer_by_name('monsters'):
            GrassSprite((obj.x, obj.y), obj.image, (self.all_sprites,self.grass_sprites),obj.properties['biome'],obj.properties['monsters'],obj.properties['level'])
        #collision layer
        for obj in tmx_map.get_layer_by_name('collisions'):
            BorderSprite((obj.x,obj.y),pygame.Surface((obj.width,obj.height)),self.collidable_sprites)

        #entities
        saved_pos = self.load_player_position()
        player_created = False
        for obj in tmx_map.get_layer_by_name('entities'):
            if obj.name == 'player' and not player_created:
                if saved_pos and player_start_pos == 'saved':
                    self.player = Player(
                        pos=saved_pos,
                        frames=self.overworld_frames['characters']['player'],
                        groups=self.all_sprites,
                        facing_direction=obj.properties['direction'],
                        collision_sprites=self.collidable_sprites
                    )
                    player_created = True
                elif obj.properties['pos'] == player_start_pos:
                    self.player = Player(
                        pos=(obj.x, obj.y),
                        frames=self.overworld_frames['characters']['player'],
                        groups=self.all_sprites,
                        facing_direction=obj.properties['direction'],
                        collision_sprites=self.collidable_sprites
                    )
                    player_created = True

        for obj in tmx_map.get_layer_by_name('entities'):
            if obj.name == 'character':
                character = Character(
                    pos=(obj.x,obj.y),
                    frames=self.overworld_frames['characters'][obj.properties['graphic']],
                    groups=(self.all_sprites,self.collidable_sprites,self.trainer_sprites),
                    facing_direction=obj.properties['direction'],
                    character_data=TRAINER_DATA[obj.properties['character_id']],
                    player=self.player,
                    create_dialog=self.create_dialog,
                    collidable_sprites=self.collidable_sprites,
                    radius=obj.properties['radius'],
                    nurse=obj.properties['character_id']=='Nurse',
                    notice_sound=self.audio['notice']
                )
                # ADD THESE 3 LINES ↓
                trainer_id = obj.properties['character_id']
                if hasattr(self, 'trainer_defeat_status') and trainer_id in self.trainer_defeat_status:
                    character.character_data['defeated'] = self.trainer_defeat_status[trainer_id]
        #water
        for obj in tmx_map.get_layer_by_name('water'):
            for x in range(int(obj.x),int(obj.x+obj.width),TILE_SIZE):
                for y in range(int(obj.y),int(obj.y+obj.height),TILE_SIZE):
                    AnimatedSprite((x,y),self.overworld_frames['water'],self.all_sprites,WORLD_LAYERS['water'])
        #coast
        for obj in tmx_map.get_layer_by_name('coast'):
            terrain=obj.properties['terrain']
            side=obj.properties['side']
            AnimatedSprite((obj.x,obj.y),self.overworld_frames['coast'][terrain][side],self.all_sprites,WORLD_LAYERS['background'])
    #dialog
    def input(self):
        if not self.dialog_tree and not self.battle:
            keys=pygame.key.get_just_pressed()
            if keys[pygame.K_SPACE]:
                for character in self.trainer_sprites:
                    if check(100, self.player, character):
                    # NEW: Prevent dialog and audio issues for already-defeated trainers
                        if character.character_data.get('defeated', False):
                            self.audio['overworld'].stop()
                            self.audio['battle'].stop()
                            pygame.mixer.stop()
                            # Do NOT start dialog, do NOT block player
                            self.audio['overworld'].play(-1)
                            return

            # Only allow dialog for undefeated trainers
                        self.player.blocked()
                        character.change_facing_direction(self.player.rect.center)
                        self.create_dialog(character)
                        character.can_rotate = False

            if keys[pygame.K_RETURN]:
                self.index_open=not self.index_open
                self.player.block=not self.player.block
    def create_dialog(self,character):
        if not self.dialog_tree:
           self.dialog_tree=DialogTree(character,self.player,self.all_sprites,self.fonts['dialog'],self.end_dialog)
    def end_dialog(self,character):
        self.dialog_tree=None
        self.player.unblocked()
        if character.nurse:
            for monster in self.player_monsters.values():
                monster.health=monster.get_stat('max_health')
                monster.energy=monster.get_stat('max_energy')
        elif not character.character_data['defeated']:
            self.battle= None
            self.create_pre_battle_snapshot()
            self.audio['overworld'].stop()
            pygame.mixer.stop()  # Stops all sound effects
            self.audio['battle'].play(-1)

            self.transition_target=Battle(
                player_monsters=self.player_monsters,
                opponent_monsters=character.monsters,
                monster_frames=self.monster_frames,
                bg_surf=self.bg_frames[character.character_data['biome']],
                fonts=self.fonts,
                end_battle=self.end_battle,
                character=character,
                sounds=self.audio
            )
            self.tint_mode='tint'
        else:
            self.player.unblocked()
            self.check_evolution()

    #transition
    def transition_check(self):
        sprites=[sprite for sprite in self.transition_sprite if sprite.rect.colliderect(self.player.hitbox)]
        if sprites:
            self.player.blocked()
            self.transition_target=sprites[0].target
            self.tint_mode='tint'
    def tint(self,dt):
        if self.tint_mode == 'untint':
            self.tint_progress -= self.tint_speed * dt

        if self.tint_mode == 'tint':
            self.tint_progress += self.tint_speed * dt

            if self.tint_progress >= 255:
                if type(self.transition_target)==Battle:
                    self.battle=self.transition_target
                elif self.transition_target=='level':
                    self.battle=None
                else:
                    self.setup(self.tmx_maps[self.transition_target[0]], self.transition_target[1])
                self.tint_mode = 'untint'
                self.transition_target = None
        self.tint_progress = max(0, min(self.tint_progress, 255))
        self.tint_surf.set_alpha(self.tint_progress)  #adjusts transparency
        self.display_surface.blit(self.tint_surf, (0,0))

    def end_battle(self,character, player_lost=False):
        self.audio['battle'].stop()
        pygame.mixer.stop()  # Stops all sound effects
        self.battle = None
        self.transition_target='level'
        self.tint_mode='tint'
        if player_lost:
            self.restore_from_snapshot()  #respawn and revert monsters
            if character:
                character.character_data['defeated'] = False  # allow retry
        else:
            #self.battle_result = 'won'  # Mark as won
            if character:
                character.character_data['defeated']=True
                self.db_manager.save_trainer_status(self.player_id, character.character_data.get('id', 'unknown'), True)
                self.create_dialog(character)
            elif not self.evolution:
                self.player.unblocked()
                self.check_evolution()
            self.save_player_progress()  # SAVE progress after win


    def save_player_progress(self):
        print("Progress saved")
        self.db_manager.save_player_progress(
            self.player_id,
            (self.player.rect.centerx, self.player.rect.centery),
            self.player_monsters)

    def check_evolution(self):
        for index,monster in self.player_monsters.items():
            if monster.evolution:
                if monster.level==monster.evolution[1]:
                    self.audio['evolution'].play()
                    self.player.blocked()
                    self.evolution=Evolution(self.monster_frames['monsters'],monster.name,monster.evolution[0],self.fonts['bold'],self.end_evolution,self.star_animation_frames)
                    self.player_monsters[index]=Monster(monster.evolution[0],monster.level)
        if not self.evolution:
            self.audio['overworld'].play(-1)

    def end_evolution(self):
        self.evolution=None
        self.player.unblocked()
        self.audio['evolution'].stop()
        self.audio['overworld'].play(-1)

    #monster encounters
    def check_monster(self):
        if [sprite for sprite in self.grass_sprites if sprite.rect.colliderect(self.player.hitbox)] and not self.battle and self.player.direction:
            if not self.encounter_timer.active:
                self.encounter_timer.activate()

    def monster_encounter(self):
        sprites = [sprite for sprite in self.grass_sprites if sprite.rect.colliderect(self.player.hitbox)]
        if sprites and self.player.direction:
            self.encounter_timer.duration = randint(800, 2500)
            self.player.blocked()
            self.audio['overworld'].stop()
            pygame.mixer.stop()  # ← ADD THIS LINE
            self.audio['battle'].play(-1)
            self.create_pre_battle_snapshot()
            self.transition_target = Battle(
				player_monsters = self.player_monsters,
				opponent_monsters = {index:Monster(monster, sprites[0].level + randint(-3,3)) for index, monster in enumerate(sprites[0].monsters)},
				monster_frames = self.monster_frames,
				bg_surf = self.bg_frames[sprites[0].biome],
				fonts = self.fonts,
				end_battle = self.end_battle,
				character = None,
                sounds=self.audio
				)
            self.tint_mode = 'tint'

    def restore_from_snapshot(self):
        if self.pre_battle_snapshot:
            self.player_monsters = self.pre_battle_snapshot
            self.setup(self.tmx_maps['world'], 'house')  # Moves player to house
            pygame.mixer.stop()
            self.audio['overworld'].play(-1)
            self.pre_battle_snapshot = None
            self.pre_battle_position = None

    def run(self):
        while True:
            dt = self.clock.tick()/1000
            self.display_surface.fill('black')
        #event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_player_progress()  # save before exit
                    self.db_manager.close()      # close DB
                    pygame.quit()
                    exit()
            #logic
            self.encounter_timer.update()
            self.input()
            self.transition_check()
            self.all_sprites.update(dt)
            self.check_monster()
            #drawing
            self.all_sprites.draw(self.player)
            #overlays
            if self.dialog_tree:
                self.dialog_tree.update()
            if self.index_open:
                self.monster_index.update(dt)
            if self.battle:
                self.battle.update(dt)
            if self.evolution:
                self.evolution.update(dt)

            self.tint(dt)

            pygame.display.update()
if __name__=='__main__':
    game=Game()
    game.run()

from game_data import MONSTER_DATA,ATTACK_DATA
from random import randint
class Monster:
    def __init__(self,name,level):
        self.name,self.level=name,level
        self.fainted = False
        self.paused=False
        #stats
        self.element=MONSTER_DATA[name]['stats']['element']
        self.base_stats=MONSTER_DATA[name]['stats']
        self.health=self.base_stats['max_health']*self.level
        self.energy=self.base_stats['max_energy']*self.level
        self.initiative=0
        self.abilities=MONSTER_DATA[name]['abilities']
        self.defending=False


        #xp
        self.xp=0
        self.level_up=self.level*150
        self.evolution=MONSTER_DATA[self.name]['evolve']

    def __repr__(self):
        return f'monster: {self.name},lvl:{self.level}'

    def get_stat(self,stat):
        return self.base_stats[stat]*self.level

    def get_stats(self):
        return {
            'Health':self.get_stat('max_health'),
            'Energy':self.get_stat('max_energy'),
            'Attack':self.get_stat('Attack'),
            'Defense':self.get_stat('Defense'),
            'Speed':self.get_stat('Speed'),
            'Recovery':self.get_stat('Recovery')
        }
    def get_abilities(self,all=True):
        if all:
            return [ability for lvl,ability in self.abilities.items() if self.level>=lvl]
        else:
            return [ability for lvl,ability in self.abilities.items() if self.level>=lvl and ATTACK_DATA[ability]['cost']<self.energy]
    def get_info(self):
        return (
            (self.health,self.get_stat('max_health')),
            (self.energy,self.get_stat('max_energy')),
            (self.initiative,100)
        )

    def update_xp(self,amount):
        if self.level_up-self.xp>amount:
            self.xp+=amount*15
        else:
            self.level+=1
            self.xp=amount-(self.level_up-self.xp)
            self.level_up=self.level*150

    def get_base_damage(self,attack):
        return self.get_stat('Attack')*ATTACK_DATA[attack]['amount']
    def reduce_energy(self,attack):
        self.energy-=ATTACK_DATA[attack]['cost']

    def stat_limiter(self):
        self.health=max(0,min(self.health,self.get_stat('max_health')))
        self.energy=max(0,min(self.energy,self.get_stat('max_energy')))
    def update(self,dt):
        self.stat_limiter()
        if not self.paused:
            self.initiative+=self.get_stat('Speed')*dt*3

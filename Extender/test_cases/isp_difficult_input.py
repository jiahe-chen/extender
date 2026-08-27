from abc import ABC, abstractmethod


class GameCharacter(ABC):
    @abstractmethod
    def melee_attack(self):
        pass
    
    @abstractmethod
    def cast_spell(self):
        pass
    
    @abstractmethod
    def fly(self):
        pass
    
    @abstractmethod
    def defend(self):
        pass


class Weapon(ABC):
    @abstractmethod
    def slash(self):
        pass
    
    @abstractmethod
    def shoot(self):
        pass
    
    @abstractmethod
    def enchant(self):
        pass
    
    @abstractmethod
    def repair(self):
        pass


class Enemy(ABC):
    @abstractmethod
    def attack(self):
        pass
    
    @abstractmethod
    def fly(self):
        pass
    
    @abstractmethod
    def poison(self):
        pass
    
    @abstractmethod
    def summon_minions(self):
        pass
    
    @abstractmethod
    def take_damage(self, damage_values):
        pass


class Mage(GameCharacter):
    def __init__(self, name, level):
        self.name = name
        self.mana = 100
        self.level = level
    
    def melee_attack(self):
        raise NotImplementedError("Mage cannot perform melee attacks!")
    
    def cast_spell(self):
        if self.mana < 10:
            print(f"{self.name} is out of mana!")
            return
        
        if self.level >= 5 and self.mana >= 30:
            print(f"{self.name} casts a powerful lightning storm!")
            self.mana -= 30
        elif self.level >= 3 and self.mana >= 20:
            print(f"{self.name} casts a fireball spell!")
            self.mana -= 20
        elif self.mana >= 10:
            print(f"{self.name} casts a basic magic missile!")
            self.mana -= 10
    
    def fly(self):
        if self.level >= 2:
            print(f"{self.name} soars through the air with magic!")
        else:
            print(f"{self.name} is too inexperienced to fly!")
    
    def defend(self):
        if self.mana >= 15:
            print(f"{self.name} creates a magical barrier!")
            self.mana -= 15
        else:
            print(f"{self.name} dodges awkwardly!")


class Fighter(GameCharacter):
    def __init__(self, name, has_weapon):
        self.name = name
        self.stamina = 100
        self.has_weapon = has_weapon
    
    def melee_attack(self):
        if self.stamina < 5:
            print(f"{self.name} is too exhausted to fight!")
            return
        
        if self.has_weapon:
            if self.stamina >= 20:
                print(f"{self.name} performs a devastating combo attack!")
                self.stamina -= 20
            elif self.stamina >= 10:
                print(f"{self.name} swings weapon with force!")
                self.stamina -= 10
            else:
                print(f"{self.name} makes a weak weapon strike!")
                self.stamina -= 5
        else:
            if self.stamina >= 15:
                print(f"{self.name} throws a powerful punch!")
                self.stamina -= 15
            else:
                print(f"{self.name} throws a basic punch!")
                self.stamina -= 5
    
    def cast_spell(self):
        raise NotImplementedError("Fighter cannot cast spells!")
    
    def fly(self):
        raise NotImplementedError("Fighter cannot fly!")
    
    def defend(self):
        if self.has_weapon and self.stamina >= 10:
            print(f"{self.name} blocks with weapon!")
            self.stamina -= 10
        elif self.stamina >= 5:
            print(f"{self.name} raises arms to defend!")
            self.stamina -= 5
        else:
            print(f"{self.name} barely manages to dodge!")


class Sword(Weapon):
    def __init__(self, sharpness, is_magic):
        self.sharpness = sharpness
        self.is_magic = is_magic
    
    def slash(self):
        if self.sharpness > 70:
            print("Sword cuts cleanly through the target!")
        elif self.sharpness > 30:
            print("Sword makes a decent cut!")
        else:
            print("Dull sword barely scratches the target!")
    
    def shoot(self):
        raise NotImplementedError("Sword cannot shoot!")
    
    def enchant(self):
        if self.is_magic:
            print("Magical sword glows with enhanced power!")
            self.sharpness += 10
        else:
            raise NotImplementedError("Non-magic sword cannot be enchanted!")
    
    def repair(self):
        if self.sharpness < 100:
            self.sharpness = min(100, self.sharpness + 25)
            print("Sword has been sharpened and repaired!")
        else:
            print("Sword is already in perfect condition!")


class Bow(Weapon):
    def __init__(self, arrows, range_val):
        self.arrows = arrows
        self.range = range_val
    
    def slash(self):
        raise NotImplementedError("Bow cannot slash!")
    
    def shoot(self):
        if self.arrows <= 0:
            print("No arrows left to shoot!")
            return
        
        if self.range > 80:
            print("Long-range shot hits the distant target!")
        elif self.range > 50:
            print("Medium-range shot finds its mark!")
        else:
            print("Short-range shot barely reaches the target!")
        self.arrows -= 1
    
    def enchant(self):
        raise NotImplementedError("Regular bow cannot be enchanted!")
    
    def repair(self):
        if self.range < 100:
            self.range = min(100, self.range + 15)
            print("Bow string tightened and wood polished!")
        else:
            print("Bow is in excellent condition!")


class Orc(Enemy):
    def __init__(self, name, strength):
        self.name = name
        self.health = 100
        self.strength = strength
    
    def attack(self):
        if self.strength > 50:
            print(f"{self.name} delivers a crushing blow!")
        else:
            print(f"{self.name} swings clumsily!")
    
    def fly(self):
        raise NotImplementedError("Orc cannot fly!")
    
    def poison(self):
        raise NotImplementedError("Orc cannot poison enemies!")
    
    def summon_minions(self):
        raise NotImplementedError("Orc cannot summon minions!")
    
    def take_damage(self, damage_values):
        total_damage = 0
        for i in range(len(damage_values)):
            if damage_values[i] > 0:
                total_damage += damage_values[i]
                if damage_values[i] > 20:
                    print(f"{self.name} staggers from heavy damage!")
        
        self.health -= total_damage
        print(f"{self.name} takes {total_damage} damage! Health: {self.health}")
        
        if self.health <= 0:
            print(f"{self.name} has been defeated!")


class Dragon(Enemy):
    def __init__(self, name, firepower):
        self.name = name
        self.health = 200
        self.firepower = firepower
        self.can_fly = True
    
    def attack(self):
        if self.firepower > 80:
            print(f"{self.name} breathes devastating flames!")
        elif self.firepower > 50:
            print(f"{self.name} breathes hot fire!")
        else:
            print(f"{self.name} breathes weak flames!")
    
    def fly(self):
        if self.can_fly and self.health > 50:
            print(f"{self.name} soars majestically through the sky!")
        elif self.health <= 50:
            print(f"{self.name} is too wounded to fly!")
    
    def poison(self):
        raise NotImplementedError("Dragon doesn't use poison!")
    
    def summon_minions(self):
        raise NotImplementedError("Dragon doesn't summon minions!")
    
    def take_damage(self, damage_values):
        total_damage = 0
        critical_hits = 0
        
        for i in range(len(damage_values)):
            if damage_values[i] > 0:
                reduced_damage = max(1, damage_values[i] - 5)
                total_damage += reduced_damage
                
                if damage_values[i] > 30:
                    critical_hits += 1
                    print(f"{self.name} roars in pain from critical hit!")
        
        self.health -= total_damage
        print(f"{self.name} takes {total_damage} damage ({critical_hits} critical hits)! Health: {self.health}")
        
        if self.health <= 0:
            print(f"{self.name} crashes to the ground, defeated!")
            self.can_fly = False


class Spider(Enemy):
    def __init__(self, name):
        self.name = name
        self.health = 50
        self.has_poison = True
    
    def attack(self):
        print(f"{self.name} bites with venomous fangs!")
    
    def fly(self):
        raise NotImplementedError("Spider cannot fly!")
    
    def poison(self):
        if self.has_poison:
            print(f"{self.name} injects deadly venom!")
        else:
            print(f"{self.name} has no poison left!")
    
    def summon_minions(self):
        raise NotImplementedError("Spider cannot summon minions!")
    
    def take_damage(self, damage_values):
        total_damage = 0
        for damage in damage_values:
            if damage > 0:
                amplified_damage = damage + (damage // 2)
                total_damage += amplified_damage
                
                if damage > 10:
                    print(f"{self.name} screeches in pain!")
        
        self.health -= total_damage
        print(f"{self.name} takes {total_damage} damage! Health: {self.health}")
        
        if self.health <= 0:
            print(f"{self.name} curls up and dies!")

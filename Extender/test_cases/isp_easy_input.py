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

class Mage(GameCharacter):
    def __init__(self, name):
        self.name = name
        self.mana = 100
    
    def melee_attack(self):
        raise NotImplementedError("Mage cannot perform melee attacks!")
    
    def cast_spell(self):
        if self.mana >= 20:
            print(f"{self.name} casts a fireball spell!")
            self.mana -= 20
        else:
            print(f"{self.name} is out of mana!")
    
    def fly(self):
        print(f"{self.name} soars through the air with magic!")
    
    def defend(self):
        print(f"{self.name} creates a magical shield!")

class Fighter(GameCharacter):
    def __init__(self, name):
        self.name = name
        self.stamina = 100
    
    def melee_attack(self):
        if self.stamina >= 10:
            print(f"{self.name} swings sword with great force!")
            self.stamina -= 10
        else:
            print(f"{self.name} is too tired to attack!")
    
    def cast_spell(self):
        raise NotImplementedError("Fighter cannot cast spells!")
    
    def fly(self):
        raise NotImplementedError("Fighter cannot fly!")
    
    def defend(self):
        print(f"{self.name} raises shield to block incoming attacks!")

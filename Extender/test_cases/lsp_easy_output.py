from abc import ABC, abstractmethod

class Bird(ABC):
    @abstractmethod
    def move(self):
        pass

class Flyable(ABC):
    @abstractmethod
    def fly(self):
        pass

class Swimmable(ABC):
    @abstractmethod
    def swim(self):
        pass

class Sparrow(Bird, Flyable):
    def move(self):
        self.fly()
    
    def fly(self):
        print("Sparrow flying fast!")

class Penguin(Bird, Swimmable):
    def move(self):
        self.swim()
    
    def swim(self):
        print("Penguin swimming gracefully!")

class BirdWatcher:
    def watch_bird(self, bird):
        bird.move()
    
    def watch_flying_bird(self, bird):
        bird.fly()
    
    def watch_swimming_bird(self, bird):
        bird.swim()
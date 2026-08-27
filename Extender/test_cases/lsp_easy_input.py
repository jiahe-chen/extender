class Bird:
    def fly(self):
        print("Flying high!")

class Sparrow(Bird):
    def fly(self):
        print("Sparrow flying fast!")

class Penguin(Bird):
    def fly(self):
        raise NotImplementedError("Penguins cannot fly!")

class BirdWatcher:
    def watch_bird(self, bird):
        bird.fly()
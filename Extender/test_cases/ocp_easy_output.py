import math

class Shape:
    def get_area(self):
        raise NotImplementedError

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_area(self):
        return self.width * self.height

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def get_area(self):
        return math.pi * self.radius * self.radius

class AreaCalculator:
    def calculate_area(self, shape):
        return shape.get_area()

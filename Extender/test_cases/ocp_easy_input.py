import math

class Shape:
    def __init__(self, type):
        self._type = type

    def get_type(self):
        return self._type


class Rectangle(Shape):
    def __init__(self, width, height):
        super().__init__("rectangle")
        self._width = width
        self._height = height

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height


class Circle(Shape):
    def __init__(self, radius):
        super().__init__("circle")
        self._radius = radius

    def get_radius(self):
        return self._radius


class AreaCalculator:
    def calculate_area(self, shape):
        if shape.get_type() == "rectangle":
            rectangle = shape
            return rectangle.get_width() * rectangle.get_height()
        elif shape.get_type() == "circle":
            circle = shape
            return math.pi * circle.get_radius() * circle.get_radius()
        return 0
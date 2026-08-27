import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Callable, Any, List


class Entity:
    _NEXT_ID = 1
    
    def __init__(self):
        self.id = Entity._NEXT_ID
        Entity._NEXT_ID += 1
    
    def get_id(self):
        return self.id


class GraphicObject(Entity):
    def __init__(self, color: str, layer: int):
        super().__init__()
        self.color = color
        self.layer = layer
    
    def get_color(self):
        return self.color
    
    def get_layer(self):
        return self.layer


class ShapeKind(Enum):
    RECTANGLE = "RECTANGLE"
    CIRCLE = "CIRCLE"
    TRIANGLE = "TRIANGLE"
    CUBE = "CUBE"
    SPHERE = "SPHERE"


class BoundingBox:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def __str__(self):
        return f"BBox({self.width}x{self.height})"


class HasWidthHeight(ABC):
    @abstractmethod
    def get_width(self):
        pass
    
    @abstractmethod
    def get_height(self):
        pass


class HasRadius(ABC):
    @abstractmethod
    def get_radius(self):
        pass


class HasTriangleSides(ABC):
    @abstractmethod
    def get_a(self):
        pass
    
    @abstractmethod
    def get_b(self):
        pass
    
    @abstractmethod
    def get_c(self):
        pass


class HasEdge(ABC):
    @abstractmethod
    def get_edge(self):
        pass


class Shape(GraphicObject, ABC):
    def __init__(self, kind: ShapeKind, color: str, layer: int):
        super().__init__(color, layer)
        self.kind = kind
    
    def get_kind(self):
        return self.kind
    
    @abstractmethod
    def is_valid(self):
        pass
    
    @abstractmethod
    def render_pseudo_svg(self):
        pass
    
    @abstractmethod
    def to_csv_row(self):
        pass
    
    @abstractmethod
    def legend_symbol(self):
        pass
    
    @abstractmethod
    def bounding_box(self):
        pass
    
    @abstractmethod
    def price(self, calc):
        pass


class TwoDShape(Shape):
    def __init__(self, kind: ShapeKind, color: str, layer: int):
        super().__init__(kind, color, layer)


class ThreeDShape(Shape):
    def __init__(self, kind: ShapeKind, color: str, layer: int):
        super().__init__(kind, color, layer)


class Rectangle(TwoDShape, HasWidthHeight):
    def __init__(self, width: float, height: float, color: str, layer: int):
        super().__init__(ShapeKind.RECTANGLE, color, layer)
        self.width = width
        self.height = height
    
    def get_width(self):
        return self.width
    
    def get_height(self):
        return self.height
    
    def is_valid(self):
        return self.width > 0 and self.height > 0
    
    def render_pseudo_svg(self):
        return f'<rect w="{self.width}" h="{self.height}" fill="{self.get_color()}" layer="{self.get_layer()}"/>'
    
    def to_csv_row(self):
        return f"rectangle,{self.width},{self.height},{self.get_color()},{self.get_layer()}"
    
    def legend_symbol(self):
        return "▭"
    
    def bounding_box(self):
        return BoundingBox(self.width, self.height)
    
    def price(self, calc):
        area = calc.compute(self, "area")
        return 0.5 * area + self.get_layer() * 2


class Circle(TwoDShape, HasRadius):
    def __init__(self, radius: float, color: str, layer: int):
        super().__init__(ShapeKind.CIRCLE, color, layer)
        self.radius = radius
    
    def get_radius(self):
        return self.radius
    
    def is_valid(self):
        return self.radius > 0
    
    def render_pseudo_svg(self):
        return f'<circle r="{self.radius}" fill="{self.get_color()}" layer="{self.get_layer()}"/>'
    
    def to_csv_row(self):
        return f"circle,{self.radius},{self.get_color()},{self.get_layer()}"
    
    def legend_symbol(self):
        return "◯"
    
    def bounding_box(self):
        d = 2 * self.radius
        return BoundingBox(d, d)
    
    def price(self, calc):
        area = calc.compute(self, "area")
        diag = calc.compute(self, "diagonal")
        return 0.6 * area + 0.1 * diag


class Triangle(TwoDShape, HasTriangleSides):
    def __init__(self, a: float, b: float, c: float, color: str, layer: int):
        super().__init__(ShapeKind.TRIANGLE, color, layer)
        self.a = a
        self.b = b
        self.c = c
    
    def get_a(self):
        return self.a
    
    def get_b(self):
        return self.b
    
    def get_c(self):
        return self.c
    
    def is_valid(self):
        return (self.a > 0 and self.b > 0 and self.c > 0 and 
                self.a + self.b > self.c and self.a + self.c > self.b and 
                self.b + self.c > self.a)
    
    def render_pseudo_svg(self):
        return f'<polygon a="{self.a}" b="{self.b}" c="{self.c}" fill="{self.get_color()}" layer="{self.get_layer()}"/>'
    
    def to_csv_row(self):
        return f"triangle,{self.a},{self.b},{self.c},{self.get_color()},{self.get_layer()}"
    
    def legend_symbol(self):
        return "△"
    
    def bounding_box(self):
        max_side = max(self.a, max(self.b, self.c))
        avg = (self.a + self.b + self.c - max_side) / 2.0
        return BoundingBox(max_side, avg)
    
    def price(self, calc):
        per = calc.compute(self, "perimeter")
        return per * 0.8


class Cube(ThreeDShape, HasEdge):
    def __init__(self, edge: float, color: str, layer: int):
        super().__init__(ShapeKind.CUBE, color, layer)
        self.edge = edge
    
    def get_edge(self):
        return self.edge
    
    def is_valid(self):
        return self.edge > 0
    
    def render_pseudo_svg(self):
        return f'<cube edge="{self.edge}" materialColor="{self.get_color()}" layer="{self.get_layer()}"/>'
    
    def to_csv_row(self):
        return f"cube,{self.edge},{self.get_color()},{self.get_layer()}"
    
    def legend_symbol(self):
        return "⬛"
    
    def bounding_box(self):
        return BoundingBox(self.edge, self.edge)
    
    def price(self, calc):
        vol = calc.compute(self, "volume")
        return 1.2 * vol


class Sphere(ThreeDShape, HasRadius):
    def __init__(self, radius: float, color: str, layer: int):
        super().__init__(ShapeKind.SPHERE, color, layer)
        self.radius = radius
    
    def get_radius(self):
        return self.radius
    
    def is_valid(self):
        return self.radius > 0
    
    def render_pseudo_svg(self):
        return f'<sphere r="{self.radius}" materialColor="{self.get_color()}" layer="{self.get_layer()}"/>'
    
    def to_csv_row(self):
        return f"sphere,{self.radius},{self.get_color()},{self.get_layer()}"
    
    def legend_symbol(self):
        return "◯"
    
    def bounding_box(self):
        d = 2 * self.radius
        return BoundingBox(d, d)
    
    def price(self, calc):
        vol = calc.compute(self, "volume")
        return 1.0 * vol + 10


class RegisteredMetric:
    def __init__(self, name: str):
        self.name_val = name
        self.handlers = {}
    
    def name(self):
        return self.name_val
    
    def on(self, type_class: type, fn: Callable):
        self.handlers[type_class] = fn
        return self
    
    def apply(self, s: Shape):
        for cls, handler in self.handlers.items():
            if isinstance(s, cls):
                return handler(s)
        return 0


class MetricCalculator:
    def __init__(self):
        self.metrics = {}
    
    def register(self, metric: RegisteredMetric):
        self.metrics[metric.name()] = metric
    
    def compute(self, shape: Shape, metric_name: str):
        m = self.metrics.get(metric_name)
        if m is None:
            raise ValueError(f"Unknown metric: {metric_name}")
        return m.apply(shape)


class ShapeValidator:
    def is_valid(self, shape: Shape):
        return shape.is_valid()


class ShapeRenderer:
    def render_pseudo_svg(self, shape: Shape):
        return shape.render_pseudo_svg()


class ShapeSerializer:
    def to_csv_row(self, shape: Shape):
        return shape.to_csv_row()


class ShapeFactory:
    def __init__(self):
        self.creators = {}
    
    def register(self, type_name: str, creator: Callable):
        self.creators[type_name.lower()] = creator
    
    def create(self, spec: str):
        parts = spec.split(";")
        type_name = parts[0].strip().lower()
        map_vals = {}
        for i in range(1, len(parts)):
            kv = parts[i].split("=")
            if len(kv) == 2:
                map_vals[kv[0].strip().lower()] = kv[1].strip()
        
        color = map_vals.get("color", "black")
        layer = int(map_vals.get("layer", "0"))
        c = self.creators.get(type_name)
        if c is None:
            raise ValueError(f"Unknown shape type: {type_name}")
        return c(map_vals, color, layer)


class ShapePricing:
    def __init__(self, calc: MetricCalculator):
        self.calc = calc
    
    def price(self, shape: Shape):
        return shape.price(self.calc)


class LegendBuilder:
    def legend_symbol(self, shape: Shape):
        return shape.legend_symbol()


class CollisionEngine:
    def bounding_box(self, shape: Shape):
        return shape.bounding_box()
    
    def overlaps(self, a: Shape, b: Shape):
        A = self.bounding_box(a)
        B = self.bounding_box(b)
        return (A.width * A.height) > 0 and (B.width * B.height) > 0


class ShapeReport:
    def __init__(self, calc: MetricCalculator):
        self.calc = calc
        self.ser = ShapeSerializer()
        self.rnd = ShapeRenderer()
        self.col = CollisionEngine()
        self.price = ShapePricing(calc)
        self.legend = LegendBuilder()
    
    def summarize(self, shapes: List[Shape]):
        sb = []
        sb.append("=== Shape Report (OCP-violating) ===\n")
        for s in shapes:
            sb.append(f"ID {s.get_id()} {s.get_kind().value} color={s.get_color()} layer={s.get_layer()}\n")
            
            sb.append(f"  CSV: {self.ser.to_csv_row(s)}\n")
            sb.append(f"  SVG: {self.rnd.render_pseudo_svg(s)}\n")
            sb.append(f"  Legend: {self.legend.legend_symbol(s)}\n")
            
            sb.append("  Metrics:")
            sb.append(f" area={self.calc.compute(s, 'area')}")
            sb.append(f" perim={self.calc.compute(s, 'perimeter')}")
            sb.append(f" diag={self.calc.compute(s, 'diagonal')}")
            if isinstance(s, ThreeDShape):
                sb.append(f" vol={self.calc.compute(s, 'volume')}")
            sb.append("\n")
            
            sb.append(f"  BBox: {self.col.bounding_box(s)}\n")
            sb.append(f"  Price: {self.price.price(s)}\n\n")
        
        return "".join(sb)


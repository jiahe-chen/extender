from abc import ABC
from enum import Enum
import math


class Entity(ABC):
    _NEXT_ID = 1

    def __init__(self):
        self._id = Entity._NEXT_ID
        Entity._NEXT_ID += 1

    @property
    def id(self):
        return self._id


class GraphicObject(Entity, ABC):
    def __init__(self, color, layer):
        super().__init__()
        self._color = color
        self._layer = layer

    @property
    def color(self):
        return self._color

    @property
    def layer(self):
        return self._layer


class ShapeKind(Enum):
    RECTANGLE = 1
    CIRCLE = 2
    TRIANGLE = 3
    CUBE = 4
    SPHERE = 5


class Shape(GraphicObject, ABC):
    def __init__(self, kind, color, layer):
        super().__init__(color, layer)
        self._kind = kind

    @property
    def kind(self):
        return self._kind


class TwoDShape(Shape, ABC):
    def __init__(self, kind, color, layer):
        super().__init__(kind, color, layer)


class ThreeDShape(Shape, ABC):
    def __init__(self, kind, color, layer):
        super().__init__(kind, color, layer)


class Rectangle(TwoDShape):
    def __init__(self, width, height, color, layer):
        super().__init__(ShapeKind.RECTANGLE, color, layer)
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height


class Circle(TwoDShape):
    def __init__(self, radius, color, layer):
        super().__init__(ShapeKind.CIRCLE, color, layer)
        self._radius = radius

    @property
    def radius(self):
        return self._radius


class Triangle(TwoDShape):
    def __init__(self, a, b, c, color, layer):
        super().__init__(ShapeKind.TRIANGLE, color, layer)
        self._a = a
        self._b = b
        self._c = c

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b

    @property
    def c(self):
        return self._c


class Cube(ThreeDShape):
    def __init__(self, edge, color, layer):
        super().__init__(ShapeKind.CUBE, color, layer)
        self._edge = edge

    @property
    def edge(self):
        return self._edge


class Sphere(ThreeDShape):
    def __init__(self, radius, color, layer):
        super().__init__(ShapeKind.SPHERE, color, layer)
        self._radius = radius

    @property
    def radius(self):
        return self._radius


class Metric(Enum):
    AREA = 1
    PERIMETER = 2
    VOLUME = 3
    DIAGONAL = 4
    BOUNDING_BOX_WIDTH = 5


class BoundingBox:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __str__(self):
        return f"BBox({self.width}x{self.height})"


class MetricCalculator:
    def compute(self, shape, metric):
        if shape.kind == ShapeKind.RECTANGLE:
            r = shape
            if metric == Metric.AREA:
                return r.width * r.height
            if metric == Metric.PERIMETER:
                return 2 * (r.width + r.height)
            if metric == Metric.DIAGONAL:
                return math.hypot(r.width, r.height)
            if metric == Metric.BOUNDING_BOX_WIDTH:
                return r.width
            if metric == Metric.VOLUME:
                return 0
        elif shape.kind == ShapeKind.CIRCLE:
            c = shape
            if metric == Metric.AREA:
                return math.pi * c.radius * c.radius
            if metric == Metric.PERIMETER:
                return 2 * math.pi * c.radius
            if metric == Metric.DIAGONAL:
                return 2 * c.radius
            if metric == Metric.BOUNDING_BOX_WIDTH:
                return 2 * c.radius
            if metric == Metric.VOLUME:
                return 0
        elif shape.kind == ShapeKind.TRIANGLE:
            t = shape
            s = (t.a + t.b + t.c) / 2.0
            if metric == Metric.AREA:
                return math.sqrt(max(0, s * (s - t.a) * (s - t.b) * (s - t.c)))
            if metric == Metric.PERIMETER:
                return t.a + t.b + t.c
            if metric == Metric.DIAGONAL:
                return max(t.a, t.b, t.c)
            if metric == Metric.BOUNDING_BOX_WIDTH:
                return max(t.a, t.b, t.c)
            if metric == Metric.VOLUME:
                return 0
        elif shape.kind == ShapeKind.CUBE:
            cube = shape
            if metric == Metric.AREA:
                return 6 * cube.edge * cube.edge
            if metric == Metric.PERIMETER:
                return 12 * cube.edge
            if metric == Metric.VOLUME:
                return cube.edge ** 3
            if metric == Metric.DIAGONAL:
                return math.sqrt(3) * cube.edge
            if metric == Metric.BOUNDING_BOX_WIDTH:
                return cube.edge
        elif shape.kind == ShapeKind.SPHERE:
            s = shape
            if metric == Metric.AREA:
                return 4 * math.pi * s.radius * s.radius
            if metric == Metric.PERIMETER:
                return 0
            if metric == Metric.VOLUME:
                return (4.0 / 3.0) * math.pi * (s.radius ** 3)
            if metric == Metric.DIAGONAL:
                return 2 * s.radius
            if metric == Metric.BOUNDING_BOX_WIDTH:
                return 2 * s.radius
        return 0


class ShapeValidator:
    def is_valid(self, shape):
        if shape.kind == ShapeKind.RECTANGLE:
            return shape.width > 0 and shape.height > 0
        if shape.kind == ShapeKind.CIRCLE:
            return shape.radius > 0
        if shape.kind == ShapeKind.TRIANGLE:
            return (
                shape.a > 0 and shape.b > 0 and shape.c > 0
                and shape.a + shape.b > shape.c
                and shape.a + shape.c > shape.b
                and shape.b + shape.c > shape.a
            )
        if shape.kind == ShapeKind.CUBE:
            return shape.edge > 0
        if shape.kind == ShapeKind.SPHERE:
            return shape.radius > 0
        return False


class ShapeRenderer:
    def render_pseudo_svg(self, shape):
        if shape.kind == ShapeKind.RECTANGLE:
            return f'<rect w="{shape.width}" h="{shape.height}" fill="{shape.color}" layer="{shape.layer}"/>'
        if shape.kind == ShapeKind.CIRCLE:
            return f'<circle r="{shape.radius}" fill="{shape.color}" layer="{shape.layer}"/>'
        if shape.kind == ShapeKind.TRIANGLE:
            return f'<polygon a="{shape.a}" b="{shape.b}" c="{shape.c}" fill="{shape.color}" layer="{shape.layer}"/>'
        if shape.kind == ShapeKind.CUBE:
            return f'<cube edge="{shape.edge}" materialColor="{shape.color}" layer="{shape.layer}"/>'
        if shape.kind == ShapeKind.SPHERE:
            return f'<sphere r="{shape.radius}" materialColor="{shape.color}" layer="{shape.layer}"/>'
        return "<unknown/>"


class ShapeSerializer:
    def to_csv_row(self, shape):
        if shape.kind == ShapeKind.RECTANGLE:
            return f"rectangle,{shape.width},{shape.height},{shape.color},{shape.layer}"
        if shape.kind == ShapeKind.CIRCLE:
            return f"circle,{shape.radius},{shape.color},{shape.layer}"
        if shape.kind == ShapeKind.TRIANGLE:
            return f"triangle,{shape.a},{shape.b},{shape.c},{shape.color},{shape.layer}"
        if shape.kind == ShapeKind.CUBE:
            return f"cube,{shape.edge},{shape.color},{shape.layer}"
        if shape.kind == ShapeKind.SPHERE:
            return f"sphere,{shape.radius},{shape.color},{shape.layer}"
        return "unknown"


class ShapeFactory:
    def create(self, spec):
        parts = spec.split(";")
        type_ = parts[0].strip().lower()
        map_ = {}
        for kv in parts[1:]:
            pair = kv.split("=")
            if len(pair) == 2:
                map_[pair[0].strip().lower()] = pair[1].strip()
        color = map_.get("color", "black")
        layer = int(map_.get("layer", "0"))
        if type_ == "rectangle":
            return Rectangle(float(map_.get("width", "0")), float(map_.get("height", "0")), color, layer)
        if type_ == "circle":
            return Circle(float(map_.get("radius", "0")), color, layer)
        if type_ == "triangle":
            return Triangle(float(map_.get("a", "0")), float(map_.get("b", "0")), float(map_.get("c", "0")), color, layer)
        if type_ == "cube":
            return Cube(float(map_.get("edge", "0")), color, layer)
        if type_ == "sphere":
            return Sphere(float(map_.get("radius", "0")), color, layer)
        raise ValueError(f"Unknown shape type: {type_}")


class ShapePricing:
    def __init__(self):
        self.calc = MetricCalculator()

    def price(self, shape):
        if shape.kind == ShapeKind.RECTANGLE:
            area = self.calc.compute(shape, Metric.AREA)
            return 0.5 * area + shape.layer * 2
        if shape.kind == ShapeKind.CIRCLE:
            area = self.calc.compute(shape, Metric.AREA)
            diag = self.calc.compute(shape, Metric.DIAGONAL)
            return 0.6 * area + 0.1 * diag
        if shape.kind == ShapeKind.TRIANGLE:
            per = self.calc.compute(shape, Metric.PERIMETER)
            return per * 0.8
        if shape.kind == ShapeKind.CUBE:
            vol = self.calc.compute(shape, Metric.VOLUME)
            return 1.2 * vol
        if shape.kind == ShapeKind.SPHERE:
            vol = self.calc.compute(shape, Metric.VOLUME)
            return 1.0 * vol + 10
        return 0


class LegendBuilder:
    def legend_symbol(self, shape):
        if shape.kind == ShapeKind.RECTANGLE:
            return "▭"
        if shape.kind == ShapeKind.CIRCLE:
            return "◯"
        if shape.kind == ShapeKind.TRIANGLE:
            return "△"
        if shape.kind == ShapeKind.CUBE:
            return "⬛"
        if shape.kind == ShapeKind.SPHERE:
            return "◯"
        return "?"


class CollisionEngine:
    def bounding_box(self, shape):
        if shape.kind == ShapeKind.RECTANGLE:
            return BoundingBox(shape.width, shape.height)
        if shape.kind == ShapeKind.CIRCLE:
            d = 2 * shape.radius
            return BoundingBox(d, d)
        if shape.kind == ShapeKind.TRIANGLE:
            max_side = max(shape.a, shape.b, shape.c)
            avg = (shape.a + shape.b + shape.c - max_side) / 2.0
            return BoundingBox(max_side, avg)
        if shape.kind == ShapeKind.CUBE:
            return BoundingBox(shape.edge, shape.edge)
        if shape.kind == ShapeKind.SPHERE:
            d = 2 * shape.radius
            return BoundingBox(d, d)
        return BoundingBox(0, 0)

    def overlaps(self, a, b):
        A = self.bounding_box(a)
        B = self.bounding_box(b)
        return (A.width * A.height) > 0 and (B.width * B.height) > 0


class ShapeReport:
    def __init__(self):
        self.calc = MetricCalculator()
        self.ser = ShapeSerializer()
        self.rnd = ShapeRenderer()
        self.col = CollisionEngine()
        self.price = ShapePricing()
        self.legend = LegendBuilder()

    def summarize(self, shapes):
        sb = []
        sb.append("=== Shape Report (OCP-violating) ===\n")
        for s in shapes:
            sb.append(f"ID {s.id} {s.kind.name} color={s.color} layer={s.layer}\n")
            sb.append(f"  CSV: {self.ser.to_csv_row(s)}\n")
            sb.append(f"  SVG: {self.rnd.render_pseudo_svg(s)}\n")
            sb.append(f"  Legend: {self.legend.legend_symbol(s)}\n")
            sb.append("  Metrics: ")
            sb.append(f" area={self.calc.compute(s, Metric.AREA)}")
            sb.append(f" perim={self.calc.compute(s, Metric.PERIMETER)}")
            sb.append(f" diag={self.calc.compute(s, Metric.DIAGONAL)}")
            if isinstance(s, ThreeDShape):
                sb.append(f" vol={self.calc.compute(s, Metric.VOLUME)}")
            sb.append("\n")
            sb.append(f"  BBox: {self.col.bounding_box(s)}\n")
            sb.append(f"  Price: {self.price.price(s)}\n\n")
        return "".join(sb)



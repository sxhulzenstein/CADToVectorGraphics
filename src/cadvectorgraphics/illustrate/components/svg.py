import logging
from enum import Enum
from numpy import ndarray, array, transpose, stack
from numpy.linalg import norm
from ...util.color import RGBA
from ...util.geometry import normalize
from ...illustrate.components.style import ArrowStyle


class SVGElementType(Enum):
    SVG = 1
    GROUP = 2
    POLYGON = 3
    LINE = 4
    PATH = 5
    TEXT = 6
    STYLE = 7
    ANY = 8
    DEVS = 9
    LINEAR_GRADIENT = 10
    STOP = 11


class SVGElement:
    def _substitude_entry_by_key(self, key: str, newkey: str):
        if key in self._args.keys():
            value = self._args.pop(key)
            self._args[newkey] = value

    def _substitute_entry_keys(self) -> None:
        self._substitude_entry_by_key("fillopacity", "fill-opacity")
        self._substitude_entry_by_key("strokewidth", "stroke-width")
        self._substitude_entry_by_key("strokeopacity", "stroke-opacity")
        self._substitude_entry_by_key("strokelinejoin", "stroke-linejoin")
        self._substitude_entry_by_key("strokelinecap", "stroke-linecap")
        self._substitude_entry_by_key("styleclass", "class")
        self._substitude_entry_by_key("strokedasharray", "stroke-dasharray")
        self._substitude_entry_by_key("stopcolor", "stop-color")
        self._substitude_entry_by_key("stopopacity", "stop-opacity")


    def __init__(self, element_type: SVGElementType, **kwargs) -> None:
        self._type: SVGElementType = element_type
        self._args: dict = kwargs
        self._contents: list[SVGElement] = []
        self._substitute_entry_keys()

    def append(self, contents) -> None:
        if contents is None:
            return
        if type(contents) is list:
            logging.warning("Contents is a list. Using extend instead of append.")
            self._contents.extend(contents)

        self._contents.append(contents)

    def extend(self, contents: list):
        if contents is None:
            return
        self._contents.extend(contents)

    def _write_additional_arguments(self) -> str:
        contents = [f"{key}=\"{content}\"" for key, content in list(self._args.items())]
        return " ".join(contents)

    def write(self, output_list: list[str]) -> None:
        arg_str: str = self._write_additional_arguments()

        if self._type == SVGElementType.SVG:
            output_list.append("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n""")
            output_list.append(f"<svg {arg_str}>\n")
            for content in self._contents:
                content.write(output_list)
            output_list.append("</svg>\n")
            return

        if self._type == SVGElementType.GROUP:
            output_list.append(f"<g {arg_str} >\n")
            for content in self._contents:
                content.write(output_list)
            output_list.append("</g>\n")
            return

        if self._type == SVGElementType.STYLE:
            output_list.append(f"<style>\n")
            for content in self._contents:
                content.write(output_list)
            output_list.append("</style>\n")
            return

        if self._type == SVGElementType.LINE:
            output_list.append(f"<line {arg_str} />\n")
            return

        if self._type == SVGElementType.POLYGON:
            output_list.append(f"<polygon {arg_str} />\n")
            return

        if self._type == SVGElementType.PATH:
            output_list.append(f"<path {arg_str} />\n")
            return

        if self._type == SVGElementType.TEXT:
            output_list.append(f"<text {arg_str}>\n")
            for content in self._contents:
                content.write(output_list)
            output_list.append("</text>")
            return

        if self._type == SVGElementType.ANY:
            output_list.append(str(self._args["content"]) + "\n")
            return

        if self._type == SVGElementType.DEVS:
            output_list.append("<defs>\n")
            for content in self._contents:
                content.write(output_list)
            output_list.append("</defs>\n")
            return

        if self._type == SVGElementType.LINEAR_GRADIENT:
            output_list.append(f"<linearGradient {arg_str}>\n")
            for content in self._contents:
                content.write(output_list)
            output_list.append("</linearGradient>\n")
            return

        if self._type == SVGElementType.STOP:
            output_list.append(f"<stop {arg_str}/>\n")
            return

    def __str__(self) -> str:
        output: list[str] = []
        self.write(output)
        return "".join(output)


class SVGHelper:
    @staticmethod
    def path(points: ndarray, stroke_color: RGBA, stroke_width: float, dash: tuple[float, ...] = (1, 0)) -> SVGElement:
        x, y = list(points[0, :]), list(points[1, :])
        if len(x) == 0 or len(y) == 0:
            path = []
        else:
            path = [f"M{x[0]},{y[0]}"]
            path.extend([f"L{xi},{yi}" for xi, yi in zip(x[1:], y[1:])])
        dasharray = ', '.join(str(v) for v in dash)
        return SVGElement(SVGElementType.PATH, d=' '.join(path), stroke=f"{stroke_color.to_hex()}", strokewidth=stroke_width,
                          strokeopacity=stroke_color.opacity, strokelinejoin="round",
                          strokelinecap="round", strokedasharray=dasharray, fill="none")

    @staticmethod
    def transform_group(scale: tuple[float, float], translate: tuple[float, float]) -> SVGElement:
        return SVGElement(SVGElementType.GROUP,
                          transform=f"scale({scale[0]}, {scale[1]}) translate({translate[0]},{translate[1]})")

    @staticmethod
    def devs() -> SVGElement:
        return SVGElement(SVGElementType.DEVS)

    @staticmethod
    def svg(width: float, height: float) -> SVGElement:
        return SVGElement(SVGElementType.SVG, xmlns="http://www.w3.org/2000/svg", width=f"{width}", height=f"{height}")

    @staticmethod
    def polygon(points: ndarray, fill: RGBA | str, stroke: RGBA, width: float, dash: tuple[int, ...] = (1, 0)) -> SVGElement:
        x, y = list(points[0, :]), list(points[1, :])
        outline = ' '.join(f"{xi},{yi}" for xi, yi in zip(x, y))
        dasharray = ', '.join(str(v) for v in dash)

        fill_color: str = fill if type(fill) is str else f"{fill.to_hex()}"

        return SVGElement(SVGElementType.POLYGON, points=outline, strokewidth=width, strokeopacity=stroke.opacity,
                          strokelinejoin="round", fill=fill_color,
                          fillopacity=1.0, stroke=f"{stroke.to_hex()}",
                          strokedasharray=dasharray)

    @staticmethod
    def style_group(stroke_color: RGBA, stroke_width: float, dash: tuple[float, ...] = (1, 0),
                    fill_color: RGBA = RGBA(0, 0, 0, 0)) -> SVGElement:
        dasharray = ', '.join(str(v) for v in dash)

        return SVGElement(SVGElementType.GROUP, stroke=f"{stroke_color.to_hex()}", strokewidth=stroke_width,
                          strokeopacity=stroke_color.opacity,
                          fill=f"{fill_color.to_hex()}", fillopacity=fill_color.opacity, strokelinejoin="round",
                          strokelinecap="round", strokedasharray=dasharray)

    @staticmethod
    def line(p0: ndarray, p1: ndarray, stroke_color: RGBA, stroke_width: float) -> SVGElement:
        return SVGElement(SVGElementType.LINE, x1=p0[0], y1=p0[1], x2=p1[0], y2=p1[1],
                          stroke=f"{stroke_color.to_hex()}", strokewidth=stroke_width, strokelinecap="round")

    @staticmethod
    def style():
        return SVGElement(SVGElementType.STYLE)

    @staticmethod
    def text(p: ndarray, text: str, style: str) -> SVGElement:
        text_element = SVGElement(SVGElementType.TEXT, x=p[0], y=p[1], styleclass=style)
        text_element.append(SVGElement(SVGElementType.ANY, content=text))
        return text_element

    @staticmethod
    def arrow(p0: ndarray, p1: ndarray, unit_length: float, style: ArrowStyle) -> SVGElement:
        actual_length: float = norm(p1 - p0)
        adjusted_arrow_head_length = style.head_length * actual_length / unit_length
        n01: ndarray = normalize(p1 - p0).flatten()
        n01_ortho: ndarray = n01[array((1, 0))] * array((1, - 1))
        p2 = p0 + (actual_length * 1.25) * n01
        q0 = p1 - adjusted_arrow_head_length * n01 - n01_ortho * style.head_width / 2
        q1 = p1 - adjusted_arrow_head_length * n01 + n01_ortho * style.head_width / 2

        group = SVGHelper.transform_group((1, 1), (0, 0))
        group.append(SVGHelper.line(p0, p1, style.color, style.stroke_width))
        group.append(SVGHelper.polygon(transpose(stack((p1, q0, q1))), style.color, style.color, style.stroke_width))
        if style.label is not None:
            style_element = SVGHelper.style()
            style_element.append(create_font_class(style.label, style.font_size, style.color))
            group.append(style_element)

            # automatic label positioning to avoid overlapping
            dx = - style.font_size if sum(n01 * array((1, 0))) < 0 else 0
            dy = style.font_size if - sum(n01 * array((0, 1))) < 0 else 0

            text = SVGHelper.text(array((p2[0] + dx, p2[1] + dy)), style.label, style.label)

            group.append(text)
        return group

    @staticmethod
    def gradient(gradient_id: str, angle: float, color: RGBA) -> SVGElement:
        grad = SVGElement(SVGElementType.LINEAR_GRADIENT, id=gradient_id, x1="0%", y1="0%", x2="100%",
                          y2="100%", gradientTransform=f"rotate({angle}, 0.5, 0.5)")
        grad.append(SVGHelper.gradient_stop(0, color, 1.0))
        grad.append(SVGHelper.gradient_stop(100, RGBA(*color.rgb(), 0), 0.0))
        return grad

    @staticmethod
    def gradient_stop(offset: float, stop_color: RGBA, stop_opacity: float) -> SVGElement:
        return SVGElement(SVGElementType.STOP, offset=f"{offset}%", stopcolor=stop_color.to_hex(),
                          stopopacity=stop_opacity)


def create_font_class(name: str, size: float, fill: RGBA, size_unit: str = "pt", style: str = "italic",
                      font: str = "serif") -> SVGElement:
    fontstyle: str = f"font: {style} {size}{size_unit} {font}; fill: {fill.to_hex()};"
    return SVGElement(SVGElementType.ANY, content=f".{name} {{ {fontstyle} }}")

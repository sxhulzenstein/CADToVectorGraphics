from ..render.render import VirtualRenderer
from ..render.components.geometry import PlanarEdgesCollection, PlanarFacet, EdgeRepresentationType
from numpy import ndarray
from ..illustrate.components.style import LineStyle, FaceStyle, CoordSystemStyle
from numpy import array, any, isnan
from ..illustrate.components.svg import SVGElement, SVGHelper
from bs4 import BeautifulSoup
from ..util.color import RGBA


class Image:
    def __init__(self, renderer: VirtualRenderer) -> None:
        self._renderer: VirtualRenderer = renderer
        self._line_styles: list[LineStyle] = []
        self._facet_style: FaceStyle | None = None
        self._coord_style: CoordSystemStyle | None = None
        self._margin: tuple[int, int] = (0, 0)
        self._bounding_box: ndarray = self._renderer.bounding_box
        self._size: tuple[int, int] = int(self._bounding_box[0, 2]), int(self._bounding_box[1, 2])
        self._zoom: tuple[float, float] = (1., 1.)
        self._scale: tuple[float, float] = (1, 1)

    @property
    def line_style(self) -> list[LineStyle]:
        return self._line_styles

    @property
    def size(self) -> tuple[int, int]:
        dx = self._bounding_box[0, 2] * self._zoom[0] + self._margin[0] * 2
        dy = self._bounding_box[1, 2] * self._zoom[1] + self._margin[1] * 2

        if self._coord_style is not None:
            dx += self._coord_style.margin * 2
            dy += self._coord_style.margin * 2

        return int(dx), int(dy)

    @property
    def width(self) -> int:
        return int(self.size[0] * self._scale[0])

    @property
    def height(self) -> int:
        return int(self.size[1] * self._scale[1])

    @property
    def margins(self) -> tuple[int, int]:
        return self._margin

    @margins.setter
    def margins(self, margins: tuple[int, int]) -> None:
        self._margin = margins

    @property
    def zoom(self) -> tuple[float, float]:
        return self._zoom

    @zoom.setter
    def zoom(self, zoom: tuple[float, float]) -> None:
        self._zoom = zoom

    @property
    def scale(self) -> tuple[float, float]:
        return self._scale

    @scale.setter
    def scale(self, scale: tuple[float, float]) -> None:
        self._scale = scale

    @property
    def translate(self) -> tuple[int, int]:
        dx = - self._bounding_box[0, 0]
        dy = - self._bounding_box[1, 1]

        return dx, dy

    def bounding_box(self) -> ndarray:
        bb = self._bounding_box
        #bb[0, :] *= self._zoom[0]
        #bb[1, :] *= self._zoom[1]
        return bb

    def add_line_style(self, line_style: LineStyle) -> None:
        self._line_styles.append(line_style)

    def set_face_style(self, face_style: FaceStyle) -> None:
        self._facet_style = face_style

    def set_coord_system_style(self, coord_system_style: CoordSystemStyle) -> None:
        self._coord_style = coord_system_style

    def _write_facet(self, facet: PlanarFacet) -> SVGElement:
        width = 0.03
        dash = (1, 0)
        stroke_color = facet.color
        if self._facet_style is not None:
            width = self._facet_style.width
            stroke_color = str(self._facet_style.color)
            if self._facet_style.dash is not None:
                dash = self._facet_style.dash

        return SVGHelper.polygon(facet.points, facet.color, stroke_color, width, dash)

    def _write_surface(self) -> SVGElement:
        surface = SVGHelper.transform_group((1, 1), (0, 0))
        for facet in self._renderer.facets:
            surface.append(self._write_facet(facet))
        return surface

    """
    @staticmethod
    def _write_wires(edges: PlanarEdgesCollection) -> list[SVGElement]:
        elements = []
        for edge in edges.edges():
            elements.append(SVGHelper.path(edge.points))
        return elements

    
    def _write_wires_collection(self) -> list[SVGElement]:

        hierarchy: list = [
            EdgeRepresentationType.HIDDENSMOOTHWIRE,
            EdgeRepresentationType.HIDDENSHARPWIRE,
            EdgeRepresentationType.VISIBLESMOOTHWIRE,
            EdgeRepresentationType.VISIBLESHARPWIRE,
            EdgeRepresentationType.VISIBLEOUTLINE
        ]
        groups = []

        for edgeGroup in hierarchy:

            edges: PlanarEdgesCollection | None = next(
                (visibleEdges for visibleEdges in self._renderer.edges if visibleEdges.edges_type == edgeGroup), None)
            if edges is None:
                continue

            line_style: LineStyle | None = next((style for style in self._line_styles if style.type == edgeGroup), None)
            if line_style is None:
                continue
            if line_style.dash is not None:
                group = SVGHelper.style_group(line_style.color, line_style.width, line_style.dash)
            else:
                group = SVGHelper.style_group(line_style.color, line_style.width)

            group.extend(self._write_wires(edges))
            groups.append(group)
        return groups
    """
    @staticmethod
    def _write_wires(edges: PlanarEdgesCollection, stroke_color: RGBA, stroke_width: float, dash: tuple = (1.0, 0) ) -> list[SVGElement]:
        elements = []
        for edge in edges.edges():
            elements.append(SVGHelper.path(edge.points, stroke_color, stroke_width, dash))
        return elements

    def _write_wires_collection(self) -> list[SVGElement]:

        hierarchy: list = [
            EdgeRepresentationType.HIDDENSMOOTHWIRE,
            EdgeRepresentationType.HIDDENSHARPWIRE,
            EdgeRepresentationType.VISIBLESMOOTHWIRE,
            EdgeRepresentationType.VISIBLESHARPWIRE,
            EdgeRepresentationType.VISIBLEOUTLINE
        ]
        paths = []

        for edgeGroup in hierarchy:

            edges: PlanarEdgesCollection | None = next(
                (visibleEdges for visibleEdges in self._renderer.edges if visibleEdges.edges_type == edgeGroup), None)
            if edges is None:
                continue

            line_style: LineStyle | None = next((style for style in self._line_styles if style.type == edgeGroup), None)
            if line_style is None:
                continue
            if line_style.dash is not None:
                paths.extend(self._write_wires(edges, line_style.color, line_style.width, line_style.dash))
            else:
                paths.extend(self._write_wires(edges, line_style.color, line_style.width))
        return paths

    def _write_coordinate_system(self) -> SVGElement | None:
        if self._coord_style is None:
            return None

        size_factor = self._coord_style.size / 2
        anchor = array([self._coord_style.size, self.height / self._scale[1] - self._coord_style.size])
        x = self._renderer.system.x * size_factor
        y = self._renderer.system.y * size_factor
        z = self._renderer.system.z * size_factor

        group = SVGHelper.transform_group((1, 1), (0, 0))

        if not any(isnan(x)):
            group.append(SVGHelper.arrow(anchor, anchor + x * array((1, -1)), size_factor, self._coord_style.x))

        if not any(isnan(y)):
            group.append(SVGHelper.arrow(anchor, anchor + y * array((1, -1)), size_factor, self._coord_style.y))

        if not any(isnan(z)):
            group.append(SVGHelper.arrow(anchor, anchor + z * array((1, -1)), size_factor, self._coord_style.z))

        return group

    def _write(self) -> str:
        svg = SVGHelper.svg(self.width, self.height)
        coord_group = SVGHelper.transform_group(self.scale, (0, 0))
        coord_sys_margin = self._coord_style.margin if self._coord_style is not None else 0
        margin_group = SVGHelper.transform_group((1, 1), (coord_sys_margin, coord_sys_margin))
        bounding_box_group = SVGHelper.transform_group(
            (self._zoom[0], self._zoom[1]),
            (self.margins[0] / (self._zoom[0] * self._scale[0]), self.margins[1] / (self._zoom[1] * self._scale[1])))
        geom_group = SVGHelper.transform_group((1, - 1), self.translate)
        geom_group.append(self._write_surface())
        geom_group.extend(self._write_wires_collection())
        bounding_box_group.append(geom_group)
        margin_group.append(bounding_box_group)
        coord_group.append(margin_group)

        coord_group.append(self._write_coordinate_system())
        svg.append(coord_group)
        return str(svg)

    def write(self, directory: str | None = None) -> None:
        name = self._renderer.scene.part.name
        if directory is None:
            filepath = f"{name}.svg"
        else:
            filepath = f"{directory}/{name}.svg"
        f = open(filepath, "w")
        f.write(self._write())
        f.close()

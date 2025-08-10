from numpy import array, zeros, transpose, ndarray, min, max, arctan2, rad2deg
from ...compose.components.geometry.mesh import Geometry, Topology
from ...util.color import RGBA
from ...util.exceptions import WrongGeometryDimensionException
from enum import Enum
from cadquery.occ_impl.shapes import Edge
from OCP.GCPnts import GCPnts_QuasiUniformDeflection as CurvePointsGenerator
from functools import cached_property
from uuid import uuid4


class PlanarFacet:
    def __init__(self, points: ndarray, face_color: RGBA,
                 node_color: list[RGBA] | None = None, ids: list[str] | None = None) -> None:
        """
        Create a two dimensional geometry of a facet

        Parameters:
            points ( ndarray ): a ( 2 x N ) numpy array containing the nodes of the face
            face_color ( RGBA ): color of the facet
        """
        self.points: ndarray = points
        self.face_color: RGBA = face_color
        self.node_color: list[RGBA] | None = node_color
        self.gradient_uuids = ids

    @staticmethod
    def _angle(p0: ndarray, p1: ndarray) -> float:
        v = p1 - p0
        a = rad2deg(arctan2(v[1], v[0]))
        return a if a >= 0.0 else a + 360.0

    @cached_property
    def gradient_angles(self) -> list[float] | None:
        if not self.node_color:
            return

        if len(self.node_color) == 3:
            return [
                PlanarFacet._angle(self.points[:, 0], 0.5 * (self.points[:, 1] + self.points[:, 2])),
                PlanarFacet._angle(self.points[:, 1], 0.5 * (self.points[:, 2] + self.points[:, 0])),
                PlanarFacet._angle(self.points[:, 2], 0.5 * (self.points[:, 0] + self.points[:, 1]))
            ]

        if len(self.node_color) == 4:
            a1 = PlanarFacet._angle(self.points[:, 0], self.points[:, 2])
            a2 = PlanarFacet._angle(self.points[:, 1], self.points[:, 3])
            return [a1, a2, a1 + 180.0 if a1 <= 180.0 else a1 - 180.0, a2 + 180.0 if a2 <= 180.0 else a2 - 180.0]

        raise NotImplementedError(len(self.node_color))


class PlanarMeshRepresentation:
    def __init__(self, geometry: list[Geometry], topology: list[Topology]) -> None:
        """
        Create a planar mesh geometry for multiple solids

        Parameters:
            geometry ( list[ Geometry ] ): planar geometries
            topology ( list[ Topology ] ): list of topologies
        """
        if not geometry[0].dimension == 2:
            raise WrongGeometryDimensionException(2, geometry[0].dimension)

        self._geometry: list[Geometry] = geometry
        self._topology: list[Topology] = topology
        self._visible: ndarray | None = None
        self._face_colors: list[ndarray] = []
        self._node_colors: list[ndarray] | None = None
        self._node_uuids: list[list[list[str]]] | None = None

    @property
    def sorted(self) -> ndarray:
        """
        Get the sorted indices of faces

        Returns:
            ndarray: a ( 2 x N ) numpy array where the first row corresponds to the solid index and the second row to the face index
        """
        if self._visible is None:
            raise Exception()
        return self._visible

    @sorted.setter
    def sorted(self, ids: ndarray) -> None:
        """
        Set the sorted indices of faces

        Parameters:
            ids ( ndarray ): a ( 2 x N ) numpy array where the first row corresponds to the solid index and the second row to the face index
        """
        self._visible = ids

    @property
    def face_colors(self) -> list[ndarray]:
        """
        Get the colors for each face of each solid

        Returns:
            list[ ndarray ]: element colors as ( 4 x N ) numpy array for each solid
        """
        return self._face_colors

    @face_colors.setter
    def face_colors(self, colors: list[ndarray]) -> None:
        """
        Set the colors for each face of each solid

        Parameters:
            colors ( list[ ndarray ] ): element colors as ( 4 x N ) numpy array for each solid
        """
        self._face_colors = colors

    @property
    def node_colors(self) -> list[ndarray]:
        return self._node_colors

    @node_colors.setter
    def node_colors(self, colors: list[ndarray]) -> None:
        self._node_uuids = [[[str(uuid4()).replace("-", "")
                              for i in range(len(node_ids))]
                             for node_ids in t.base.values()]
                            for t in self._topology]
        self._node_colors = colors

    def facet(self, mesh_id: int, facet_id: int) -> PlanarFacet:
        """
        Extract a specified facet as PlanarFacet

        Parameters:
            mesh_id ( int ): mesh index where the face is located
            facet_id ( int ): face index for the required face

        Returns:
            PlanarFacet: requested face information
        """
        if facet_id not in self.sorted[1, :]:
            raise Exception()

        p: ndarray = self._geometry[int(mesh_id)].base[:, array(self._topology[int(mesh_id)][int(facet_id)]).flatten()]
        if self._face_colors is None:
            raise Exception()

        c_face: ndarray = self._face_colors[int(mesh_id)][:, int(facet_id)].flatten()
        if self._node_colors is None:
            return PlanarFacet(p, RGBA(*c_face))

        node_ids = self._topology[int(mesh_id)].base[facet_id]
        c_nodes: ndarray = self._node_colors[int(mesh_id)][:, node_ids]
        return PlanarFacet(p, RGBA(*c_face),
                           [RGBA(*c_nodes[:, i].flatten()) for i in range(c_nodes.shape[1])],
                           self._node_uuids[int(mesh_id)][int(facet_id)]
                           )

    def __iter__(self):
        """
        Create an iterator to iterate over all PlanarFacets

        Returns:
            PlanarMeshRepresentation: iterator initialized
        """
        self._index = 0
        return self

    def __next__(self) -> PlanarFacet:
        """
        Move the iterator to the next Facet

        Returns:
            PlanarFacet: The next PlanarFacet
        """
        index = self._index
        self._index += 1

        if not index < self._visible.shape[1]:
            raise StopIteration()

        return self.facet(*self._visible[:, index].flatten())

    @cached_property
    def bounding_box(self) -> ndarray:
        """
        Calculate the two-dimensional boundingbox by using all geometry objects

        Returns:
            ndarray: a ( 2 x 3 ) numpy array containing the mins, maxs and lengths for the x and y direction on the plane
        """
        bb = zeros((2, 3))

        geometries: list[ndarray] = [geom.base for geom in self._geometry]
        mins = zeros((2, len(geometries)))
        maxs = zeros((2, len(geometries)))
        for index in range(len(geometries)):
            mins[:, index] = min(geometries[index], axis=1)
            maxs[:, index] = max(geometries[index], axis=1)

        bb[:, 0] = min(mins, axis=1)
        bb[:, 1] = max(maxs, axis=1)
        bb[:, 2] = bb[:, 1] - bb[:, 0]
        return bb


class EdgeRepresentationType(Enum):
    """
    Enum for classifying the edges
    """
    VISIBLEOUTLINE = 1
    HIDDENSMOOTHWIRE = 2
    VISIBLESMOOTHWIRE = 3
    HIDDENSHARPWIRE = 4
    VISIBLESHARPWIRE = 5


class PlanarEdge:
    def __init__(self, points: ndarray) -> None:
        self._points: ndarray = points

    @property
    def start(self) -> ndarray:
        return self._points[:, 0]

    @property
    def end(self) -> ndarray:
        return self._points[:, -1]

    @property
    def points(self) -> ndarray:
        return self._points


class PlanarEdgesCollection:
    def __init__(self, edges: list[Edge], edge_type: EdgeRepresentationType) -> None:
        """
        Create a planar edges geometry

        Parameters:
            edges ( list[ Edge ] ): a list containing cadquery edges
            edge_type ( EdgeRepresentationType ): type of geometry for all edges in list
        """
        self._wires: list[PlanarEdge] = PlanarEdgesCollection._create_wires_from_edges(edges)
        self._type: EdgeRepresentationType = edge_type

    @staticmethod
    def _adapt_edge_into_curve(edge: Edge):
        return edge._geomAdaptor()

    @staticmethod
    def _generate_points_on_wire_curve(edge: Edge) -> ndarray:
        curve = PlanarEdgesCollection._adapt_edge_into_curve(edge)
        start: float = curve.FirstParameter()
        end: float = curve.LastParameter()
        tolerance: float = 1.e-2
        points: CurvePointsGenerator = CurvePointsGenerator(curve, tolerance, start, end)

        if not points.IsDone():
            return array([[], []])

        return transpose(array([[points.Value(i + 1).X(), points.Value(i + 1).Y()]
                                for i in range(points.NbPoints())]))

    @staticmethod
    def _create_wires_from_edges(edges: list[Edge]) -> list[PlanarEdge]:
        return [PlanarEdge(PlanarEdgesCollection._generate_points_on_wire_curve(edge)) for edge in edges]

    @property
    def edges_type(self) -> EdgeRepresentationType:
        """
        Get the type of the edges
        """
        return self._type

    def edges(self) -> list[PlanarEdge]:
        """
        Get the planar edges
        """
        return self._wires


class PlanarCoordinateSystemRepresentation:
    def __init__(self, x: ndarray, y: ndarray, z: ndarray) -> None:
        """
        Create a planar coordinate system

        Parameters:
            x ( ndarray ): x-axis vector in 2D coordinates
            y ( ndarray ): y-axis vector in 2D coordinates
            z ( ndarray ): z-axis vector in 2D coordinates
        """
        self._x = x
        self._y = y
        self._z = z
        self._anchor = array((0.0, 0.0))

    @property
    def anchor(self) -> ndarray:
        """
        Get the origin of the coordinate system

        Returns:
            ndarray: anchor as 2D coordinates
        """
        return self._anchor

    @anchor.setter
    def anchor(self, anchor: ndarray) -> ndarray:
        """
        Set the anchor/ origin of the coordinate system

        Parameters:
            anchor ( ndarray ): new anchor of the coordinate system
        """
        self._anchor = anchor

    @property
    def x(self) -> ndarray:
        """
        Get the x direction of the coordinate system

        Returns:
            ndarray: x direction as numpy array
        """
        return self._x

    @property
    def y(self) -> ndarray:
        """
        Get the y direction of the coordinate system

        Returns:
            ndarray: y direction as numpy array
        """
        return self._y

    @property
    def z(self) -> ndarray:
        """
        Get the z direction of the coordinate system

        Returns:
            ndarray: z direction as numpy array
        """
        return self._z

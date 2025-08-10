from typing import Optional
from ..compose.compose import VirtualScene
from ..render.components.project import Projector
from ..render.components.geometry import PlanarMeshRepresentation, PlanarEdgesCollection, \
    PlanarCoordinateSystemRepresentation
from numpy import ndarray


class ColorTable:
    ...


class VirtualRenderer:
    def __init__(self, scene: VirtualScene) -> None:
        """
        Create a renderer object

        Parameters:
            scene ( VirtualScene ): the renderer is created by passing a scene
        """
        self._scene: VirtualScene = scene
        self._projector: Projector = Projector(scene.camera)
        self._facets: PlanarMeshRepresentation | None = None
        self._edges: list[PlanarEdgesCollection] = []
        self._coordinate_system: PlanarCoordinateSystemRepresentation | None = None

    @property
    def scene(self) -> VirtualScene:
        """
        Get the scene within the renderer

        Returns:
            VirtualScene: the internal scene
        """
        return self._scene

    def render(self, use_nodes: bool = False, color_table: ColorTable | None = None) -> None:
        """
        Render the part using the camera, the part itself and its surrounding lights

        Parameters:
            use_nodes: Interpolate colors over face
            color_table ( Optional[ ColorTable ] = None ): color table ( not implemented yet )
        """
        self._facets = self._projector.project_facets(self._scene.part)
        self._facets.sorted = self._projector.determine_visible_faces(self._scene.part)
        self._facets.face_colors = self._projector.determine_face_colors(
            self._scene.part, self._scene.lights, color_table)
        if use_nodes:
            self._facets.node_colors = self._projector.determine_node_colors(
                self._scene.part, self._scene.lights, color_table)

        self._edges = self._projector.project_curves_and_edges(self._scene.part)
        self._coordinate_system = self._projector.get_coordinate_system()

    @property
    def bounding_box(self) -> ndarray:
        """
        Get the bounding box of the 2D mesh

        Returns:
            ndarray: bounding box as ( 2 x 3 ) numpy array
        """
        return self._facets.bounding_box

    @property
    def system(self) -> PlanarCoordinateSystemRepresentation:
        """
        Get the coordinate system geometry

        Returns:
            PlanarCoordinateSystemRepresentation: 2D coordinate system
        """
        return self._coordinate_system

    @property
    def facets(self) -> PlanarMeshRepresentation | None:
        return self._facets

    @property
    def edges(self) -> list[PlanarEdgesCollection]:
        return self._edges

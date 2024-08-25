from typing import Optional
from cadvectorgraphics.compose.compose import VirtualScene
from cadvectorgraphics.render.components.project import Projector
from cadvectorgraphics.render.components.geometry import PlanarMeshRepresentation, PlanarEdgesRepresentation, PlanarCoordinateSystemRepresentation
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
        self._projector: Projector = Projector( scene.camera )
        self._facets: PlanarMeshRepresentation | None = None
        self._edges: list[ PlanarEdgesRepresentation ] = []
        self._coordinatesystem: PlanarCoordinateSystemRepresentation | None = None

    @property
    def scene( self ) -> VirtualScene:
        """
        Get the scene within the renderer

        Returns:
            VirtualScene: the internal scene
        """
        return self._scene

    def render( self, colorTable: Optional[ ColorTable ] = None ) -> None:
        """
        Render the part using the camera, the part itself and its surounding lights

        Parameters:
            colorTable ( Optional[ ColorTable ] = None ): color table ( not implemented yet )
        """
        self._facets = self._projector.projectFacets( self._scene.part )
        self._facets.sorted = self._projector.determineVisibleFaces( self._scene.part )
        self._facets.colors = self._projector.determineFaceColors( self._scene.part, self._scene._lights, colorTable )
        self._edges = self._projector.projectCurvesAndEdges( self._scene.part )
        self._coordinatesystem = self._projector.getCoordinateSystem()
    
    def boundingBox( self ) -> ndarray:
        """
        Get the bounding box of the 2D mesh

        Returns:
            ndarray: bounding box as ( 2 x 3 ) numpy array
        """
        return self._facets.boundingBox()
    
    def system( self ) -> PlanarCoordinateSystemRepresentation:
        """
        Get the coordinate system representation

        Returns:
            PlanarCoordinateSystemRepresentation: 2D coordinate system
        """
        return self._coordinatesystem
from typing import Optional
from compose.compose import VirtualScene
from render.components.project import Projector
from render.components.geometry import PlanarMeshRepresentation, PlanarEdgesRepresentation, PlanarCoordinateSystemRepresentation
from compose.components.representation.mesh import Geometry, Topology
from compose.components.bind import PartRepresentation
from numpy.typing import NDArray
from numpy import array, min, max, zeros
from util.color import RGBA

class ColorTable:
    ...

class VirtualRenderer:
    def __init__(self, scene: VirtualScene) -> None:
        self._scene: VirtualScene = scene
        self._projector: Projector = Projector( scene.camera )
        self._facets: PlanarMeshRepresentation | None = None
        self._edges: list[ PlanarEdgesRepresentation ] = []
        self._coordinatesystem: PlanarCoordinateSystemRepresentation | None = None

    @property
    def scene( self ) -> VirtualScene:
        return self._scene

    def selectCamera( self, cameraId: int ) -> None:
        self._scene.setCurrentCamera( cameraId )

    def render( self, colorTable: Optional[ ColorTable ] = None ): 
        self._facets = self._projector.projectFacets( self._scene.part )
        self._facets.sorted = self._projector.determineVisibleFaces( self._scene.part )
        self._facets.colors = self._projector.determineFaceColors( self._scene.part, self._scene._lights, colorTable )
        self._edges = self._projector.projectCurvesAndEdges( self._scene.part )
        self._coordinatesystem = self._projector.getCoordinateSystem()
    
    def boundingBox( self ) -> NDArray:
        return self._facets.boundingBox()
    
    def system( self ) -> PlanarCoordinateSystemRepresentation:
        return self._coordinatesystem
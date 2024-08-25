from numpy.typing import NDArray
from numpy import array, zeros, transpose, ndarray, min, max, int64
from cadvectorgraphics.compose.components.representation.mesh import Geometry, Topology
from cadvectorgraphics.util.color import RGBA
from enum import Enum
from cadquery.occ_impl.shapes import Edge
from OCP.GCPnts import GCPnts_QuasiUniformDeflection as CurvePointsGenerator


class PlanarFacet:
    def __init__( self, points: ndarray, color: RGBA ) -> None:
        """
        Create a two dimensional representation of a facet

        Parameters:
            points ( ndarray ): a ( 2 x N ) numpy array containing the nodes of the face
            color ( RGBA ): color of the facet
        """
        self.points: NDArray = points
        self.color: RGBA = color

class PlanarMeshRepresentation:
    def __init__( self, geometry: list[ Geometry ], topology: list[ Topology ] ) -> None:
        """
        Create a planar mesh representation for multiple solids

        Parameters:
            geometry ( list[ Geometry ] ): planar geometries
            topology ( list[ Topology ] ): list of topologies
        """
        if not geometry[ 0 ].dimension == 2:
            raise Exception()

        self._geometry: list[ Geometry ] = geometry
        self._topology: list[ Topology ] = topology
        self._visible: ndarray | None = None
        self._colors: list[ ndarray ] = []
    
    @property
    def sorted( self ) -> ndarray:
        """
        Get the sorted indices of faces

        Returns:
            ndarray: a ( 2 x N ) numpy array where the first row corresponds to the solid index and the second row to the face index
        """
        if self._visible is None:
            raise Exception()
        return self._visible
    
    @sorted.setter
    def sorted( self, ids: ndarray ) -> None:
        """
        Set the sorted indices of faces

        Parameters:
            ids ( ndarray ): a ( 2 x N ) numpy array where the first row corresponds to the solid index and the second row to the face index
        """
        self._visible = ids
    
    @property
    def colors( self ) -> list[ ndarray ]:
        """
        Get the colors for each face of each solid

        Returns:
            list[ ndarray ]: element colors as ( 4 x N ) numpy array for each solid
        """
        if self._colors is None:
            raise Exception()
        return self._colors
    
    @colors.setter
    def colors( self, colors: list[ ndarray ] ) -> None:
        """
        Set the colors for each face of each solid

        Parameters:
            colors ( list[ ndarray ] ): element colors as ( 4 x N ) numpy array for each solid
        """
        self._colors = colors

    def facet( self, meshId: int, facetId: int ) -> PlanarFacet:
        """
        Extract a specified facet as PlanarFacet

        Parameters:
            meshId ( int ): mesh index where the face is located
            facetId ( int ): face index for the required face

        Returns:
            PlanarFacet: requested face information
        """
        if not facetId in self.sorted[ 1, : ]:
            raise Exception()
        
        p: NDArray = self._geometry[ int( meshId ) ].base[ :, array( self._topology[ int( meshId ) ] [ int( facetId ) ] ).flatten() ]
        if self._colors is None:
            raise Exception()
        
        c: NDArray = self._colors[ int(meshId) ][ :, int(facetId) ].flatten()
        return PlanarFacet( p, RGBA( *c ) )
    
    def __iter__( self ):
        """
        Create an iterator to iterate over all PlanarFacets

        Returns:
            PlanarMeshRepresentation: iterator initialized
        """
        self._index = 0
        return self

    def __next__( self ) -> PlanarFacet:
        """
        Move the iterator to the next Facet

        Returns:
            PlanarFacet: The next PlanarFacet
        """
        index = self._index
        self._index += 1

        if not index < self._visible.shape[ 1 ]:
            raise StopIteration()

        return self.facet( *self._visible[ :, index ].flatten() )
    
    def boundingBox( self ) -> ndarray:
        """
        Calculate the two-dimensional boundingbox by using all geometry objects

        Returns:
            ndarray: a ( 2 x 3 ) numpy array containing the mins, maxs and lengths for the x and y direction on the plane
        """
        bb = zeros( ( 2, 3 ) )

        geometries: list[ ndarray ] = [ geom.base for geom in self._geometry ]
        mins = zeros( ( 2, len( geometries ) ) )
        maxs = zeros( ( 2, len( geometries ) ) )
        for index in range( len( geometries ) ):
            mins[ :, index ] = min( geometries[ index ], axis = 1 )
            maxs[ :, index ] = max( geometries[ index ], axis = 1 )

        bb[ :, 0 ] = min( mins, axis = 1 )
        bb[ :, 1 ] = max( maxs, axis = 1 )
        bb[ :, 2 ] = bb[ :, 1 ] - bb[ :, 0 ] 
        return bb 

class EdgeRepresentationType( Enum ):
    """
    Enum for classifying the edges
    """
    VISIBLEOUTLINE = 1
    HIDDENSMOOTHWIRE = 2
    VISIBLESMOOTHWIRE = 3
    HIDDENSHARPWIRE = 4 
    VISIBLESHARPWIRE = 5

class PlanarEdge:
    def __init__( self, points: NDArray ) -> None:
        self._points: NDArray = points

    @property
    def start( self ) -> NDArray:
        return self._points[ :, 0 ]

    @property
    def end( self ) -> NDArray:
        return self._points[ :, -1 ]
    
    @property
    def points( self ) -> NDArray:
        return self._points


class PlanarEdgesRepresentation:    
    def __init__( self, edges: list[ Edge ], edgeType: EdgeRepresentationType ) -> None:
        """
        Create a planar edges representation

        Parameters:
            edges ( list[ Edge ] ): a list containing cadquery edges
            edgeType ( EdgeRepresentationType ): type of representation for all edges in list
        """
        self._wires: list[ PlanarEdge ] = self._createWiresFromEdgeList( edges )
        self._type: EdgeRepresentationType = edgeType

    def _adaptEdgeIntoCurve(self, edge):
        return edge._geomAdaptor()

    def _generatePointsOnWireCurve(self, edge: Edge) -> NDArray:
        curve = self._adaptEdgeIntoCurve( edge )
        start: float = curve.FirstParameter()
        end: float = curve.LastParameter()
        tolerance: float = 1.e-2
        points: CurvePointsGenerator = CurvePointsGenerator( curve, tolerance, start, end )

        if not points.IsDone():
            raise Exception()
        
        return transpose( array( [ [ points.Value( i + 1 ).X(), points.Value( i + 1 ).Y() ] 
                                  for i in range( points.NbPoints() ) ] ) )

    def _createWiresFromEdgeList( self, edges: list[ Edge ] ) -> list[ PlanarEdge ]:
        mappedEdges: list[ PlanarEdge ] = []
        for edge in edges:
            mappedEdges.append( PlanarEdge( self._generatePointsOnWireCurve( edge ) ) )
        return mappedEdges

class PlanarCoordinateSystemRepresentation:
    def __init__( self, x: ndarray, y: ndarray, z: ndarray) -> None:
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
        self._anchor = array( ( 0.0, 0.0 ) )
    
    @property
    def anchor( self ) -> ndarray:
        """
        Get the origin of the coordinate system

        Returns:
            ndarray: anchor as 2D coordinates
        """
        return self._anchor
    
    @anchor.setter
    def anchor( self, anchor: ndarray ) -> ndarray:
        """
        Set the anchor/ origin of the coordinate system

        Parameters:
            anchor ( ndarray ): new anchor of the coordinate system
        """
        self._anchor = anchor
    
    @property
    def x( self ) -> ndarray:
        """
        Get the x direction of the coordinate system

        Returns:
            ndarray: x direction as numpy array
        """
        return self._x
    
    @property
    def y( self ) -> ndarray:
        """
        Get the y direction of the coordinate system

        Returns:
            ndarray: y direction as numpy array
        """
        return self._y
    
    @property
    def z( self ) -> ndarray:
        """
        Get the z direction of the coordinate system

        Returns:
            ndarray: z direction as numpy array
        """
        return self._z


from render.render import VirtualRenderer
from render.components.geometry import PlanarEdgesRepresentation, PlanarMeshRepresentation, PlanarFacet, EdgeRepresentationType
from numpy import ndarray
from illustrate.components.style import LineStyle, FaceStyle, CoordSystemStyle, ArrowStyle
from numpy import array, any, isnan, stack, transpose, zeros
from numpy.linalg import norm
from util.geometry import normalize
from util.color import RGBA
from illustrate.components.svg import SVGElement, SVGHelper, CreatefontClass

class Image:
    def __init__( self, renderer: VirtualRenderer ) -> None:
        self._renderer: VirtualRenderer = renderer
        self._lineStyles: list[ LineStyle ] = []
        self._faceStyle: FaceStyle | None = None
        self._coordStyle: CoordSystemStyle | None = None
        self._margin: tuple[ int, int ] = ( 0, 0 )
        self._boundingBox: ndarray = self._renderer.boundingBox()
        self._size: tuple[ int, int ] = self._boundingBox[ 0, 2 ], self._boundingBox[ 1, 2 ]
        self._zoom: tuple[ float, float ] = ( 1., 1.)
    
    @property
    def lineStyle( self ) -> list[ LineStyle ]:
        return self._lineStyles

    @property
    def dimensions( self ) -> tuple[ int, int ]:
        dx = int( ( self._size[ 0 ] + self._margin[ 0 ] * 2 ) * self._zoom[ 0 ] )
        dy = int( ( self._size[ 1 ] + self._margin[ 1 ] * 2 ) * self._zoom[ 1 ] )

        if self._coordStyle is not None:
            dx += self._coordStyle.size  * self._zoom[ 0 ]
            dy += self._coordStyle.size  * self._zoom[ 1 ]

        return dx, dy

    @property
    def width( self ) -> int:
        return self.dimensions[ 0 ]
    
    @property
    def height( self ) -> int:
        return self.dimensions[ 1 ]

    @property
    def margins( self ) -> tuple[ int, int ]:
        return self.margins

    @margins.setter
    def margins( self, margins: tuple[ int, int ] ) -> None:
        self._margin = margins
    
    @property
    def zoom( self ) -> tuple[ float, float ]:
        return self._zoom

    @zoom.setter
    def zoom( self, zoom: tuple[ float,float ] ) -> None:
        self._zoom = zoom

    @property
    def translate( self ) -> tuple[ int, int ]:
        dx = - self._boundingBox[ 0, 0 ] + self._margin[ 0 ]
        dy = - self._boundingBox[ 1, 1 ] - self._margin[ 1 ]

        if not self._coordStyle is None:
            dx += self._coordStyle.size
            self._renderer._coordinatesystem.anchor = array( 
                ( self._boundingBox[ 0, 0 ] - self._coordStyle.size + self._margin[ 0 ] / 2, self._boundingBox[ 1, 0 ] - self._coordStyle.size + self._margin[ 1 ] / 2 )  )

        return dx, dy
    
    def addLineStyle( self, linestyle: LineStyle ) -> None:
        self._lineStyles.append( linestyle )

    def setFaceStyle( self, facestyle: FaceStyle ) -> None:
        self._faceStyle = facestyle

    def setCoordSystemStyle( self, coordSystemStyle: CoordSystemStyle ) -> None:
        self._coordStyle = coordSystemStyle

        
class SVG( Image ):
    def __init__( self, renderer: VirtualRenderer ) -> None:
        super().__init__( renderer )

    def _writeFacet( self, facet: PlanarFacet ) -> SVGElement:
        width = 0.03
        dash = (1 , 0 )
        strokecolor = facet.color
        if not self._faceStyle is None:
            width = self._faceStyle.width
            strokecolor = str( self._faceStyle.color )
            if not self._faceStyle.dash is None:
                dash = self._faceStyle.dash
        
        return SVGHelper.Polygon( facet.points, facet.color, strokecolor, width, dash )


    def _writeSurface(self) -> list[ str ]:
        surface = SVGHelper.TransformGroup( (1,1), (0,0) )
        for facet in self._renderer._facets:
             surface.append( self._writeFacet( facet ) )
        return surface

    def _writeWires( self, edges: PlanarEdgesRepresentation ) -> list[ SVGElement ]:
        elements = []
        for edge in edges._wires:
            elements.append( SVGHelper.Path( edge.points ) )
        return elements


    def _writeWiresCollection( self ) -> list[ SVGElement ]:

        hierarchy: list = [
            EdgeRepresentationType.HIDDENSMOOTHWIRE,
            EdgeRepresentationType.HIDDENSHARPWIRE,
            EdgeRepresentationType.VISIBLESMOOTHWIRE,
            EdgeRepresentationType.VISIBLESHARPWIRE,
            EdgeRepresentationType.VISIBLEOUTLINE
        ]
        groups = []

        for edgeGroup in hierarchy:
            
            edges: PlanarEdgesRepresentation | None = next( ( visibleEdges for visibleEdges in self._renderer._edges if visibleEdges._type == edgeGroup ), None )
            if edges is None:
                continue

            linestyle: LineStyle | None = next( ( style for style in self._lineStyles if style.type == edgeGroup ), None )
            if linestyle is None:
                continue
            if not linestyle.dash is None:
                group = SVGHelper.StyleGroup( linestyle.color, linestyle.width, linestyle.dash )
            else:
                group = SVGHelper.StyleGroup( linestyle.color, linestyle.width )

            group.extend( self._writeWires( edges ) )
            groups.append( group )
        return groups
        
    
    def _writeArrow( self, p0: ndarray, p1: ndarray, style: ArrowStyle, unitLength: float) -> SVGElement:
        actualLength: float = norm( p1- p0 )
        adjustedArrowHeadLength = style.length * actualLength / unitLength
        n01: ndarray = normalize( p1 - p0 ).flatten()
        n01Ortho: ndarray = n01[ array( ( 1, 0 ) ) ] * array( ( 1, - 1 ) )
        p2 = p0 + ( actualLength + 1 ) * n01
        q0 = p1 - adjustedArrowHeadLength * n01 - n01Ortho * style.width / 2
        q1 = p1 - adjustedArrowHeadLength * n01 + n01Ortho * style.width / 2

        group = SVGHelper.TransformGroup( ( 1, 1 ),  ( 0, 0 ) )
        group.append( SVGHelper.Line( p0, p1, RGBA( 255, 0, 0 ), 0.1 ) )
        group.append( SVGHelper.Polygon( transpose( stack( ( p1, q0, q1 ) ) ), RGBA( 255, 0, 0  ), RGBA( 255, 0, 0  ), 0.1 ) )
        labelGroup = SVGHelper.TransformGroup( ( 1, -1 ),  (  p2[ 0 ],  - p2[ 1 ] ) )

        labelGroup.append( SVGHelper.Text( zeros( 2 ), "x", "smallItalic" ) )
        group.append( labelGroup )

        return group

    def _writeCoordinateSystem( self ) -> SVGElement | None:
        if self._coordStyle is None:
            return None
        
        sizefactor = self._coordStyle.size / 2
        anchor = self._renderer._coordinatesystem.anchor
        x = self._renderer._coordinatesystem.x * sizefactor
        y = self._renderer._coordinatesystem.y * sizefactor
        z = self._renderer._coordinatesystem.z * sizefactor

        group = SVGHelper.TransformGroup( ( 1, 1 ), ( 0, 0 ) )

        if not any( isnan( x ) ):
            group.append( self._writeArrow( anchor, anchor + x, self._coordStyle.arrowStyle, sizefactor ) )
        
        if not any( isnan( y ) ):
            group.append( self._writeArrow( anchor, anchor + y, self._coordStyle.arrowStyle, sizefactor ) )
        
        if not any( isnan( z ) ):
            group.append( self._writeArrow( anchor, anchor + z, self._coordStyle.arrowStyle, sizefactor ) )

        return group

    
    def _writeStyles( self ) -> str:
        style = SVGHelper.Style()
        style.append( CreatefontClass( "smallItalic", 6, RGBA( 255, 0, 0 ) ) )
        return style

    def _write( self ) -> str:
        svg = SVGHelper.SVG( self.width, self.height )
        group = SVGHelper.TransformGroup( ( self._zoom[ 0 ], - self._zoom[ 1 ] ), self.translate )
        group.append( self._writeStyles() )
        group.append( self._writeSurface() )
        group.extend( self._writeWiresCollection() )
        group.append( self._writeCoordinateSystem() )
        svg.append( group )
        return str( svg )
    
    def write( self, directory: str ) -> None:
        name = self._renderer.scene.part.model.name
        filepath = f"{ directory }/{ name }.svg"
        f = open( filepath, "w" )
        svg: str = self._write( )
        f.write( svg )
        f.close()

        
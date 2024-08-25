from cadvectorgraphics.render.render import VirtualRenderer
from cadvectorgraphics.render.components.geometry import PlanarEdgesRepresentation, PlanarFacet, EdgeRepresentationType
from numpy import ndarray
from cadvectorgraphics.illustrate.components.style import LineStyle, FaceStyle, CoordSystemStyle, ArrowStyle
from numpy import array, any, isnan, stack, transpose, zeros
from numpy.linalg import norm
from cadvectorgraphics.util.geometry import normalize
from cadvectorgraphics.util.color import RGBA
from cadvectorgraphics.illustrate.components.svg import SVGElement, SVGHelper, CreatefontClass

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
        self._scale: tuple[ float, float ] = ( 1, 1 )
    
    @property
    def lineStyle( self ) -> list[ LineStyle ]:
        return self._lineStyles

    @property
    def size( self ) -> tuple[ int, int ]:
        dx = int( self._boundingBox[ 0, 2 ] * self._zoom[ 0 ] ) + self._margin[ 0 ] * 2
        dy = int( self._boundingBox[ 1, 2 ] * self._zoom[ 1 ] ) + self._margin[ 1 ] * 2

        if self._coordStyle is not None:
            dx += self._coordStyle.margin * 2
            dy += self._coordStyle.margin * 2

        return dx, dy

    @property
    def width( self ) -> int:
        return self.size[ 0 ] * self._scale[ 0 ]
    
    @property
    def height( self ) -> int:
        return self.size[ 1 ] * self._scale[ 1 ]

    @property
    def margins( self ) -> tuple[ int, int ]:
        return self._margin

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
    def scale( self ) -> tuple[ float, float ]:
        return self._scale
    
    @scale.setter
    def scale( self, scale: tuple[ float, float ] ) -> None:
        self._scale = scale

    @property
    def translate( self ) -> tuple[ int, int ]:
        dx = - self._boundingBox[ 0, 0 ]
        dy = - self._boundingBox[ 1, 1 ]

        return dx, dy
    
    def boundingBox( self ) -> ndarray:
        bb = self._boundingBox
        bb[ 0, :] *= self._zoom[ 0 ]
        bb[ 1, :] *= self._zoom[ 1 ]
        return bb

    def addLineStyle( self, linestyle: LineStyle ) -> None:
        self._lineStyles.append( linestyle )

    def setFaceStyle( self, facestyle: FaceStyle ) -> None:
        self._faceStyle = facestyle

    def setCoordSystemStyle( self, coordSystemStyle: CoordSystemStyle ) -> None:
        self._coordStyle = coordSystemStyle

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
        surface = SVGHelper.TransformGroup( ( 1, 1 ), ( 0, 0 ) )
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

    def _writeCoordinateSystem( self ) -> SVGElement | None:
        if self._coordStyle is None:
            return None
        
        sizefactor = self._coordStyle.size / 2
        anchor = array( [ self._coordStyle.size, self.height - self._coordStyle.size ] )
        x = self._renderer._coordinatesystem.x * sizefactor
        y = self._renderer._coordinatesystem.y * sizefactor
        z = self._renderer._coordinatesystem.z * sizefactor

        group = SVGHelper.TransformGroup( ( 1, 1 ), ( 0, 0 ) )

        if not any( isnan( x ) ):
            group.append( SVGHelper.Arrow( anchor, anchor + x * array( ( 1, -1 ) ), sizefactor, self._coordStyle.x ) )
        
        if not any( isnan( y ) ):
            group.append( SVGHelper.Arrow( anchor, anchor + y * array( ( 1, -1 ) ), sizefactor, self._coordStyle.y ) )
        
        if not any( isnan( z ) ):
            group.append( SVGHelper.Arrow( anchor, anchor + z * array( ( 1, -1 ) ), sizefactor, self._coordStyle.z ) )

        return group

    def _write( self ) -> str:
        svg = SVGHelper.SVG( self.width, self.height )
        coordGroup = SVGHelper.TransformGroup( self.scale, ( 0, 0 ) )
        coordSysMargin = self._coordStyle.margin if not self._coordStyle is None else 0
        marginGroup = SVGHelper.TransformGroup( ( 1, 1 ), ( coordSysMargin, coordSysMargin ) )
        boundingBoxGroup = SVGHelper.TransformGroup( ( self._zoom[ 0 ], self._zoom[ 1 ] ), ( self.margins[ 0 ] / self._zoom[ 0 ], self.margins[ 1 ] / self._zoom[ 1 ] )  )
        geomGroup = SVGHelper.TransformGroup( ( 1, - 1 ), self.translate )
        geomGroup.append( self._writeSurface() )
        geomGroup.extend( self._writeWiresCollection() )
        boundingBoxGroup.append( geomGroup )
        marginGroup.append( boundingBoxGroup )
        coordGroup.append( marginGroup )

        coordGroup.append( self._writeCoordinateSystem() )
        svg.append( coordGroup )
        return str( svg )
    
    def write( self, directory: str ) -> None:
        name = self._renderer.scene.part.name
        filepath = f"{ directory }/{ name }.svg"
        f = open( filepath, "w" )
        svg: str = self._write()
        f.write( svg )
        f.close()

        
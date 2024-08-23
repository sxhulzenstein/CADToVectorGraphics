from render.render import VirtualRenderer
from render.components.geometry import PlanarEdgesRepresentation, PlanarMeshRepresentation, PlanarFacet, EdgeRepresentationType
from numpy import ndarray
from illustrate.components.style import LineStyle, FaceStyle, CoordSystemStyle, ArrowStyle
from numpy import array, any, isnan
from numpy.linalg import norm
from util.geometry import normalize

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

    def _writeFacet( self, facet: PlanarFacet ) -> str:
        width = 0.03
        dash = ""
        strokecolor = str( facet.color )
        if not self._faceStyle is None:
            width = self._faceStyle.width
            strokecolor = str( self._faceStyle.color )
            if not self._faceStyle.dash is None:
                dash += "stroke-dasharray=\""
                dash += ', '.join( str( v ) for v in self._faceStyle.dash ) +"\""

        """< polygon points = "50,200 250,200 150,50" fill = "url(#gradient2)" / >"""
        x, y = list( facet.points[ 0, : ] ), list( facet.points[ 1, : ] )
        output = f"<polygon points=\""
        output += " ".join( f"{ xi },{ yi }" for xi, yi in zip( x, y ) )
        output += f"""" fill="rgb{ str( facet.color ) }" stroke="rgb{ strokecolor }" stroke-width="{width}" stroke-linejoin="round" {dash} fill-opacity="{facet.color.alpha / 255}" />\n"""
        return output

    def _writeSurface(self) -> list[ str ]:
        surfaces = [ "<g>" ]
        for facet in self._renderer._facets:
            surfaces.append( self._writeFacet( facet ) )
        surfaces.append( "</g>\n" )
        return surfaces

    def _writeWires( self, edges: PlanarEdgesRepresentation ) -> list[ str ]:
        wires: list[ str ] = []
        for edge in edges._wires:
            x, y = list( edge.points[ 0, : ] ), list( edge.points[ 1, : ] )
            wires.append(f"<path d=\"M{ x[ 0 ] },{ y[ 0 ] } ")
            wires.append(" ".join(f"L{ xi },{ yi }" for xi, yi in zip( x[ 1: ], y[ 1: ] ) ))
            wires.append(" \" />\n")
        return wires

    def _writeWiresCollection( self ) -> list[ str ]:

        hierarchy: list = [
            EdgeRepresentationType.HIDDENSMOOTHWIRE,
            EdgeRepresentationType.HIDDENSHARPWIRE,
            EdgeRepresentationType.VISIBLESMOOTHWIRE,
            EdgeRepresentationType.VISIBLESHARPWIRE,
            EdgeRepresentationType.VISIBLEOUTLINE
        ]

        wireStrings: list[ str ] = []

        for edgeGroup in hierarchy:
            edges: PlanarEdgesRepresentation | None = next( ( visibleEdges for visibleEdges in self._renderer._edges if visibleEdges._type == edgeGroup ), None )
            if edges is None:
                continue

            linestyle: LineStyle | None = next( ( style for style in self._lineStyles if style.type == edgeGroup ), None )
            if linestyle is None:
                continue
            
            dash = ""
            if not linestyle.dash is None:
                dash += "stroke-dasharray=\""
                dash += ', '.join( str( v ) for v in linestyle.dash ) +"\""

            wireStrings.append( f"""<g stroke="rgb{ str( linestyle.color ) }" stroke-width="{ linestyle.width }" stroke-opacity="{ linestyle.color.alpha / 255 }" {dash} fill="none" stroke-linejoin="round" stroke-linecap="round">""" )
            wireStrings.extend( self._writeWires( edges ) )
            wireStrings.append( """</g>\n""" )
        return wireStrings
    
    def _writeArrow( self, p0: ndarray, p1: ndarray, style: ArrowStyle, unitLength: float) -> str:
        result = []
        actualLength: float = norm( p1- p0 )
        adjustedArrowHeadLength = style.length * actualLength / unitLength
        n01: ndarray = normalize( p1 - p0 ).flatten()
        n01Ortho: ndarray = n01[ array( ( 1, 0 ) ) ] * array( ( 1, - 1 ) )

        q0 = p1 - adjustedArrowHeadLength * n01 - n01Ortho * style.width / 2
        q1 = p1 - adjustedArrowHeadLength * n01 + n01Ortho * style.width / 2
        result.append(
            f"""<line x1="{ p0[ 0 ] }" y1="{ p0[ 1 ] }" x2="{ p1[ 0 ] }" y2="{ p1[ 1 ] }" stroke="red" stroke-width="{ 0.1 }" stroke-linecap="round" />\n""")
        
        result.append(f""""<polygon points="{p1[ 0 ]},{p1[ 1 ]} { q0[ 0 ] },{ q0[ 1 ] } {q1[ 0 ]},{q1[ 1 ]}" fill="red" stroke="red" stroke-width="{0.1}" stroke-linejoin="round" />\n""")
        
        p2 = p0 + ( actualLength + 1 ) * n01
        text = "x"
        result.append( f"""<g transform="scale({ 1 }, { - 1 })   translate({ p2[ 0 ] },{ - p2[ 1 ] } )">\n""" )
        result.append( f"""<text x="0" y="0" class="smallItalic">{text}</text>\n""" )
        result.append("</g>")

        return ''.join(result)



    def _writeCoordinateSystem( self ) -> list[ str ]:
        if self._coordStyle is None:
            return []
        
        sizefactor = self._coordStyle.size / 2
        anchor = self._renderer._coordinatesystem.anchor
        x = self._renderer._coordinatesystem.x * sizefactor
        y = self._renderer._coordinatesystem.y * sizefactor
        z = self._renderer._coordinatesystem.z * sizefactor

        vectors: list[ str ] = [ "<g>\n" ]
        if not any( isnan( x ) ):
            vectors.append( self._writeArrow( anchor, anchor + x, self._coordStyle.arrowStyle, sizefactor ) )
        
        if not any( isnan( y ) ):
            vectors.append( self._writeArrow( anchor, anchor + y, self._coordStyle.arrowStyle, sizefactor ) )
        
        if not any( isnan( z ) ):
            vectors.append( self._writeArrow( anchor, anchor + z, self._coordStyle.arrowStyle, sizefactor ) )
        vectors.append("</g>\n")
        return vectors
    
    def _writeStyles( self ) -> str:
        return """<style> .smallItalic { font: italic 4px serif; fill: red; } </style>"""

    def _write( self, facets: PlanarMeshRepresentation, edges: list[ PlanarEdgesRepresentation ] ) -> str:
        # add version and encoding
        entries = ["""<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n"""]

        dx = self.translate[ 0 ]
        dy = self.translate[ 1 ]
        
        # add width and height
        entries.append( f"""<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg" width="{ self.width }" height="{ self.height }">\n""" )
        entries.append( f"""<g transform="scale({ self._zoom[ 0 ] }, { - self._zoom[ 1 ] })   translate({ dx },{ dy } )">\n""" )
        entries.append( self._writeStyles() )
        entries.extend( self._writeSurface() )
        entries.extend( self._writeWiresCollection() )
        entries.extend( self._writeCoordinateSystem() )
        entries.append( "</g>" )
        entries.append( "</svg>" )
        return ''.join(entries)

    def write( self, name: str, directory: str ) -> None:
        filepath = f"{ directory }/{ name }.svg"
        f = open( filepath, "w" )
        svg: str = self._write( self._renderer._facets, self._renderer._edges )
        f.write( svg )
        f.close()

        
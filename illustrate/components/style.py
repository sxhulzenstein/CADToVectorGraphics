from render.components.geometry import EdgeRepresentationType
from util.color import RGBA

class LineStyle:
    def __init__( self, edgeType: EdgeRepresentationType ) -> None:
        self._type: EdgeRepresentationType = edgeType
        self._color: RGBA = RGBA( 0, 0, 0, 255 )
        self._width: float = 0.
        self._dash: tuple[ int, ... ] | None = None
    
    @property
    def width( self ) -> float:
        return self._width

    @width.setter
    def width( self, width: float ) -> None:
        self._width = abs( width )
    
    @property 
    def color( self ) -> RGBA:
        return self._color
    
    @color.setter
    def color( self, color: tuple[ int, int, int, int ] ) -> None:
        self._color = RGBA( *color )

    @property
    def type( self ) -> EdgeRepresentationType:
        return self._type
    
    @property
    def dash( self ) -> tuple[ int, ... ] | None:
        return self._dash
    
    @dash.setter
    def dash( self, dash: tuple[ int, ... ] ) -> None:
        self._dash = dash

class FaceStyle:
    def __init__( self, color: tuple[ int, int, int, int ] ) -> None:
        self._color: RGBA = RGBA( *color )
        self._width: float = 0.03
        self._dash: tuple[ int, ... ] | None = None
    
    @property
    def width( self ) -> float:
        return self._width

    @width.setter
    def width( self, width: float ) -> None:
        self._width = abs( width )
    
    @property 
    def color( self ) -> RGBA:
        return self._color
    
    @color.setter
    def color( self, color: tuple[ int, int, int, int ] ) -> None:
        self._color = RGBA( *color )
    
    @property
    def dash( self ) -> tuple[ int, ... ] | None:
        return self._dash
    
    @dash.setter
    def dash( self, dash: tuple[ int, ... ] ) -> None:
        self._dash = dash
    
class ArrowStyle:
    def __init__( self, width: float, length: float ) -> None:
        self._width = width
        self._length = length
    
    @property
    def width( self ) -> float:
        return self._width
    
    @property
    def length( self ) -> float:
        return self._length


class CoordSystemStyle:
    def __init__( self, size: float ) -> None:
        self._size: float = size
        self._width: float = 1
        self._arrow: ArrowStyle = ArrowStyle( 1 * self._width, 2 * self._width )
    
    @property
    def arrowStyle( self ) -> ArrowStyle:
        return self._arrow

    @arrowStyle.setter
    def arrowStyle( self, style: tuple[ float, float ] ) -> None:
        self._arrow = ArrowStyle( style[ 0 ], style[ 1 ] )

    @property
    def width( self ) -> float:
        return self._width
    
    @property
    def size( self ) -> float:
        return self._size
    

    
    

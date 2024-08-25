from cadvectorgraphics.render.components.geometry import EdgeRepresentationType
from cadvectorgraphics.util.color import RGBA

class LineStyle:
    def __init__( self, edgeType: EdgeRepresentationType ) -> None:
        """
        Create style description for edges

        Parameters:
            edgeType ( EdgeRepresentationType ): visibility type of the drawn edge
        """
        self._type: EdgeRepresentationType = edgeType
        self._color: RGBA = RGBA( 0, 0, 0, 255 )
        self._width: float = 0.
        self._dash: tuple[ int, ... ] | None = None
    
    @property
    def width( self ) -> float:
        """
        Get the stroke width of the edge

        Returns:
            float: stroke width
        """
        return self._width

    @width.setter
    def width( self, width: float ) -> None:
        """
        Set the stroke width of the edge

        Parameters:
            width ( float ): new stroke width
        """
        self._width = abs( width )
    
    @property 
    def color( self ) -> RGBA:
        """
        Get the stroke color of the line

        Returns:
            RGBA: stroke color of the line
        """
        return self._color
    
    @color.setter
    def color( self, color: tuple[ int, ... ] ) -> None:
        """
        Set the stroke color of the line

        Parameters:
            color ( tuple[ int, ... ] ): new stroke color
        """
        self._color = RGBA( *color )

    @property
    def type( self ) -> EdgeRepresentationType:
        """
        Get the visibility type of the edge
        
        Returns:
            EdgeRepresentationType: edge visibility type
        """
        return self._type
    
    @property
    def dash( self ) -> tuple[ int, ... ] | None:
        """
        Get the dash array for the stroke

        Returns:
            tuple[ int, ... ] | None: dash array
        """
        return self._dash
    
    @dash.setter
    def dash( self, dash: tuple[ int, ... ] ) -> None:
        """
        Set the dash array for the stroke

        Parameters:
            dash ( tuple[ int, ... ] ): new dash array
        """
        self._dash = dash

class FaceStyle:
    def __init__( self, strokeColor: tuple[ int, ... ] ) -> None:
        """
        Create a style description for the lines of the factes

        Parameters:
            strokeColor ( tuple[ int, ... ] ): stroke color of the outline for each face
        """
        self._color: RGBA = RGBA( *strokeColor )
        self._width: float = 0.03
        self._dash: tuple[ int, ... ] | None = None
    
    @property
    def width( self ) -> float:
        """
        Get the stroke width of the face outline

        Returns:
            float: stroke width
        """
        return self._width

    @width.setter
    def width( self, width: float ) -> None:
        """
        Set the stroke width of the face outline

        Parameters: 
            width ( float ): set the stroke width
        """
        self._width = abs( width )
    
    @property 
    def color( self ) -> RGBA:
        """
        Get the stroke color of the face outline

        Returns:
            RGBA: stroke color
        """
        return self._color
    
    @color.setter
    def color( self, color: tuple[ int, ... ] ) -> None:
        """
        Set the stroke color of the face outline

        Parameters:
            color ( tuple[ int, ... ] ): new stroke color
        """
        self._color = RGBA( *color )
    
    @property
    def dash( self ) -> tuple[ int, ... ] | None:
        """
        Get the dash array for the stroke

        Returns:
            tuple[ int, ... ] | None: dash array
        """
        return self._dash
    
    @dash.setter
    def dash( self, dash: tuple[ int, ... ] ) -> None:
        """
        Set the dash array for the stroke

        Parameters:
            dash ( tuple[ int, ... ] ): new dash array
        """
        self._dash = dash
    
class ArrowStyle:
    def __init__( self, width: float, length: float ) -> None:
        """
        Create a style description for an arrow

        Parameters:
            width ( float ): width of the arrow head
            length ( float ): length of the arrow head
        """
        self._width: float = width
        self._length: float = length
        self._label: str = ""
    
    @property
    def width( self ) -> float:
        """
        Get the width of the arrow head

        Returns:
            float: width
        """
        return self._width
    
    @property
    def length( self ) -> float:
        """
        Get the length of the arrow head
        
        Returns:
            float: length
        """
        return self._length


class CoordSystemStyle:
    def __init__( self, size: float ) -> None:
        """
        Create a style description for the coordinate system

        Parameters:
            size ( float ): illustration size of the coord system
        """
        self._size: float = size
        self._width: float = 1
        self._arrow: ArrowStyle = ArrowStyle( 1 * self._width, 2 * self._width )
    
    @property
    def arrowStyle( self ) -> ArrowStyle:
        """
        Get the arrow style:

        Returns:
            ArrowStyle: style description for the arrows
        """
        return self._arrow

    @arrowStyle.setter
    def arrowStyle( self, style: tuple[ float, float ] | ArrowStyle ) -> None:
        """
        Set the arrow style:

        Parameters:
            style( tuple[ float, float ] | ArrowStyle ): style description for the arrows
        """
        self._arrow = ArrowStyle( style[ 0 ], style[ 1 ] )

    @property
    def width( self ) -> float:
        """
        Get the stroke width of the arrows

        Returns:
            float: stroke width
        """
        return self._width
    
    @property
    def size( self ) -> float:
        """
        Get the size of the coordinate system
        
        Returns:
            float: size of the coordinate system
        """
        return self._size
    

    
    

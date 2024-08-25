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
    def __init__( self, strokewidth: float, color: RGBA, label: str, fontsize: float ) -> None:
        """
        Create a style description for an arrow

        Parameters:
            width ( float ): width of the arrow head
            length ( float ): length of the arrow head
        """
        self._strokeWidth: float = strokewidth
        self._headwidth: float = strokewidth * 3
        self._headlength: float = strokewidth * 4
        self._label: str = label
        self._strokecolor: RGBA = color
        self._fontsize: float = fontsize
    
    @property
    def headwidth( self ) -> float:
        """
        Get the width of the arrow head multiplied by stroke width

        Returns:
            float: width
        """
        return self._headwidth
    
    @property
    def headlength( self ) -> float:
        """
        Get the length of the arrow head multiplied by stroke width
        
        Returns:
            float: length
        """
        return self._headlength
    
    @headwidth.setter
    def headwidth( self, width: float ) -> None:
        """
        Set the width of the arrow head prefactor for stroke width
        
        Parameters:
            width ( float ): length
        """
        self._headwidth = width * self._headwidth
    
    @headlength.setter
    def headlength( self, length ) -> None:
        """
        Set the length of the arrow head prefactor for stroke width
        
        Parameters:
            length ( float ): length
        """
        self._headlength = self._strokeWidth * length 

    @property
    def label( self ) -> str:
        """
        Get the arrow's label

        Returns:
            str: arrow label
        """
        return self._label
    
    @property
    def color( self ) -> RGBA:
        """
        Get the stroke color

        Returns:
            RGBA: stroke color
        """
        return self._strokecolor
    
    @property
    def strokewidth( self ) -> float:
        """
        Get the stroke width

        Returns:
            float: stroke width
        """
        return self._strokeWidth
    
    @strokewidth.setter
    def strokewidth( self, strokewidth: float ) -> float:
        """
        Set the stroke width

        Parameters:
            strokewidth ( float ): new stroke width
        """
        oldWidth = self._strokeWidth
        self._headwidth *= strokewidth / oldWidth
        self._headlength *= strokewidth / oldWidth
        self._strokeWidth = strokewidth

    @property
    def fontSize( self ) -> float:
        """
        Get the font size

        Returns:
            float: font size
        """
        return self._fontsize


class CoordSystemStyle:
    def __init__( self, size: float ) -> None:
        """
        Create a style description for the coordinate system

        Parameters:
            size ( float ): illustration size of the coord system
        """
        self._size: float = size
        self._fontsize = size / 5
        self._x: ArrowStyle = ArrowStyle( size / 25., RGBA( 0, 0, 0 ), "x", self._fontsize )
        self._y: ArrowStyle = ArrowStyle( size / 25., RGBA( 0, 0, 0 ), "y", self._fontsize)
        self._z: ArrowStyle = ArrowStyle( size / 25., RGBA( 0, 0, 0 ), "z", self._fontsize)
        self._margin = 2 * size
    
    @property
    def x( self ) -> ArrowStyle:
        """
        Get the style information for the x-axis

        Returns:
            ArrowStyle: style information
        """
        return self._x
    
    @property
    def y( self ) -> ArrowStyle:
        """
        Get the style information for the y-axis

        Returns:
            ArrowStyle: style information
        """
        return self._y
    
    @property
    def z( self ) -> ArrowStyle:
        """
        Get the style information for the z-axis

        Returns:
            ArrowStyle: style information
        """
        return self._z

    @x.setter
    def x( self, x: ArrowStyle ) -> None:
        """
        Set the style information for the x-axis

        Parameters:
            x ( ArrowStyle ): style information
        """
        self._x = x
    
    @y.setter
    def y( self, y: ArrowStyle ) -> None:
        """
        Set the style information for the y-axis

        Parameters:
            y ( ArrowStyle ): style information
        """
        self._y = y
    
    @z.setter
    def z( self, z: ArrowStyle ) -> None:
        """
        Set the style information for the z-axis

        Parameters:
            z ( ArrowStyle ): style information
        """
        self._z = z

    @property
    def size( self ) -> float:
        """
        Get the size of the coordinate system
        
        Returns:
            float: size of the coordinate system
        """
        return self._size
    
    @property
    def margin( self ) -> float:
        """
        Get the margin of the coordinate system area

        Returns:
            float: margin
        """
        return self._margin
    
    

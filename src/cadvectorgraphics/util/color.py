from random import randint

class RGBA:
    def __init__( self, r: int, g: int, b: int, a: int = 255 ) -> None:
        """
        Create an object holding color information

        Parameters:
            r ( int ): red channel color
            g ( int ): green channel color
            b ( int ): blue channel color
            a ( int ): alpha channel color
        """
        self._r = r
        self._g = g
        self._b = b
        self._a = a

    @property
    def red( self ) -> int:
        """
        Get the red channel value

        Returns:
            int: red value
        """
        return self._r

    @property
    def green( self ) -> int:
        """
        Get the green channel value

        Returns:
            int: green value
        """
        return self._g

    @property
    def blue( self ) -> int:
        """
        Get the blue channel value

        Returns:
            int: blue value
        """
        return self._b

    @property
    def alpha( self ) -> int:
        """
        Get the alpha channel value

        Returns:
            int: alpha value
        """
        return self._a
    
    @property
    def opacity( self ) -> float:
        """
        Get the opacity from alpha value

        Returns:
            float: opacity value
        """
        return self._a / 255

    def __str__( self ) -> str:
        """
        Output of rgb color as string

        Returns:
            str: color as string
        """
        return f"({ self._r }, { self._g }, { self._b })"
    
    def rgb( self ) -> tuple[ int, int, int ]:
        """
        Get the rgb color as tuple

        Returns:
            tuple[ int, int, int ]: color as tuple
        """
        return int( self._r ), int( self._g ), int( self._b )
    
    def rgba( self ) -> tuple[ int, int, int, int ]:
        """
        Get the rgba color as tuple

        Returns:
            tuple[ int, int, int, int ]: color as tuple
        """
        return self._r, self._g, self._b, self._a
    

def randomGrayColor( lowerBound: int, upperBound: int ) -> RGBA:
    """
    Generate a random gray color within a range

    Parameters:
        lowerBound ( int ): darkest gray color
        upperBound ( int ): lightest gray color
    """
    color: int = randint( lowerBound, upperBound )
    return RGBA( color, color, color )
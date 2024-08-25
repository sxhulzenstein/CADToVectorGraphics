from cadvectorgraphics.util.color import RGBA
from numpy import ndarray, array, reshape

class LightSource:
    def __init__( self, 
                  position: tuple[ float, float, float ] | list[ float ] | ndarray ) -> None:
        """
        Create a light source

        Parameters:
            position ( tuple[ float, float, float ] | list[ float ] | ndarray ): spacial position of the camera

        """
        self._position: ndarray = reshape( array( position ), ( 3, 1 ) )
        self._color: RGBA = RGBA( 255, 255, 255 )

    @property
    def color( self ) -> RGBA:
        """
        Get the color of the light source

        Returns:
            RGBA: color of the light
        """
        return self._color

    @color.setter
    def color( self, color: tuple[ int, int, int ] | tuple[ int, int, int, int ] | RGBA ) -> None:
        """
        Set the color of the light source

        Parameters:
            color ( tuple[ int, int, int ] | tuple[ int, int, int, int ] | RGBA ): light source color
        """
        if type( color ) is RGBA:
            self._color = color
            return
        self._color = RGBA( *color )

    @property
    def position( self ) -> ndarray:
        """
        Get the position of the light source

        Returns:
            ndarray: light source position as ( 3 x 1 ) numpy array
        """
        return self._position
    
from util.geometry import normalize
from numpy import ndarray, zeros, array, reshape

class Camera:
    def __init__(self, view: tuple[ float, float, float ] | list[ float ] | ndarray ) -> None:
        """
        Create a camera as view port for a virtual scene

        Parameters:
            view ( tuple[ float, float, float ] | list[ float ] | ndarray ): view direction
        """
        horizontalDirection: tuple[ float, float, float ] = ( 0., 0., 0. )
        self._position: ndarray = zeros( ( 3, 1 ) )
        self._view: ndarray = reshape( normalize( array( view ) ), ( 3, 1 ) )
        self._horizontal: ndarray = reshape( normalize( array( horizontalDirection ) ), ( 3, 1 ) )
    
    @property
    def position( self ) -> ndarray:
        """
        Get the position of the camera

        Returns:
            ndarray: position as ( 3 x 1 ) numpy array

        """
        return self._position
    
    @property
    def view( self ) -> ndarray:
        """
        Get the view direction of the camera

        Returns:
            ndarray: view direction as ( 3 x 1 ) numpy array with unitary length

        """
        return self._view
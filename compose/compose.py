from compose.components.bind import PartRepresentation
from compose.components.illuminate import LightSource
from compose.components.view import Camera

class VirtualScene:
    def __init__( self, part: PartRepresentation ) -> None:
        """
        Create a virtual scene to place the spectator, the parts and the lights

        Parameters:
            part ( PartRepresentation ): part for the scene
        """
        self._camera: Camera | None = None
        self._part: PartRepresentation  = part
        self._lights: list[ LightSource ] = []
        
    def appendLightSource( self, light: LightSource ) -> None:
        """
        Add a light source to the scene

        Parameters:
            light ( LightSource ): the light that shall be added 
        """
        self._lights.append( light )
    
    @property
    def camera( self ) -> Camera:
        """
        Get the camera of the scene

        Returns:
            Camera: the camera of this scene
        """
        if not self._camera is None:
            return self._camera
        raise Exception( "Camers is not defined." )
    
    @camera.setter
    def camera( self, camera: Camera ) -> None:
        """
        Set a camera for the scene

        Parameters:
            camera ( Camera ): camera which shall be set
        """
        self._camera = camera
    
    @property
    def part( self ) -> PartRepresentation:
        """
        Get the part representation

        Returns:
            PartRepresentation: part of this scene
        """
        return self._part
    
    @property
    def lights( self ) -> list[ LightSource ]:
        """
        Get the list of light sources

        Returns:
            list[ LightSource ]: list of light sources in this scene
        """
        return self._lights
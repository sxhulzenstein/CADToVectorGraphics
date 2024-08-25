from cadquery import Workplane as CADModelBase
from cadquery import importers
from pathlib import Path
from uuid import uuid4

class CADModel:
    def __init__( self, data: CADModelBase | str, name: str | None = None ) -> None:
        """
        Creating an instance of an internal CADModel representation.

        Parameters:
            data ( CADModelBase | str ): CADQuery Workplane containing Solids or filepath to CAD-file
            name ( str | None = None ): name of the CAD-Object. If name is None, a uuid is generated automatically or is extracted from the filepath

        """
        if type( data ) is str:
            self._base: CADModelBase = importers.importStep( data )
            self._name: str = Path( data ).name.removesuffix( ".step" ).removesuffix(".Step").removesuffix(".STEP").removesuffix(".stp")
        else:
            self._base: CADModelBase = data
            self._name: str = str( uuid4() )
        
        if not name is None:
            self._name = name

    @property
    def base( self ) -> CADModelBase:
        """
        Get the CADQuery Workplane of the CAD-Object

        Returns:
            CADModelBase: a CADQuery Workplane
        """
        return self._base
    
    @property
    def name( self ) -> str:
        """
        Get the name of the CAD-Object

        Returns:
            str: name of the object
        """
        return self._name
    
    @name.setter
    def name( self, name : str ) -> None:
        self._name = name
from cadquery import Workplane as CADModelBase
from cadquery import importers
from uuid import uuid4
from ....util.file import FilePathInfo, File


class CADModel:
    def __init__(self, data: CADModelBase, name: str | None = None) -> None:
        """
        Creating an instance of an internal CADModel geometry.

        Parameters:
            data ( CADModelBase | str ): CADQuery work plane containing Solids or filepath to CAD-file
            name ( str | None = None ):
                name of the CAD-Object. If name is None, a uuid is generated automatically or is extracted
                from the filepath

        """
        self._base: CADModelBase = data
        self._name: str = str(uuid4()) if not name else name

    @classmethod
    def from_file(cls, filepath: str) -> "CADModel":
        base: CADModelBase = importers.importStep(filepath)
        file_info: FilePathInfo = File.extract_file_info(filepath)
        name: str = file_info.filename
        return cls(base, name)

    @property
    def base(self) -> CADModelBase:
        """
        Get the CADQuery work plane of the CAD-Object

        Returns:
            CADModelBase: a CADQuery work plane
        """
        return self._base

    @property
    def name(self) -> str:
        """
        Get the name of the CAD-Object

        Returns:
            str: name of the object
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

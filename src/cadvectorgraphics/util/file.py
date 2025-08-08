import os
from dataclasses import dataclass


@dataclass()
class FilePathInfo:
    """
    A class containing information received from the file path

    Attributes:
        filepath: The original file path
        directory: The directory where the file can be found
        filename: The base name of the file without the extension
        extension: The suffix of the file (e.g. `dxf` or `json`)
    """
    filepath: str
    directory: str
    filename: str
    extension: str


class File:
    """
    A class for extracting file information
    """

    @staticmethod
    def extract_file_info(filepath: str) -> FilePathInfo:
        """
        Separate the file path to receive the directory, the base name and the file extension

        Args:
            filepath: The filepath which shall be evaluated

        Returns:
            Directory, base name and extension from the file path
        """
        fp = os.path.abspath(filepath)
        directory = os.path.dirname(fp)
        components = os.path.basename(fp).split(".")
        extension = components.pop()
        filename = ".".join(components)
        return FilePathInfo(fp, directory, filename, extension)
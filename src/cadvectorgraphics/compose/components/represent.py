from .geometry.cad import CADModel
from .geometry.mesh import Mesh, MeshModelGenerator
from .geometry.material import MaterialProperties
from ...util.color import RGBA, randomGrayColor
from cadquery import Solid
from dataclasses import dataclass


@dataclass
class SolidRepresentation:
    base: Solid
    color: RGBA = randomGrayColor(50, 230)
    material: MaterialProperties = MaterialProperties(0.7, 0.7, 0.3, 0.5)
    mesh: Mesh | None = None


class PartRepresentation:
    def __init__(self, model: CADModel) -> None:
        """
        Create an instance of a part geometry

        Parameters:
            model ( CADModel ): the CAD-object for which a mesh geometry should be generated
        """
        self._model: CADModel = model
        self._solids: list[SolidRepresentation] = [
            SolidRepresentation(solid) for solid in self._model.base.val().Solids()]

    @classmethod
    def from_file(cls, filepath: str) -> "PartRepresentation":
        return cls(CADModel.from_file(filepath))

    def _assert_is_valid_index(self, index) -> None:
        if index > len(self._solids) - 1:
            raise Exception()

        if index + len(self._solids) < 0:
            raise Exception()

    @property
    def model(self) -> CADModel:
        """
        Get the internal CAD-object

        Returns:
            CADModel: base CAD object
        """
        return self._model

    def generate_all_meshes(self, options) -> None:
        """
        Generate meshes for each solid with the same setting
        """
        for solid in self._solids:
            solid.mesh = Mesh(*MeshModelGenerator.generate(solid.base, options))

    def generate_mesh(self, solid_index: int, options) -> None:
        """
        Generate a mesh for a specific solid
        """
        self._assert_is_valid_index(solid_index)
        self._solids[solid_index].mesh = Mesh(*MeshModelGenerator.generate(self._solids[solid_index].base, options))

    def set_mesh(self, solid_index: int, mesh: Mesh) -> None:
        """
        Set the mesh for a specific solid

        Parameters:
            solid_index ( int ):
                index of the Solid in the list of solids. For assemblies, the order is the same as in the assembly file
            mesh ( MeshModel ): externally generated mesh
        """
        self._assert_is_valid_index(solid_index)
        self._solids[solid_index].mesh = mesh

    def set_color(self, solid_index: int, color: tuple[int, ...]) -> None:
        """
        Set the color of a specific solid

        Parameters:
            solid_index ( int ):
                index of the Solid in the list of solids. For assemblies, the order is the same as in the assembly file
            color ( tuple[ int, ... ] ): new color of the solid as tuple
        """
        self._assert_is_valid_index(solid_index)
        self._solids[solid_index].color = RGBA(*color)

    def set_material(self, solid_index: int, material: MaterialProperties) -> None:
        """
        Set the material property of a specific solid

        Parameters:
            solid_index ( int ):
                index of the Solid in the list of solids. For assemblies, the order is the same as in the assembly file
            material ( MaterialProperties ): new material property of the solid
        """
        self._assert_is_valid_index(solid_index)
        self._solids[solid_index].material = material

    @property
    def solids(self) -> list[SolidRepresentation]:
        """
        Get the list of solids

        Returns:
            list[ Solid ]: list of base solids
        """
        return self._solids

    def __iter__(self):
        """
        Create an iterator for the solids

        Returns:
            PartRepresetantion
        """
        self._solidIndex = 0
        return self

    def __next__(self) -> SolidRepresentation:
        """
        Move iterator for solids to next item

        Returns:
            SolidRepresentation: next solid
        """
        index = self._solidIndex
        self._solidIndex += 1

        if not index < len(self._solids):
            raise StopIteration()

        return self._solids[index]

    @property
    def name(self) -> str:
        """
        Get the name of the part

        Returns:
            str: name
        """
        return self._model.name

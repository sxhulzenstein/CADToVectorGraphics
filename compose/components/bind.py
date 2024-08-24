from compose.components.representation.cad import CADModel, MaterialProperties
from compose.components.representation.mesh import MeshModel, MeshSize
from util.color import RGBA, randomGrayColor
from cadquery.occ_impl.shapes import Solid

class SolidRepresentation:
    def __init__( self, solid: Solid ) -> None:
        """
        Create a SolidRepresentation object to hold the optical properties the Solid object and the MeshModel

        Parameters:
            solid ( Solid ): base solid object. The initial color and material properties are generated automatically
        """
        self._base: Solid = solid
        self._color: RGBA = randomGrayColor( 50, 230 )
        self._material: MaterialProperties = MaterialProperties(0.7, 0.7, 0.3, 0.5)
        self._mesh: MeshModel | None = None
    
    @property
    def color( self ) -> RGBA:
        """
        Get the Color property of the Solid

        Returns:
            RGBA: color of the solid
        """
        return self._color
    
    @color.setter
    def color( self, color: RGBA ) -> None:
        """
        Set the Color property of the Solid

        Parameters:
            color ( RGBA ): color of the solid
        """
        self._color = color
    
    @property
    def material( self ) -> MaterialProperties:
        """
        Get the material property of the Solid

        Returns:
            MaterialProperties: material property of the solid
        """
        return self._material
    
    @material.setter
    def material( self, material: MaterialProperties ) -> None:
        """
        Set the material property of the Solid

        Parameters ( MaterialProperties ):
            new material property of the solid
        """
        self._material = material
    
    @property
    def mesh( self ) -> MeshModel:
        """
        Get the mesh model of the Solid

        Returns:
            MeshModel: mesh model of the solid
        """
        return self._mesh
    
    @mesh.setter
    def mesh( self, mesh: MeshModel ) -> None:
        """
        Set the mesh model of the Solid

        Parameters:
            mesh ( MeshModel ): new mesh model of the solid
        """
        self._mesh = mesh

    @property
    def base( self ) -> Solid:
        """
        Get the base Solid

        Returns:
            Solid: internal solid
        """
        return self._base


class PartRepresentation:
    def __init__( self, model: CADModel | str ) -> None:
        """
        Create an instance of a part representation

        Parameters:
            model ( CADModel ): the CAD-object for which a mesh representation should be generated
        """
        if type( model ) is str:
            self._model = CADModel( model )
        else:
            self._model: CADModel = model
        self._solids: list[ SolidRepresentation ] = [ SolidRepresentation( solid ) for solid in self._model.base.val().Solids() ]
        
    def _assertIsValidIndex( self, index ) -> None:
        if index > len( self._solids ) - 1:
            raise Exception()
        
        if index + len( self._solids ) < 0:
            raise Exception()
    
    @property
    def model( self ) -> CADModel:
        """
        Get the internal CAD-object

        Returns:
            CADModel: base CAD object
        """
        return self._model
    
    def tessellateAll( self, size: tuple[ float, float ] | MeshSize = MeshSize.DEFAULT ) -> None:
        """
        Generate meshes for each solid with the same setting

        Parameters:
            size ( tuple[ float, float ] | MeshSize = MeshSize.DEFAULT ): settings for the element size
        """
        for solid in self._solids:
            solid.mesh = MeshModel( solid.base, size )
    
    def tessellate( self, solidIndex: int, size: tuple[ float, float ] | MeshSize = MeshSize.DEFAULT ) -> None:
        """
        Generate a mesh for a specific solid

        Parameters:
            solidIndex ( int ): index of the Solid in the list of solids. For assemblies, the order is the same as in the assembly file
            size ( tuple[ float, float ] | MeshSize = MeshSize.DEFAULT ): settings for the element size
        """
        self._assertIsValidIndex( solidIndex )
        self._solids[ solidIndex ].mesh = MeshModel( self._solids[ solidIndex ].base, size )
    
    def mesh( self, solidIndex: int, mesh: MeshModel ) -> None:
        """
        Set the mesh for a specific solid

        Parameters:
            solidIndex ( int ): index of the Solid in the list of solids. For assemblies, the order is the same as in the assembly file
            mesh ( MeshModel ): externally generated mesh
        """
        self._assertIsValidIndex( solidIndex )
        self._solids[ solidIndex ].mesh = mesh

    def color( self, solidIndex: int, color: tuple[ int, ... ] ) -> None:
        """
        Set the color of a specific solid

        Parameters:
            solidIndex ( int ): index of the Solid in the list of solids. For assemblies, the order is the same as in the assembly file
            color ( tuple[ int, ... ] ): new color of the solid as tuple
        """
        self._assertIsValidIndex( solidIndex )
        self._solids[ solidIndex ].color = RGBA( *color )

    def material( self, solidIndex: int, material: MaterialProperties ) -> None:
        """
        Set the material property of a specific solid

        Parameters:
            solidIndex ( int ): index of the Solid in the list of solids. For assemblies, the order is the same as in the assembly file
            material ( MaterialProperties ): new material property of the solid
        """
        self._assertIsValidIndex( solidIndex )
        self._solids[ solidIndex ].material = material

    @property
    def solids( self ) -> list[ SolidRepresentation ]:
        """
        Get the list of solids

        Returns:
            list[ Solid ]: list of base solids
        """
        return self._solids
    
    def __iter__( self ):
        """
        Create an iterator for the solids

        Returns:
            PartRepresetantion
        """
        self._solidIndex = 0
        return self

    def __next__( self ) -> SolidRepresentation:
        """
        Move iterator for solids to next item

        Returns:
            SolidRepresentation: next solid
        """
        index = self._solidIndex
        self._solidIndex += 1

        if not index < len( self._solids ):
            raise StopIteration()

        return self._solids[ index ]
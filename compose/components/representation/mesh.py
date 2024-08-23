from cadquery import Vector as VectorBase
from numpy.typing import NDArray
from numpy import array, zeros, cross, ndarray, transpose
from util.geometry import cNormalize
from compose.components.representation.cad import CADModel
from cadquery import exporters
from cadquery.occ_impl.shapes import Solid
import uuid, tempfile, gmsh, os
from enum import Enum
from meshio import read, Mesh as MeshIOMesh

class Geometry:
    def __init__( self, geometry: list[ VectorBase ] | list[ tuple[ float, float, float ] ] | ndarray ) -> None:
        """
        Creates an Object containing nodes of an arbitrary mesh

        Parameters:
            geometry ( list[ VectorBase ] | list[ tuple[ float, float, float ] ] | ndarray ): geometry information
        """
        if len( geometry ) == 0:
            raise Exception()
        
        if type( geometry[ 0 ] ) is tuple:
            self._base = array( geometry )
        elif type( geometry[ 0 ] ) is VectorBase:
            self._base = array( [ [ p.x, p.y, p.z ] for p in geometry ] ).transpose()
        elif type( geometry ) is ndarray:
            self._base = geometry
        else:
            raise Exception()
    
    @property
    def base( self ) -> ndarray:
        """
        Get the container of all nodes

        Returns:
            ndarray: container as numpy array
        """
        return self._base
    
    @property
    def dimension( self ) -> int:
        """
        Get the dimension of the point cloud

        Returns:
            int: number of entries of each column ( = dimension )
        """
        return self._base.shape[ 0 ]
    
    @property
    def size( self ) -> int:
        """
        Get the size of the point cloud

        Returns:
            int: number of entries of each row ( = size )
        """
        return self._base.shape[ 1 ]
    
    def __len__( self ) -> int:
        """
        Get the size of the point cloud

        Returns:
            int: number of entries of each row ( = size )
        """
        return self.size
        

class Topology:
    def __init__( self, topology: list[ tuple[ int, ... ] ] | list[ list[ int ] ] ) -> None:
        """
        Creating an object which contains the topological information of a mesh

        Parameters:
            topology ( list[ tuple[ int, ... ] ] | list[ list[ int ] ]  ): topological information
        """
        self._base: dict[ int, tuple[ int, ... ] ] = { key : topology[ key ] for key in range( len( topology ) ) }
        self._triangles: dict[ int, tuple[ int, int, int ] ] = { key : value for key, value  in self._base.items() if len( value ) == 3 }
        self._quadrilaterals: dict[ int, tuple[ int, int, int, int ] ] = { key : value for key, value in self._base.items() if len( value ) == 4 }
    
    @property
    def base( self ) -> dict[ int, tuple[ int, ... ] ]:
        """
        Get the base object holding the topology

        Returns:
            dict[ int, tuple[ int, ... ] ]: topology information
        """
        return self._base
    
    @property
    def triangles( self ) -> dict[ int, tuple[ int, int, int ] ]:
        """
        Extract the topological information of the triangles 

        Returns:
            dict[ int, tuple[ int, int, int ] ]: topology information of triangles
        """
        return self._triangles

    @property
    def quadrilaterals( self ) -> dict[ int, tuple[ int, int, int, int ] ]:
        """
        Extract the topological information of the quadrilaterals 

        Returns:
            dict[ int, tuple[ int, int, int, int ] ]: topology information of quadrilaterals
        """
        return self._quadrilaterals
    
    def __getitem__( self, key: int | list[ int ] | tuple[ int, ... ] ) -> tuple[ int, ... ] | list[ tuple[ int, ... ] ]:
        """
        Get node indices of one or more elements

        Parameters:
            key ( int | list[ int ] | tuple[ int, ... ] ): indices of elements

        Returns:
            tuple[ int, ... ] | list[ tuple[ int, ... ] ]: topology information of requested elements
        """
        if type( key ) is int:
            return self._base[ key ]
        elif type( key ) is tuple or type( key ) is list:
            return [ self._base[ face ] for face in key ]
        else:
            raise Exception(type(key))
    
    def __setitem__( self, key: int, ids: tuple[ int, ... ] ) -> None:
        """
        Set the node indices of one element

        Parameters:
            key ( int ): face id
            ids ( tuple[ int, ... ] ): node ids of the adjusted face

        """
        self._base[ key ] = ids

    def __len__( self ) -> int:
        """
        Get the number of elements in the topology

        Returns:
            int: number of 2D elements
        """
        return self.size

    @property
    def size( self ) -> int:
        """
        Get the number of elements in the topology

        Returns:
            int: number of 2D elements
        """
        return len( self._base ) 

class Mesh:
    def __init__( self, geometry: list[ VectorBase ] | ndarray, topology: list[ tuple[ int, ... ] ] | list[ list[ int ] ] ) -> None:
        """
        Create a Mesh object containing geometric and topological information

        Parameters:
            geometry ( list[ VectorBase ] | ndarray ): geometric information
            topology ( list[ tuple[ int, ... ] ] | list[ list[ int ] ] ): topological information
        """
        self._geometry: Geometry = Geometry( geometry )
        self._topology: Topology = Topology( topology )

    @property
    def nNodes( self ) -> int:
        """
        Get the number of nodes in the point cloud

        Returns:
            int: number of points
        """
        return len( self._geometry.size )
    
    @property
    def nFaces( self ) -> int:
        """
        Get the number of faces in the topology

        Returns:
            int: number of faces
        """
        return len( self._topology.base )
    
    @property
    def topology( self ) -> Topology:
        """
        Get the the topology of the mesh

        Returns:
            Topology: topology of the mesh
        """
        return self._topology
    
    @property
    def geometry( self ) -> Geometry:
        """
        Get the the geometry of the mesh

        Returns:
            Geometry: geometry of the mesh
        """
        return self._geometry


class MeshSize( Enum ):
    """
    Enum containing fineness of elements
    """
    DEFAULT = 1
    BULKY = 5
    COARSE = 10
    GRAINY = 20
    MEDIUM = 50
    FINE = 100
    ULTRAFINE = 200
    ATOMIC = 500
    INSANE = 1000


class MeshModelGenerator:
    def __init__( self, cad: CADModel | Solid ) -> None:
        """
        Create a Geberator for a Mesh

        Parameters:
            cad ( CADModel | Solid ): CAD-object or Solid which shall be meshed
        """
        self._model: CADModel | Solid = cad

        if type( cad ) is CADModel:
            self._boundingBox = cad.base.val().BoundingBox()
        else:
            self._boundingBox = cad.BoundingBox()

    def _initializeMesher( self ) -> None:
          gmsh.initialize()    
    
    def _determineMimMaxElementSize( self, size: tuple[ float, float] | MeshSize ) -> tuple[ float, float ]:
        if type( size ) is tuple:
            return size[ 0 ], size[ 1 ]

        if size == MeshSize.DEFAULT:
            area = self._model.base.val().Area
            return area / max( self._boundingBox.xlen, self._boundingBox.ylen, self._boundingBox.zlen ), area / min( self._boundingBox.xlen, self._boundingBox.ylen, self._boundingBox.zlen )

        minSize = min( self._boundingBox.xlen, self._boundingBox.ylen, self._boundingBox.zlen ) / ( size.value * 0.75 )
        maxSize = max( self._boundingBox.xlen, self._boundingBox.ylen, self._boundingBox.zlen ) / ( size.value * 1.25 )

        print( minSize, maxSize )

        return minSize, maxSize
    
    def _generate( self, minSize, maxSize ) -> None:
         with tempfile.NamedTemporaryFile( suffix = ".step", delete = False ) as file:
            file.close()
                    
            if type( self._model ) is CADModel:
                exporters.export( self._model.base, file.name )
            else:
                self._model.exportStep( file.name )
            
            gmsh.model.add( str( uuid.uuid4() ) )
            gmsh.merge( file.name )
            os.remove( file.name )
            gmsh.option.setNumber( "Mesh.Algorithm", 6 )
            gmsh.option.setNumber( "Mesh.MeshSizeMin", minSize )
            gmsh.option.setNumber( "Mesh.MeshSizeMax", maxSize )
            gmsh.model.mesh.generate( 2 )

    def _readMesh( self, filepath: str ) -> Mesh:
        meshInfo: MeshIOMesh = read( filepath )
        return Mesh( transpose( array( meshInfo.points ) ), meshInfo.get_cells_type("triangle") )

    def _toMesh( self ) -> Mesh:
        with tempfile.NamedTemporaryFile( suffix = ".msh", delete = False ) as meshfile:
            meshfile.close()
            gmsh.write( meshfile.name )
            mesh: Mesh = self._readMesh( meshfile.name )
            os.remove( meshfile.name )
        gmsh.finalize()
    
        return mesh

    def generate( self, size: tuple[ float, float] | MeshSize = MeshSize.DEFAULT ) -> Mesh:
        """
        Generate a mesh for the cad model   
        Note: If the mesh generation of gmsh fails, the meshing algorithm of cadquery is used

        Parameters:
            size ( tuple[ float, float] | MeshSize = MeshSize.DEFAULT ): min and max sizes for elements or qualitative element size
        
        Returns:
            Mesh: new Mesh generated by gmsh
        """
        self._initializeMesher()
        minSize, maxSize = self._determineMimMaxElementSize( size )
        try:
            self._generate( minSize, maxSize )
            return self._toMesh()
        except:
            gmsh.finalize()
            geometry, topology = self._model.tessellate( 10 )
        return Mesh( geometry, topology )

class MeshModel:
    def __init__( self,
                  model: CADModel | Mesh | Solid, 
                  size: tuple[ float, float ] | MeshSize = MeshSize.DEFAULT,
                  name: str | None = None ) -> None:
        """
        Create a MeshModel to store or generate a Mesh

        Parameters:
            model ( CADModel | Mesh | Solid ): CAD-object as CADModel or Solid or a Mesh
            size ( tuple[ float, float ] | MeshSize = MeshSize.DEFAULT ): if the mesh is not given a new mesh is generated from the cad object by using the size options
            name ( str | None ): Name of the mesh model. If None is given, the name is an automatically generated uuid.
        """
        if type( model ) is Mesh:
            self._mesh: Mesh = model
        elif type( model ) is CADModel or type( model ) is Solid:
            self._mesh: Mesh = MeshModelGenerator( model ).generate( size )
        else: 
            raise Exception()

        self._centers: ndarray = self._calculateCenters()
        self._normals: ndarray = self._calculateNormals()
        self._name: str = name if not name is None else str( uuid.uuid4() )

    def _triangleCenters( self, triangulation: NDArray ) -> NDArray:
        p: NDArray = self._mesh.geometry.base
        return 1 / 3 * ( p[ :, triangulation[ 0, : ] ] + p[ :, triangulation[ 1, : ] ] + p[ :, triangulation[ 2, : ] ] )

    def _calculateCenters( self ) -> NDArray:
        centers: ndarray = zeros( ( 3, self._mesh.nFaces ) )

        triangleIds: ndarray = array( list( self._mesh.topology.triangles.keys() ) )

        if not len( triangleIds ) == 0:
            triangles: ndarray = array( list( self._mesh.topology.triangles.values() ) ).transpose()
            centersOfTriangles: ndarray = self._triangleCenters( triangles )
            centers[ :, triangleIds ] += centersOfTriangles
        
        quadrilateralIds: ndarray =  array( list( self._mesh.topology.quadrilaterals.keys() ) )
        if not len( quadrilateralIds ) == 0:
            quadrilaterals: ndarray = array( list( self._mesh.topology.quadrilaterals.values() ) ).transpose()
            centersOfQuadrilaterals: ndarray = 1. / 2. * ( self._triangleCenters( quadrilaterals[ array( [ 0, 1, 2 ] ), : ] ) 
                                       + self._triangleCenters( quadrilaterals[ array( [ 2, 3, 0 ] ) , : ] ) )
            centers[ :, quadrilateralIds ] += centersOfQuadrilaterals

        return centers
    
    def _triangleNormals( self, triangulation ) -> ndarray:
        p: ndarray = self._mesh.geometry.base

        v0: ndarray = p[ :, triangulation[ 0, : ] ]
        v1: ndarray = p[ :, triangulation[ 1, : ] ]
        v2: ndarray = p[ :, triangulation[ 2, : ] ]

        return cNormalize( cross( v1 - v0, v2 - v1, axis = 0 ) )

    def _calculateNormals( self ) -> ndarray:
        normals: ndarray = zeros( ( 3, self._mesh.nFaces ) )
        triangleIds: ndarray = array( list( self._mesh.topology.triangles.keys() ) )

        if not len( triangleIds ) == 0:
            triangles: ndarray = array( list( self._mesh.topology.triangles.values() ) ).transpose()
            normalsOfTriangles: ndarray = self._triangleNormals( triangles )
            normals[ :, triangleIds ] += normalsOfTriangles
        
        quadrilateralIds: ndarray =  array( list( self._mesh.topology.quadrilaterals.keys() ) )
        if not len( quadrilateralIds ) == 0:
            quadrilaterals: ndarray = array( list( self._mesh.topology.quadrilaterals.values() ) ).transpose()
            normalsOfQuadrilaterals: ndarray = self._triangleNormals( quadrilaterals[ array( [ 0, 1, 2 ] ), : ] ) 
            + self._triangleNormals( quadrilaterals[ array( [ 0, 2, 3 ] ), : ] )
            normals[ :, quadrilateralIds ] += normalsOfQuadrilaterals

        return cNormalize( normals )
    
    @property
    def normals( self ) -> ndarray:
        """
        Get the normals of each face
    
        Returns:
            ndarray: Normals of the mesh as ( 3 x N ) array
        """
        return self._normals
    
    @property
    def centers( self ) -> ndarray:
        """
        Get the centroids for each face
    
        Returns:
            ndarray: Centers of the mesh as ( 3 x N ) array
        """
        return self._centers
    
    @property
    def name( self ) -> str:
        """
        Get the name of the mesh
    
        Returns:
            str: mesh model name
        """
        return self._name
    
    @property
    def base( self ) -> Mesh:
        """
        Get the Mesh base
    
        Returns:
            Mesh: mesh base class
        """
        return self._mesh
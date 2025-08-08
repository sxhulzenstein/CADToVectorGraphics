from cadquery import Vector as VectorBase
from numpy import ndarray, hstack
from numpy import array, zeros, cross, ndarray, transpose
from ....util.geometry import columnwise_normalize
from .cad import CADModel
from cadquery.occ_impl.shapes import Solid
from meshio import read
from .geometry import Geometry
from .topology import Topology
from .generator import MeshModelGenerator


class Mesh:
    def __init__(self,
                 geometry: list[VectorBase] | ndarray,
                 triangles: ndarray,
                 quadrilaterals: ndarray) -> None:
        """
        Create a Mesh object containing geometric and topological information

        Parameters:
            geometry ( list[ VectorBase ] | ndarray ): geometric information
            topology ( list[ tuple[ int, ... ] ] | list[ list[ int ] ] ): topological information
        """
        self._geometry: Geometry = Geometry(geometry)
        self._topology: Topology = Topology(triangles, quadrilaterals)
        self._centers: ndarray = self._calculate_centers()
        self._normals: ndarray = self._normals()

    @classmethod
    def from_file(cls, file_path: str) -> "Mesh":
        mesh_info = read(file_path)
        return cls(transpose(array(mesh_info.points)), mesh_info.get_cells_type("triangle"))

    @classmethod
    def from_model(cls, model: CADModel | Solid, options) -> "Mesh":
        return cls(*MeshModelGenerator.generate(model, options))

    @property
    def n_nodes(self) -> int:
        """
        Get the number of nodes in the point cloud

        Returns:
            int: number of points
        """
        return self._geometry.size

    @property
    def n_faces(self) -> int:
        """
        Get the number of faces in the topology

        Returns:
            int: number of faces
        """
        return len(self._topology)

    @property
    def topology(self) -> Topology:
        """
        Get the the topology of the mesh

        Returns:
            Topology: topology of the mesh
        """
        return self._topology

    @property
    def geometry(self) -> Geometry:
        """
        Get the the geometry of the mesh

        Returns:
            Geometry: geometry of the mesh
        """
        return self._geometry

    def _triangle_centers(self, triangulation: ndarray) -> ndarray:
        p: ndarray = self.geometry.base
        return 1 / 3 * (p[:, triangulation[0, :]] + p[:, triangulation[1, :]] + p[:, triangulation[2, :]])

    def _calculate_centers(self) -> ndarray:
        centers: ndarray = zeros((3, self.n_faces))

        triangle_ids: ndarray = array(list(self.topology.triangles.keys()))

        if not len(triangle_ids) == 0:
            triangles: ndarray = array(list(self.topology.triangles.values())).transpose()
            centers_of_triangles: ndarray = self._triangle_centers(triangles)
            centers[:, triangle_ids] += centers_of_triangles

        quadrilateral_ids: ndarray = array(list(self.topology.quadrilaterals.keys()))
        if not len(quadrilateral_ids) == 0:
            quadrilaterals: ndarray = array(list(self.topology.quadrilaterals.values())).transpose()
            centers_of_quadrilaterals: ndarray = 0.5 * (self._triangle_centers(quadrilaterals[array([0, 1, 2]), :])
                                                        + self._triangle_centers(quadrilaterals[array([2, 3, 0]), :]))
            centers[:, quadrilateral_ids] += centers_of_quadrilaterals

        return centers

    def _triangle_normals(self, triangulation) -> ndarray:
        p: ndarray = self.geometry.base

        v0: ndarray = p[:, triangulation[0, :]]
        v1: ndarray = p[:, triangulation[1, :]]
        v2: ndarray = p[:, triangulation[2, :]]

        return columnwise_normalize(cross(v1 - v0, v2 - v1, axis=0))

    def _normals(self) -> ndarray:
        normals: ndarray = zeros((3, self.n_faces))
        triangle_ids: ndarray = array(list(self.topology.triangles.keys()))

        if not len(triangle_ids) == 0:
            triangles: ndarray = array(list(self.topology.triangles.values())).transpose()
            normals_of_triangles: ndarray = self._triangle_normals(triangles)
            normals[:, triangle_ids] += normals_of_triangles

        quadrilateral_ids: ndarray = array(list(self.topology.quadrilaterals.keys()))
        if not len(quadrilateral_ids) == 0:
            quadrilaterals: ndarray = array(list(self.topology.quadrilaterals.values())).transpose()
            normals_of_quadrilaterals: ndarray = (self._triangle_normals(quadrilaterals[array([0, 1, 2]), :])
                                                  + self._triangle_normals(quadrilaterals[array([0, 2, 3]), :]))
            normals[:, quadrilateral_ids] += normals_of_quadrilaterals

        return columnwise_normalize(normals)

    @property
    def normals(self) -> ndarray:
        """
        Get the normals of each face

        Returns:
            ndarray: Normals of the mesh as ( 3 x N ) array
        """
        return self._normals

    @property
    def centers(self) -> ndarray:
        """
        Get the centroids for each face

        Returns:
            ndarray: Centers of the mesh as ( 3 x N ) array
        """
        return self._centers

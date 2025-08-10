from ...compose.components.view import Camera
from ...compose.components.geometry.cad import CADModelBase
from ...compose.components.represent import PartRepresentation, SolidRepresentation
from ...compose.components.geometry.mesh import Geometry, Topology
from ...compose.components.illuminate import LightSource
from ...render.components.geometry import PlanarMeshRepresentation, PlanarEdgesCollection, EdgeRepresentationType, \
    PlanarCoordinateSystemRepresentation
from ...util.geometry import columnwise_normalize
from ...util.color import RGBA
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Dir as OCPDirection, gp_Ax2 as OCPAxis, gp_Pnt as OCPSpacialPoint, gp_Pnt2d as OCPPlanarPoint
from numpy import transpose, hstack, array, argwhere, argsort, tile, zeros, where, round, sum, ones, ndarray, ndarray
from OCP.HLRBRep import HLRBRep_HLRToShape as OCPShapeAlgo, HLRBRep_Algo as OCPProjectionAlgo
from OCP.BRepLib import BRepLib
from cadquery.occ_impl.shapes import Shape
CurveBuilder = BRepLib.BuildCurves3d_s


class ColorTable:
    pass


class Projector:
    def __init__(self, camera: Camera) -> None:
        """
        Create a projector which uses OCC functionalities to project nodes onto a plane

        Parameters:
            camera ( Camera ): camer for which a projector shall be created
        """
        self._camera: Camera = camera
        self._base = HLRAlgo_Projector(
            OCPAxis(OCPSpacialPoint(*self._camera.position), OCPDirection(*self._camera.view)))

    def _remove_adverted_faces(self, part: PartRepresentation) -> dict[int, ndarray]:
        visible_facets: dict[int, ndarray] = {}

        for solid_index, solid in enumerate(part.solids):
            ids: ndarray = array(list(solid.mesh.topology.base.keys()))
            prod: ndarray = transpose(self._camera.view) @ solid.mesh.face_normals[:, ids]
            visible_facets[solid_index] = ids[argwhere(prod >= 0).flatten()].flatten()
        return visible_facets

    def _sort_faces_by_position(self, non_adverted_faces: dict[int, ndarray], part: PartRepresentation) -> ndarray:
        directional_distances: list[ndarray] = []
        for index, ids, solid in zip(non_adverted_faces.keys(), non_adverted_faces.values(), part.solids):
            centers = solid.mesh.centers[:, ids]
            result = zeros((3, ids.shape[0]))
            result[0, :] = transpose(self._camera.view) @ centers
            result[1, :] = ones((1, ids.shape[0])) * index
            result[2, :] = ids
            directional_distances.append(result)
        directional_distances_stack = hstack(tuple(directional_distances))

        return directional_distances_stack[1:, argsort(directional_distances_stack[0, :]).flatten()]

    def _uv_coordinates_using_projector(self, points: ndarray) -> ndarray:
        uv_points: ndarray = zeros((2, points.shape[1]))
        for index in range(uv_points.shape[1]):
            projected_uv_point = OCPPlanarPoint(0., 0.)
            self._base.Project(OCPSpacialPoint(*points[:, index]), projected_uv_point)
            uv_points[:, index] = array([projected_uv_point.X(), projected_uv_point.Y()])
        return uv_points

    @staticmethod
    def _init_shape_algo_filter(projector: HLRAlgo_Projector, cad: CADModelBase) -> OCPShapeAlgo:
        hlr: OCPProjectionAlgo = OCPProjectionAlgo()
        hlr.Add(cad.val().wrapped)
        hlr.Projector(projector)
        hlr.Update()
        hlr.Hide()
        return OCPShapeAlgo(hlr)

    @staticmethod
    def _insert_edges_if_not_null(edges: list[PlanarEdgesCollection], edges_for_edge_type: dict) -> None:
        for edgeType, edgesForType in edges_for_edge_type.items():
            if edgesForType.IsNull():
                continue
            CurveBuilder(edgesForType)
            edges.append(PlanarEdgesCollection(Shape(edgesForType).Edges(), edgeType))

    def _determine_colors(self,
                          anchors: ndarray,
                          normals: ndarray,
                          material,
                          lights: list[LightSource],
                          base_color: RGBA,
                          color_table: ColorTable | None = None) -> ndarray:
        n_normals: int = normals.shape[1]
        n_sources: int = len(lights)

        view_direction: ndarray = - tile(self._camera.view, (1, n_normals))

        if color_table is None:
            ambient: ndarray = transpose(tile(array(base_color.rgb()), (n_normals, 1)))
        else:
            raise NotImplementedError()

        if n_sources == 0:
            return ambient

        colors = zeros((4, n_normals))
        colors[3, :] = ones((1, n_normals)) * base_color.alpha

        for source in lights:
            diffuse = transpose(tile(array(source.color.rgb()), (n_normals, 1)))
            specular = transpose(tile(array(source.color.rgb()), (n_normals, 1)))
            light_source_directions = columnwise_normalize(tile(source.position, (1, n_normals)) - anchors)
            light_source_directions_cos = tile(sum(light_source_directions * normals, axis=0), (3, 1))

            # ensure that all cosine values of the diffuse part are positive
            light_source_directions_cos = where(light_source_directions_cos < 0., 0., light_source_directions_cos)

            reflection_directions = 2.0 * light_source_directions_cos * normals - light_source_directions
            reflection_directions_cos = sum(reflection_directions * view_direction, axis=0)

            # ensure that all cosine values of the specular part are positive
            reflection_directions_cos = where(reflection_directions_cos < 0., 0., reflection_directions_cos)

            colors[0: 3, :] += (1. / n_sources) * ambient * material.ka

            diffuse_term = material.kd * light_source_directions_cos * diffuse
            colors[0:3, :] += diffuse_term

            specular_term = material.ks * tile(reflection_directions_cos ** material.alpha, (3, 1)) * specular
            specular_term = where(diffuse_term < 0, 0, specular_term)
            colors[0: 3, :] += specular_term

        return round(where(colors > 255, 255, colors))

    def _determine_face_colors(self,
                               solid: SolidRepresentation,
                               lights: list[LightSource],
                               color_table: ColorTable | None = None) -> ndarray:
        return self._determine_colors(solid.mesh.centers, solid.mesh.face_normals, solid.material,
                                      lights, solid.color, color_table)

    def _determine_node_colors(self,
                               solid: SolidRepresentation,
                               lights: list[LightSource],
                               color_table: ColorTable | None = None) -> ndarray:
        return self._determine_colors(solid.mesh.geometry.base, solid.mesh.nodal_normals, solid.material,
                                      lights, solid.color, color_table)

    def determine_visible_faces(self, part: PartRepresentation) -> ndarray:
        """
        Determine and sort the indices of faces which are facing towards the camera

        Parameters:
            part ( PartRepresentation ): part holding a collection of Solids
        
        Returns:
            ndarray:
                indices as ( 2 x N ) numpy array where the first row contains the index of the solid and the second row
                the face index whithin that solid
        """
        return self._sort_faces_by_position(self._remove_adverted_faces(part), part)

    def determine_face_colors(self,
                              part: PartRepresentation,
                              lights: list[LightSource],
                              color_table: ColorTable | None = None) -> list[ndarray]:
        """
        Determine the color of each face with respect to the camera position and the light sources   
        Note: Feature ColorTable is not implemented yet

        Parameters:
            part ( PartRepresentation ): part containing meshes to calculate the color for
            lights ( list[ LightSource ] ): list of light sources
            color_table ( Optional[ ColorTable ] = None ): colortable for calculating the color depending on mesh values
        
        Returns:
            list[ ndarray ]: list of numpy arrays with size ( 4 x N ) for each solid
        
        """
        return [self._determine_face_colors(solid, lights, color_table) for solid in part]

    def determine_node_colors(self,
                              part: PartRepresentation,
                              lights: list[LightSource],
                              color_table: ColorTable | None = None) -> list[ndarray]:
        return [self._determine_node_colors(solid, lights, color_table) for solid in part]

    def project_facets(self, part: PartRepresentation) -> PlanarMeshRepresentation:
        """
        Project the geometry of the mesh onto a plane to receive the planar coordinates

        Parameters:
            part ( PartRepresentation ): part containing the geometry for a collection of solids
        
        Returns:
            VisibleFacets: Mesh containing the 2D geometries and the topologies

        """
        geometry: list[Geometry] = []
        topology: list[Topology] = []
        for solid in part:
            geometry.append(Geometry(self._uv_coordinates_using_projector(solid.mesh.geometry.base)))
            topology.append(solid.mesh.topology)

        return PlanarMeshRepresentation(geometry, topology)

    def project_curves_and_edges(self, part: PartRepresentation) -> list[PlanarEdgesCollection]:
        """
        Project the smooth and sharp edges and the outline one a plane

        Parameters:
            part ( PartRepresentation ): part containing a collection of solids

        Returns:
            list[ VisibleEdges ]: Wire collection for each visibility type
        """
        model_base: CADModelBase = part.model.base

        shape_filter: OCPShapeAlgo = self._init_shape_algo_filter(self._base, model_base)
        edges: list[PlanarEdgesCollection] = []

        edges_for_edge_type: dict = {
            EdgeRepresentationType.VISIBLEOUTLINE: shape_filter.OutLineVCompound(),
            EdgeRepresentationType.HIDDENSMOOTHWIRE: shape_filter.OutLineHCompound(),
            EdgeRepresentationType.HIDDENSHARPWIRE: shape_filter.HCompound(),
            EdgeRepresentationType.VISIBLESMOOTHWIRE: shape_filter.Rg1LineVCompound(),
            EdgeRepresentationType.VISIBLESHARPWIRE: shape_filter.VCompound()
        }

        self._insert_edges_if_not_null(edges, edges_for_edge_type)

        return edges

    def get_coordinate_system(self) -> PlanarCoordinateSystemRepresentation:
        """
        Project a three-dimensional CoordinateSystem onto a plane

        Returns:
            CoordinateSystem: a projected coordinate system
        """
        coordinates = self._uv_coordinates_using_projector(transpose(
            array([(0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.)])))

        o, x, y, z = coordinates[:, 0], coordinates[:, 1], coordinates[:, 2], coordinates[:, 3]

        system = PlanarCoordinateSystemRepresentation(x - o, y - o, z - o)
        system.anchor = o

        return system

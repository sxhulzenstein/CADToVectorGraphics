from cadvectorgraphics.compose.components.view import Camera
from cadvectorgraphics.compose.components.representation.cad import CADModelBase
from cadvectorgraphics.compose.components.bind import PartRepresentation, SolidRepresentation
from cadvectorgraphics.compose.components.representation.mesh import Geometry, Topology
from cadvectorgraphics.compose.components.illuminate import LightSource
from cadvectorgraphics.render.components.geometry import PlanarMeshRepresentation, PlanarEdgesRepresentation, EdgeRepresentationType, PlanarCoordinateSystemRepresentation
from cadvectorgraphics.util.geometry import cNormalize
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Dir as OCPDirection, gp_Ax2 as OCPAxis,gp_Pnt as OCPSpacialPoint, gp_Pnt2d as OCPPlanarPoint
from typing import Optional
from numpy.typing import NDArray
from numpy import transpose, hstack, array, argwhere, argsort, tile, zeros, where, round, sum, ones, ndarray, full
from OCP.HLRBRep import HLRBRep_HLRToShape as OCPShapeAlgo, HLRBRep_Algo as OCPProjectionAlgo
from OCP.BRepLib import BRepLib
CurveBuilder = BRepLib.BuildCurves3d_s
from cadquery.occ_impl.shapes import Shape
from copy import deepcopy


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
            OCPAxis( OCPSpacialPoint( *self._camera.position ), OCPDirection( *self._camera.view ) ) )

    def _removeAdvertedFaces( self, part: PartRepresentation ) -> dict[ int, ndarray ]:
        visibleFacets: list[ ndarray ] = []

        for solid in part:
            ids: NDArray = array( list( solid.mesh.base.topology.base.keys() ) )
            scalarProd: NDArray = transpose( self._camera.view ) @ solid.mesh.normals[ :, ids ]
            visibleFacets.append( ids[ argwhere( scalarProd >= 0 ).flatten() ].flatten() )
        return visibleFacets

    def _sortFacesByPosition( self, idsDict: list[ ndarray ], part: PartRepresentation ) -> ndarray:
        directionalDistances: list[ ndarray ] = []
        index = 0
        for ids, solid in zip( idsDict, part.solids ):
            centers = solid.mesh.centers[ :, ids ]
            result = zeros( ( 3, ids.shape[ 0 ] ) )
            result[ 0, : ] =  transpose( self._camera.view ) @ centers
            result[ 1, : ] = ones( ( 1, ids.shape[ 0 ] ) ) * index
            index += 1
            result[ 2, : ] = ids
            directionalDistances.append( result )
        directionalDistancesStack = hstack( tuple( directionalDistances ) )

        return directionalDistancesStack[ 1 :, argsort( directionalDistancesStack[ 0, : ] ).flatten() ]

    def _uvCoordinatesUsingProjector( self, points: NDArray ) -> NDArray:
        uv_points: NDArray = zeros( ( 2, points.shape[ 1 ] ) )
        for index in range( uv_points.shape[ 1 ] ):
            projectedUVPoint = OCPPlanarPoint( 0., 0. )
            self._base.Project( OCPSpacialPoint( *points[ : ,index ] ), projectedUVPoint )
            uv_points[ :, index ] = array( [ projectedUVPoint.X(), projectedUVPoint.Y() ] )
        return uv_points

    def _initShapeAlgoFilter( self, cad: CADModelBase ) -> OCPShapeAlgo:
            hlr: OCPProjectionAlgo = OCPProjectionAlgo()
            hlr.Add( cad.val().wrapped )
            hlr.Projector( self._base )
            hlr.Update()
            hlr.Hide()
            return OCPShapeAlgo( hlr )
    
    def _insertEdgesIfNotNull( self, edges: list[ PlanarEdgesRepresentation ], edgesForEdgeType: dict ) -> None:
        for edgeType, edgesForType in edgesForEdgeType.items():
            if edgesForType.IsNull():
                continue
            CurveBuilder( edgesForType )
            edges.append( PlanarEdgesRepresentation( Shape( edgesForType ).Edges(), edgeType ) )

    def _determineFaceColors( self,
                              solid: SolidRepresentation, 
                              lights: list[ LightSource ], 
                              colorTable: Optional[ ColorTable ] = None ) -> ndarray:     
        
        mesh = solid.mesh
        ka = solid.material.ka
        kd = solid.material.kd
        ks = solid.material.ks
        alpha = solid.material.alpha

        normals = mesh.normals
        centers = mesh.centers

        nNormals: int = normals.shape[ 1 ]
        nSources: int = len( lights )

        viewDirection: NDArray = - tile( self._camera.view, ( 1, nNormals ) )

        if colorTable is None:
            ambient: NDArray = transpose( tile( array( solid.color.rgb() ), ( nNormals, 1 ) ) )
        else: 
            raise NotImplementedError()
        
        if nSources == 0:
            return ambient

        colors = zeros( ( 4, nNormals ) )
        colors[ 3, : ] = ones( ( 1, nNormals ) ) * solid.color.alpha
        
        for source in lights:
            diffuse = transpose( tile( array( source.color.rgb() ), ( nNormals, 1 ) ) )
            specular = transpose( tile( array( source.color.rgb() ), ( nNormals, 1 ) ) )
            lightSourceDirections = cNormalize( tile( source.position, ( 1, nNormals ) ) - centers )
            lightSourceDirectionsCos = tile( sum( lightSourceDirections * normals, axis=0 ) ,  ( 3, 1 ) )

            # ensure that all cosine values of the diffuse part are positive
            lightSourceDirectionsCos = where( lightSourceDirectionsCos < 0., 0., lightSourceDirectionsCos )

            reflectionDirections = 2.0 * lightSourceDirectionsCos * normals - lightSourceDirections
            reflectionDirectionsCos = sum( reflectionDirections * viewDirection, axis = 0 )
            
            # ensure that all cosine values of the specular part are positive
            reflectionDirectionsCos = where( reflectionDirectionsCos < 0., 0., reflectionDirectionsCos )

            colors[ 0 : 3, : ] += ( 1. / nSources ) * ambient * ka

            diffuseTerm = kd * lightSourceDirectionsCos * diffuse
            colors[ 0 : 3, : ] += diffuseTerm

            specularTerm = ks * tile( reflectionDirectionsCos ** alpha, ( 3, 1 ) ) * specular
            specularTerm = where( diffuseTerm < 0, 0, specularTerm )
            colors[ 0 : 3, : ] += specularTerm

        return round( where( colors > 255, 255, colors ) )

    def determineVisibleFaces( self, part: PartRepresentation ) -> ndarray:
        """
        Determine and sort the indices of faces which are facing towards the camera

        Parameters:
            part ( PartRepresentation ): part holding a collection of Solids
        
        Returns:
            ndarray: indices as ( 2 x N ) numpy array where the first row contains the index of the solid and the second row the face index whithin that solid
        """
        return self._sortFacesByPosition( self._removeAdvertedFaces( part ), part )
    
    
    def determineFaceColors( self,
                             part: PartRepresentation, 
                             lights: list[ LightSource ], 
                             colorTable: Optional[ ColorTable ] = None ) -> list[ ndarray ]:
        """
        Determine the color of each face with respect to the camera position and the light sources   
        Note: Feature ColorTable is not implemented yet

        Parameters:
            part ( PartRepresentation ): part containing meshes to calculate the calor for
            lights ( list[ LightSource ] ): list of light sources
            colorTable ( Optional[ ColorTable ] = None ): colortable for calculating the color depending on mesh values
        
        Returns:
            list[ ndarray ]: list of numpy arrays with size ( 4 x N ) for each solid
        
        """
        colors: list[ ndarray ] = []
        for solid in part:
            colors.append( self._determineFaceColors( solid, lights, colorTable ) )
        return colors


    def projectFacets( self, part: PartRepresentation ) -> PlanarMeshRepresentation:
        """
        Project the geometry of the mesh onto a plane to receive the planar coordinates

        Parameters:
            part ( PartRepresentation ): part containing the geometry for a collection of solids
        
        Returns:
            VisibleFacets: Mesh containing the 2D geometries and the topologies

        """
        geometry: list[ Geometry ] = []
        topology: list[ Topology ] = []
        for solid in part:
            geometry.append( Geometry( self._uvCoordinatesUsingProjector( solid.mesh.base.geometry.base ) ) )
            topology.append( solid.mesh.base.topology )
        
        return PlanarMeshRepresentation( geometry, topology )
    
    def projectCurvesAndEdges( self, part: PartRepresentation ) -> list[ PlanarEdgesRepresentation ]:
        """
        Project the smooth and sharp edges and the outline one a plane

        Parameters:
            part ( PartRepresentation ): part containing a collection of solids

        Returns:
            list[ VisibleEdges ]: Wire collection for each visibility type
        """
        modelBase: CADModelBase = part.model.base

        filter: OCPShapeAlgo = self._initShapeAlgoFilter( modelBase )
        edges: list[ PlanarEdgesRepresentation ] = []

        edgesForEdgeType: dict = {
            EdgeRepresentationType.VISIBLEOUTLINE : filter.OutLineVCompound(),
            EdgeRepresentationType.HIDDENSMOOTHWIRE : filter.OutLineHCompound(),
            EdgeRepresentationType.HIDDENSHARPWIRE : filter.HCompound(),
            EdgeRepresentationType.VISIBLESMOOTHWIRE : filter.Rg1LineVCompound(),
            EdgeRepresentationType.VISIBLESHARPWIRE : filter.VCompound()
        }

        self._insertEdgesIfNotNull( edges, edgesForEdgeType )
        
        return edges
    
    def getCoordinateSystem( self ) -> PlanarCoordinateSystemRepresentation:
        """
        Project a threedimensional CoordinateSystem onto a plane

        Returns:
            CoordinateSystem: a projected coordinate system
        """
        coords = self._uvCoordinatesUsingProjector( transpose( 
            array( [ ( 0., 0., 0. ), ( 1., 0., 0. ), ( 0., 1., 0. ) , ( 0., 0., 1. ) ] ) ) )
        
        o, x, y, z = coords[ :, 0 ], coords[ :, 1 ], coords[ :, 2 ], coords[ :, 3 ]

        system = PlanarCoordinateSystemRepresentation( x - o, y - o, z - o )
        system.anchor = o

        return system
        



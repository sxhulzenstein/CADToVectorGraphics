from .cad import CADModel
from cadquery import Solid, exporters, Face
import gmsh
import tempfile
from numpy import ndarray, array, transpose, hstack
from meshio import read, Mesh as MeshIOMesh
from uuid import uuid4
import os
from dataclasses import dataclass
import logging


@dataclass
class DefaultGeneratorOptions:
    tolerance: float = 0.01
    angular_tolerance: float = 0.1


@dataclass
class GmshGeneratorOptions:
    mesh_size_min: float | None = None
    mesh_size_max: float | None = None
    mesh_size_from_curvature: float | None = None  # Number of elements per 2 * pi
    dimension: int = 2
    algorithm: int = 6


class DefaultGenerator:
    @staticmethod
    def generate(model: CADModel | Solid, options: DefaultGeneratorOptions) -> tuple[ndarray, ndarray, ndarray]:
        g, t = model.tessellate(options.tolerance, options.angular_tolerance)
        geometry = transpose(array([p.toTuple() for p in g]))
        triangles = transpose(array(t))
        return geometry, triangles, array([])


class GmshGenerator:
    @staticmethod
    def _read_mesh(filepath: str) -> tuple[ndarray, ndarray, ndarray]:
        mesh_info: MeshIOMesh = read(filepath)
        return (transpose(array(mesh_info.points)), mesh_info.get_cells_type("triangle"),
                mesh_info.get_cells_type("quad"))

    @staticmethod
    def _generate(model: CADModel | Solid | Face, options: GmshGeneratorOptions) -> tuple[ndarray, ndarray, ndarray]:
        gmsh.clear()
        with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as file:
            file.close()

            if type(model) is CADModel:
                exporters.export(model.base, file.name)
            else:
                model.exportStep(file.name)

            gmsh.model.add(str(uuid4()))
            gmsh.merge(file.name)
            os.remove(file.name)
            gmsh.option.setNumber("Mesh.Algorithm", options.algorithm)

            if options.mesh_size_min:
                gmsh.option.setNumber("Mesh.MeshSizeMin", options.mesh_size_min)

            if options.mesh_size_max:
                gmsh.option.setNumber("Mesh.MeshSizeMax", options.mesh_size_max)

            if options.mesh_size_from_curvature:
                gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", options.mesh_size_from_curvature)

            gmsh.model.mesh.generate(options.dimension)

        with tempfile.NamedTemporaryFile(suffix=".msh", delete=False) as mesh_file:
            mesh_file.close()
            gmsh.write(mesh_file.name)
            geometry, triangles, quadrilaterals = GmshGenerator._read_mesh(mesh_file.name)
            os.remove(mesh_file.name)
        return geometry, transpose(triangles), transpose(quadrilaterals)

    @staticmethod
    def _generate_by_surfaces(model: CADModel | Solid, options: GmshGeneratorOptions):
        faces: list[Face] = model.base.faces().vals() if type(model) is CADModel else model.Faces()
        geometries = []
        triangles = []
        quadrilaterals = []

        index_shift = 0
        for face in faces:
            g, t, q = GmshGenerator._generate(face, options)
            geometries.append(g)
            triangles.append(t + index_shift)
            quadrilaterals.append(q + index_shift)
            index_shift += g.shape[1]

        return hstack(geometries), hstack(triangles), hstack(quadrilaterals)

    @staticmethod
    def generate(model: CADModel | Solid, options: GmshGeneratorOptions) -> tuple[ndarray, ndarray, ndarray]:
        try:
            gmsh.initialize()
            return GmshGenerator._generate_by_surfaces(model, options)
        except Exception as e:
            logging.warning(f"Using the default mesh generator because gmsh threw the following error: \n {str(e)}")
            return DefaultGenerator.generate(model, DefaultGeneratorOptions())
        finally:
            gmsh.finalize()


class MeshModelGenerator:
    @staticmethod
    def generate(model: CADModel | Solid,
                 options: GmshGeneratorOptions | DefaultGeneratorOptions) -> tuple[ndarray, ndarray, ndarray]:
        if type(options) is GmshGeneratorOptions:
            return GmshGenerator.generate(model, options)
        if type(options) is DefaultGenerator:
            return DefaultGenerator.generate(model, options)
        raise NotImplementedError(type(options))

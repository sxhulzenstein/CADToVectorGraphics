import unittest
from cadquery import Workplane, importers, BoundBox
from src.cadvectorgraphics.compose.components.geometry.cad import CADModel


class TestComposeRepresentationCad(unittest.TestCase):
    def assertEqualBoundingBox(self, expected: BoundBox, actual: BoundBox) -> None:
        self.assertEqual(expected.xlen, actual.xlen)
        self.assertEqual(expected.ylen, actual.ylen)
        self.assertEqual(expected.zlen, actual.zlen)

        self.assertEqual(expected.xmin, actual.xmin)
        self.assertEqual(expected.ymin, actual.ymin)
        self.assertEqual(expected.zmin, actual.zmin)

        self.assertEqual(expected.xmax, actual.xmax)
        self.assertEqual(expected.ymax, actual.ymax)
        self.assertEqual(expected.zmax, actual.zmax)

    def test_init_cad_by_model(self) -> None:
        model = Workplane().box(10, 10, 10)
        cad = CADModel(model, "A CAD model.")
        self.assertEqual(cad.name, "A CAD model.")
        self.assertEqual(cad.base, model)

    def test_init_cad_by_filepath(self) -> None:
        cad = CADModel.from_file("data/cube_10.step")
        self.assertEqual(cad.name, "cube_10")
        self.assertEqualBoundingBox(cad.base.val().BoundingBox(), Workplane().box(10, 10, 10).val().BoundingBox())


if __name__ == '__main__':
    unittest.main()

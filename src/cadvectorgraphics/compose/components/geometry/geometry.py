from cadquery import Vector as VectorBase
from numpy import array, ndarray
from ....util.exceptions import EmptyGeometryException


class Geometry:
    def __init__(self, points: list[VectorBase] | list[tuple[float, ...]] | ndarray) -> None:
        """
        Creates an Object containing nodes of an arbitrary mesh

        Parameters:
            points ( list[ VectorBase ] | list[ tuple[ float, ... ] ] | ndarray ): geometry information
        """
        if len(points) == 0:
            raise EmptyGeometryException()

        if type(points[0]) is tuple:
            self._base = array(points)
        elif type(points[0]) is VectorBase:
            self._base = array([p.toTuple() for p in points]).transpose()
        elif type(points) is ndarray:
            self._base = points
        else:
            raise Exception()

    @property
    def base(self) -> ndarray:
        """
        Get the container of all nodes

        Returns:
            ndarray: container as numpy array
        """
        return self._base

    @property
    def dimension(self) -> int:
        """
        Get the dimension of the point cloud

        Returns:
            int: number of entries of each column ( = dimension )
        """
        return self._base.shape[0]

    @property
    def size(self) -> int:
        """
        Get the size of the point cloud

        Returns:
            int: number of entries of each row ( = size )
        """
        return self._base.shape[1]

    def __len__(self) -> int:
        """
        Get the size of the point cloud

        Returns:
            int: number of entries of each row ( = size )
        """
        return self.size

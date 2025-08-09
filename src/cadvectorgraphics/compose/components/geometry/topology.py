from numpy import ndarray
from functools import cached_property


class Topology:
    def __init__(self, triangles: ndarray, quadrilaterals: ndarray) -> None:
        """
        Creating an object which contains the topological information of a mesh

        Parameters:
            triangles ( list[ tuple[ int, ... ] ] | list[ list[ int ] ]  ): topological information
            quadrilaterals
        """
        self._base: dict[int, ndarray] = ({key: triangles[:, key].flatten()
                                           for key in range(triangles.shape[1])}
                                          | {key + triangles.shape[1]: quadrilaterals[:, key].flatten()
                                             for key in range(quadrilaterals.shape[1])})

    @property
    def base(self) -> dict[int, ndarray]:
        """
        Get the base object holding the topology

        Returns:
            dict[ int, tuple[ int, ... ] ]: topology information
        """
        return self._base

    @cached_property
    def triangles(self) -> dict[int, ndarray]:
        """
        Extract the topological information of the triangles

        Returns:
            dict[ int, tuple[ int, int, int ] ]: topology information of triangles
        """
        return {key: value for key, value in self._base.items() if len(value) == 3}

    @cached_property
    def quadrilaterals(self) -> dict[int, ndarray]:
        """
        Extract the topological information of the quadrilaterals

        Returns:
            dict[ int, tuple[ int, int, int, int ] ]: topology information of quadrilaterals
        """
        return {key: value for key, value in self._base.items() if len(value) == 4}

    def __getitem__(self, key: int | list[int] | tuple[int, ...]) -> ndarray | list[ndarray]:
        """
        Get node indices of one or more elements

        Parameters:
            key ( int | list[ int ] | tuple[ int, ... ] ): indices of elements

        Returns:
            tuple[ int, ... ] | list[ tuple[ int, ... ] ]: topology information of requested elements
        """
        if type(key) is int:
            return self._base[key]
        elif type(key) is tuple or type(key) is list:
            return [self._base[face] for face in key]
        else:
            raise TypeError(type(key))

    def __setitem__(self, key: int, ids: ndarray) -> None:
        """
        Set the node indices of one element

        Parameters:
            key ( int ): face id
            ids ( tuple[ int, ... ] ): node ids of the adjusted face

        """
        self._base[key] = ids

    def __len__(self) -> int:
        """
        Get the number of elements in the topology

        Returns:
            int: number of 2D elements
        """
        return self.size

    @property
    def size(self) -> int:
        """
        Get the number of elements in the topology

        Returns:
            int: number of 2D elements
        """
        return len(self._base.keys())

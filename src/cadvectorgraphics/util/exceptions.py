class EmptyGeometryException(Exception):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(message if message else "The provided geometry has no points.")


class WrongGeometryDimensionException(Exception):
    def __init__(self, desired_dimension: int, actual_dimension: int) -> None:
        super().__init__(f"Geometry has the dimension {actual_dimension} but {desired_dimension} is desired.")
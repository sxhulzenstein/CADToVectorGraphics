from numpy import isnan, array, errstate
from numpy import divide, sum,  multiply, where, sqrt, ndarray, zeros
from numpy.matlib import repmat, sum, reshape
from numpy.linalg import norm


def normalize( matrix: ndarray ) -> ndarray:
    """
    Normalize the matrix

    Parameters:
        matrix ( ndarray ): input matrix
    
    Returns:
        ndarray: normalized matrix
    """
    n = norm( matrix )
    return zeros(matrix.shape) if n == 0.0 else divide( matrix, n)


def columnwise_normalize(matrix: ndarray) -> ndarray:
    """
    Columnwise Normalizing of a matrix

    Parameters:
        matrix ( ndarray ): input matrix

    Returns:
        ndarray: normalized matrix
    """
    n = repmat( sqrt( sum( multiply( matrix, matrix ), axis = 0 ) ), matrix.shape[ 0 ], 1 )
    with errstate(divide='ignore', invalid='ignore'):
        return where((isnan(n)) | (n == 0), 0, divide(matrix, n))

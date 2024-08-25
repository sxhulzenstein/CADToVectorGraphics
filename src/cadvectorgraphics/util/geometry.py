from numpy import isnan, array
from numpy import divide, sum,  multiply, where, sqrt, ndarray
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
    return divide( matrix, norm( matrix ) )

def cNormalize( matrix: ndarray ) -> ndarray:
    """
    Columnwise Normalizing of a matrix

    Parameters:
        matrix ( ndarray ): input matrix

    Returns:
        ndarray: normalized matrix
    """
    n = divide( matrix, repmat( sqrt( sum( multiply( matrix, matrix ), axis = 0 ) ), matrix.shape[ 0 ], 1 ) )
    return where( isnan( n ), 0, n )
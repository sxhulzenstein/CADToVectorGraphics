from numpy import isnan, array
from numpy import divide, sum,  multiply, where, sqrt, ndarray
from numpy.matlib import repmat, sum, reshape
from numpy.linalg import norm

def normalize( matrix: ndarray ) -> ndarray:
    return divide( matrix, norm( matrix ) )

def cNormalize( matrix: ndarray ) -> ndarray:
    n = divide( matrix, repmat( sqrt( sum( multiply( matrix, matrix ), axis = 0 ) ), matrix.shape[ 0 ], 1 ) )
    return where( isnan( n ), 0, n )
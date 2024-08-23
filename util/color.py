from random import randint

class RGBA:
    def __init__( self, r: int, g: int, b: int, a: int = 255 ) -> None:
        self._r = r
        self._g = g
        self._b = b
        self._a = a

    @property
    def red( self ) -> int:
        return self._r

    @property
    def green( self ) -> int:
        return self._g

    @property
    def blue( self ) -> int:
        return self._b

    @property
    def alpha( self ) -> int:
        return self._a

    def __str__( self ) -> str:
        return f"({ self._r }, { self._g }, { self._b })"
    
    def rgb( self ) -> tuple[ int, int, int ]:
        return int( self._r ), int( self._g ), int( self._b )
    
    def rgba( self ) -> tuple[ int, int, int, int ]:
        return self._r, self._g, self._b, self._a
    

def randomGrayColor( lowerBound: int, upperBound: int ) -> RGBA:
    color: int = randint(lowerBound, upperBound)
    return RGBA( color, color, color )
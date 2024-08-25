from enum import Enum
from numpy import ndarray, array, zeros, transpose, stack
from numpy.linalg import norm
from cadvectorgraphics.util.color import RGBA
from cadvectorgraphics.util.geometry import normalize
from cadvectorgraphics.illustrate.components.style import ArrowStyle
from uuid import uuid4

class SVGElementType( Enum ):
    SVG = 1
    GROUP = 2
    POLYGON = 3
    LINE = 4
    PATH = 5
    TEXT = 6
    STYLE = 7
    ANY = 8

class SVGElement:
    def _substitudeEntryByKey( self, key: str, newkey: str ):
        if key in self._args.keys():
            value = self._args.pop( key )
            self._args[ newkey ] = value

    def _substitudeEntryKeys( self ) -> None:
        self._substitudeEntryByKey( "fillopacity", "fill-opacity" )
        self._substitudeEntryByKey( "strokewidth", "stroke-width" )
        self._substitudeEntryByKey( "strokeopacity", "stroke-opacity" )
        self._substitudeEntryByKey( "strokelinejoin", "stroke-linejoin" )
        self._substitudeEntryByKey( "strokelinecap", "stroke-linecap" )
        self._substitudeEntryByKey( "styleclass", "class" )
        self._substitudeEntryByKey( "strokedasharray", "stroke-dasharray" )
    
    def __init__( self, elementType: SVGElementType, **kwargs ) -> None:
        self._type: SVGElementType = elementType
        self._args: dict = kwargs
        self._contents: list[ SVGElement ] = []
        self._substitudeEntryKeys()
    
    def append( self, contents ) -> None:
        if contents is None:
            return
        self._contents.append( contents )
    
    def extend( self, contents: list ):
        if contents is None:
            return
        self._contents.extend( contents )

    def _writeAdditionalArgumenst( self ) -> str:
        contents = [ f"{ key }=\"{content}\"" for key, content in list( self._args.items() ) ]
        return " ".join( contents )

    def write( self, outputlist: list[ str ] ) -> None:
        argStr: str = self._writeAdditionalArgumenst()

        if self._type == SVGElementType.SVG:
            outputlist.append( """<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n""" )
            outputlist.append( f"<svg { argStr }>\n" )
            for content in self._contents:
                content.write( outputlist )
            outputlist.append( "</svg>\n" )
        
        if self._type == SVGElementType.GROUP:
            outputlist.append( f"<g { argStr } >\n" )
            for content in self._contents:
                content.write( outputlist )
            outputlist.append( "</g>\n" )
        
        if self._type == SVGElementType.STYLE:
            outputlist.append( f"<style>\n" )
            for content in self._contents:
                content.write( outputlist )
            outputlist.append( "</style>\n" )
        
        if self._type == SVGElementType.LINE:
            outputlist.append( f"<line { argStr } />\n" )
        
        if self._type == SVGElementType.POLYGON:
            outputlist.append( f"<polygon { argStr } />\n" )

        if self._type == SVGElementType.PATH:
            outputlist.append( f"<path { argStr } />\n" )
        
        if self._type == SVGElementType.TEXT:
            outputlist.append( f"<text {argStr}>\n" )
            for content in self._contents:
                content.write( outputlist )
            outputlist.append( "</text>" )
        
        if self._type == SVGElementType.ANY:
            outputlist.append( str( self._args[ "content" ] ) +"\n" )

    def __str__( self ) -> str:
        output: list[ str ] = []
        self.write( output )
        return "".join( output )

class SVGHelper:
    @staticmethod
    def Path( points: ndarray ) -> SVGElement:
        x, y = list( points[ 0, : ] ), list( points[ 1, : ] )
        path = [ f"M{ x[ 0 ] },{ y[ 0 ] }" ]
        path.extend( [ f"L{ xi },{ yi }" for xi, yi in zip( x[ 1 : ], y[ 1 : ] ) ] )
        return SVGElement( SVGElementType.PATH, d = ' '.join( path ) )
    
    @staticmethod
    def TransformGroup( scale: tuple[ float, float ], translate: tuple[ float, float ] ) -> SVGElement:
        return SVGElement( SVGElementType.GROUP, transform=f"scale({ scale[ 0 ] }, { scale[ 1 ] }) translate({ translate[ 0 ] },{ translate[ 1 ] })" )
    
    @staticmethod
    def SVG( width: float, height: float ) -> SVGElement:
        return SVGElement( SVGElementType.SVG, xmlns = "http://www.w3.org/2000/svg", width = f"{ width }", height = f"{ height }" )
    
    @staticmethod
    def Polygon( points: ndarray, fill: RGBA, stroke: RGBA, width: float, dash: tuple[ int, ... ] = ( 1, 0 ) ) -> SVGElement:
        x, y = list( points[ 0, : ] ), list( points[ 1, : ] )
        outline = ' '.join( f"{ xi },{ yi }" for xi, yi in zip( x, y ) )
        dasharray = ', '.join( str( v ) for v in dash )
        return SVGElement( SVGElementType.POLYGON, points = outline, strokewidth = width, strokeopacity = stroke.opacity, 
                           fillopacity = fill.opacity, strokelinejoin = "round", fill = f"rgb{ str( fill ) }", stroke = f"rgb{ str( stroke ) }", 
                           strokedasharray = dasharray )
    
    @staticmethod
    def StyleGroup( strokeColor: RGBA, strokeWidth: float, dash: tuple[ float, ...] = ( 1, 0 ), fillColor: RGBA = RGBA( 0, 0, 0, 0 ) ) -> SVGElement:
        dasharray = ', '.join( str( v ) for v in dash )

        return SVGElement( SVGElementType.GROUP, stroke = f"rgb{ str( strokeColor ) }", strokewidth = strokeWidth, strokeopacity = strokeColor.opacity, 
                           fill = f"{ str( fillColor ) }", fillopacity = fillColor.opacity, strokelinejoin = "round", strokelinecap = "round", strokedasharray=dasharray )
    
    @staticmethod
    def Line( p0: ndarray, p1: ndarray, strokeColor: RGBA, strokeWidth: float ) -> SVGElement:
        return SVGElement( SVGElementType.LINE, x1 = p0[ 0 ], y1 = p0[ 1 ], x2 = p1[ 0 ], y2 = p1[ 1 ], 
                          stroke = f"rgb{ str( strokeColor ) }", strokewidth = strokeWidth, strokelinecap = "round" )
    
    @staticmethod
    def Style():
        return SVGElement( SVGElementType.STYLE )
    
    @staticmethod
    def Text( p: ndarray, text: str, style: str ) -> SVGElement:
        textelement = SVGElement( SVGElementType.TEXT, x=p[ 0 ], y=p[ 1 ], styleclass=style )
        textelement.append( SVGElement( SVGElementType.ANY, content=text ) )
        return textelement
    
    @staticmethod
    def Arrow( p0: ndarray, p1: ndarray, unitLength: float, style: ArrowStyle ) -> SVGElement:
        actualLength: float = norm( p1- p0 )
        adjustedArrowHeadLength = style.headlength * actualLength / unitLength
        n01: ndarray = normalize( p1 - p0 ).flatten()
        n01Ortho: ndarray = n01[ array( ( 1, 0 ) ) ] * array( ( 1, - 1 ) )
        p2 = p0 + ( actualLength * 1.25 ) * n01
        q0 = p1 - adjustedArrowHeadLength * n01 - n01Ortho * style.headwidth / 2
        q1 = p1 - adjustedArrowHeadLength * n01 + n01Ortho * style.headwidth / 2

        group = SVGHelper.TransformGroup( ( 1, 1 ),  ( 0, 0 ) )
        group.append( SVGHelper.Line( p0, p1, style.color, style.strokewidth ) )
        group.append( SVGHelper.Polygon( transpose( stack( ( p1, q0, q1 ) ) ), style.color, style.color, style.strokewidth ) )
        if not style.label is None:
            styleElement = SVGHelper.Style()
            styleElement.append( CreatefontClass( style.label, style.fontSize, style.color ) )
            group.append( styleElement )

            # automatic label positioning to avoid overlapping
            dx = - style.fontSize if sum( n01 * array( ( 1, 0 ) ) ) < 0 else 0
            dy = style.fontSize if - sum( n01 * array( ( 0, 1 ) ) ) < 0 else 0

            text = SVGHelper.Text( (  p2[ 0 ] + dx,  p2[ 1 ] + dy ), style.label, style.label )

            group.append( text )
        return group
        

def CreatefontClass( name: str, size: float, fill: RGBA, sizeUnit: str = "pt", style: str = "italic", font: str = "serif" ) -> SVGElement:
    fontstyle: str = f"font: { style } { size }{ sizeUnit } { font }; fill: rgb{ str( fill ) };"
    return SVGElement( SVGElementType.ANY, content=f".{name} {{ {fontstyle} }}" )
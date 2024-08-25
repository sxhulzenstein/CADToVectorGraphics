# CADVectorGraphics - Converting CAD files to beautiful scalable vector graphics

## Motivation
Have you ever gotten annoyed by MS Word minimizing the resolution of your images? Did you ever feel the frustration of losing the fine details in your illustrations in just a few pixels? - Then you are in the right place! 
This python project aims to provide a possibility to render a CAD object as a vector graphic, namely a SVG. 

## Implemented Features ... so far
Integreted features are:
* importing `.step` files or importing `cadquery`-objects
* import of single part or assemblies
* creating a triangular surface mesh of the imported model using a simplified interface to the `gmsh` library
* colorizing each imported model
* setting the material properties ka, kd, ks and the shininess for rendering the object
* setting a view position
* adding multiple light sources, given by color and position
* rendering which includes shading of the object
* adding different edge line styles and face outline styles
* adding and configuring a coordinate system
* scaling the resulting image, giving margins and zooming into the object
* exporting the image as SVG

## What's next?
Although the use case is very specific, there are still several features that might be nice to have:
* exporting the created meshes
* generating volume meshes for external simulations, also non-linear elements
* importing simulation data
* displaying simulation data requires implementing a legend
* cutting models and showing the cut surfaces using line patterns similair to technical drawings
* annotations using arrows and labels
* shallow dimensioning
* illustrating rotation axes
* exporting images as EMF, PDF, TIKZ ...
* anything that comes to  mind by the users

## Installation
The package can be installed using pip with the following command:
```
pip install cadvectorgraphics
```

## Troubleshooting

### Troubles with newer versions of numpy
If you have the issue of some packages not finding a numpy object, try using an older version (e.g. 1.26) of numpy
```
pip install numpy==1.26 --upgrade
```

### SVG not really working for MS office applications
A scalable vector graphic might not be the best choice for the use in MS office applications. A better option would be to use the Enhanced Meta File (EMF). However it's quite easy to convert an SVG to an EMF file using Inkscape. You can either open the SVG in Inkscape directly and save it as a new file with the suitable extension.
The other method is to use Inksckape from the command line.
```bat
cd [DIR_TO_MY_FILE]
inkscape "[FILENAME].svg" --export-filename="[FILENAME].emf" --export-dpi="[DPI]"
```
Of coarse you have to adjust `DIR_TO_MY_FILE`, `FILENAME` and `DPI` according to your needs. You can find more information on that [here](https://wiki.inkscape.org/wiki/Using_the_Command_Line). Do not forget to add the `inkscape.exe` to your PATH before executing the command.

## Example

In the following, a small example script is provided.

```python
from cadvectorgraphics import *

from cadquery import Workplane, exporters

# providing an initial model with cadquery
# the CAD-file can be obtained from any prefered CAD-system
box = Workplane().box( 10, 10, 10 ).edges( "|Z" ).fillet( 1 ).faces(">Z").workplane().cboreHole( 5, 7, 3 )
exporters.export( box, "model.step" )

# importing the file to a CAD-model representation
part = PartRepresentation( "model.step" )
part.color( 0, ( 100, 200, 100 ) )

# creating a mesh from the CAD-file
part.tessellateAll( size = MeshSize.GRAINY )

# creating a scene to assemble all necessary objects such as the view, the ligths and the model
scene = VirtualScene( part )
scene.setCameraPosition( position = ( 15, 15, 15 ) )

# adding a light source
# multiple lights can be added
# if none is added, the object will be displayed with the given base color
lightSource = LightSource( position = ( 20, 10, 0 ) )
lightSource.color = ( 150, 50, 255 )
scene.appendLightSource( light = lightSource )

# adding the scene with all components to a renderer
renderer: VirtualRenderer = VirtualRenderer( scene )
renderer.render()

# creating an image from the renderer result
image = Image( renderer )

# zooming into the geometry
image.zoom = ( 10, 10 )

# scaling all elements of the image
image.scale = ( 1, 1 )

# setting margins
image.margins = ( 5, 5 )

# creating line styles for special edges and curves
# if none is added, only the mesh is visible
visibleOutlineStyle = LineStyle( EdgeRepresentationType.VISIBLEOUTLINE )
visibleOutlineStyle.width = 0.25
visibleOutlineStyle.color = ( 0, 0, 0 )
image.addLineStyle( visibleOutlineStyle )

visibleSharpStyle = LineStyle( EdgeRepresentationType.VISIBLESHARPWIRE )
visibleSharpStyle.width = 0.25
visibleSharpStyle.color = ( 0, 0, 0 )
image.addLineStyle( visibleSharpStyle )

visibleSmoothStyle = LineStyle( EdgeRepresentationType.VISIBLESMOOTHWIRE )
visibleSmoothStyle.width = 0.1
visibleSmoothStyle.color = ( 0, 0, 0 )
visibleSmoothStyle.dash = ( 1, 0.2, 0.2, 0.2 )
image.addLineStyle( visibleSmoothStyle )

# creating style information for the coordinate system
coordStyle = CoordSystemStyle( size = 30 )
image.setCoordSystemStyle( coordStyle )

# export the image as svg
image.write()
```
This script has the following output then. It may be said that this an png image so that it can be seen here.
![model](https://github.com/user-attachments/assets/b09f3b13-0691-451b-ac8a-78d8435ff034)

![model](https://github.com/user-attachments/assets/e6f8096e-c8d4-4279-9018-31ec5d812398)

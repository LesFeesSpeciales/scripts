# LFS Blender Scripts

Various Blender scripts, used in production or proof of concepts.

### Files
#### Filesize graph
This script generates a curve in the 3D view based on a file sequence present in the specified directory. It should be used to monitor image sequence rendering. It allows the user to quickly spot empty images, as well as some artifacts when an image has a different weight from its neighbors.

---
### Layout
#### Camera plane
Import an image and parent it to the camera. You can then set the distance and width from the image object's properties. The plane will adjust to the camera's FOV or focal length.  
You can easily import several images at once, which will be equally spaced in depth. This is useful when creating painted stage-like sets which need to stick to a camera.

![Plane settings](docs/camera_plane_props.png "Camera Custom Properties")  
Two settings are available upon selecting a plane:
* `distance` is the distance from the camera to the plane
* `passepartout` is an additional scale for the plane

![Focal 1](docs/camera_plane_focal1.png "Focal 1")  
![Focal 2](docs/camera_plane_focal2.png "Focal 2")  
Two focal settings with the same plane.

---
### Material
#### Material tuning
Change some material properties. Useful for recolorizing textures on multiple objects at the same time (eg. add a globally darker shade to a character in a given shot). Blender Internal only.

#### Proxify
Create proxy images to enhance performance in scenes containing a large number of large textures.

---
### Rigging
#### Shape to bone
Transfer a mesh object's shape to the active bone in Pose Mode. Automatically creates a `WGT_` object instance.

---
### Simulation
#### Particle system template
An example script to create particle simulations using duplivert instances at each animation frame.

#### Fourmis
French for “ants”. Uses the particle system template to generate an ant colony walking along a specified path using boids.

-----

# License

Blender scripts shared by **Les Fées Spéciales** are, except where otherwise noted, licensed under the GPLv2 license.

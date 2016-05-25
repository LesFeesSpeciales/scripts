# Copyright Les Fees Speciales 2016
# 
# voeu@les-fees-speciales.coop
# 
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
# 
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
# 
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
# 
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

bl_info = {
    "name": "Create Camera Plane",
    "author": "Les Fees Speciales",
    "version": (1, 0),
    "blender": (2, 75, 0),
    "location": "Camera > Camera Plane",
    "description": "Imports image and sticks it to the camera",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
    }


#----------------------------------------------------------
# File camera_plane.py
#----------------------------------------------------------
import bpy, math
from bpy_extras.io_utils import ImportHelper
from rna_prop_ui import rna_idprop_ui_prop_get
from bpy.props import *
import os

#def enable_addon(self, addon_name):
#    """
#    from http://blender.stackexchange.com/questions/15638/how-to-distinguish-between-addon-is-not-installed-and-addon-is-not-enabled
#    """
#    if addon_name not in addon_utils.addons_fake_modules.keys():
#        self.report("ERROR", "%s: Addon not installed." % addon_name)
#    else:
#        default, state = addon_utils.check(addon_name)
#        if not state:
#            try:
#                mod = addon_utils.enable(addon_name, default_set=False, persistent=False)
#            except:
#                self.report("%s: Could not enable Addon on the fly." % addon_name )
#                print("%s: Could not enable Addon on the fly." % addon_name )

#    return state
 
class IMPORT_OT_Camera_Plane(bpy.types.Operator, ImportHelper):
    '''Build a camera plane'''
    bl_idname = "camera.camera_plane_build"
    bl_label = "Build Camera Plane"
    bl_options = {'REGISTER', 'UNDO'}
    _context_path = "object.data"
    _property_type = bpy.types.Camera
    
    # -----------
    # File props.
    files = CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory = StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    
    def build_camera_plane(self, context):
        # Selection Camera
        cam = context.scene.camera

        selected = context.selected_objects
        
        # Enable import images addon
        dir, file = os.path.split(self.filepath)
        try:
            bpy.ops.import_image.to_plane(files=[{"name": file}],
                directory=dir,
                use_transparency=True,
                use_shadeless=True,
                transparency_method='Z_TRANSPARENCY')
        except AttributeError:
            self.report({'ERROR'}, 'Addon Import Images As Planes not loaded. Please load it.')
            return {'CANCELLED'}
        plane = context.active_object
        # Scale factor: Import images addon imports images with a height of 1
        # this scales it back to a width of 1
        scale_factor = plane.dimensions[0]
        for v in plane.data.vertices:
            #scale_factor = v.co[0]
            v.co /= scale_factor
        plane.parent = cam
        plane.matrix_world = cam.matrix_world
        plane.lock_location = (True,)*3
        plane.lock_rotation = (True,)*3
        plane.lock_scale    = (True,)*3

        # Custom properties
        prop = rna_idprop_ui_prop_get(plane, "distance", create=True)
        plane["distance"] = 25.0
        prop["soft_min"] = 0
        prop["soft_max"] = 10000
        prop["min"] = 0
        prop["max"] = 1000

        prop = rna_idprop_ui_prop_get(plane, "passepartout", create=True)
        plane["passepartout"] = 1.2
        prop["soft_min"] = 0
        prop["soft_max"] = 100
        prop["min"] = 0
        prop["max"] = 100
        
        
        # DRIVERS

        ## DISTANCE ##
        driver = plane.driver_add('location',2)

        # driver type
        driver.driver.type = 'SCRIPTED'

        # enable Debug Info
        driver.driver.show_debug_info = True

        var = driver.driver.variables.new()

        # variable name
        var.name = "distance"

        # variable type
        var.type = 'SINGLE_PROP'
        var.targets[0].id = plane
        var.targets[0].data_path = '["distance"]'

        # Expression
        driver.driver.expression = "-distance"

        # SCALE X AND Y
        for axis in range(2):
            driver = plane.driver_add('scale', axis)

            # driver type
            driver.driver.type = 'SCRIPTED'

            # enable Debug Info
            driver.driver.show_debug_info = True

            # Variable DISTANCE
            var = driver.driver.variables.new()
            # variable name
            var.name = "distance"
            # variable type
            var.type = 'SINGLE_PROP'
            var.targets[0].id = plane
            var.targets[0].data_path = '["distance"]'

            # Variable FOV
            var = driver.driver.variables.new()
            # variable name
            var.name = "FOV"
            # variable type
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = "CAMERA"
            var.targets[0].id = cam.data
            var.targets[0].data_path = 'angle'

            # Variable passepartout
            var = driver.driver.variables.new()
            # variable name
            var.name = "passepartout"
            # variable type
            var.type = 'SINGLE_PROP'
            var.targets[0].id = plane
            var.targets[0].data_path = '["passepartout"]'


            # Expression
            driver.driver.expression = "tan(FOV/2) * distance*2 * passepartout"

        return {'FINISHED'}
     
    def execute(self, context):
        return self.build_camera_plane(context)
        #return {'FINISHED'}

#
#    Registration
#    Makes it possible to access the script from the Add > Mesh menu
#
 
def menu_func(self, context):
    self.layout.operator("camera.camera_plane_build", 
        text="Camera Plane", 
        icon='MESH_PLANE')
 
def register():
   bpy.utils.register_module(__name__)
   bpy.types.DATA_PT_camera.append(menu_func)
 
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.DATA_PT_camera.remove(menu_func)
 
if __name__ == "__main__":
    register()
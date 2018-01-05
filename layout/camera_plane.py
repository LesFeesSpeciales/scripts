# Copyright (C) 2016 Les Fees Speciales
# voeu@les-fees-speciales.coop
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


bl_info = {
    "name": "Create Camera Plane",
    "author": "Les Fees Speciales",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "location": "Camera > Camera Plane",
    "description": "Imports image and sticks it to the camera",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
    }


#----------------------------------------------------------
# File camera_plane.py
#----------------------------------------------------------
import bpy
import math
from bpy_extras.io_utils import ImportHelper
from rna_prop_ui import rna_idprop_ui_prop_get
from bpy.props import *
import os


class IMPORT_OT_Camera_Plane(bpy.types.Operator, ImportHelper):
    '''Build a camera plane'''
    bl_idname = "camera.camera_plane_build"
    bl_label = "Build Camera Plane"
    bl_options = {'REGISTER', 'UNDO'}
    _context_path = "object.data"
    _property_type = bpy.types.Camera

    # -----------
    # File props.
    files = CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'})
    directory = StringProperty(
        maxlen=1024,
        subtype='FILE_PATH',
        options={'HIDDEN', 'SKIP_SAVE'})
    passepartout = EnumProperty(
        name='Passepartout',
        items=(('16_9', '16 : 9', '16 : 9'),
               ('16_10', '16 : 10', '16 : 10')),
        default='16_9',
        # options={'HIDDEN'},
    )
    # passepartout = FloatProperty(
    #     name='Passepartout',
    #     default=100.0,
    #     soft_min=0,
    #     soft_max=500,
    #     min=0,
    #     max=500,
    #     subtype='PERCENTAGE',
    # )
    distance = FloatProperty(
        name='Distance',
        default=25.0,
        soft_min=0,
        soft_max=10000,
        min=0,
        max=1000,
        subtype='DISTANCE',
        unit='LENGTH'
    )

    def build_camera_plane(self, context):
        # Selection Camera
        cam = context.active_object

        # selected = context.selected_objects

        files = [os.path.basename(f.name) for f in self.files]
        for i, f in enumerate(files):
            try:
                bpy.ops.import_image.to_plane(
                    files=[{"name": f}],
                    directory=self.directory,
                    use_transparency=True,
                    shader='SHADELESS',
                    # use_shadeless=True,
                    # transparency_method='Z_TRANSPARENCY'
                    )
            except AttributeError:
                self.report(
                    {'ERROR'},
                    'Addon Import Images As Planes not loaded. '
                    'Please load it.')
                return {'CANCELLED'}
            plane = context.active_object
            # Scale factor: Import images addon imports
            # images with a height of 1
            # this scales it back to a width of 1
            scale_factor = plane.dimensions[0]
            for v in plane.data.vertices:
                #scale_factor = v.co[0]
                v.co /= scale_factor
            plane.parent = cam
            plane.show_wire = True
            plane.matrix_world = cam.matrix_world
            plane.lock_location = (True,)*3
            plane.lock_rotation = (True,)*3
            plane.lock_scale =    (True,)*3

            # Custom properties
            prop = rna_idprop_ui_prop_get(plane, "distance", create=True)
            plane["distance"] = self.distance - i*0.1  # Multiple planes spacing
            prop["soft_min"] = 0
            prop["soft_max"] = 10000
            prop["min"] = 0
            prop["max"] = 1000
            prop["default"] = 100

            if self.passepartout == '16_9':
                passepartout = 100 * (1 + 400 / 2400)
            elif self.passepartout == '16_10':
                passepartout = 100 * (1 + 400 / 2560)
            else:
                passepartout = 100.0

            prop = rna_idprop_ui_prop_get(plane, "passepartout", create=True)
            plane["passepartout"] = passepartout
            prop["soft_min"] = 0
            prop["soft_max"] = 1000
            prop["min"] = 0
            prop["max"] = 1000

            # DRIVERS
            ## DISTANCE ##
            driver = plane.driver_add('location', 2)

            # driver type
            driver.driver.type = 'SCRIPTED'

            # enable Debug Info
            driver.driver.show_debug_info = True

            # Variable
            var = driver.driver.variables.new()
            var.name = "distance"
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
                var.name = "distance"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = plane
                var.targets[0].data_path = '["distance"]'

                # Variable FOV
                var = driver.driver.variables.new()
                var.name = "FOV"
                var.type = 'SINGLE_PROP'
                var.targets[0].id_type = "OBJECT"
                var.targets[0].id = cam
                var.targets[0].data_path = 'data.angle'

                # Variable passepartout
                var = driver.driver.variables.new()
                var.name = "passepartout"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = plane
                var.targets[0].data_path = '["passepartout"]'

                # Expression
                driver.driver.expression = \
                    "tan(FOV/2) * distance*2 * passepartout/100.0"

        return {'FINISHED'}

    def execute(self, context):
        return self.build_camera_plane(context)
        #return {'FINISHED'}

#
#    Registration
#    Makes it possible to access the script from the Add > Mesh menu
#


def menu_func(self, context):
    self.layout.operator(
        "camera.camera_plane_build",
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

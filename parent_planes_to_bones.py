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
    "name": "Parent planes to bones",
    "author": "Les Fees Speciales",
    "version": (1, 0),
    "blender": (2, 76, 0),
    "location": "View3D > Tool > Parent planes to bones",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Rigging",
    }

import bpy
import re
from bpy.types import Operator

#obj = bpy.context.object

#planes = bpy.context.selected_objects
#planes.remove(obj)

def strip_numbers(name):
    """ Returns the name with trailing numbers stripped from it.
    """
    # regexp = re.compile("\.[0-9]+$")
    matches = re.findall("\.[0-9]+$", name)
    if matches:
        return name[:-len(matches[-1])]
    else:
        return name

SUFFIX_HIERARCHY = {
    ".L": "_gauche",
    ".R": "_droit"
}

def parent_planes_to_bones(self, context):
    obj = context.object
    initial_position = obj.data.pose_position
    obj.data.pose_position = 'REST'
    context.scene.update()
    for b in obj.data.bones:
        if b.use_deform:
#            print(b.name[4:])
            bone_name = b.name
            if bone_name[:4] == 'DEF-':
                bone_name = bone_name[4:]
            if bone_name[-2:] in ['.L', '.R']:
                obj_name, suffix = bone_name[:-2].replace(' ', '_'), bone_name[-2:]
                # Check for object existing
                if obj_name + suffix in bpy.data.objects:
                    obj_name += suffix
                    new_name = obj_name
                elif obj_name + SUFFIX_HIERARCHY[suffix] in bpy.data.objects:
                    obj_name += SUFFIX_HIERARCHY[suffix]
                    new_name = obj_name
                elif obj_name in bpy.data.objects:
                    new_name = obj_name + suffix
                else:
                    self.report({"WARNING"}, "Could not find object %s (%s)" % (obj_name, suffix))
                    continue
                
                p = bpy.data.objects[obj_name]
                
                # Check that object is not already parented
                if bone_name in context.scene.objects and (context.scene.objects[bone_name].parent == obj and context.scene.objects[bone_name].parent_bone == b.name):
                    self.report({"WARNING"}, "Object %s already child of bone %s" % (obj_name, b.name))
                    continue
                
                mat = p.matrix_world.copy()
                if new_name in bpy.context.scene.objects:
                    bpy.context.scene.objects.unlink(bpy.data.objects[new_name])
                if obj_name in bpy.context.scene.objects:
                    bpy.context.scene.objects.unlink(bpy.data.objects[obj_name])
                p = bpy.data.objects.new(new_name, p.data)
                bpy.context.scene.objects.link(p)
            else:
                if not bone_name.replace(' ', '_') in bpy.data.objects:
                    self.report({"WARNING"}, "Could not find object %s" % bone_name)
                    continue
                p = bpy.data.objects[bone_name.replace(' ', '_')]
                mat = p.matrix_world.copy()

            p.parent = obj
            p.parent_type = 'BONE'
            p.parent_bone = b.name
            p.matrix_world = mat
            p.hide_select = True

            p.name = strip_numbers(p.name)
                
#                print("Could not connect", s.name)
    obj.data.pose_position = initial_position

def unparent_planes_from_bones(self, context):
    obj = context.object
    initial_position = obj.data.pose_position
    obj.data.pose_position = 'REST'
    context.scene.update()

    for child in obj.children:
        mat = child.matrix_world.copy()
        child.parent = None
        child.matrix_world = mat

    obj.data.pose_position = initial_position

    obj.hide_select = False


class OBJECT_OT_parent_planes_to_bones(Operator):
    """Parent planes to bones"""
    bl_idname = "rigging.parent_planes_to_bones"
    bl_label = "Parent planes to bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.object and context.object.type == 'ARMATURE'
    
    def execute(self, context):
        parent_planes_to_bones(self, context)

        return {'FINISHED'}


class OBJECT_OT_unparent_planes_from_bones(Operator):
    """Parent planes to bones"""
    bl_idname = "rigging.unparent_planes_from_bones"
    bl_label = "Unparent planes from bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.object and context.object.type == 'ARMATURE'
    
    def execute(self, context):
        unparent_planes_from_bones(self, context)

        return {'FINISHED'}


class VIEW3D_PT_parent_planes_to_bones(bpy.types.Panel):
    bl_label = "Parent planes to bones"
    bl_category = 'Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(self, context):
        return context.object and context.object.type == 'ARMATURE'

    def draw(self, context):
        obj = context.active_object
        col = self.layout.column(align=True)
        col.active = obj is not None
        col.operator("rigging.parent_planes_to_bones")
        col.operator("rigging.unparent_planes_from_bones")

def register():
    bpy.utils.register_class(OBJECT_OT_parent_planes_to_bones)
    bpy.utils.register_class(OBJECT_OT_unparent_planes_from_bones)
    bpy.utils.register_class(VIEW3D_PT_parent_planes_to_bones)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_parent_planes_to_bones)
    bpy.utils.unregister_class(OBJECT_OT_unparent_planes_from_bones)
    bpy.utils.unregister_class(VIEW3D_PT_parent_planes_to_bones)


if __name__ == "__main__":
    register()

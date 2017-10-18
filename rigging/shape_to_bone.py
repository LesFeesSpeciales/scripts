# Copyright (C) 2017 Les Fees Speciales
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
    "name": "Shape To Bone",
    "author": "Les fees speciales",
    "version": (0, 1, 2),
    "blender": (2, 75, 0),
    "location": "View 3D > Tools",
    "description": "Use selected object as the shape for active bone.",
    "warning": "",
    "wiki_url": "",
    "category": "Rigging",
}

import bpy
from mathutils import Matrix

def main(context):
    selected = context.selected_objects[:]
    selected.remove(context.object)
    obj = selected[0]
    pbone = context.active_pose_bone

    mesh_name = 'WGT-' + pbone.name

    if mesh_name in context.scene.objects:
        context.scene.objects.unlink(context.scene.objects[mesh_name])
        bpy.data.objects[mesh_name].user_clear()

    mesh_copy = obj.to_mesh(context.scene, True, 'PREVIEW')
    mesh_copy.name = mesh_name
    obj_copy = bpy.data.objects.new(mesh_name, mesh_copy)
    obj_copy.name = mesh_name
    context.scene.objects.link(obj_copy)

    obj_copy.layers = [False if i != 19 else True for i in range(20)]

    b_length = pbone.bone.length

    pbone.custom_shape = obj_copy
    pbone.bone.show_wire = True

    for v in obj_copy.data.vertices:
        v.co = (context.object.matrix_world * pbone.matrix * b_length).inverted() * obj.matrix_world * v.co


class ShapeToBone(bpy.types.Operator):
    """Reposition selected mesh so that the active bone takes the mesh as custom shape.
    You need to be in pose mode with a mesh object selected."""
    bl_idname = "pose.shape_to_bone"
    bl_label = "Shape To Bone"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 1 and context.active_pose_bone is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}

def edit_bone_shape(context):
    """Function for bone shape editing"""
    pbone = context.active_pose_bone
    shape_object = pbone.custom_shape
    shape_layers = shape_object.layers

    if not shape_object.name in context.scene.objects:
        context.scene.objects.link(shape_object)

    shape_object.layers = context.object.layers

    shape_object.matrix_world = (pbone.bone.length) * context.object.matrix_world * pbone.matrix
    shape_object.location = context.object.matrix_world * pbone.head
    shape_object.hide = False

    context.object.select = False
    context.scene.objects.active = shape_object
    bpy.ops.object.mode_set(mode='EDIT')


class EditBoneShape(bpy.types.Operator):
    """Add mesh object at same postion as current bone. You can then edit it and reapply it."""
    bl_idname = "pose.edit_bone_shape"
    bl_label = "Edit Bone Shape"

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.active_pose_bone and context.active_pose_bone.custom_shape
#        return len(context.selected_objects) > 1 and context.active_pose_bone is not None

    def execute(self, context):
        edit_bone_shape(context)
        return {'FINISHED'}

class ShapeToBonePanel(bpy.types.Panel):
    """Shape To Bone"""
    bl_label = "Shape To Bone"
    bl_idname = "SCENE_PT_shape_bone"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'posemode'
    bl_category = 'Tools'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        if len(context.selected_objects) != 2:
            col.label('Please select one mesh object,', icon='ERROR')
            col.label('then the bone in Pose Mode')
        col.operator("pose.shape_to_bone")
        col.operator("pose.edit_bone_shape")

def register():
    bpy.utils.register_class(ShapeToBone)
    bpy.utils.register_class(EditBoneShape)
    bpy.utils.register_class(ShapeToBonePanel)


def unregister():
    bpy.utils.unregister_class(EditBoneShape)
    bpy.utils.unregister_class(ShapeToBone)
    bpy.utils.unregister_class(ShapeToBonePanel)


if __name__ == "__main__":
    register()

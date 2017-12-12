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
    "name": "Automatic Weight Selected",
    "description": "Create automatic weights only for selected bones.",
    "author": "Les Fées Spéciales",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "View3D",
    "wiki_url": "",
    "category": "Paint"}

import bpy


def store_def_settings(self, context):
    """Store DEF setting"""
    for pb in self.arm_obj.pose.bones:
        self.def_bones[pb.name] = pb.bone.use_deform
        if pb not in context.selected_pose_bones:
            pb.bone.use_deform = False
        else:
            if not pb.bone.use_deform:
                self.report({'INFO'}, 'Bone %s is non-deforming.' % pb.name)


def restore_def_settings(self):
    """Restore DEF setting"""
    for pb in self.arm_obj.pose.bones:
        pb.bone.use_deform = self.def_bones[pb.name]


class AutomaticWeightSelected(bpy.types.Operator):
    bl_idname = "paint.automatic_weight_selected"
    bl_label = "Automatic Weight Selected"
    bl_description = "Add weight only to selected bones"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'PAINT_WEIGHT'
                and len(context.selected_objects) == 2)

    def execute(self, context):
        self.def_bones = {}

        mesh_obj = context.object
        # Get armature object
        arm_obj = set(context.selected_objects)
        arm_obj.discard(mesh_obj)
        self.arm_obj = tuple(arm_obj)[0]

        store_def_settings(self, context)
        mesh_obj.vertex_groups.clear()
        # Automatic weight
        bpy.ops.paint.weight_from_bones(type='AUTOMATIC')
        restore_def_settings(self)
        return {"FINISHED"}


class ArmatureDeformObject(bpy.types.Operator):
    bl_idname = "pose.parent"
    bl_label = "Armature Deform To Selected"
    bl_description = "Add Armature Deform, only to selected bones"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return (context.mode in {'OBJECT', 'POSE'}
                and len(context.selected_objects) == 2)

    def execute(self, context):
        self.def_bones = {}

        self.arm_obj = context.object
        # Get armature object
        mesh_obj = set(context.selected_objects)
        mesh_obj.discard(self.arm_obj)
        mesh_obj = tuple(mesh_obj)[0]

        store_def_settings(self, context)
        mesh_obj.vertex_groups.clear()
        mat = mesh_obj.matrix_world.copy()
        # Automatic weight
        bpy.ops.object.parent_set(type='ARMATURE_AUTO',
                                  xmirror=False,
                                  keep_transform=False)
        mesh_obj.matrix_world = mat
        restore_def_settings(self)
        return {"FINISHED"}


def weight_tools_panel(self, context):
    layout = self.layout
    layout.operator("paint.automatic_weight_selected")


def relations_panel(self, context):
    layout = self.layout
    layout.operator("paint.automatic_weight_selected")


class VIEW3D_PT_posemode_relations(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Relations"
    bl_context = "posemode"
    bl_label = "Relations"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)

        col.label(text="Parent:")
        col.operator("pose.parent")


def register():
    bpy.utils.register_class(AutomaticWeightSelected)
    bpy.utils.register_class(ArmatureDeformObject)
    bpy.utils.register_class(VIEW3D_PT_posemode_relations)
    bpy.types.VIEW3D_PT_tools_weightpaint.append(weight_tools_panel)
    bpy.types.VIEW3D_PT_tools_relations.append(relations_panel)


def unregister():
    bpy.utils.unregister_class(AutomaticWeightSelected)
    bpy.utils.unregister_class(ArmatureDeformObject)
    bpy.utils.unregister_class(VIEW3D_PT_posemode_relations)
    bpy.types.VIEW3D_PT_tools_weightpaint.remove(weight_tools_panel)
    bpy.types.VIEW3D_PT_tools_relations.remove(relations_panel)


if __name__ == "__main__":
    register()

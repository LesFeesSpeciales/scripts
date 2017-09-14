# Copyright Les Fees Speciales 2017
#
# voeu@les-fees-speciales.coop
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "Material Tuning",
    "author": "Les Fees Speciales",
    "version": (0, 3),
    "blender": (2, 77, 0),
    "location": "View3D > Tools > LFS",
    "description": "Change some material properties. Useful for recoloring textures on multiple objects.",
    "category": "Material"}

import bpy
import os

NODE_SETTINGS = [
    {
        "name": "Gamma",
        "type": "ShaderNodeGamma",
        "input_socket": "Color",
        "inputs": ["Gamma"],
        "default_values": {
            "Gamma": 1.0,
        },
    }, {
        "name": "Hue Saturation Value",
        "type": "ShaderNodeHueSaturation",
        "input_socket": "Color",
        "inputs": [
            "Hue",
            "Saturation",
            "Value"
        ],
        "default_values": {
            "Hue": 0.5,
            "Saturation": 1.0,
            "Value": 1.0,
            },
    }, {
        "name": "RGB Curves",
        "type": "ShaderNodeRGBCurve",
        "input_socket": "Color",
        "inputs": [],
    }, {
        "name": "Mix",
        "type": "ShaderNodeMixRGB",
        "input_socket": "Color1",
        "inputs": ["Color2", "Fac"],
        "settings": {
            "blend_type": "HUE",
        },
        "default_values": {
            "Color2": (0.5, 0.5, 0.5, 1.0),
            "Fac": 1.0,
        },
    }
]


def setup_node_tree(obj):
    """If object is not properly setup, create node tree."""
    mat = obj.active_material
    mat.use_nodes = True

    nodes = mat.node_tree.nodes

    input_node = nodes["Material"]
    input_node.material = mat
    output_node = nodes["Output"]
    output_node.location.x = (len(NODE_SETTINGS)+1) * 300
    mat.node_tree.links.new(input_node.outputs["Alpha"],
                            output_node.inputs["Alpha"], )
    previous_node = input_node

    for i, node_s in enumerate(NODE_SETTINGS):
        if not node_s["name"] in nodes:
            node = nodes.new(node_s["type"])
            node.location.x = ((input_node.location.x + output_node.location.x)
                               * (i+1) / (len(NODE_SETTINGS)+1))
            node.location.y = (input_node.location.y
                               + output_node.location.y) / 2
            input_socket = node_s["input_socket"]
            mat.node_tree.links.new(previous_node.outputs["Color"],
                                    node.inputs[input_socket], )
            previous_node = node
        if "settings" in node_s:
            for setting, value in node_s["settings"].items():
                setattr(node, setting, value)
        if "default_values" in node_s:
            for input_socket, value in node_s["default_values"].items():
                node.inputs[input_socket].default_value = value

    mat.node_tree.links.new(node.outputs["Color"],
                            output_node.inputs["Color"],)


def copy_to_selected(obj, selected_objs):
    """Copy tuning settings from active to selected objects"""
    mat = obj.active_material
    for so in selected_objs:
        so_mat = so.active_material
        if so_mat is not None:
            if not so_mat.use_nodes:
                setup_node_tree(so)
            for node_s in NODE_SETTINGS:
                node = mat.node_tree.nodes[node_s["name"]]
                so_node = so_mat.node_tree.nodes[node_s["name"]]
                for prop in node_s["inputs"]:
                    so_node.inputs[prop].default_value = \
                        node.inputs[prop].default_value
                # Hack for curves
                if node.type == "CURVE_RGB":
                    for prop in ["black_level", "clip_max_x", "clip_max_y",
                                 "clip_min_x", "clip_min_y", "white_level",
                                 "use_clip"]:
                        setattr(so_node.mapping,
                                prop,
                                getattr(node.mapping, prop))
                    so_node.mapping.initialize()
                    for so_curve, curve in zip(
                            so_node.mapping.curves, node.mapping.curves):
                        so_curve.extend = curve.extend
                        # Match number of points
                        while len(so_curve.points) < len(curve.points):
                            so_curve.points.new(0, 0)
                        while len(so_curve.points) > len(curve.points):
                            so_curve.points.remove(so_curve.points[0])
                        # Copy points
                        for so_point, point in zip(so_curve.points,
                                                   curve.points):
                            so_point.handle_type = point.handle_type
                            so_point.location = point.location
                            so_point.select = True
                    so_node.mapping.update()


class SetupNodeTree(bpy.types.Operator):
    """Create node tree for material tuning"""
    bl_idname = "lfs.tuning_setup_node_tree"
    bl_label = "Setup Node Tree"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        setup_node_tree(context.object)
        return {"FINISHED"}


class CopyTuningToSelected(bpy.types.Operator):
    """Copy node tree for material tuning"""
    bl_idname = "lfs.tuning_copy_to_selected"
    bl_label = "Copy To Selected"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        dest_objects = context.selected_objects
        copy_to_selected(context.object, dest_objects)
        return {"FINISHED"}


def bake_all_textures(self):
    bpy.context.scene.render.bake_type = 'FULL'
    bpy.context.scene.render.use_bake_to_vertex_color = False
    bpy.context.scene.render.use_bake_selected_to_active = False
    bpy.context.scene.render.use_bake_clear = True
    bpy.context.scene.render.bake_margin = 16

    scene_objects = {obj: obj.active_material
                     for obj in bpy.context.scene.objects
                     if obj.active_material}
    # scene_materials = [obj.mat for obj in scene_objects]
    for obj, mat in scene_objects.items():
        if (mat.use_nodes
                and 'Output' in mat.node_tree.nodes):  # vague test for BI mat
            object_texture = mat.active_texture
            if "asset_uuid" in obj:
                # find asset name
                for item in bpy.context.scene.imported_items:
                    if item.asset_uuid == obj["asset_uuid"]:
                        break
                texture_name = item.name + '_' + mat.name
            else:
                texture_name = obj.name + '_' + mat.name
            if object_texture is None:
                # object_texture = bpy.data.textures.new(texture_name, 'IMAGE')
                new_image = bpy.data.images.new(
                    texture_name, 1024, 1024, alpha=True)
            else:
                existing_image = object_texture.image
                new_image = bpy.data.images.new(
                    texture_name, existing_image.size[0],
                    existing_image.size[1], alpha=True)
            if obj.data.uv_textures.active is not None:
                for uv_face in obj.data.uv_textures.active.data:
                    uv_face.image = new_image
            else:
                self.report(
                    {"WARNING"},
                    "Could not bake object %s: no UV map" % obj.name)
                continue

            # bake
            for sel_obj in bpy.context.selected_objects:
                sel_obj.select = False
            hide = obj.hide
            hide_select = obj.hide_select
            hide_render = obj.hide
            # Fix for objects which have drivers on hide
            # TODO same with keyframes
            drivers = {}
            if obj.animation_data and obj.animation_data.drivers:
                for d_i, d in enumerate(obj.animation_data.drivers):
                    if d.data_path in ('hide', 'hide_select', 'hide_render'):
                        drivers[d_i] = d.mute
                        d.mute = True

            obj.hide = False
            obj.hide_select = False
            obj.hide_render = False
            obj.select = True
            bpy.context.scene.objects.active = obj

            print("Baking object %s..." % obj.name)
            bpy.ops.object.bake_image('EXEC_DEFAULT')

            bpy.ops.object.mode_set(mode='OBJECT')

            # Restore property states
            obj.hide = hide
            obj.hide_select = hide_select
            obj.hide_render = hide_render
            for d_i, d in drivers.items():
                obj.animation_data.drivers[d_i].mute = d

            new_image.file_format = 'PNG'
            new_image.filepath_raw = ('//textures/%s.png' % texture_name)
            os.makedirs(bpy.path.abspath('//textures/'), exist_ok=True)
            new_image.save()

            mat.use_nodes = False
            if object_texture is None:
                tex_slot = mat.texture_slots.add()
            else:
                tex_slot = mat.texture_slots[0]
            new_texture = bpy.data.textures.new(texture_name, 'IMAGE')
            new_texture.image = new_image
            tex_slot.texture = new_texture

    print("Done baking.")


class BakeAllTextures(bpy.types.Operator):
    """Bake all textures to directory"""
    bl_idname = "lfs.tuning_bake_all_textures"
    bl_label = "Bake All Textures"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return bpy.data.filepath

    def execute(self, context):
        bake_all_textures(self)
        return {"FINISHED"}


def reset_all():
    """Reset all fields to their default values"""
    nodes = bpy.context.object.active_material.node_tree.nodes
    for node_s in NODE_SETTINGS:
        node = nodes[node_s["name"]]
        if "default_values" in node_s:
            for input_socket, value in node_s["default_values"].items():
                node.inputs[input_socket].default_value = value
        # Hack for curves
        if node.type == "CURVE_RGB":
            print(node)
            node.mapping.use_clip = True
            node.mapping.clip_max_x = 1.0
            node.mapping.clip_max_y = 1.0
            node.mapping.clip_min_x = 0.0
            node.mapping.clip_min_y = 0.0

            for curve in node.mapping.curves:
                print(curve)
                while len(curve.points) > 2:
                    curve.points.remove(curve.points[1])
                    print(len(curve.points))
                curve.points[0].location = [0.0, 0.0]
                curve.points[0].handle_type = 'AUTO'
                curve.points[1].location = [1.0, 1.0]
                curve.points[1].handle_type = 'AUTO'
                curve.extend = 'EXTRAPOLATED'

            node.mapping.update()


class ResetAll(bpy.types.Operator):
    """Bake all textures to directory"""
    bl_idname = "lfs.tuning_reset_all"
    bl_label = "Reset All Parameters"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        reset_all()
        return {"FINISHED"}


class MaterialTuningPanel(bpy.types.Panel):
    bl_idname = "material_tuning_panel"
    bl_label = "Material Tuning"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        mat = context.material
        engine = context.scene.render.engine
        return mat and engine in {'BLENDER_RENDER', 'BLENDER_GAME'}

    def draw(self, context):
        layout = self.layout

        if context.material is not None:
            # col.label("Node Settings:")
            if (context.material.use_nodes
                    and 'Hue Saturation Value'
                    in context.material.node_tree.nodes):

                col = layout.column(align=True)
                col.operator('lfs.tuning_reset_all')
                col.separator()
                for node_s in NODE_SETTINGS:
                    col = layout.column(align=True)
                    node = context.material.node_tree.nodes[node_s["name"]]
                    for prop in node_s["inputs"]:
                        col.prop(node.inputs[prop], "default_value", text=prop)

                    col.context_pointer_set("node", node)

                    # Hack for curves
                    if node.type == "CURVE_RGB":
                        if hasattr(node, "draw_buttons_ext"):
                            node.draw_buttons_ext(context, col)
                        elif hasattr(node, "draw_buttons"):
                            node.draw_buttons(context, col)
                    col.separator()

                col = layout.column(align=True)
                col.separator()
                col.operator('lfs.tuning_copy_to_selected')
                # col = layout.column()
                # if not bpy.data.filepath:
                #     col.label(icon='ERROR', text='Please save file first')
                # col.operator('lfs.tuning_bake_all_textures')
            else:
                col = layout.column()
                col.operator('lfs.tuning_setup_node_tree')


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

#setup_node_tree(bpy.context.object)

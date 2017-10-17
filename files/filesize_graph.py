# Copyright (C) 2017 Les Fees Speciales
# voeu@les-fees-speciales.coop
#
# Created by Les Fees Speciales
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.


bl_info = {
    "name": "Filesize Graph",
    "description": "Les Fees Speciales",
    "author": "Les Fees Speciales",
    "version": (0, 0, 1),
    "blender": (2, 77, 0),
    "location": "View3D",
    "description": "Helps visualize file sizes in a folder, in graph form",
    "category": "Files"
}

import bpy
import os
import re

rexp = re.compile(r'([0-9]+)')


def visualize_size(name, basedir):

    frames = {}
    max_frame = 0
    max_size = 0

    for file in os.listdir(basedir):
        frame_number = int(rexp.findall(file)[-1])
        if int(frame_number) > max_frame:
            max_frame = frame_number

        size = os.path.getsize(os.path.join(basedir, file))

        frames[frame_number] = size
        if size > max_size:
            max_size = size

    for i in range(1, max_frame + 1):
        if not i in frames:
            frames[i] = -1

#    for frame, size in frames.items():
#        txt.write('{:03d}'.format(frame) + ' ' + str(size))
#        txt.write('\n')

    if not name in bpy.data.objects:
        curve = bpy.data.curves.new(name, 'CURVE')
        obj = bpy.data.objects.new(name, curve)
        bpy.context.scene.objects.link(obj)
    else:
        obj = bpy.data.objects[name]

    obj.data.splines.clear()
    spline = obj.data.splines.new('POLY')
    obj.data.dimensions = '3D'
    spline.points.add(len(frames)-1)
    for i, (frame, size) in enumerate(frames.items()):
#        print(frame, size)
        spline.points[i].co.x = frame
        spline.points[i].co.z = size / (max_size if size != -1.0 else 1) * 100


class FilesizeGraph(bpy.types.Operator):
    bl_idname = "lfs.filesize_graph"
    bl_label = "Filesize Graph"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        for g in context.scene.filesize_graphs:
            visualize_size(g.name, g.dirpath)
        return {"FINISHED"}


class FilesizeGraphAdd(bpy.types.Operator):
    bl_idname = "lfs.filesize_graph_add"
    bl_label = "Filesize Graph Add"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        context.scene.filesize_graphs.add()
        context.scene.filesize_graphs[-1].name = "Graph"
        return {"FINISHED"}


class FilesizeGraphRemove(bpy.types.Operator):
    bl_idname = "lfs.filesize_graph_remove"
    bl_label = "Filesize Graph Remove"
    bl_description = ""
    bl_options = {"REGISTER"}

    index = bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        context.scene.filesize_graphs.remove(self.index)
        return {"FINISHED"}


class FilesizeGraphPanel(bpy.types.Panel):
    bl_idname = "lfs.filesize_graph_panel"
    bl_label = "Filesize Graph"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Files"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column(align=True)
        for i, g in enumerate(context.scene.filesize_graphs):
            sub = col.row(align=True)
            split = sub.split(percentage=0.2, align=True)
            split.prop(g, "name", text="")
            split.prop(g, "dirpath", text="")
            sub.operator("lfs.filesize_graph_remove", icon='X', text="").index = i
        col = row.column()

        sub = col.column(align=True)
        sub.operator("lfs.filesize_graph_add", icon='ZOOMIN', text="")

        layout.operator('lfs.filesize_graph')


class Texture_Variations(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(default='')
    dirpath = bpy.props.StringProperty(default='', subtype='DIR_PATH')


def register():
    bpy.utils.register_class(Texture_Variations)
    bpy.types.Scene.filesize_graphs = bpy.props.CollectionProperty(
        name="Filesize Graphs", type=Texture_Variations)
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

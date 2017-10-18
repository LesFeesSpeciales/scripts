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
    "name": "Plane tesselation",
    "description": "Tesselate textured planes based on image. BI only. ",
    "author": "Les Fées Speciales",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "View3D",
    "warning": "Needs a custom version of triangle. See README for more info",
    "wiki_url": "https://github.com/LesFeesSpeciales/LFS-blender-scripts",
    "category": "Rigging" }


import numpy as np
from scipy import misc, spatial
from skimage import measure
import triangle

import bpy
import bmesh
from mathutils import Vector, Matrix

import os

def main(context):
    def is_polygon_clockwise(verts):
        '''Direction of a 2D polygon
        return: is_cw (bool)
        https://stackoverflow.com/a/1165943/4561348
        '''
        total = 0
        for i in range(len(verts)-1):
            v1, v2 = verts[i], verts[i+1]
            total += (v2[0] - v1[0]) * (v2[1] + v1[1])
        total += (v2[0] - verts[0][0]) * (v2[1] + verts[0][1])

        return (total <= 0)

    def get_contours(contours, tolerance=0.0005):
        '''Concatenate a list of contours and approximate it if possible'''
        global_contour = {'vertices': [],
                          'segments': [],
                          'holes':    [],
                          }

        previous_region_index = 0

        for c in contours:
            c = c.copy()
            c -= padding # Remove padding
            for axis in range(2):
                c[..., axis] *= (shape[axis] + padding*2) / shape[axis] # Scale back to pre-padding on each axis
            c /= np.array(padded_array.shape)  # Divide to get a 1x1 square.
            c[..., 1] *= shape[1] / shape[0]   # Get aspect ratio back

            # Simplify polygon
            c = measure.approximate_polygon(c, tolerance)

            global_contour['vertices'].extend(c)

            for pt_i in range(len(c)-1):
                global_contour['segments'].append(
                    [pt_i + previous_region_index, pt_i + previous_region_index + 1]
                )
            global_contour['segments'].append([len(c) - 1 + previous_region_index, previous_region_index])

            previous_region_index += len(c)

            # Add hole if polygon ccw
            if is_polygon_clockwise(c):
                c_ar = np.array(c)
                global_contour['holes'].append([c_ar[..., 0].mean(), c_ar[..., 1].mean()])
                # TODO: find point inside concave polygons

        if not global_contour['holes']:
            del global_contour['holes']
        return global_contour

    def get_plane_matrix(ob, poly_index=0):
        """Get object's polygon local matrix from uvs.
        This will only work if uvs occupy all space, to get bounds"""
        for p_i, p in enumerate(ob.data.uv_layers.active.data):
            if p.uv == Vector((0, 0)):
                p0 = p_i
            elif p.uv == Vector((1, 0)):
                px = p_i
            elif p.uv == Vector((0, 1)):
                py = p_i

        p0 = ob.data.vertices[ob.data.loops[p0].vertex_index].co
        px = ob.data.vertices[ob.data.loops[px].vertex_index].co - p0
        py = ob.data.vertices[ob.data.loops[py].vertex_index].co - p0

        rot_mat = Matrix((px, py, px.cross(py))).transposed().to_4x4()
        trans_mat = Matrix.Translation(p0)
        mat = trans_mat * rot_mat

        print("mat =", repr(ob.matrix_world * mat))

        return mat

    for obj_orig in context.selected_objects:

        print(obj_orig.name)

        if obj_orig.type != 'MESH':
            continue

        b_tex = obj_orig.active_material.texture_slots[0].texture
        b_img = b_tex.image

        fimg = np.array(b_img.pixels).reshape([b_img.size[1], b_img.size[0], 4])
        fimg = np.flip(fimg, 0) # flip along y axis

        gimg = fimg[..., 3]

        # Threshold for half transparency
        thresh_mask = gimg[...] < 0.01
        gimg[:] = 1.0
        gimg[thresh_mask] = 0.0

        # Pad array
        shape = gimg.shape
        padding = 2
        padded_shape = (shape[0] + padding*2, shape[1] + padding*2)
        padded_array = np.zeros(padded_shape)
        padded_array[padding:shape[0]+padding, padding:shape[1]+padding] = gimg

        contours = measure.find_contours(padded_array, 0.2)

        global_contour = get_contours(contours)
        res = triangle.triangulate(global_contour, opts='piqa0.0005')
        if not 'segments' in res:
            # Retry when triangle cannot generate tesselation
            # Why does this happen?
            global_contour = get_contours(contours, 0.0001)
            res = triangle.triangulate(global_contour, opts='piqa0.0005')

        mesh = bpy.data.meshes.new(obj_orig.data.name)
        mesh.materials.append(obj_orig.active_material)

        bm = bmesh.new()

        for v_co in res['vertices']:
            x = v_co[1] * shape[0] / shape[1]
            y = (1-v_co[0])
            # Create vertex
            bm.verts.new([x, y, 0])

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        for s in res['segments']:
            bm.edges.new((bm.verts[s[0]], bm.verts[s[1]]))

        for face in res['triangles']:
            bm.faces.new([bm.verts[i] for i in face])

        edges = []
        for edge in bm.edges:
            edge.select = True
            edges.append(edge)

        bmesh.ops.remove_doubles(bm, verts=bm.verts)

        bm.verts.index_update()

        # UVs
        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.layers.tex.verify()
        for f in bm.faces:
            for l in f.loops:
                luv = l[uv_layer]
                luv.uv = l.vert.co.xy

        # Transform verts to mesh coordinates
        mat = get_plane_matrix(obj_orig)
        for v in bm.verts:
            v.co = mat * v.co

        bm.to_mesh(mesh)
        mesh.update()

        obj_orig.data = mesh
        mesh.name = obj_orig.data.name

class CutPlanes(bpy.types.Operator):
    bl_idname = "object.cut_planes"
    bl_label = "Cut Planes"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        main(context)
        return {"FINISHED"}

class Tesselation(bpy.types.Panel):
    bl_idname = "tesselation"
    bl_label = "Tesselation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.cut_planes")

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

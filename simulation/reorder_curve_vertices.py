# Copyright (C) 2015 Les Fees Speciales
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


import bpy
import time
obj = bpy.context.object

verts = []
edges = []
for v in obj.data.vertices:
    if v.select:
        verts.append(v)
        break

print(verts[-1].index)
while len(verts) != len(obj.data.vertices):
    print(2, len(verts), len(obj.data.vertices))

    for e in obj.data.edges:
        if verts[-1].index in e.vertices and e not in edges:
            current_edge = e
            if current_edge.vertices[0] == verts[-1]:
                v_index = current_edge.vertices[0]
            else:
                v_index = current_edge.vertices[1]

            verts.append(obj.data.vertices[v_index])

            edges.append(e)
            break
print(3)
edges = [[i, i+1] for i in range(len(verts)-1)]

verts = [v.co for v in verts]

##CREATE NEW MESH
name = obj.data.name
new_mesh = bpy.data.meshes.new(obj.data.name + '_Reordered')
#new_obj = bpy.data.objects.new(obj.name + '_Reordered', new_mesh)
#bpy.context.scene.objects.link(new_obj)
new_mesh.from_pydata(verts, edges, [])
print('lhj')
obj.data = new_mesh
obj.data.name = name

print('DONE')

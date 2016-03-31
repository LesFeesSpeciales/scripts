# Copyright Les Fees Speciales 2015
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

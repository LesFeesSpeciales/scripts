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
from mathutils import Vector, noise
from time import time

'''
Template for a particle system
Includes efficient caching using duplication
'''

class Particle:
    def __init__(self, location=Vector()):
        self.location = location.copy()
        self.velocity = noise.random_unit_vector()

        self.active = True
        
        
class Particle_system:
    
    def __init__(self):
        self.frame = 0
        
        self.particles = []
        
        bpy.ops.mesh.primitive_ico_sphere_add(location=(0,0,0))
        self.instance_obj = bpy.data.objects[bpy.context.scene.particle_simulation_settings.instance]
        self.instance_mesh = self.instance_obj.data
        
        
    def add_particle(self, particles_number):
        '''Add a new particle to the system'''
        for p in range(particles_number):
            self.particles.append(Particle())

    def kill_particle(self, part):
        self.particles.remove(part)
        
    
    def step(self):
        '''Simulate next frame'''
        self.frame += 1
        
        for part in self.particles:
            if part.active:
                
                previous_velocity = part.velocity.copy()

                # SIMULATE STUFF HERE


                # SET NEW LOCATION
                part.location += part.velocity



        self.create_frame(self.frame)
    
    def create_frame(self, frame):
        '''
        For each frame:
            - create a new instance of the object to duplicate (eg. a sphere)
            - get a list of vertices from particles' positions
            - create a new generator objects, use the vertex list to generate mesh
                - this object will be used for duplication
            - parent the object to duplicate to the generator object
            - animate the visibility of both objects
            '''
        
        instance_obj_frame = bpy.data.objects.new('instance_{:05}'.format(frame), self.instance_mesh)
        bpy.context.scene.objects.link(instance_obj_frame)
        
    
        vertices = ((p.location, p.velocity) for p in self.particles)
        generator_mesh = bpy.data.meshes.new('generator_{:05}'.format(frame))
        
        for v in vertices:
            generator_mesh.vertices.add(1)
            generator_mesh.vertices[-1].co = v[0]
            generator_mesh.vertices[-1].normal = v[1]
        
        generator_obj = bpy.data.objects.new('generator_{:05}'.format(frame), generator_mesh)
        bpy.context.scene.objects.link(generator_obj)
        
        instance_obj_frame.parent = generator_obj
        generator_obj.dupli_type = "VERTS"
        generator_obj.use_dupli_vertices_rotation = True
        
        #anim
        generator_obj.keyframe_insert('hide', frame=frame)
        generator_obj.keyframe_insert('hide_render', frame=frame)
        generator_obj.hide = True
        generator_obj.hide_render = True
        generator_obj.keyframe_insert('hide', frame=frame+1)
        generator_obj.keyframe_insert('hide_render', frame=frame+1)
        generator_obj.keyframe_insert('hide', frame=frame-1)
        generator_obj.keyframe_insert('hide_render', frame=frame-1)
        

# Operator and panel for ease of use

def main(context):
    
    #Remove objects from previous sim
    for o in bpy.data.objects:
        if o.name.startswith('generator') or o.name.startswith('Ico') or o.name.startswith('instance'):
            o.user_clear()
            bpy.context.scene.objects.unlink(o)
            bpy.data.objects.remove(o)
    
    number = bpy.context.scene.particle_simulation_settings.number
    start_frame = bpy.context.scene.particle_simulation_settings.start_frame
    end_frame = bpy.context.scene.particle_simulation_settings.end_frame
    scale = bpy.context.scene.particle_simulation_settings.scale
    a_ps = Particle_system()
    a_ps.add_particle(number)
    
    print('\n---')
    start = time()
    for f in range(start_frame, end_frame+1):
#        a_ps.add_particles(1)
        if f%10 == 0:
            print('frame: {:04}'.format(f))
        a_ps.step()
    print('Simulated in {:05.5f} seconds'.format(time() - start))


class SimulationPanel(bpy.types.Panel):
    """"""
    bl_category = "Tools"
    bl_label = "Simulation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
#        layout.label(text=" Simple Row:")

        column = layout.column(align=True)
        column.prop(scene.particle_simulation_settings, "number")
        column.prop(scene.particle_simulation_settings, "start_frame")
        column.prop(scene.particle_simulation_settings, "end_frame")
        column.prop(scene.particle_simulation_settings, "scale")
        column = layout.column(align=True)
        column.prop_search(scene.particle_simulation_settings, "instance", scene, "objects")
        
        layout.separator()
        
        column = layout.row()
        column.operator("simulation.generate")


class ParticlesOperator(bpy.types.Operator):
    """Generate particle simulation"""
    bl_idname = "simulation.generate"
    bl_label = "Particle Simulation"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        main(context)
        return {'FINISHED'}

def register():
    class ParticleSimulationSettings(bpy.types.PropertyGroup):
        number = bpy.props.IntProperty(name='Number Of Particles', description='Number Of Particles', min=1, soft_max=1000, default = 100)
        start_frame = bpy.props.IntProperty(name='Start Frame', description='Start Frame', min=0, soft_max=1000, default = 1)
        end_frame = bpy.props.IntProperty(name='End Frame', description='End Frame', min=1, soft_max=1000, default = 100)
        scale = bpy.props.FloatProperty(name='Particle Scale', description='Particle Scale', min=0.0, soft_max=1000.0, default = 1.0)
        instance = bpy.props.StringProperty(name='Instance Object', description='Instance Object', default='')
        
    bpy.utils.register_class(ParticleSimulationSettings)
    bpy.types.Scene.particle_simulation_settings = bpy.props.PointerProperty(type=ParticleSimulationSettings)
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
#
#    # test call
#    bpy.ops.object.simple_operator()

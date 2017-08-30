# Copyright Les Fees Speciales 2015
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

import bpy
from mathutils import Vector, noise
from mathutils.kdtree import KDTree
from random import random, randint, gauss, seed
from math import fabs
from time import time

'''
Template for a particle system
Includes efficient caching using duplication
'''

class Particle:


    def __init__(self, index, scale, location=Vector()):
        targ_vel = 0.005 * scale
        self.MAX_VEL = gauss(targ_vel, targ_vel / 10)

        self.location = location.copy()
        self.velocity = noise.random_unit_vector() * self.MAX_VEL
        self.guide_index = index

        self.noise_seed = noise.random_unit_vector()

        self.active = True

        self.direction = randint(0,1)*2-1

#        if index > guide_len/2:
#            self.direction = -1
#        else:
#            self.direction = 1


        self.behaviour = 0.6 # 1 = guide ; 0 = turbulence

class Particle_system:


    def __init__(self, guide, ground, scale):

        self.GUIDE_STRENGTH = 1.0 * scale

        self.TURBULENCE_FREQUENCY = 10 * scale
        self.TURBULENCE_STRENGTH = 1.0 * scale

        self.AVOID_THRESHOLD = 0.01 * scale
        self.AVOID_STRENGTH = 0.2 * scale

        self.frame = 0

        self.particles = []
        self.guide = guide
#        self.vertex_distance = (self.guide.data.vertices[0].co - self.guide.data.vertices[1].co).length_squared

        self.guide_tree = KDTree(len(self.guide.data.vertices))
        for v in self.guide.data.vertices:
            self.guide_tree.insert(v.co, v.index)
        self.guide_tree.balance()

        self.ground = ground
        self.scale = scale

#        bpy.ops.mesh.primitive_ico_sphere_add(location=(0,0,0), size=0.01)
#        self.instance_obj = bpy.context.object
#        self.instance_obj = bpy.data.objects['Fleche']
        self.instance_obj = bpy.data.objects[bpy.context.scene.ant_instance]
        self.instance_mesh = self.instance_obj.data
#        self.instance_mesh.materials.append(bpy.data.materials['noir'])


    def add_particles(self, particles_number):
        '''Add a new particle to the system'''
        for p in range(particles_number):
            ind = randint(1, len(self.guide.data.vertices)-2)
            self.particles.append(Particle(ind, self.scale, self.guide.data.vertices[ind].co))

    def kill_particle(self, part):
        self.particles.remove(part)

    def create_tree(self):
        self.parts_tree = KDTree(len(self.particles))
        for i, p in enumerate(self.particles):
            self.parts_tree.insert(p.location, i)
        self.parts_tree.balance()


    def step(self):
        '''Simulate next frame'''
        self.frame += 1
        self.create_tree()

        for part in self.particles:
            if part.active:

                previous_velocity = part.velocity.copy()

                #guide vector
                guide_vector = self.guide.data.vertices[part.guide_index].co - part.location
                guide_vector = guide_vector.normalized() * self.GUIDE_STRENGTH

                #turbulence vector
                turbulence = noise.turbulence_vector(part.noise_seed+part.location, 2, False, 1, self.TURBULENCE_STRENGTH, self.TURBULENCE_FREQUENCY)
#                part.noise_seed += turbulence / 50
#                if part.velocity.length_squared < 0.0001:
#                    part.noise_seed = noise.random_unit_vector()
                part.noise_seed.z += 0.01

                #boid-like vector
                too_close = self.parts_tree.find_range(part.location, self.AVOID_THRESHOLD)
                avoid_vector = Vector()
                for p in too_close:

                    other_vec = part.location - p[0]
                    if other_vec.length_squared < 0.0001:
                        continue
                    other_vec /= other_vec.length
                    avoid_vector += other_vec

#                avoid_vector.normalize()
#                avoid_vector -= part.velocity
                avoid_vector *= self.AVOID_STRENGTH

                #velocity change

                part.velocity += avoid_vector

                part.velocity += turbulence * (1.0-part.behaviour)
                part.velocity += guide_vector * part.behaviour

                #limit velocity (drag and shit)
                if part.velocity.length > part.MAX_VEL:
                    part.velocity.length = part.MAX_VEL

                # limit rotation
                rotation_scalar = previous_velocity.dot(part.velocity) * 0.5 + 0.5 # normalized 0-1
#                rotation_scalar **= 3
                if rotation_scalar > 0.1:
                    rotation_scalar = 0.1
#                rotation_scalar = 0
                part.velocity *= (rotation_scalar)
                part.velocity += previous_velocity * (1-rotation_scalar)

                # put that shit on the ground
                closest = self.ground.closest_point_on_mesh(part.location)
                part.location = closest[0]
                # velocity parallel to the ground
                vel_norm = part.velocity.length
                inter = part.velocity.cross(closest[1])
                part.velocity = closest[1].cross(inter)
                part.velocity.length = vel_norm
#                print(part.velocity)

                # SET NEW LOCATION
                part.location += part.velocity

                # behaviour change
                part.behaviour += random()*0.1-0.05
                if part.behaviour < 0.8:
                    part.behaviour = 0.8
                if part.behaviour > 0.9:
                    part.behaviour = 0.9

#                # set goal to next vertex if close enough
                pt, ind, dist = self.guide_tree.find(part.location)
                if fabs(ind - part.guide_index) < 2:
                    part.guide_index += part.direction
#                if self.frame % 20 == 0:
#                    part.guide_index += part.direction

#                if next_point_distance.length_squared < self.vertex_distance:
#                    part.guide_index += 1

                # switch direction if end reached
                if part.guide_index >= len(self.guide.data.vertices)-1 or part.guide_index == 1:
#                    part.active = False
#                    self.kill_particle(part)
                    part.direction = -part.direction
                    part.guide_index += part.direction

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


        vertices = [(p.location, p.velocity) for p in self.particles]
        generator_mesh = bpy.data.meshes.new('generator_{:05}'.format(frame))

#        generator_mesh.from_pydata(vertices, [], [])

        ## Track to camera
#        cam = bpy.context.scene.camera
        for v in vertices:
            generator_mesh.vertices.add(1)
            generator_mesh.vertices[-1].co = v[0]
            generator_mesh.vertices[-1].normal = v[1]
#            generator_mesh.vertices[-1].normal = cam.location - v

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


def main(context):

    for o in bpy.data.objects:
        if o.name.startswith('generator') or o.name.startswith('Ico') or o.name.startswith('instance'):
            o.user_clear()
            bpy.context.scene.objects.unlink(o)
            bpy.data.objects.remove(o)

#    guide = bpy.data.objects['Chemin']
#    ground = bpy.data.objects['Sol']
    guide = bpy.data.objects[bpy.context.scene.ant_guide]
    ground = bpy.data.objects[bpy.context.scene.ant_ground]
    number_ants = bpy.context.scene.ant_number
    start_frame = bpy.context.scene.ant_start_frame
    end_frame = bpy.context.scene.ant_end_frame
    scale = bpy.context.scene.ant_scale
#    ground = bpy.context.selected_objects[-1]
    a_ps = Particle_system(guide, ground, scale)
    a_ps.add_particles(number_ants)

    print('\n---')
    start = time()
    seed(0)
    noise.seed_set(0)
    for f in range(start_frame, end_frame+1):
#        a_ps.add_particles(1)
        if f%10 == 0:
            print('frame: {:04}'.format(f))
        a_ps.step()
    print('Simulated in {:05.5f} seconds'.format(time() - start))


class AntPanel(bpy.types.Panel):
    """"""
    bl_category = "Tools"
    bl_label = "Ant Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
#        layout.label(text=" Simple Row:")

        column = layout.column(align=True)
        column.prop(scene, "ant_number")
        column.prop(scene, "ant_start_frame")
        column.prop(scene, "ant_end_frame")
        column.prop(scene, "ant_scale")
        column = layout.column(align=True)
        column.prop_search(scene, "ant_ground", scene, "objects")
        column.prop_search(scene, "ant_guide", scene, "objects")
        column.prop_search(scene, "ant_instance", scene, "objects")

        layout.separator()

        column = layout.row()
        column.operator("ant.generate")


class AntOperator(bpy.types.Operator):
    """Generate ant colony"""
    bl_idname = "ant.generate"
    bl_label = "Ant Generator"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        main(context)
        return {'FINISHED'}

def register():
    bpy.types.Scene.ant_number = bpy.props.IntProperty(name='Number Of Ants', description='Number Of Ants', min=1, soft_max=1000, default = 100)
    bpy.types.Scene.ant_start_frame = bpy.props.IntProperty(name='Start Frame', description='Start Frame', min=0, soft_max=1000, default = 1)
    bpy.types.Scene.ant_end_frame = bpy.props.IntProperty(name='End Frame', description='End Frame', min=1, soft_max=1000, default = 100)
    bpy.types.Scene.ant_scale = bpy.props.FloatProperty(name='Colony Scale', description='Colony Scale', min=0.0, soft_max=100.0, default = 1.0)
    bpy.types.Scene.ant_ground = bpy.props.StringProperty(name='Ground Object', description='Ground Object', default='')
    bpy.types.Scene.ant_guide = bpy.props.StringProperty(name='Guide Object', description='Guide Object', default='')
    bpy.types.Scene.ant_instance = bpy.props.StringProperty(name='Instance Object', description='Instance Object', default='')

    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
#
#    # test call
#    bpy.ops.object.simple_operator()

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
from bpy.types import Operator

#obj = bpy.context.object

#planes = bpy.context.selected_objects
#planes.remove(obj)

suffix_hierarchy = {
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
#                print(b.name[4:-2])
                obj_name, suffix = bone_name[:-2].replace(' ', '_'), bone_name[-2:]
                # Check for object existing
                if not obj_name in bpy.data.objects:
                    if not obj_name + suffix_hierarchy[suffix] in bpy.data.objects:
                        self.report({"WARNING"}, "Could not find object %s" % obj_name)
                        continue
                    else:
                        obj_name = obj_name + suffix_hierarchy[suffix]
                
                p = bpy.data.objects[obj_name]
                
                # Check that object is not already parented
                if bone_name in context.scene.objects and context.scene.objects[bone_name].parent == obj and context.scene.objects[bone_name].parent_bone == b.name:
                    self.report({"WARNING"}, "Object %s already child of bone %s" % (obj_name, b.name))
                    continue
                
                mat = p.matrix_world.copy()
                if p.name in bpy.context.scene.objects:
                    bpy.context.scene.objects.unlink(p)
                p = bpy.data.objects.new(bone_name[:], p.data)
                bpy.context.scene.objects.link(p)
            else:
                if not bone_name in bpy.data.objects:
                    self.report({"WARNING"}, "Could not find object %s" % bone_name)
                    continue
                p = bpy.data.objects[bone_name[:]]
                mat = p.matrix_world.copy()

            p.parent = obj
            p.parent_type = 'BONE'
            p.parent_bone = b.name
            p.matrix_world = mat
                
#                print("Could not connect", s.name)
    obj.data.pose_position = initial_position


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


class VIEW3D_PT_parent_planes_to_bones(bpy.types.Panel):
    bl_label = "Parent planes to bones"
    bl_category = 'Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        obj = context.active_object
        if obj is not None:
            r = self.layout.row()
            r.operator("rigging.parent_planes_to_bones")

def register():
    bpy.utils.register_class(OBJECT_OT_parent_planes_to_bones)
    bpy.utils.register_class(VIEW3D_PT_parent_planes_to_bones)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_parent_planes_to_bones)
    bpy.utils.unregister_class(VIEW3D_PT_parent_planes_to_bones)


if __name__ == "__main__":
    register()

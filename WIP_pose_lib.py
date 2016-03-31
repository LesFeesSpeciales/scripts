import bpy
import json
import os
from bpy import context
from bpy.props import *
from mathutils import Matrix


JSON_PATH = '/tmp/'

#----------------------------------------------------------
# PROPS
#----------------------------------------------------------
def initSceneProperties(scn):
    bpy.types.Scene.jsonName = StringProperty(
        name = "Pose Name")
    scn['jsonName'] = "TMP"
    return
initSceneProperties(bpy.context.scene)

#----------------------------------------------------------
# JSON
#----------------------------------------------------------
def json_write(output_path, bone_dict, file_name):
    with open(os.path.join(output_path, file_name+'.json'), 'a') as outfile:
        json.dump(bone_dict, outfile, indent = 2, ensure_ascii=False)

def json_read(file_path, file_name):
    with open(os.path.join(file_path, file_name)) as json_file:
        json_data = json.load(json_file)
        return json_data

    
#----------------------------------------------------------
# METHODS
#----------------------------------------------------------
def export_transforms(fileName):
    bpy.ops.object.mode_set(mode='POSE')
    boneTransform_dict = {}
    bone_list = []
    if len(bpy.context.selected_pose_bones):
        bone_list = bpy.context.selected_pose_bones
    else : 
        for arma in [r for r in bpy.data.objects if r.type == 'ARMATURE']:
            bone_list.extend(arma.pose.bones)
    
    boneTransform_dict = {}
    for bone in bone_list:
        if bone.id_data.name not in boneTransform_dict:
            boneTransform_dict[bone.id_data.name] = {}
        print('----------------')
        matrix_final = bone.matrix_basis
        matrix_json = [tuple(e) for e in list(matrix_final)]
        
        boneTransform_dict[bone.id_data.name][bone.name] = matrix_json
        
    json_write(JSON_PATH, boneTransform_dict, fileName)
    
    
def import_transforms(fileName):
    bpy.ops.object.mode_set(mode='POSE')
            
    bones = bpy.context.selected_pose_bones
    if bones == [] : 
        for rig in [r for r in bpy.data.objects if r.type == 'ARMATURE']:
            for bone in rig.pose.bones:
                bones.append(bone)
    
    json_data = {}
    json_data = json_read(JSON_PATH, fileName+".json")
    print("Reading json data")
    
    for bone in bones:
        arma = bone.id_data.name
        if json_data.get(arma) and json_data.get(arma).get(bone.name): # If the armature is in json_data and the bone is in armature
            json_matrix = json_data.get(arma).get(bone.name) #Transforms dictionary
            #print(bone.name, ' --- ', value)
            
            matrix_final = Matrix(json_matrix)
            print(bone.name, '\n', matrix_final)
            
#            bone.matrix_world = matrix_final
            bone.matrix_basis = matrix_final
            
            '''
                else :
                    if key == "POSITION" :
                        mode = "location"
                        value = transformDict[key]
                    elif key == "SCALE" :
                        mode = "scale"
                    elif key == "AXIS_ANGLE":
                        mode = "rotation_axis_angle"
                    elif key == "QUATERNION":
                        mode = "rotation_quaternion"
                    else : 
                        mode = "rotation_euler"
                    value = transformDict[key]
                    setattr(bone, mode, value)
            '''
                        

'''
bpy.ops.object.mode_set(mode='POSE')
pose_bone = context.active_pose_bone

# we can get the object from the pose bone
obj = pose_bone.id_data
matrix_final = obj.matrix_world * pose_bone.matrix

print(matrix_final)


# now we can view the matrix by applying it to an object
obj_empty = bpy.data.objects.new("Test", None)
context.scene.objects.link(obj_empty)
obj_empty.matrix_world = matrix_final
'''                    
#----------------------------------------------------------
# PANEL
#----------------------------------------------------------
class PosePanel(bpy.types.Panel):
    bl_label = "Pose Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "LFS"
 
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn, 'jsonName')
        layout.operator("lsf.export")
        layout.operator("lsf.import")
        
#----------------------------------------------------------
# OPERATORS
#----------------------------------------------------------
class Pose_export(bpy.types.Operator):
    bl_idname = "lsf.export"
    bl_label = "Export Pose Lib"
    
    def execute(self, context):
        scn = context.scene
        if os.path.isfile(os.path.join(JSON_PATH+scn['jsonName']+".json")):
            bpy.ops.object.dialog_operator('INVOKE_DEFAULT') #calls the popup
        else:
            self.report({'INFO'}, "Creating the pose in library")
            export_transforms(scn['jsonName'])
        
        return{'FINISHED'}

class Pose_import(bpy.types.Operator):
    bl_idname = "lsf.import"
    bl_label = "Import Pose Lib"
 
    def execute(self, context):
        scn = context.scene
        if os.path.isfile(os.path.join(JSON_PATH+scn['jsonName']+".json")):
            self.report({'INFO'}, "Loading the pose in library")
            import_transforms(scn['jsonName'])
        else:
            self.report({'ERROR'}, "Pose name does not exist, please pick an existing pose name")
        
        return{'FINISHED'}    
overwrite = False

#----------------------------------------------------------
# POPUP
#----------------------------------------------------------
class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "Pose already exist, overwrite or change the pose name"
    
    overwrite = BoolProperty(name="Overwrite")
    
    def execute(self, context):
        scn = context.scene
        if self.overwrite:
            print("Overwriting the file ", bpy.context.scene['jsonName'], ".json")
            os.remove(os.path.join(JSON_PATH+scn['jsonName']+".json"))
            export_transforms(scn['jsonName'])
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
#----------------------------------------------------------
# REGISTER
#----------------------------------------------------------
bpy.utils.register_class(DialogOperator)
bpy.utils.register_module(__name__)
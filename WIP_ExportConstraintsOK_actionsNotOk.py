import bpy
import json
import os
from bpy.props import *

#----------------------------------------------------------
# PROPS
#----------------------------------------------------------
# def initSceneProperties():
    # bpy.types.Scene.json_name = StringProperty(name = "Pose Name", default = "TMP")
    
    # return
# initSceneProperties()

def initSceneProperties(scn):
    bpy.types.Scene.json_name = StringProperty(
        name = "Pose Name")
    scn['json_name'] = "TMP"
    return
initSceneProperties(bpy.context.scene)

#----------------------------------------------------------
# JSON
#----------------------------------------------------------
def json_write(output_path, bone_dict, file_name):
    with open(os.path.join(output_path, file_name+'.json'), 'a') as outfile:
        json.dump(bone_dict, outfile, indent=4, ensure_ascii=False)

def json_read(file_path, file_name):
    with open(os.path.join(file_path, file_name)) as json_file:
        json_data = json.load(json_file)
        return json_data

#----------------------------------------------------------
# EXPORT
#----------------------------------------------------------
def export_transforms(file_name):

    print("--------------------------------------------------------------")
    bpy.ops.object.mode_set(mode='POSE')
    # tmp_types = []
    bone_data = {}
    bones = []
    if len(bpy.context.selected_pose_bones):
        bones = bpy.context.selected_pose_bones
    else : 
        for arma in [r for r in bpy.data.objects if r.type == 'ARMATURE']:
            bones.extend(arma.pose.bones)
    for bone in bones:
        # If the armature name wich bone is afected is not in the dictionary, append new dictionary in bone_data
        if bone.id_data.name not in bone_data: 
            bone_data[bone.id_data.name] = {}
        # TRANSFORMS
        if bone.rotation_mode == "AXIS_ANGLE":
            mode = "rotation_axis_angle"
        elif bone.rotation_mode == "QUATERNION":
            mode = "rotation_quaternion"
        else:
            mode = "rotation_euler"
        # Append new dictionary in bone_Data[armature.name][bone.name] with transforms info
        bone_data[bone.id_data.name][bone.name] = {}
        bone_data[bone.id_data.name][bone.name][bone.rotation_mode] = tuple(getattr(bone, mode))
        bone_data[bone.id_data.name][bone.name].update({"POSITION" : tuple(getattr(bone, 'location'))})
        bone_data[bone.id_data.name][bone.name].update({"SCALE" : tuple(getattr(bone, 'scale'))})
        #CONSTRAINS
        # If there are constraints on bone, append new dictionary in bone_Data[armature.name][bone.name]
        if len(bone.constraints): 
            bone_data[bone.id_data.name][bone.name].update({"CONSTRAINTS" : {}})
            for bone_constraint in bone.constraints:
                bone_data[bone.id_data.name][bone.name]["CONSTRAINTS"].update({bone_constraint.name : {}})
                for cst_parameters in dir(bone_constraint):
                    if cst_parameters.startswith('__') or cst_parameters.startswith('bl_') or cst_parameters.startswith('rna_'):
                        pass
                    elif getattr(bone_constraint, cst_parameters) is not None:
                        my_type = type(getattr(bone_constraint, cst_parameters))
                        my_attr = getattr(bone_constraint, cst_parameters)
                        
                        if my_type == bpy.types.Object:
                            bone_data[bone.id_data.name][bone.name]["CONSTRAINTS"][bone_constraint.name].update({cst_parameters : my_attr.name})
                        elif my_type == bpy.types.Action:
                            pass    
                            # print(bone.id_data.name, " ", bone.name, "----- Action ---->", my_attr.name)
                        else:
                            bone_data[bone.id_data.name][bone.name]["CONSTRAINTS"][bone_constraint.name].update({cst_parameters : my_attr}) # str(type(getattr(bone_constraint, cst_parameters)))}
                        
                        # if my_type not in tmp_types:
                            # tmp_types.append(my_type)
    # for tty in tmp_types:
        # print(tty)
    try:
        json_write("D:\_FAC\ColoBlender2015\Pipeline\PoseLib", bone_data, file_name)
    except:
        print("not ok", bone_data)
        
#----------------------------------------------------------
# IMPORT
#----------------------------------------------------------
def import_transforms(file_name):
    bpy.ops.object.mode_set(mode='POSE')
            
    bones = bpy.context.selected_pose_bones
    if bones == [] : 
        for rig in [r for r in bpy.data.objects if r.type == 'ARMATURE']:
            for bone in rig.pose.bones:
                bones.append(bone)
    
    json_data = {}
    json_data = json_read("D:\_FAC\ColoBlender2015\Pipeline\PoseLib\\", file_name + ".json")    
    print("Reading json data")
    
    for bone in bones:
        arma = bone.id_data.name
        if json_data.get(arma) and json_data.get(arma).get(bone.name): # If the armature is in json_data and the bone is in armature
            transformDict = json_data.get(arma).get(bone.name) #Transforms dictionary
            #print(bone.name, ' --- ', value)
            # print('BONE = ', bone.name, '\nKEYS = ', transformDict, '\n')
            for key in transformDict:
                #print('BONE = ', bone.name, '\nKEY = ', key, '\nVALUE = ', transformDict[key], '\n')
                if key == "CONSTRAINTS":
                    print(bone.name, ' ----> ',  transformDict[key], "\n")
                elif key == "ACTIONS":
                    print (bone.name, ' ----> ',  transformDict[key], "\n")
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
        layout.prop(scn, 'json_name')
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
        if os.path.isfile("D:\_FAC\ColoBlender2015\Pipeline\PoseLib\\"+scn['json_name']+".json"):
            bpy.ops.object.dialog_operator('INVOKE_DEFAULT') #calls the popup
        else:
            self.report({'INFO'}, "Creating the pose in library")
            export_transforms(scn['json_name'])
        
        return{'FINISHED'}

class Pose_import(bpy.types.Operator):
    bl_idname = "lsf.import"
    bl_label = "Import Pose Lib"
 
    def execute(self, context):
        scn = context.scene
        if os.path.isfile("D:\_FAC\ColoBlender2015\Pipeline\PoseLib\\"+scn['json_name']+".json"):
            self.report({'INFO'}, "Loading the pose in library")
            import_transforms(scn['json_name'])
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
            print("Overwriting the file ", bpy.context.scene['json_name']+".json")
            os.remove("D:\_FAC\ColoBlender2015\Pipeline\PoseLib\\"+scn['json_name']+".json")
            export_transforms(scn['json_name'])
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
#----------------------------------------------------------
# REGISTER
#----------------------------------------------------------
bpy.utils.register_class(DialogOperator)
bpy.utils.register_module(__name__)
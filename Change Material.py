import bpy
import re

bl_info = {
    "name": "Change Material",
    "description": "Allow user to batch replace materials accurately",
    "author": "WuYin",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Material",
    "category": "Material",
}

class MaterialMappingItem(bpy.types.PropertyGroup):
    old_material: bpy.props.StringProperty(name="Old Material")
    new_material: bpy.props.StringProperty(name="New Material")

class ChangeMaterialPanel(bpy.types.Panel):
    bl_label = "Change Material"
    bl_idname = "VIEW3D_PT_change_material"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Material'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.operator("material_mapping.clean_material_names", text="Clean Material Names", icon='SORTALPHA')
        layout.operator("material_mapping.get_selected_materials", text="Get Selected Materials", icon='MATERIAL')
        
        if not hasattr(scene, "material_mapping"):
            scene.material_mapping.clear()
        
        for index, item in enumerate(scene.material_mapping):
            row = layout.row()
            row.prop_search(item, "old_material", bpy.data, "materials", text="")
            row.label(icon='FORWARD')
            row.prop_search(item, "new_material", bpy.data, "materials", text="")
            row.operator("material_mapping.remove", text="", icon='X').index = index
        
        layout.operator("material_mapping.add", icon='ADD')
        layout.operator("material_mapping.remove_last", text="Remove Last", icon='REMOVE')
        layout.operator("material_mapping.swap", text="Swap Materials", icon='FILE_REFRESH')
        layout.operator("material_mapping.apply", text="Apply", icon='CHECKMARK')

class CleanMaterialNamesOperator(bpy.types.Operator):
    bl_idname = "material_mapping.clean_material_names"
    bl_label = "Clean Material Names"
    bl_description = "Keep only English characters. If there are duplicate material names, add a number to the name."

    def execute(self, context):
        existing_names = set()
        name_count = {}
        
        def clean_name(name):
            cleaned = re.sub(r'[^a-zA-Z]', '', name)
            if not cleaned:
                cleaned = "Material"
            return cleaned
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material:
                        original_name = slot.material.name
                        new_name = clean_name(original_name)
                        
                        if new_name in name_count:
                            name_count[new_name] += 1
                            new_name = f"{new_name}_{name_count[new_name]:03d}"
                        else:
                            name_count[new_name] = 0
                        
                        existing_names.add(new_name)
                        slot.material.name = new_name
                        
        return {'FINISHED'}

class GetSelectedMaterialsOperator(bpy.types.Operator):
    bl_idname = "material_mapping.get_selected_materials"
    bl_label = "Get Selected Materials"
    bl_description = "Enter all materials of the currently selected object into the material panel on the left in order."
  
    def execute(self, context):
        scene = context.scene
        if not hasattr(scene, "material_mapping"):
            scene.material_mapping.clear()
        
        material_names = []
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material and slot.material.name not in material_names:
                        material_names.append(slot.material.name)
        
        for name in material_names:
            item = scene.material_mapping.add()
            item.old_material = name
        
        return {'FINISHED'}

class AddMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.add"
    bl_label = "Add Material Mapping"

    def execute(self, context):
        context.scene.material_mapping.add()
        return {'FINISHED'}

class RemoveMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.remove"
    bl_label = "Remove Material Mapping"
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        scene = context.scene
        if 0 <= self.index < len(scene.material_mapping):
            scene.material_mapping.remove(self.index)
        return {'FINISHED'}

class RemoveLastMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.remove_last"
    bl_label = "Remove Last Material Mapping"

    def execute(self, context):
        scene = context.scene
        if scene.material_mapping:
            scene.material_mapping.remove(len(scene.material_mapping) - 1)
        return {'FINISHED'}

class SwapMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.swap"
    bl_label = "Swap Materials"

    def execute(self, context):
        for item in context.scene.material_mapping:
            item.old_material, item.new_material = item.new_material, item.old_material
        return {'FINISHED'}

class ApplyMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.apply"
    bl_label = "Apply Material Mapping"

    def execute(self, context):
        scene = context.scene
        material_map = {item.old_material: item.new_material for item in scene.material_mapping if item.old_material and item.new_material}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material and slot.material.name in material_map:
                        slot.material = bpy.data.materials.get(material_map[slot.material.name], slot.material)
        
        return {'FINISHED'}

classes = [
    MaterialMappingItem,
    ChangeMaterialPanel,
    CleanMaterialNamesOperator,
    GetSelectedMaterialsOperator,
    AddMaterialMapping,
    RemoveMaterialMapping,
    RemoveLastMaterialMapping,
    SwapMaterialMapping,
    ApplyMaterialMapping,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    if not hasattr(bpy.types.Scene, "material_mapping"):
        bpy.types.Scene.material_mapping = bpy.props.CollectionProperty(type=MaterialMappingItem)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "material_mapping"):
        del bpy.types.Scene.material_mapping

if __name__ == "__main__":
    register()

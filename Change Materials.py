import bpy
import re
import json

bl_info = {
    "name": "Change Materials",
    "description": "Allow user to batch replace materials accurately and export/import material mappings",
    "author": "WuYin",
    "version": (1, 2),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Change Materials",
    "category": "Material",
}

class MaterialMappingItem(bpy.types.PropertyGroup):
    old_material: bpy.props.StringProperty(name="Old Material")
    new_material: bpy.props.StringProperty(name="New Material")

    def draw_old_material_icon(self, layout, context):
        """繪製材質的預覽圖示"""
        if self.old_material:
            material = bpy.data.materials.get(self.old_material)
            if material:
                # 顯示材質的預覽圖示
                layout.label(text="", icon_value=layout.icon(material))
            else:
                # 如果材質不存在，顯示預設圖示
                layout.label(text="", icon='MATERIAL')
        else:
            # 如果沒有材質，顯示預設圖示
            layout.label(text="", icon='MATERIAL')

    def draw_new_material_icon(self, layout, context):
        """繪製材質的預覽圖示"""
        if self.new_material:
            material = bpy.data.materials.get(self.new_material)
            if material:
                # 顯示材質的預覽圖示
                layout.label(text="", icon_value=layout.icon(material))
            else:
                # 如果材質不存在，顯示預設圖示
                layout.label(text="", icon='MATERIAL')
        else:
            # 如果沒有材質，顯示預設圖示
            layout.label(text="", icon='MATERIAL')
            

# Add default MaterialMappingItem
def add_default_material_mappings(scene):
    if not hasattr(scene, "material_mapping"):
        scene.material_mapping.clear()
    for _ in range(3):
        scene.material_mapping.add()

# Listen to file load event
@bpy.app.handlers.persistent
def load_handler(dummy):
    scene = bpy.context.scene
    # Check if at least one MaterialMappingItem already exists
    if not hasattr(scene, "material_mapping") or len(scene.material_mapping) == 0:
        add_default_material_mappings(scene)

class ChangeMaterialPanel(bpy.types.Panel):
    bl_label = "Change Materials"
    bl_idname = "VIEW3D_PT_change_material"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Change Materials'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        if not hasattr(scene, "material_mapping"):
            scene.material_mapping.clear()
        
        for index, item in enumerate(scene.material_mapping):
            row = layout.row()
            
            item.draw_old_material_icon(row, context)
            row.prop_search(item, "old_material", bpy.data, "materials", text="")

            row.label(icon='FORWARD')
            
            item.draw_new_material_icon(row, context)
            row.prop_search(item, "new_material", bpy.data, "materials", text="")

            row.operator("material_mapping.remove", text="", icon='X').index = index

        layout.operator("material_mapping.add", icon='ADD')
        layout.operator("material_mapping.remove_last", text="Remove Last", icon='REMOVE')
        layout.operator("material_mapping.swap", text="Swap Materials", icon='ARROW_LEFTRIGHT')
        layout.operator("material_mapping.apply", text="Apply", icon='CHECKMARK')
        layout.operator("material_mapping.clean_material_names", text="Clean Material Names", icon='SORTALPHA')
        layout.operator("material_mapping.get_selected_materials", text="Get Selected Materials", icon='MATERIAL')
        layout.operator("material_mapping.export", text="Export Mapping", icon='EXPORT')
        layout.operator("material_mapping.import", text="Import Mapping", icon='IMPORT')

class AddMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.add"
    bl_label = "Add Material Mapping"
    bl_description = "Add a new material mapping entry to the list."
    bl_options = {'UNDO'}

    def execute(self, context):
        context.scene.material_mapping.add()
        return {'FINISHED'}

class RemoveMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.remove"
    bl_label = "Remove Material Mapping"
    bl_description = "Remove the selected material mapping entry from the list."
    bl_options = {'UNDO'}
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        scene = context.scene
        if 0 <= self.index < len(scene.material_mapping):
            scene.material_mapping.remove(self.index)
        return {'FINISHED'}

class RemoveLastMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.remove_last"
    bl_label = "Remove Last Material Mapping"
    bl_description = "Remove the last material mapping entry from the list."
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        if scene.material_mapping:
            scene.material_mapping.remove(len(scene.material_mapping) - 1)
        return {'FINISHED'}

class SwapMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.swap"
    bl_label = "Swap Materials"
    bl_description = "Swap the old and new materials in all mapping entries."
    bl_options = {'UNDO'}

    def execute(self, context):
        for item in context.scene.material_mapping:
            item.old_material, item.new_material = item.new_material, item.old_material
        return {'FINISHED'}

class ApplyMaterialMapping(bpy.types.Operator):
    bl_idname = "material_mapping.apply"
    bl_label = "Apply Material Mapping"
    bl_description = "Apply the material mapping to the selected objects, replacing old materials with new ones."
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        material_map = {item.old_material: item.new_material for item in scene.material_mapping if item.old_material and item.new_material}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material and slot.material.name in material_map:
                        slot.material = bpy.data.materials.get(material_map[slot.material.name], slot.material)
        
        return {'FINISHED'}

class CleanMaterialNamesOperator(bpy.types.Operator):
    bl_idname = "material_mapping.clean_material_names"
    bl_label = "Clean Material Names"
    bl_description = "Keep only English characters. If there are duplicate material names, add a number to the name."
    bl_options = {'UNDO'}

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
    bl_options = {'UNDO'}
  
    def execute(self, context):
        scene = context.scene
        if not hasattr(scene, "material_mapping"):
            scene.material_mapping.clear()
        
        # Get all material names from selected objects
        material_names = []
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material and slot.material.name not in material_names:
                        material_names.append(slot.material.name)
        
        # Check if all MaterialMappingItem entries are empty
        all_empty = all(not item.old_material and not item.new_material for item in scene.material_mapping)
        
        if all_empty:
            # If all entries are empty, fill from the start without adding new items
            for i, name in enumerate(material_names):
                if i < len(scene.material_mapping):
                    scene.material_mapping[i].old_material = name
                else:
                    # If there are more materials than slots, add new items
                    item = scene.material_mapping.add()
                    item.old_material = name
        else:
            # Find the last continuous empty slots from the bottom
            last_empty_index = -1
            for i in range(len(scene.material_mapping) - 1, -1, -1):
                if not scene.material_mapping[i].old_material and not scene.material_mapping[i].new_material:
                    last_empty_index = i
                else:
                    break
            
            if last_empty_index != -1:
                # Fill from the last empty index
                for i, name in enumerate(material_names):
                    if last_empty_index + i < len(scene.material_mapping):
                        scene.material_mapping[last_empty_index + i].old_material = name
                    else:
                        # If there are more materials than slots, add new items
                        item = scene.material_mapping.add()
                        item.old_material = name
            else:
                # No empty slots, add new entries
                for name in material_names:
                    item = scene.material_mapping.add()
                    item.old_material = name
        
        return {'FINISHED'}

class ExportMaterialMappingOperator(bpy.types.Operator):
    bl_idname = "material_mapping.export"
    bl_label = "Export Material Mapping"
    bl_description = "Save material mapping to a JSON file for later use."

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def ensure_json_extension(self):
        if self.filepath and not self.filepath.lower().endswith('.json'):
            self.filepath += '.json'

    def execute(self, context):
        self.ensure_json_extension()

        scene = context.scene
        mapping_data = [{"old_material": item.old_material, "new_material": item.new_material} for item in scene.material_mapping]
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=4)

        self.report({'INFO'}, "Material mapping exported successfully")
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "Material_Mapping.json"
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ImportMaterialMappingOperator(bpy.types.Operator):
    bl_idname = "material_mapping.import"
    bl_label = "Import Material Mapping"
    bl_description = "Load material mapping from a previously saved JSON file."
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene

        with open(self.filepath, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)

        self.fill_material_mapping(scene, mapping_data)

        self.report({'INFO'}, "Material mapping imported successfully")
        return {'FINISHED'}

    def fill_material_mapping(self, scene, mapping_data):
        all_empty = all(not item.old_material and not item.new_material for item in scene.material_mapping)

        if all_empty:
            for i, entry in enumerate(mapping_data):
                if i < len(scene.material_mapping):
                    scene.material_mapping[i].old_material = entry.get("old_material", "")
                    scene.material_mapping[i].new_material = entry.get("new_material", "")
                else:
                    item = scene.material_mapping.add()
                    item.old_material = entry.get("old_material", "")
                    item.new_material = entry.get("new_material", "")
        else:
            last_empty_index = -1
            for i in range(len(scene.material_mapping) - 1, -1, -1):
                if not scene.material_mapping[i].old_material and not scene.material_mapping[i].new_material:
                    last_empty_index = i
                else:
                    break

            if last_empty_index != -1:
                for i, entry in enumerate(mapping_data):
                    if last_empty_index + i < len(scene.material_mapping):
                        scene.material_mapping[last_empty_index + i].old_material = entry.get("old_material", "")
                        scene.material_mapping[last_empty_index + i].new_material = entry.get("new_material", "")
                    else:
                        item = scene.material_mapping.add()
                        item.old_material = entry.get("old_material", "")
                        item.new_material = entry.get("new_material", "")
            else:
                for entry in mapping_data:
                    item = scene.material_mapping.add()
                    item.old_material = entry.get("old_material", "")
                    item.new_material = entry.get("new_material", "")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

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
    ExportMaterialMappingOperator,
    ImportMaterialMappingOperator,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    if not hasattr(bpy.types.Scene, "material_mapping"):
        bpy.types.Scene.material_mapping = bpy.props.CollectionProperty(type=MaterialMappingItem)
    
    # Add default MaterialMappingItem
    if bpy.context and hasattr(bpy.context, "scene"):
        add_default_material_mappings(bpy.context.scene)
    
    # Listen to file load event
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "material_mapping"):
        del bpy.types.Scene.material_mapping
    
    # Remove event listener
    bpy.app.handlers.load_post.remove(load_handler)

if __name__ == "__main__":
    register()
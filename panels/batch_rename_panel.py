import bpy
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup, Panel
from ..utils.published_file_detector import detect_published_file_status

class FindReplaceItem(PropertyGroup):
    find: StringProperty(name="Find")
    replace: StringProperty(name="Replace")

class TextureBatchRenamerProperties(PropertyGroup):
    find_replace: CollectionProperty(type=FindReplaceItem)
    find_replace_index: IntProperty(name="Index", default=0)
    prefix_text: StringProperty(name="Prefix")
    suffix_text: StringProperty(name="Suffix")
    status: StringProperty(default="")

class TEXTURE_PT_BatchRenamePanel(bpy.types.Panel):
    bl_idname = "TEXTURE_PT_BatchRenamePanel"
    bl_label = "Batch Rename Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.texture_batch_renamer
        
        # Auto-detect published file
        is_published, source_path = detect_published_file_status(context)
        
        # Published file warning (inline)
        if is_published:
            warning_row = layout.row()
            warning_row.alert = True
            warning_col = warning_row.column(align=True)
            warning_col.scale_y = 0.8
            warning_col.label(text="🚫 Published file - Operations disabled", icon='ERROR')
            if source_path:
                warning_col.label(text=f"Source: {source_path}", icon='BLANK1')
            layout.separator()
        
        # Batch Rename Tools section
        box = layout.box()
        box.label(text="Batch Rename Tools", icon='SORTALPHA')
        
        row = box.row(align=True)
        row.enabled = not is_published
        row.label(text="Find & Replace", icon='VIEWZOOM')
        row.operator("texture.add_findreplace", text="", icon='ADD')
        row.operator("texture.remove_findreplace", text="", icon='REMOVE')
        row.operator("texture.clear_rule", text="", icon='TRASH')
        
        for i, item in enumerate(props.find_replace):
            box_in = box.box()
            col = box_in.column(align=True)
            col.enabled = not is_published
            col.prop(item, "find", text="Find")
            col.prop(item, "replace", text="Replace")
        
        col = box.column(align=True)
        col.enabled = not is_published
        col.prop(props, "prefix_text", text="Prefix")
        col.prop(props, "suffix_text", text="Suffix")
        
        row = box.row()
        row.enabled = not is_published
        row.operator("texture.batch_rename", icon='CHECKMARK', text="Apply Batch Rename")
        
        row = box.row()
        row.enabled = not is_published
        row.operator("texture.batch_rename_files", icon='FILE_TICK', text="Save Files")
        
        maps_box = layout.box()
        maps_box.label(text="Auto-Correct Maps", icon='NODE_TEXTURE')
        
        row = maps_box.row()
        row.enabled = not is_published
        row.operator("texture.auto_correct_maps", icon='AUTO', text="Run")

def register():
    bpy.utils.register_class(FindReplaceItem)
    bpy.utils.register_class(TextureBatchRenamerProperties)
    bpy.types.Scene.texture_batch_renamer = bpy.props.PointerProperty(type=TextureBatchRenamerProperties)
    bpy.utils.register_class(TEXTURE_PT_BatchRenamePanel)

def unregister():
    bpy.utils.unregister_class(TEXTURE_PT_BatchRenamePanel)
    del bpy.types.Scene.texture_batch_renamer
    bpy.utils.unregister_class(TextureBatchRenamerProperties)
    bpy.utils.unregister_class(FindReplaceItem)
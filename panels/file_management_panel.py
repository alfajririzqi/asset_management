import bpy
from ..utils.published_file_detector import detect_published_file_status

class TEXTURE_PT_FileManagementPanel(bpy.types.Panel):
    """Panel for file management operations"""
    bl_idname = "TEXTURE_PT_FileManagementPanel"
    bl_label = "File Management"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        is_published, source_path = detect_published_file_status(context)
        
        if is_published:
            warning_row = layout.row()
            warning_row.alert = True
            warning_col = warning_row.column(align=True)
            warning_col.scale_y = 0.8
            warning_col.label(text="🚫 Published file - Operations disabled", icon='ERROR')
            if source_path:
                row = warning_col.row()
                row.scale_y = 1.2
                op = row.operator("asset.copy_source_path", text=f"Source: {source_path}", icon='COPYDOWN', emboss=False)
                op.source_path = source_path
            layout.separator()
        
        stats_box = layout.box()
        stats_text = self._get_texture_statistics()
        stats_box.label(text=stats_text, icon='INFO')
        
        texture_opt_box = layout.box()
        texture_opt_box.label(text="Texture Optimization", icon='IMAGE_DATA')

        row = texture_opt_box.row(align=True)
        row.enabled = not is_published
        row.operator("texture.downgrade_resolution", text="Downgrade Resolution", icon='MOD_DECIM')
        row.separator()
        row.operator("texture.restore_resolution", text="", icon='FILE_REFRESH')

        row = texture_opt_box.row(align=True)
        row.enabled = not is_published
        row.operator("texture.convert_image_format", text="Convert Image Format", icon='IMAGE_PLANE')
        row.separator()
        row.operator("texture.restore_image_format", text="", icon='FILE_REFRESH')
        
        file_ops_box = layout.box()
        file_ops_box.label(text="File Operations", icon='FILE_FOLDER')
        
        row = file_ops_box.row()
        row.enabled = not is_published
        row.operator("asset.consolidate_textures", text="Consolidate Textures", icon='COPYDOWN')
        
        row = file_ops_box.row()
        row.enabled = not is_published
        row.operator("texture.cleanup_unused_textures", text="Cleanup Unused Textures", icon='TRASH')
    
    def _get_texture_statistics(self):
        import os
        
        total_textures = 0
        external_count = 0
        unused_count = 0
        packed_count = 0
        
        if bpy.data.filepath:
            current_dir = os.path.normpath(os.path.dirname(bpy.data.filepath))
        else:
            current_dir = None
        
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source != 'FILE':
                continue
            
            # SKIP: Ignore external link images (library overrides)
            if img.library:
                continue
            
            total_textures += 1
            
            # Count packed
            if img.packed_file:
                packed_count += 1
                continue
            
            # Count unused
            if img.users == 0:
                unused_count += 1
            
            # Count external (outside current blend directory)
            if current_dir and img.filepath:
                abs_path = bpy.path.abspath(img.filepath)
                abs_path = os.path.normpath(abs_path)
                if os.path.exists(abs_path) and not abs_path.startswith(current_dir):
                    external_count += 1
        
        # Build simple status text
        stats_text = f"Textures: {total_textures}"
        if external_count > 0:
            stats_text += f" | External: {external_count}"
        if packed_count > 0:
            stats_text += f" | Packed: {packed_count}"
        if unused_count > 0:
            stats_text += f" | Unused: {unused_count}"
        
        return stats_text

def register():
    bpy.utils.register_class(TEXTURE_PT_FileManagementPanel)

def unregister():
    bpy.utils.unregister_class(TEXTURE_PT_FileManagementPanel)
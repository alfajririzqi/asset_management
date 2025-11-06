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
        
        # Statistics section
        stats_box = layout.box()
        stats_text = self._get_texture_statistics()
        stats_box.label(text=stats_text, icon='INFO')
        
        # Texture Optimization section
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
        
        # File Operations section
        file_ops_box = layout.box()
        file_ops_box.label(text="File Operations", icon='FILE_FOLDER')
        
        row = file_ops_box.row()
        row.enabled = not is_published
        row.operator("asset.consolidate_textures", text="Consolidate Textures", icon='COPYDOWN')
        
        row = file_ops_box.row()
        row.enabled = not is_published
        row.operator("texture.cleanup_unused_textures", text="Cleanup Unused Textures", icon='TRASH')
    
    def _get_texture_statistics(self):
        """Calculate simple texture statistics for display"""
        import os
        
        # Count textures
        total_textures = 0
        external_count = 0
        unused_count = 0
        packed_count = 0
        
        # Get textures directory if file is saved
        if bpy.data.filepath:
            blend_dir = os.path.dirname(bpy.data.filepath)
            textures_dir = os.path.join(blend_dir, "textures")
            textures_dir_exists = os.path.exists(textures_dir)
        else:
            textures_dir_exists = False
            textures_dir = ""
        
        # Count texture statistics
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source != 'FILE':
                continue
            
            total_textures += 1
            
            # Count packed
            if img.packed_file:
                packed_count += 1
                continue
            
            # Count unused
            if img.users == 0:
                unused_count += 1
                continue
            
            # Count external (only if we have a textures directory)
            if textures_dir_exists and img.filepath_raw:
                abs_path = bpy.path.abspath(img.filepath_raw)
                if os.path.exists(abs_path):
                    try:
                        if os.path.commonpath([abs_path, textures_dir]) != textures_dir:
                            external_count += 1
                    except ValueError:
                        external_count += 1
        
        # Build simple status text
        return f"📊 Total: {total_textures}  |  External: {external_count}  |  Unused: {unused_count}  |  Packed: {packed_count}"

def register():
    bpy.utils.register_class(TEXTURE_PT_FileManagementPanel)

def unregister():
    bpy.utils.unregister_class(TEXTURE_PT_FileManagementPanel)
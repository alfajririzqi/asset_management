import bpy
import os
import shutil

class TEXTURE_OT_DowngradeResolution(bpy.types.Operator):
    """Downgrade texture resolution to 2K, 1K, or 512."""
    bl_idname = "texture.downgrade_resolution"
    bl_label = "Downgrade Resolution"
    bl_description = "Downgrade texture resolution and backup original files"
    
    resolution: bpy.props.EnumProperty(
        name="Target Resolution",
        items=[
            ('2K', "2K (2048)", "Downgrade to 2048px max dimension"),
            ('1K', "1K (1024)", "Downgrade to 1024px max dimension"),
            ('512', "512 (512)", "Downgrade to 512px max dimension")
        ],
        default='2K'
    )
    
    backup_original: bpy.props.BoolProperty(
        name="Backup Original",
        description="Backup original files into `.backup` folder with .hires extension",
        default=True
    )
    
    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "resolution", expand=True)
        layout.prop(self, "backup_original")
        if self.backup_original:
            layout.label(text="Backups saved as: filename.png.hires", icon='INFO')
        layout.separator()
        layout.label(text="Original files will be overwritten!", icon='ERROR')
    
    def execute(self, context):
        if self.resolution == '2K':
            target_size = 2048
        elif self.resolution == '1K':
            target_size = 1024
        else:
            target_size = 512
        
        downgraded = 0
        skipped = 0
        errors = 0
        udim_skipped = 0
        
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source != 'FILE':
                skipped += 1
                continue
            if hasattr(img, "tiles") and len(img.tiles) > 1:
                udim_skipped += 1
                skipped += 1
                continue
            
            abs_path = bpy.path.abspath(img.filepath_raw)
            if not abs_path or not os.path.exists(abs_path):
                self.report({'WARNING'}, f"File not found for {img.name}")
                skipped += 1
                continue
            
            original_width, original_height = img.size
            max_dimension = max(original_width, original_height)
            
            if max_dimension <= target_size:
                skipped += 1
                continue
            
            try:
                # Backup original with .hires extension marker
                if self.backup_original:
                    backup_dir = os.path.join(os.path.dirname(abs_path), ".backup")
                    os.makedirs(backup_dir, exist_ok=True)
                    
                    original_filename = os.path.basename(abs_path)
                    backup_filename = original_filename + ".hires"
                    backup_path = os.path.join(backup_dir, backup_filename)
                    
                    if not os.path.exists(backup_path):
                        shutil.copy2(abs_path, backup_path)
                
                if original_width > original_height:
                    new_width = target_size
                    new_height = int(original_height * (target_size / original_width))
                else:
                    new_height = target_size
                    new_width = int(original_width * (target_size / original_height))
                
                img.scale(new_width, new_height)
                img.save()
                
                downgraded += 1
                
            except Exception as e:
                errors += 1
                self.report({'ERROR'}, f"Error downgrading {img.name}: {str(e)}")
        
        msg = f"Downgraded: {downgraded}"
        if skipped > 0:
            msg += f" • Skipped: {skipped - udim_skipped}"
        if udim_skipped > 0:
            msg += f" • UDIM skipped: {udim_skipped}"
        if errors > 0:
            msg += f" • Errors: {errors}"
        
        if downgraded > 0:
            self.report({'INFO'}, msg)
        else:
            self.report({'WARNING'}, msg)
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(TEXTURE_OT_DowngradeResolution)


def unregister():
    bpy.utils.unregister_class(TEXTURE_OT_DowngradeResolution)

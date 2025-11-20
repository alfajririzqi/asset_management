import bpy
import os
import shutil

class TEXTURE_OT_ConvertImageFormat(bpy.types.Operator):
    """Convert all file-based textures to PNG or JPEG."""
    bl_idname = "texture.convert_image_format"
    bl_label = "Convert Image Format"
    bl_description = "Convert all file-based textures to PNG or JPEG"

    target_format: bpy.props.EnumProperty(
        name="Target Format",
        items=[
            ('PNG',  "PNG",  "Lossless, alpha supported"),
            ('JPEG', "JPEG", "Lossy, no alpha")
        ],
        default='PNG',
    )

    backup_original: bpy.props.BoolProperty(
        name="Backup Original",
        description="Move originals into a `.backup` folder and append .fmt extension",
        default=True,
    )

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_format", expand=True)
        if self.target_format == 'JPEG':
            layout.label(text="JPEG format does not support alpha channel", icon='ERROR')
        layout.prop(self, "backup_original")
        if self.backup_original:
            layout.label(text="Backups saved as: filename.png.fmt", icon='INFO')
        layout.separator()
        layout.label(text="Original files will be overwritten!", icon='ERROR')
        layout.separator()
        layout.label(text="Note: External & packed textures will be skipped", icon='INFO')

    def execute(self, context):
        from ..utils.texture_detector import detect_external_and_packed_textures
        
        external_imgs, packed_imgs, local_imgs = detect_external_and_packed_textures(context)
        
        converted = 0
        skipped = 0
        skipped_external = 0
        skipped_packed = 0
        blend_dir = os.path.dirname(bpy.data.filepath)

        if not blend_dir:
            self.report({'ERROR'}, "Please save your .blend file before converting textures")
            return {'CANCELLED'}

        target_ext = ".png" if self.target_format == 'PNG' else ".jpg"

        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source != 'FILE':
                skipped += 1
                continue
            
            # Skip external textures
            if img.name in external_imgs:
                skipped_external += 1
                continue
            
            # Skip packed textures
            if img.name in packed_imgs:
                skipped_packed += 1
                continue

            original_abs_path = bpy.path.abspath(img.filepath)

            if getattr(img, "packed_file", None):
                try:
                    img.unpack(method='WRITE_ORIGINAL')
                    original_abs_path = bpy.path.abspath(img.filepath)
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to unpack {img.name}: {str(e)}")
                    skipped += 1
                    continue

            if not original_abs_path or not os.path.exists(original_abs_path):
                self.report({'WARNING'}, f"File not found for {img.name} at {img.filepath}")
                skipped += 1
                continue

            root, current_ext = os.path.splitext(original_abs_path)
            if current_ext.lower() == target_ext.lower():
                skipped += 1
                continue

            original_format = img.file_format
            original_filepath_raw = img.filepath_raw

            new_abs_path = root + target_ext
            new_rel_path = bpy.path.relpath(new_abs_path, start=blend_dir)

            if self.backup_original:
                backup_dir = os.path.join(os.path.dirname(original_abs_path), ".backup")
                os.makedirs(backup_dir, exist_ok=True)
                original_filename = os.path.basename(original_abs_path)
                backup_filename = original_filename + ".fmt"
                dest = os.path.join(backup_dir, backup_filename)
                if not os.path.exists(dest):
                    try:
                        shutil.copy2(original_abs_path, dest)
                    except Exception as e:
                        self.report({'WARNING'}, f"Backup failed for {original_filename}: {str(e)}")
                        skipped += 1
                        continue

            try:
                temp_img = None
                if not img.has_data:
                    temp_img = bpy.data.images.load(original_abs_path, check_existing=False)
                    temp_img.file_format = self.target_format
                    temp_img.filepath_raw = new_abs_path
                    temp_img.save()
                    bpy.data.images.remove(temp_img)
                else:
                    img.file_format = self.target_format
                    img.filepath_raw = new_abs_path
                    img.save()

                if os.path.exists(original_abs_path) and original_abs_path != new_abs_path:
                    try:
                        os.remove(original_abs_path)
                    except Exception as e:
                        self.report({'WARNING'}, f"Failed to delete original file {os.path.basename(original_abs_path)}: {str(e)}")

                img.filepath = new_rel_path
                img.name = os.path.basename(new_abs_path)

                converted += 1

            except Exception as e:
                img.file_format = original_format
                img.filepath_raw = original_filepath_raw
                self.report({'ERROR'}, f"Failed to convert {img.name}: {str(e)}")
                skipped += 1

        msg = f"Converted: {converted}"
        if skipped > 0:
            msg += f" | Skipped: {skipped}"
        if skipped_external > 0:
            msg += f" | External: {skipped_external}"
        if skipped_packed > 0:
            msg += f" | Packed: {skipped_packed}"
        
        if converted > 0:
            self.report({'INFO'}, msg)
        else:
            self.report({'WARNING'}, msg)
        
        # Log activity
        from ..utils.activity_logger import log_activity
        format_name = "PNG" if self.target_format == 'PNG' else "JPEG"
        details = f"Format: {format_name} | Converted: {converted}"
        if skipped_external > 0:
            details += f" | External: {skipped_external}"
        if skipped_packed > 0:
            details += f" | Packed: {skipped_packed}"
        
        log_activity("CONVERT_FORMAT", details, context)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(TEXTURE_OT_ConvertImageFormat)

def unregister():
    bpy.utils.unregister_class(TEXTURE_OT_ConvertImageFormat)
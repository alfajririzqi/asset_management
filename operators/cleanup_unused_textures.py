import bpy
import glob
import os
import re
import shutil
import time
from difflib import get_close_matches

class TEXTURE_OT_CleanupUnusedTextures(bpy.types.Operator):
    """Scan the project's textures folder and move or delete unused textures."""
    bl_idname = "texture.cleanup_unused_textures"
    bl_label = "Cleanup Unused Textures"
    bl_description = "Scan the /textures directory and move/delete unused textures"

    action: bpy.props.EnumProperty(
        name="Action",
        description="Select the action to perform",
        items=[
            ('MOVE_TO_TRASH', "Move to .trash", "Move unused textures to a .trash folder"),
            ('DELETE_PERMANENTLY', "Delete Permanently", "Delete unused textures permanently"),
        ],
        default='MOVE_TO_TRASH',
    )

    unused_textures = []
    total_unused = 0

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}

        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")

        if not os.path.exists(textures_dir):
            self.report({'ERROR'}, f"Textures directory not found: {textures_dir}")
            return {'CANCELLED'}

        IMAGE_EXTENSIONS = {
            'png', 'jpg', 'jpeg', 'tga', 'bmp', 'tiff', 'webp', 'exr', 'hdr', 'dds',
            'psd', 'svg', 'gif', 'mp4', 'mov', 'avi', 'mkv',
        }

        texture_files = set()  
        for ext in IMAGE_EXTENSIONS:
            texture_files.update(glob.glob(os.path.join(textures_dir, f"*.{ext}")))
            texture_files.update(glob.glob(os.path.join(textures_dir, f"*.{ext.upper()}")))
        
        texture_files = list(texture_files)  

        def normalize_udim(path):
            udim_match = re.search(r'(_\d{4})(?=\.)', path)
            if udim_match:
                return os.path.splitext(path)[0].replace(udim_match.group(1), '_<UDIM>')
            return path

        used_textures = set()
        for img in bpy.data.images:
            if img.source != 'FILE':
                continue
            try:
                abs_path = bpy.path.abspath(img.filepath)
                norm_path = os.path.normpath(abs_path)
                norm_path = normalize_udim(norm_path)
                used_textures.add(norm_path)
            except Exception:
                continue

        self.unused_textures = []
        for tex_path in texture_files:
            norm_path = os.path.normpath(tex_path)
            norm_path = normalize_udim(norm_path)
            if norm_path not in used_textures:
                self.unused_textures.append(tex_path)

        self.total_unused = len(self.unused_textures)

        if not self.unused_textures:
            self.report({'INFO'}, "No unused textures found")
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Found {self.total_unused} unused texture(s):", icon='INFO')

        for tex_path in self.unused_textures[:5]:
            layout.label(text=f"- {os.path.basename(tex_path)}", icon='BLANK1')

        if self.total_unused > 5:
            layout.label(text=f"- and {self.total_unused - 5} more...", icon='BLANK1')

        layout.separator()
        layout.label(text="Select action to perform:", icon='INFO')
        layout.prop(self, "action", expand=True)
        layout.separator()
        layout.label(text="Note: This operation cannot be undone!", icon='ERROR')

    def execute(self, context):
        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")
        trash_dir = os.path.join(textures_dir, ".backup", ".trash")
        processed = 0
        skipped = 0
        failed = 0

        for tex_path in self.unused_textures:
            if not os.path.exists(tex_path):
                skipped += 1
                print(f"Skipped (file not found): {os.path.basename(tex_path)}")
                continue
            
            if not os.access(tex_path, os.R_OK):
                failed += 1
                self.report({'WARNING'}, f"No read permission: {os.path.basename(tex_path)}")
                continue

            try:
                if self.action == 'DELETE_PERMANENTLY':
                    os.remove(tex_path)
                    processed += 1
                else:
                    os.makedirs(trash_dir, exist_ok=True)
                    
                    filename = os.path.basename(tex_path)
                    dest_path = os.path.join(trash_dir, filename)

                    if os.path.exists(dest_path):
                        name, ext = os.path.splitext(filename)
                        timestamp = int(time.time() * 1000)  
                        dest_path = os.path.join(trash_dir, f"{name}_{timestamp}{ext}")

                    shutil.move(tex_path, dest_path)
                    processed += 1
                    
            except PermissionError as e:
                failed += 1
                self.report({'ERROR'}, f"Permission denied: {os.path.basename(tex_path)}")
            except FileNotFoundError as e:
                skipped += 1
                print(f"File disappeared during processing: {os.path.basename(tex_path)}")
            except Exception as e:
                failed += 1
                self.report({'ERROR'}, f"Failed to process {os.path.basename(tex_path)}: {str(e)}")

        # Build result message
        action_word = "deleted" if self.action == 'DELETE_PERMANENTLY' else "moved to .trash"
        
        if processed > 0:
            msg = f"Successfully {action_word} {processed} texture(s)"
            if skipped > 0:
                msg += f" • Skipped {skipped} (not found)"
            if failed > 0:
                msg += f" • Failed {failed}"
            self.report({'INFO'}, msg)
        elif skipped > 0 or failed > 0:
            msg = f"No textures processed"
            if skipped > 0:
                msg += f" • {skipped} skipped (not found)"
            if failed > 0:
                msg += f" • {failed} failed"
            self.report({'WARNING'}, msg)
        else:
            self.report({'WARNING'}, "No textures were processed")
        
        # Log activity
        from ..utils.activity_logger import log_activity
        action = "Delete" if self.action == 'DELETE_PERMANENTLY' else "Move to Trash"
        details = f"Action: {action} | Cleaned: {processed}"
        if skipped > 0:
            details += f" | Skipped: {skipped}"
        if failed > 0:
            details += f" | Failed: {failed}"
        
        log_activity("CLEANUP_UNUSED_TEXTURES", details, context)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(TEXTURE_OT_CleanupUnusedTextures)


def unregister():
    bpy.utils.unregister_class(TEXTURE_OT_CleanupUnusedTextures)
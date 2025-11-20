import bpy
import os
import shutil

class TEXTURE_OT_RestoreResolution(bpy.types.Operator):
    """Restore all downgraded textures to their original resolution from .backup folder."""
    bl_idname = "texture.restore_resolution"
    bl_label = "Restore Resolution"
    bl_description = "Restore all downgraded textures from .backup folder (*.hires) to original resolution"

    backup_folders_found = []
    total_backups = 0
    backup_info = [] 

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}

        blend_dir = os.path.dirname(bpy.data.filepath)
        self.backup_folders_found = []
        self.total_backups = 0
        self.backup_info = []

        search_dirs = [os.path.join(blend_dir, "textures"), blend_dir]

        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source == 'FILE' and img.filepath:
                img_dir = os.path.dirname(bpy.path.abspath(img.filepath))
                if img_dir and img_dir not in search_dirs:
                    search_dirs.append(img_dir)

        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            
            backup_dir = os.path.join(search_dir, ".backup")
            if os.path.exists(backup_dir) and os.path.isdir(backup_dir):
                hires_files = [f for f in os.listdir(backup_dir) 
                               if f.endswith('.hires') and os.path.isfile(os.path.join(backup_dir, f))]
                if hires_files:
                    self.backup_folders_found.append(backup_dir)
                    self.total_backups += len(hires_files)

                    for hires_file in hires_files:
                        original_name = hires_file[:-6]  
                        root_name = os.path.splitext(original_name)[0]
                        parent_dir = os.path.dirname(backup_dir)
                        
                        backup_path = os.path.join(backup_dir, hires_file)
                        try:
                            temp_img = bpy.data.images.load(backup_path, check_existing=False)
                            backup_res = f"{temp_img.size[0]}x{temp_img.size[1]}"
                            bpy.data.images.remove(temp_img)
                        except:
                            backup_res = "Unknown"
                        
                        current_res = None
                        current_path = os.path.join(parent_dir, original_name)
                        if os.path.exists(current_path):
                            try:
                                temp_img = bpy.data.images.load(current_path, check_existing=False)
                                current_res = f"{temp_img.size[0]}x{temp_img.size[1]}"
                                bpy.data.images.remove(temp_img)
                            except:
                                current_res = "Unknown"
                        
                        if current_res and backup_res != current_res:
                            self.backup_info.append({
                                'name': root_name,
                                'backup_res': backup_res,
                                'current_res': current_res
                            })

        if not self.backup_folders_found:
            self.report({'INFO'}, "No resolution backup files (.hires) found")
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Found {self.total_backups} backup file(s) in {len(self.backup_folders_found)} location(s)", icon='INFO')
        layout.separator()
        layout.label(text="Note: External & packed textures will be skipped", icon='INFO')

        if len(self.backup_folders_found) <= 3:
            for backup_dir in self.backup_folders_found:
                rel_path = os.path.relpath(backup_dir, os.path.dirname(bpy.data.filepath))
                layout.label(text=f"• {rel_path}", icon='BLANK1')
        else:
            layout.label(text=f"• Multiple locations found", icon='BLANK1')

        layout.separator()

        if self.backup_info:
            box = layout.box()
            box.label(text="Resolution Restorations Detected:", icon='FILE_REFRESH')

            conversions = {}
            for info in self.backup_info:
                key = f"{info['current_res']} → {info['backup_res']}"
                conversions.setdefault(key, []).append(info['name'])

            shown = 0
            for conversion, names in conversions.items():
                if shown >= 3:
                    remaining = sum(len(v) for k, v in conversions.items() if k not in list(conversions.keys())[:3])
                    if remaining > 0:
                        box.label(text=f"  ... and {remaining} more", icon='BLANK1')
                    break

                box.label(text=f"  {conversion}: {len(names)} file(s)", icon='BLANK1')
                for name in names[:2]:
                    box.label(text=f"    • {name}", icon='BLANK1')
                if len(names) > 2:
                    box.label(text=f"    • ... and {len(names) - 2} more", icon='BLANK1')
                shown += 1

        layout.separator()
        layout.label(text="Backup files (*.hires) will be deleted", icon='ERROR')

    def execute(self, context):
        from ..utils.texture_detector import detect_external_and_packed_textures
        
        # Detect textures to skip
        external_imgs, packed_imgs, local_imgs = detect_external_and_packed_textures(context)
        
        restored = 0
        skipped = 0
        skipped_external = 0
        skipped_packed = 0
        failed = 0
        deleted_downgraded = 0
        blend_dir = os.path.dirname(bpy.data.filepath)

        for backup_dir in self.backup_folders_found:
            parent_dir = os.path.dirname(backup_dir)
            backup_files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.hires')]

            for backup_path in backup_files:
                try:
                    backup_filename = os.path.basename(backup_path)
                    original_filename = backup_filename[:-6]  
                    restore_path = os.path.join(parent_dir, original_filename)
                    
                    # Check if corresponding image is external or packed
                    should_skip = False
                    restore_abs = os.path.normpath(restore_path)
                    for img in bpy.data.images:
                        if img.source != 'FILE':
                            continue
                        if img.filepath:
                            img_abs = os.path.normpath(bpy.path.abspath(img.filepath))
                            if img_abs == restore_abs:
                                if img.name in external_imgs:
                                    skipped_external += 1
                                    should_skip = True
                                    break
                                elif img.name in packed_imgs:
                                    skipped_packed += 1
                                    should_skip = True
                                    break
                    
                    if should_skip:
                        continue

                    if not os.path.exists(restore_path):
                        self.report({'WARNING'}, f"Downgraded file not found: {original_filename}")
                        skipped += 1
                        continue

                    try:
                        os.remove(restore_path)
                        deleted_downgraded += 1
                    except Exception as e:
                        self.report({'WARNING'}, f"Could not delete downgraded file {original_filename}: {str(e)}")

                    shutil.copy2(backup_path, restore_path)
                    restored += 1

                    self._update_image_datablock(restore_path, blend_dir)

                    try:
                        os.remove(backup_path)
                    except Exception as e:
                        self.report({'WARNING'}, f"Could not remove backup {backup_filename}: {str(e)}")

                except Exception as e:
                    failed += 1
                    self.report({'WARNING'}, f"Failed to restore {os.path.basename(backup_path)}: {str(e)}")
                    continue

        msg = f"Restored {restored} file(s)"
        if deleted_downgraded > 0:
            msg += f" | Deleted {deleted_downgraded} downgraded"
        if skipped > 0:
            msg += f" | Skipped {skipped}"
        if skipped_external > 0:
            msg += f" | External {skipped_external}"
        if skipped_packed > 0:
            msg += f" | Packed {skipped_packed}"
        if failed > 0:
            msg += f" | Failed {failed}"

        self.report({'INFO'}, msg)
        
        # Log activity
        from ..utils.activity_logger import log_activity
        details = f"Restored: {restored}"
        if deleted_downgraded > 0:
            details += f" | Deleted: {deleted_downgraded}"
        if skipped_external > 0:
            details += f" | External: {skipped_external}"
        if skipped_packed > 0:
            details += f" | Packed: {skipped_packed}"
        if failed > 0:
            details += f" | Failed: {failed}"
        
        log_activity("RESTORE_RESOLUTION", details, context)
        
        return {'FINISHED'}

    def _update_image_datablock(self, restored_path, blend_dir):
        restored_abs = os.path.normpath(restored_path)
        restored_name = os.path.basename(restored_path)

        for img in bpy.data.images:
            if img.source != 'FILE':
                continue
            try:
                img_abs_path = os.path.normpath(bpy.path.abspath(img.filepath))
            except:
                continue

            if img_abs_path == restored_abs:
                try:
                    img.reload()
                except Exception as e:
                    self.report({'WARNING'}, f"Could not reload {img.name}: {str(e)}")


def register():
    bpy.utils.register_class(TEXTURE_OT_RestoreResolution)


def unregister():
    bpy.utils.unregister_class(TEXTURE_OT_RestoreResolution)

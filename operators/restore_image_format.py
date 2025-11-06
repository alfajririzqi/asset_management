import bpy
import os
import shutil

class TEXTURE_OT_RestoreImageFormat(bpy.types.Operator):
    """Restore all converted textures to their original format from .backup folder."""
    bl_idname = "texture.restore_image_format"
    bl_label = "Restore Image Format"
    bl_description = "Restore all file-based textures from .backup folder (*.fmt) to original format"

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
                fmt_files = [f for f in os.listdir(backup_dir) 
                            if f.endswith('.fmt') and os.path.isfile(os.path.join(backup_dir, f))]
                if fmt_files:
                    self.backup_folders_found.append(backup_dir)
                    self.total_backups += len(fmt_files)

                    for fmt_file in fmt_files:
                        original_name = fmt_file[:-4]
                        backup_ext = os.path.splitext(original_name)[1].upper().replace('.', '')
                        root_name = os.path.splitext(original_name)[0]

                        current_ext = None
                        parent_dir = os.path.dirname(backup_dir)
                        for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                            check_path = os.path.join(parent_dir, root_name + ext)
                            if os.path.exists(check_path):
                                current_ext = ext.upper().replace('.', '')
                                if current_ext == 'JPEG':
                                    current_ext = 'JPG'
                                break

                        if current_ext and backup_ext != current_ext:
                            self.backup_info.append({
                                'name': root_name,
                                'backup_format': backup_ext,
                                'current_format': current_ext
                            })

        if not self.backup_folders_found:
            self.report({'INFO'}, "No format backup files (.fmt) found")
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Found {self.total_backups} backup file(s) in {len(self.backup_folders_found)} location(s)", icon='INFO')

        if len(self.backup_folders_found) <= 3:
            for backup_dir in self.backup_folders_found:
                rel_path = os.path.relpath(backup_dir, os.path.dirname(bpy.data.filepath))
                layout.label(text=f"• {rel_path}", icon='BLANK1')
        else:
            layout.label(text=f"• Multiple locations found", icon='BLANK1')

        layout.separator()

        if self.backup_info:
            box = layout.box()
            box.label(text="Format Conversions Detected:", icon='FILE_REFRESH')
            conversions = {}
            for info in self.backup_info:
                key = f"{info['backup_format']} → {info['current_format']}"
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
        layout.label(text="Backup files (*.fmt) will be deleted", icon='ERROR')

    def execute(self, context):
        restored = 0
        skipped = 0
        failed = 0
        deleted_converted = 0
        blend_dir = os.path.dirname(bpy.data.filepath)

        for backup_dir in self.backup_folders_found:
            parent_dir = os.path.dirname(backup_dir)
            backup_files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.fmt')]

            for backup_path in backup_files:
                try:
                    backup_filename = os.path.basename(backup_path)
                    original_filename = backup_filename[:-4]
                    restore_path = os.path.join(parent_dir, original_filename)

                    root_name = os.path.splitext(original_filename)[0]
                    original_ext = os.path.splitext(original_filename)[1]
                    converted_files = []
                    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                        if ext.lower() != original_ext.lower():
                            potential = os.path.join(parent_dir, root_name + ext)
                            if os.path.exists(potential):
                                converted_files.append(potential)

                    if os.path.exists(restore_path):
                        skipped += 1
                        continue

                    shutil.copy2(backup_path, restore_path)
                    restored += 1

                    self._update_image_datablock(restore_path, converted_files, blend_dir)

                    for converted_file in converted_files:
                        try:
                            os.remove(converted_file)
                            deleted_converted += 1
                        except:
                            pass

                    try:
                        os.remove(backup_path)
                    except:
                        pass

                except Exception as e:
                    failed += 1
                    self.report({'WARNING'}, f"Failed to restore {os.path.basename(backup_path)}: {str(e)}")
                    continue

        msg = f"Restored {restored} file(s)"
        if deleted_converted > 0:
            msg += f" • Deleted {deleted_converted} converted file(s)"
        if skipped > 0:
            msg += f" • Skipped {skipped}"
        if failed > 0:
            msg += f" • Failed {failed}"

        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def _update_image_datablock(self, restored_path, converted_files, blend_dir):
        restored_abs = os.path.normpath(restored_path)
        search_paths = [os.path.normpath(f) for f in converted_files]
        root_name = os.path.splitext(os.path.basename(restored_path))[0]

        for img in bpy.data.images:
            if img.source != 'FILE':
                continue
            try:
                img_abs_path = os.path.normpath(bpy.path.abspath(img.filepath))
            except:
                continue

            if img_abs_path in search_paths:
                new_rel_path = bpy.path.relpath(restored_path, start=blend_dir)
                img.filepath = new_rel_path
                img.name = os.path.basename(restored_path)
                try:
                    img.reload()
                except:
                    pass
                continue

            try:
                img_root = os.path.splitext(os.path.basename(img.filepath))[0]
                if img_root == root_name:
                    img_dir = os.path.dirname(bpy.path.abspath(img.filepath))
                    if os.path.normpath(img_dir) == os.path.normpath(os.path.dirname(restored_path)):
                        new_rel_path = bpy.path.relpath(restored_path, start=blend_dir)
                        img.filepath = new_rel_path
                        img.name = os.path.basename(restored_path)
                        try:
                            img.reload()
                        except:
                            pass
            except:
                continue


def register():
    bpy.utils.register_class(TEXTURE_OT_RestoreImageFormat)

def unregister():
    bpy.utils.unregister_class(TEXTURE_OT_RestoreImageFormat)

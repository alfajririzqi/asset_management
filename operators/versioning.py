import bpy
import os
import shutil
import time
import hashlib
import fnmatch
from datetime import datetime

LOG_FILENAME = "versioning_activity.log"


def get_version_list(self, context):
    """Get list of version files for EnumProperty (filtered by current blend name)"""
    fp = bpy.data.filepath
    if not fp:
        return []
    versions_dir = os.path.join(os.path.dirname(fp), "versions")
    if not os.path.exists(versions_dir):
        return []
    
    current_filename = os.path.basename(fp)
    base_name = current_filename.replace('.blend', '')
    
    items = []
    all_blends = [f for f in os.listdir(versions_dir) if f.endswith('.blend')]
    
    matching_blends = [f for f in all_blends if f.startswith(base_name)]
    
    matching_blends.sort(key=lambda f: os.path.getmtime(os.path.join(versions_dir, f)), reverse=True)
    
    for idx, name in enumerate(matching_blends):
        label = name
        desc = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
            os.path.getmtime(os.path.join(versions_dir, name))
        ))
        items.append((name, label, desc, idx))
    
    return items if items else [('NONE', 'No versions', 'No versions available', 0)]


def ensure_versions_dir(main_filepath):
    """Create versions directory if it doesn't exist"""
    if not main_filepath:
        return None
    versions_dir = os.path.join(os.path.dirname(main_filepath), "versions")
    os.makedirs(versions_dir, exist_ok=True)
    return versions_dir


def append_log_compact(main_filepath, message_short):
    """Append one compact line to versioning_activity.log with timestamp"""
    versions_dir = ensure_versions_dir(main_filepath)
    if not versions_dir:
        return
    log_path = os.path.join(versions_dir, LOG_FILENAME)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message_short};\n"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def calculate_file_hash(filepath):
    """Calculate MD5 hash of a file"""
    if not os.path.exists(filepath):
        return None
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def get_latest_version_file(main_filepath):
    """Get the most recent version file"""
    if not main_filepath:
        return None
    versions_dir = os.path.join(os.path.dirname(main_filepath), "versions")
    if not os.path.exists(versions_dir):
        return None
    blends = [f for f in os.listdir(versions_dir) if f.endswith('.blend')]
    if not blends:
        return None
    blends.sort(key=lambda f: os.path.getmtime(os.path.join(versions_dir, f)), reverse=True)
    return os.path.join(versions_dir, blends[0])


def save_current_file_copy(main_filepath):
    """Copy the current main .blend to versions/ with incremental naming"""
    if not main_filepath or not os.path.exists(main_filepath):
        return None
    directory = os.path.dirname(main_filepath)
    filename = os.path.basename(main_filepath)
    base, ext = os.path.splitext(filename)
    versions_dir = ensure_versions_dir(main_filepath)
    if not versions_dir:
        return None
    existing = [f for f in os.listdir(versions_dir) if f.startswith(base + "_v") and f.endswith(ext)]
    existing.sort()
    version_count = len(existing)
    new_name = f"{base}_v{version_count + 1:03d}{ext}"
    dest = os.path.join(versions_dir, new_name)
    try:
        shutil.copy2(main_filepath, dest)
        append_log_compact(main_filepath, f"Versioning created: {os.path.basename(dest)}")
        return dest
    except Exception:
        return None


def try_operator_find_missing(textures_root):
    """Try to use Blender's built-in find missing files operator"""
    if not os.path.exists(textures_root):
        return False
    try:
        bpy.ops.image.find_missing_files(directory=textures_root)
        return True
    except Exception:
        return False


def manual_relink_images(main_filepath, textures_root):
    """Manually relink missing image files"""
    fixed = 0
    not_found = []
    if not main_filepath or not os.path.exists(textures_root):
        return fixed, not_found

    candidates = {}
    for root, _, files in os.walk(textures_root):
        for f in files:
            lower_f = f.lower()
            if any(lower_f.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.tga', '.exr', '.tif', '.bmp', '.hdr', '.webp']):
                candidates.setdefault(lower_f, []).append(os.path.join(root, f))

    main_dir = os.path.dirname(main_filepath)

    for img in bpy.data.images:
        if img.name in ('Render Result', 'Viewer Node'):
            continue
        
        if img.packed_file is not None:
            continue
        if not img.filepath:
            continue

        abs_path = bpy.path.abspath(img.filepath)
        if os.path.exists(abs_path):
            continue

        base_name = os.path.basename(abs_path).lower()
        found_path = None
        
        if base_name in candidates:
            found_path = candidates[base_name][0]
        else:
            name_no_ext, ext = os.path.splitext(base_name)
            import re
            m = re.match(r"^(.*)\.\d{3,4}$", name_no_ext)
            if m:
                candidate_base = m.group(1) + ext
                if candidate_base in candidates:
                    found_path = candidates[candidate_base][0]
            
            if not found_path:
                for cand_name, paths in candidates.items():
                    if name_no_ext in cand_name:
                        found_path = paths[0]
                        break

        if found_path and os.path.exists(found_path):
            rel = os.path.relpath(found_path, start=main_dir).replace("\\", "/")
            rel_prefixed = "//" + rel
            try:
                img.filepath = rel_prefixed
                try:
                    img.reload()
                except Exception:
                    pass
                fixed += 1
            except Exception:
                not_found.append(img.name)
        else:
            not_found.append(img.name)

    return fixed, not_found


class FILE_OT_SaveVersion(bpy.types.Operator):
    """Create a version copy of current .blend file"""
    bl_idname = "file.save_version"
    bl_label = "Create Version"
    bl_description = "Create version copy of current .blend into versions/ folder"
    bl_options = {'REGISTER'}

    def execute(self, context):
        main_fp = bpy.data.filepath
        if not main_fp:
            self.report({'ERROR'}, "Main file is not saved. Please save first.")
            return {'CANCELLED'}
        
        current_dir = os.path.dirname(main_fp)
        parent_dir = os.path.dirname(current_dir)
        
        if os.path.basename(current_dir) == "versions":
            self.report({'ERROR'}, "Cannot create version from a version file! Open the original file instead.")
            return {'CANCELLED'}
        
        if "versions" + os.sep in main_fp or main_fp.endswith(os.sep + "versions"):
            self.report({'ERROR'}, "Cannot create version from a version file! Open the original file instead.")
            return {'CANCELLED'}
        
        dest = save_current_file_copy(main_fp)
        if dest:
            self.report({'INFO'}, f"Saved version: {os.path.basename(dest)}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to create version copy.")
            return {'CANCELLED'}


class FILE_OT_RestoreVersion(bpy.types.Operator):
    """Restore selected version by copying it over the main file"""
    bl_idname = "file.restore_version"
    bl_label = "Restore Selected Version"
    bl_description = "Restore selected version by copying its .blend over the main file, then relink textures"
    bl_options = {'REGISTER'}

    def execute(self, context):
        main_fp = bpy.data.filepath
        if not main_fp:
            self.report({'ERROR'}, "Main file is not saved.")
            return {'CANCELLED'}

        selected = context.scene.selected_version
        if not selected or selected == 'NONE':
            self.report({'ERROR'}, "No version selected.")
            return {'CANCELLED'}

        directory = os.path.dirname(main_fp)
        versions_dir = os.path.join(directory, "versions")
        source = os.path.join(versions_dir, selected)
        destination = main_fp

        if not os.path.exists(source):
            self.report({'ERROR'}, f"Version file not found: {selected}")
            return {'CANCELLED'}

        latest = get_latest_version_file(main_fp)
        skip_copy = False
        if latest and os.path.exists(latest):
            try:
                main_mtime = os.path.getmtime(main_fp)
                latest_mtime = os.path.getmtime(latest)
                if latest_mtime >= main_mtime:
                    skip_copy = True
                else:
                    main_hash = calculate_file_hash(main_fp)
                    latest_hash = calculate_file_hash(latest)
                    if main_hash is not None and main_hash == latest_hash:
                        skip_copy = True
            except Exception:
                skip_copy = False

        if not skip_copy:
            backup = save_current_file_copy(main_fp)
            if backup:
                self.report({'INFO'}, f"Backup created: {os.path.basename(backup)}")
            else:
                self.report({'WARNING'}, "Failed to create backup before restore; proceeding.")

        try:
            shutil.copy2(source, destination)
            sstat = os.stat(source)
            os.utime(destination, (sstat.st_atime, sstat.st_mtime))
            append_log_compact(main_fp, f"Restore created: {os.path.basename(source)}")
        except Exception as e:
            self.report({'ERROR'}, f"Restore failed: {e}")
            return {'CANCELLED'}

        try:
            bpy.ops.wm.revert_mainfile()
        except Exception:
            pass

        # Auto-fix textures from ./textures folder
        textures_root_abs = os.path.join(directory, "textures")
        ran_op = try_operator_find_missing(textures_root_abs)

        fixed = 0
        not_found = []

        if not ran_op:
            fixed, not_found = manual_relink_images(destination, textures_root_abs)
        else:
            mfixed, mnotfound = manual_relink_images(destination, textures_root_abs)
            fixed += mfixed
            not_found.extend(mnotfound)

        # Reload all images
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            try:
                img.reload()
            except Exception:
                pass

        # Auto-reload all linked libraries
        reloaded_libs = 0
        for lib in bpy.data.libraries:
            try:
                lib.reload()
                reloaded_libs += 1
            except Exception as e:
                # Library might be missing or broken, skip silently
                pass

        if reloaded_libs > 0:
            self.report({'INFO'}, f"Restored: {os.path.basename(source)} | Textures: {fixed} | Libraries: {reloaded_libs}")
        else:
            self.report({'INFO'}, f"Restored: {os.path.basename(source)} (textures fixed: {fixed})")
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FILE_OT_SaveVersion)
    bpy.utils.register_class(FILE_OT_RestoreVersion)
    
    bpy.types.Scene.selected_version = bpy.props.EnumProperty(
        name="Select Version",
        description="Choose a version to restore",
        items=get_version_list
    )


def unregister():
    bpy.utils.unregister_class(FILE_OT_RestoreVersion)
    bpy.utils.unregister_class(FILE_OT_SaveVersion)
    
    try:
        del bpy.types.Scene.selected_version
    except Exception:
        pass
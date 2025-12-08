"""
Asset Publishing System with Linked Library Support

This module provides a comprehensive publishing workflow for Blender assets:
- Pre-publish validation with Force Publish option
- Automatic versioning (overwrite/increment modes)
- Linked library management with structure mirroring
- Texture consolidation and validation
- Clean delivery structure with centralized logging

Author: Rizqi Alfajri
Version: 1.5.0
Date: November 17, 2025
"""

import bpy
import os
import shutil
import glob
import re
from datetime import datetime
import getpass
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, EnumProperty
from bpy.types import PropertyGroup


# =============================================================================
# DATA CLASSES & PROPERTY GROUPS
# =============================================================================

class LibrarySelectionItem(PropertyGroup):
    """Property group for storing linked library info in UI"""
    name: StringProperty(name="Library Name")
    filepath: StringProperty(name="File Path", subtype='FILE_PATH')
    structure: StringProperty(name="Publish Structure")
    selected: BoolProperty(name="Include in Publish", default=True)
    depth: IntProperty(name="Nesting Depth", default=0)
    status: StringProperty(name="Validation Status", default="")
    folder_name: StringProperty(name="Folder Name")
    has_textures: BoolProperty(name="Has Textures", default=False)


# =============================================================================
# UTILITY CLASSES
# =============================================================================

class PathResolver:
    """Resolve publish paths from linked library relative paths"""
    
    def __init__(self, publish_root):
        self.publish_root = os.path.normpath(publish_root)
        self.master_root = None
    
    def detect_master_root(self, current_file_path):
        """Detect master root folder that contains the assets folder"""
        if not current_file_path:
            return None
        
        current_dir = os.path.dirname(current_file_path)
        current_dir = os.path.normpath(current_dir)
        
        check_dir = current_dir
        max_levels = 10
        
        for _ in range(max_levels):
            assets_folder = os.path.join(check_dir, "assets")
            
            if os.path.exists(assets_folder) and os.path.isdir(assets_folder):
                return os.path.normpath(check_dir)
            
            parent = os.path.dirname(check_dir)
            
            if parent == check_dir:
                break
            
            check_dir = parent
        
        return None
    
    def extract_structure_from_link(self, library_filepath):
        """Extract publish structure from Blender library link path"""
        lib_absolute = bpy.path.abspath(library_filepath)
        lib_absolute = os.path.normpath(lib_absolute)
        
        filename = os.path.basename(lib_absolute)
        
        if library_filepath.startswith('//'):
            lib_relative = library_filepath[2:]  
            lib_relative = lib_relative.replace('\\', '/') 
            
            parts = [p for p in lib_relative.split('/') if p and p != '..']
            
            if len(parts) > 1:
                structure = '/'.join(parts[:-1])
            else:
                structure = ''
        else:
            if self.master_root:
                assets_folder = os.path.join(self.master_root, "assets")
                try:
                    rel_from_assets = os.path.relpath(lib_absolute, assets_folder)
                    rel_from_assets = os.path.normpath(rel_from_assets)
                    
                    if not rel_from_assets.startswith('..'):
                        parts = rel_from_assets.split(os.sep)
                        structure = '/'.join(parts[:-1]) if len(parts) > 1 else ''
                    else:
                        lib_dir = os.path.dirname(lib_absolute)
                        parts = lib_dir.split(os.sep)
                        structure = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else (parts[-1] if parts else '')
                except ValueError:
                    lib_dir = os.path.dirname(lib_absolute)
                    parts = lib_dir.split(os.sep)
                    structure = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else (parts[-1] if parts else '')
            else:
                lib_dir = os.path.dirname(lib_absolute)
                parts = lib_dir.split(os.sep)
                structure = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else (parts[-1] if parts else '')
        
        publish_path = os.path.join(self.publish_root, structure, filename)
        publish_path = os.path.normpath(publish_path)
        
        textures_dir = os.path.join(os.path.dirname(lib_absolute), 'textures')
        folder_name = os.path.basename(os.path.dirname(lib_absolute))
        
        return {
            'absolute': lib_absolute,
            'structure': structure,
            'filename': filename,
            'publish_path': publish_path,
            'textures_dir': textures_dir,
            'folder_name': folder_name
        }
    
    def get_current_file_structure(self, current_file_path, publish_structure=None):
        """Get publish structure for current file using master root detection"""
        if not self.master_root:
            self.master_root = self.detect_master_root(current_file_path)
        
        if publish_structure:
            structure = publish_structure
        else:
            if self.master_root:
                try:
                    assets_folder = os.path.join(self.master_root, "assets")
                    rel_from_assets = os.path.relpath(current_file_path, assets_folder)
                    rel_from_assets = os.path.normpath(rel_from_assets)
                    
                    parts = rel_from_assets.split(os.sep)[:-1]
                    structure = '/'.join(parts) if parts else ''
                    
                except ValueError:
                    file_dir = os.path.dirname(current_file_path)
                    parent_folder = os.path.basename(file_dir)
                    grandparent_folder = os.path.basename(os.path.dirname(file_dir))
                    structure = f"{grandparent_folder}/{parent_folder}"
            else:
                file_dir = os.path.dirname(current_file_path)
                parent_folder = os.path.basename(file_dir)
                grandparent_folder = os.path.basename(os.path.dirname(file_dir))
                structure = f"{grandparent_folder}/{parent_folder}"
        
        filename = os.path.basename(current_file_path)
        publish_folder = os.path.join(self.publish_root, structure)
        
        return {
            'structure': structure,
            'filename': filename,
            'publish_folder': os.path.normpath(publish_folder),
            'textures_dir': os.path.join(os.path.dirname(current_file_path), 'textures')
        }
    
    def get_version_filename(self, filename, version_number):
        """Get versioned filename (e.g. house.blend -> house_v003.blend)"""
        name, ext = os.path.splitext(filename)
        return f"{name}_v{version_number:03d}{ext}"


class CircularDependencyError(Exception):
    """Custom exception for circular library dependencies"""
    pass


class LinkedLibraryScanner:
    """Scan and validate linked libraries recursively (max depth: 3 levels)"""
    
    def __init__(self, publish_root, max_depth=3):
        self.publish_root = publish_root
        self.max_depth = max_depth
        self.visited = set()
        self.libraries = []
        self.path_resolver = PathResolver(publish_root)
    
    def scan(self, current_depth=0):
        """Scan linked libraries from current open file"""
        if current_depth >= self.max_depth:
            return self.libraries
        
        current_file = bpy.data.filepath
        if not current_file:
            return self.libraries
        
        current_file = os.path.normpath(current_file)
        
        if current_file in self.visited:
            raise CircularDependencyError(f"Circular dependency: {current_file}")
        
        self.visited.add(current_file)
        
        for lib in bpy.data.libraries:
            lib_info = self.path_resolver.extract_structure_from_link(lib.filepath)
            
            if not lib_info:
                continue
            
            lib_info['exists'] = os.path.exists(lib_info['absolute'])
            lib_info['has_textures'] = os.path.exists(lib_info['textures_dir'])
            lib_info['depth'] = current_depth + 1
            lib_info['library_name'] = lib.name
            
            self.libraries.append(lib_info)
        
        return self.libraries
    
    def scan_recursive(self, blend_file_path, current_depth=0):
        """Recursively scan nested libraries (requires opening files - slow)"""
        pass


# =============================================================================
# MAIN PUBLISHING OPERATOR
# =============================================================================

class ASSET_OT_Publish(bpy.types.Operator):
    """Publish asset to production folder with clean textures"""
    bl_idname = "asset.publish"
    bl_label = "Publish Asset"
    bl_description = "Publish asset with validated textures, purged data, and optional versioning"
    bl_options = {'REGISTER'}
    
    asset_name = ""
    blend_file = ""
    textures_to_copy = []
    validation_errors = []
    validation_warnings = []
    files_to_remove = []
    is_forced = False
    libraries_to_publish = []
    
    def write_publish_log(self, publish_path, asset_path, target_path, texture_count, status, notes=""):
        """Write to centralized publish log"""
        log_file = os.path.join(publish_path, ".publish_activity.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        mode = bpy.context.scene.publish_versioning_mode
        
        log_entry = (
            f"[{timestamp}] PUBLISH | "
            f"Asset: {self.asset_name} | "
            f"Path: {target_path} | "
            f"Source: {asset_path} | "
            f"User: {username} | "
            f"Mode: {mode} | "
            f"Textures: {texture_count} | "
            f"Status: {status}"
        )
        if notes:
            log_entry += f" | Notes: {notes}"
        log_entry += "\n"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Warning: Could not write to log: {e}")
    
    def get_asset_name(self):
        """Get asset name from parent folder of .blend file"""
        if not bpy.data.filepath:
            return None
        blend_dir = os.path.dirname(bpy.data.filepath)
        return os.path.basename(blend_dir)
    
    def validate_publish(self, context):
        """Validate asset is ready for publish"""
        self.validation_errors = []
        self.validation_warnings = []
        
        if not bpy.data.filepath:
            self.validation_errors.append("File must be saved first")
            return False
        
        publish_path = context.scene.publish_path
        if not publish_path or not publish_path.strip():
            self.validation_errors.append("Publish path not set. Set path in Publish panel first")
            return False
        
        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")
        
        if not os.path.exists(textures_dir):
            self.validation_warnings.append("Textures folder not found (will publish without textures)")
            return len(self.validation_errors) == 0
        
        external_textures = []
        missing_textures = []
        packed_textures = []
        
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source != 'FILE':
                continue
            
            if img.packed_file:
                packed_textures.append(img.name)
                continue
            
            if not img.filepath_raw:
                continue
            
            abs_path = bpy.path.abspath(img.filepath_raw)
            
            if not os.path.exists(abs_path):
                missing_textures.append(img.name)
                continue
            
            try:
                if os.path.commonpath([abs_path, textures_dir]) != textures_dir:
                    external_textures.append(img.name)
            except ValueError:
                external_textures.append(img.name)
        
        if missing_textures:
            self.validation_warnings.append(f"Missing textures ({len(missing_textures)}): {', '.join(missing_textures[:3])}")
        
        if external_textures:
            self.validation_warnings.append(f"External textures found ({len(external_textures)}). Will copy only local textures")
        
        if packed_textures:
            self.validation_warnings.append(f"Packed textures ({len(packed_textures)}) - will remain packed in published file")
        
        return len(self.validation_errors) == 0
    
    def get_used_textures(self):
        """Get list of textures actually used in the blend file"""
        used_textures = set()
        
        def normalize_udim(path):
            """Match Blender's UDIM detection: any 4-digit number in standard range (1001-1100)"""
            udim_pattern = r'\b(\d{4})\b'
            match = re.search(udim_pattern, path)
            
            if match:
                tile_num = int(match.group(1))
                if 1001 <= tile_num <= 1100:
                    return path.replace(match.group(1), '<UDIM>', 1)
            
            return path
        
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source != 'FILE':
                continue
            if img.packed_file:
                continue
            
            try:
                abs_path = bpy.path.abspath(img.filepath)
                norm_path = os.path.normpath(abs_path)
                norm_path = normalize_udim(norm_path)
                used_textures.add(norm_path)
            except Exception:
                continue
        
        return used_textures
    
    def scan_textures_folder(self, textures_dir):
        """Scan textures folder recursively and categorize files"""
        IMAGE_EXTENSIONS = {
            'png', 'jpg', 'jpeg', 'tga', 'bmp', 'tiff', 'webp', 'exr', 'hdr', 'dds',
            'psd', 'svg', 'gif',
        }
        
        all_files = []
        for root, dirs, files in os.walk(textures_dir):
            # Skip hidden folders (.backup, .trash)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                ext = file.rsplit('.', 1)[-1].lower() if '.' in file else ''
                if ext in IMAGE_EXTENSIONS:
                    all_files.append(os.path.join(root, file))
        
        used_textures = self.get_used_textures()
        
        textures_to_copy = []
        unused_files = []
        
        def normalize_udim(path):
            """Match Blender's UDIM detection: any 4-digit number in standard range (1001-1100)"""
            udim_pattern = r'\b(\d{4})\b'
            match = re.search(udim_pattern, path)
            
            if match:
                tile_num = int(match.group(1))
                if 1001 <= tile_num <= 1100:
                    return path.replace(match.group(1), '<UDIM>', 1)
            
            return path
        
        for file_path in all_files:
            norm_path = os.path.normpath(file_path)
            norm_path = normalize_udim(norm_path)
            
            if norm_path in used_textures:
                textures_to_copy.append(file_path)
            else:
                unused_files.append(file_path)
        
        return textures_to_copy, unused_files
    
    def get_target_path(self, context):
        """Get target publish path with versioning"""
        publish_path = context.scene.publish_path
        base_path = os.path.join(publish_path, self.asset_name)
        
        if context.scene.publish_versioning_mode == 'OVERWRITE':
            return base_path
        
        version_num = 1
        while True:
            versioned_path = f"{base_path}_v{version_num:03d}"
            if not os.path.exists(versioned_path):
                return versioned_path
            version_num += 1
    
    def relink_external_libraries(self, blend_file_path, published_libraries, publish_root, context):
        """Relink external libraries in published blend file to use new relative paths"""
        try:
            from bpy_extras import blendfile
            
            relinked_count = 0
            
            lib_path_map = {}
            for lib in published_libraries:
                if lib['structure'].startswith('_external'):
                    lib_name = lib['name']  
                    new_path = lib['path']   
                    lib_path_map[lib_name] = new_path
                    print(f"External lib to relink: {lib_name} → {new_path}")
            
            if not lib_path_map:
                print("No external libraries to relink")
                return 0
            
            print(f"\nRelinking libraries in: {blend_file_path}")
            published_file_dir = os.path.dirname(blend_file_path)
            
            with blendfile.open_blend(blend_file_path, mode='r+b') as blend:
                for block in blend.blocks:
                    if block.code == b'LI':
                        lib_data = block.get_pointer(b'name')
                        if lib_data:
                            lib_name_bytes = lib_data[0]
                            lib_filepath_bytes = block.get_pointer(b'filepath')
                            
                            if lib_filepath_bytes:
                                old_path = lib_filepath_bytes[0].decode('utf-8', errors='ignore')
                                old_abs = bpy.path.abspath(old_path) if old_path.startswith('//') else old_path
                                lib_folder_name = os.path.basename(os.path.dirname(old_abs))
                                
                                if lib_folder_name in lib_path_map:
                                    new_abs_path = lib_path_map[lib_folder_name]
                                    
                                    try:
                                        rel_path = os.path.relpath(new_abs_path, published_file_dir)
                                        blender_rel_path = "//" + rel_path.replace("\\", "/")
                                        new_path_bytes = blender_rel_path.encode('utf-8')
                                        block.set_pointer(b'filepath', [new_path_bytes])
                                        relinked_count += 1
                                        print(f"✓ Relinked: {lib_folder_name}")
                                        print(f"    Old: {old_path}")
                                        print(f"    New: {blender_rel_path}")
                                        
                                    except ValueError:
                                        new_path_bytes = new_abs_path.encode('utf-8')
                                        block.set_pointer(b'filepath', [new_path_bytes])
                                        relinked_count += 1
                                        print(f"✓ Relinked (absolute): {lib_folder_name}")
            
            print(f"\n✓ Relinked {relinked_count} external libraries (low-level edit)")
            return relinked_count
            
        except ImportError:
            print("⚠ Low-level blendfile library not available, using fallback method")
            return self._relink_by_opening_file(blend_file_path, published_libraries, publish_root, context)
            
        except Exception as e:
            print(f"⚠ Warning: Failed to relink libraries: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _relink_by_opening_file(self, blend_file_path, published_libraries, publish_root, context):
        try:
            import bpy
            
            relinked_count = 0
            lib_path_map = {}
            
            for lib in published_libraries:
                if lib['structure'].startswith('_external'):
                    lib_path_map[lib['name']] = lib['path']
            
            if not lib_path_map:
                return 0
            
            current_file = bpy.data.filepath
            
            print(f"Opening file for relink (fallback method): {blend_file_path}")
            bpy.ops.wm.open_mainfile(filepath=blend_file_path)
            
            published_file_dir = os.path.dirname(blend_file_path)
            for lib in bpy.data.libraries:
                lib_folder_name = os.path.basename(os.path.dirname(bpy.path.abspath(lib.filepath)))
                
                if lib_folder_name in lib_path_map:
                    new_abs_path = lib_path_map[lib_folder_name]
                    
                    try:
                        rel_path = os.path.relpath(new_abs_path, published_file_dir)
                        blender_rel_path = "//" + rel_path.replace("\\", "/")
                        lib.filepath = blender_rel_path
                        relinked_count += 1
                    except ValueError:
                        lib.filepath = new_abs_path
                        relinked_count += 1
            
            bpy.ops.wm.save_mainfile(filepath=blend_file_path)
            if current_file:
                bpy.ops.wm.open_mainfile(filepath=current_file)
            
            return relinked_count
            
        except Exception as e:
            print(f"Fallback relink failed: {e}")
            try:
                if current_file:
                    bpy.ops.wm.open_mainfile(filepath=current_file)
            except:
                pass
            return 0
    
    def publish_master_file(self, source_path, target_folder, context):
        """Publish master file with versioning support (overwrite or increment)"""
        os.makedirs(target_folder, exist_ok=True)
        
        base_filename = os.path.basename(source_path)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        if context.scene.publish_versioning_mode == 'VERSIONING':
            version_num = 1
            while True:
                versioned_name = f"{name_without_ext}_v{version_num:03d}.blend"
                versioned_path = os.path.join(target_folder, versioned_name)
                if not os.path.exists(versioned_path):
                    published_path = versioned_path
                    break
                version_num += 1
            
            self.copy_blend_file_with_cleanup(source_path, published_path)
            
            if context.scene.publish_sync_to_master:
                master_path = os.path.join(target_folder, base_filename)
                self.copy_blend_file_with_cleanup(source_path, master_path)
                print(f"✓ Auto-synced to master: {master_path}")
        else:
            published_path = os.path.join(target_folder, base_filename)
            self.copy_blend_file_with_cleanup(source_path, published_path)
        
        return published_path
    
    def publish_linked_library(self, lib_info, context):
        """Publish linked library with structure mirroring"""
        source_path = lib_info['filepath']
        publish_root = context.scene.publish_path
        structure = lib_info.get('structure', '')
        folder_name = lib_info.get('folder_name', os.path.basename(os.path.dirname(source_path)))
        
        target_folder = os.path.join(publish_root, structure)
        os.makedirs(target_folder, exist_ok=True)
        
        base_filename = os.path.basename(source_path)
        target_path = os.path.join(target_folder, base_filename)
        shutil.copy2(source_path, target_path)
        
        print(f"Published library: {folder_name}")
        print(f"  Source: {source_path}")
        print(f"  Target: {target_path}")
        print(f"  Structure: {structure}")
        
        return target_path
    
    def copy_blend_file_with_cleanup(self, source_path, target_path):
        """
        Copy .blend file and purge orphan data.
        
        Args:
            source_path: Source .blend file
            target_path: Destination .blend file
        """
        shutil.copy2(source_path, target_path)
    
    def copy_library_textures(self, lib_info, target_folder):
        """Copy textures folder with subdirectories (skips hidden folders)"""
        source_lib_dir = os.path.dirname(lib_info['filepath'])
        source_textures_dir = os.path.join(source_lib_dir, 'textures')
        
        if not os.path.exists(source_textures_dir):
            print(f"  No textures folder for {lib_info.get('folder_name', 'library')}")
            return
        
        target_textures_dir = os.path.join(target_folder, 'textures')
        os.makedirs(target_textures_dir, exist_ok=True)
        
        copied_count = 0
        for root, dirs, files in os.walk(source_textures_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            rel_path = os.path.relpath(root, source_textures_dir)
            
            if rel_path == '.':
                target_dir = target_textures_dir
            else:
                target_dir = os.path.join(target_textures_dir, rel_path)
                os.makedirs(target_dir, exist_ok=True)
            
            for filename in files:
                if filename.startswith('.'):
                    continue
                
                source_file = os.path.join(root, filename)
                target_file = os.path.join(target_dir, filename)
                shutil.copy2(source_file, target_file)
                copied_count += 1
        
        print(f"  Copied {copied_count} textures")
        return copied_count
    
    def invoke(self, context, event):
        if not context.scene.publish_check_done:
            self.report({'ERROR'}, "Run 'Check Publish' first to validate asset readiness")
            return {'CANCELLED'}
        
        if context.scene.publish_is_published_file:
            self.report({'ERROR'}, "Cannot publish from publish directory! Open the source file instead.")
            return {'CANCELLED'}
        
        self.asset_name = self.get_asset_name()
        if not self.asset_name:
            self.report({'ERROR'}, "Could not determine asset name")
            return {'CANCELLED'}
        
        validation_passed = self.validate_publish(context)
        self.is_forced = context.scene.publish_force
        
        if not validation_passed and not self.is_forced:
            return context.window_manager.invoke_props_dialog(self, width=500)
        
        if self.is_forced and self.validation_warnings:
            pass
        
        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")
        
        if os.path.exists(textures_dir):
            self.textures_to_copy, unused_files = self.scan_textures_folder(textures_dir)
        else:
            self.textures_to_copy = []
            unused_files = []
        
        self.files_to_remove = []
        if os.path.exists(textures_dir):
            backup_dir = os.path.join(textures_dir, ".backup")
            trash_dir = os.path.join(textures_dir, ".trash")
            
            if os.path.exists(backup_dir):
                self.files_to_remove.append(".backup folder")
            if os.path.exists(trash_dir):
                self.files_to_remove.append(".trash folder")
        
        if unused_files:
            self.files_to_remove.extend([f"Unused: {os.path.basename(f)}" for f in unused_files[:5]])
            if len(unused_files) > 5:
                self.files_to_remove.append(f"... and {len(unused_files) - 5} more unused files")
        
        self.libraries_to_publish = []
        
        if context.scene.publish_include_libraries:
            for item in context.scene.publish_library_selection:
                if item.selected:
                    lib_info = {
                        'filepath': item.filepath,
                        'structure': item.structure,
                        'folder_name': item.folder_name,
                        'has_textures': item.has_textures,
                        'status': item.status
                    }
                    self.libraries_to_publish.append(lib_info)
            
            print(f"\nLibraries to publish: {len(self.libraries_to_publish)}")
            for lib in self.libraries_to_publish:
                print(f"  - {lib['folder_name']} ({lib['structure']})")
        
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        
        if self.validation_errors:
            box = layout.box()
            box.alert = True
            box.label(text="🚫 CRITICAL ERRORS (Cannot Force):", icon='ERROR')
            for error in self.validation_errors:
                box.label(text=f"  • {error}", icon='BLANK1')
            layout.separator()
            layout.label(text="Fix these errors first", icon='INFO')
            return
        
        if self.validation_warnings:
            box = layout.box()
            box.alert = True
            box.label(text="⚠️ WARNINGS:", icon='ERROR')
            for warning in self.validation_warnings:
                box.label(text=f"  • {warning}", icon='BLANK1')
            
            if self.is_forced:
                force_box = layout.box()
                force_box.alert = True
                force_box.label(text="🚨 FORCE PUBLISH ACTIVE", icon='ERROR')
            
            layout.separator()
        
        box = layout.box()
        box.label(text="� Asset Publish Info", icon='ASSET_MANAGER')
        
        col = box.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False
        col.scale_y = 0.85
        
        row = col.row(align=True)
        row.label(text="Asset Name:")
        row.label(text=self.asset_name)
        
        row = col.row(align=True)
        row.label(text="File Name:")
        row.label(text=os.path.basename(bpy.data.filepath))
        
        row = col.row(align=True)
        row.label(text="Publish Path:")
        row.label(text=context.scene.publish_path)
        
        target_path = self.get_target_path(context)
        target_folder = os.path.basename(target_path).replace('.blend', '')
        
        # For include libraries, show parent folder like single publish
        if self.libraries_to_publish:
            current_folder = os.path.dirname(bpy.data.filepath)
            parent_folder_name = os.path.basename(current_folder)
            target_folder = parent_folder_name
        
        row = col.row(align=True)
        row.label(text="Target Folder:")
        row.label(text=target_folder)
        
        layout.separator()
        
        box = layout.box()
        box.label(text="📦 Files Summary", icon='FILEBROWSER')
        
        split = box.split(factor=0.5)
        
        col_send = split.column(align=True)
        
        total_files = 1 + len(self.textures_to_copy)
        if self.libraries_to_publish:
            total_files += len(self.libraries_to_publish)
        
        col_send.label(text=f"✅ Will Send ({total_files}):", icon='CHECKMARK')
        
        inner_col = col_send.column(align=True)
        inner_col.use_property_split = True
        inner_col.use_property_decorate = False
        inner_col.scale_y = 0.8
        
        row = inner_col.row(align=True)
        row.label(text="Blend File:")
        row.label(text=os.path.basename(bpy.data.filepath))
        
        if self.textures_to_copy:
            inner_col.separator(factor=0.3)
            inner_col.label(text="Textures:")
            for tex_path in self.textures_to_copy[:5]:
                tex_name = os.path.basename(tex_path)
                tex_display = tex_name if len(tex_name) < 30 else tex_name[:27] + "..."
                row = inner_col.row(align=True)
                row.label(text="  " + tex_display, icon='TEXTURE')
            
            if len(self.textures_to_copy) > 5:
                row = inner_col.row(align=True)
                row.label(text=f"  ... and {len(self.textures_to_copy) - 5} more", icon='BLANK1')
        
        if self.libraries_to_publish:
            inner_col.separator(factor=0.3)
            row = inner_col.row(align=True)
            row.label(text="Libraries:")
            row.label(text=f"{len(self.libraries_to_publish)} files")
        
        col_exclude = split.column(align=True)
        
        if self.files_to_remove:
            col_exclude.label(text=f"🗑️ Will NOT Send ({len(self.files_to_remove)}):", icon='TRASH')
            
            inner_col2 = col_exclude.column(align=True)
            inner_col2.scale_y = 0.8
            
            for item in self.files_to_remove[:5]:
                item_display = item if len(item) < 35 else item[:32] + "..."
                row = inner_col2.row(align=True)
                row.label(text="  " + item_display, icon='BLANK1')
            
            if len(self.files_to_remove) > 5:
                inner_col2.separator(factor=0.2)
                row = inner_col2.row(align=True)
                row.label(text=f"  ... and {len(self.files_to_remove) - 5} more", icon='BLANK1')
        
        layout.separator()
        
        if self.libraries_to_publish:
            box = layout.box()
            box.label(text=f"🔗 Linked Libraries ({len(self.libraries_to_publish)}):", icon='LINKED')
            
            for lib_info in self.libraries_to_publish[:4]:
                lib_name = lib_info['folder_name']
                lib_structure = lib_info['structure']
                box.label(text=f"  → {lib_name}", icon='FILE_BLEND')
                
                row = box.row()
                row.scale_y = 0.7
                row.label(text=f"     Structure: {lib_structure}", icon='BLANK1')
            
            if len(self.libraries_to_publish) > 4:
                box.label(text=f"  ... and {len(self.libraries_to_publish) - 4} more libraries", icon='BLANK1')
        
        layout.separator()
        
        if context.scene.publish_versioning_mode == 'VERSIONING':
            box = layout.box()
            box.label(text="🔄 Versioning Options:", icon='FILE_REFRESH')
            
            row = box.row()
            row.prop(context.scene, "publish_sync_to_master", text="Auto-sync to Master", icon='LINKED')
            
            info_col = box.column(align=True)
            info_col.scale_y = 0.7
            if context.scene.publish_sync_to_master:
                info_col.label(text=f"✓ Will also update master file (without _v suffix)", icon='BLANK1')
                info_col.label(text=f"✓ Master = {self.asset_name}.blend", icon='BLANK1')
            else:
                info_col.label(text="ℹ Version and master files will be independent", icon='BLANK1')
            
            layout.separator()
        
        layout.label(text="⚠️ Asset will be cleaned before publish:", icon='INFO')
        layout.label(text="  • Orphan data will be purged", icon='BLANK1')
        layout.label(text="  • File will be saved", icon='BLANK1')
        
        if self.libraries_to_publish:
            layout.label(text="  • Linked libraries will be published", icon='BLANK1')
    
    def execute(self, context):
        if self.validation_errors:
            self.report({'ERROR'}, "Cannot publish: fix critical errors first")
            return {'CANCELLED'}
        
        try:
            publish_path = context.scene.publish_path
            
            if not os.path.exists(publish_path):
                try:
                    os.makedirs(publish_path, exist_ok=True)
                    self.report({'INFO'}, f"Created publish directory: {publish_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Cannot create publish path: {str(e)}")
                    return {'CANCELLED'}
            
            self.report({'INFO'}, "Cleaning blend file...")
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            bpy.ops.wm.save_mainfile()
            
            current_file = bpy.data.filepath
            current_folder = os.path.dirname(current_file)
            current_filename = os.path.basename(current_file)
            
            current_file_normalized = os.path.abspath(os.path.normpath(current_file))
            
            internal_lib_paths = [current_file_normalized]
            
            current_drive = os.path.splitdrive(current_file_normalized)[0]
            for lib_info in self.libraries_to_publish:
                lib_filepath = lib_info['filepath']
                lib_filepath_normalized = os.path.abspath(os.path.normpath(lib_filepath))
                lib_drive = os.path.splitdrive(lib_filepath_normalized)[0]
                
                if lib_drive == current_drive:
                    internal_lib_paths.append(lib_filepath_normalized)
            
            if len(internal_lib_paths) > 1:
                try:
                    common_root = os.path.commonpath(internal_lib_paths)
                except ValueError:
                    common_root = os.path.dirname(current_file_normalized)
            else:
                common_root = os.path.dirname(current_file_normalized)
            
            rel_path = os.path.relpath(current_file_normalized, common_root)
            master_structure = os.path.dirname(rel_path)
            
            # For single publish (no libraries), add asset folder level
            if not self.libraries_to_publish or len(self.libraries_to_publish) == 0:
                asset_folder_name = os.path.basename(current_folder)
                
                if not master_structure or master_structure == '.':
                    master_structure = asset_folder_name
                elif not master_structure.endswith(asset_folder_name):
                    master_structure = os.path.join(master_structure, asset_folder_name)
            
            master_target_folder = os.path.join(publish_path, master_structure)
            master_textures_dir = os.path.join(current_folder, "textures")
            
            print(f"\nMaster file structure:")
            print(f"  Common root: {common_root}")
            print(f"  Structure: {master_structure}")
            print(f"  Target: {master_target_folder}")
            
            library_count = 0
            if context.scene.publish_include_libraries and self.libraries_to_publish:
                library_count = len(self.libraries_to_publish)
                self.report({'INFO'}, f"Publishing {library_count} linked libraries")
                
                from ..utils.activity_logger import log_activity
                log_activity(
                    "PUBLISH_START",
                    f"Asset: {self.asset_name} | Libraries: {library_count}",
                    context
                )
            
            published_libraries = []
            from ..utils.activity_logger import log_activity
            
            for lib_info in self.libraries_to_publish:
                try:
                    lib_path = self.publish_linked_library(lib_info, context)
                    published_libraries.append({
                        'name': lib_info['folder_name'],
                        'path': lib_path,
                        'structure': lib_info['structure'],
                        'source': lib_info['filepath']
                    })
                    
                    lib_folder = os.path.dirname(lib_path)
                    tex_count = self.copy_library_textures(lib_info, lib_folder)
                    
                    self.report({'INFO'}, f"Published library: {lib_info['folder_name']}")
                    
                    log_activity(
                        "PUBLISH_LIBRARY",
                        f"{lib_info['folder_name']} | Structure: {lib_info['structure']} | Textures: {tex_count} | Status: SUCCESS",
                        context
                    )
                    
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to publish library {lib_info['folder_name']}: {str(e)}")
                    
                    log_activity(
                        "PUBLISH_LIBRARY",
                        f"{lib_info['folder_name']} | Structure: {lib_info['structure']} | Status: FAILED - {str(e)}",
                        context
                    )
            
            published_path = self.publish_master_file(
                source_path=current_file,
                target_folder=master_target_folder,
                context=context
            )
            
            self.report({'INFO'}, f"Published master file: {os.path.basename(published_path)}")
            
            from ..utils.activity_logger import log_activity
            
            target_textures = os.path.join(master_target_folder, "textures")
            os.makedirs(target_textures, exist_ok=True)
            
            copied_count = 0
            if os.path.exists(master_textures_dir) and self.textures_to_copy:
                for tex_path in self.textures_to_copy:
                    # Preserve subfolder structure (wood/, metal/, etc)
                    rel_path = os.path.relpath(tex_path, master_textures_dir)
                    target_tex = os.path.join(target_textures, rel_path)
                    
                    # Create subfolder if needed
                    target_subdir = os.path.dirname(target_tex)
                    os.makedirs(target_subdir, exist_ok=True)
                    
                    shutil.copy2(tex_path, target_tex)
                    copied_count += 1
            elif not os.path.exists(master_textures_dir):
                self.report({'INFO'}, "No textures folder found - publishing without textures")
            
            log_activity(
                "PUBLISH_MASTER",
                f"{os.path.basename(published_path)} | Textures: {copied_count} | Target: {os.path.basename(master_target_folder)}",
                context
            )
            
            if published_libraries:
                relinked_count = self.relink_external_libraries(
                    published_path, 
                    published_libraries, 
                    publish_path,
                    context
                )
                if relinked_count > 0:
                    self.report({'INFO'}, f"Relinked {relinked_count} external libraries")
            
            status = "SUCCESS"
            notes = ""
            
            if self.is_forced and self.validation_warnings:
                status = "SUCCESS (FORCED)"
                notes = f"{len(self.validation_warnings)} warnings ignored"
            
            self.write_publish_log_v2(
                publish_path=publish_path,
                published_path=published_path,
                source_path=current_file,
                texture_count=copied_count,
                linked_libraries=published_libraries,
                status=status,
                notes=notes
            )
            
            force_text = " (FORCED)" if self.is_forced else ""
            lib_text = f" + {len(published_libraries)} libraries" if published_libraries else ""
            
            self.report(
                {'INFO'},
                f"Published {self.asset_name}{force_text}{lib_text} | "
                f"{copied_count} textures | Target: {master_target_folder}"
            )
            
            successful_libs = len(published_libraries)
            total_libs = len(self.libraries_to_publish) if self.libraries_to_publish else 0
            
            if total_libs > 0:
                log_activity(
                    "PUBLISH_COMPLETE",
                    f"Asset: {self.asset_name} | Libraries: {successful_libs}/{total_libs} successful | Status: {status}",
                    context
                )
            else:
                log_activity(
                    "PUBLISH_COMPLETE",
                    f"Asset: {self.asset_name} | Textures: {copied_count} | Status: {status}",
                    context
                )
            
            context.scene.publish_force = False
            context.scene.publish_libraries_validated = False
            
            return {'FINISHED'}
            
        except Exception as e:
            try:
                publish_path = context.scene.publish_path
                self.write_publish_log(
                    publish_path=publish_path,
                    asset_path=os.path.dirname(bpy.data.filepath),
                    target_path="FAILED",
                    texture_count=0,
                    status=f"FAILED - {str(e)}"
                )
            except:
                pass
            
            from ..utils.activity_logger import log_activity
            log_activity(
                "PUBLISH_FAILED",
                f"Asset: {self.asset_name} | Error: {str(e)}",
                context
            )
            
            self.report({'ERROR'}, f"Publish failed: {str(e)}")
            return {'CANCELLED'}
    
    def write_publish_log_v2(self, publish_path, published_path, source_path, 
                            texture_count, linked_libraries, status, notes=""):
        log_file = os.path.join(publish_path, ".publish_activity.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        
        log_entry = (
            f"[{timestamp}] PUBLISH | "
            f"Asset: {self.asset_name} | "
            f"Path: {published_path} | "
            f"Source: {source_path} | "
            f"User: {username} | "
            f"Textures: {texture_count} | "
            f"Linked: {len(linked_libraries)} | "
            f"Status: {status}"
        )
        
        if notes:
            log_entry += f" | Notes: {notes}"
        
        log_entry += "\n"
        
        for lib in linked_libraries:
            log_entry += (
                f"  └─ LINKED | "
                f"Library: {lib['name']} | "
                f"Structure: {lib['structure']} | "
                f"Path: {lib['path']} | "
                f"Source: {lib.get('source', 'Unknown')}\n"
            )
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Warning: Could not write to log: {e}")


# ============================================================================
# LIBRARY HELPER OPERATORS
# ============================================================================

class ASSET_OT_CopyLibraryPath(bpy.types.Operator):
    """Copy library file path to clipboard"""
    bl_idname = "asset.copy_library_path"
    bl_label = "Copy Library Path"
    bl_description = "Copy linked library file path to clipboard for easy access"
    bl_options = {'REGISTER'}
    
    library_path: StringProperty(name="Library Path")
    library_name: StringProperty(name="Library Name")
    
    @classmethod
    def description(cls, context, properties):
        """Dynamic tooltip showing full path"""
        if properties.library_path:
            return f"Path: {properties.library_path}\n\nClick to copy path to clipboard"
        return "Copy library file path to clipboard"
    
    def execute(self, context):
        """Copy path to clipboard"""
        try:
            context.window_manager.clipboard = self.library_path
            
            self.report({'INFO'}, f"Copied path: {self.library_name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to copy: {str(e)}")
            return {'CANCELLED'}


# =============================================================================
# PROPERTY UPDATE CALLBACKS
# =============================================================================

def update_include_libraries(self, context):
    """Auto-validate libraries when checkbox is toggled ON"""
    if context.scene.publish_include_libraries:
        from .check_publish import quick_validate_linked_libraries
        
        try:
            total, errors, warnings = quick_validate_linked_libraries(context)
            print(f"Auto-validated libraries: {total} total, {errors} errors, {warnings} warnings")
        except Exception as e:
            print(f"Auto-validation error: {e}")
            context.scene.publish_libraries_validated = False
    else:
        context.scene.publish_libraries_validated = False
        context.scene.publish_library_selection.clear()


class ASSET_OT_ReloadLibrary(bpy.types.Operator):
    """Reload linked library"""
    bl_idname = "asset.reload_library"
    bl_label = "Reload Library"
    bl_description = "Reload linked library to update changes"
    bl_options = {'REGISTER', 'UNDO'}
    
    library_path: StringProperty(name="Library Path")
    
    def execute(self, context):
        """Reload library"""
        if not self.library_path:
            self.report({'ERROR'}, "No library path provided")
            return {'CANCELLED'}
        
        import os
        
        target_path_norm = os.path.normpath(os.path.abspath(self.library_path))
        
        lib_to_reload = None
        for lib in bpy.data.libraries:
            lib_abs_path = bpy.path.abspath(lib.filepath)
            lib_path_norm = os.path.normpath(os.path.abspath(lib_abs_path))
            
            if lib_path_norm == target_path_norm:
                lib_to_reload = lib
                break
        
        if not lib_to_reload:
            self.report({'WARNING'}, "Library not loaded in current scene")
            return {'CANCELLED'}
        
        try:
            lib_to_reload.reload()
            self.report({'INFO'}, f"Reloaded: {lib_to_reload.name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to reload library: {str(e)}")
            return {'CANCELLED'}


class ASSET_OT_OpenLibraryFile(bpy.types.Operator):
    """Open library .blend file in new Blender instance"""
    bl_idname = "asset.open_library_file"
    bl_label = "Open Library File"
    bl_description = "Open library .blend file in new Blender instance"
    bl_options = {'REGISTER'}
    
    library_path: StringProperty(name="Library Path")
    
    def execute(self, context):
        """Open file in new Blender instance"""
        import subprocess
        import sys
        
        if not os.path.exists(self.library_path):
            self.report({'ERROR'}, f"File not found: {self.library_path}")
            return {'CANCELLED'}
        
        try:
            blender_exe = bpy.app.binary_path
            
            subprocess.Popen([blender_exe, self.library_path])
            
            filename = os.path.basename(self.library_path)
            self.report({'INFO'}, f"Opening: {filename}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open: {str(e)}")
            return {'CANCELLED'}


class ASSET_OT_CopySourcePath(bpy.types.Operator):
    """Copy source file path to clipboard"""
    bl_idname = "asset.copy_source_path"
    bl_label = "Copy Source Path"
    bl_description = "Copy original source file path to clipboard"
    bl_options = {'REGISTER'}
    
    source_path: StringProperty(name="Source Path")
    
    def execute(self, context):
        """Copy source path to clipboard"""
        try:
            context.window_manager.clipboard = self.source_path
            self.report({'INFO'}, f"Copied source path to clipboard")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to copy: {str(e)}")
            return {'CANCELLED'}


# =============================================================================
# ADDON REGISTRATION
# =============================================================================

def register():
    bpy.utils.register_class(LibrarySelectionItem)
    bpy.utils.register_class(ASSET_OT_Publish)
    bpy.utils.register_class(ASSET_OT_CopyLibraryPath)
    bpy.utils.register_class(ASSET_OT_ReloadLibrary)
    bpy.utils.register_class(ASSET_OT_OpenLibraryFile)
    bpy.utils.register_class(ASSET_OT_CopySourcePath)
    
    # ===== Publishing Settings =====
    bpy.types.Scene.publish_structure = StringProperty(
        name="Publish Structure",
        description="Folder structure for publishing (e.g., 'sets/rumah'). Auto-detected from file location",
        default=""
    )
    
    bpy.types.Scene.publish_path = StringProperty(
        name="Publish Path",
        description="Root directory where assets will be published",
        subtype='DIR_PATH',
        default=""
    )
    
    bpy.types.Scene.publish_versioning_mode = EnumProperty(
        name="Versioning Mode",
        description="How to handle file versioning",
        items=[
            ('OVERWRITE', 'Overwrite', 'Always overwrite existing file (no versions)', 'FILE_REFRESH', 0),
            ('VERSIONING', 'Versioning', 'Create versioned files (rumah_v001.blend, v002, etc.)', 'FILE_TICK', 1),
        ],
        default='OVERWRITE'
    )
    
    bpy.types.Scene.publish_force = BoolProperty(
        name="Force Publish",
        description="Bypass validation warnings (critical errors still block)",
        default=False
    )
    
    bpy.types.Scene.publish_sync_to_master = BoolProperty(
        name="Auto-sync to Master",
        description="Also update master file (without _v suffix) when publishing versioned file",
        default=False
    )
    
    bpy.types.Scene.publish_include_libraries = BoolProperty(
        name="Include Linked Libraries",
        description="Publish linked libraries together with current file",
        default=False,
        update=update_include_libraries
    )
    
    bpy.types.Scene.publish_library_selection = CollectionProperty(
        type=LibrarySelectionItem
    )
    
    bpy.types.Scene.publish_select_all_libraries = BoolProperty(
        name="Select All Libraries",
        description="Select or deselect all linked libraries",
        default=True,
        update=lambda self, context: toggle_all_libraries(context)
    )
    
    bpy.types.Scene.publish_libraries_validated = BoolProperty(
        name="Libraries Validated",
        description="Deep validation completed for linked libraries",
        default=False
    )
    
    bpy.types.Scene.publish_library_count = IntProperty(
        name="Library Count",
        description="Total number of linked libraries found",
        default=0
    )
    
    bpy.types.Scene.publish_library_errors = IntProperty(
        name="Library Errors",
        description="Number of libraries with errors",
        default=0
    )
    
    bpy.types.Scene.publish_library_warnings = IntProperty(
        name="Library Warnings",
        description="Number of libraries with warnings",
        default=0
    )
    
    bpy.types.Scene.publish_large_texture_count = IntProperty(
        name="Large Texture Count",
        description="Number of textures exceeding 4K resolution",
        default=0
    )
    
    # ===== NEW VALIDATION RESULTS =====
    
    bpy.types.Scene.publish_transform_issue_count = IntProperty(
        name="Transform Issues",
        description="Number of objects with unapplied transforms",
        default=0
    )
    
    bpy.types.Scene.publish_empty_slots_count = IntProperty(
        name="Empty Material Slots",
        description="Number of objects with empty or unused material slots",
        default=0
    )
    
    bpy.types.Scene.publish_duplicate_texture_count = IntProperty(
        name="Duplicate Textures",
        description="Number of duplicate textures that can be optimized",
        default=0
    )
    
    bpy.types.Scene.publish_duplicate_material_count = IntProperty(
        name="Duplicate Materials",
        description="Number of duplicate materials that can be optimized",
        default=0
    )


def toggle_all_libraries(context):
    select_all = context.scene.publish_select_all_libraries
    for item in context.scene.publish_library_selection:
        item.selected = select_all


def unregister():
    bpy.utils.unregister_class(ASSET_OT_CopySourcePath)
    bpy.utils.unregister_class(ASSET_OT_OpenLibraryFile)
    bpy.utils.unregister_class(ASSET_OT_ReloadLibrary)
    bpy.utils.unregister_class(ASSET_OT_CopyLibraryPath)
    bpy.utils.unregister_class(ASSET_OT_Publish)
    bpy.utils.unregister_class(LibrarySelectionItem)
    
    del bpy.types.Scene.publish_duplicate_material_count
    del bpy.types.Scene.publish_duplicate_texture_count
    del bpy.types.Scene.publish_empty_slots_count
    del bpy.types.Scene.publish_transform_issue_count
    del bpy.types.Scene.publish_large_texture_count
    del bpy.types.Scene.publish_library_warnings
    del bpy.types.Scene.publish_library_errors
    del bpy.types.Scene.publish_library_count
    del bpy.types.Scene.publish_libraries_validated
    del bpy.types.Scene.publish_select_all_libraries
    del bpy.types.Scene.publish_library_selection
    del bpy.types.Scene.publish_include_libraries
    del bpy.types.Scene.publish_sync_to_master
    del bpy.types.Scene.publish_force
    del bpy.types.Scene.publish_versioning_mode
    del bpy.types.Scene.publish_path
    del bpy.types.Scene.publish_structure


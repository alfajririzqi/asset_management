import bpy
import os
import shutil
import glob
import re
from datetime import datetime
import getpass
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, EnumProperty
from bpy.types import PropertyGroup


# ============================================================================
# PROPERTY GROUPS
# ============================================================================

class LibrarySelectionItem(PropertyGroup):
    """PropertyGroup for storing linked library info in UI"""
    name: StringProperty(name="Library Name")
    filepath: StringProperty(name="File Path", subtype='FILE_PATH')
    structure: StringProperty(name="Publish Structure")  # e.g., "environment/kayu"
    selected: BoolProperty(name="Include in Publish", default=True)
    depth: IntProperty(name="Nesting Depth", default=0)
    status: StringProperty(name="Validation Status", default="")  # OK, WARNING, ERROR
    folder_name: StringProperty(name="Folder Name")  # e.g., "kayu"
    has_textures: BoolProperty(name="Has Textures", default=False)


# ============================================================================
# HELPER CLASSES - Linked Libraries Support
# ============================================================================

class PathResolver:
    """
    Resolve publish paths from linked library relative paths.
    Detects master root folder from current file, then uses it for library structure extraction.
    """
    
    def __init__(self, publish_root):
        self.publish_root = os.path.normpath(publish_root)
        self.master_root = None  # Will be detected from current file
    
    def detect_master_root(self, current_file_path):
        """
        Detect master root folder - the folder that CONTAINS the assets folder.
        
        Logic: Find the folder that contains "assets" subfolder.
        
        Args:
            current_file_path: Absolute path to current .blend file
            
        Returns:
            str: Absolute path to master root (e.g., "G:/...asset_management/")
        
        Example:
            Input: "G:/...asset_management/assets/sets/rumah/rumah.blend"
            Finds: "assets" folder exists in "G:/...asset_management/"
            Output: "G:/...asset_management/"
        """
        if not current_file_path:
            return None
        
        current_dir = os.path.dirname(current_file_path)
        current_dir = os.path.normpath(current_dir)
        
        # Walk UP the directory tree
        check_dir = current_dir
        max_levels = 10  # Safety limit
        
        for _ in range(max_levels):
            # Check if this directory contains "assets" subfolder
            assets_folder = os.path.join(check_dir, "assets")
            
            if os.path.exists(assets_folder) and os.path.isdir(assets_folder):
                # Found it! This is the master root
                return os.path.normpath(check_dir)
            
            # Move up one level
            parent = os.path.dirname(check_dir)
            
            # Reached root drive
            if parent == check_dir:
                break
            
            check_dir = parent
        
        # Fallback: return None (will use old behavior)
        return None
    
    def extract_structure_from_link(self, library_filepath):
        """
        Extract publish structure from Blender library link path.
        
        CRITICAL: Uses Blender's RELATIVE path to preserve structure, ensuring:
        - Mirror folder structure in publish/
        - Client files won't have broken links
        
        Args:
            library_filepath: Blender library filepath (e.g., "//../../props/kursiHover/prp_kursiHover_mdl.blend")
        
        Returns:
            dict with 'absolute', 'structure', 'filename', 'publish_path'
        
        Example:
            Current file: .../assets/sets/rumah/rumah.blend
            Library link: //../../props/kursiHover/prp_kursiHover_mdl.blend
            
            Blender path breakdown:
            - "//" = current file's directory (.../assets/sets/rumah/)
            - "../.." = go up 2 levels to .../assets/
            - "props/kursiHover/" = structure we need!
            
            Output: {
                'structure': 'props/kursiHover',
                'publish_path': '.../publish/props/kursiHover/prp_kursiHover_mdl.blend'
            }
            
            Why this works: Blender relative path ALREADY contains correct structure!
        """
        # Get absolute path from Blender relative path
        lib_absolute = bpy.path.abspath(library_filepath)
        lib_absolute = os.path.normpath(lib_absolute)
        
        filename = os.path.basename(lib_absolute)
        
        # BEST METHOD: Parse Blender's relative path directly
        # Blender path: //../../props/kursiHover/file.blend
        # Structure: props/kursiHover
        
        if library_filepath.startswith('//'):
            # Remove "//" prefix and normalize
            lib_relative = library_filepath[2:]  # Remove "//"
            lib_relative = lib_relative.replace('\\', '/')  # Normalize slashes
            
            # Split path parts
            parts = [p for p in lib_relative.split('/') if p and p != '..']
            
            # Structure = all parts except filename
            # e.g., ['props', 'kursiHover', 'file.blend'] → 'props/kursiHover'
            if len(parts) > 1:
                structure = '/'.join(parts[:-1])
            else:
                structure = ''
        else:
            # Absolute path - fallback to extracting from absolute path
            if self.master_root:
                assets_folder = os.path.join(self.master_root, "assets")
                try:
                    rel_from_assets = os.path.relpath(lib_absolute, assets_folder)
                    rel_from_assets = os.path.normpath(rel_from_assets)
                    
                    if not rel_from_assets.startswith('..'):
                        # Inside assets/
                        parts = rel_from_assets.split(os.sep)
                        structure = '/'.join(parts[:-1]) if len(parts) > 1 else ''
                    else:
                        # Outside assets/ - use last 2 path parts
                        lib_dir = os.path.dirname(lib_absolute)
                        parts = lib_dir.split(os.sep)
                        structure = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else (parts[-1] if parts else '')
                except ValueError:
                    lib_dir = os.path.dirname(lib_absolute)
                    parts = lib_dir.split(os.sep)
                    structure = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else (parts[-1] if parts else '')
            else:
                # No master root - extract from path
                lib_dir = os.path.dirname(lib_absolute)
                parts = lib_dir.split(os.sep)
                structure = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else (parts[-1] if parts else '')
        
        # Build publish path (mirror structure)
        publish_path = os.path.join(self.publish_root, structure, filename)
        publish_path = os.path.normpath(publish_path)
        
        # Textures directory (same location as library file)
        textures_dir = os.path.join(os.path.dirname(lib_absolute), 'textures')
        
        # Get folder name for UI display
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
        """
        Get publish structure for current file using master root detection.
        
        Args:
            current_file_path: Absolute path to current .blend file
            publish_structure: Optional - scene.publish_structure property
        
        Returns:
            dict with structure info
        
        Example:
            Master root: G:/.../asset_management/
            Current file: G:/.../asset_management/assets/sets/rumah/rumah.blend
            Structure: sets/rumah  (relative to assets/ folder)
        """
        # Detect master root if not already done
        if not self.master_root:
            self.master_root = self.detect_master_root(current_file_path)
        
        if publish_structure:
            # User has set custom structure
            structure = publish_structure
        else:
            # Auto-detect from file location using master root
            if self.master_root:
                try:
                    # Get path to assets folder
                    assets_folder = os.path.join(self.master_root, "assets")
                    
                    # Get relative path from assets folder
                    rel_from_assets = os.path.relpath(current_file_path, assets_folder)
                    rel_from_assets = os.path.normpath(rel_from_assets)
                    
                    # Split to get parts (excluding filename)
                    parts = rel_from_assets.split(os.sep)[:-1]
                    
                    # Structure = path from assets/ folder
                    # e.g., "sets/rumah" or "props/meja"
                    structure = '/'.join(parts) if parts else ''
                    
                except ValueError:
                    # Fallback to old behavior
                    file_dir = os.path.dirname(current_file_path)
                    parent_folder = os.path.basename(file_dir)
                    grandparent_folder = os.path.basename(os.path.dirname(file_dir))
                    structure = f"{grandparent_folder}/{parent_folder}"
            else:
                # No master root - use old behavior
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
        """
        Get versioned filename.
        
        Example:
            filename: rumah.blend
            version_number: 3
            returns: rumah_v003.blend
        """
        name, ext = os.path.splitext(filename)
        return f"{name}_v{version_number:03d}{ext}"


class CircularDependencyError(Exception):
    """Raised when circular library dependency detected"""
    pass


class LinkedLibraryScanner:
    """
    Scan and validate linked libraries recursively.
    Max depth: 3 levels (current file + 2 nested levels)
    """
    
    def __init__(self, publish_root, max_depth=3):
        self.publish_root = publish_root
        self.max_depth = max_depth
        self.visited = set()  # Prevent circular dependencies
        self.libraries = []   # Flat list of all discovered libraries
        self.path_resolver = PathResolver(publish_root)
    
    def scan(self, current_depth=0):
        """
        Scan linked libraries from current open file.
        
        Returns:
            List of library info dicts
        """
        if current_depth >= self.max_depth:
            return self.libraries
        
        current_file = bpy.data.filepath
        if not current_file:
            return self.libraries
        
        current_file = os.path.normpath(current_file)
        
        # Check for circular dependency
        if current_file in self.visited:
            raise CircularDependencyError(f"Circular dependency: {current_file}")
        
        self.visited.add(current_file)
        
        # Scan libraries in current file
        for lib in bpy.data.libraries:
            lib_info = self.path_resolver.extract_structure_from_link(lib.filepath)
            
            if not lib_info:
                continue
            
            # Check if file exists
            lib_info['exists'] = os.path.exists(lib_info['absolute'])
            lib_info['has_textures'] = os.path.exists(lib_info['textures_dir'])
            lib_info['depth'] = current_depth + 1
            lib_info['library_name'] = lib.name
            
            self.libraries.append(lib_info)
        
        return self.libraries
    
    def scan_recursive(self, blend_file_path, current_depth=0):
        """
        Recursively scan nested libraries (for future deep scanning).
        Note: Requires opening each .blend file (slow, implement later)
        """
        # TODO: Implement recursive scanning by opening each .blend file
        # For now, only scan current file's direct links
        pass


# ============================================================================
# MAIN PUBLISH OPERATOR
# ============================================================================

class ASSET_OT_Publish(bpy.types.Operator):
    """Publish asset to production folder with clean textures.
    
    Process:
    • Validates all textures are consolidated locally
    • Purges orphan data from blend file
    • Copies only used textures (skips unused files)
    • Excludes .backup and .trash folders
    • Supports versioning mode (assetName_v001, v002, etc)
    • Logs all publish activity to .log files
    """
    bl_idname = "asset.publish"
    bl_label = "Publish Asset"
    bl_description = "Publish asset with validated textures, purged data, and optional versioning"
    bl_options = {'REGISTER'}
    
    # Internal data
    asset_name = ""
    blend_file = ""
    textures_to_copy = []
    validation_errors = []
    validation_warnings = []
    files_to_remove = []
    is_forced = False
    libraries_to_publish = []  # List of library info dicts to publish
    
    def write_publish_log(self, publish_path, asset_path, target_path, texture_count, status, notes=""):
        """Write to centralized publish log in publish folder"""
        log_file = os.path.join(publish_path, ".publish_activity.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        mode = bpy.context.scene.publish_versioning_mode
        
        # Enhanced log format with paths for detection
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
            print(f"Warning: Could not write to centralized log: {e}")
    
    def write_asset_history(self, asset_dir, target_path, texture_count, status, notes=""):
        """Removed - No longer writing per-asset history (clean delivery)"""
        pass
    
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
        
        # Check file is saved - ABSOLUTE requirement (can't force)
        if not bpy.data.filepath:
            self.validation_errors.append("File must be saved first")
            return False
        
        # Check publish path is set - ABSOLUTE requirement (can't force)
        publish_path = context.scene.publish_path
        if not publish_path or not publish_path.strip():
            self.validation_errors.append("Publish path not set. Set path in Publish panel first")
            return False
        
        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")
        
        # Check textures folder exists - WARNING (can be forced)
        if not os.path.exists(textures_dir):
            self.validation_warnings.append("Textures folder not found (will publish without textures)")
            # Skip texture validation if no folder
            return len(self.validation_errors) == 0
        
        # Check all textures are in local textures folder
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
            
            # Check if texture is in local textures folder
            try:
                if os.path.commonpath([abs_path, textures_dir]) != textures_dir:
                    external_textures.append(img.name)
            except ValueError:
                external_textures.append(img.name)
        
        # ALL texture issues are now WARNINGS (can be forced)
        if missing_textures:
            self.validation_warnings.append(f"Missing textures ({len(missing_textures)}): {', '.join(missing_textures[:3])}")
        
        if external_textures:
            self.validation_warnings.append(f"External textures found ({len(external_textures)}). Will copy only local textures")
        
        if packed_textures:
            self.validation_warnings.append(f"Packed textures ({len(packed_textures)}) will be skipped")
        
        return len(self.validation_errors) == 0
    
    def get_used_textures(self):
        """Get list of textures actually used in the blend file"""
        used_textures = set()
        
        def normalize_udim(path):
            """Normalize UDIM texture paths"""
            udim_match = re.search(r'(_\d{4})(?=\.)', path)
            if udim_match:
                return os.path.splitext(path)[0].replace(udim_match.group(1), '_<UDIM>')
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
        """Scan textures folder and categorize files"""
        IMAGE_EXTENSIONS = {
            'png', 'jpg', 'jpeg', 'tga', 'bmp', 'tiff', 'webp', 'exr', 'hdr', 'dds',
            'psd', 'svg', 'gif',
        }
        
        all_files = []
        for ext in IMAGE_EXTENSIONS:
            all_files.extend(glob.glob(os.path.join(textures_dir, f"*.{ext}")))
            all_files.extend(glob.glob(os.path.join(textures_dir, f"*.{ext.upper()}")))
        
        # Remove duplicates (Windows is case-insensitive, can find same file twice)
        all_files = list(set(all_files))
        
        used_textures = self.get_used_textures()
        
        textures_to_copy = []
        unused_files = []
        
        def normalize_udim(path):
            udim_match = re.search(r'(_\d{4})(?=\.)', path)
            if udim_match:
                return os.path.splitext(path)[0].replace(udim_match.group(1), '_<UDIM>')
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
        """Get target publish path with versioning if needed (OLD SYSTEM - folder-based)"""
        publish_path = context.scene.publish_path
        base_path = os.path.join(publish_path, self.asset_name)
        
        if context.scene.publish_versioning_mode == 'OVERWRITE':
            return base_path
        
        # Versioning mode - find next version number
        version_num = 1
        while True:
            versioned_path = f"{base_path}_v{version_num:03d}"
            if not os.path.exists(versioned_path):
                return versioned_path
            version_num += 1
    
    # ========================================================================
    # ========================================================================
    # FILE PUBLISHING METHODS (OVERWRITE MODE - NO VERSIONING)
    # ========================================================================
    
    def publish_master_file(self, source_path, target_folder, context):
        """
        Publish master file with versioning mode support.
        
        Process:
        1. Determine filename based on versioning mode
        2. Copy file to publish folder
        3. Purge orphan data
        4. Textures handled separately
        
        Modes:
        - OVERWRITE: house.blend (always overwrites)
        - VERSIONING: house_v001.blend, house_v002.blend (incremental)
        
        Args:
            source_path: Absolute path to source .blend file
            target_folder: Target folder for publishing
            context: Blender context
        
        Returns:
            str: Published file path
        """
        # Create target folder if needed
        os.makedirs(target_folder, exist_ok=True)
        
        # Get base filename
        base_filename = os.path.basename(source_path)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        # Determine final filename based on mode
        if context.scene.publish_versioning_mode == 'VERSIONING':
            # Find next version number
            version_num = 1
            while True:
                versioned_name = f"{name_without_ext}_v{version_num:03d}.blend"
                versioned_path = os.path.join(target_folder, versioned_name)
                if not os.path.exists(versioned_path):
                    published_path = versioned_path
                    break
                version_num += 1
        else:
            # OVERWRITE mode - use original filename
            published_path = os.path.join(target_folder, base_filename)
        
        # Copy file with cleanup
        self.copy_blend_file_with_cleanup(source_path, published_path)
        
        return published_path
    
    def publish_linked_library(self, lib_info, context):
        """
        Publish linked library with versioning mode support.
        
        Process:
        1. Copy library file to publish path
        2. Purge orphan data
        3. Respect versioning mode (overwrite or versioned filenames)
        
        Args:
            lib_info: Library info dict from LinkedLibraryScanner
            context: Blender context
        
        Returns:
            str: Published file path
        """
        source_path = lib_info['absolute']
        base_target_path = lib_info['publish_path']
        
        # Create target folder
        target_folder = os.path.dirname(base_target_path)
        os.makedirs(target_folder, exist_ok=True)
        
        # Get base filename
        base_filename = os.path.basename(source_path)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        # Determine final filename based on mode
        if context.scene.publish_versioning_mode == 'VERSIONING':
            # Find next version number
            version_num = 1
            while True:
                versioned_name = f"{name_without_ext}_v{version_num:03d}.blend"
                versioned_path = os.path.join(target_folder, versioned_name)
                if not os.path.exists(versioned_path):
                    target_path = versioned_path
                    break
                version_num += 1
        else:
            # OVERWRITE mode - use original filename
            target_path = os.path.join(target_folder, base_filename)
        
        # Copy file with cleanup
        self.copy_blend_file_with_cleanup(source_path, target_path)
        
        return target_path
    
    def copy_blend_file_with_cleanup(self, source_path, target_path):
        """
        Copy .blend file and purge orphan data.
        
        Args:
            source_path: Source .blend file
            target_path: Destination .blend file
        """
        # For now, simple copy
        # TODO: Implement orphan data purging by opening file in background
        shutil.copy2(source_path, target_path)
        
        # TODO: Open target file, purge orphans, save, close
        # This requires background Blender instance or careful handling
        # For MVP, we skip purging during publish
    
    def copy_library_textures(self, lib_info, target_folder):
        """
        Copy textures for a linked library.
        
        Args:
            lib_info: Library info dict
            target_folder: Target folder for published library
        """
        source_textures_dir = lib_info['textures_dir']
        target_textures_dir = os.path.join(target_folder, 'textures')
        
        if not os.path.exists(source_textures_dir):
            return
        
        # Create target textures folder
        os.makedirs(target_textures_dir, exist_ok=True)
        
        # Copy all texture files (overwrite)
        for filename in os.listdir(source_textures_dir):
            source_file = os.path.join(source_textures_dir, filename)
            
            # Skip directories and hidden files
            if os.path.isdir(source_file) or filename.startswith('.'):
                continue
            
            target_file = os.path.join(target_textures_dir, filename)
            shutil.copy2(source_file, target_file)
    
    # ========================================================================
    # END NEW METHODS
    # ========================================================================
    
    def invoke(self, context, event):
        # SAFETY CHECK 1: Require validation check to be run first
        if not context.scene.publish_check_done:
            self.report({'ERROR'}, "Run 'Check Publish' first to validate asset readiness")
            return {'CANCELLED'}
        
        # SAFETY CHECK 2: Block if this is a published file (Option A - Total Block)
        if context.scene.publish_is_published_file:
            self.report({'ERROR'}, "Cannot publish from publish directory! Open the source file instead.")
            return {'CANCELLED'}
        
        # Get asset name
        self.asset_name = self.get_asset_name()
        if not self.asset_name:
            self.report({'ERROR'}, "Could not determine asset name")
            return {'CANCELLED'}
        
        # Validate
        validation_passed = self.validate_publish(context)
        
        # Check if force publish is enabled
        self.is_forced = context.scene.publish_force
        
        # Only block on ABSOLUTE errors (file not saved, no publish path)
        # Everything else can be forced!
        if not validation_passed and not self.is_forced:
            # Has critical errors and NOT forcing
            return context.window_manager.invoke_props_dialog(self, width=500)
        
        # If forcing, allow even with critical warnings
        if self.is_forced and self.validation_warnings:
            # Force mode - bypass all warnings
            pass
        
        # Scan textures (only if folder exists)
        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")
        
        if os.path.exists(textures_dir):
            self.textures_to_copy, unused_files = self.scan_textures_folder(textures_dir)
        else:
            self.textures_to_copy = []
            unused_files = []
        
        # Find folders to remove (.backup, .trash)
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
        
        # ====================================================================
        # SCAN LINKED LIBRARIES (for dialog display)
        # ====================================================================
        self.libraries_to_publish = []
        
        if context.scene.publish_include_libraries:
            publish_path = context.scene.publish_path
            
            try:
                scanner = LinkedLibraryScanner(publish_path, max_depth=3)
                libraries = scanner.scan()
                
                # Filter selected libraries
                for lib_info in libraries:
                    # Check if selected in UI
                    is_selected = True
                    for item in context.scene.publish_library_selection:
                        if item.filepath == lib_info['absolute']:
                            is_selected = item.selected
                            break
                    
                    if is_selected and lib_info['exists']:
                        self.libraries_to_publish.append(lib_info)
                
            except CircularDependencyError as e:
                self.report({'ERROR'}, f"Circular dependency detected: {str(e)}")
                return {'CANCELLED'}
            except Exception as e:
                self.report({'WARNING'}, f"Library scan warning: {str(e)}")
        
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        
        # Show validation errors (ABSOLUTE - can't force)
        if self.validation_errors:
            box = layout.box()
            box.alert = True
            box.label(text="🚫 CRITICAL ERRORS (Cannot Force):", icon='ERROR')
            for error in self.validation_errors:
                box.label(text=f"  • {error}", icon='BLANK1')
            layout.separator()
            layout.label(text="Fix these errors first", icon='INFO')
            return
        
        # Show validation warnings (can be forced)
        if self.validation_warnings:
            box = layout.box()
            box.alert = True
            box.label(text="⚠️ WARNINGS:", icon='ERROR')
            for warning in self.validation_warnings:
                box.label(text=f"  • {warning}", icon='BLANK1')
            
            if self.is_forced:
                layout.separator()
                force_box = layout.box()
                force_box.alert = True
                force_box.label(text="🚨 FORCE PUBLISH ACTIVE", icon='ERROR')
                force_box.label(text="⚠️ ALL WARNINGS WILL BE IGNORED", icon='BLANK1')
                force_box.label(text="⚠️ YOU TAKE FULL RESPONSIBILITY", icon='BLANK1')
            
            layout.separator()
        
        # Asset info
        box = layout.box()
        box.label(text="📦 Asset Information:", icon='ASSET_MANAGER')
        box.label(text=f"Asset Name: {self.asset_name}", icon='BLANK1')
        box.label(text=f"Blend File: {os.path.basename(bpy.data.filepath)}", icon='BLANK1')
        
        layout.separator()
        
        # Publish settings
        box = layout.box()
        box.label(text="⚙️ Publish Settings:", icon='SETTINGS')
        box.label(text=f"Path: {context.scene.publish_path}", icon='BLANK1')
        box.label(text=f"Mode: {context.scene.publish_versioning_mode}", icon='BLANK1')
        
        target_path = self.get_target_path(context)
        box.label(text=f"Target: {target_path}", icon='BLANK1')
        
        layout.separator()
        
        # Files to send
        box = layout.box()
        
        # Calculate total files to send
        total_files = 1 + len(self.textures_to_copy)  # Master blend + textures
        if self.libraries_to_publish:
            total_files += len(self.libraries_to_publish)  # Add library blend files
        
        box.label(text=f"✅ Files to Send ({total_files}):", icon='CHECKMARK')
        
        # Master file
        box.label(text=f"  • {os.path.basename(bpy.data.filepath)} (cleaned)", icon='FILE_BLEND')
        box.label(text=f"  • {len(self.textures_to_copy)} texture files", icon='TEXTURE')
        
        # Preview some textures with file sizes
        for tex in self.textures_to_copy[:3]:
            try:
                file_size = os.path.getsize(tex)
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                box.label(text=f"    - {os.path.basename(tex)} ({size_str})", icon='BLANK1')
            except Exception:
                # Fallback if file size can't be determined
                box.label(text=f"    - {os.path.basename(tex)}", icon='BLANK1')
        if len(self.textures_to_copy) > 3:
            box.label(text=f"    - ... and {len(self.textures_to_copy) - 3} more", icon='BLANK1')
        
        # Show linked libraries if any
        if self.libraries_to_publish:
            box.separator(factor=0.5)
            box.label(text=f"  • {len(self.libraries_to_publish)} Linked Libraries:", icon='LINKED')
            
            for lib_info in self.libraries_to_publish[:5]:
                indent = "  " * lib_info['depth']
                lib_name = lib_info['folder_name']
                lib_structure = lib_info['structure']
                box.label(text=f"    {indent}→ {lib_name} ({lib_structure})", icon='FILE_BLEND')
            
            if len(self.libraries_to_publish) > 5:
                box.label(text=f"    ... and {len(self.libraries_to_publish) - 5} more libraries", icon='BLANK1')
        
        layout.separator()
        
        # Files to exclude
        if self.files_to_remove:
            box = layout.box()
            box.label(text=f"🗑️ Will NOT Send:", icon='TRASH')
            for item in self.files_to_remove[:10]:
                box.label(text=f"  • {item}", icon='BLANK1')
        
        layout.separator()
        layout.label(text="⚠️ Asset will be cleaned before publish:", icon='INFO')
        layout.label(text="  • Orphan data will be purged", icon='BLANK1')
        layout.label(text="  • File will be saved", icon='BLANK1')
        
        if self.libraries_to_publish:
            layout.label(text="  • Linked libraries will be published", icon='BLANK1')
    
    def execute(self, context):
        """
        Main publish execution with linked libraries support.
        
        NEW FLOW:
        1. Validate & setup
        2. Scan linked libraries (if enabled)
        3. Publish linked libraries first
        4. Publish master file
        5. Copy textures for all files
        6. Update logs
        """
        # Only check ABSOLUTE errors (file not saved, no publish path)
        # Force publish bypasses ALL warnings!
        if self.validation_errors:
            self.report({'ERROR'}, "Cannot publish: fix critical errors first")
            return {'CANCELLED'}
        
        try:
            # ================================================================
            # STEP 1: Setup & Validation
            # ================================================================
            publish_path = context.scene.publish_path
            
            # Validate publish path
            if not os.path.exists(publish_path):
                try:
                    os.makedirs(publish_path, exist_ok=True)
                    self.report({'INFO'}, f"Created publish directory: {publish_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Cannot create publish path: {str(e)}")
                    return {'CANCELLED'}
            
            # Clean the blend file (purge orphans)
            self.report({'INFO'}, "Cleaning blend file...")
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            bpy.ops.wm.save_mainfile()
            
            # Initialize PathResolver
            path_resolver = PathResolver(publish_path)
            
            # ================================================================
            # STEP 2: Collect Files to Publish
            # ================================================================
            
            # Current file info
            current_file = bpy.data.filepath
            current_structure = context.scene.publish_structure
            current_info = path_resolver.get_current_file_structure(
                current_file,
                publish_structure=current_structure
            )
            
            # Auto-set publish_structure if empty (first time)
            if not current_structure:
                context.scene.publish_structure = current_info['structure']
            
            files_to_publish = {
                'master': {
                    'source_path': current_file,
                    'target_folder': current_info['publish_folder'],
                    'filename': current_info['filename'],
                    'textures_dir': current_info['textures_dir'],
                    'structure': current_info['structure']
                },
                'libraries': []
            }
            
            # Use libraries already scanned in invoke()
            library_count = 0
            if context.scene.publish_include_libraries and self.libraries_to_publish:
                # Use pre-scanned libraries from invoke()
                files_to_publish['libraries'] = self.libraries_to_publish
                library_count = len(self.libraries_to_publish)
                self.report({'INFO'}, f"Publishing {library_count} linked libraries")
            
            # ================================================================
            # STEP 3: Publish Linked Libraries First
            # ================================================================
            published_libraries = []
            
            for lib_info in files_to_publish['libraries']:
                try:
                    lib_path = self.publish_linked_library(lib_info, context)
                    published_libraries.append({
                        'name': lib_info['folder_name'],
                        'path': lib_path,
                        'structure': lib_info['structure']
                    })
                    
                    # Copy library textures
                    lib_folder = os.path.dirname(lib_path)
                    self.copy_library_textures(lib_info, lib_folder)
                    
                    self.report({'INFO'}, f"Published library: {lib_info['folder_name']}")
                    
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to publish library {lib_info['folder_name']}: {str(e)}")
            
            # ================================================================
            # STEP 4: Publish Master File
            # ================================================================
            master_info = files_to_publish['master']
            
            # Publish (overwrite mode - no versioning)
            published_path = self.publish_master_file(
                source_path=master_info['source_path'],
                target_folder=master_info['target_folder'],
                context=context
            )
            
            self.report({'INFO'}, f"Published master file: {os.path.basename(published_path)}")
            
            # ================================================================
            # STEP 5: Copy Master File Textures
            # ================================================================
            target_textures = os.path.join(master_info['target_folder'], "textures")
            os.makedirs(target_textures, exist_ok=True)
            
            copied_count = 0
            if os.path.exists(master_info['textures_dir']) and self.textures_to_copy:
                for tex_path in self.textures_to_copy:
                    tex_filename = os.path.basename(tex_path)
                    target_tex = os.path.join(target_textures, tex_filename)
                    shutil.copy2(tex_path, target_tex)
                    copied_count += 1
            elif not os.path.exists(master_info['textures_dir']):
                self.report({'INFO'}, "No textures folder found - publishing without textures")
            
            # ================================================================
            # STEP 6: Write Logs
            # ================================================================
            status = "SUCCESS"
            notes = ""
            
            if self.is_forced and self.validation_warnings:
                status = "SUCCESS (FORCED)"
                notes = f"{len(self.validation_warnings)} warnings ignored"
            
            # Enhanced log with library info
            self.write_publish_log_v2(
                publish_path=publish_path,
                published_path=published_path,
                source_path=current_file,
                texture_count=copied_count,
                linked_libraries=published_libraries,
                status=status,
                notes=notes
            )
            
            # ================================================================
            # STEP 7: Success Report
            # ================================================================
            force_text = " (FORCED)" if self.is_forced else ""
            lib_text = f" + {len(published_libraries)} libraries" if published_libraries else ""
            
            self.report(
                {'INFO'},
                f"Published {self.asset_name}{force_text}{lib_text} | "
                f"{copied_count} textures | Target: {master_info['target_folder']}"
            )
            
            # Reset flags
            context.scene.publish_force = False
            context.scene.publish_libraries_validated = False
            
            return {'FINISHED'}
            
        except Exception as e:
            # Log failure
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
            
            self.report({'ERROR'}, f"Publish failed: {str(e)}")
            return {'CANCELLED'}
    
    def write_publish_log_v2(self, publish_path, published_path, source_path, 
                            texture_count, linked_libraries, status, notes=""):
        """
        Enhanced publish log with linked libraries support (OVERWRITE mode).
        
        Format:
        [timestamp] PUBLISH | Asset: name | Path: path | Source: path | Linked: X | Status: SUCCESS
          └─ LINKED | Library: name | Structure: structure | Path: path
        """
        log_file = os.path.join(publish_path, ".publish_activity.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        
        # Main entry (no versioning info)
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
        
        # Add linked library entries
        for lib in linked_libraries:
            log_entry += (
                f"  └─ LINKED | "
                f"Library: {lib['name']} | "
                f"Structure: {lib['structure']} | "
                f"Path: {lib['path']}\n"
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
    bl_description = "Copy library file path to clipboard"
    bl_options = {'REGISTER'}
    
    library_path: StringProperty(name="Library Path")
    library_name: StringProperty(name="Library Name")
    
    def execute(self, context):
        """Copy path to clipboard"""
        try:
            # Copy to clipboard
            context.window_manager.clipboard = self.library_path
            
            self.report({'INFO'}, f"Copied path: {self.library_name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to copy: {str(e)}")
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
            # Get Blender executable path
            blender_exe = bpy.app.binary_path
            
            # Open in new instance
            subprocess.Popen([blender_exe, self.library_path])
            
            filename = os.path.basename(self.library_path)
            self.report({'INFO'}, f"Opening: {filename}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open: {str(e)}")
            return {'CANCELLED'}


def register():
    # Register PropertyGroup
    bpy.utils.register_class(LibrarySelectionItem)
    bpy.utils.register_class(ASSET_OT_Publish)
    bpy.utils.register_class(ASSET_OT_CopyLibraryPath)
    bpy.utils.register_class(ASSET_OT_OpenLibraryFile)
    
    # ===== Publishing Settings =====
    
    # Publish structure for current file (auto-detected or manual)
    bpy.types.Scene.publish_structure = StringProperty(
        name="Publish Structure",
        description="Folder structure for publishing (e.g., 'sets/rumah'). Auto-detected from file location",
        default=""
    )
    
    # Publish path (target root directory)
    bpy.types.Scene.publish_path = StringProperty(
        name="Publish Path",
        description="Root directory where assets will be published",
        subtype='DIR_PATH',
        default=""
    )
    
    # Versioning mode
    bpy.types.Scene.publish_versioning_mode = EnumProperty(
        name="Versioning Mode",
        description="How to handle file versioning",
        items=[
            ('OVERWRITE', 'Overwrite', 'Always overwrite existing file (no versions)', 'FILE_REFRESH', 0),
            ('VERSIONING', 'Versioning', 'Create versioned files (rumah_v001.blend, v002, etc.)', 'FILE_TICK', 1),
        ],
        default='OVERWRITE'
    )
    
    # Force publish (bypass warnings)
    bpy.types.Scene.publish_force = BoolProperty(
        name="Force Publish",
        description="Bypass validation warnings (critical errors still block)",
        default=False
    )
    
    # ===== Linked Libraries Settings =====
    
    # Include linked libraries toggle
    bpy.types.Scene.publish_include_libraries = BoolProperty(
        name="Include Linked Libraries",
        description="Publish linked libraries together with current file",
        default=False
    )
    
    # Library selection collection
    bpy.types.Scene.publish_library_selection = CollectionProperty(
        type=LibrarySelectionItem
    )
    
    # Select all libraries checkbox
    bpy.types.Scene.publish_select_all_libraries = BoolProperty(
        name="Select All Libraries",
        description="Select or deselect all linked libraries",
        default=True,
        update=lambda self, context: toggle_all_libraries(context)
    )
    
    # Libraries validated flag
    bpy.types.Scene.publish_libraries_validated = BoolProperty(
        name="Libraries Validated",
        description="Deep validation completed for linked libraries",
        default=False
    )
    
    # Library validation results
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


def toggle_all_libraries(context):
    """Callback to select/deselect all libraries"""
    select_all = context.scene.publish_select_all_libraries
    for item in context.scene.publish_library_selection:
        item.selected = select_all


def unregister():
    # Unregister classes
    bpy.utils.unregister_class(ASSET_OT_OpenLibraryFile)
    bpy.utils.unregister_class(ASSET_OT_CopyLibraryPath)
    bpy.utils.unregister_class(ASSET_OT_Publish)
    bpy.utils.unregister_class(LibrarySelectionItem)
    
    # Delete scene properties
    del bpy.types.Scene.publish_library_warnings
    del bpy.types.Scene.publish_library_errors
    del bpy.types.Scene.publish_library_count
    del bpy.types.Scene.publish_libraries_validated
    del bpy.types.Scene.publish_select_all_libraries
    del bpy.types.Scene.publish_library_selection
    del bpy.types.Scene.publish_include_libraries
    del bpy.types.Scene.publish_force
    del bpy.types.Scene.publish_versioning_mode
    del bpy.types.Scene.publish_path
    del bpy.types.Scene.publish_structure


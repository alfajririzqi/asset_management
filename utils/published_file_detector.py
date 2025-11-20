"""
Published File Detection Utility

Shared helper to detect if current file is a published file.
Used across multiple panels to protect published files from modification.
"""

import bpy
import os
import re


def detect_published_file_status(context):
    """
    Detect if current file is a published file (READ-ONLY for panels).
    Safe to call from panel.draw() - does NOT modify scene properties.
    
    Detects both OLD (folder-based) and NEW (file-based) versioning:
    - OLD: AssetName_v001/ folder pattern
    - NEW: asset_v001.blend filename pattern
    
    Returns:
        tuple: (is_published: bool, source_path: str)
    """
    if not bpy.data.filepath:
        return False, ""
    
    # Check cache first (stored in scene properties by operators)
    if hasattr(context.scene, 'publish_is_published_file'):
        if hasattr(context.scene, '_publish_detection_cached'):
            # Cache is valid - return cached values
            return context.scene.publish_is_published_file, context.scene.publish_source_path
    
    # No cache - run detection (but don't write to scene)
    current_file = bpy.data.filepath
    current_file = os.path.normpath(current_file)
    current_dir = os.path.dirname(current_file)
    current_filename = os.path.basename(current_file)
    publish_path = context.scene.publish_path if hasattr(context.scene, 'publish_path') else ""
    
    # METHOD 1: Check FILE pattern (NEW - file-based versioning)
    # Pattern: asset_v001.blend, rumah_v002.blend, etc.
    if re.match(r'.+_v\d{3}\.blend$', current_filename, re.IGNORECASE):
        # Check log in current directory
        log_file = os.path.join(current_dir, ".publish_activity.log")
        if os.path.exists(log_file):
            source = parse_log_for_file(log_file, current_file)
            if source:
                return True, source
        
        # Check log in parent directory
        parent = os.path.dirname(current_dir)
        log_file = os.path.join(parent, ".publish_activity.log")
        if os.path.exists(log_file):
            source = parse_log_for_file(log_file, current_file)
            if source:
                return True, source
    
    # METHOD 2: Check FOLDER pattern (OLD - folder-based versioning)
    # Pattern: AssetName_v001/ folder
    folder_name = os.path.basename(current_dir)
    if re.match(r'.+_v\d{3}$', folder_name):
        parent = os.path.dirname(current_dir)
        log_file = os.path.join(parent, ".publish_activity.log")
        if os.path.exists(log_file):
            source = parse_log_for_path(log_file, current_dir)
            if source:
                return True, source
    
    # METHOD 3: Check using publish path setting
    if publish_path:
        log_file = os.path.join(publish_path, ".publish_activity.log")
        if os.path.exists(log_file):
            # Try file-based first
            source = parse_log_for_file(log_file, current_file)
            if source:
                return True, source
            # Then folder-based
            source = parse_log_for_path(log_file, current_dir)
            if source:
                return True, source
    
    # METHOD 4: Search upward for .publish_activity.log (for nested publish structures)
    # Check up to 5 levels up
    current_search_dir = current_dir
    for _ in range(5):
        parent = os.path.dirname(current_search_dir)
        if parent == current_search_dir:  # Reached root
            break
        
        log_file = os.path.join(parent, ".publish_activity.log")
        if os.path.exists(log_file):
            # Check if this file path is in the log
            source = parse_log_for_file(log_file, current_file)
            if source:
                return True, source
        
        current_search_dir = parent
    
    # Not a published file
    return False, ""


def detect_library_published_status(library_path):
    """
    Detect if a linked library is a published file.
    
    Args:
        library_path: str - Absolute path to library .blend file
        
    Returns:
        tuple: (is_published: bool, source_path: str)
    """
    if not library_path or not os.path.exists(library_path):
        return False, ""
    
    library_path = os.path.normpath(library_path)
    library_dir = os.path.dirname(library_path)
    library_filename = os.path.basename(library_path)
    
    # METHOD 1: Check FILE pattern (NEW - file-based versioning)
    if re.match(r'.+_v\d{3}\.blend$', library_filename, re.IGNORECASE):
        # Check log in current directory
        log_file = os.path.join(library_dir, ".publish_activity.log")
        if os.path.exists(log_file):
            source = parse_log_for_file(log_file, library_path)
            if source:
                return True, source
        
        # Check log in parent directory
        parent = os.path.dirname(library_dir)
        log_file = os.path.join(parent, ".publish_activity.log")
        if os.path.exists(log_file):
            source = parse_log_for_file(log_file, library_path)
            if source:
                return True, source
    
    # METHOD 2: Check FOLDER pattern (OLD - folder-based versioning)
    folder_name = os.path.basename(library_dir)
    if re.match(r'.+_v\d{3}$', folder_name):
        parent = os.path.dirname(library_dir)
        log_file = os.path.join(parent, ".publish_activity.log")
        if os.path.exists(log_file):
            source = parse_log_for_path(log_file, library_dir)
            if source:
                return True, source
    
    # METHOD 3: Search upward for .publish_activity.log (for libraries in subfolders)
    # Check up to 5 levels up
    current_search_dir = library_dir
    for _ in range(5):
        parent = os.path.dirname(current_search_dir)
        if parent == current_search_dir:  # Reached root
            break
        
        log_file = os.path.join(parent, ".publish_activity.log")
        if os.path.exists(log_file):
            # Check if this library path is in the log
            source = parse_log_for_file(log_file, library_path)
            if source:
                return True, source
        
        current_search_dir = parent
    
    return False, ""


def update_published_file_cache(context, is_published, source_path):
    """
    Update scene properties with published file detection results.
    ONLY call from operators (execute/invoke), NEVER from panel.draw()!
    
    Args:
        context: Blender context
        is_published: bool - Is this a published file?
        source_path: str - Original source path (or empty string)
    """
    try:
        context.scene.publish_is_published_file = is_published
        context.scene.publish_source_path = source_path if source_path else ""
        context.scene._publish_detection_cached = True
    except Exception as e:
        print(f"Warning: Could not update published file cache: {e}")


def parse_log_for_path(log_file, target_path):
    """
    Parse publish activity log (OLD format) and return source path if target found.
    
    OLD Format:
    [timestamp] PUBLISH | Asset: name | Path: target | Source: source | ...
    
    Args:
        log_file: Path to .publish_activity.log
        target_path: Folder path to search for (normalized)
        
    Returns:
        str or None: Source path if found, None otherwise
    """
    target_path = os.path.normpath(target_path)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'Path:' in line:
                    path_match = re.search(r'Path: ([^|]+)', line)
                    if path_match:
                        logged_path = os.path.normpath(path_match.group(1).strip())
                        if logged_path == target_path:
                            source_match = re.search(r'Source: ([^|]+)', line)
                            if source_match:
                                return source_match.group(1).strip()
    except Exception as e:
        print(f"Error parsing log: {e}")
    
    return None


def parse_log_for_file(log_file, target_file):
    """
    Parse publish activity log and return source path if target found.
    
    Log Format:
    [timestamp] PUBLISH | Asset: name | Path: published_path | Source: source | ...
      └─ LINKED | Library: name | Path: path | Source: source
    
    Args:
        log_file: Path to .publish_activity.log
        target_file: File path to search for (normalized)
        
    Returns:
        str or None: Source path if found, None otherwise
    """
    target_file = os.path.normpath(target_file)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'PUBLISH |' in line and 'Path:' in line:
                    path_match = re.search(r'Path: ([^|]+)', line)
                    if path_match:
                        logged_path = os.path.normpath(path_match.group(1).strip())
                        if logged_path == target_file:
                            source_match = re.search(r'Source: ([^|]+)', line)
                            if source_match:
                                return source_match.group(1).strip()
                
                if '└─ LINKED |' in line:
                    path_match = re.search(r'Path: ([^|]+)', line)
                    if path_match:
                        logged_path = os.path.normpath(path_match.group(1).strip())
                        if logged_path == target_file:
                            source_match = re.search(r'\|\s*Source:\s*(.+?)(?:\s*\n|$)', line)
                            if source_match:
                                return source_match.group(1).strip()
    except Exception as e:
        print(f"Error parsing log: {e}")
    
    return None

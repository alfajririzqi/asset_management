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
    
    # Not a published file
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
    Parse publish activity log (NEW format) and return source path if target found.
    
    NEW Format:
    [timestamp] PUBLISH | Asset: name | Version: versioned_path | Latest: latest_path | Source: source | ...
      └─ LINKED | Library: name | Path: path
    
    Checks both Version and Latest paths.
    
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
                # Skip LINKED entries
                if line.strip().startswith('└─ LINKED'):
                    continue
                
                # Check main PUBLISH entries
                if 'PUBLISH |' in line:
                    # Check Version path
                    version_match = re.search(r'Version: ([^|]+)', line)
                    if version_match:
                        logged_path = os.path.normpath(version_match.group(1).strip())
                        if logged_path == target_file:
                            source_match = re.search(r'Source: ([^|]+)', line)
                            if source_match:
                                return source_match.group(1).strip()
                    
                    # Check Latest path
                    latest_match = re.search(r'Latest: ([^|]+)', line)
                    if latest_match:
                        logged_path = os.path.normpath(latest_match.group(1).strip())
                        if logged_path == target_file:
                            source_match = re.search(r'Source: ([^|]+)', line)
                            if source_match:
                                return source_match.group(1).strip()
                
                # Check LINKED library entries (for libraries published with main file)
                if '└─ LINKED |' in line:
                    path_match = re.search(r'Path: (.+)$', line)
                    if path_match:
                        logged_path = os.path.normpath(path_match.group(1).strip())
                        if logged_path == target_file:
                            # Library is published - it's a published file
                            # Source is the library itself (libraries always overwrite)
                            return "LINKED_LIBRARY"
    except Exception as e:
        print(f"Error parsing log: {e}")
    
    return None

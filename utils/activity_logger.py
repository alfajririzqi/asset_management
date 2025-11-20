"""
Activity Logger Utility

Tracks user operations in the addon with configurable location and auto-truncate.
"""

import bpy
import os
from datetime import datetime


def get_log_path(context=None):
    """Get activity log path based on preferences"""
    try:
        prefs = bpy.context.preferences.addons[__package__.split('.')[0]].preferences
        
        if not prefs.enable_activity_logging:
            return None
        
        log_location = prefs.activity_log_location
        
        if log_location == 'PER_PROJECT':
            if bpy.data.filepath:
                blend_dir = os.path.dirname(bpy.data.filepath)
                return os.path.join(blend_dir, ".addon_activity.log")
            else:
                addon_dir = os.path.dirname(os.path.dirname(__file__))
                return os.path.join(addon_dir, ".addon_activity_temp.log")
        
        elif log_location == 'GLOBAL':
            addon_dir = os.path.dirname(os.path.dirname(__file__))
            return os.path.join(addon_dir, ".addon_activity.log")
        
        elif log_location == 'CUSTOM':
            custom_path = prefs.activity_log_custom_path
            if custom_path and os.path.exists(os.path.dirname(custom_path)):
                return custom_path
            else:
                addon_dir = os.path.dirname(os.path.dirname(__file__))
                return os.path.join(addon_dir, ".addon_activity.log")
        
    except Exception as e:
        print(f"Activity logger warning: {e}")
        return None


def truncate_log_if_needed(log_path, max_entries=1000, keep_entries=900):
    """Auto-truncate log file if it exceeds max entries"""
    try:
        if not os.path.exists(log_path):
            return
        
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) > max_entries:
            lines = lines[-keep_entries:]
            
            with open(log_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"Activity log truncated: kept {keep_entries} newest entries")
    
    except Exception as e:
        print(f"Failed to truncate log: {e}")


def log_activity(operation, details="", context=None):
    """
    Log an operation to the activity log
    
    Args:
        operation: Operation name (e.g., "PUBLISH", "OPTIMIZE_TEXTURES")
        details: Additional details about the operation
        context: Blender context (optional)
    """
    try:
        log_path = get_log_path(context)
        
        if not log_path:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] {operation}"
        if details:
            log_entry += f" | {details}"
        log_entry += "\n"
        
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        truncate_log_if_needed(log_path)
        
    except Exception as e:
        print(f"Failed to log activity: {e}")


def get_activity_stats():
    """Get statistics about current activity log"""
    try:
        log_path = get_log_path()
        
        if not log_path or not os.path.exists(log_path):
            return {
                'exists': False,
                'entries': 0,
                'size': 0,
                'path': log_path or "Not configured"
            }
        
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        file_size = os.path.getsize(log_path)
        
        return {
            'exists': True,
            'entries': len(lines),
            'size': file_size,
            'path': log_path
        }
    
    except Exception as e:
        print(f"Failed to get activity stats: {e}")
        return {
            'exists': False,
            'entries': 0,
            'size': 0,
            'path': "Error"
        }

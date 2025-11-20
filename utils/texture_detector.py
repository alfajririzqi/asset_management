"""
Utility for detecting external and packed texture files.
Used to skip these textures in file operations to prevent modifying files outside project scope.
"""

import bpy
import os


def detect_external_and_packed_textures(context):
    """
    Detect textures that should be skipped in file operations.
    
    External textures: Files located outside current blend directory
    Packed textures: Files embedded in .blend file
    
    Args:
        context: Blender context
    
    Returns:
        tuple: (external_images, packed_images, local_images)
        - external_images: list of image names outside blend directory
        - packed_images: list of packed image names
        - local_images: list of processable image names
    """
    
    if not bpy.data.filepath:
        return [], [], []
    
    current_dir = os.path.normpath(os.path.dirname(bpy.data.filepath))
    
    external_images = []
    packed_images = []
    local_images = []
    
    for img in bpy.data.images:
        # Skip special images
        if img.name in ('Render Result', 'Viewer Node'):
            continue
        if img.source != 'FILE':
            continue
        
        # Check packed first
        if img.packed_file:
            packed_images.append(img.name)
            continue
        
        if not img.filepath:
            continue
        
        abs_path = bpy.path.abspath(img.filepath)
        abs_path = os.path.normpath(abs_path)
        
        if not os.path.exists(abs_path):
            continue
        
        # Check if external (outside current directory)
        if abs_path.startswith(current_dir):
            local_images.append(img.name)
        else:
            external_images.append(img.name)
    
    return external_images, packed_images, local_images

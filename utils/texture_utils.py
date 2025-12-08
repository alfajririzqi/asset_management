"""
Texture Utility Functions
Shared utilities for texture scanning and UDIM handling across operators.
"""

import bpy
import os
import re


def normalize_udim(path):
    """
    Normalize UDIM texture paths to use <UDIM> placeholder.
    
    Matches Blender's UDIM detection: any 4-digit number in standard range (1001-1100)
    with any separator (., _, -, or standalone).
    
    Examples:
        armor_BaseColor.1001.png  → armor_BaseColor.<UDIM>.png
        texture_color_1050.exr    → texture_color_<UDIM>.exr
        wood-roughness-1025.png   → wood-roughness-<UDIM>.png
        project_2024.png          → project_2024.png (unchanged, out of range)
    
    Args:
        path: File path to normalize
        
    Returns:
        Normalized path with <UDIM> placeholder if applicable
    """
    # Pattern: word boundary + 4 digits + word boundary
    # Matches: _1001, .1001, -1001, or standalone 1001
    udim_pattern = r'\b(\d{4})\b'
    match = re.search(udim_pattern, path)
    
    if match:
        tile_num = int(match.group(1))
        # Standard UDIM range: 1001-1100 (10x10 grid)
        if 1001 <= tile_num <= 1100:
            # Replace first occurrence with <UDIM>
            return path.replace(match.group(1), '<UDIM>', 1)
    
    return path


def get_used_textures(include_material_nodes=True, include_bpy_images=True):
    """
    Get set of all texture paths actually used in the blend file.
    
    This function scans BOTH material shader nodes AND bpy.data.images to ensure
    UDIM textures are properly detected (they may not be in bpy.data.images if not loaded).
    
    Args:
        include_material_nodes: Scan material shader nodes for Image Texture nodes
        include_bpy_images: Scan bpy.data.images for loaded images
        
    Returns:
        set: Normalized absolute paths of all used textures (with UDIM placeholders)
    """
    used_textures = set()
    
    if include_material_nodes:
        # CRITICAL: Scan shader nodes first (includes UDIM references)
        # UDIM textures are NOT in bpy.data.images if not loaded, but ARE in material nodes!
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    img = node.image
                    try:
                        abs_path = bpy.path.abspath(img.filepath)
                        norm_path = os.path.normpath(abs_path)
                        
                        # If already has <UDIM>, keep it as-is
                        if '<UDIM>' not in norm_path:
                            norm_path = normalize_udim(norm_path)
                        
                        used_textures.add(norm_path)
                    except Exception:
                        continue
    
    if include_bpy_images:
        # Also scan bpy.data.images (for images not in materials)
        for img in bpy.data.images:
            if img.source != 'FILE':
                continue
            
            # SKIP: Ignore external link images (library overrides)
            if img.library:
                continue
            
            try:
                abs_path = bpy.path.abspath(img.filepath)
                norm_path = os.path.normpath(abs_path)
                
                # If already has <UDIM>, keep it as-is
                if '<UDIM>' not in norm_path:
                    norm_path = normalize_udim(norm_path)
                
                used_textures.add(norm_path)
            except Exception:
                continue
    
    return used_textures

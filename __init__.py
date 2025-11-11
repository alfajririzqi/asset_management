# ##### BEGIN GPL LICENSE BLOCK #####
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Asset Management",
    "author": "Rizqi Alfajri",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > N Panel",
    "description": "Production-ready asset management with publishing workflow, texture optimization, and version control",
    "category": "Assets",
    "doc_url": "https://github.com/alfajririzqi/asset_management"
}

import bpy
import os
from bpy.app.handlers import persistent
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import AddonPreferences
import bpy.utils.previews
from . import operators, panels

preview_collections = {}

# ============================================================================
# ADDON PREFERENCES
# ============================================================================

class AssetManagementPreferences(AddonPreferences):
    """Addon preferences for Asset Management"""
    bl_idname = __package__
    
    # === DEFAULT PATHS ===
    default_publish_path: StringProperty(
        name="Default Publish Path",
        description="Default folder for publishing assets (auto-loaded when file opens)",
        subtype='DIR_PATH',
        default=""
    )
    
    # === VALIDATION THRESHOLDS ===
    check_texture_resolution: BoolProperty(
        name="Check Texture Resolution",
        description="Show warning if textures exceed maximum resolution during validation",
        default=True
    )
    
    max_texture_resolution: EnumProperty(
        name="Max Texture Resolution",
        description="Maximum texture resolution threshold for validation warning",
        items=[
            ('1024', "1K (1024px)", "Warn if texture exceeds 1024px"),
            ('2048', "2K (2048px)", "Warn if texture exceeds 2048px"),
            ('4096', "4K (4096px)", "Warn if texture exceeds 4096px"),
            ('8192', "8K (8192px)", "Warn if texture exceeds 8192px")
        ],
        default='4096'
    )
    
    # === VALIDATION CHECKS ===
    check_transform_issues: BoolProperty(
        name="Check Transform Issues",
        description="Validate transforms are applied (scale/rotation) before publishing",
        default=True
    )
    
    check_empty_material_slots: BoolProperty(
        name="Check Empty Material Slots",
        description="Validate no empty or unused material slots exist before publishing",
        default=False
    )
    
    check_duplicate_textures: BoolProperty(
        name="Check Duplicate Textures",
        description="Validate no duplicate textures exist (can be optimized)",
        default=True
    )
    
    check_duplicate_materials: BoolProperty(
        name="Check Duplicate Materials",
        description="Validate no duplicate materials exist (can be optimized)",
        default=True
    )
    
    # === SCENE ANALYSIS ===
    analysis_auto_save: BoolProperty(
        name="Auto-Save Analysis Reports",
        description="Automatically save scene analysis reports to /reports folder (Plain Text format, always overwrite)",
        default=False
    )

    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        # === DEFAULT PATHS ===
        box = layout.box()
        box.label(text="Default Paths", icon='FILE_FOLDER')
        
        col = box.column(align=True)
        col.prop(self, "default_publish_path")
        
        # === VALIDATION ===
        box = layout.box()
        box.label(text="Validation Settings", icon='CHECKMARK')
        
        col = box.column(align=True)
        
        # Thresholds
        col.separator()
        col.label(text="Thresholds:", icon='DRIVER')
        col.prop(self, "check_texture_resolution")
        
        # Show max resolution dropdown only if check is enabled
        if self.check_texture_resolution:
            col.prop(self, "max_texture_resolution")
        
        # Validation checks
        col.separator()
        col.label(text="Enable Checks:", icon='SOLO_ON')
        col.prop(self, "check_transform_issues")
        col.prop(self, "check_empty_material_slots")
        col.prop(self, "check_duplicate_textures")
        col.prop(self, "check_duplicate_materials")
        
        
        # === SCENE ANALYSIS ===
        box = layout.box()
        box.label(text="Scene Analysis", icon='VIEWZOOM')
        
        col = box.column(align=True)
        col.prop(self, "analysis_auto_save")
        
        if self.analysis_auto_save:
            info_box = box.box()
            info_col = info_box.column(align=True)
            info_col.scale_y = 0.8
            info_col.label(text="Reports will be saved to:", icon='INFO')
            info_col.label(text="  //reports/", icon='BLANK1')
            info_col.label(text="  • Scene_MaterialUsage.txt", icon='BLANK1')
            info_col.label(text="  • Scene_TextureUsage.txt", icon='BLANK1')
            info_col.label(text="  • Scene_TexturePaths.txt", icon='BLANK1')
            info_col.label(text="Format: Plain Text (.txt), Always overwrite", icon='BLANK1')
        
        
        # === FOOTER ===
        layout.separator()
        footer = layout.row()
        footer.alignment = 'CENTER'
        footer.scale_y = 0.7
        
        # Use custom icon if loaded
        pcoll = preview_collections.get("main")
        if pcoll and "logo_white" in pcoll:
            icon_id = pcoll["logo_white"].icon_id
            footer.label(text="Asset Management v1.0.0 | GPL-3.0 License", icon_value=icon_id)
        else:
            footer.label(text="Asset Management v1.0.0 | GPL-3.0 License", icon='INFO')

# ============================================================================

@persistent
def reset_publish_validation_on_load(dummy):
    """Reset publish validation when file is loaded to ensure fresh check"""
    try:
        scene = bpy.context.scene
        scene.publish_check_done = False
        scene.publish_is_published_file = False
        scene.publish_source_path = ""
        scene.publish_force = False
        scene.publish_libraries_validated = False
        scene.publish_library_count = 0
        scene.publish_library_errors = 0
        scene.publish_library_warnings = 0

        if hasattr(scene, '_publish_detection_cached'):
            delattr(scene, '_publish_detection_cached')
        
        # Auto-load default values from preferences (if empty/default)
        try:
            prefs = bpy.context.preferences.addons[__package__].preferences
            
            # Auto-fill publish path if empty
            if not scene.publish_path and prefs.default_publish_path:
                scene.publish_path = prefs.default_publish_path
        
        except Exception:
            pass  # Preferences not available or not set

    except Exception as e:
        print(f"Reset validation warning: {e}")


def register():
    # Load custom icons
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "panels", "icons")
    
    # Load logo_white.png
    logo_white_path = os.path.join(icons_dir, "logo_white.png")
    if os.path.exists(logo_white_path):
        pcoll.load("logo_white", logo_white_path, 'IMAGE')
    
    preview_collections["main"] = pcoll
    
    # Register preferences first
    bpy.utils.register_class(AssetManagementPreferences)
    
    operators.register()
    panels.register()
    
    # Register app handler for auto-reset validation on file load
    if reset_publish_validation_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(reset_publish_validation_on_load)

def unregister():
    # Unload custom icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    # Unregister app handler
    if reset_publish_validation_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(reset_publish_validation_on_load)
    
    panels.unregister()
    operators.unregister()
    
    # Unregister preferences
    bpy.utils.unregister_class(AssetManagementPreferences)

    if hasattr(bpy.types.Scene, "highpoly_threshold"):
        del bpy.types.Scene.highpoly_threshold
    if hasattr(bpy.types.Scene, "highpoly_use_modifiers"):
        del bpy.types.Scene.highpoly_use_modifiers
    if hasattr(bpy.types.Scene, "highpoly_mode_active"):
        del bpy.types.Scene.highpoly_mode_active
    if hasattr(bpy.types.Scene, "highpoly_original_bg"):
        del bpy.types.Scene.highpoly_original_bg
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
    "version": (1, 2, 2),
    "blender": (3, 6, 0),
    "location": "View3D > N Panel",
    "description": "Production-ready asset management with publishing workflow, texture optimization, and version control",
    "category": "Assets",
    "doc_url": "https://docs-asset-management.vercel.app/"
}

import bpy
import os
import webbrowser
from bpy.app.handlers import persistent
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import AddonPreferences
import bpy.utils.previews
from . import operators, panels

preview_collections = {}

# ============================================================================
# SOCIAL MEDIA OPERATORS
# ============================================================================

class ASSET_OT_OpenInstagram(bpy.types.Operator):
    """Open Instagram profile in browser"""
    bl_idname = "asset.open_instagram"
    bl_label = "Open Instagram"
    bl_description = "Visit Instagram profile"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        webbrowser.open("https://www.instagram.com/rizqyalfajri/")
        self.report({'INFO'}, "Opening Instagram...")
        return {'FINISHED'}


class ASSET_OT_OpenFacebook(bpy.types.Operator):
    """Open Facebook profile in browser"""
    bl_idname = "asset.open_facebook"
    bl_label = "Open Facebook"
    bl_description = "Visit Facebook profile"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        webbrowser.open("https://www.facebook.com/rizqyalfajri/")
        self.report({'INFO'}, "Opening Facebook...")
        return {'FINISHED'}


class ASSET_OT_OpenTikTok(bpy.types.Operator):
    """Open TikTok profile in browser"""
    bl_idname = "asset.open_tiktok"
    bl_label = "Open TikTok"
    bl_description = "Visit TikTok profile"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        webbrowser.open("https://www.tiktok.com/@rizqyalfajri")
        self.report({'INFO'}, "Opening TikTok...")
        return {'FINISHED'}


# ============================================================================
# ADDON PREFERENCES
# ============================================================================

class AssetManagementPreferences(AddonPreferences):
    """Addon preferences for Asset Management"""
    bl_idname = __package__
    
    default_publish_path: StringProperty(
        name="Default Publish Path",
        description="Default folder for publishing assets (auto-loaded when file opens)",
        subtype='DIR_PATH',
        default=""
    )
    
    # Validation Thresholds
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
    
    # Validation Checks
    check_transform_issues: BoolProperty(
        name="Check Transform Issues",
        description="Validate transforms are applied (scale/rotation) before publishing",
        default=False
    )
    
    check_empty_material_slots: BoolProperty(
        name="Check Empty Material Slots",
        description="Validate no empty or unused material slots exist before publishing",
        default=True
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
    
    # Scene Analysis
    analysis_auto_save: BoolProperty(
        name="Auto-Save Analysis Reports",
        description="Automatically save scene analysis reports to /reports folder (Plain Text format, always overwrite)",
        default=False
    )
    
    # Activity Logging
    enable_activity_logging: BoolProperty(
        name="Enable Activity Logging",
        description="Track all operations performed in the addon",
        default=False
    )
    
    activity_log_location: EnumProperty(
        name="Log Location",
        description="Where to save activity log files",
        items=[
            ('PER_PROJECT', "Per-Project", "Save log in each .blend file's folder (.addon_activity.log)", 'FILE_FOLDER', 0),
            ('GLOBAL', "Global", "Save log in addon folder (shared across all projects)", 'WORLD', 1),
            ('CUSTOM', "Custom Path", "Choose custom location for log file", 'FILEBROWSER', 2)
        ],
        default='PER_PROJECT'
    )
    
    activity_log_custom_path: StringProperty(
        name="Custom Log Path",
        description="Custom location for activity log file",
        subtype='FILE_PATH',
        default=""
    )

    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        box = layout.box()
        box.label(text="Default Paths", icon='FILE_FOLDER')
        col = box.column(align=True)
        col.prop(self, "default_publish_path")
        
        box = layout.box()
        box.label(text="Validation Settings", icon='CHECKMARK')
        
        col = box.column(align=True)
        col.separator()
        col.label(text="Thresholds:", icon='DRIVER')
        col.prop(self, "check_texture_resolution")
        
        if self.check_texture_resolution:
            col.prop(self, "max_texture_resolution")
        
        col.separator()
        col.label(text="Enable Checks:", icon='SOLO_ON')
        col.prop(self, "check_transform_issues")
        col.prop(self, "check_empty_material_slots")
        col.prop(self, "check_duplicate_textures")
        col.prop(self, "check_duplicate_materials")
        
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
        
        box = layout.box()
        box.label(text="Activity Tracking", icon='FILE_TEXT')
        col = box.column(align=True)
        col.prop(self, "enable_activity_logging")
        
        if self.enable_activity_logging:
            layout.prop(self, "activity_log_location", text="")
            
            if self.activity_log_location == 'CUSTOM':
                layout.prop(self, "activity_log_custom_path", text="")
                        
            from .utils.activity_logger import get_activity_stats
            stats = get_activity_stats()
            
            box = layout.box()
            col = box.column(align=True)
            col.scale_y = 0.8
            
            if stats['exists']:
                col.label(text=f"ℹ️ Current entries: {stats['entries']}", icon='BLANK1')
                col.label(text=f"ℹ️ File size: {stats['size']} bytes", icon='BLANK1')
            else:
                col.label(text="ℹ️ No activity log yet", icon='INFO')
                col.label(text="ℹ️ Log will be created on first operation", icon='BLANK1')
            
            layout.operator("asset.copy_activity_log_path", icon='COPYDOWN')
        
        layout.separator()
        layout.label(text="Support & Social Media", icon='WORLD')
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 1.2
        
        pcoll = preview_collections.get("main")
        
        if pcoll and "instagram" in pcoll:
            icon_id = pcoll["instagram"].icon_id
            col.operator("asset.open_instagram", text="Instagram", icon_value=icon_id)
        else:
            col.operator("asset.open_instagram", text="Instagram", icon='COMMUNITY')
        
        if pcoll and "facebook" in pcoll:
            icon_id = pcoll["facebook"].icon_id
            col.operator("asset.open_facebook", text="Facebook", icon_value=icon_id)
        else:
            col.operator("asset.open_facebook", text="Facebook", icon='COMMUNITY')
        
        if pcoll and "tiktok" in pcoll:
            icon_id = pcoll["tiktok"].icon_id
            col.operator("asset.open_tiktok", text="TikTok", icon_value=icon_id)
        else:
            col.operator("asset.open_tiktok", text="TikTok", icon='COMMUNITY')


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
        scene.publish_include_libraries = False
        scene.publish_libraries_validated = False
        scene.publish_library_count = 0
        scene.publish_library_errors = 0
        scene.publish_library_warnings = 0
        
        # Clear library selection list
        scene.publish_library_selection.clear()

        if hasattr(scene, '_publish_detection_cached'):
            delattr(scene, '_publish_detection_cached')
        
        # Auto-detect published file status on file open
        from .utils.published_file_detector import detect_published_file_status, update_published_file_cache
        try:
            is_published, source_path = detect_published_file_status(bpy.context)
            update_published_file_cache(bpy.context, is_published, source_path)
        except Exception as e:
            print(f"Published file detection error: {e}")
        
        # Auto-load default publish path from preferences
        try:
            prefs = bpy.context.preferences.addons[__package__].preferences
            if not scene.publish_path and prefs.default_publish_path:
                scene.publish_path = prefs.default_publish_path
        except Exception:
            pass

    except Exception as e:
        print(f"Reset validation warning: {e}")


def register():
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "panels", "icons")
    
    logo_white_path = os.path.join(icons_dir, "logo_white.png")
    if os.path.exists(logo_white_path):
        pcoll.load("logo_white", logo_white_path, 'IMAGE')
    
    instagram_path = os.path.join(icons_dir, "instagram.png")
    if os.path.exists(instagram_path):
        pcoll.load("instagram", instagram_path, 'IMAGE')
    
    facebook_path = os.path.join(icons_dir, "facebook.png")
    if os.path.exists(facebook_path):
        pcoll.load("facebook", facebook_path, 'IMAGE')
    
    tiktok_path = os.path.join(icons_dir, "tiktok.png")
    if os.path.exists(tiktok_path):
        pcoll.load("tiktok", tiktok_path, 'IMAGE')
    
    preview_collections["main"] = pcoll
    
    bpy.utils.register_class(ASSET_OT_OpenInstagram)
    bpy.utils.register_class(ASSET_OT_OpenFacebook)
    bpy.utils.register_class(ASSET_OT_OpenTikTok)
    bpy.utils.register_class(AssetManagementPreferences)
    
    operators.register()
    panels.register()
    
    if reset_publish_validation_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(reset_publish_validation_on_load)


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    if reset_publish_validation_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(reset_publish_validation_on_load)
    
    panels.unregister()
    operators.unregister()
    
    bpy.utils.unregister_class(AssetManagementPreferences)
    bpy.utils.unregister_class(ASSET_OT_OpenTikTok)
    bpy.utils.unregister_class(ASSET_OT_OpenFacebook)
    bpy.utils.unregister_class(ASSET_OT_OpenInstagram)

    if hasattr(bpy.types.Scene, "highpoly_threshold"):
        del bpy.types.Scene.highpoly_threshold
    if hasattr(bpy.types.Scene, "highpoly_use_modifiers"):
        del bpy.types.Scene.highpoly_use_modifiers
    if hasattr(bpy.types.Scene, "highpoly_mode_active"):
        del bpy.types.Scene.highpoly_mode_active
    if hasattr(bpy.types.Scene, "highpoly_original_bg"):
        del bpy.types.Scene.highpoly_original_bg
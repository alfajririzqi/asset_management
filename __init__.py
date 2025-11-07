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
    "location": "View3D > N Panel > Asset Management",
    "description": "Streamline asset publishing, texture optimization, and version control for production workflows",
    "category": "Pipeline",
    "license": "GPL-3.0",
    "doc_url": "https://github.com/alfajririzqi/asset_management",
}

import bpy
from bpy.app.handlers import persistent
from . import operators, panels


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

    except Exception as e:
        print(f"Reset validation warning: {e}")


def register():
    operators.register()
    panels.register()
    
    # Register app handler for auto-reset validation on file load
    if reset_publish_validation_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(reset_publish_validation_on_load)

def unregister():
    # Unregister app handler
    if reset_publish_validation_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(reset_publish_validation_on_load)
    
    panels.unregister()
    operators.unregister()

    if hasattr(bpy.types.Scene, "highpoly_threshold"):
        del bpy.types.Scene.highpoly_threshold
    if hasattr(bpy.types.Scene, "highpoly_use_modifiers"):
        del bpy.types.Scene.highpoly_use_modifiers
    if hasattr(bpy.types.Scene, "highpoly_mode_active"):
        del bpy.types.Scene.highpoly_mode_active
    if hasattr(bpy.types.Scene, "highpoly_original_bg"):
        del bpy.types.Scene.highpoly_original_bg
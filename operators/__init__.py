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

from . import (
    optimize_linked,
    optimize_materials,
    optimize_textures,
    check_highpoly,
    check_transform,
    auto_correct_maps,
    downgrade_resolution,
    convert_image_format,
    consolidate_textures,
    cleanup_unused_textures,
    restore_image_format,
    restore_resolution,
    versioning,
    check_scene,
    clear_orphan_data,
    clear_material_slots,
    publish,
    check_publish
)

modules = [
    optimize_linked,
    optimize_materials,
    optimize_textures,
    check_highpoly,
    check_transform,
    auto_correct_maps,
    downgrade_resolution,
    convert_image_format,
    consolidate_textures,
    cleanup_unused_textures,
    restore_image_format,
    restore_resolution,
    versioning,
    check_scene,
    clear_orphan_data,
    clear_material_slots,
    publish,
    check_publish
]

def register():
    for mod in modules:
        mod.register()

def unregister():
    for mod in reversed(modules):
        mod.unregister()
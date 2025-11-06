import bpy
import os
from collections import defaultdict

class ASSET_OT_optimize_texture_duplicates(bpy.types.Operator):
    """Merge duplicate images that reference the same file path into a single image."""
    bl_idname = "asset.optimize_texture_duplicates"
    bl_label = "Optimize Texture Duplicates"
    bl_description = "Merge duplicate textures (same file path) into single texture"
    bl_options = {'REGISTER', 'UNDO'}

    duplicate_groups = []

    def get_sort_key(self, img):
        """Return a sort key for image selection.

        Priority:
        - (0, 0) for names without a three-digit numeric suffix (preferred)
        - (1, n) for names with a three-digit numeric suffix like '.001' (lower priority)
        """
        name = img.name
        parts = name.rsplit('.', 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 3:
            suffix_num = int(parts[1])
            return (1, suffix_num)
        return (0, 0)

    def find_duplicates(self, context):
        """Find groups of images that share identical filepaths (external images only)."""
        image_groups = defaultdict(list)
        for img in bpy.data.images:
            if img.filepath:
                image_groups[img.filepath].append(img)
        return [images for images in image_groups.values() if len(images) > 1]

    def invoke(self, context, event):
        self.duplicate_groups = self.find_duplicates(context)
        if not self.duplicate_groups:
            self.report({'INFO'}, "No duplicate textures detected")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Textures to be optimized:", icon='INFO')

        for group in self.duplicate_groups:
            base = group[0]
            layout.separator()
            layout.label(text=f" • Base: {base.name}", icon='TEXTURE')
            for img in group[1:]:
                layout.label(text=f"   → {img.name}", icon='LINKED')

    def execute(self, context):
        textures_removed = 0
        for group in self.duplicate_groups:
            images_sorted = sorted(group, key=self.get_sort_key)
            main_image = images_sorted[0]

            for img in images_sorted[1:]:
                for material in bpy.data.materials:
                    if material.use_nodes:
                        for node in material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.image == img:
                                node.image = main_image
                bpy.data.images.remove(img)
                textures_removed += 1

        bpy.ops.outliner.orphans_purge(do_recursive=True)

        self.report(
            {'INFO'},
            f"{textures_removed} texture duplicates removed | Total unique textures: {len(bpy.data.images)}"
        )
        return {'FINISHED'}


class TEXTURE_OT_BatchRename(bpy.types.Operator):
    """Apply batch renaming rules to image texture names."""
    bl_idname = "texture.batch_rename"
    bl_label = "Batch Rename Textures"
    bl_description = "Apply batch renaming rules to image texture names"

    def execute(self, context):
        props = context.scene.texture_batch_renamer
        for img in bpy.data.images:
            if img.source != 'FILE':
                continue
            name = img.name
            for pair in props.find_replace:
                if pair.find:
                    name = name.replace(pair.find, pair.replace)
            if props.prefix_text and not name.startswith(props.prefix_text):
                name = props.prefix_text + name
            if props.suffix_text and not name.endswith(props.suffix_text):
                name += props.suffix_text
            if name != img.name:
                img.name = name
        self.report({'INFO'}, "Textures renamed successfully")
        return {'FINISHED'}


class TEXTURE_OT_BatchRenameFiles(bpy.types.Operator):
    bl_idname = "texture.batch_rename_files"
    bl_label = "Rename Texture Files"
    bl_description = "Rename texture files on disk to match datablock names in Blender (extension always from file)"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        blend_dir = os.path.dirname(bpy.data.filepath)
        if not blend_dir:
            self.report({'ERROR'}, ".blend file must be saved first")
            return {'CANCELLED'}

        renamed, skipped, errors = 0, 0, 0

        for img in bpy.data.images:
            if img.packed_file or not img.filepath_raw:
                skipped += 1
                continue

            abs_path = bpy.path.abspath(img.filepath_raw)
            if not os.path.exists(abs_path):
                skipped += 1
                continue

            base_dir = os.path.dirname(abs_path)

            _, ext = os.path.splitext(abs_path)
            if not ext:
                self.report({'WARNING'}, f"No extension found for {abs_path}, skipped")
                skipped += 1
                continue

            name_root, _ = os.path.splitext(img.name)
            safe_root = bpy.path.clean_name(name_root)

            new_filename = f"{safe_root}{ext}"
            new_path = os.path.join(base_dir, new_filename)

            if os.path.basename(abs_path) == new_filename:
                skipped += 1
                continue

            if os.path.exists(new_path):
                self.report({'WARNING'}, f"File already exists: {new_path}")
                skipped += 1
                continue

            try:
                os.rename(abs_path, new_path)
                rel = bpy.path.relpath(new_path, start=blend_dir)
                img.filepath = rel
                img.filepath_raw = rel
                renamed += 1
            except Exception as e:
                self.report({'ERROR'}, f"Error renaming {os.path.basename(abs_path)}: {str(e)}")
                errors += 1

        self.report({'INFO'}, f"Done: {renamed} renamed, {skipped} skipped, {errors} errors")
        return {'FINISHED'}


class TEXTURE_OT_AddFindReplace(bpy.types.Operator):
    bl_idname = "texture.add_findreplace"
    bl_label = "Add Find/Replace"

    def execute(self, context):
        props = context.scene.texture_batch_renamer
        props.find_replace.add()
        props.find_replace_index = len(props.find_replace) - 1
        return {'FINISHED'}


class TEXTURE_OT_RemoveFindReplace(bpy.types.Operator):
    bl_idname = "texture.remove_findreplace"
    bl_label = "Remove Find/Replace"

    def execute(self, context):
        props = context.scene.texture_batch_renamer
        idx = props.find_replace_index
        if props.find_replace:
            props.find_replace.remove(idx)
            props.find_replace_index = max(0, idx - 1)
        return {'FINISHED'}


class TEXTURE_OT_ClearRule(bpy.types.Operator):
    bl_idname = "texture.clear_rule"
    bl_label = "Clear Rule"
    bl_description = "Reset all batch rename rules to default settings"

    def execute(self, context):
        props = context.scene.texture_batch_renamer
        props.find_replace.clear()
        props.find_replace_index = 0
        props.prefix_text = ""
        props.suffix_text = ""
        self.report({'INFO'}, "All batch rename rules have been reset")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_optimize_texture_duplicates)
    bpy.utils.register_class(TEXTURE_OT_BatchRename)
    bpy.utils.register_class(TEXTURE_OT_BatchRenameFiles)
    bpy.utils.register_class(TEXTURE_OT_AddFindReplace)
    bpy.utils.register_class(TEXTURE_OT_RemoveFindReplace)
    bpy.utils.register_class(TEXTURE_OT_ClearRule)


def unregister():
    bpy.utils.unregister_class(TEXTURE_OT_ClearRule)
    bpy.utils.unregister_class(TEXTURE_OT_RemoveFindReplace)
    bpy.utils.unregister_class(TEXTURE_OT_AddFindReplace)
    bpy.utils.unregister_class(TEXTURE_OT_BatchRenameFiles)
    bpy.utils.unregister_class(TEXTURE_OT_BatchRename)
    bpy.utils.unregister_class(ASSET_OT_optimize_texture_duplicates)

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
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        
        total_duplicates = sum(len(group) - 1 for group in self.duplicate_groups)
        total_groups = len(self.duplicate_groups)
        
        # Header with summary
        box = layout.box()
        box.label(text=f"🖼️ Found {total_groups} duplicate group(s)", icon='INFO')
        box.label(text=f"Total {total_duplicates} texture(s) will be merged", icon='TEXTURE')
        
        layout.separator()
        
        max_display_groups = 10
        groups_to_show = self.duplicate_groups[:max_display_groups]
        
        if total_groups <= 5:
            # 1 COLUMN LAYOUT (vertical)
            for i, group in enumerate(groups_to_show):
                if i > 0:
                    layout.separator(factor=0.5)
                
                base = group[0]
                duplicates = group[1:]
                
                box = layout.box()
                box.label(text=f"Base: {base.name}", icon='TEXTURE')
                
                if duplicates:
                    col = box.column(align=True)
                    col.scale_y = 0.8
                    
                    max_items = 3
                    for img in duplicates[:max_items]:
                        col.label(text=f"  • {img.name}", icon='LINKED')
                    
                    if len(duplicates) > max_items:
                        col.label(text=f"  ... and {len(duplicates) - max_items} more", icon='THREE_DOTS')
        else:
            # 2 COLUMN TABLE LAYOUT (side by side)
            split = layout.split(factor=0.5)
            col_left = split.column()
            col_right = split.column()
            
            for i, group in enumerate(groups_to_show):
                base = group[0]
                duplicates = group[1:]
                
                col = col_left if i < 5 else col_right
                
                if i % 5 > 0:
                    col.separator(factor=0.5)
                
                box = col.box()
                box.label(text=f"Base: {base.name}", icon='TEXTURE')
                
                if duplicates:
                    sub = box.column(align=True)
                    sub.scale_y = 0.8
                    
                    max_items = 3
                    for img in duplicates[:max_items]:
                        sub.label(text=f"  • {img.name}", icon='LINKED')
                    
                    if len(duplicates) > max_items:
                        sub.label(text=f"  ... and {len(duplicates) - max_items} more", icon='THREE_DOTS')
        
        # Show "more groups" if total > 5
        if total_groups > max_display_groups:
            layout.separator()
            row = layout.row()
            row.label(text=f"... and {total_groups - max_display_groups} more groups", icon='THREE_DOTS')

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
            
            # Apply find/replace
            for pair in props.find_replace:
                if pair.find:
                    name = name.replace(pair.find, pair.replace)
            
            # Split name and extension
            if '.' in name:
                base_name, extension = name.rsplit('.', 1)
                extension = '.' + extension
            else:
                base_name = name
                extension = ''
            
            if props.prefix_text and not base_name.startswith(props.prefix_text):
                base_name = props.prefix_text + base_name
            
            if props.suffix_text and not base_name.endswith(props.suffix_text):
                base_name += props.suffix_text
            
            # Reconstruct full name
            name = base_name + extension
            
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
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Rename files on disk to match Blender names?", icon='FILE_REFRESH')
        layout.separator()
        layout.label(text="Note: External & packed textures will be skipped", icon='INFO')

    def execute(self, context):
        from ..utils.texture_detector import detect_external_and_packed_textures
        
        blend_dir = os.path.dirname(bpy.data.filepath)
        if not blend_dir:
            self.report({'ERROR'}, ".blend file must be saved first")
            return {'CANCELLED'}
        
        # Detect textures to skip
        external_imgs, packed_imgs, local_imgs = detect_external_and_packed_textures(context)

        renamed = 0
        skipped = 0
        skipped_external = 0
        skipped_packed = 0
        errors = 0

        for img in bpy.data.images:
            # Skip packed textures
            if img.name in packed_imgs:
                skipped_packed += 1
                continue
            
            # Skip external textures
            if img.name in external_imgs:
                skipped_external += 1
                continue
            
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

        msg = f"Renamed: {renamed}"
        if skipped > 0:
            msg += f" | Skipped: {skipped}"
        if skipped_external > 0:
            msg += f" | External: {skipped_external}"
        if skipped_packed > 0:
            msg += f" | Packed: {skipped_packed}"
        if errors > 0:
            msg += f" | Errors: {errors}"
        
        self.report({'INFO'}, msg)
        
        # Log activity
        from ..utils.activity_logger import log_activity
        details = f"Renamed: {renamed}"
        if skipped_external > 0:
            details += f" | External: {skipped_external}"
        if skipped_packed > 0:
            details += f" | Packed: {skipped_packed}"
        if errors > 0:
            details += f" | Errors: {errors}"
        
        log_activity("BATCH_RENAME_FILES", details, context)
        
        return {'FINISHED'}


class TEXTURE_OT_AddFindReplace(bpy.types.Operator):
    bl_idname = "texture.add_findreplace"
    bl_label = "Add Find/Replace"
    bl_description = "Add a new find and replace rule for batch texture renaming"

    def execute(self, context):
        props = context.scene.texture_batch_renamer
        props.find_replace.add()
        props.find_replace_index = len(props.find_replace) - 1
        return {'FINISHED'}


class TEXTURE_OT_RemoveFindReplace(bpy.types.Operator):
    bl_idname = "texture.remove_findreplace"
    bl_label = "Remove Find/Replace"
    bl_description = "Remove the selected find and replace rule from the list"

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

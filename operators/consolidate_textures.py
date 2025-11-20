import bpy
import os
import shutil


class ASSET_OT_ConsolidateTextures(bpy.types.Operator):
    """Move or copy external textures into the local 'textures' folder and retarget image paths."""
    bl_idname = "asset.consolidate_textures"
    bl_label = "Consolidate Textures"
    bl_description = "Move or copy external textures to the local 'textures' folder and repath them"

    operation_mode: bpy.props.EnumProperty(
        name="Operation",
        description="Choose to move or copy texture files",
        items=[
            ('MOVE', 'Move Files', 'Move texture files to textures folder (original files will be deleted)', 'FORWARD', 0),
            ('COPY', 'Copy Files', 'Copy texture files to textures folder (keep original files)', 'DUPLICATE', 1),
        ],
        default='COPY'
    )

    textures_to_move = []
    packed_textures = []
    missing_textures = []

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first.")
            return {'CANCELLED'}

        blend_dir = os.path.dirname(bpy.data.filepath)
        target_dir = os.path.join(blend_dir, "textures")
        
        self.textures_to_move = []
        self.packed_textures = []
        self.missing_textures = []

        for img in bpy.data.images:
            if img.source != 'FILE':
                continue
            
            if img.packed_file:
                self.packed_textures.append(img.name)
                continue
            
            if not img.filepath_raw:
                continue

            source_path = bpy.path.abspath(img.filepath_raw)
            
            if not os.path.exists(source_path):
                self.missing_textures.append({
                    'name': img.name,
                    'path': img.filepath_raw
                })
                continue
            
            try:
                if os.path.commonpath([source_path, target_dir]) == target_dir:
                    continue
            except ValueError:
                pass

            filename = os.path.basename(source_path)
            dest_path = os.path.join(target_dir, filename)
            
            self.textures_to_move.append({
                "image": img,
                "source_path": source_path,
                "dest_path": dest_path,
                "filename": filename,
            })

        if self.textures_to_move or self.packed_textures or self.missing_textures:
            return context.window_manager.invoke_props_dialog(self)

        self.report({'INFO'}, "All textures are already in the local 'textures' folder.")
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Operation Mode:", icon='SETTINGS')
        layout.prop(self, "operation_mode", expand=True)
        
        layout.separator()
        
        if self.missing_textures:
            box = layout.box()
            box.alert = True
            box.label(text=f"⚠️ MISSING TEXTURES ({len(self.missing_textures)}):", icon='ERROR')
            
            col = box.column(align=True)
            for miss in self.missing_textures[:3]:
                col.label(text=f"  • {miss['name']}", icon='BLANK1')
                col.label(text=f"    Path: {miss['path']}", icon='BLANK1')
            
            if len(self.missing_textures) > 3:
                col.label(text=f"  • ... and {len(self.missing_textures) - 3} more", icon='BLANK1')
            
            layout.separator()
        
        # Packed textures info
        if self.packed_textures:
            box = layout.box()
            box.label(text=f"✅ PACKED TEXTURES ({len(self.packed_textures)}) - Skipped:", icon='PACKAGE')
            
            col = box.column(align=True)
            for packed_name in self.packed_textures[:3]:
                col.label(text=f"  • {packed_name}", icon='BLANK1')
            
            if len(self.packed_textures) > 3:
                col.label(text=f"  • ... and {len(self.packed_textures) - 3} more", icon='BLANK1')
            
            layout.separator()
        
        # Textures to consolidate
        if self.textures_to_move:
            layout.label(text=f"🔄 WILL CONSOLIDATE ({len(self.textures_to_move)}):", icon='INFO')

            for tex_info in self.textures_to_move[:3]:
                box = layout.box()
                col = box.column(align=True)
                col.label(text=f"{tex_info['filename']}", icon='IMAGE_DATA')
                col.label(text=f"From: {tex_info['source_path']}", icon='BLANK1')
                col.label(text=f"To:   {tex_info['dest_path']}", icon='BLANK1')

            if len(self.textures_to_move) > 3:
                layout.label(text=f"... and {len(self.textures_to_move) - 3} more.", icon='BLANK1')

            layout.separator()
            if self.operation_mode == 'MOVE':
                layout.label(text="⚠️ This will MOVE files on your disk.", icon='ERROR')
                layout.label(text="Original files will be deleted!", icon='ERROR')
            else:
                layout.label(text="ℹ️ This will COPY files to textures folder.", icon='INFO')
                layout.label(text="Original files will be kept.", icon='CHECKMARK')
        else:
            layout.label(text="No textures to consolidate.", icon='INFO')
            if not self.missing_textures:
                layout.label(text="All textures are already in ./textures", icon='CHECKMARK')

    def execute(self, context):
        from ..utils.activity_logger import log_activity
        
        if not self.textures_to_move:
            self.report({'INFO'}, "No textures to consolidate.")
            return {'CANCELLED'}
        
        moved_count = 0
        error_count = 0
        skipped_count = 0
        blend_dir = os.path.dirname(bpy.data.filepath)
        target_dir = os.path.join(blend_dir, "textures")
        os.makedirs(target_dir, exist_ok=True)

        for tex_info in self.textures_to_move:
            img = tex_info['image']
            source_path = tex_info['source_path']
            dest_path = tex_info['dest_path']
            filename = tex_info['filename']

            try:
                if os.path.exists(dest_path):
                    skipped_count += 1
                    continue

                if self.operation_mode == 'MOVE':
                    shutil.move(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
                
                img.filepath_raw = dest_path
                img.filepath = bpy.path.relpath(dest_path, start=blend_dir)
                
                try:
                    img.reload()
                except:
                    pass
                
                moved_count += 1
                
            except Exception as e:
                error_count += 1
                self.report({'ERROR'}, f"Failed to move {filename}: {e}")

        # Build result message
        operation_text = "Moved" if self.operation_mode == 'MOVE' else "Copied"
        msg = f"✅ {operation_text}: {moved_count}"
        if skipped_count > 0:
            msg += f" • Skipped: {skipped_count} (already exists)"
        if error_count > 0:
            msg += f" • Errors: {error_count}"
        if len(self.packed_textures) > 0:
            msg += f" • Packed: {len(self.packed_textures)} (skipped)"
        if len(self.missing_textures) > 0:
            msg += f" • Missing: {len(self.missing_textures)} (not found)"
        
        self.report({'INFO'}, msg)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_ConsolidateTextures)


def unregister():
    bpy.utils.unregister_class(ASSET_OT_ConsolidateTextures)
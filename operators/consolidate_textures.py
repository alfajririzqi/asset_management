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
    
    conflict_resolution_mode: bpy.props.EnumProperty(
        name="Conflict Action",
        description="How to handle files that already exist in textures/ folder",
        items=[
            ('RELINK', 'Re-link Only', 'Just update path to local file (recommended if same file)', 'LINKED', 0),
            ('OVERWRITE', 'Overwrite', 'Replace local file with external file', 'FILE_REFRESH', 1),
            ('SKIP', 'Skip', 'Keep external path, do not consolidate', 'PANEL_CLOSE', 2),
        ],
        default='RELINK'
    )
    
    unpack_packed_textures: bpy.props.BoolProperty(
        name="Unpack Packed Textures",
        description="Unpack packed textures to /textures folder",
        default=False
    )

    textures_to_move = []
    packed_textures = []
    missing_textures = []
    conflicting_textures = []  # Same filename exists in target

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first.")
            return {'CANCELLED'}

        blend_dir = os.path.dirname(bpy.data.filepath)
        target_dir = os.path.join(blend_dir, "textures")
        
        self.textures_to_move = []
        self.packed_textures = []
        self.missing_textures = []
        self.conflicting_textures = []
        self.conflict_actions = {}

        for img in bpy.data.images:
            if img.source != 'FILE':
                continue
            
            # SKIP: Ignore external link images (library overrides)
            if img.library:
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
            
            # Check for file conflict
            if os.path.exists(dest_path):
                # Compare by date modified (exactly same = same file)
                source_mtime = os.path.getmtime(source_path)
                dest_mtime = os.path.getmtime(dest_path)
                source_size = os.path.getsize(source_path)
                dest_size = os.path.getsize(dest_path)
                
                is_same_file = (source_mtime == dest_mtime and source_size == dest_size)
                
                self.conflicting_textures.append({
                    "image": img,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "filename": filename,
                    "source_mtime": source_mtime,
                    "dest_mtime": dest_mtime,
                    "source_size": source_size,
                    "dest_size": dest_size,
                    "is_same_file": is_same_file,
                })
            else:
                self.textures_to_move.append({
                    "image": img,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "filename": filename,
                })

        # Auto-select default conflict resolution based on detection
        if self.conflicting_textures:
            same_count = sum(1 for c in self.conflicting_textures if c['is_same_file'])
            # If majority are same files, default to RELINK
            self.conflict_resolution_mode = 'RELINK' if same_count > len(self.conflicting_textures) / 2 else 'OVERWRITE'
        
        if self.textures_to_move or self.conflicting_textures or self.packed_textures or self.missing_textures:
            return context.window_manager.invoke_props_dialog(self)

        self.report({'INFO'}, "All textures are already in the local 'textures' folder.")
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        
        # Conflicts section first (most important)
        if self.conflicting_textures:
            box = layout.box()
            box.label(text=f"⚠️ FILE CONFLICTS ({len(self.conflicting_textures)}):", icon='ERROR')
            
            # Count same vs different files
            same_count = sum(1 for c in self.conflicting_textures if c['is_same_file'])
            diff_count = len(self.conflicting_textures) - same_count
            
            col = box.column(align=True)
            if same_count > 0:
                col.label(text=f"  • {same_count} file(s) already exist (same date & size)", icon='CHECKMARK')
            if diff_count > 0:
                col.label(text=f"  • {diff_count} file(s) exist but different (date or size mismatch)", icon='ERROR')
            
            layout.separator()
            
            # Show first 3 conflicts (compact)
            for conflict in self.conflicting_textures[:3]:
                row = layout.row()
                row.label(text=conflict['filename'], icon='IMAGE_DATA')
                if conflict['is_same_file']:
                    row.label(text="(Same file)", icon='LINKED')
                else:
                    row.label(text="(Different)", icon='ERROR')
            
            if len(self.conflicting_textures) > 3:
                layout.label(text=f"... and {len(self.conflicting_textures) - 3} more.", icon='BLANK1')
            
            layout.separator()
            
            # Batch action for ALL conflicts
            box = layout.box()
            box.label(text="Conflict Resolution (applies to all):", icon='SETTINGS')
            
            row = box.row(align=True)
            row.prop_enum(self, "conflict_resolution_mode", 'RELINK')
            row.prop_enum(self, "conflict_resolution_mode", 'OVERWRITE')
            row.prop_enum(self, "conflict_resolution_mode", 'SKIP')
            
            # Show recommendation based on majority
            col = box.column(align=True)
            if same_count > diff_count:
                col.label(text="✅ Re-link recommended (most files are the same)", icon='INFO')
            elif diff_count > 0:
                col.label(text="⚠️ Caution: Some files are different", icon='ERROR')
            
            layout.separator()
        
        # Operation mode (only show if there are non-conflict textures)
        if self.textures_to_move:
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
            box.label(text=f"📦 PACKED TEXTURES ({len(self.packed_textures)}):", icon='PACKAGE')
            
            col = box.column(align=True)
            for packed_name in self.packed_textures[:3]:
                col.label(text=f"  • {packed_name}", icon='BLANK1')
            
            if len(self.packed_textures) > 3:
                col.label(text=f"  • ... and {len(self.packed_textures) - 3} more", icon='BLANK1')
            
            box.separator()
            
            # Toggle to unpack
            row = box.row()
            row.prop(self, "unpack_packed_textures", toggle=True)
            
            # Info text
            info_col = box.column(align=True)
            info_col.scale_y = 0.8
            if self.unpack_packed_textures:
                info_col.label(text="✅ Will unpack to /textures folder", icon='BLANK1')
            else:
                info_col.label(text="ℹ️ Packed textures will remain embedded", icon='BLANK1')
            
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
        
        if not self.textures_to_move and not self.conflicting_textures:
            self.report({'INFO'}, "No textures to consolidate.")
            return {'CANCELLED'}
        
        moved_count = 0
        relinked_count = 0
        overwritten_count = 0
        skipped_count = 0
        error_count = 0
        blend_dir = os.path.dirname(bpy.data.filepath)
        target_dir = os.path.join(blend_dir, "textures")
        os.makedirs(target_dir, exist_ok=True)

        # Handle conflicting textures with batch action
        action = self.conflict_resolution_mode  # Use same action for all conflicts
        
        for conflict in self.conflicting_textures:
            img = conflict['image']
            source_path = conflict['source_path']
            dest_path = conflict['dest_path']
            filename = conflict['filename']
            
            try:
                if action == 'RELINK':
                    # Just update the path, don't copy/move
                    img.filepath_raw = dest_path
                    img.filepath = bpy.path.relpath(dest_path, start=blend_dir)
                    try:
                        img.reload()
                    except:
                        pass
                    relinked_count += 1
                    
                elif action == 'OVERWRITE':
                    # Overwrite the existing file
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
                    overwritten_count += 1
                    
                elif action == 'SKIP':
                    # Do nothing
                    skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                self.report({'ERROR'}, f"Failed to process conflict {filename}: {e}")

        # Handle regular textures (no conflicts)
        for tex_info in self.textures_to_move:
            img = tex_info['image']
            source_path = tex_info['source_path']
            dest_path = tex_info['dest_path']
            filename = tex_info['filename']

            try:
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
                self.report({'ERROR'}, f"Failed to consolidate {filename}: {e}")

        # Handle packed textures unpacking (if enabled)
        unpacked_count = 0
        if self.unpack_packed_textures:
            textures_dir = os.path.join(blend_dir, "textures")
            os.makedirs(textures_dir, exist_ok=True)
            
            for img in bpy.data.images:
                # Skip non-file sources
                if img.source != 'FILE':
                    continue
                
                # Skip library images
                if img.library:
                    continue
                
                # Only unpack if packed
                if img.packed_file:
                    try:
                        # Set filepath to textures folder
                        img.filepath = f"//textures/{img.name}"
                        
                        # Unpack to local file
                        img.unpack(method='WRITE_LOCAL')
                        
                        unpacked_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        self.report({'ERROR'}, f"Failed to unpack {img.name}: {e}")

        # Build result message
        operation_text = "Moved" if self.operation_mode == 'MOVE' else "Copied"
        msg_parts = []
        
        if moved_count > 0:
            msg_parts.append(f"{operation_text}: {moved_count}")
        if relinked_count > 0:
            msg_parts.append(f"Re-linked: {relinked_count}")
        if overwritten_count > 0:
            msg_parts.append(f"Overwritten: {overwritten_count}")
        if skipped_count > 0:
            msg_parts.append(f"Skipped: {skipped_count}")
        if error_count > 0:
            msg_parts.append(f"Errors: {error_count}")
        if unpacked_count > 0:
            msg_parts.append(f"Unpacked: {unpacked_count}")
        if len(self.packed_textures) > 0 and not self.unpack_packed_textures:
            msg_parts.append(f"Packed: {len(self.packed_textures)} (skipped)")
        if len(self.missing_textures) > 0:
            msg_parts.append(f"Missing: {len(self.missing_textures)} (not found)")
        
        msg = "✅ " + " • ".join(msg_parts) if msg_parts else "No textures consolidated"
        
        self.report({'INFO'}, msg)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_ConsolidateTextures)


def unregister():
    bpy.utils.unregister_class(ASSET_OT_ConsolidateTextures)
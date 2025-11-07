import bpy
import os


class ASSET_PT_Publish(bpy.types.Panel):
    """Asset Publishing Panel"""
    bl_label = "Publishing"
    bl_idname = "ASSET_PT_publish"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Pre-Publish Check Button
        box = layout.box()
        box.label(text="Validation:", icon='CHECKMARK')
        
        row = box.row()
        row.scale_y = 1.3
        row.operator("asset.check_publish", text="Run Pre-Publish Checks", icon='VIEWZOOM')
        
        if not bpy.data.filepath:
            row.enabled = False
        
        # Show validation results if check has been run
        if scene.publish_check_done:
            layout.separator()
            
            # Published File Warning (if detected)
            if scene.publish_is_published_file:
                warning_box = layout.box()
                warning_box.alert = True
                warning_box.label(text="🚫 PUBLISHED FILE DETECTED", icon='ERROR')
                col = warning_box.column(align=True)
                col.scale_y = 0.8
                if scene.publish_source_path:
                    col.label(text=f"Source: {scene.publish_source_path}", icon='BLANK1')
                col.label(text="Cannot publish from publish directory!", icon='BLANK1')
                col.label(text="This prevents recursive versioning (v001_v001)", icon='BLANK1')
                
                layout.separator()
            
            # Validation Results
            layout.separator()
            result_box = layout.box()
            result_box.label(text="Validation Results:", icon='PRESET_NEW')
            col = result_box.column(align=True)
            
            # Textures folder
            if scene.publish_textures_exist:
                col.label(text=f"Textures folder: {scene.publish_texture_count} files", icon='CHECKMARK')
            else:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text="Textures folder missing (will publish without textures)", icon='ERROR')
                else:
                    col.label(text="Textures folder missing (will publish without textures)", icon='INFO')
            
            # External textures
            if scene.publish_external_count == 0:
                col.label(text="All textures consolidated", icon='CHECKMARK')
            else:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_external_count} external textures (can force)", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_external_count} external textures (can force)", icon='INFO')
            
            # Missing textures
            if scene.publish_missing_count == 0:
                col.label(text="No missing textures", icon='CHECKMARK')
            else:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_missing_count} missing textures (can force)", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_missing_count} missing textures (can force)", icon='INFO')
            
            # Packed textures
            if scene.publish_packed_count > 0:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_packed_count} packed textures", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_packed_count} packed textures", icon='INFO')
            
            # Orphan data
            if scene.publish_orphan_count > 0:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_orphan_count} orphan data blocks", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_orphan_count} orphan data blocks", icon='INFO')
            else:
                col.label(text="No orphan data", icon='CHECKMARK')
            
            # Force Publish option (if has warnings)
            if scene.publish_has_warnings:
                layout.separator()
                force_box = layout.box()
                force_box.prop(scene, "publish_force", text="Force Publish (ignore warnings)", icon='ERROR')
                
                if scene.publish_force:
                    info_col = force_box.column(align=True)
                    info_col.scale_y = 0.7
                    info_col.label(text="⚠️ All warnings will be ignored", icon='BLANK1')
                    info_col.label(text="⚠️ You take full responsibility", icon='BLANK1')
        
        layout.separator()
        
        # ====================================================================
        # LINKED LIBRARIES SECTION
        # ====================================================================
        
        library_box = layout.box()
        library_box.label(text="Linked Libraries:", icon='LINKED')
        
        # Include libraries checkbox (enabled only after check)
        row = library_box.row()
        row.prop(scene, "publish_include_libraries", text="Publish Linked Libraries")
        
        # Disable if published file OR if check not done
        if scene.publish_is_published_file:
            row.enabled = False
            info_row = library_box.row()
            info_row.scale_y = 0.7
            info_row.label(text="⚠ Cannot modify from published file", icon='INFO')
        elif not scene.publish_check_done:
            row.enabled = False
            info_row = library_box.row()
            info_row.scale_y = 0.7
            info_row.label(text="⚠ Run 'Check Publish Readiness' first", icon='INFO')
        
        # Only show library details if enabled
        if scene.publish_include_libraries:
            library_box.separator(factor=0.5)
            
            # Validate button
            row = library_box.row()
            row.scale_y = 1.2
            row.operator("asset.validate_libraries", text="Scan & Validate Libraries", icon='VIEWZOOM')
            
            # Show validation results if validated
            if scene.publish_libraries_validated:
                library_box.separator(factor=0.5)
                
                # Summary
                summary_row = library_box.row(align=True)
                summary_row.label(text=f"Found: {scene.publish_library_count} libraries", icon='BLANK1')
                
                if scene.publish_library_errors > 0:
                    error_col = summary_row.column()
                    error_col.alert = True
                    error_col.label(text=f"✗ {scene.publish_library_errors} errors", icon='ERROR')
                
                if scene.publish_library_warnings > 0:
                    warn_col = summary_row.column()
                    warn_col.alert = True
                    warn_col.label(text=f"⚠ {scene.publish_library_warnings} warnings", icon='INFO')
                
                # Library selection list
                if scene.publish_library_count > 0:
                    library_box.separator(factor=0.5)
                    
                    # Select all checkbox
                    row = library_box.row()
                    row.prop(scene, "publish_select_all_libraries", text="Select All")
                    # Disable if published file
                    if scene.publish_is_published_file:
                        row.enabled = False
                    
                    library_box.separator(factor=0.3)
                    
                    # List of libraries with checkboxes + action buttons
                    lib_list_box = library_box.box()
                    lib_list_box.label(text="Library Selection:", icon='OUTLINER')
                    
                    for item in scene.publish_library_selection:
                        # Indentation based on depth
                        row = lib_list_box.row(align=True)
                        
                        # Add indent spaces (visual hierarchy)
                        indent = "  " * (item.depth - 1) if item.depth > 1 else ""
                        
                        # Checkbox
                        checkbox_col = row.column()
                        checkbox_col.prop(item, "selected", text="")
                        # Disable checkbox if published file
                        if scene.publish_is_published_file:
                            checkbox_col.enabled = False
                        
                        # Library name with depth indicator
                        depth_icon = 'OUTLINER_OB_MESH' if item.depth == 1 else 'DOT'
                        label_text = f"{indent}{item.folder_name}"
                        
                        # Color based on status
                        if "ERROR" in item.status:
                            col = row.column()
                            col.alert = True
                            col.label(text=label_text, icon='ERROR')
                        elif "WARNING" in item.status:
                            col = row.column()
                            col.alert = True
                            col.label(text=label_text, icon='INFO')
                        else:
                            row.label(text=label_text, icon=depth_icon)
                        
                        # Action buttons (right side)
                        row.separator()
                        
                        # Copy path button
                        copy_op = row.operator("asset.copy_library_path", text="", icon='COPYDOWN', emboss=False)
                        copy_op.library_path = item.filepath
                        copy_op.library_name = item.folder_name
                        
                        # Open file button (only if file exists)
                        if os.path.exists(item.filepath):
                            open_op = row.operator("asset.open_library_file", text="", icon='FILE_BLEND', emboss=False)
                            open_op.library_path = item.filepath
                        else:
                            # Show disabled icon if missing
                            disabled_col = row.column()
                            disabled_col.enabled = False
                            disabled_col.label(text="", icon='QUESTION')
                        
                        # Show status on hover (via sublabel)
                        if item.status and item.status != "OK":
                            status_row = lib_list_box.row()
                            status_row.scale_y = 0.6
                            status_row.label(text=f"    └─ {item.status}", icon='BLANK1')
                
                # No libraries found message
                elif scene.publish_library_count == 0 and scene.publish_library_errors == 0:
                    info_row = library_box.row()
                    info_row.scale_y = 0.8
                    info_row.label(text="No linked libraries detected", icon='INFO')
        
        layout.separator()

        # Publish Settings
        publish_box = layout.box()
        publish_box.label(text="Settings:", icon='SETTINGS')
        
        # Publish path browse
        col = publish_box.column(align=True)
        col.label(text="Publish Path:", icon='FILE_FOLDER')
        col.prop(scene, "publish_path", text="")
        
        # Versioning mode - Table style with icons
        col.separator(factor=0.5)
        col.label(text="Mode:", icon='MOD_BUILD')
        
        # Check if master file exists (required for versioning)
        master_exists = False
        if scene.publish_path and bpy.data.filepath:
            blend_dir = os.path.dirname(bpy.data.filepath)
            asset_name = os.path.basename(blend_dir)
            master_path = os.path.join(scene.publish_path, f"{asset_name}.blend")
            master_exists = os.path.exists(master_path)
        
        # Grid layout for toggle buttons
        row = col.row(align=True)
        row.prop_enum(scene, "publish_versioning_mode", 'OVERWRITE', text="Overwrite", icon='FILE_REFRESH')
        
        # Disable versioning if no master exists
        versioning_col = row.column()
        versioning_col.prop_enum(scene, "publish_versioning_mode", 'VERSIONING', text="Versioning", icon='LINENUMBERS_ON')
        if not master_exists:
            versioning_col.enabled = False
            # Show tooltip explanation
            help_row = col.row()
            help_row.scale_y = 0.7
            help_row.label(text="Versioning requires master file (publish with Overwrite first)", icon='INFO')
        
        # Preview target path
        if scene.publish_path and bpy.data.filepath:
            blend_dir = os.path.dirname(bpy.data.filepath)
            asset_name = os.path.basename(blend_dir)
            
            if scene.publish_versioning_mode == 'VERSIONING':
                # Find next version
                base_path = os.path.join(scene.publish_path, asset_name)
                version_num = 1
                while os.path.exists(f"{base_path}_v{version_num:03d}"):
                    version_num += 1
                target_preview = f"{asset_name}_v{version_num:03d}"
            else:
                target_preview = asset_name
            
            col.separator(factor=0.5)
            col.label(text=f"→ {target_preview}", icon='FORWARD')
        
        # Publish button
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        
        # Determine if publish button should be enabled
        can_publish = True
        disable_reason = ""
        
        # PRIORITY 1: Must have file and path
        if not bpy.data.filepath:
            can_publish = False
            disable_reason = "File not saved"
        elif not scene.publish_path:
            can_publish = False
            disable_reason = "Publish path not set"
        # PRIORITY 2: Must run validation check first
        elif not scene.publish_check_done:
            can_publish = False
            disable_reason = "Run validation check first"
        # PRIORITY 3: Block if published file (Total Block)
        elif scene.publish_is_published_file:
            can_publish = False
            disable_reason = "Cannot publish from publish directory"
        # PRIORITY 4: Block if has warnings without force
        elif scene.publish_has_warnings and not scene.publish_force:
            can_publish = False
            disable_reason = "Enable Force Publish to continue"
        
        row.enabled = can_publish
        op = row.operator("asset.publish", text="Publish File", icon='PACKAGE')
        
        # Show disable reason as tooltip/sublabel
        if not can_publish and disable_reason:
            info_row = layout.row()
            info_row.scale_y = 0.7
            info_row.label(text=f"⚠️ {disable_reason}", icon='INFO')


def register():
    bpy.utils.register_class(ASSET_PT_Publish)
    

def unregister():
    bpy.utils.unregister_class(ASSET_PT_Publish)

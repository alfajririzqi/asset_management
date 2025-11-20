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

        # Check if published file (auto-detected on file load)
        if scene.publish_is_published_file:
            warning_box = layout.box()
            warning_box.alert = True
            warning_box.label(text="🚫 PUBLISHED FILE DETECTED", icon='ERROR')
            col = warning_box.column(align=True)
            if scene.publish_source_path:
                # Clickable operator to copy source path (larger scale)
                row = col.row()
                row.scale_y = 1.2
                op = row.operator("asset.copy_source_path", text=f"Source: {scene.publish_source_path}", icon='COPYDOWN', emboss=False)
                op.source_path = scene.publish_source_path
            col.scale_y = 0.8
            col.label(text="Cannot publish from publish directory!", icon='BLANK1')
            col.label(text="This prevents recursive versioning (v001_v001)", icon='BLANK1')
        
        box = layout.box()
        box.label(text="Validation:", icon='CHECKMARK')
        
        row = box.row()
        row.scale_y = 1.3
        row.operator("asset.check_publish", text="Run Pre-Publish Checks", icon='VIEWZOOM')
        
        # Disable if: 1) File not saved, OR 2) Published file detected
        if not bpy.data.filepath or scene.publish_is_published_file:
            row.enabled = False
        
        if scene.publish_check_done:
                
            
            result_box = layout.box()
            result_box.label(text="Validation Results:", icon='PRESET_NEW')
            col = result_box.column(align=True)
            
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
            
            # Large textures warning (if enabled in preferences)
            if hasattr(scene, 'publish_large_texture_count') and scene.publish_large_texture_count > 0:
                # Get max resolution from preferences for display
                try:
                    prefs = bpy.context.preferences.addons['asset_management'].preferences
                    max_res_label = {
                        '1024': '1K',
                        '2048': '2K',
                        '4096': '4K',
                        '8192': '8K'
                    }.get(prefs.max_texture_resolution, '4K')
                except Exception:
                    max_res_label = '4K'
                
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_large_texture_count} textures exceed {max_res_label} resolution", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_large_texture_count} textures exceed {max_res_label} resolution", icon='INFO')
            
            # ===== NEW VALIDATION CHECKS =====
            
            # Transform issues
            if hasattr(scene, 'publish_transform_issue_count') and scene.publish_transform_issue_count > 0:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_transform_issue_count} objects with transform issues (Tools: Check Transforms)", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_transform_issue_count} objects with transform issues", icon='INFO')
            
            # Empty material slots
            if hasattr(scene, 'publish_empty_slots_count') and scene.publish_empty_slots_count > 0:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_empty_slots_count} empty material slots (Tools: Clear Unused Slots)", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_empty_slots_count} empty material slots", icon='INFO')
            
            # Duplicate textures
            if hasattr(scene, 'publish_duplicate_texture_count') and scene.publish_duplicate_texture_count > 0:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_duplicate_texture_count} duplicate textures (Tools: Optimize Textures)", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_duplicate_texture_count} duplicate textures", icon='INFO')
            
            # Duplicate materials
            if hasattr(scene, 'publish_duplicate_material_count') and scene.publish_duplicate_material_count > 0:
                if not scene.publish_force:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"{scene.publish_duplicate_material_count} duplicate materials (Tools: Optimize Materials)", icon='ERROR')
                else:
                    col.label(text=f"{scene.publish_duplicate_material_count} duplicate materials", icon='INFO')
            
            # Force Publish option (if has warnings)
            if scene.publish_has_warnings:
                force_box = layout.box()
                force_row = force_box.row()
                force_row.prop(scene, "publish_force", text="Force Publish (ignore warnings)", icon='ERROR')
                # Disable if published file
                if scene.publish_is_published_file:
                    force_row.enabled = False
                
                if scene.publish_force:
                    info_col = force_box.column(align=True)
                    info_col.scale_y = 0.7
                    info_col.label(text="⚠️ All warnings will be ignored", icon='BLANK1')
                    info_col.label(text="⚠️ You take full responsibility", icon='BLANK1')
                
        # ====================================================================
        # LINKED LIBRARIES SECTION
        # ====================================================================
        
        library_box = layout.box()
        library_box.label(text="Linked Libraries:", icon='LINKED')
        
        # Include libraries checkbox (requires pre-publish validation first)
        row = library_box.row()
        row.prop(scene, "publish_include_libraries", text="Publish Linked Libraries")
        
        # Disable if: 1) Published file, OR 2) Pre-publish validation not done
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
            # Show validation results (auto-validated when checkbox enabled)
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
                        row = lib_list_box.row(align=True)
                        
                        has_error = "ERROR" in item.status
                        has_warning = "WARNING" in item.status
                        
                        if has_error or has_warning:
                            row.alert = True
                        
                        checkbox_col = row.column()
                        checkbox_col.prop(item, "selected", text="")
                        if scene.publish_is_published_file:
                            checkbox_col.enabled = False
                        
                        if has_error:
                            status_icon = 'ERROR'
                        elif has_warning:
                            status_icon = 'INFO'
                        else:
                            status_icon = 'CHECKMARK'
                        
                        if item.structure and item.structure != "_external":
                            label_text = f"{item.folder_name} ({item.structure})"
                        else:
                            label_text = f"{item.folder_name}"
                        
                        name_col = row.column()
                        op = name_col.operator("asset.copy_library_path", text=label_text, icon=status_icon, emboss=False)
                        op.library_path = item.filepath
                        op.library_name = item.folder_name
                        
                        # Action buttons (right side) - SWITCHED ORDER: Open first, then Reload
                        row.separator()
                        
                        # Open file button (only if file exists) - NOW FIRST
                        if os.path.exists(item.filepath):
                            open_op = row.operator("asset.open_library_file", text="", icon='FILE_BLEND', emboss=False)
                            open_op.library_path = item.filepath
                        else:
                            # Show disabled icon if missing
                            disabled_col = row.column()
                            disabled_col.enabled = False
                            disabled_col.label(text="", icon='QUESTION')
                        
                        # Reload library button - NOW SECOND (use custom operator)
                        if os.path.exists(item.filepath):
                            # Find the library object to reload - normalize paths for comparison
                            lib_to_reload = None
                            item_path_norm = os.path.normpath(os.path.abspath(item.filepath))
                            
                            for lib in bpy.data.libraries:
                                lib_path_abs = bpy.path.abspath(lib.filepath)
                                lib_path_norm = os.path.normpath(os.path.abspath(lib_path_abs))
                                
                                if lib_path_norm == item_path_norm:
                                    lib_to_reload = lib
                                    break
                            
                            if lib_to_reload:
                                reload_op = row.operator("asset.reload_library", text="", icon='FILE_REFRESH', emboss=False)
                                reload_op.library_path = item.filepath
                            else:
                                # Library not loaded, show disabled icon
                                disabled_col = row.column()
                                disabled_col.enabled = False
                                disabled_col.label(text="", icon='FILE_REFRESH')
                        else:
                            # File missing, show disabled icon
                            disabled_col = row.column()
                            disabled_col.enabled = False
                            disabled_col.label(text="", icon='FILE_REFRESH')
                        
                        # Show status details below (for errors/warnings)
                        if item.status and item.status != "OK":
                            # Split status by line breaks if multiple messages
                            status_messages = item.status.split(';')
                            
                            for msg in status_messages:
                                status_row = lib_list_box.row()
                                status_row.scale_y = 0.7
                                status_row.label(text=f"  └─ {msg.strip()}", icon='BLANK1')
                
                # No libraries found message
                elif scene.publish_library_count == 0 and scene.publish_library_errors == 0:
                    info_row = library_box.row()
                    info_row.scale_y = 0.8
                    info_row.label(text="No linked libraries detected", icon='INFO')
        
        # Publish Settings
        publish_box = layout.box()
        publish_box.label(text="Settings:", icon='SETTINGS')
        
        # Publish path browse
        col = publish_box.column(align=True)
        col.label(text="Publish Path:", icon='FILE_FOLDER')
        path_row = col.row()
        path_row.prop(scene, "publish_path", text="")
        # Disable if published file
        if scene.publish_is_published_file:
            path_row.enabled = False
        
        # Versioning mode - Table style with icons
        col.separator(factor=0.5)
        col.label(text="Mode:", icon='MOD_BUILD')
        
        # Grid layout for toggle buttons
        row = col.row(align=True)
        row.prop_enum(scene, "publish_versioning_mode", 'OVERWRITE', text="Overwrite", icon='FILE_REFRESH')
        row.prop_enum(scene, "publish_versioning_mode", 'VERSIONING', text="Versioning", icon='LINENUMBERS_ON')
        # Disable if published file
        if scene.publish_is_published_file:
            row.enabled = False
        
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

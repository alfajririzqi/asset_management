import bpy
import os


# ============================================================================
# HELPER FUNCTIONS - Linked Libraries Validation
# ============================================================================

def quick_validate_linked_libraries(context):
    """
    Quick validation for linked libraries (without publish_path requirement).
    
    Directly scans bpy.data.libraries and checks:
    - File exists
    - File is readable
    - Has textures folder
    
    Updates publish_library_selection collection with validation results.
    
    Returns:
        tuple: (total_count, error_count, warning_count)
    """
    # Clear existing collection
    context.scene.publish_library_selection.clear()
    
    try:
        # Get all linked libraries directly from bpy.data
        libraries = list(bpy.data.libraries)
        
        total_count = len(libraries)
        error_count = 0
        warning_count = 0
        
        if total_count == 0:
            # No libraries found
            context.scene.publish_library_count = 0
            context.scene.publish_library_errors = 0
            context.scene.publish_library_warnings = 0
            context.scene.publish_libraries_validated = True
            return (0, 0, 0)
        
        # Validate each library
        for lib in libraries:
            # Create item in collection
            item = context.scene.publish_library_selection.add()
            item.name = lib.name
            
            # Get absolute path
            lib_filepath = bpy.path.abspath(lib.filepath)
            item.filepath = lib_filepath
            
            # Extract folder name from path
            if lib_filepath:
                folder_name = os.path.basename(os.path.dirname(lib_filepath))
                item.folder_name = folder_name
            
            # No structure/depth info (we don't have publish_path context)
            item.structure = ""
            item.depth = 1
            item.selected = True  # Default: all selected
            
            # Validation checks
            errors = []
            warnings = []
            
            # Check 1: File exists
            if not os.path.exists(lib_filepath):
                errors.append("File not found")
                error_count += 1
            else:
                # Check 2: File readable (try to get size)
                try:
                    os.path.getsize(lib_filepath)
                except Exception as e:
                    errors.append(f"Cannot read file: {str(e)}")
                    error_count += 1
                
                # Check 3: Has textures folder
                lib_dir = os.path.dirname(lib_filepath)
                textures_dir = os.path.join(lib_dir, "textures")
                if not os.path.exists(textures_dir):
                    warnings.append("No textures folder")
                    warning_count += 1
                else:
                    item.has_textures = True
            
            # Set status
            if errors:
                item.status = f"ERROR: {'; '.join(errors)}"
            elif warnings:
                item.status = f"WARNING: {'; '.join(warnings)}"
            else:
                item.status = "OK"
        
        # Update scene properties
        context.scene.publish_library_count = total_count
        context.scene.publish_library_errors = error_count
        context.scene.publish_library_warnings = warning_count
        context.scene.publish_libraries_validated = True
        
        return (total_count, error_count, warning_count)
        
    except Exception as e:
        print(f"Library validation error: {e}")
        import traceback
        traceback.print_exc()
        context.scene.publish_library_count = 0
        context.scene.publish_library_errors = 1
        context.scene.publish_library_warnings = 0
        context.scene.publish_libraries_validated = True
        return (0, 1, 0)


# ============================================================================
# OPERATORS
# ============================================================================

class ASSET_OT_CheckPublish(bpy.types.Operator):
    """Run pre-publish validation checks and show results in panel"""
    bl_idname = "asset.check_publish"
    bl_label = "Check Publish Readiness"
    bl_description = "Validate asset is ready for publishing"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'WARNING'}, "File not saved")
            return {'CANCELLED'}
        
        # Detect if this is a published file (and update cache)
        from ..utils.published_file_detector import detect_published_file_status, update_published_file_cache
        
        is_published, source_path = detect_published_file_status(context)
        update_published_file_cache(context, is_published, source_path)
        
        # Gather validation data
        blend_dir = os.path.dirname(bpy.data.filepath)
        asset_name = os.path.basename(blend_dir)
        fname = os.path.basename(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")
        
        # Check textures folder
        textures_exist = os.path.exists(textures_dir)
        texture_count = 0
        if textures_exist:
            texture_count = len([f for f in os.listdir(textures_dir) 
                               if os.path.isfile(os.path.join(textures_dir, f)) 
                               and not f.startswith('.')])
        
        # Check external/missing textures
        external_count = 0
        missing_count = 0
        packed_count = 0
        
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source != 'FILE':
                continue
            
            if img.packed_file:
                packed_count += 1
                continue
            
            if not img.filepath_raw:
                continue
            
            abs_path = bpy.path.abspath(img.filepath_raw)
            
            if not os.path.exists(abs_path):
                missing_count += 1
                continue
            
            try:
                if textures_exist:
                    if os.path.commonpath([abs_path, textures_dir]) != textures_dir:
                        external_count += 1
            except ValueError:
                external_count += 1
        
        # Check orphan data
        orphan_count = 0
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                orphan_count += 1
        for mat in bpy.data.materials:
            if mat.users == 0:
                orphan_count += 1
        for img in bpy.data.images:
            if img.name not in ('Render Result', 'Viewer Node') and img.users == 0:
                orphan_count += 1
        
        # Check texture resolution (if enabled in preferences)
        large_texture_count = 0
        try:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences
            if prefs.check_texture_resolution:
                # Get max resolution from preferences (default 4096)
                max_res = int(prefs.max_texture_resolution)
                
                for img in bpy.data.images:
                    if img.name in ('Render Result', 'Viewer Node'):
                        continue
                    if img.source != 'FILE':
                        continue
                    # Check if resolution exceeds threshold
                    if img.size[0] > max_res or img.size[1] > max_res:
                        large_texture_count += 1
        except Exception:
            pass  # Preferences not available or disabled
        
        # ===== NEW VALIDATION CHECKS =====
        
        # 1. Check high poly objects (use scene's highpoly_threshold, not from preferences)
        highpoly_count = 0
        try:
            # Use threshold from scene property (Check High Poly panel)
            threshold = context.scene.highpoly_threshold if hasattr(context.scene, 'highpoly_threshold') else 50000
            
            for obj in context.view_layer.objects:
                if obj.type != 'MESH':
                    continue
                # Calculate triangle count
                depsgraph = context.evaluated_depsgraph_get()
                eval_obj = obj.evaluated_get(depsgraph)
                mesh = eval_obj.to_mesh()
                tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
                eval_obj.to_mesh_clear()
                
                if tris > threshold:
                    highpoly_count += 1
        except Exception:
            pass
        
        # 2. Check transform issues (if enabled)
        transform_issue_count = 0
        try:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences
            if prefs.check_transform_issues:
                for obj in context.view_layer.objects:
                    if obj.type != 'MESH':
                        continue
                    
                    has_issue = False
                    
                    # Check unapplied scale
                    scale = obj.scale
                    if not (abs(scale.x - 1.0) < 0.0001 and 
                           abs(scale.y - 1.0) < 0.0001 and 
                           abs(scale.z - 1.0) < 0.0001):
                        has_issue = True
                    
                    # Check unapplied rotation
                    rot = obj.rotation_euler
                    if not (abs(rot.x) < 0.0001 and 
                           abs(rot.y) < 0.0001 and 
                           abs(rot.z) < 0.0001):
                        has_issue = True
                    
                    if has_issue:
                        transform_issue_count += 1
        except Exception:
            pass
        
        # 3. Check empty material slots (if enabled)
        empty_slots_count = 0
        try:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences
            if prefs.check_empty_material_slots:
                for obj in context.view_layer.objects:
                    if obj.type != 'MESH' or not obj.data:
                        continue
                    
                    mesh = obj.data
                    used_material_indices = set(poly.material_index for poly in mesh.polygons)
                    
                    # Check each slot
                    for i, slot in enumerate(obj.material_slots):
                        # Empty slot or unused slot
                        if slot.material is None or i not in used_material_indices:
                            empty_slots_count += 1
        except Exception:
            pass
        
        # 4. Check duplicate textures (if enabled)
        duplicate_texture_count = 0
        try:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences
            if prefs.check_duplicate_textures:
                from collections import defaultdict
                image_groups = defaultdict(list)
                for img in bpy.data.images:
                    if img.filepath:  # Only external images
                        image_groups[img.filepath].append(img)
                # Count duplicates (groups with more than 1 image)
                for images in image_groups.values():
                    if len(images) > 1:
                        duplicate_texture_count += len(images) - 1
        except Exception:
            pass
        
        # 5. Check duplicate materials (if enabled)
        duplicate_material_count = 0
        try:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences
            if prefs.check_duplicate_materials:
                from collections import defaultdict
                # Simple duplicate detection by name pattern (ends with .001, .002, etc)
                material_groups = defaultdict(list)
                for mat in bpy.data.materials:
                    # Remove numeric suffix
                    base_name = mat.name
                    if '.' in base_name:
                        parts = base_name.rsplit('.', 1)
                        if parts[1].isdigit() and len(parts[1]) == 3:
                            base_name = parts[0]
                    material_groups[base_name].append(mat)
                
                # Count duplicates
                for mats in material_groups.values():
                    if len(mats) > 1:
                        duplicate_material_count += len(mats) - 1
        except Exception:
            pass
        
        # Store results in scene properties
        context.scene.publish_check_done = True
        context.scene.publish_large_texture_count = large_texture_count
        context.scene.publish_highpoly_count = highpoly_count
        context.scene.publish_transform_issue_count = transform_issue_count
        context.scene.publish_empty_slots_count = empty_slots_count
        context.scene.publish_duplicate_texture_count = duplicate_texture_count
        context.scene.publish_duplicate_material_count = duplicate_material_count
        context.scene.publish_asset_name = asset_name
        context.scene.publish_file_name = fname
        context.scene.publish_textures_exist = textures_exist
        context.scene.publish_texture_count = texture_count
        context.scene.publish_external_count = external_count
        context.scene.publish_missing_count = missing_count
        context.scene.publish_packed_count = packed_count
        context.scene.publish_orphan_count = orphan_count
        
        # Determine critical errors (blocking) vs warnings (can be forced)
        # Critical errors: ONLY absolute requirements (no publish path)
        has_critical_errors = (not context.scene.publish_path)
        
        # Warnings: ALL other issues can be forced (textures, optimization, transforms, etc)
        has_warnings = (not textures_exist or 
                       external_count > 0 or 
                       missing_count > 0 or
                       packed_count > 0 or 
                       orphan_count > 0 or
                       highpoly_count > 0 or
                       transform_issue_count > 0 or
                       empty_slots_count > 0 or
                       duplicate_texture_count > 0 or
                       duplicate_material_count > 0)
        
        context.scene.publish_has_errors = has_critical_errors
        context.scene.publish_has_warnings = has_warnings
        context.scene.publish_is_ready = not has_critical_errors
        
        self.report({'INFO'}, "Validation complete")
        return {'FINISHED'}


class ASSET_OT_ValidateLibraries(bpy.types.Operator):
    """Validate linked libraries for publishing"""
    bl_idname = "asset.validate_libraries"
    bl_label = "Validate Linked Libraries"
    bl_description = "Check all linked libraries are ready for publishing"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'WARNING'}, "File not saved")
            return {'CANCELLED'}
        
        # Run validation (no publish_path required - scans bpy.data.libraries directly)
        total, errors, warnings = quick_validate_linked_libraries(context)
        
        # Report results
        if errors > 0:
            self.report(
                {'WARNING'}, 
                f"Found {total} libraries: {errors} errors, {warnings} warnings"
            )
        elif warnings > 0:
            self.report(
                {'INFO'}, 
                f"Found {total} libraries: {warnings} warnings"
            )
        elif total > 0:
            self.report(
                {'INFO'}, 
                f"All {total} libraries validated successfully"
            )
        else:
            self.report({'INFO'}, "No linked libraries found")
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_CheckPublish)
    bpy.utils.register_class(ASSET_OT_ValidateLibraries)
    
    # Register scene properties for validation results
    bpy.types.Scene.publish_check_done = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.publish_asset_name = bpy.props.StringProperty(default="")
    bpy.types.Scene.publish_file_name = bpy.props.StringProperty(default="")
    bpy.types.Scene.publish_textures_exist = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.publish_texture_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.publish_external_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.publish_missing_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.publish_packed_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.publish_orphan_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.publish_has_errors = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.publish_has_warnings = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.publish_is_ready = bpy.props.BoolProperty(default=False)
    
    # Published file detection
    bpy.types.Scene.publish_is_published_file = bpy.props.BoolProperty(
        name="Is Published File",
        description="Current file is a published file",
        default=False
    )
    bpy.types.Scene.publish_source_path = bpy.props.StringProperty(
        name="Source Path",
        description="Original source path of published file",
        default=""
    )


def unregister():
    # Clean up scene properties
    if hasattr(bpy.types.Scene, "publish_source_path"):
        del bpy.types.Scene.publish_source_path
    if hasattr(bpy.types.Scene, "publish_is_published_file"):
        del bpy.types.Scene.publish_is_published_file
    if hasattr(bpy.types.Scene, "publish_is_ready"):
        del bpy.types.Scene.publish_is_ready
    if hasattr(bpy.types.Scene, "publish_has_warnings"):
        del bpy.types.Scene.publish_has_warnings
    if hasattr(bpy.types.Scene, "publish_has_errors"):
        del bpy.types.Scene.publish_has_errors
    if hasattr(bpy.types.Scene, "publish_orphan_count"):
        del bpy.types.Scene.publish_orphan_count
    if hasattr(bpy.types.Scene, "publish_packed_count"):
        del bpy.types.Scene.publish_packed_count
    if hasattr(bpy.types.Scene, "publish_missing_count"):
        del bpy.types.Scene.publish_missing_count
    if hasattr(bpy.types.Scene, "publish_external_count"):
        del bpy.types.Scene.publish_external_count
    if hasattr(bpy.types.Scene, "publish_texture_count"):
        del bpy.types.Scene.publish_texture_count
    if hasattr(bpy.types.Scene, "publish_textures_exist"):
        del bpy.types.Scene.publish_textures_exist
    if hasattr(bpy.types.Scene, "publish_file_name"):
        del bpy.types.Scene.publish_file_name
    if hasattr(bpy.types.Scene, "publish_asset_name"):
        del bpy.types.Scene.publish_asset_name
    if hasattr(bpy.types.Scene, "publish_check_done"):
        del bpy.types.Scene.publish_check_done
    
    bpy.utils.unregister_class(ASSET_OT_ValidateLibraries)
    bpy.utils.unregister_class(ASSET_OT_CheckPublish)

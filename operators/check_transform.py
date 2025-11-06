import bpy
import mathutils


class ASSET_OT_check_transform(bpy.types.Operator):
    """Check objects for transform issues (unapplied scale, rotation, extreme values)."""
    bl_idname = "asset.check_transform"
    bl_label = "Check Transforms"
    bl_description = "Detect unapplied transforms and extreme scale values"
    bl_options = {'REGISTER'}

    BACKGROUND_COLOR = (0.2, 0.25, 0.28)  # Dark blue-gray (different from high poly)

    def execute(self, context):
        # Auto-exit other analysis modes first
        if hasattr(context.scene, "highpoly_mode_active") and context.scene.highpoly_mode_active:
            bpy.ops.asset.exit_highpoly()
        
        # Force Solid viewport shading for accurate analysis
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        if space.shading.type != 'SOLID':
                            space.shading.type = 'SOLID'
        
        # Store original viewport settings
        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                if not hasattr(context.scene, "transform_original_bg"):
                    context.scene.transform_original_bg = space.shading.background_color[:3]
                if not hasattr(context.scene, "transform_original_type"):
                    context.scene.transform_original_type = space.shading.background_type
                if not hasattr(context.scene, "transform_original_color_type"):
                    context.scene.transform_original_color_type = space.shading.color_type
        
        # Set viewport for transform analysis
        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.shading.background_type = 'VIEWPORT'
                space.shading.background_color = self.BACKGROUND_COLOR
        
        issue_count = 0
        unapplied_scale_count = 0
        non_uniform_scale_count = 0
        extreme_scale_count = 0
        unapplied_rotation_count = 0
        
        # Reset all objects first
        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            obj.color = (1.0, 1.0, 1.0, 1.0)
            # Clean up previous markers
            if "_transform_issue" in obj:
                del obj["_transform_issue"]
            if "_transform_type" in obj:
                del obj["_transform_type"]
        
        # Only check objects in active view layer (not hidden collections)
        objects_to_check = [obj for obj in context.view_layer.objects if obj.type == 'MESH']
        
        # Count hidden objects for info display
        hidden_count = len([obj for obj in context.scene.objects if obj.type == 'MESH']) - len(objects_to_check)
        
        # Check each mesh object
        for obj in objects_to_check:
            
            has_issue = False
            issue_type = []
            severity = 0  # 1=yellow, 2=orange, 3=red
            
            # Check for unapplied scale (not 1.0, 1.0, 1.0)
            scale = obj.scale
            if not (abs(scale.x - 1.0) < 0.0001 and 
                   abs(scale.y - 1.0) < 0.0001 and 
                   abs(scale.z - 1.0) < 0.0001):
                issue_type.append("Unapplied Scale")
                unapplied_scale_count += 1
                has_issue = True
                severity = max(severity, 2)  # Orange
                
                # Check non-uniform scale
                if not (abs(scale.x - scale.y) < 0.0001 and 
                       abs(scale.y - scale.z) < 0.0001):
                    issue_type.append("Non-uniform Scale")
                    non_uniform_scale_count += 1
                    severity = max(severity, 2)  # Orange
                
                # Check extreme scale
                min_scale = min(abs(scale.x), abs(scale.y), abs(scale.z))
                max_scale = max(abs(scale.x), abs(scale.y), abs(scale.z))
                if min_scale < 0.01 or max_scale > 100:
                    issue_type.append("Extreme Scale")
                    extreme_scale_count += 1
                    severity = max(severity, 3)  # Red
            
            # Check for unapplied rotation (not 0, 0, 0)
            rot = obj.rotation_euler
            if not (abs(rot.x) < 0.0001 and 
                   abs(rot.y) < 0.0001 and 
                   abs(rot.z) < 0.0001):
                issue_type.append("Unapplied Rotation")
                unapplied_rotation_count += 1
                has_issue = True
                severity = max(severity, 1)  # Yellow
            
            # Mark object if has issues
            if has_issue:
                obj["_transform_issue"] = True
                obj["_transform_type"] = ", ".join(issue_type)
                issue_count += 1
                
                # Set color based on severity
                if severity == 3:
                    obj.color = (1.0, 0.0, 0.0, 1.0)  # Red - Critical
                elif severity == 2:
                    obj.color = (1.0, 0.5, 0.0, 1.0)  # Orange - Warning
                else:
                    obj.color = (1.0, 1.0, 0.0, 1.0)  # Yellow - Info
        
        # Set viewport to object color mode
        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.shading.color_type = 'OBJECT'
        
        # Store statistics in scene
        context.scene.transform_check_done = True
        context.scene.transform_issue_count = issue_count
        context.scene.transform_unapplied_scale = unapplied_scale_count
        context.scene.transform_non_uniform = non_uniform_scale_count
        context.scene.transform_extreme_scale = extreme_scale_count
        context.scene.transform_unapplied_rotation = unapplied_rotation_count
        context.scene.transform_mode_active = True
        context.scene.transform_hidden_skipped = hidden_count
        
        context.area.tag_redraw()
        
        if issue_count > 0:
            self.report(
                {'WARNING'},
                f"Found {issue_count} objects with transform issues"
            )
        else:
            self.report({'INFO'}, "No transform issues found - all clean!")
        
        return {'FINISHED'}


class ASSET_OT_refresh_transform(bpy.types.Operator):
    """Re-run transform analysis without exiting mode."""
    bl_idname = "asset.refresh_transform"
    bl_label = "Refresh Analysis"
    bl_description = "Update transform analysis"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.asset.check_transform()
        self.report({'INFO'}, "Transform analysis refreshed")
        return {'FINISHED'}


class ASSET_OT_select_transform_issues(bpy.types.Operator):
    """Select all objects with transform issues."""
    bl_idname = "asset.select_transform_issues"
    bl_label = "Select Issues"
    bl_description = "Select all objects with transform issues"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_count = 0
        unhidden_count = 0
        
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select objects with transform issues (only if in active view layer)
        view_layer_objects = context.view_layer.objects
        for obj in context.scene.objects:
            if obj.type == 'MESH' and "_transform_issue" in obj:
                # Check if object is in active view layer
                if obj.name in view_layer_objects:
                    try:
                        # Temporarily unhide if hidden
                        was_hidden = obj.hide_get()
                        if was_hidden:
                            obj.hide_set(False)
                            unhidden_count += 1
                        
                        obj.select_set(True)
                        selected_count += 1
                    except Exception as e:
                        print(f"Warning: Could not select {obj.name}: {e}")
        
        if selected_count > 0:
            if unhidden_count > 0:
                self.report({'INFO'}, f"Selected {selected_count} objects with transform issues (unhid {unhidden_count} hidden)")
            else:
                self.report({'INFO'}, f"Selected {selected_count} objects with transform issues")
        else:
            self.report({'WARNING'}, "No objects with transform issues found")
        
        return {'FINISHED'}


class ASSET_OT_apply_all_transforms(bpy.types.Operator):
    """Apply all transforms to selected objects."""
    bl_idname = "asset.apply_all_transforms"
    bl_label = "Apply All Transforms"
    bl_description = "Apply scale and rotation to selected objects (WARNING: Cannot undo!)"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Modifier safety classification
    DANGEROUS_MODIFIERS = {
        'MIRROR', 'ARRAY', 'BEVEL', 'SOLIDIFY', 'SCREW', 
        'LATTICE', 'ARMATURE', 'CURVE', 'SHRINKWRAP', 
        'SIMPLE_DEFORM', 'CAST', 'HOOK', 'LAPLACIANDEFORM',
        'SURFACE_DEFORM', 'WARP', 'WAVE', 'BOOLEAN',
        'NODES'  # Geometry Nodes can be unpredictable
    }
    
    SAFE_MODIFIERS = {
        'SUBSURF', 'MULTIRES', 'TRIANGULATE', 'DECIMATE',
        'SMOOTH', 'CORRECTIVE_SMOOTH', 'WEIGHTED_NORMAL',
        'EDGE_SPLIT', 'REMESH'
    }
    
    def _check_transform_safety(self, objects):
        """Check selected objects for dangerous modifiers (excluding ARMATURE - rigged objects protected).
        
        Returns:
            tuple: (has_danger, danger_report)
            - has_danger (bool): True if dangerous modifiers found (excluding ARMATURE)
            - danger_report (dict): {obj_name: [modifier_names]}
        """
        danger_report = {}
        
        for obj in objects:
            if obj.type != 'MESH':
                continue
            
            # Check if object has ARMATURE (rigged - will be skipped)
            has_armature = any(mod.type == 'ARMATURE' for mod in obj.modifiers)
            
            dangerous_mods = []
            for mod in obj.modifiers:
                # Include dangerous modifiers EXCEPT ARMATURE
                if mod.type in self.DANGEROUS_MODIFIERS and mod.type != 'ARMATURE':
                    dangerous_mods.append(f"{mod.name} ({mod.type})")
            
            if dangerous_mods:
                # Add note if object has armature (will be skipped)
                if has_armature:
                    danger_report[obj.name + " [RIGGED - WILL BE SKIPPED]"] = dangerous_mods
                else:
                    danger_report[obj.name] = dangerous_mods
        
        return (len(danger_report) > 0, danger_report)

    def invoke(self, context, event):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # CRITICAL: Check for dangerous modifiers (excluding ARMATURE)
        has_danger, danger_report = self._check_transform_safety(selected)
        
        if has_danger:
            # Store danger report in scene for dialog access
            context.scene.transform_danger_report = str(danger_report)
            
            # Show dialog popup instead of blocking
            return context.window_manager.invoke_props_dialog(self, width=500)
        
        # Safe to proceed - show normal confirmation
        return context.window_manager.invoke_confirm(self, event)
    
    def draw(self, context):
        """Draw dialog when dangerous modifiers detected."""
        layout = self.layout
        
        # Check if we have danger report
        if hasattr(context.scene, 'transform_danger_report') and context.scene.transform_danger_report:
            import ast
            try:
                danger_report = ast.literal_eval(context.scene.transform_danger_report)
            except:
                danger_report = {}
            
            if danger_report:
                # Header warning
                box = layout.box()
                row = box.row()
                row.alert = True
                row.label(text="⚠ DANGEROUS MODIFIERS DETECTED", icon='ERROR')
                
                # List objects and their dangerous modifiers
                box.label(text="Objects with risky modifiers:", icon='INFO')
                for obj_name, mod_list in danger_report.items():
                    obj_row = box.row()
                    obj_row.label(text=f"• {obj_name}:", icon='OBJECT_DATA')
                    
                    for mod_name in mod_list:
                        mod_row = box.row()
                        mod_row.label(text=f"    - {mod_name}", icon='MODIFIER')
                
                # Workflow explanation
                layout.separator()
                info_box = layout.box()
                info_box.label(text="AUTO-WORKFLOW:", icon='SETTINGS')
                info_box.label(text="1. Backup objects to .temp collection", icon='BLANK1')
                info_box.label(text="2. Apply dangerous modifiers on originals", icon='BLANK1')
                info_box.label(text="3. Apply transforms on originals", icon='BLANK1')
                info_box.label(text="", icon='BLANK1')
                info_box.label(text="⚠ Objects with ARMATURE will be SKIPPED", icon='ARMATURE_DATA')
                
                layout.separator()
                layout.label(text="Proceed with auto-workflow?", icon='QUESTION')
        else:
            # Normal confirmation
            layout.label(text="Apply transforms to selected objects?", icon='QUESTION')

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        # Check if we need auto-workflow (dangerous modifiers detected)
        has_danger, danger_report = self._check_transform_safety(selected)
        
        if has_danger:
            # AUTO-WORKFLOW: Backup → Apply Modifiers → Apply Transforms
            print("\n" + "="*70)
            print("🔧 AUTO-WORKFLOW: Dangerous Modifiers Detected")
            print("="*70)
            
            # Step 1: Create backup in .temp collection
            print("\n📦 STEP 1: Creating backups in .temp collection...")
            temp_collection = self._get_or_create_temp_collection(context)
            
            backup_count = 0
            for obj in selected:
                # Skip if object has ARMATURE modifier (rigged objects protected)
                if self._has_armature_modifier(obj):
                    print(f"  ⚠ SKIPPED {obj.name} - Has ARMATURE (rigged object protected)")
                    continue
                
                # Create backup
                obj_copy = obj.copy()
                obj_copy.data = obj.data.copy()
                obj_copy.name = f"{obj.name}_backup"
                
                # Link to .temp collection (collection is excluded from view layer, so objects auto-hidden)
                temp_collection.objects.link(obj_copy)
                
                backup_count += 1
                print(f"  ✓ Backed up: {obj.name} → {obj_copy.name}")
            
            print(f"\n✅ Created {backup_count} backups")
            
            # Step 2: Apply dangerous modifiers on ORIGINAL objects
            print(f"\n🔧 STEP 2: Applying dangerous modifiers on originals...")
            modifiers_applied = 0
            
            for obj in selected:
                # Skip if has ARMATURE
                if self._has_armature_modifier(obj):
                    continue
                
                # Find dangerous modifiers (excluding ARMATURE)
                dangerous_mods = []
                for mod in obj.modifiers:
                    if mod.type in self.DANGEROUS_MODIFIERS and mod.type != 'ARMATURE':
                        dangerous_mods.append(mod.name)
                
                if dangerous_mods:
                    # Set as active to apply modifiers
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    
                    # Apply each dangerous modifier
                    for mod_name in dangerous_mods:
                        try:
                            mod = obj.modifiers.get(mod_name)
                            if mod:
                                bpy.ops.object.modifier_apply(modifier=mod_name)
                                modifiers_applied += 1
                                print(f"  ✓ Applied {mod_name} ({mod.type}) on {obj.name}")
                        except Exception as e:
                            print(f"  ⚠ Could not apply {mod_name} on {obj.name}: {e}")
            
            print(f"\n✅ Applied {modifiers_applied} dangerous modifiers")
            
            # Step 3: Apply transforms on ORIGINAL objects
            print(f"\n🎯 STEP 3: Applying transforms on originals...")
            applied_count = 0
            
            for obj in selected:
                # Skip if has ARMATURE
                if self._has_armature_modifier(obj):
                    continue
                
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                try:
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                    applied_count += 1
                    print(f"  ✓ Applied transforms on {obj.name}")
                except Exception as e:
                    print(f"  ⚠ Could not apply transform to {obj.name}: {e}")
            
            print(f"\n✅ Applied transforms to {applied_count} objects")
            print("="*70 + "\n")
            
            # Clear danger report
            context.scene.transform_danger_report = ""
            
            # Restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected:
                obj.select_set(True)
            
            # Refresh analysis
            if context.scene.transform_mode_active:
                bpy.ops.asset.refresh_transform()
            
            self.report({'INFO'}, f"Auto-workflow complete: {backup_count} backups, {modifiers_applied} modifiers applied, {applied_count} transforms applied")
            return {'FINISHED'}
        
        else:
            # NORMAL WORKFLOW: No dangerous modifiers, just apply transforms
            applied_count = 0
            
            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue
                
                # Apply all transforms
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                try:
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                    applied_count += 1
                except Exception as e:
                    self.report({'WARNING'}, f"Could not apply transform to {obj.name}: {str(e)}")
            
            # Refresh analysis
            if context.scene.transform_mode_active:
                bpy.ops.asset.refresh_transform()
            
            self.report({'INFO'}, f"Applied transforms to {applied_count} objects")
            return {'FINISHED'}
    
    def _get_or_create_temp_collection(self, context):
        """Get or create .temp collection and exclude from view layer."""
        if ".temp" in bpy.data.collections:
            temp_collection = bpy.data.collections[".temp"]
        else:
            temp_collection = bpy.data.collections.new(".temp")
            context.scene.collection.children.link(temp_collection)
            
            # Exclude from view layer (this hides all objects in collection)
            layer_collection = context.view_layer.layer_collection.children.get(".temp")
            if layer_collection:
                layer_collection.exclude = True
        
        return temp_collection
    
    def _has_armature_modifier(self, obj):
        """Check if object has ARMATURE modifier (rigged object)."""
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE':
                return True
        return False


class ASSET_OT_exit_transform(bpy.types.Operator):
    """Exit transform check mode and restore default view."""
    bl_idname = "asset.exit_transform"
    bl_label = "Exit Transform Mode"
    bl_description = "Return to normal view"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Reset object colors
        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            obj.color = (1.0, 1.0, 1.0, 1.0)
            if "_transform_issue" in obj:
                del obj["_transform_issue"]
            if "_transform_type" in obj:
                del obj["_transform_type"]
        
        # Reset viewport settings
        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                if hasattr(context.scene, "transform_original_type"):
                    space.shading.background_type = context.scene.transform_original_type
                else:
                    space.shading.background_type = 'THEME'
                
                if hasattr(context.scene, "transform_original_bg"):
                    space.shading.background_color = context.scene.transform_original_bg
                else:
                    space.shading.background_color = (0.0, 0.0, 0.0)
                
                if hasattr(context.scene, "transform_original_color_type"):
                    space.shading.color_type = context.scene.transform_original_color_type
                else:
                    space.shading.color_type = 'MATERIAL'
        
        context.scene.transform_mode_active = False
        context.area.tag_redraw()
        
        self.report({'INFO'}, "Exited transform check mode")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_check_transform)
    bpy.utils.register_class(ASSET_OT_refresh_transform)
    bpy.utils.register_class(ASSET_OT_select_transform_issues)
    bpy.utils.register_class(ASSET_OT_apply_all_transforms)
    bpy.utils.register_class(ASSET_OT_exit_transform)
    
    # Register scene properties
    bpy.types.Scene.transform_check_done = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.transform_mode_active = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.transform_issue_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.transform_unapplied_scale = bpy.props.IntProperty(default=0)
    bpy.types.Scene.transform_non_uniform = bpy.props.IntProperty(default=0)
    bpy.types.Scene.transform_extreme_scale = bpy.props.IntProperty(default=0)
    bpy.types.Scene.transform_unapplied_rotation = bpy.props.IntProperty(default=0)
    
    bpy.types.Scene.transform_hidden_skipped = bpy.props.IntProperty(
        name="Hidden Objects Skipped",
        description="Number of hidden objects not checked",
        default=0,
    )
    
    # Viewport state storage
    bpy.types.Scene.transform_original_bg = bpy.props.FloatVectorProperty(
        name="Original Background Color",
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype='COLOR',
    )
    bpy.types.Scene.transform_original_type = bpy.props.StringProperty(default='THEME')
    bpy.types.Scene.transform_original_color_type = bpy.props.StringProperty(default='MATERIAL')
    
    # Danger report for dialog
    bpy.types.Scene.transform_danger_report = bpy.props.StringProperty(default="")


def unregister():
    # Clean up scene properties
    if hasattr(bpy.types.Scene, "transform_danger_report"):
        del bpy.types.Scene.transform_danger_report
    if hasattr(bpy.types.Scene, "transform_original_color_type"):
        del bpy.types.Scene.transform_original_color_type
    if hasattr(bpy.types.Scene, "transform_original_type"):
        del bpy.types.Scene.transform_original_type
    if hasattr(bpy.types.Scene, "transform_original_bg"):
        del bpy.types.Scene.transform_original_bg
    if hasattr(bpy.types.Scene, "transform_hidden_skipped"):
        del bpy.types.Scene.transform_hidden_skipped
    if hasattr(bpy.types.Scene, "transform_unapplied_rotation"):
        del bpy.types.Scene.transform_unapplied_rotation
    if hasattr(bpy.types.Scene, "transform_extreme_scale"):
        del bpy.types.Scene.transform_extreme_scale
    if hasattr(bpy.types.Scene, "transform_non_uniform"):
        del bpy.types.Scene.transform_non_uniform
    if hasattr(bpy.types.Scene, "transform_unapplied_scale"):
        del bpy.types.Scene.transform_unapplied_scale
    if hasattr(bpy.types.Scene, "transform_issue_count"):
        del bpy.types.Scene.transform_issue_count
    if hasattr(bpy.types.Scene, "transform_mode_active"):
        del bpy.types.Scene.transform_mode_active
    if hasattr(bpy.types.Scene, "transform_check_done"):
        del bpy.types.Scene.transform_check_done
    
    bpy.utils.unregister_class(ASSET_OT_exit_transform)
    bpy.utils.unregister_class(ASSET_OT_apply_all_transforms)
    bpy.utils.unregister_class(ASSET_OT_select_transform_issues)
    bpy.utils.unregister_class(ASSET_OT_refresh_transform)
    bpy.utils.unregister_class(ASSET_OT_check_transform)

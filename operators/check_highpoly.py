import bpy
import math

class ASSET_OT_check_highpoly(bpy.types.Operator):
    """Highlight objects exceeding polygon threshold."""
    bl_idname = "asset.check_highpoly"
    bl_label = "Check High Poly Objects"
    bl_description = "Highlight objects exceeding polygon threshold"
    bl_options = {'REGISTER'}

    BACKGROUND_COLOR = (0.302, 0.282, 0.157) 

    def get_tris_count(self, obj, use_modifiers=True):
        """Return triangle count for the given object."""
        if obj.type != 'MESH':
            return 0

        if use_modifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
            eval_obj.to_mesh_clear()
        else:
            mesh = obj.data
            tris = sum(len(p.vertices) - 2 for p in mesh.polygons)

        return tris

    def execute(self, context):
        # Auto-exit other analysis modes first
        if hasattr(context.scene, "transform_mode_active") and context.scene.transform_mode_active:
            bpy.ops.asset.exit_transform()
        
        # Force Solid viewport shading for accurate analysis
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        if space.shading.type != 'SOLID':
                            space.shading.type = 'SOLID'
        
        high_poly_count = 0

        # Store original viewport settings (only if not already stored)
        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                if not hasattr(context.scene, "highpoly_original_bg"):
                    context.scene.highpoly_original_bg = space.shading.background_color[:3]
                if not hasattr(context.scene, "highpoly_original_type"):
                    context.scene.highpoly_original_type = space.shading.background_type
                # Always store current color type (might be changed by other mode)
                if not hasattr(context.scene, "highpoly_original_color_type"):
                    context.scene.highpoly_original_color_type = space.shading.color_type

        # Set viewport for high poly analysis
        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                if not hasattr(context.scene, "highpoly_original_bg"):
                    context.scene.highpoly_original_bg = space.shading.background_color[:3]
                if not hasattr(context.scene, "highpoly_original_type"):
                    context.scene.highpoly_original_type = space.shading.background_type

        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.shading.background_type = 'VIEWPORT'
                space.shading.background_color = self.BACKGROUND_COLOR

        context.area.tag_redraw()
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

        # Reset all objects first
        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            obj.color = (1.0, 1.0, 1.0, 1.0)
            if "_high_poly" in obj:
                del obj["_high_poly"]
            if "_tris_count" in obj:
                del obj["_tris_count"]

        # Only check objects in active view layer (not hidden collections)
        objects_to_check = [obj for obj in context.view_layer.objects if obj.type == 'MESH']
        
        # Count hidden objects for info display
        hidden_count = len([obj for obj in context.scene.objects if obj.type == 'MESH']) - len(objects_to_check)

        for obj in objects_to_check:
            tris = self.get_tris_count(obj, context.scene.highpoly_use_modifiers)
            if tris > context.scene.highpoly_threshold:
                obj["_high_poly"] = True
                obj["_tris_count"] = tris
                obj.color = (1.0, 0.0, 0.0, 1.0)
                high_poly_count += 1

        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.shading.color_type = 'OBJECT'

        context.scene.highpoly_mode_active = True
        
        # Store statistics including hidden count
        context.scene.highpoly_hidden_skipped = hidden_count

        self.report(
            {'WARNING'},
            f"Found {high_poly_count} high-poly objects exceeding {context.scene.highpoly_threshold} tris"
        )
        return {'FINISHED'}


class ASSET_OT_refresh_highpoly(bpy.types.Operator):
    """Re-run high-poly analysis without exiting mode."""
    bl_idname = "asset.refresh_highpoly"
    bl_label = "Refresh Analysis"
    bl_description = "Update high-poly analysis (useful after modifying objects)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Simply re-run the check operator
        bpy.ops.asset.check_highpoly()
        self.report({'INFO'}, "High-poly analysis refreshed")
        return {'FINISHED'}


class ASSET_OT_select_highpoly(bpy.types.Operator):
    """Select all high-poly objects."""
    bl_idname = "asset.select_highpoly"
    bl_label = "Select High-Poly"
    bl_description = "Select all objects exceeding threshold for batch operations"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_count = 0
        unhidden_count = 0
        
        # Deselect all first
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select high-poly objects (only if in active view layer)
        view_layer_objects = context.view_layer.objects
        for obj in context.scene.objects:
            if obj.type == 'MESH' and "_high_poly" in obj:
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
                self.report({'INFO'}, f"Selected {selected_count} high-poly objects (unhid {unhidden_count} hidden)")
            else:
                self.report({'INFO'}, f"Selected {selected_count} high-poly objects")
        else:
            self.report({'WARNING'}, "No high-poly objects found. Run analysis first.")
        
        return {'FINISHED'}


class ASSET_OT_isolate_highpoly(bpy.types.Operator):
    """Toggle isolation of high-poly objects (hide/unhide non-high-poly)."""
    bl_idname = "asset.isolate_highpoly"
    bl_label = "Isolate High-Poly"
    bl_description = "Toggle: Hide all objects except high-poly ones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check if already isolated
        is_isolated = getattr(context.scene, 'highpoly_isolated', False)
        
        if is_isolated:
            # UN-ISOLATE: Show all hidden objects
            unhidden_count = 0
            for obj in context.view_layer.objects:
                if obj.type != 'MESH':
                    continue
                
                # Check if object was hidden by isolation (custom property)
                if "_isolated_by_highpoly" in obj:
                    obj.hide_set(False)
                    del obj["_isolated_by_highpoly"]
                    unhidden_count += 1
            
            context.scene.highpoly_isolated = False
            self.report({'INFO'}, f"Un-isolated: showed {unhidden_count} objects")
        else:
            # ISOLATE: Hide non-high-poly objects
            hidden_count = 0
            for obj in context.view_layer.objects:
                if obj.type != 'MESH':
                    continue
                
                # Hide non-high-poly objects and mark them
                if "_high_poly" not in obj:
                    obj.hide_set(True)
                    obj["_isolated_by_highpoly"] = True  # Mark for restoration
                    hidden_count += 1
            
            context.scene.highpoly_isolated = True
            self.report({'INFO'}, f"Isolated high-poly objects (hid {hidden_count} objects)")
        
        return {'FINISHED'}


class ASSET_OT_exit_highpoly(bpy.types.Operator):
    """Exit high-poly analysis mode and restore default view."""
    bl_idname = "asset.exit_highpoly"
    bl_label = "Exit High Poly Mode"
    bl_description = "Return to normal view and reset object colors"
    bl_options = {'REGISTER'}

    def execute(self, context):
        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            obj.color = (1.0, 1.0, 1.0, 1.0)
            if "_high_poly" in obj:
                del obj["_high_poly"]
            if "_tris_count" in obj:
                del obj["_tris_count"]
            # Clear isolation markers
            if "_isolated_by_highpoly" in obj:
                obj.hide_set(False)
                del obj["_isolated_by_highpoly"]

        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                if hasattr(context.scene, "highpoly_original_type"):
                    space.shading.background_type = context.scene.highpoly_original_type
                else:
                    space.shading.background_type = 'THEME'
                
                if hasattr(context.scene, "highpoly_original_bg"):
                    space.shading.background_color = context.scene.highpoly_original_bg
                else:
                    space.shading.background_color = (0.0, 0.0, 0.0)
                
                # Restore original color type
                if hasattr(context.scene, "highpoly_original_color_type"):
                    space.shading.color_type = context.scene.highpoly_original_color_type
                else:
                    space.shading.color_type = 'MATERIAL'

        context.area.tag_redraw()
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

        context.scene.highpoly_mode_active = False
        context.scene.highpoly_isolated = False  # Reset isolation state

        self.report({'INFO'}, "Exited high-poly analysis mode")
        return {'FINISHED'}


def register():
    bpy.types.Scene.highpoly_threshold = bpy.props.IntProperty(
        default=50000,
        min=1,
    )

    bpy.types.Scene.highpoly_use_modifiers = bpy.props.BoolProperty(
        default=True,
    )

    bpy.types.Scene.highpoly_mode_active = bpy.props.BoolProperty(
        default=False,
    )
    
    bpy.types.Scene.highpoly_hidden_skipped = bpy.props.IntProperty(
        name="Hidden Objects Skipped",
        description="Number of hidden objects not checked",
        default=0,
    )
    
    bpy.types.Scene.highpoly_isolated = bpy.props.BoolProperty(
        name="Isolated Mode",
        description="High-poly objects are isolated (non-high-poly hidden)",
        default=False,
    )

    bpy.types.Scene.highpoly_original_bg = bpy.props.FloatVectorProperty(
        name="Original Background Color",
        description="Stored viewport background color for restoration",
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype='COLOR',
        min=0.0,
        max=1.0,
    )
    
    bpy.types.Scene.highpoly_original_type = bpy.props.StringProperty(
        name="Original Background Type",
        description="Stored viewport background type for restoration",
        default='THEME',
    )
    
    bpy.types.Scene.highpoly_original_color_type = bpy.props.StringProperty(
        name="Original Color Type",
        description="Stored viewport color type for restoration",
        default='MATERIAL',
    )

    bpy.utils.register_class(ASSET_OT_check_highpoly)
    bpy.utils.register_class(ASSET_OT_refresh_highpoly)
    bpy.utils.register_class(ASSET_OT_select_highpoly)
    bpy.utils.register_class(ASSET_OT_isolate_highpoly)
    bpy.utils.register_class(ASSET_OT_exit_highpoly)


def unregister():
    bpy.utils.unregister_class(ASSET_OT_exit_highpoly)
    bpy.utils.unregister_class(ASSET_OT_isolate_highpoly)
    bpy.utils.unregister_class(ASSET_OT_select_highpoly)
    bpy.utils.unregister_class(ASSET_OT_refresh_highpoly)
    bpy.utils.unregister_class(ASSET_OT_check_highpoly)

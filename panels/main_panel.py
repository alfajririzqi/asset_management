import bpy
import os
import bpy.utils.previews

icon = None

def get_icon_id(name):
    global icon
    return icon[name].icon_id if icon and name in icon else 0

class ASSET_MANAGEMENT_PT_main(bpy.types.Panel):
    bl_idname = "ASSET_MANAGEMENT_PT_main"
    bl_label = "Asset Management"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'

    def draw_header(self, context):
        self.layout.label(icon_value=get_icon_id("asset_logo"))

    def draw(self, context):
        pass

class ASSET_STATS_PT_panel(bpy.types.Panel):
    bl_idname = "ASSET_STATS_PT_panel"
    bl_label = "Statistics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'
    bl_parent_id = "ASSET_MANAGEMENT_PT_main"

    def draw(self, context):
        layout = self.layout
        
        # Count statistics (exclude Render Result & Viewer Node)
        total_objects = len([obj for obj in bpy.data.objects if obj.type == 'MESH'])
        total_materials = len(bpy.data.materials)
        total_textures = len([img for img in bpy.data.images 
                             if img.source == 'FILE' and img.name not in ('Render Result', 'Viewer Node')])
        total_libraries = len(bpy.data.libraries)
        total_nodegroups = len(bpy.data.node_groups)
        
        total_unused = 0
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                total_unused += 1
        for mat in bpy.data.materials:
            if mat.users == 0:
                total_unused += 1
        for img in bpy.data.images:
            if img.name not in ('Render Result', 'Viewer Node') and img.users == 0:
                total_unused += 1
        for obj in bpy.data.objects:
            if obj.users == 0:
                total_unused += 1
        for col in bpy.data.collections:
            if col.users == 0:
                total_unused += 1
        
        box = layout.box()
        
        # Row 1
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col1.label(text=f"📦 Objects: {total_objects}")
        col2 = split.column(align=True)
        col2.label(text=f"📚 Libraries: {total_libraries}")
        
        # Row 2
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col1.label(text=f"🎨 Materials: {total_materials}")
        col2 = split.column(align=True)
        col2.label(text=f"🔗 NodeGroups: {total_nodegroups}")
        
        # Row 3
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col1.label(text=f"🖼️  Textures: {total_textures}")
        col2 = split.column(align=True)
        col2.label(text=f"🗑️  Unused: {total_unused}")
        
        # Action buttons
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("scene.analyze_deep", icon='TEXT', text="Analyze Scene Deeply")        


class ASSET_ANALYSIS_PT_panel(bpy.types.Panel):
    bl_idname = "ASSET_ANALYSIS_PT_panel"
    bl_label = "Analysis Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'
    bl_parent_id = "ASSET_MANAGEMENT_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        analysis_box = layout.box()
        analysis_box.label(text="High Poly Analysis", icon='ZOOM_ALL')
        
        row = analysis_box.row(align=True)
        row.prop(context.scene, "highpoly_threshold", text="Threshold")
        row.prop(context.scene, "highpoly_use_modifiers", text="", icon='MODIFIER')
        
        if hasattr(context.scene, "highpoly_mode_active"):
            if not context.scene.highpoly_mode_active:
                # Initial check button
                check_row = analysis_box.row()
                check_row.scale_y = 1.5
                check_row.operator("asset.check_highpoly", text="CHECK HIGH POLY OBJECTS", icon='VIEWZOOM')
            else:
                # Row 1: Select All | Isolate | Refresh
                action_row = analysis_box.row(align=True)
                action_row.scale_y = 1.3
                
                action_row.operator("asset.select_highpoly", text="Select All", icon='RESTRICT_SELECT_OFF')
                
                # Isolate button - changes based on state
                is_isolated = context.scene.highpoly_isolated if hasattr(context.scene, 'highpoly_isolated') else False
                if is_isolated:
                    action_row.operator("asset.isolate_highpoly", text="Un-Isolate", icon='RESTRICT_VIEW_OFF')
                else:
                    action_row.operator("asset.isolate_highpoly", text="Isolate", icon='RESTRICT_VIEW_ON')
                
                # Refresh button
                action_row.operator("asset.refresh_highpoly", text="Refresh", icon='FILE_REFRESH')
                
                # Row 2: Exit button
                exit_row = analysis_box.row(align=True)
                exit_row.scale_y = 1.3
                exit_row.alert = True
                exit_row.operator("asset.exit_highpoly", text="Exit", icon='CANCEL')
                
                # Simple statistics
                high_poly_count = 0
                total_tris = 0
                hidden_count = 0
                
                for obj in context.scene.objects:
                    if obj.type == 'MESH':
                        # Count hidden objects (not in view layer)
                        if obj.name not in context.view_layer.objects:
                            hidden_count += 1
                        
                        # Count high poly objects
                        if "_high_poly" in obj:
                            high_poly_count += 1
                            if "_tris_count" in obj:
                                total_tris += obj["_tris_count"]
                
                if high_poly_count > 0:
                    # Format tris count with K/M suffix
                    if total_tris >= 1000000:
                        tris_text = f"{total_tris / 1000000:.1f}M"
                    elif total_tris >= 1000:
                        tris_text = f"{total_tris / 1000:.0f}K"
                    else:
                        tris_text = str(total_tris)
                    
                    stats_row = analysis_box.row()
                    stats_row.alert = True
                    stats_row.label(text=f"📊 {high_poly_count} objects • {tris_text} tris", icon='INFO')
                else:
                    stats_row = analysis_box.row()
                    stats_row.label(text="✓ No high-poly objects found", icon='CHECKMARK')
                
                # Always show hidden count info
                if hidden_count > 0:
                    warning_row = analysis_box.row()
                    warning_row.label(text=f"ℹ {hidden_count} hidden objects not analyzed", icon='HIDE_ON')
        else:
            analysis_box.label(text="Initializing...", icon='INFO')
            analysis_box.label(text="Please restart Blender to load this add-on", icon='ERROR')
        
        # Transform Check Analysis
        layout.separator()
        transform_box = layout.box()
        transform_box.label(text="Transform Check", icon='OBJECT_ORIGIN')
        
        if hasattr(context.scene, "transform_mode_active"):
            if not context.scene.transform_mode_active:
                # Initial check button
                check_row = transform_box.row()
                check_row.scale_y = 1.5
                check_row.operator("asset.check_transform", text="CHECK TRANSFORMS", icon='VIEWZOOM')
            else:
                # Row 1: Select Issues | Apply | Refresh
                action_row = transform_box.row(align=True)
                action_row.scale_y = 1.3
                
                action_row.operator("asset.select_transform_issues", text="Select Issues", icon='RESTRICT_SELECT_OFF')
                action_row.operator("asset.apply_all_transforms", text="Apply", icon='CHECKMARK')
                action_row.operator("asset.refresh_transform", text="Refresh", icon='FILE_REFRESH')
                
                # Row 2: Exit button (red alert)
                exit_row = transform_box.row(align=True)
                exit_row.scale_y = 1.3
                exit_row.alert = True
                exit_row.operator("asset.exit_transform", text="Exit", icon='CANCEL')
                
                # Simple statistics
                issue_count = context.scene.transform_issue_count
                hidden_count = 0
                
                # Count hidden objects
                for obj in context.scene.objects:
                    if obj.type == 'MESH' and obj.name not in context.view_layer.objects:
                        hidden_count += 1
                
                if issue_count > 0:
                    stats_col = transform_box.column(align=True)
                    stats_col.alert = True
                    stats_col.label(text=f"📊 {issue_count} objects with issues", icon='INFO')
                    
                    # Detailed breakdown (minimal)
                    if context.scene.transform_unapplied_scale > 0:
                        stats_col.label(text=f"  • {context.scene.transform_unapplied_scale} unapplied scale", icon='BLANK1')
                    if context.scene.transform_extreme_scale > 0:
                        stats_col.label(text=f"  • {context.scene.transform_extreme_scale} extreme scale", icon='BLANK1')
                    if context.scene.transform_unapplied_rotation > 0:
                        stats_col.label(text=f"  • {context.scene.transform_unapplied_rotation} unapplied rotation", icon='BLANK1')
                else:
                    stats_row = transform_box.row()
                    stats_row.label(text="✓ All transforms clean", icon='CHECKMARK')
                
                # Always show hidden count info
                if hidden_count > 0:
                    warning_row = transform_box.row()
                    warning_row.label(text=f"ℹ {hidden_count} hidden objects not analyzed", icon='HIDE_ON')
        else:
            transform_box.label(text="Initializing...", icon='INFO')


class ASSET_OPTIMIZATION_PT_panel(bpy.types.Panel):
    bl_idname = "ASSET_OPTIMIZATION_PT_panel"
    bl_label = "Optimization Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'
    bl_parent_id = "ASSET_MANAGEMENT_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        # Check if published file
        from ..utils.published_file_detector import detect_published_file_status
        is_published, source_path = detect_published_file_status(context)
        
        # Published file warning (inline)
        if is_published:
            warning_row = layout.row()
            warning_row.alert = True
            warning_col = warning_row.column(align=True)
            warning_col.scale_y = 0.8
            warning_col.label(text="🚫 Published file - Operations disabled", icon='ERROR')
            layout.separator()
        
        # ====================================================================
        # ASSET OPTIMIZATION SECTION
        # ====================================================================
        
        optimization_box = layout.box()
        optimization_box.label(text="Asset Optimization", icon='TOOL_SETTINGS')
        
        # Linked Objects
        row = optimization_box.row()
        row.enabled = not is_published
        row.scale_y = 1.2
        row.operator("asset.optimize_linked_objects", text="Optimize Linked Objects", icon='LINKED')
        
        # Material Duplicates
        row = optimization_box.row()
        row.enabled = not is_published
        row.scale_y = 1.2
        row.operator("asset.optimize_material_duplicates", text="Optimize Material Duplicates", icon='MATERIAL')
        
        # Texture Duplicates
        row = optimization_box.row()
        row.enabled = not is_published
        row.scale_y = 1.2
        row.operator("asset.optimize_texture_duplicates", text="Optimize Texture Duplicates", icon='TEXTURE')
        
        layout.separator()
        
        # ====================================================================
        # CLEANUP SECTION
        # ====================================================================
        
        cleanup_box = layout.box()
        cleanup_box.label(text="Cleanup Operations", icon='BRUSH_DATA')
        
        # Clear Unused Material Slots
        row = cleanup_box.row()
        row.enabled = not is_published
        row.scale_y = 1.2
        row.operator("material.clear_unused_slots", text="Clear Unused Material Slots", icon='TRASH')
        
        # Clear Orphan Data
        row = cleanup_box.row()
        row.enabled = not is_published
        row.scale_y = 1.2
        row.operator("scene.clear_orphan_data", text="Clear Orphan Data", icon='ORPHAN_DATA')

def register_icon():
    global icon
    script_dir = os.path.dirname(__file__)
    icons_dir = os.path.join(script_dir, "icons")
    icon = bpy.utils.previews.new()
    icon.load("asset_logo", os.path.join(icons_dir, "logo.png"), 'IMAGE')

def unregister_icon():
    global icon
    if icon:
        bpy.utils.previews.remove(icon)
        icon = None

def register():
    register_icon()
    
    # High Poly Analysis settings
    bpy.types.Scene.highpoly_threshold = bpy.props.IntProperty(
        default=50000,
        min=1
    )
    
    bpy.types.Scene.highpoly_use_modifiers = bpy.props.BoolProperty(
        default=True
    )
    
    bpy.types.Scene.highpoly_mode_active = bpy.props.BoolProperty(
        default=False
    )
    
    bpy.utils.register_class(ASSET_MANAGEMENT_PT_main)
    bpy.utils.register_class(ASSET_STATS_PT_panel)
    bpy.utils.register_class(ASSET_ANALYSIS_PT_panel)
    bpy.utils.register_class(ASSET_OPTIMIZATION_PT_panel)


def unregister():
    unregister_icon()
    bpy.utils.unregister_class(ASSET_OPTIMIZATION_PT_panel)
    bpy.utils.unregister_class(ASSET_ANALYSIS_PT_panel)
    bpy.utils.unregister_class(ASSET_STATS_PT_panel)
    bpy.utils.unregister_class(ASSET_MANAGEMENT_PT_main)
    
    del bpy.types.Scene.highpoly_threshold
    del bpy.types.Scene.highpoly_use_modifiers
    del bpy.types.Scene.highpoly_mode_active
import bpy
import os
import time
from ..utils.published_file_detector import detect_published_file_status


class FILE_PT_Versioning(bpy.types.Panel):
    """File Versioning Panel"""
    bl_label = "Versioning"
    bl_idname = "FILE_PT_versioning"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Management'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        is_version_file = False
        if bpy.data.filepath:
            current_dir = os.path.dirname(bpy.data.filepath)
            if os.path.basename(current_dir) == "versions" or "versions" + os.sep in bpy.data.filepath:
                is_version_file = True
        
        is_published, source_path = detect_published_file_status(context)

        box = layout.box()
        if bpy.data.filepath:
            fname = os.path.basename(bpy.data.filepath)
            col = box.column(align=True)
            col.label(text="Active File:", icon='FILE_BLEND')
            col.label(text=fname, icon='BLANK1')
            
            try:
                mod = time.localtime(os.path.getmtime(bpy.data.filepath))
                mod_s = time.strftime("%Y-%m-%d %H:%M:%S", mod)
                col.separator(factor=0.5)
                col.label(text="Last Modified:", icon='TIME')
                col.label(text=mod_s, icon='BLANK1')
            except Exception:
                pass
        else:
            box.label(text="File not saved", icon='ERROR')
        
        if is_published:
            layout.separator()
            warning_row = layout.row()
            warning_row.alert = True
            warning_col = warning_row.column(align=True)
            warning_col.scale_y = 0.8
            warning_col.label(text="🚫 Published file - Operations disabled", icon='ERROR')
            if source_path:
                row = warning_col.row()
                row.scale_y = 1.2
                op = row.operator("asset.copy_source_path", text=f"Source: {source_path}", icon='COPYDOWN', emboss=False)
                op.source_path = source_path
        
        if is_version_file:
            layout.separator()
            warning_row = layout.row()
            warning_row.alert = True
            warning_col = warning_row.column(align=True)
            warning_col.scale_y = 0.8
            warning_col.label(text="🚫 Version file - Cannot create version", icon='ERROR')
            warning_col.label(text="Open the original file to create versions", icon='BLANK1')

        row = layout.row(align=True)
        row.scale_y = 1.3
        col = row.column(align=True)
        col.operator("file.save_version", icon='ADD', text="Create Version")
        if not bpy.data.filepath or is_published or is_version_file:
            col.enabled = False

        # Restore version section
        box = layout.box()
        box.label(text="Restore Version", icon='FILE_REFRESH')
        
        row = box.row(align=True)
        row.prop(scene, "selected_version", text="")

        row = box.row(align=True)
        row.scale_y = 1.2
        can_restore = bool(bpy.data.filepath and scene.selected_version and scene.selected_version != 'NONE' and not is_published and not is_version_file)
        row.enabled = can_restore
        row.operator("file.restore_version", icon='FILE_TICK', text="Restore")

        if bpy.data.filepath:
            versions_dir = os.path.join(os.path.dirname(bpy.data.filepath), "versions")
            if os.path.exists(versions_dir):
                import re
                current_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
                pattern = re.compile(rf"^{re.escape(current_name)}_v\d{{3}}\.blend$")
                
                blends = [f for f in os.listdir(versions_dir) if pattern.match(f)]
                blends.sort(key=lambda f: os.path.getmtime(os.path.join(versions_dir, f)), reverse=True)
                count = len(blends)
                
                col = layout.column(align=True)
                col.label(text=f"Available versions: {count}", icon='LINENUMBERS_ON')
                
                if blends:
                    latest = blends[0]
                    latest_m = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
                        os.path.getmtime(os.path.join(versions_dir, latest))
                    ))
                    col.label(text=f"Newest: {latest}", icon='BLANK1')
                    col.label(text=f"Time: {latest_m}", icon='BLANK1')
            else:
                layout.separator()
                layout.label(text="No versions folder found", icon='INFO')


def register():
    bpy.utils.register_class(FILE_PT_Versioning)


def unregister():
    bpy.utils.unregister_class(FILE_PT_Versioning)
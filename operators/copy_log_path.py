import bpy


class ASSET_OT_CopyActivityLogPath(bpy.types.Operator):
    """Copy activity log file path to clipboard"""
    bl_idname = "asset.copy_activity_log_path"
    bl_label = "Copy Log Path"
    bl_description = "Copy activity log file path to clipboard"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        from ..utils.activity_logger import get_log_path
        
        log_path = get_log_path(context)
        
        if not log_path:
            self.report({'WARNING'}, "Activity logging is disabled")
            return {'CANCELLED'}
        
        context.window_manager.clipboard = log_path
        self.report({'INFO'}, f"Copied: {log_path}")
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_CopyActivityLogPath)


def unregister():
    bpy.utils.unregister_class(ASSET_OT_CopyActivityLogPath)

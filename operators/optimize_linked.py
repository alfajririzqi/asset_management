import bpy
import hashlib

class ASSET_OT_optimize_linked_objects(bpy.types.Operator):
    """Convert full duplicates (Shift+D) to linked duplicates (Alt+D)."""
    bl_idname = "asset.optimize_linked_objects"
    bl_label = "Optimize Linked Objects"
    bl_description = "Convert full duplicates (Shift+D) to linked duplicates (Alt+D)"
    bl_options = {'REGISTER', 'UNDO'}

    duplicate_groups = []

    def find_duplicates(self, context):
        """Find groups of objects that share identical geometry but use different mesh datablocks."""
        mesh_objects = [obj for obj in context.scene.objects if obj.type == 'MESH']
        if not mesh_objects:
            return []

        mesh_groups = {}
        for obj in mesh_objects:
            mesh_hash = self.get_mesh_hash(obj.data)
            mesh_groups.setdefault(mesh_hash, []).append(obj)

        duplicate_groups = []
        for objs in mesh_groups.values():
            if len(objs) <= 1:
                continue

            data_groups = {}
            for obj in objs:
                data_groups.setdefault(obj.data, []).append(obj)

            if len(data_groups) > 1:
                base_data_group = max(data_groups.values(), key=len)
                base_data = base_data_group[0].data

                to_convert = []
                for data, group in data_groups.items():
                    if data != base_data:
                        to_convert.extend(group)

                if to_convert:
                    duplicate_groups.append([base_data_group[0]] + to_convert)

        return duplicate_groups

    def get_mesh_hash(self, mesh):
        """Generate a hash from mesh geometry (vertices and faces)."""
        if not mesh or not mesh.vertices or not mesh.polygons:
            return "empty"
        vertices = [v.co[:] for v in mesh.vertices]
        faces = [tuple(p.vertices) for p in mesh.polygons]
        data = (tuple(vertices), tuple(faces))
        return hashlib.sha256(str(data).encode('utf-8')).hexdigest()

    def invoke(self, context, event):
        self.duplicate_groups = self.find_duplicates(context)
        if not self.duplicate_groups:
            self.report({'INFO'}, "No duplicate objects detected")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        
        total_duplicates = sum(len(group) - 1 for group in self.duplicate_groups)
        
        # Header with summary
        box = layout.box()
        box.label(text=f"🔗 Found {len(self.duplicate_groups)} duplicate group(s)", icon='INFO')
        box.label(text=f"Total {total_duplicates} object(s) will be linked", icon='OBJECT_DATAMODE')
        
        layout.separator()
        
        max_groups = 15
        for i, group in enumerate(self.duplicate_groups[:max_groups]):
            if i > 0:
                layout.separator(factor=0.5)
            
            base = group[0]
            layout.label(text=f"Base: {base.name}", icon='OBJECT_DATAMODE')
            
            duplicates = group[1:]
            if duplicates:
                grid = layout.grid_flow(row_major=True, columns=2, align=True)
                grid.scale_y = 0.8
                
                max_display = 6  
                for obj in duplicates[:max_display]:
                    grid.label(text=f"→ {obj.name}", icon='LINKED')
                
                # Show "more items" if list is long
                if len(duplicates) > max_display:
                    layout.label(text=f"  ... and {len(duplicates) - max_display} more", icon='THREE_DOTS')
        
        # Show "more groups" if many groups
        if len(self.duplicate_groups) > max_groups:
            layout.separator()
            row = layout.row()
            row.label(text=f"... and {len(self.duplicate_groups) - max_groups} more groups", icon='THREE_DOTS')

    def execute(self, context):
        converted_count = 0
        orphan_meshes = set()

        for group in self.duplicate_groups:
            base_obj = group[0]
            for obj in group[1:]:
                old_data = obj.data
                obj.data = base_obj.data
                orphan_meshes.add(old_data)
                converted_count += 1

        cleaned_orphans = 0
        for mesh in orphan_meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
                cleaned_orphans += 1

        self.report(
            {'INFO'},
            f"Converted {converted_count} objects; removed {cleaned_orphans} orphan mesh(es)"
        )
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_optimize_linked_objects)


def unregister():
    bpy.utils.unregister_class(ASSET_OT_optimize_linked_objects)

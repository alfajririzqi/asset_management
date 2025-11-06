import bpy


class MATERIAL_OT_ClearUnusedSlots(bpy.types.Operator):
    """Remove empty and unused material slots from selected objects"""
    bl_idname = "material.clear_unused_slots"
    bl_label = "Clear Unused Material Slots"
    bl_description = "Remove empty slots and materials not assigned to any faces"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects and any(obj.type == 'MESH' for obj in context.selected_objects)
    
    def execute(self, context):
        empty_slots_removed = 0
        unused_materials_removed = 0
        processed_objects = 0
        
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.data:
                continue
            
            processed_objects += 1
            mesh = obj.data
            
            # Get materials actually used by faces
            used_material_indices = set()
            for poly in mesh.polygons:
                used_material_indices.add(poly.material_index)
            
            # Find slots to remove (empty or unused)
            slots_to_remove = []
            for i, slot in enumerate(obj.material_slots):
                # Remove if empty (None)
                if slot.material is None:
                    slots_to_remove.append(i)
                    empty_slots_removed += 1
                # Remove if not used by any face
                elif i not in used_material_indices:
                    slots_to_remove.append(i)
                    unused_materials_removed += 1
            
            # Remove slots from end to start (avoid index shifting)
            for slot_index in reversed(slots_to_remove):
                obj.active_material_index = slot_index
                # Use proper context
                with context.temp_override(object=obj):
                    bpy.ops.object.material_slot_remove()
        
        # Report results
        total_removed = empty_slots_removed + unused_materials_removed
        if total_removed > 0:
            msg = f"Removed {total_removed} slot(s) from {processed_objects} object(s)"
            if empty_slots_removed > 0:
                msg += f" ({empty_slots_removed} empty"
            if unused_materials_removed > 0:
                if empty_slots_removed > 0:
                    msg += f", {unused_materials_removed} unused)"
                else:
                    msg += f" ({unused_materials_removed} unused)"
            elif empty_slots_removed > 0:
                msg += ")"
            self.report({'INFO'}, msg)
        else:
            self.report({'INFO'}, f"No unused material slots found in {processed_objects} object(s)")
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MATERIAL_OT_ClearUnusedSlots)


def unregister():
    bpy.utils.unregister_class(MATERIAL_OT_ClearUnusedSlots)

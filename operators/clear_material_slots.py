import bpy


class MATERIAL_OT_ClearUnusedSlots(bpy.types.Operator):
    """Remove empty and unused material slots from selected objects"""
    bl_idname = "material.clear_unused_slots"
    bl_label = "Clear Unused Material Slots"
    bl_description = "Remove empty slots and materials not assigned to any faces"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Store preview data for dialog
    preview_data = {}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects and any(obj.type == 'MESH' for obj in context.selected_objects)
    
    def invoke(self, context, event):
        """Scan and show confirmation dialog with preview"""
        self.preview_data = self._scan_unused_slots(context)
        
        total_removable = sum(len(slots) for slots in self.preview_data.values())
        
        if total_removable == 0:
            self.report({'INFO'}, "No unused material slots found")
            return {'CANCELLED'}
        
        # Show confirmation dialog
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        """Draw confirmation dialog with preview"""
        layout = self.layout
        
        total_removable = sum(len(slots) for slots in self.preview_data.values())
        
        # Header
        box = layout.box()
        box.label(text=f"🧹 Found {total_removable} unused slot(s) in {len(self.preview_data)} object(s)", icon='INFO')
        
        layout.separator()
        
        # Show objects and their unused slots with grid layout
        max_objects = 10
        obj_items = list(self.preview_data.items())[:max_objects]
        
        for obj_name, slot_info in obj_items:
            obj_box = layout.box()
            obj_box.label(text=f"Object: {obj_name}", icon='OBJECT_DATA')
            
            # Grid layout for slot names (2 columns)
            if slot_info:
                grid = obj_box.grid_flow(row_major=True, columns=2, align=True)
                grid.scale_y = 0.8
                
                max_slots = 8
                for slot_name, slot_type in slot_info[:max_slots]:
                    icon = 'BLANK1' if slot_type == 'empty' else 'MATERIAL'
                    label = f"→ {slot_name}" if slot_name else "→ [Empty Slot]"
                    grid.label(text=label, icon=icon)
                
                # Show "more items" if many slots
                if len(slot_info) > max_slots:
                    obj_box.label(text=f"  ... and {len(slot_info) - max_slots} more slots", icon='THREE_DOTS')
        
        # Show "more objects" if many objects
        if len(self.preview_data) > max_objects:
            layout.separator()
            row = layout.row()
            row.label(text=f"... and {len(self.preview_data) - max_objects} more objects", icon='THREE_DOTS')
        
        layout.separator()
        layout.label(text="Remove these unused slots?", icon='QUESTION')
    
    def _scan_unused_slots(self, context):
        """Scan for unused material slots
        
        Returns:
            dict: {obj_name: [(slot_name, slot_type), ...]}
        """
        preview = {}
        
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.data:
                continue
            
            mesh = obj.data
            
            # Get materials actually used by faces
            used_material_indices = set()
            for poly in mesh.polygons:
                used_material_indices.add(poly.material_index)
            
            # Find slots to remove (empty or unused)
            unused_slots = []
            for i, slot in enumerate(obj.material_slots):
                # Empty slot
                if slot.material is None:
                    unused_slots.append(("[Empty Slot]", 'empty'))
                # Unused slot
                elif i not in used_material_indices:
                    unused_slots.append((slot.material.name, 'unused'))
            
            if unused_slots:
                preview[obj.name] = unused_slots
        
        return preview
    
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

import bpy


class SCENE_OT_ClearOrphanData(bpy.types.Operator):
    """Clear unused data (orphan data and unused linked libraries)"""
    bl_idname = "scene.clear_orphan_data"
    bl_label = "Clear Unused Data"
    bl_description = "Remove orphan datablocks and unused linked libraries"
    bl_options = {'REGISTER', 'UNDO'}

    orphan_stats = {}
    unused_libraries = []

    def invoke(self, context, event):
        self.orphan_stats = self._scan_orphan_data()
        self.unused_libraries = self._scan_unused_libraries()
        total_orphans = sum(self.orphan_stats.values())
        
        if total_orphans == 0 and len(self.unused_libraries) == 0:
            self.report({'INFO'}, "No unused data found")
            return {'CANCELLED'}
        
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        
        total_orphans = sum(self.orphan_stats.values())
        
        # Orphan data summary
        box = layout.box()
        box.label(text=f"Orphan Data: {total_orphans} item(s)", icon='ORPHAN_DATA')
        
        if total_orphans > 0:
            col = box.column(align=True)
            
            for data_type, count in self.orphan_stats.items():
                if count > 0:
                    icon = self._get_icon_for_datatype(data_type)
                    col.label(text=f"  • {data_type}: {count}", icon=icon)
            
            # Show detailed list for Materials
            if self.orphan_stats.get('Materials', 0) > 0:
                layout.separator()
                mat_box = layout.box()
                mat_box.label(text="📦 Unused Materials List:", icon='MATERIAL')
                
                unused_materials = [mat.name for mat in bpy.data.materials if mat.users == 0]
                
                # Use grid layout (2 columns) for compact display
                grid = mat_box.grid_flow(row_major=True, columns=2, align=True)
                grid.scale_y = 0.8
                
                max_display = 15
                for i, mat_name in enumerate(sorted(unused_materials[:max_display])):
                    grid.label(text=f"• {mat_name}", icon='BLANK1')
                
                # Show "more items" if list is long
                if len(unused_materials) > max_display:
                    mat_box.separator()
                    row = mat_box.row()
                    row.label(text=f"... and {len(unused_materials) - max_display} more materials", icon='THREE_DOTS')
        
        # Unused libraries
        if self.unused_libraries:
            layout.separator()
            box = layout.box()
            box.label(text=f"Unused Libraries: {len(self.unused_libraries)}", icon='LIBRARY_DATA_BROKEN')
            
            col = box.column(align=True)
            for lib_path in self.unused_libraries[:5]:
                import os
                lib_name = os.path.basename(lib_path)
                col.label(text=f"  • {lib_name}", icon='BLANK1')
            
            if len(self.unused_libraries) > 5:
                col.label(text=f"  • ... and {len(self.unused_libraries) - 5} more", icon='BLANK1')
        
        # Warning
        layout.separator()
        layout.label(text="⚠️ This operation cannot be undone!", icon='ERROR')
        layout.label(text="Make sure to save a backup first.", icon='INFO')

    def execute(self, context):
        removed_orphans = 0
        removed_libraries = 0
        
        # Clear orphan data (run multiple times to catch nested orphans)
        for _ in range(3):
            count = self._clear_orphan_data()
            removed_orphans += count
            if count == 0:
                break
        
        removed_libraries = self._clear_unused_libraries()
        
        # Report
        msg = f"✅ Removed {removed_orphans} orphan datablock(s)"
        if removed_libraries > 0:
            msg += f" • {removed_libraries} unused library(ies)"
        
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def _scan_orphan_data(self):
        """Scan for orphan datablocks (0 users)"""
        stats = {
            'Meshes': 0,
            'Materials': 0,
            'Textures': 0,
            'Images': 0,
            'Objects': 0,
            'Collections': 0,
            'Actions': 0,
            'Curves': 0,
            'Lights': 0,
            'Cameras': 0,
        }
        
        # Meshes
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                stats['Meshes'] += 1
        
        # Materials
        for mat in bpy.data.materials:
            if mat.users == 0:
                stats['Materials'] += 1
        
        # Textures
        for tex in bpy.data.textures:
            if tex.users == 0:
                stats['Textures'] += 1
        
        # Images (exclude Render Result and Viewer Node)
        for img in bpy.data.images:
            if img.name not in ('Render Result', 'Viewer Node') and img.users == 0:
                stats['Images'] += 1
        
        # Objects
        for obj in bpy.data.objects:
            if obj.users == 0:
                stats['Objects'] += 1
        
        # Collections
        for col in bpy.data.collections:
            if col.users == 0:
                stats['Collections'] += 1
        
        # Actions
        for action in bpy.data.actions:
            if action.users == 0:
                stats['Actions'] += 1
        
        # Curves
        for curve in bpy.data.curves:
            if curve.users == 0:
                stats['Curves'] += 1
        
        # Lights
        for light in bpy.data.lights:
            if light.users == 0:
                stats['Lights'] += 1
        
        # Cameras
        for camera in bpy.data.cameras:
            if camera.users == 0:
                stats['Cameras'] += 1
        
        return stats

    def _scan_unused_libraries(self):
        """Scan for linked libraries with no users (check objects, materials, meshes, node groups, images)"""
        unused = []
        
        for lib in bpy.data.libraries:
            has_users = False
            
            # Check objects from this library
            for obj in bpy.data.objects:
                if obj.library == lib and obj.users > 0:
                    has_users = True
                    break
            
            if not has_users:
                # Check materials
                for mat in bpy.data.materials:
                    if mat.library == lib and mat.users > 0:
                        has_users = True
                        break
            
            if not has_users:
                # Check meshes
                for mesh in bpy.data.meshes:
                    if mesh.library == lib and mesh.users > 0:
                        has_users = True
                        break
            
            if not has_users:
                # Check collections
                for col in bpy.data.collections:
                    if col.library == lib and col.users > 0:
                        has_users = True
                        break
            
            if not has_users:
                # Check node groups (critical for shader editor)
                for node_group in bpy.data.node_groups:
                    if node_group.library == lib:

                        is_used = False
                        
                        for mat in bpy.data.materials:
                            if mat.use_nodes and mat.node_tree:
                                for node in mat.node_tree.nodes:
                                    if node.type == 'GROUP' and node.node_tree == node_group:
                                        is_used = True
                                        break
                            if is_used:
                                break
                        
                        if is_used:
                            has_users = True
                            break
            
            if not has_users:
                # Check images from this library (textures in shader editor)
                for img in bpy.data.images:
                    if img.library == lib:
                        is_used = False
                        
                        for mat in bpy.data.materials:
                            if mat.use_nodes and mat.node_tree:
                                for node in mat.node_tree.nodes:
                                    if node.type == 'TEX_IMAGE' and node.image == img:
                                        is_used = True
                                        break
                            if is_used:
                                break
                        
                        if is_used:
                            has_users = True
                            break
            
            if not has_users:
                unused.append(lib.filepath)
        
        return unused

    def _clear_orphan_data(self):
        """Clear orphan datablocks, return count removed"""
        removed = 0
        
        # Meshes
        for mesh in list(bpy.data.meshes):
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
                removed += 1
        
        # Materials
        for mat in list(bpy.data.materials):
            if mat.users == 0:
                bpy.data.materials.remove(mat)
                removed += 1
        
        # Textures
        for tex in list(bpy.data.textures):
            if tex.users == 0:
                bpy.data.textures.remove(tex)
                removed += 1
        
        # Images (exclude Render Result and Viewer Node)
        for img in list(bpy.data.images):
            if img.name not in ('Render Result', 'Viewer Node') and img.users == 0:
                bpy.data.images.remove(img)
                removed += 1
        
        # Objects
        for obj in list(bpy.data.objects):
            if obj.users == 0:
                bpy.data.objects.remove(obj)
                removed += 1
        
        # Collections
        for col in list(bpy.data.collections):
            if col.users == 0:
                bpy.data.collections.remove(col)
                removed += 1
        
        # Actions
        for action in list(bpy.data.actions):
            if action.users == 0:
                bpy.data.actions.remove(action)
                removed += 1
        
        # Curves
        for curve in list(bpy.data.curves):
            if curve.users == 0:
                bpy.data.curves.remove(curve)
                removed += 1
        
        # Lights
        for light in list(bpy.data.lights):
            if light.users == 0:
                bpy.data.lights.remove(light)
                removed += 1
        
        # Cameras
        for camera in list(bpy.data.cameras):
            if camera.users == 0:
                bpy.data.cameras.remove(camera)
                removed += 1
        
        return removed

    def _clear_unused_libraries(self):
        """Clear unused linked libraries, return count removed"""
        removed = 0
        
        for lib_path in self.unused_libraries:
            for lib in list(bpy.data.libraries):
                if lib.filepath == lib_path:
                    try:
                        bpy.data.libraries.remove(lib)
                        removed += 1
                    except Exception as e:
                        print(f"Could not remove library {lib.filepath}: {e}")
        
        return removed

    def _get_icon_for_datatype(self, data_type):
        """Get appropriate icon for datatype"""
        icons = {
            'Meshes': 'MESH_DATA',
            'Materials': 'MATERIAL',
            'Textures': 'TEXTURE',
            'Images': 'IMAGE_DATA',
            'Objects': 'OBJECT_DATA',
            'Collections': 'OUTLINER_COLLECTION',
            'Actions': 'ACTION',
            'Curves': 'CURVE_DATA',
            'Lights': 'LIGHT',
            'Cameras': 'CAMERA_DATA',
        }
        return icons.get(data_type, 'DOT')


def register():
    bpy.utils.register_class(SCENE_OT_ClearOrphanData)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_ClearOrphanData)
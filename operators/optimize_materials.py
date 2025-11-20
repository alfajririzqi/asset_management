import bpy
from collections import defaultdict


class ASSET_OT_optimize_material_duplicates(bpy.types.Operator):
    """Merge duplicate materials into single material instances."""
    bl_idname = "asset.optimize_material_duplicates"
    bl_label = "Optimize Material Duplicates"
    bl_description = "Merge duplicate materials (same properties) into single material"
    bl_options = {'REGISTER', 'UNDO'}

    duplicate_groups = []

    def get_socket_value(self, socket):
        """Safely get socket default value"""
        if not hasattr(socket, 'default_value'):
            return None
        
        try:
            val = socket.default_value
            if hasattr(val, '__iter__') and not isinstance(val, str):
                return tuple(round(v, 6) for v in val)  
            elif isinstance(val, (int, float)):
                return round(val, 6)
            else:
                return val
        except:
            return None

    def get_node_properties(self, node):
        """Get comprehensive node properties for all node types"""
        props = []
        
        props.append(('type', node.type))
        
        if node.type == 'TEX_IMAGE':
            if node.image:
                props.append(('image_filepath', node.image.filepath))
                props.append(('colorspace', node.image.colorspace_settings.name))
                props.append(('interpolation', node.interpolation))
                props.append(('extension', node.extension))
            else:
                props.append(('image_filepath', None))
        
        elif node.type == 'BSDF_PRINCIPLED':
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
            props.append(('distribution', node.distribution))
        
        elif node.type == 'BSDF_DIFFUSE':
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        elif node.type == 'BSDF_GLOSSY':
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
            props.append(('distribution', node.distribution))
        
        elif node.type == 'MIX_SHADER':
            if not node.inputs[0].is_linked:
                val = self.get_socket_value(node.inputs[0])
                props.append(('fac', val))
        
        elif node.type == 'MIX':
            if hasattr(node, 'blend_type'):
                props.append(('blend_type', node.blend_type))
            if hasattr(node, 'data_type'):
                props.append(('data_type', node.data_type))
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        elif node.type == 'VALTORGB':  
            if hasattr(node, 'color_ramp'):
                ramp = node.color_ramp
                props.append(('interpolation', ramp.interpolation))
                stops = []
                for elem in ramp.elements:
                    stops.append((elem.position, tuple(elem.color)))
                props.append(('stops', tuple(stops)))
        
        elif node.type == 'VALUE':
            for output in node.outputs:
                val = self.get_socket_value(output)
                if val is not None:
                    props.append(('value', val))
        
        elif node.type == 'RGB':
            for output in node.outputs:
                val = self.get_socket_value(output)
                if val is not None:
                    props.append(('color', val))
        
        elif node.type == 'MATH':
            props.append(('operation', node.operation))
            if hasattr(node, 'use_clamp'):
                props.append(('use_clamp', node.use_clamp))
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        elif node.type == 'VECT_MATH':
            props.append(('operation', node.operation))
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        elif node.type == 'MAPPING':
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        elif node.type == 'TEX_COORD':
            if hasattr(node, 'object'):
                props.append(('object', node.object.name if node.object else None))
        
        elif node.type == 'NORMAL_MAP':
            props.append(('space', node.space))
            if hasattr(node, 'uv_map'):
                props.append(('uv_map', node.uv_map))
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        elif node.type == 'BUMP':
            if hasattr(node, 'invert'):
                props.append(('invert', node.invert))
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        else:
            for input in node.inputs:
                if not input.is_linked:
                    val = self.get_socket_value(input)
                    if val is not None:
                        props.append((f'input_{input.name}', val))
        
        return tuple(sorted(props, key=lambda x: x[0]))

    def get_material_hash(self, material):
        """Generate a comprehensive hash from material properties and node tree structure."""
        if not material:
            return "empty"

        props = []
        
        props.append(('diffuse_color', tuple(round(v, 6) for v in material.diffuse_color)))
        props.append(('metallic', round(material.metallic, 6)))
        props.append(('roughness', round(material.roughness, 6)))
        props.append(('use_nodes', material.use_nodes))
        
        if hasattr(material, 'blend_method'):
            props.append(('blend_method', material.blend_method))
        if hasattr(material, 'shadow_method'):
            props.append(('shadow_method', material.shadow_method))
        
        if material.use_nodes and material.node_tree:
            node_data = []
            
            for node in material.node_tree.nodes:
                node_props = self.get_node_properties(node)
                
                connections = []
                for output in node.outputs:
                    for link in output.links:
                        connections.append((
                            output.name,
                            link.to_node.type,
                            link.to_socket.name
                        ))
                
                node_tuple = (node_props, tuple(sorted(connections)))
                node_data.append(node_tuple)
            
            props.append(('nodes', tuple(sorted(node_data, key=str))))
        
        try:
            return hash(tuple(props))
        except TypeError as e:
            return str(props)

    def find_duplicates(self, context):
        """Find groups of materials that share identical properties."""
        material_groups = defaultdict(list)
        
        print("\n" + "="*60)
        print("DEBUG: Material Hash Analysis")
        print("="*60)
        
        for material in bpy.data.materials:
            if material.users == 0:
                continue
            
            try:
                mat_hash = self.get_material_hash(material)
                material_groups[mat_hash].append(material)
                
                print(f"\n{material.name}:")
                print(f"  Hash: {mat_hash}")
                print(f"  Users: {material.users}")
                if material.use_nodes and material.node_tree:
                    print(f"  Nodes: {len(material.node_tree.nodes)}")
                    for node in material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            print(f"    - {node.type}: {node.image.filepath}")
                        else:
                            print(f"    - {node.type}")
                            
            except Exception as e:
                print(f"Error hashing material {material.name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print("\n" + "="*60)
        print(f"Total hash groups: {len(material_groups)}")
        for hash_val, mats in material_groups.items():
            if len(mats) > 1:
                print(f"\nDuplicate group ({len(mats)} materials):")
                for mat in mats:
                    print(f"  - {mat.name}")
        print("="*60 + "\n")

        return [mats for mats in material_groups.values() if len(mats) > 1]

    def invoke(self, context, event):
        self.duplicate_groups = self.find_duplicates(context)
        
        if not self.duplicate_groups:
            self.report({'INFO'}, "No duplicate materials detected")
            return {'CANCELLED'}
        
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        
        total_duplicates = sum(len(group) - 1 for group in self.duplicate_groups)
        total_groups = len(self.duplicate_groups)
        
        # Header with summary
        box = layout.box()
        box.label(text=f"📦 Found {total_groups} duplicate group(s)", icon='INFO')
        box.label(text=f"Total {total_duplicates} material(s) will be merged", icon='MATERIAL')
        
        layout.separator()
        
        max_display_groups = 10
        groups_to_show = self.duplicate_groups[:max_display_groups]
        
        if total_groups <= 5:
            # 1 COLUMN LAYOUT (vertical)
            for i, group in enumerate(groups_to_show):
                if i > 0:
                    layout.separator(factor=0.5)
                
                base = group[0]
                duplicates = group[1:]
                
                box = layout.box()
                box.label(text=f"Base: {base.name}", icon='MATERIAL')
                
                if duplicates:
                    col = box.column(align=True)
                    col.scale_y = 0.8
                    
                    max_items = 3
                    for mat in duplicates[:max_items]:
                        col.label(text=f"  • {mat.name}", icon='LINKED')
                    
                    if len(duplicates) > max_items:
                        col.label(text=f"  ... and {len(duplicates) - max_items} more", icon='THREE_DOTS')
        else:
            # 2 COLUMN TABLE LAYOUT (side by side)
            split = layout.split(factor=0.5)
            col_left = split.column()
            col_right = split.column()
            
            for i, group in enumerate(groups_to_show):
                base = group[0]
                duplicates = group[1:]
                
                col = col_left if i < 5 else col_right
                
                if i % 5 > 0:
                    col.separator(factor=0.5)
                
                box = col.box()
                box.label(text=f"Base: {base.name}", icon='MATERIAL')
                
                if duplicates:
                    sub = box.column(align=True)
                    sub.scale_y = 0.8
                    
                    max_items = 3
                    for mat in duplicates[:max_items]:
                        sub.label(text=f"  • {mat.name}", icon='LINKED')
                    
                    if len(duplicates) > max_items:
                        sub.label(text=f"  ... and {len(duplicates) - max_items} more", icon='THREE_DOTS')
        
        # Show "more groups" if total > 5
        if total_groups > max_display_groups:
            layout.separator()
            row = layout.row()
            row.label(text=f"... and {total_groups - max_display_groups} more groups", icon='THREE_DOTS')

    def execute(self, context):
        materials_removed = 0
        slots_updated = 0

        for group in self.duplicate_groups:
            base_material = group[0]

            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    for slot in obj.material_slots:
                        if slot.material in group[1:]:
                            slot.material = base_material
                            slots_updated += 1

            for material in group[1:]:
                if material.users == 0:
                    bpy.data.materials.remove(material)
                    materials_removed += 1

        self.report(
            {'INFO'},
            f"✅ {materials_removed} materials removed • {slots_updated} slots updated"
        )
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ASSET_OT_optimize_material_duplicates)


def unregister():
    bpy.utils.unregister_class(ASSET_OT_optimize_material_duplicates)
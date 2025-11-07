import bpy, threading, os
from datetime import datetime

class SCENE_OT_AnalyzeSceneDeep(bpy.types.Operator):
    """Analyze scene deeply - Generate 4 detailed reports: Data Usage (overview), Material Usage, Texture Usage, and Texture Paths"""
    bl_idname = "scene.analyze_deep"
    bl_label = "Analyze Scene Deeply"
    bl_description = "Generate comprehensive reports with hybrid formatting for better readability"
    bl_options = {'REGISTER'}

    _timer = None
    _thread = None
    _is_running = False
    _reports_data = {}
    _progress = 0

    def modal(self, context, event):
        wm = context.window_manager
        if event.type == 'TIMER':
            wm.progress_update(self._progress)

            if not self._is_running and self._thread is not None:
                wm.event_timer_remove(self._timer)
                wm.progress_end()

                if self._reports_data.get('success'):
                    self._create_text_datablocks_main_thread()
                    
                    # Show completion dialog using separate operator
                    bpy.ops.scene.show_analysis_result('INVOKE_DEFAULT')
                    
                    return {'FINISHED'}
                else:
                    self.report({'ERROR'}, self._reports_data.get('error', 'Unknown error'))
                    return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        wm.progress_begin(0, 100)
        self._progress = 0

        self._is_running = True
        self._reports_data = {}
        self._thread = threading.Thread(target=self._generate_reports_thread)
        self._thread.start()

        return {'RUNNING_MODAL'}
    
    def _generate_reports_thread(self):
        try:
            self._progress = 10
            tex_paths_report = self._generate_texture_paths_report()

            self._progress = 40
            material_usage_report = self._generate_material_usage_report()

            self._progress = 70
            texture_usage_report = self._generate_texture_usage_report()

            self._progress = 90
            self._reports_data = {
                'success': True,
                'reports': [
                    {'name': "Scene_MaterialUsage", 'content': material_usage_report},
                    {'name': "Scene_TextureUsage", 'content': texture_usage_report},
                    {'name': "Scene_TexturePaths", 'content': tex_paths_report}
                ]
            }
            self._progress = 100
        except Exception as e:
            self._reports_data = {'success': False, 'error': str(e)}
        finally:
            self._is_running = False

    def _create_text_datablocks_main_thread(self):
        for report in self._reports_data.get('reports', []):
            if report['name'] in bpy.data.texts:
                bpy.data.texts.remove(bpy.data.texts[report['name']])
            text = bpy.data.texts.new(report['name'])
            text.write(report['content'])

    def _generate_texture_paths_report(self):
        """Generate texture paths report with resolution and relative/absolute paths"""
        lines = []
        lines.append("=" * 60)
        lines.append("📁 TEXTURE PATHS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")

        # Collect all images from bpy.data.images
        found_images = []
        missing_images = []
        packed_images = []
        linked_library_images = {} 

        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node'):
                continue
            if img.source == 'GENERATED':
                continue
            
            # Check if from linked library
            if img.library:
                lib_path = img.library.filepath
                if lib_path not in linked_library_images:
                    linked_library_images[lib_path] = []
                
                if img.filepath:
                    abs_path = bpy.path.abspath(img.filepath, library=img.library)
                    resolution = f"{img.size[0]}x{img.size[1]}" if img.size[0] > 0 else "Unknown"
                    
                    if img.filepath.startswith('//'):
                        display_path = img.filepath
                    else:
                        display_path = abs_path if os.path.exists(abs_path) else img.filepath
                    
                    linked_library_images[lib_path].append({
                        'name': img.name,
                        'path': display_path,
                        'resolution': resolution,
                        'exists': os.path.exists(abs_path) if abs_path else False
                    })
                continue
            
            # Check if packed
            if img.packed_file:
                resolution = f"{img.size[0]}x{img.size[1]}" if img.size[0] > 0 else "Unknown"
                packed_images.append({
                    'name': img.name,
                    'resolution': resolution
                })
                continue
            
            # Check file path
            if img.filepath:
                abs_path = bpy.path.abspath(img.filepath)
                rel_path = img.filepath
                resolution = f"{img.size[0]}x{img.size[1]}" if img.size[0] > 0 else "Unknown"
                
                if os.path.exists(abs_path):
                    if rel_path.startswith('//'):
                        display_path = rel_path
                    else:
                        display_path = abs_path
                    
                    # Get file size
                    try:
                        file_size = os.path.getsize(abs_path)
                        if file_size < 1024:
                            size_str = f"{file_size} B"
                        elif file_size < 1024 * 1024:
                            size_str = f"{file_size / 1024:.1f} KB"
                        else:
                            size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    except Exception:
                        size_str = "Unknown"
                    
                    found_images.append({
                        'path': display_path,
                        'resolution': resolution,
                        'size': size_str,
                        'is_relative': rel_path.startswith('//')
                    })
                else:
                    missing_images.append({
                        'path': rel_path,
                        'abs_path': abs_path
                    })

        # Scan textures folder for unused textures
        unused_textures = []
        if os.path.exists(textures_dir):
            used_files = set()
            for img in bpy.data.images:
                if img.source == 'FILE' and img.filepath:
                    abs_path = bpy.path.abspath(img.filepath)
                    if os.path.exists(abs_path):
                        used_files.add(os.path.normpath(abs_path))
            
            # Scan for image files
            image_extensions = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tiff', '.webp', '.exr', '.hdr', '.dds'}
            for root, dirs, files in os.walk(textures_dir):
                # Skip .backup folder
                if '.backup' in root:
                    continue
                for file in files:
                    file_lower = file.lower()
                    if any(file_lower.endswith(ext) for ext in image_extensions):
                        file_path = os.path.normpath(os.path.join(root, file))
                        if file_path not in used_files:
                            rel_from_textures = os.path.relpath(file_path, textures_dir)
                            
                            # Get file size
                            try:
                                file_size = os.path.getsize(file_path)
                                if file_size < 1024:
                                    size_str = f"{file_size} B"
                                elif file_size < 1024 * 1024:
                                    size_str = f"{file_size / 1024:.1f} KB"
                                else:
                                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                            except Exception:
                                size_str = "Unknown"
                            
                            unused_textures.append({
                                'path': rel_from_textures,
                                'size': size_str
                            })

        # Build report with statistics
        lines.append(f"Total Textures in Blend: {len(found_images) + len(missing_images) + len(packed_images)}")
        lines.append(f"Linked Library Textures: {sum(len(imgs) for imgs in linked_library_images.values())}")
        lines.append(f"Unused Textures in Folder: {len(unused_textures)}")
        lines.append("")
        
        # Found images
        if found_images:
            lines.append("[FOUND]")
            for img in sorted(found_images, key=lambda x: x['path']):
                lines.append(f"  • {img['path']} == ({img['resolution']}) [{img['size']}]")
            lines.append("")

        # Linked library textures
        if linked_library_images:
            lines.append("[LINKED LIBRARIES]")
            for lib_path, images in sorted(linked_library_images.items()):
                # Display library path
                if lib_path.startswith('//'):
                    lib_display = lib_path
                else:
                    lib_display = lib_path
                
                lines.append(f"Library: {lib_display}")
                
                if images:
                    lines.append(f"  Textures: {len(images)}")
                    for img_info in images:
                        status = "" if img_info['exists'] else " [MISSING]"
                        lines.append(f"    • {img_info['name']} ({img_info['resolution']}){status}")
                else:
                    lines.append("  No textures")
                
                lines.append("")

        # Missing images
        if missing_images:
            lines.append("[MISSING]")
            for img in sorted(missing_images, key=lambda x: x['path']):
                lines.append(f"  • ✗ {img['path']}")
                lines.append(f"    Expected: {img['abs_path']}")
            lines.append("")

        # Packed images
        if packed_images:
            lines.append("[PACKED]")
            for img in sorted(packed_images, key=lambda x: x['name']):
                lines.append(f"  • 📦 {img['name']} == ({img['resolution']})")
            lines.append("")

        # Unused textures in folder
        if unused_textures:
            lines.append("[UNUSED IN FOLDER /textures]")
            for tex in sorted(unused_textures, key=lambda x: x['path']):
                lines.append(f"  • {tex['path']} [{tex['size']}]")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _generate_data_usage_report(self):
        """Generate concise overview report with statistics and warnings"""
        lines = []
        lines.append("=" * 60)
        lines.append("SCENE DATA USAGE REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Count statistics
        total_objects = len([obj for obj in bpy.data.objects if obj.type == 'MESH'])
        total_materials = len(bpy.data.materials)
        total_textures = len([img for img in bpy.data.images 
                             if img.source == 'FILE' and img.name not in ('Render Result', 'Viewer Node')])

        lines.append(f"📊 STATISTICS:")
        lines.append(f"  • Total Objects: {total_objects}")
        lines.append(f"  • Total Materials: {total_materials}")
        lines.append(f"  • Total Textures: {total_textures}")
        lines.append("")

        # Analyze material and texture usage
        material_usage = {}
        texture_usage = {}
        
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                if slot.material:
                    mat = slot.material
                    if mat.name not in material_usage:
                        material_usage[mat.name] = []
                    if obj.name not in material_usage[mat.name]:
                        material_usage[mat.name].append(obj.name)
                    
                    # Get textures from material
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.image:
                                if node.image.name not in texture_usage:
                                    texture_usage[node.image.name] = []
                                if mat.name not in texture_usage[node.image.name]:
                                    texture_usage[node.image.name].append(mat.name)

        # Count orphans
        orphan_materials = [mat.name for mat in bpy.data.materials if mat.name not in material_usage]
        orphan_textures = [img.name for img in bpy.data.images 
                          if img.source == 'FILE' and img.name not in ('Render Result', 'Viewer Node') 
                          and img.name not in texture_usage]

        # Warnings section
        has_warnings = False
        if orphan_materials or orphan_textures:
            lines.append("⚠️  WARNINGS:")
            has_warnings = True
            
            if orphan_materials:
                lines.append(f"  • {len(orphan_materials)} materials not assigned to any object")
            if orphan_textures:
                lines.append(f"  • {len(orphan_textures)} textures not used in any material")
            lines.append("")

        # Linked libraries count
        linked_collections = {}
        for collection in bpy.data.collections:
            if collection.library:
                lib_path = collection.library.filepath
                if lib_path not in linked_collections:
                    linked_collections[lib_path] = []
                linked_collections[lib_path].append(collection.name)
        
        if linked_collections:
            if not has_warnings:
                lines.append("")
            lines.append(f"🔗 LINKED LIBRARIES:")
            lines.append(f"  • {len(linked_collections)} linked library file(s)")
            lines.append("")

        # Footer with references to detailed reports
        lines.append("-" * 60)
        lines.append("📋 DETAILED REPORTS AVAILABLE:")
        lines.append("  → Scene_MaterialUsage  (Material assignments per object)")
        lines.append("  → Scene_TextureUsage   (Texture usage per material)")
        lines.append("  → Scene_TexturePaths   (File paths and resolutions)")
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)

    def _generate_material_usage_report(self):
        """Generate material usage report with hybrid formatting"""
        lines = []
        lines.append("=" * 60)
        lines.append("📦 MATERIAL USAGE REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Collect material usage
        material_usage = {}
        
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                if slot.material:
                    mat = slot.material
                    if mat.name not in material_usage:
                        material_usage[mat.name] = []
                    if obj.name not in material_usage[mat.name]:
                        material_usage[mat.name].append(obj.name)

        # Count statistics
        total_materials = len(bpy.data.materials)
        used_materials = len(material_usage)
        orphan_materials = total_materials - used_materials

        lines.append(f"Total Materials: {total_materials}")
        lines.append(f"Used Materials: {used_materials}")
        if orphan_materials > 0:
            lines.append(f"Orphan Materials: {orphan_materials} ⚠️")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

        # Format material usage with hybrid approach
        for mat in sorted(bpy.data.materials, key=lambda x: x.name):
            if mat.name in material_usage:
                usage_list = sorted(material_usage[mat.name])
                lines.append(self._format_usage_hybrid(mat.name, usage_list, "objects", threshold=5, emoji="📦 "))
            else:
                lines.append(f"📦 {mat.name}: NOT ASSIGNED TO ANY OBJECT ⚠️")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _generate_texture_usage_report(self):
        """Generate texture usage report with hybrid formatting"""
        lines = []
        lines.append("=" * 60)
        lines.append("🖼️  TEXTURE USAGE REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Collect texture usage
        texture_usage = {}
        
        for mat in bpy.data.materials:
            if not mat.use_nodes or not mat.node_tree:
                continue
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    img_name = node.image.name
                    if img_name not in texture_usage:
                        texture_usage[img_name] = []
                    if mat.name not in texture_usage[img_name]:
                        texture_usage[img_name].append(mat.name)

        # Count statistics
        all_textures = [img for img in bpy.data.images 
                       if img.source == 'FILE' and img.name not in ('Render Result', 'Viewer Node')]
        total_textures = len(all_textures)
        used_textures = len(texture_usage)
        orphan_textures = total_textures - used_textures

        lines.append(f"Total Textures: {total_textures}")
        lines.append(f"Used Textures: {used_textures}")
        if orphan_textures > 0:
            lines.append(f"Orphan Textures: {orphan_textures} ⚠️")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

        # Format texture usage with hybrid approach
        for img in sorted(all_textures, key=lambda x: x.name):
            if img.name in texture_usage:
                usage_list = sorted(texture_usage[img.name])
                lines.append(self._format_usage_hybrid(img.name, usage_list, "materials", threshold=5, emoji="🖼️  "))
            else:
                lines.append(f"🖼️  {img.name}: NOT USED IN ANY MATERIAL ⚠️")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _format_usage_hybrid(self, item_name, usage_list, category="items", threshold=5, emoji=""):
        """
        Smart hybrid formatting based on list length
        
        Args:
            item_name: Name of the item (material/texture)
            usage_list: List of items using this resource
            category: Category name for display (objects/materials)
            threshold: Max items for horizontal format (default: 5)
            emoji: Emoji prefix for the item (e.g., 📦 for materials, 🖼️ for textures)
        
        Returns:
            Formatted string with hybrid layout
        """
        count = len(usage_list)
        
        # Horizontal format for items ≤ threshold
        if count <= threshold:
            items_str = ", ".join(usage_list)
            return f"{emoji}{item_name}: Used by {count} {category} [{items_str}]"
        
        # Vertical format for items > threshold
        lines = [f"{emoji}{item_name}: Used by {count} {category}"]
        for i, item in enumerate(usage_list):
            if i < count - 1:
                lines.append(f"  ├─ {item}")
            else:
                lines.append(f"  └─ {item}")
        
        return "\n".join(lines)

    def _generate_material_usage_report_old(self):
        """Generate material usage report with linked library collections - OLD VERSION"""
        lines = []
        lines.append("=" * 60)
        lines.append("SCENE DATA USAGE REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Count statistics (for full report)
        total_objects = len([obj for obj in bpy.data.objects if obj.type == 'MESH'])
        total_materials = len(bpy.data.materials)
        total_textures = len([img for img in bpy.data.images 
                             if img.source == 'FILE' and img.name not in ('Render Result', 'Viewer Node')])

        lines.append(f"Total Objects: {total_objects}")
        lines.append(f"Total Materials: {total_materials}")
        lines.append(f"Total Textures: {total_textures}")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

        # Track material usage
        material_usage = {}  
        texture_usage = {}   

        mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        
        for obj in sorted(mesh_objects, key=lambda x: x.name):
            if obj.data:
                vert_count = len(obj.data.vertices)
                if vert_count >= 1000:
                    vert_str = f"{vert_count / 1000:.1f}K"
                else:
                    vert_str = str(vert_count)
            else:
                vert_str = "0"
            
            mat_count = len([slot for slot in obj.material_slots if slot.material])
            
            lines.append(f"OBJECT: {obj.name} [{vert_str} verts] [{mat_count} material(s)]")
            
            if not obj.material_slots:
                lines.append("  └─ NO MATERIAL ASSIGNED")
                lines.append("")
                continue
            
            for slot in obj.material_slots:
                mat = slot.material
                if not mat:
                    continue
                
                if mat.name not in material_usage:
                    material_usage[mat.name] = []
                material_usage[mat.name].append(obj.name)
                
                lines.append(f"  └─ MATERIAL: {mat.name}")
                
                textures = self._get_textures_from_material(mat)
                
                if textures:
                    for i, tex_name in enumerate(sorted(textures)):
                        prefix = "├─" if i < len(textures) - 1 else "└─"
                        lines.append(f"       {prefix} {tex_name}")
                        
                        if tex_name not in texture_usage:
                            texture_usage[tex_name] = []
                        if mat.name not in texture_usage[tex_name]:
                            texture_usage[tex_name].append(mat.name)
                else:
                    lines.append(f"       └─ No textures")
                
                lines.append("")

        # Material summary
        lines.append("-" * 60)
        lines.append("MATERIAL SUMMARY:")
        lines.append("")
        
        for mat in bpy.data.materials:
            if mat.name in material_usage:
                obj_list = ", ".join(material_usage[mat.name])
                lines.append(f"  • {mat.name}: Used by {len(material_usage[mat.name])} object(s) ({obj_list})")
            else:
                lines.append(f"  • {mat.name}: NOT ASSIGNED TO ANY OBJECT ⚠️")
        
        lines.append("")

        # Texture summary
        lines.append("TEXTURE SUMMARY:")
        lines.append("")
        
        for img in bpy.data.images:
            if img.name in ('Render Result', 'Viewer Node') or img.source != 'FILE':
                continue
            
            if img.name in texture_usage:
                mat_list = ", ".join(texture_usage[img.name])
                lines.append(f"  • {img.name}: Used in {len(texture_usage[img.name])} material(s) ({mat_list})")
            else:
                lines.append(f"  • {img.name}: NOT USED IN ANY MATERIAL ⚠️")

        lines.append("")
        lines.append("-" * 60)
        
        # Linked Libraries Section (at bottom)
        linked_collections = {}
        for collection in bpy.data.collections:
            if collection.library:
                lib_path = collection.library.filepath
                if lib_path not in linked_collections:
                    linked_collections[lib_path] = []
                linked_collections[lib_path].append(collection.name)
        
        if linked_collections:
            lines.append("[LINKED LIBRARIES]")
            lines.append("")
            
            for lib_path, collections in sorted(linked_collections.items()):
                # Display library path
                if lib_path.startswith('//'):
                    lib_display = lib_path
                else:
                    lib_display = lib_path
                
                # Use first collection name as library display name
                lib_name = collections[0] if collections else "Unknown"
                
                lines.append(f"Library: {lib_name}")
                lines.append(f"    └─ {lib_display}")
                lines.append("")  # Empty line between libraries
        
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _get_textures_from_material(self, material):
        """Extract texture names from material node tree"""
        textures = []
        
        if not material.use_nodes or not material.node_tree:
            return textures
        
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                textures.append(node.image.name)
        
        return textures

    def _create_text_datablock(self, name, content):
        """Create or update text datablock in Text Editor"""
        if name in bpy.data.texts:
            bpy.data.texts.remove(bpy.data.texts[name])
        
        text = bpy.data.texts.new(name)
        text.write(content)


class SCENE_OT_ShowAnalysisResult(bpy.types.Operator):
    """Show scene analysis result dialog"""
    bl_idname = "scene.show_analysis_result"
    bl_label = "Scene Analysis Complete"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def execute(self, context):
        return {'FINISHED'}
    
    def draw(self, context):
        """Draw dialog with report preview and switch button"""
        layout = self.layout
        
        # Header
        box = layout.box()
        box.label(text="✅ Scene Analysis Complete", icon='CHECKMARK')
        
        layout.separator()
        
        # Preview Scene_MaterialUsage Report
        if "Scene_MaterialUsage" in bpy.data.texts:
            mat_report = bpy.data.texts["Scene_MaterialUsage"]
            content = mat_report.as_string()
            lines = content.split('\n')
            
            box = layout.box()
            box.label(text="📦 Scene_MaterialUsage Report:", icon='MATERIAL')
            
            col = box.column(align=True)
            col.scale_y = 0.7
            
            # Skip header and show first few materials
            preview_count = 0
            start_showing = False
            skipped_lines = 0
            
            for i, line in enumerate(lines):
                if not start_showing:
                    if line.startswith("-" * 10):  # Divider after stats
                        start_showing = True
                        skipped_lines = i + 2
                    continue
                
                if preview_count < 10:
                    col.label(text=line)
                    preview_count += 1
                else:
                    break
            
            # Show "more lines" indicator
            if len(lines) - skipped_lines > 10:
                remaining = len(lines) - skipped_lines - 10
                box.separator()
                row = box.row()
                row.label(text=f"... {remaining} more lines", icon='THREE_DOTS')
        
        layout.separator()
        
        # Preview Scene_TextureUsage Report
        if "Scene_TextureUsage" in bpy.data.texts:
            tex_usage_report = bpy.data.texts["Scene_TextureUsage"]
            content = tex_usage_report.as_string()
            lines = content.split('\n')
            
            box = layout.box()
            box.label(text="🖼️  Scene_TextureUsage Report:", icon='TEXTURE')
            
            col = box.column(align=True)
            col.scale_y = 0.7
            
            # Skip header and show first few textures
            preview_count = 0
            start_showing = False
            skipped_lines = 0
            
            for i, line in enumerate(lines):
                if not start_showing:
                    if line.startswith("-" * 10):  # Divider after stats
                        start_showing = True
                        skipped_lines = i + 2
                    continue
                
                if preview_count < 10:
                    col.label(text=line)
                    preview_count += 1
                else:
                    break
            
            # Show "more lines" indicator
            if len(lines) - skipped_lines > 10:
                remaining = len(lines) - skipped_lines - 10
                box.separator()
                row = box.row()
                row.label(text=f"... {remaining} more lines", icon='THREE_DOTS')
        
        layout.separator()
        
        # Preview Scene_TexturePaths Report
        if "Scene_TexturePaths" in bpy.data.texts:
            texture_report = bpy.data.texts["Scene_TexturePaths"]
            content = texture_report.as_string()
            lines = content.split('\n')
            
            box = layout.box()
            box.label(text="� Scene_TexturePaths Report:", icon='FILE_IMAGE')
            
            col = box.column(align=True)
            col.scale_y = 0.7
            
            # Skip stats and show first section
            preview_count = 0
            start_showing = False
            skipped_lines = 0
            
            for i, line in enumerate(lines):
                if not start_showing:
                    if line.startswith("[FOUND]") or line.startswith("[LINKED") or line.startswith("[MISSING]"):
                        start_showing = True
                        skipped_lines = i
                    else:
                        continue
                
                if preview_count < 10:
                    col.label(text=line)
                    preview_count += 1
                else:
                    break
            
            # Show "more lines" indicator
            if len(lines) - skipped_lines > 10:
                remaining = len(lines) - skipped_lines - 10
                box.separator()
                row = box.row()
                row.label(text=f"... {remaining} more lines", icon='THREE_DOTS')
        
        layout.separator()
        
        # Info message - how to access full reports
        info_box = layout.box()
        info_col = info_box.column(align=True)
        info_col.scale_y = 0.8
        info_col.label(text="📝 Full reports saved in Text Editor:", icon='INFO')
        info_col.label(text="    • Scene_MaterialUsage (Material assignments)", icon='BLANK1')
        info_col.label(text="    • Scene_TextureUsage (Texture usage)", icon='BLANK1')
        info_col.label(text="    • Scene_TexturePaths (File paths)", icon='BLANK1')
        info_col.label(text="Open Scripting workspace to view full reports", icon='BLANK1')


def register():
    bpy.utils.register_class(SCENE_OT_AnalyzeSceneDeep)
    bpy.utils.register_class(SCENE_OT_ShowAnalysisResult)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_ShowAnalysisResult)
    bpy.utils.unregister_class(SCENE_OT_AnalyzeSceneDeep)

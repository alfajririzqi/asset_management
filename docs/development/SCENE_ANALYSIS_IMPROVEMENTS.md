# Scene Analysis - Improvement Discussion

## 📋 Issues & Solutions

### ✅ 1. Text Editor Not Loading (FIXED)

**Problem:**
- Text Editor tidak load Scene_DataUsage setelah switch ke Scripting workspace
- Blender naming: Text baru di Text Editor biasa pakai prefix "F" (e.g., "F Scene_DataUsage")

**Solution Implemented:**
```python
# Double-check logic:
1. Switch workspace → delay 0.05s
2. Loop semua areas, cari TEXT_EDITOR type
3. Loop semua spaces dalam area tersebut
4. Set space.text = data_usage_text
5. Fallback: Loop semua spaces di semua areas (jika Text Editor ada tapi hidden)
```

**Note:** Blender text datablock naming ("F Scene_DataUsage") adalah internal display saja. `bpy.data.texts["Scene_DataUsage"]` tetap bekerja correct.

---

### 🔧 2. Check Analysis - Force Solid Viewport Mode

**Current Issue:**
User mungkin dalam **Material Preview**, **Rendered**, atau **Wireframe** mode saat run check → Analysis jadi tidak akurat.

**Proposed Solution:**
```python
# In check_highpoly.py and check_transform.py

def execute(self, context):
    # Store original shading mode
    original_shading = {}
    
    # Force all 3D viewports to SOLID mode
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Store original
                    original_shading[area] = space.shading.type
                    
                    # Switch to SOLID
                    space.shading.type = 'SOLID'
    
    # ... run analysis ...
    
    # Restore original shading (optional - user might prefer staying in SOLID)
    # for area, shading_type in original_shading.items():
    #     for space in area.spaces:
    #         if space.type == 'VIEW_3D':
    #             space.shading.type = shading_type
    
    return {'FINISHED'}
```

**Question for You:**
- **Restore shading setelah check?** Atau biarkan di SOLID mode agar user aware?
- **Show warning** jika user di mode selain SOLID? ("Switched to Solid mode for accurate analysis")

**Implementation Priority:** ⭐⭐⭐⭐⭐ (High - affects accuracy)

---

### ⚠️ 3. Apply Transform - Modifier Safety Check

**Critical Issue:**
Apply Transform pada object dengan **sensitive modifiers** bisa **destroy geometry**!

#### Dangerous Modifiers (DON'T apply transform):
```python
DANGEROUS_MODIFIERS = {
    'MIRROR',       # ⚠️ Mirror axis akan berubah
    'ARRAY',        # ⚠️ Array offset calculation rusak
    'BEVEL',        # ⚠️ Bevel width calculation berubah
    'SOLIDIFY',     # ⚠️ Thickness calculation rusak
    'SCREW',        # ⚠️ Rotation axis berubah
    'LATTICE',      # ⚠️ Lattice deformation rusak
    'ARMATURE',     # ⚠️ Bone relationship rusak (VERY DANGEROUS!)
    'CURVE',        # ⚠️ Curve deformation rusak
    'SHRINKWRAP',   # ⚠️ Target offset rusak
    'SIMPLE_DEFORM',# ⚠️ Deform axis berubah
}
```

#### Safe Modifiers (OK to apply transform):
```python
SAFE_MODIFIERS = {
    'SUBSURF',          # ✅ Subdivision - Safe
    'MULTIRES',         # ✅ Multi-resolution - Safe
    'TRIANGULATE',      # ✅ Triangulate - Safe
    'DECIMATE',         # ✅ Decimate - Safe
    'SMOOTH',           # ✅ Smooth - Safe
    'CORRECTIVE_SMOOTH',# ✅ Safe
    'WELD',             # ✅ Safe
    'WEIGHTED_NORMAL',  # ✅ Safe
}
```

#### Proposed Implementation:

**Option A: Block Apply (Conservative)**
```python
def check_transform_safety(obj):
    """Check if object is safe for apply transform"""
    dangerous_mods = []
    
    for mod in obj.modifiers:
        if mod.type in DANGEROUS_MODIFIERS:
            dangerous_mods.append((mod.name, mod.type))
    
    return dangerous_mods

# In check_transform.py execute():
for obj in problematic_objects:
    dangerous_mods = check_transform_safety(obj)
    
    if dangerous_mods:
        # DON'T auto-apply, show warning
        mod_list = ", ".join([f"{name} ({type})" for name, type in dangerous_mods])
        warnings.append(
            f"⚠️ {obj.name}: Has sensitive modifiers ({mod_list}). "
            f"Apply transform MANUALLY with caution!"
        )
    else:
        # Safe to apply
        safe_objects.append(obj)
```

**Option B: User Confirmation (Advanced)**
```python
# Show dialog with list of objects + their modifiers
# User can:
# - Check/uncheck objects to apply
# - See modifier warnings
# - Apply selectively

class TRANSFORM_OT_ApplyWithModifierCheck(bpy.types.Operator):
    """Apply transform with modifier safety check"""
    
    objects_to_apply: bpy.props.CollectionProperty(type=ObjectItem)
    
    def invoke(self, context, event):
        # Build list with safety info
        for obj in problematic_objects:
            dangerous_mods = check_transform_safety(obj)
            item = self.objects_to_apply.add()
            item.obj = obj
            item.is_safe = len(dangerous_mods) == 0
            item.modifier_info = str(dangerous_mods)
        
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        
        for item in self.objects_to_apply:
            row = layout.row()
            
            if item.is_safe:
                row.prop(item, "apply", text=f"✅ {item.obj.name}")
            else:
                row.alert = True
                row.prop(item, "apply", text=f"⚠️ {item.obj.name}")
                row.label(text=item.modifier_info, icon='ERROR')
```

**Recommendation:** **Option A** (Conservative Block)
- Safer untuk user
- Prevent data loss
- Clear warnings
- User bisa manual apply jika mereka paham risikonya

**Question for You:**
1. **Option A atau B?** Block automatic apply atau kasih user pilihan?
2. **Add "Force Apply" checkbox?** Dengan warning "May destroy geometry"?
3. **Armature modifier:** TOTAL BLOCK atau warning saja? (Armature + apply transform = disaster!)

**Implementation Priority:** ⭐⭐⭐⭐⭐ (Critical - prevent data loss!)

---

### 💡 4. Interactive Selection Buttons in Preview Dialog

**Your Question:**
> Apakah memungkinkan di popup dialog preview ada button untuk select material/object?
> Apakah coding semakin rumit?

**Answer:** ✅ **MEMUNGKINKAN**, tapi ada **trade-offs**.

#### Complexity Level: ⭐⭐⭐ (Medium)

#### Example Implementation:

```python
class SCENE_OT_SelectObject(bpy.types.Operator):
    """Select specific object from report"""
    bl_idname = "scene.select_object"
    bl_label = "Select Object"
    bl_options = {'REGISTER', 'UNDO'}
    
    object_name: bpy.props.StringProperty()
    
    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        
        if obj:
            # Deselect all
            bpy.ops.object.select_all(action='DESELECT')
            
            # Select object
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
            # Frame object in view
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            override = context.copy()
                            override['area'] = area
                            override['region'] = region
                            bpy.ops.view3d.view_selected(override)
                            break
            
            self.report({'INFO'}, f"Selected: {obj.name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Object not found: {self.object_name}")
            return {'CANCELLED'}


class SCENE_OT_SelectMaterial(bpy.types.Operator):
    """Select all objects using specific material"""
    bl_idname = "scene.select_material"
    bl_label = "Select Objects with Material"
    bl_options = {'REGISTER', 'UNDO'}
    
    material_name: bpy.props.StringProperty()
    
    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        
        if not mat:
            self.report({'ERROR'}, f"Material not found: {self.material_name}")
            return {'CANCELLED'}
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select objects with this material
        selected_count = 0
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material == mat:
                        obj.select_set(True)
                        selected_count += 1
                        break
        
        if selected_count > 0:
            self.report({'INFO'}, f"Selected {selected_count} object(s) using '{mat.name}'")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"No objects found using '{mat.name}'")
            return {'CANCELLED'}
```

#### UI Integration in Dialog:

```python
# In SCENE_OT_ShowAnalysisResult.draw():

def draw(self, context):
    layout = self.layout
    
    # ... existing preview code ...
    
    # Parse report and add selection buttons
    if "Scene_DataUsage" in bpy.data.texts:
        content = bpy.data.texts["Scene_DataUsage"].as_string()
        lines = content.split('\n')
        
        for line in lines:
            # Detect object line
            if line.startswith("OBJECT:"):
                # Extract object name
                obj_name = line.split("OBJECT:")[1].split("[")[0].strip()
                
                row = layout.row()
                row.scale_y = 0.7
                
                # Object name label (70% width)
                row.label(text=line, icon='OBJECT_DATA')
                
                # Select button (30% width)
                op = row.operator("scene.select_object", text="", icon='RESTRICT_SELECT_OFF')
                op.object_name = obj_name
            
            # Detect material line
            elif "MATERIAL:" in line:
                mat_name = line.split("MATERIAL:")[1].strip()
                
                row = layout.row()
                row.scale_y = 0.7
                
                # Material name label
                row.label(text=line, icon='MATERIAL')
                
                # Select button
                op = row.operator("scene.select_material", text="", icon='RESTRICT_SELECT_OFF')
                op.material_name = mat_name
            
            else:
                # Regular line
                layout.label(text=line)
```

#### Pros & Cons:

**✅ Advantages:**
1. **User-friendly** - Quick selection dari preview
2. **Workflow efficient** - No need manual search
3. **Visual feedback** - Frame selected object in viewport
4. **Multi-material selection** - Select all objects using material

**❌ Disadvantages:**
1. **Dialog complexity** - More parsing logic needed
2. **Dialog height** - Buttons add vertical space (might be too tall)
3. **Performance** - Parsing report multiple times
4. **Maintenance** - Need to sync button logic with report format

#### Alternative: Simpler Approach

Instead of **per-item buttons**, add **global action buttons** at bottom:

```python
def draw(self, context):
    # ... preview report ...
    
    layout.separator()
    
    # Global action buttons
    row = layout.row(align=True)
    row.operator("scene.select_all_analyzed_objects", text="Select All Objects", icon='OBJECT_DATA')
    row.operator("scene.select_problematic_only", text="Select Problematic Only", icon='ERROR')
    
    row = layout.row(align=True)
    row.operator("scene.highlight_unused_materials", text="Highlight Unused Materials", icon='MATERIAL')
    row.operator("scene.highlight_missing_textures", text="Highlight Missing Textures", icon='TEXTURE')
```

**This is simpler** and **less cluttered**.

#### My Recommendation:

**Phase 1 (Current):** Focus on **fix critical issues** (shading mode, modifier safety)

**Phase 2 (Future):** Add **global selection buttons** at bottom of dialog
- "Select All Analyzed Objects"
- "Select Objects with Warnings"
- "Highlight Unused Materials"

**Phase 3 (Optional):** Add **per-item buttons** if users request it

**Coding Complexity:**
- Global buttons: ⭐⭐ (Easy)
- Per-item buttons: ⭐⭐⭐⭐ (Medium-Hard, needs parsing)

---

## 🎯 Priority Roadmap

### High Priority (Must Fix):
1. ✅ **Text Editor loading** (DONE)
2. ⭐⭐⭐⭐⭐ **Modifier safety check** (CRITICAL - prevent data loss!)
3. ⭐⭐⭐⭐⭐ **Auto-switch to Solid mode** (Affects accuracy)

### Medium Priority (Nice to Have):
4. ⭐⭐⭐ **Global selection buttons** in dialog
5. ⭐⭐ **Better warning messages** for dangerous operations

### Low Priority (Future):
6. ⭐ **Per-item selection buttons** (if requested by users)
7. ⭐ **Advanced modifier detection** (edge cases)

---

## ❓ Questions for Discussion:

### For Issue #2 (Viewport Shading):
- [ ] Restore shading after check? Or keep in SOLID mode?
- [ ] Show warning message when switching? ("Switched to Solid mode for analysis")

### For Issue #3 (Modifier Safety):
- [ ] Option A (Block auto-apply) or Option B (User confirmation dialog)?
- [ ] Add "Force Apply" checkbox with warning?
- [ ] Should Armature modifier be TOTAL BLOCK or just warning?
- [ ] What about Curve modifier? Also dangerous?

### For Issue #4 (Selection Buttons):
- [ ] Global buttons atau per-item buttons?
- [ ] Implement now atau nanti after critical fixes?
- [ ] What actions most useful? (Select objects? Highlight materials? Frame in view?)

---

**Next Steps:**
1. You decide on questions above
2. I implement priority fixes (modifier safety + shading mode)
3. Test in production
4. Iterate based on feedback

Let's discuss! 🚀

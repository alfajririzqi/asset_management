# Scene Analysis Dialog - Selection Buttons Concept

## 🎯 Goal
Add **selection buttons** in Scene Analysis dialog popup untuk select objects/materials/textures berdasarkan report data.

---

## 📊 Current Dialog Structure

```
┌─────────────────────────────────────────────────────┐
│ ✅ Scene Analysis Complete                          │
├─────────────────────────────────────────────────────┤
│ 📄 Scene_DataUsage Report:                         │
│   [FOUND IN SCENE]                                  │
│   Collection: Props                                 │
│     • Chair (Mesh) - 2 materials                   │
│     • Table (Mesh) - 1 materials                   │
│   ...                                               │
│   ... 150 more lines                                │
├─────────────────────────────────────────────────────┤
│ 📄 Scene_TexturePaths Report:                      │
│   [FOUND] 15 textures in /textures                 │
│     • wood_diffuse.png (2K)                        │
│     • metal_normal.png (4K)                        │
│   ...                                               │
│   ... 80 more lines                                 │
├─────────────────────────────────────────────────────┤
│ [Switch to Scripting Workspace]                    │
└─────────────────────────────────────────────────────┘
```

---

## 🆕 Proposed Enhancement

### **Option A: Selection Buttons Below Each Report**

```
┌─────────────────────────────────────────────────────┐
│ ✅ Scene Analysis Complete                          │
├─────────────────────────────────────────────────────┤
│ 📄 Scene_DataUsage Report:                         │
│   [FOUND IN SCENE]                                  │
│   Collection: Props                                 │
│     • Chair (Mesh) - 2 materials                   │
│     • Table (Mesh) - 1 materials                   │
│   ... 150 more lines                                │
│                                                     │
│   [Select All Objects] [Select All Materials] ← NEW │
├─────────────────────────────────────────────────────┤
│ 📄 Scene_TexturePaths Report:                      │
│   [FOUND] 15 textures in /textures                 │
│     • wood_diffuse.png (2K)                        │
│     • metal_normal.png (4K)                        │
│   ... 80 more lines                                 │
│                                                     │
│   [Select All Textures] ← NEW                      │
├─────────────────────────────────────────────────────┤
│ [Switch to Scripting Workspace]                    │
└─────────────────────────────────────────────────────┘
```

### **Option B: Action Bar at Bottom**

```
┌─────────────────────────────────────────────────────┐
│ ✅ Scene Analysis Complete                          │
├─────────────────────────────────────────────────────┤
│ [Report previews...]                                │
├─────────────────────────────────────────────────────┤
│ QUICK ACTIONS:                                      │
│ [Select Objects] [Select Materials] [Select Images] │ ← NEW
├─────────────────────────────────────────────────────┤
│ [Switch to Scripting Workspace]                    │
└─────────────────────────────────────────────────────┘
```

### **Option C: Expandable Actions**

```
┌─────────────────────────────────────────────────────┐
│ ✅ Scene Analysis Complete                          │
├─────────────────────────────────────────────────────┤
│ [Report previews...]                                │
├─────────────────────────────────────────────────────┤
│ ▼ Quick Actions                                     │ ← Collapsible
│   [Select All Objects (12)]                         │
│   [Select All Materials (8)]                        │
│   [Select All Images (15)]                          │
│   [Select Missing Textures (3)]                     │
├─────────────────────────────────────────────────────┤
│ [Switch to Scripting Workspace]                    │
└─────────────────────────────────────────────────────┘
```

---

## 💻 Implementation Approach

### **Challenge: Dialog Context Limitation**

Blender dialog operators run in **modal context** yang tidak punya direct access ke scene data untuk selection operations.

**Problem:**
```python
class SCENE_OT_ShowAnalysisResult(bpy.types.Operator):
    def draw(self, context):
        # This is DRAW context, not EXECUTE context
        # Cannot directly select objects here
        layout.operator("scene.select_objects")  # ← Needs to work in dialog context
```

### **Solution 1: Store Analysis Data in Scene Properties**

```python
# In SCENE_OT_AnalyzeSceneDeep.execute()
def execute(self, context):
    # ... analysis code ...
    
    # Store object names for later selection
    object_names = [obj.name for obj in scene_objects]
    context.scene.analysis_objects = str(object_names)  # Store as JSON string
    
    # Store material names
    material_names = [mat.name for mat in materials_found]
    context.scene.analysis_materials = str(material_names)
    
    # Store texture names
    texture_names = [img.name for img in images_found]
    context.scene.analysis_textures = str(texture_names)
```

### **Solution 2: Create Selection Operators**

```python
class SCENE_OT_SelectAnalyzedObjects(bpy.types.Operator):
    """Select all objects found in scene analysis"""
    bl_idname = "scene.select_analyzed_objects"
    bl_label = "Select All Objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Parse stored data
        import ast
        object_names = ast.literal_eval(context.scene.analysis_objects)
        
        # Select objects
        bpy.ops.object.select_all(action='DESELECT')
        selected_count = 0
        
        for obj_name in object_names:
            obj = bpy.data.objects.get(obj_name)
            if obj and obj.name in context.view_layer.objects:
                obj.select_set(True)
                selected_count += 1
        
        self.report({'INFO'}, f"Selected {selected_count} objects from analysis")
        return {'FINISHED'}


class SCENE_OT_SelectAnalyzedMaterials(bpy.types.Operator):
    """Select objects using analyzed materials"""
    bl_idname = "scene.select_analyzed_materials"
    bl_label = "Select All Materials"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        import ast
        material_names = ast.literal_eval(context.scene.analysis_materials)
        
        # Select objects that use these materials
        bpy.ops.object.select_all(action='DESELECT')
        selected_count = 0
        
        for obj in context.view_layer.objects:
            if obj.type == 'MESH':
                for mat_slot in obj.material_slots:
                    if mat_slot.material and mat_slot.material.name in material_names:
                        obj.select_set(True)
                        selected_count += 1
                        break
        
        self.report({'INFO'}, f"Selected {selected_count} objects with analyzed materials")
        return {'FINISHED'}


class SCENE_OT_SelectAnalyzedTextures(bpy.types.Operator):
    """Open Image Editor and select first analyzed texture"""
    bl_idname = "scene.select_analyzed_textures"
    bl_label = "Select All Textures"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        import ast
        texture_names = ast.literal_eval(context.scene.analysis_textures)
        
        if not texture_names:
            self.report({'WARNING'}, "No textures found in analysis")
            return {'CANCELLED'}
        
        # Find Image Editor area and set first texture
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                for space in area.spaces:
                    if space.type == 'IMAGE_EDITOR':
                        first_texture = bpy.data.images.get(texture_names[0])
                        if first_texture:
                            space.image = first_texture
                            self.report({'INFO'}, f"Opened {first_texture.name} in Image Editor")
                            return {'FINISHED'}
        
        self.report({'WARNING'}, "No Image Editor found. Open Image Editor first.")
        return {'CANCELLED'}
```

### **Solution 3: Update Dialog Draw Method**

```python
class SCENE_OT_ShowAnalysisResult(bpy.types.Operator):
    def draw(self, context):
        layout = self.layout
        
        # ... existing report previews ...
        
        # NEW: Quick Actions section
        layout.separator()
        
        box = layout.box()
        box.label(text="QUICK ACTIONS:", icon='SETTINGS')
        
        # Check if we have stored analysis data
        has_objects = hasattr(context.scene, 'analysis_objects') and context.scene.analysis_objects
        has_materials = hasattr(context.scene, 'analysis_materials') and context.scene.analysis_materials
        has_textures = hasattr(context.scene, 'analysis_textures') and context.scene.analysis_textures
        
        # Action buttons
        row = box.row(align=True)
        
        # Select Objects button
        btn = row.operator("scene.select_analyzed_objects", text="Select Objects", icon='OBJECT_DATA')
        btn.enabled = has_objects
        
        # Select Materials button
        btn = row.operator("scene.select_analyzed_materials", text="Select Materials", icon='MATERIAL')
        btn.enabled = has_materials
        
        # Select Textures button
        btn = row.operator("scene.select_analyzed_textures", text="Open Textures", icon='IMAGE_DATA')
        btn.enabled = has_textures
        
        layout.separator()
        
        # Existing workspace switch button
        layout.operator("scene.open_text_editor_area", text="Switch to Scripting Workspace", icon='WORKSPACE')
```

---

## 📋 Scene Properties Registration

```python
def register():
    bpy.utils.register_class(SCENE_OT_AnalyzeSceneDeep)
    bpy.utils.register_class(SCENE_OT_ShowAnalysisResult)
    bpy.utils.register_class(SCENE_OT_OpenTextEditorArea)
    
    # NEW: Register selection operators
    bpy.utils.register_class(SCENE_OT_SelectAnalyzedObjects)
    bpy.utils.register_class(SCENE_OT_SelectAnalyzedMaterials)
    bpy.utils.register_class(SCENE_OT_SelectAnalyzedTextures)
    
    # NEW: Scene properties for storing analysis data
    bpy.types.Scene.analysis_objects = bpy.props.StringProperty(default="")
    bpy.types.Scene.analysis_materials = bpy.props.StringProperty(default="")
    bpy.types.Scene.analysis_textures = bpy.props.StringProperty(default="")


def unregister():
    # Clean up properties
    if hasattr(bpy.types.Scene, "analysis_textures"):
        del bpy.types.Scene.analysis_textures
    if hasattr(bpy.types.Scene, "analysis_materials"):
        del bpy.types.Scene.analysis_materials
    if hasattr(bpy.types.Scene, "analysis_objects"):
        del bpy.types.Scene.analysis_objects
    
    bpy.utils.unregister_class(SCENE_OT_SelectAnalyzedTextures)
    bpy.utils.unregister_class(SCENE_OT_SelectAnalyzedMaterials)
    bpy.utils.unregister_class(SCENE_OT_SelectAnalyzedObjects)
    
    # ... existing unregister ...
```

---

## 🎨 Visual Mockup (Final Result)

```
┌─────────────────────────────────────────────────────────┐
│ ✅ Scene Analysis Complete                              │
├─────────────────────────────────────────────────────────┤
│ 📄 Scene_DataUsage Report:                             │
│   [FOUND IN SCENE]                                      │
│   Collection: Props                                     │
│     • Chair (Mesh) - 2 materials                       │
│     • Table (Mesh) - 1 materials                       │
│   ... 150 more lines                                    │
├─────────────────────────────────────────────────────────┤
│ 📄 Scene_TexturePaths Report:                          │
│   [FOUND] 15 textures in /textures                     │
│     • wood_diffuse.png (2K)                            │
│     • metal_normal.png (4K)                            │
│   ... 80 more lines                                     │
├─────────────────────────────────────────────────────────┤
│ QUICK ACTIONS:                                          │
│ [Select Objects (12)] [Select Materials (8)] [Open Textures (15)] │
├─────────────────────────────────────────────────────────┤
│ [Switch to Scripting Workspace]                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Workflow

### User Scenario:
1. Run "Analyze Scene Deeply"
2. Progress bar completes → Dialog appears
3. User sees report preview in dialog
4. User clicks **"Select Objects"** → All analyzed objects selected in viewport
5. User clicks **"Select Materials"** → All objects using analyzed materials selected
6. User clicks **"Open Textures"** → First texture loaded in Image Editor
7. User clicks **"Switch to Scripting Workspace"** → Full report visible

---

## 🔧 Complexity Analysis

| Feature | Complexity | Benefit |
|---------|-----------|---------|
| **Store analysis data in scene props** | Low | Essential for selection |
| **Select Objects operator** | Low | Direct object.select_set() |
| **Select Materials operator** | Medium | Need to find objects using materials |
| **Open Textures operator** | Medium | Need to switch to Image Editor |
| **UI Integration** | Low | Just add buttons to draw() |

**Total Implementation Time:** ~2-3 hours

---

## 📝 Recommendations

### **Phase 1 (Immediate):**
- ✅ Store object/material/texture names in scene properties
- ✅ Create "Select Objects" operator (easiest)
- ✅ Add button to dialog

### **Phase 2 (Next):**
- ✅ Create "Select Materials" operator
- ✅ Create "Open Textures" operator
- ✅ Add counts to buttons: "Select Objects (12)"

### **Phase 3 (Optional):**
- ⏳ Category-specific selection (e.g., "Select Props", "Select Lights")
- ⏳ "Select Missing Textures" button
- ⏳ "Select High-Poly Objects" integration

---

## ⚠️ Potential Issues & Solutions

### Issue 1: Dialog Closes After Button Click
**Problem:** Clicking operator button in dialog closes dialog immediately

**Solution:** Use `INVOKE_DEFAULT` in button call:
```python
# In draw() method
row.operator("scene.select_analyzed_objects", text="Select Objects")
# Button executes operator, dialog stays open until user clicks OK/Cancel
```

### Issue 2: Large Data Stored in Scene
**Problem:** Storing 1000+ object names in StringProperty

**Solution:** 
- Option A: Use JSON compression
- Option B: Store only counts, reconstruct list on-demand
- Option C: Use temporary text datablock instead of scene property

### Issue 3: Outdated Data After Re-Analysis
**Problem:** Old selection data persists if user runs analysis multiple times

**Solution:** Clear properties at start of analysis:
```python
def execute(self, context):
    # Clear old data first
    context.scene.analysis_objects = ""
    context.scene.analysis_materials = ""
    context.scene.analysis_textures = ""
    
    # ... run analysis ...
```

---

**Status:** 📋 Concept ready for implementation discussion
**Recommendation:** Start with **Option A** (Selection Buttons Below Each Report) - most intuitive UX

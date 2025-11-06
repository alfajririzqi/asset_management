# Scene Analysis UI Demo

## 📊 Dialog Popup Preview

Berikut adalah tampilan **Dialog Popup** yang muncul setelah Scene Analysis selesai:

```
╔════════════════════════════════════════════════════════════════╗
║                    Scene Analysis Complete ✅                  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │ 📄 Scene_DataUsage Report:                              │ ║
║  │                                                          │ ║
║  │ ========================================================│ ║
║  │ SCENE DATA USAGE REPORT                                 │ ║
║  │ Generated: 2025-11-04 14:23:45                          │ ║
║  │ ========================================================│ ║
║  │                                                          │ ║
║  │ OBJECT: Cube [8 verts] [1 material(s)]                  │ ║
║  │   └─ MATERIAL: Material.001                             │ ║
║  │        └─ BaseColor_1k.png                              │ ║
║  │                                                          │ ║
║  │ OBJECT: Sphere [482 verts] [2 material(s)]              │ ║
║  │   └─ MATERIAL: Metal_Material                           │ ║
║  │        ├─ Metallic_1k.png                               │ ║
║  │        ├─ Roughness_1k.png                              │ ║
║  │        └─ Normal_1k.png                                 │ ║
║  │                                                          │ ║
║  │ OBJECT: Character [15.2K verts] [3 material(s)]         │ ║
║  │   └─ MATERIAL: Skin_Material                            │ ║
║  │        ├─ Skin_Diffuse.png                              │ ║
║  │        └─ Skin_Normal.png                               │ ║
║  │                                                          │ ║
║  │ ... 87 more lines ⋯                                     │ ║
║  │ See full report → ℹ                                     │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │ 📄 Scene_TexturePaths Report:                           │ ║
║  │                                                          │ ║
║  │ ========================================================│ ║
║  │ TEXTURE PATHS REPORT                                    │ ║
║  │ Generated: 2025-11-04 14:23:45                          │ ║
║  │ ========================================================│ ║
║  │                                                          │ ║
║  │ [FOUND]                                                 │ ║
║  │   • //textures/BaseColor_1k.png == (1024x1024) [2.4 MB] │ ║
║  │   • //textures/Normal_1k.png == (1024x1024) [3.1 MB]    │ ║
║  │   • //textures/Roughness_1k.png == (1024x1024) [512 KB] │ ║
║  │   • //textures/Metallic_1k.png == (1024x1024) [450 KB]  │ ║
║  │   • //textures/AO_1k.png == (1024x1024) [380 KB]        │ ║
║  │   • //textures/Emissive_1k.png == (1024x1024) [1.2 MB]  │ ║
║  │                                                          │ ║
║  │ [LINKED LIBRARIES]                                      │ ║
║  │ Library: //libs/character.blend                         │ ║
║  │   Textures: 8                                           │ ║
║  │     • Character_Diffuse.png (2048x2048)                 │ ║
║  │     • Character_Normal.png (2048x2048)                  │ ║
║  │                                                          │ ║
║  │ ... 34 more lines ⋯                                     │ ║
║  │ See full report → ℹ                                     │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │    [ Switch to Scripting Workspace ] 💼                 │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║                            [ OK ]                              ║
╚════════════════════════════════════════════════════════════════╝
```

## 🎯 User Workflow

### Step 1: Run Analysis
User klik **"Analyze Scene Deeply"** di panel → Progress bar 0-100%

### Step 2: Dialog Appears (600px width)
Dialog popup muncul dengan:
- ✅ **Header**: "Scene Analysis Complete" 
- 📄 **Scene_DataUsage Preview**: 15 baris **SKIP stats** (langsung ke OBJECT list)
- 🔢 **Remaining Lines**: "... 87 more lines" + hint
- 📄 **Scene_TexturePaths Preview**: 15 baris **SKIP stats** (langsung ke [FOUND])
- 🔢 **Remaining Lines**: "... 34 more lines" + hint
- 💼 **Button**: "Switch to Scripting Workspace"

### Step 3: Switch to Scripting Workspace
User klik **"Switch to Scripting Workspace"** button → Blender switch ke **Scripting workspace** dan Text Editor otomatis load `Scene_DataUsage`.

## 🔧 Technical Details

### Dialog Components

```python
def draw(self, context):
    layout = self.layout
    
    # 1. HEADER BOX
    box = layout.box()
    box.label(text="✅ Scene Analysis Complete", icon='CHECKMARK')
    
    # 2. SCENE_DATAUSAGE PREVIEW (15 lines, no stats)
    data_usage = bpy.data.texts.get("Scene_DataUsage")
    content = data_usage.as_string()
    lines = content.split('\n')
    
    box = layout.box()
    box.label(text="📄 Scene_DataUsage Report:", icon='TEXT')
    
    col = box.column(align=True)
    col.scale_y = 0.7
    
    # Skip stats section, show content directly (after "----")
    preview_count = 0
    start_showing = False
    
    for line in lines:
        if not start_showing:
            if line.startswith("----"):  # Divider after stats
                start_showing = True
                continue
        
        if start_showing and preview_count < 15:
            col.label(text=line)
            preview_count += 1
    
    # Show remaining lines indicator
    if len(lines) - skipped_lines > 15:
        remaining = len(lines) - skipped_lines - 15
        box.separator()
        row = box.row()
        row.label(text=f"... {remaining} more lines", icon='THREE_DOTS')
        row.label(text="See full report →", icon='INFO')
    
    # 3. SCENE_TEXTUREPATHS PREVIEW (same pattern)
    texture_report = bpy.data.texts.get("Scene_TexturePaths")
    # ... same logic
    
    # 4. ACTION BUTTON (to the point, no extra label)
    layout.operator("scene.open_text_editor_area", 
                   text="Switch to Scripting Workspace", 
                   icon='WORKSPACE')
```

### Button Action

```python
def execute(self, context):
    # 1. Get report from memory
    data_usage_text = bpy.data.texts.get("Scene_DataUsage")
    
    # 2. Get Scripting workspace (Blender default)
    scripting_workspace = bpy.data.workspaces.get('Scripting')
    
    # 3. Switch to Scripting workspace
    context.window.workspace = scripting_workspace
    
    # 4. Find Text Editor area
    for area in context.screen.areas:
        if area.type == 'TEXT_EDITOR':
            # 5. Load report + enable features
            space.text = data_usage_text
            space.show_line_numbers = True
            space.show_syntax_highlight = True
            break
    
    # 6. Dialog auto-closes
    return {'FINISHED'}
```

## 📝 Report Content (Full Version with Stats)

### Scene_DataUsage Report (FULL VERSION)
```
============================================================
SCENE DATA USAGE REPORT
Generated: 2025-11-04 14:23:45
============================================================

Total Objects: 15
Total Materials: 8
Total Textures: 42

------------------------------------------------------------

OBJECT: Cube [8 verts] [1 material(s)]
  └─ MATERIAL: Material.001
       └─ BaseColor_1k.png
       
OBJECT: Sphere [482 verts] [2 material(s)]
  └─ MATERIAL: Metal_Material
       ├─ Metallic_1k.png
       ├─ Roughness_1k.png
       └─ Normal_1k.png

OBJECT: Character [15.2K verts] [3 material(s)]
  └─ MATERIAL: Skin_Material
       ├─ Skin_Diffuse.png
       └─ Skin_Normal.png

------------------------------------------------------------
MATERIAL SUMMARY:

  • Material.001: Used by 1 object(s) (Cube)
  • Metal_Material: Used by 1 object(s) (Sphere)
  • Skin_Material: Used by 1 object(s) (Character)

TEXTURE SUMMARY:

  • BaseColor_1k.png: Used in 1 material(s) (Material.001)
  • Metallic_1k.png: Used in 1 material(s) (Metal_Material)

------------------------------------------------------------
[LINKED LIBRARIES]

Library: Character_Rig
    └─ //libs/character.blend

Library: Environment
    └─ //libs/environment.blend
    
============================================================
```

### Scene_TexturePaths Report (FULL VERSION)
```
============================================================
TEXTURE PATHS REPORT
Generated: 2025-11-04 14:23:45
============================================================

Total Textures in Blend: 42
Linked Library Textures: 12
Unused Textures in Folder: 3

[FOUND]
  • //textures/BaseColor_1k.png == (1024x1024) [2.4 MB]
  • //textures/Normal_1k.png == (1024x1024) [3.1 MB]
  • //textures/Roughness_1k.png == (1024x1024) [512.3 KB]
  • //textures/Metallic_1k.png == (1024x1024) [450.2 KB]
  • //textures/AO_1k.png == (1024x1024) [380.5 KB]

[LINKED LIBRARIES]
Library: //libs/character.blend
  Textures: 8
    • Character_Diffuse.png (2048x2048)
    • Character_Normal.png (2048x2048)
    • Character_Roughness.png (2048x2048)

[MISSING]
  • ✗ //textures/old_texture.png
    Expected: G:/Projects/textures/old_texture.png

[PACKED]
  • 📦 Generated_Texture == (512x512)

[UNUSED IN FOLDER /textures]
  • backup_color.jpg [1.8 MB]
  • test_normal.png [3.2 MB]
  
============================================================
```

## 🎨 UI Features

### Visual Elements
- ✅ **Green checkmark** for completion
- 📄 **Document icon** for report headers
- ⋯ **Three dots icon** for "more lines" indicator
- ℹ **Info icon** for hints (shortened)
- 💼 **Workspace icon** for button
- 🔢 **Dynamic line count** (auto-calculated)
- 📊 **File size display** - Shows texture sizes in B/KB/MB format

### Layout
- **Width**: 600px (like Blender Preferences)
- **Two boxed previews** - one for each report
- **Compressed text** (scale_y = 0.7) for more lines visible
- **Preview limit**: 15 lines per report
- **Smart indicators**: Shows exact number of remaining lines
- **Direct button** - no extra "View full reports:" label

### Behavior
- **Modal dialog** - blocks interaction until closed
- **Live report preview** - shows actual content (15 lines)
- **Smart line counting** - calculates remaining lines
- **Dual preview** - both reports visible
- **One-click switch** to Scripting workspace
- **Auto-load report** with syntax highlighting
- **Auto-close dialog** after button click

## 🚀 Advantages

1. ✅ **Best of Both Worlds** - Full stats in report, clean preview in dialog
2. ✅ **Smart Preview** - Skip stats, show actual content immediately
3. ✅ **Complete Reports** - Full statistics preserved for analysis
4. ✅ **Dual Report View** - Both reports visible in one dialog
5. ✅ **Smart Indicators** - Exact remaining line count
6. ✅ **One-Click Switch** - Direct to Scripting workspace
7. ✅ **Blender Native** - Uses Scripting workspace (default layout)
8. ✅ **Auto-Load** - Scene_DataUsage in Text Editor automatically
9. ✅ **Informative** - 15 lines of content gives good context

## 🎯 Key Changes from Previous Version

- ✅ **Full Report**: Stats tetap ada (Total Objects/Materials/Textures)
- ✅ **Dialog Preview**: Skip stats section, langsung ke content
- ✅ **Smart Skip Logic**: 
  - Scene_DataUsage: Skip sampai setelah "----" divider
  - Scene_TexturePaths: Skip sampai [FOUND] atau [LINKED] section
- ❌ **Removed**: "View full reports:" label before button
- ✅ **Simplified**: Hint text "See full report →"
- ✅ **Best of Both**: Full stats in report, clean preview in dialog

---

**Created**: 2025-11-04  
**Dialog Width**: 600px  
**Preview Lines**: 15 per report  
**Operator ID**: `scene.analyze_deep`  
**Helper Operator**: `scene.open_text_editor_area`

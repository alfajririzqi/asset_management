# GitHub Copilot Training Instructions

**Use this file to train GitHub Copilot in a new project/device**

---

## 📚 How to Use This File

### **Step 1: Open New Project in VS Code**
```bash
# Clone or open your project
git clone https://github.com/alfajririzqi/asset_management.git
cd asset_management
code .
```

### **Step 2: Train Copilot**
In Copilot Chat, type:
```
@workspace Read .github/copilot-instructions.md and COPILOT_TRAINING.md. 
Summarize the addon architecture, key design patterns, and safety mechanisms.
```

### **Step 3: Verify Understanding**
Ask Copilot:
```
@workspace Explain the published file detection system and why it's important.
@workspace How do I add a new panel with published file protection?
@workspace What is the circular import prevention pattern?
```

If Copilot answers correctly, training successful! ✅

---

## 🎯 Quick Context Summary

### **Project Overview**
- **Name:** Blender Asset Management Addon
- **Purpose:** Production-ready asset publishing, texture optimization, and version control
- **Target:** Freelancers, hobbyists, asset creators
- **Blender:** 4.0+
- **License:** GPL-3.0

### **Version Strategy**
- **v1.0 (FREE):** Complete single-file workflow (current)
- **v2.0 (PRO ~$19):** Batch automation features (planned)

---

## 🏗️ Architecture Quick Reference

### **Module Structure**
```
asset_management/
├── operators/          # Business logic (publish, optimize, analyze)
├── panels/            # UI components (main, versioning, publish, etc.)
├── utils/             # Shared utilities (published_file_detector)
└── __init__.py        # Registration + app handlers
```

### **Critical Design Patterns**

#### 1. **Circular Import Prevention**
```python
# ❌ WRONG - Causes circular import
from ..operators.check_publish import detect_published_file_status

# ✅ CORRECT - Use utils for shared code
from ..utils.published_file_detector import detect_published_file_status
```

**Why:** Operators import each other → Panels import from operators → Circular dependency

**Solution:** Place shared utilities in `utils/` module

---

#### 2. **Published File Detection (3-Layer)**
```python
# METHOD 1: Folder pattern (AssetName_v001)
if re.match(r'.+_v\d{3}$', folder_name):
    return True, source_path

# METHOD 2: User's publish_path setting
log_file = os.path.join(publish_path, ".publish_activity.log")

# METHOD 3: Parent folder fallback
parent_log = os.path.join(parent_dir, ".publish_activity.log")
```

**Caching:** Use `_publish_detection_cached` attribute to prevent repeated I/O

---

#### 3. **Published File Protection (TOTAL BLOCK)**
```python
# In ALL panels that modify files:
is_published, source = detect_published_file_status(context)

if is_published:
    row.alert = True
    row.label(text="🚫 Published file - Operations disabled")
    row.enabled = False  # Disable ALL modification operators
```

**Philosophy:** Prevent recursive versioning - NEVER modify published files

**Blocked Operations:**
- ❌ Publishing
- ❌ Versioning  
- ❌ Texture optimization
- ❌ Batch rename
- ❌ All file modifications

---

## 🚨 Critical Safety Rules

### **Rule 1: Published File Protection is NON-NEGOTIABLE**
- Every panel that modifies files MUST check `detect_published_file_status()`
- Detection must run BEFORE any operation
- Cache results to prevent performance issues

### **Rule 2: Force Publish - Only 2 Absolute Blocks**
```python
# CRITICAL - Always block (can't force)
if not bpy.data.filepath:
    errors.append("File not saved")
if not context.scene.publish_path:
    errors.append("No publish path")

# WARNINGS ONLY - Force publish bypasses these
if missing_textures:
    warnings.append("Missing textures")  # Can force
```

### **Rule 3: Validation Required Before Publish**
```python
# In publish operator invoke()
if not context.scene.publish_check_done:
    self.report({'ERROR'}, "Run 'Check Publish Readiness' first")
    return {'CANCELLED'}
```

**Auto-Reset:** App handler clears `publish_check_done` on file load

---

## 🎨 UI Patterns

### **Pattern 1: Inline Warnings (Consistent)**
```python
# ✅ CORRECT - Per-row red color
if is_published:
    row = box.row()
    row.alert = True  # Individual row alert
    row.label(text="⚠ Warning message", icon='ERROR')

# ❌ WRONG - Box-level alert
if is_published:
    box.alert = True  # Don't do this
```

### **Pattern 2: Validation Results Display**
```python
# Individual item colors (not box-level)
for item_type, message, detail in validation_results:
    row = box.row()
    if item_type == "error":
        row.alert = True  # Red for this row only
        row.label(text=f"✗ {message}", icon='ERROR')
    elif item_type == "warning":
        row.alert = True
        row.label(text=f"⚠ {message}", icon='INFO')
    else:
        row.label(text=f"✓ {message}", icon='CHECKMARK')
```

### **Pattern 3: Button Disable Logic (Priority-based)**
```python
# Priority 1: Published file (highest)
if is_published:
    row.enabled = False
    row.label(text="Cannot publish: Published file")
    
# Priority 2: Validation not done
elif not check_done:
    row.enabled = False
    row.label(text="Run validation first")
    
# Priority 3: Critical errors (only if not force)
elif has_errors and not force_publish:
    row.enabled = False
    row.label(text="Fix errors or enable Force Publish")
```

---

## 📝 Logging System

### **Single Log File**
- **Location:** `{publish_path}/.publish_activity.log`
- **Format:** 
  ```
  [2025-11-07 14:23:45] PUBLISH | Asset: Chair | Path: D:\Publish\Chair_v001 | Source: D:\Assets\Chair | User: Artist | Mode: Normal | Textures: 15 | Status: SUCCESS
  ```

### **Why Single Log?**
- Clean client delivery (no metadata in published folders)
- Centralized tracking
- Easy parsing for detection

**Removed:** Per-asset `.asset_history.json` files (old system)

---

## 🔧 Common Tasks

### **Task 1: Add New Panel with Protection**
```python
from ..utils.published_file_detector import detect_published_file_status

class MY_PT_NewPanel(bpy.types.Panel):
    def draw(self, context):
        layout = self.layout
        
        # Detect published file
        is_published, source = detect_published_file_status(context)
        
        # Show warning
        if is_published:
            row = layout.row()
            row.alert = True
            row.label(text=f"🚫 Published File", icon='ERROR')
        
        # Disable operators
        row = layout.row()
        row.enabled = not is_published
        row.operator("my.operator")
```

### **Task 2: Add New Validation Check**
```python
# In operators/check_publish.py execute()

# 1. Gather data
new_check_value = your_check_logic()

# 2. Store in scene property
context.scene.your_check_result = new_check_value

# 3. In panels/publish_panel.py, display result
if scene.your_check_result:
    row = box.row()
    row.alert = True
    row.label(text="✗ Your warning", icon='ERROR')
```

### **Task 3: Debug Circular Imports**
```
Error: AttributeError: module 'operators.check_publish' has no attribute 'X'

Solution:
1. Check if function is in utils/, not operators/
2. Update imports: from ..utils.module import ...
3. Verify utils/__init__.py exists
4. Reload addon in Blender (F3 → "Reload Scripts")
```

---

## 📋 Scene Properties Reference

```python
# Publishing
publish_check_done: BoolProperty          # Validation completed
publish_force: BoolProperty               # Force publish mode
publish_path: StringProperty              # Publish directory

# Published File Detection
publish_is_published_file: BoolProperty   # Current file is published
publish_source_path: StringProperty       # Original source path
_publish_detection_cached: (dynamic)      # Cache (prevent repeated I/O)

# Validation Results
publish_asset_name: StringProperty
publish_file_name: StringProperty
publish_textures_exist: BoolProperty
publish_texture_count: IntProperty
publish_external_textures: IntProperty
publish_missing_textures: IntProperty
publish_packed_textures: IntProperty
publish_orphan_count: IntProperty
```

---

## 🐛 Known Issues & Solutions

### **Issue 1: Panels Not Loading**
**Symptom:** Empty N-panel, no UI visible  
**Cause:** Circular import  
**Solution:** Move shared code to `utils/` module

### **Issue 2: Validation Not Resetting**
**Symptom:** Old results persist after opening new file  
**Cause:** App handler not clearing cache  
**Solution:** Check `reset_publish_validation_on_load()` in `__init__.py`

### **Issue 3: Detection Not Working**
**Symptom:** Published file not detected  
**Solution:** 
1. Clear `_publish_detection_cached` attribute
2. Check log format: `Path: {path} | Source: {source}`
3. Verify `.publish_activity.log` exists

---

## 🚀 Pro Version (v2.0) - Planned Features

**Theme:** Batch Automation for Large-Scale Projects

### **4 Core Features:**

1. **Batch Publishing** ⭐⭐⭐⭐⭐
   - Queue multiple blend files
   - Background processing
   - Auto-retry failed items
   - Time saved: 2-3 hours per batch

2. **Batch Downgrade Texture** ⭐⭐⭐⭐⭐
   - Downgrade all textures in bulk
   - Select resolution (4K → 2K → 1K → 512px)
   - Process entire project folders
   - Time saved: 30-60 minutes per batch

3. **Batch Convert Image Format** ⭐⭐⭐⭐⭐
   - Convert to PNG, JPEG, TIFF, TGA, EXR, WebP
   - Multi-format export for different platforms
   - Per-format quality settings
   - Time saved: 45-90 minutes per batch

4. **Batch Cleanup Operations** ⭐⭐⭐⭐⭐
   - Clear orphan data in multiple files
   - Remove unused material slots
   - Optimize file sizes (30-50% reduction)
   - Time saved: 1-2 hours per batch

**Total Time Saved:** 4-7 hours per large project  
**Pricing:** $15-19 one-time  
**Launch:** ~12 months after v1.0

---

## 💡 Development Principles

### **Key Principles:**
1. ⚠️ **Safety First:** Published file protection is non-negotiable
2. 📦 **Clean Delivery:** No metadata in published folders
3. 🔄 **Avoid Circular Imports:** Use utils/ for shared code
4. 🎨 **Consistent UI:** Individual row alerts, inline warnings
5. 📝 **Single Source of Truth:** One `.publish_activity.log`

### **Testing Checklist:**
- [ ] Reload addon (F3 → "Reload Scripts")
- [ ] Check all panels load (4 main panels)
- [ ] Open source file → Operators enabled
- [ ] Open published file → Inline warnings + disabled
- [ ] Run validation → Individual red colors display
- [ ] Force publish → Bypasses warnings only
- [ ] Check log format in `.publish_activity.log`

---

## 🎓 Training Verification Questions

Ask Copilot these to verify training:

1. **Architecture:**
   - "Where should I put a shared utility function?"
   - "Why do we use utils/ instead of operators/ for shared code?"

2. **Safety:**
   - "What operations are blocked on published files?"
   - "How many absolute blocks exist in force publish mode?"

3. **Patterns:**
   - "How do I add published file protection to a new panel?"
   - "What's the correct way to display validation warnings?"

4. **Debugging:**
   - "What causes circular import errors in this addon?"
   - "How do I clear the published file detection cache?"

5. **Pro Features:**
   - "What are the 4 batch features in v2.0 Pro?"
   - "Why is batch focus perfect for freelancers?"

---

## 📌 Quick Command Reference

```python
# Detect published file
from ..utils.published_file_detector import detect_published_file_status
is_published, source = detect_published_file_status(context)

# Scene properties (common)
context.scene.publish_check_done
context.scene.publish_is_published_file
context.scene.publish_force

# App handler (reset validation)
@persistent
def reset_publish_validation_on_load(dummy):
    scene = bpy.context.scene
    scene.publish_check_done = False
    if hasattr(scene, '_publish_detection_cached'):
        delattr(scene, '_publish_detection_cached')
```

---

**Last Updated:** 2025-11-07  
**Version:** 1.0 (FREE)  
**Next Version:** 2.0 PRO (Batch Automation) - Planned

---

## ✅ Training Complete Checklist

- [ ] Copilot understands addon architecture
- [ ] Copilot knows circular import prevention pattern
- [ ] Copilot understands published file protection
- [ ] Copilot can explain force publish rules
- [ ] Copilot knows UI patterns (inline warnings, row alerts)
- [ ] Copilot understands Pro version strategy
- [ ] Copilot can answer debugging questions

**If all checked:** You're ready to code! 🚀

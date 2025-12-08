# Blender Asset Management Addon - Copilot Instructions

## 🎯 Addon Overview
Production-ready Blender 3.6+ addon untuk asset management dengan fokus pada **publish workflow**, **texture optimization**, **versioning system**, dan **linked library management**.

**Current Version:** 1.5.0  
**Release Date:** November 17, 2025

## 📐 Architecture

### Module Structure
```
asset_management/
├── operators/          # Business logic & operations
│   ├── publish.py     # Main publish operator dengan validation & logging
│   ├── check_publish.py  # Pre-publish validation
│   ├── versioning.py  # Version management
│   ├── optimize_*.py  # Texture optimization operators
│   └── ...
├── panels/            # UI components
│   ├── main_panel.py           # Root panel
│   ├── publish_panel.py        # Publishing UI dengan validation results
│   ├── versioning_panel.py     # Version creation/restore UI
│   ├── file_management_panel.py # Texture operations UI
│   └── batch_rename_panel.py   # Batch rename UI
├── utils/             # Shared utilities (PENTING: mencegah circular imports)
│   └── published_file_detector.py  # Multi-layer published file detection
└── __init__.py        # Registration & app handlers
```

### 🔄 Critical Design Patterns

#### 1. Circular Import Prevention
**ALWAYS** letakkan shared utilities di `utils/` module, BUKAN di `operators/`.
```python
# ❌ WRONG - Causes circular import
from ..operators.check_publish import detect_published_file_status

# ✅ CORRECT - Independent utility
from ..utils.published_file_detector import detect_published_file_status
```

**Why:** `operators/__init__.py` imports all operators → panels import from operators → circular dependency.

#### 2. Published File Detection (3-Layer)
```python
# METHOD 1: Folder pattern (AssetName_v001, _v002, etc)
folder_name = "Character_v001" → Published
folder_name = "Character_WIP" → Source

# METHOD 2: User's publish_path setting
Check .publish_activity.log in publish_path directory

# METHOD 3: Parent folder fallback
Check parent directory for .publish_activity.log
```

**Caching:** Use `_publish_detection_cached` attribute to prevent repeated I/O on panel redraws.

#### 3. Scene Properties for Persistent State
```python
# Validation results
context.scene.publish_check_done: BoolProperty
context.scene.publish_is_published_file: BoolProperty
context.scene.publish_source_path: StringProperty

# User settings
context.scene.publish_path: StringProperty
context.scene.publish_force: BoolProperty
```

**App Handler:** `reset_publish_validation_on_load()` clears validation on file load.

## 🚨 Critical Safety Mechanisms

### 1. Published File Protection (TOTAL BLOCK)
**Philosophy:** Prevent recursive versioning - NEVER modify published files.

**Implementation:**
```python
# In ALL panels (Versioning, File Management, Batch Rename, Publish)
is_published, source = detect_published_file_status(context)

if is_published:
    row.alert = True
    row.label(text=f"⚠ Published File (Source: {source})", icon='ERROR')
    row.enabled = False  # Disable ALL operators
```

**Operators Blocked:**
- ❌ Publish button
- ❌ Create Version
- ❌ Restore Version
- ❌ All texture operations (optimize, consolidate, convert, etc)
- ❌ Batch rename

### 2. Force Publish - Option A (Total Bypass)
**Rules:**
- Only 2 ABSOLUTE blocks:
  1. File not saved (`bpy.data.filepath` empty)
  2. Publish path not set (`context.scene.publish_path` empty)
  
- Everything else = WARNING (force-able):
  - Texture folder not found
  - Missing textures
  - External textures
  - Orphan data
  - Packed textures

**Code Pattern:**
```python
def validate_publish(self, context):
    errors = []
    warnings = []
    
    # CRITICAL - Always block
    if not bpy.data.filepath:
        errors.append(("File not saved", "Save your file first"))
    if not context.scene.publish_path:
        errors.append(("No publish path", "Set publish path in settings"))
    
    # WARNINGS ONLY - Force publish bypasses these
    if not os.path.exists(textures_dir):
        warnings.append(("Texture folder not found", "Create textures/ folder"))
    
    return errors, warnings
```

### 3. Validation Required Before Publish
```python
# In publish operator invoke()
if not context.scene.publish_check_done:
    self.report({'ERROR'}, "Run 'Check Publish Readiness' first")
    return {'CANCELLED'}
```

**Auto-Reset:** App handler clears `publish_check_done` on file load.

## 📝 Logging System - Clean Delivery

### Single Log File
**Location:** `{publish_path}/.publish_activity.log` (root level, NOT in published folders)

**Format:**
```
[2025-10-30 14:23:45] PUBLISH | Asset: Character | Path: D:\Publish\Character_v001 | Source: D:\Assets\Character | User: Artist | Mode: Normal | Textures: 15 | Status: SUCCESS
[2025-10-30 14:25:12] PUBLISH | Asset: Prop | Path: D:\Publish\Prop_v001 | Source: D:\Assets\Prop | User: Artist | Mode: Force | Textures: 8 | Status: FAILED - External textures found
```

**Why Single Log:**
- Clean client delivery (no metadata in published folders)
- Centralized tracking
- Easy parsing for detection

**Removed:** Per-asset `.asset_history.json` files (old system)

## 🎨 UI Guidelines

### Inline Warnings (Consistent Pattern)
```python
# ✅ CORRECT - Per-item red color
if is_published:
    row = box.row()
    row.alert = True  # Individual row alert
    row.label(text="⚠ Warning message", icon='ERROR')

# ❌ WRONG - Box-level alert (inconsistent)
if is_published:
    box.alert = True  # Don't do this
```

### Validation Results Display
```python
# Individual item colors (not box-level)
for item_type, message, detail in validation_results:
    row = box.row()
    if item_type == "error":
        row.alert = True  # Red color for this row only
        row.label(text=f"✗ {message}", icon='ERROR')
    elif item_type == "warning":
        row.alert = True  # Red color for warnings too
        row.label(text=f"⚠ {message}", icon='INFO')
    else:
        row.label(text=f"✓ {message}", icon='CHECKMARK')
```

### Button Disable Logic (Priority-based)
```python
# Priority 1: Published file (highest)
if is_published:
    row.enabled = False
    row.label(text="Cannot publish: This is a published file")
    
# Priority 2: Validation not done
elif not check_done:
    row.enabled = False
    row.label(text="Run validation first")
    
# Priority 3: Critical errors (only if not force)
elif has_errors and not force_publish:
    row.enabled = False
    row.label(text="Fix errors or enable Force Publish")
```

## 🔧 Common Tasks

### Adding New Panel Protection
```python
# 1. Import detector
from ..utils.published_file_detector import detect_published_file_status

# 2. Check at panel draw start
def draw(self, context):
    layout = self.layout
    
    # Detect published file
    is_published, source = detect_published_file_status(context)
    
    # Show warning
    if is_published:
        box = layout.box()
        row = box.row()
        row.alert = True
        source_display = source if source else "Unknown"
        row.label(text=f"⚠ Published File (Source: {source_display})", icon='ERROR')
    
    # Disable operators
    row = layout.row()
    row.enabled = not is_published
    row.operator("your.operator")
```

### Adding New Validation Check
```python
# In check_publish.py execute()

# 1. Gather data
new_check_value = your_check_logic()

# 2. Store in scene property
context.scene.your_check_result = new_check_value

# 3. In publish_panel.py, display result
if scene.your_check_result:
    row = box.row()
    row.alert = True  # Red if problem
    row.label(text="✗ Your warning", icon='ERROR')
```

### Debugging Circular Imports
```
Error: AttributeError: module 'operators.check_publish' has no attribute 'detect_published_file_status'

Solution:
1. Check if function is in utils/, not operators/
2. Update imports: from ..utils.published_file_detector import ...
3. Verify utils/__init__.py exists
4. Reload addon in Blender
```

## 🧪 Testing Checklist

### After Major Changes
- [ ] Reload addon in Blender (`F3` → "Reload Scripts")
- [ ] Check all 4 panels load (Publishing, Versioning, File Management, Batch Rename)
- [ ] Open source file → Operators enabled
- [ ] Open published file → Inline warnings + operators disabled
- [ ] Run validation → Results display with individual red colors
- [ ] Test force publish → Bypasses warnings, blocks only critical errors
- [ ] Check `.publish_activity.log` → Format correct, no files in published folders

## 📋 Scene Properties Reference

```python
# Publishing
publish_check_done: BoolProperty          # Validation completed
publish_force: BoolProperty               # Force publish mode
publish_path: StringProperty              # Publish directory

# Published File Detection
publish_is_published_file: BoolProperty   # Current file is published
publish_source_path: StringProperty       # Original source path
_publish_detection_cached: (dynamic)      # Cache to prevent repeated I/O

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

## ⚙️ Addon Preferences System

### Preferences Structure (`__init__.py`)
```python
class AssetManagementPreferences(AddonPreferences):
    # Default Paths
    default_publish_path: StringProperty  # Auto-loaded on file open
    
    # Validation Thresholds
    highpoly_default_threshold: IntProperty(default=10000)  # Polygon count limit (always checked)
    check_texture_resolution: BoolProperty(default=True)
    max_texture_resolution: EnumProperty(default='4096')  # 1K/2K/4K/8K
    
    # Validation Checks (Enable/Disable)
    check_transform_issues: BoolProperty(default=True)
    check_empty_material_slots: BoolProperty(default=False)
    check_duplicate_textures: BoolProperty(default=True)
    check_duplicate_materials: BoolProperty(default=True)
    
    # Scene Analysis
    analysis_auto_save: BoolProperty(default=False)  # Opt-in
```

### Auto-Load Pattern
```python
# In app handler: reset_publish_validation_on_load()
if not context.scene.publish_path and prefs.default_publish_path:
    context.scene.publish_path = prefs.default_publish_path
```

### Texture Resolution Check Logic
**CRITICAL:** Operator `>` (greater than), BUKAN `>=`
```python
max_res = int(prefs.max_texture_resolution)
if img.size[0] > max_res or img.size[1] > max_res:
    large_texture_count += 1

# Example: max_res = 2048 (2K)
# - Texture 2048x2048 → IGNORED (2048 = 2048, not greater)
# - Texture 4096x4096 → WARNING (4096 > 2048)
```

**Validation Checks Matching Tools:**
- ✅ High Poly Objects → Tool: `check_highpoly.py` (always checked, uses threshold from preferences)
- ✅ Transform Issues → Tool: `check_transform.py` (Apply All Transforms)
- ✅ Empty Material Slots → Tool: `clear_material_slots.py`
- ✅ Duplicate Textures → Tool: `optimize_textures.py`
- ✅ Duplicate Materials → Tool: `optimize_materials.py`
- ✅ Large Textures → Tool: `downgrade_resolution.py`
- ✅ External Textures → Tool: `consolidate_textures.py`
- ✅ Orphan Data → Tool: `clear_orphan_data.py`

## 📚 Linked Libraries Workflow

### Dependency Chain (CRITICAL ORDER)
```
1. Run "Check Publish Readiness" (ASSET_OT_CheckPublish)
   ↓ Enables checkbox
2. Centang "Publish Linked Libraries" (publish_include_libraries)
   ↓ Shows scan button
3. Klik "Scan & Validate Libraries" (ASSET_OT_ValidateLibraries)
   ↓ NO publish_path required!
4. Validation results displayed
```

### Library Scan Logic - Common Root Detection
```python
# Step 1: Separate by drive
current_drive = os.path.splitdrive(current_file)[0]
for lib in libraries:
    lib_drive = os.path.splitdrive(lib.filepath)[0]
    if lib_drive == current_drive:
        internal_lib_paths.append(lib.filepath)
    else:
        external_libs.append(lib.name)

# Step 2: Find common root for internal libraries only
common_root = os.path.commonpath(internal_lib_paths)

# Step 3: Calculate structure for each library
for lib_filepath in lib_filepaths:
    if lib in external_libs or not lib_filepath.startswith(common_root):
        # External library - preserve parent folder with _external/ prefix
        parent_folder = os.path.basename(os.path.dirname(lib_filepath))
        structure = f"_external/{parent_folder}"  # "_external/_backup"
    else:
        # Internal library - mirror structure (includes folder name!)
        rel_path = os.path.relpath(lib_filepath, common_root)
        structure = os.path.dirname(rel_path)  # "01_character/01_main/arkana"
```

**Why NO publish_path:**
- Checkbox depends on `publish_check_done`, NOT `publish_path`
- Scan only needs current blend file's linked libraries
- Publish_path only needed for ACTUAL PUBLISH, not validation

### Structure Mirroring Logic
```
Master Folder (auto-detected common root):
assets/
  ├── char/main/arkana/arkana.blend          [lib]
  └── set/sitemap/pohonWanamatu/
      ├── pohonWanamatu.blend                [current]
      └── pohonWanamatu_ground.blend         [lib]

Publish Folder (mirrored structure):
publish/
  ├── 01_character/01_main/arkana/chr_arkana.blend    [copied]
  ├── 04_set/sitemap/pohonWanamatu/pohonWanamatu.blend [published]
  └── _external/_backup/ground_wanamatu.blend         [external from D:\_backup\]

External Libraries (Option C+):
publish/
  └── _external/
      └── _backup/                           [parent folder preserved]
          ├── ground_wanamatu.blend          [copied]
          └── textures/                      [textures preserved]
```

**External Library Handling:**
- Detect: Library outside common root (different path or drive)
- Copy: To `_external/{parent_folder}/` (preserves parent directory name)
- Structure: `_external/_backup` for files in `D:\_backup\file.blend`
- Preserve: Textures and folder structure (recursive copy with os.walk)
- Skip: Hidden folders (.backup, .trash)
- Result: External libs grouped in _external/ folder, internal libs mirror structure

### Publish Execution Flow (publish.py)
```python
# STEP 1: Setup paths (calculate structure from common root)
master_target_folder = os.path.join(publish_path, master_structure)

# STEP 2: Publish linked libraries FIRST
for lib_info in self.libraries_to_publish:
    lib_path = self.publish_linked_library(lib_info, context)
    self.copy_library_textures(lib_info, lib_folder)

# STEP 3: Publish master file
published_path = self.publish_master_file(current_file, master_target_folder, context)

# STEP 4: Copy master textures
target_textures = os.path.join(master_target_folder, "textures")

# STEP 5: Relink external libraries (NEW!)
relinked_count = self.relink_external_libraries(
    published_path, published_libraries, publish_path, context
)
# Opens published file, updates library paths to relative paths, saves

# STEP 6: Write logs
```

**Key Functions:**
- `publish_linked_library(lib_info, context)`:
  - Determines target folder from `lib_info['structure']`
  - Internal: `publish_path/structure/` (structure already includes folder name)
  - External: `publish_path/_external/parent_folder/` (preserves parent directory)
  - Copies .blend file with `shutil.copy2()`
  
- `copy_library_textures(lib_info, target_folder)`:
  - Uses `os.walk()` to recursively copy textures/
  - Skips hidden folders (starts with '.')
  - Preserves subfolder structure
  - Returns copied texture count

- `relink_external_libraries(blend_file, published_libs, publish_root, context)` (NEW):
  - Opens published .blend file
  - Relinks external libraries (_external/*) to new relative paths
  - Calculates relative path from published file to _external/ location
  - Saves file and reopens original
  - Returns count of relinked libraries

### UI Enable Logic (publish_panel.py)
```python
# Checkbox disabled if:
if scene.publish_is_published_file:
    row.enabled = False  # Published file
elif not scene.publish_check_done:
    row.enabled = False  # Pre-publish not run yet
    # Show: "Run 'Check Publish Readiness' first"
```

## 🚀 Development Workflow

### Making Changes
1. **Read context** from this file
2. **Check existing patterns** in similar operators/panels
3. **Follow architecture** (utils/ for shared code)
4. **Test in Blender** after changes
5. **Update this file** if adding new patterns

### Key Principles
- ⚠️ **Safety First:** Published file protection is NON-NEGOTIABLE
- 📦 **Clean Delivery:** No metadata in published folders
- 🔄 **Avoid Circular Imports:** Use utils/ for shared code
- 🎨 **Consistent UI:** Individual row alerts, inline warnings
- 📝 **Single Source of Truth:** One .publish_activity.log
- 🎯 **Validation Matches Tools:** Every check must have solving tool
- 🔗 **Library Scan Independence:** No publish_path for validation

## 🐛 Known Issues & Solutions

### Panels Not Loading
**Symptom:** Empty N-panel, no UI visible
**Cause:** Circular import (panels import from operators)
**Solution:** Move shared code to utils/ module

### Validation Not Resetting
**Symptom:** Old validation results persist after opening new file
**Cause:** App handler not clearing cache
**Solution:** Check `reset_publish_validation_on_load()` in `__init__.py`

### Detection Not Working
**Symptom:** Published file not detected
**Cause:** Cache not cleared or log format mismatch
**Solution:** 
1. Clear `_publish_detection_cached` attribute
2. Check log format matches: `Path: {path} | Source: {source}`

## 📝 Recent Conversations & Decisions

### 2025-11-14: Structure Mirroring & Common Root Detection

**Context:** User reported publish system doesn't properly mirror folder structure from master folder, causing library path errors after publish.

**Problem:**
```
Master: assets/set/sitemap/pohonWanamatu/pohonWanamatu.blend
        assets/char/main/arkana/arkana.blend [linked]

Publish: publish/set/sitemap/pohonWanamatu/pohonWanamatu.blend
         publish/??? [structure broken, paths error]
```

**Solution - Auto-Detect Common Root:**
1. Scan current file + all linked libraries
2. Find common root folder (shared parent)
3. Extract structure relative to common root
4. Mirror exact structure to publish folder
5. External libs (outside common root) → copy to `_external/{folder_name}/`

**Key Decisions:**
1. **Auto-detection only:** No manual structure setting, detect from file paths
2. **Common root algorithm:** Use `os.path.commonpath()` to find shared parent
3. **Structure preservation:** Mirror exact folder hierarchy from common root
4. **External library handling (Option C+):**
   - Copy entire folder to `_external/{folder_name}/`
   - Preserve textures and subfolders
   - Auto-relink with relative paths
5. **Error on different drives:** Show error if external lib on different drive (cannot find common root)

**Files Modified:**
- `operators/check_publish.py`: Added common root detection in `quick_validate_linked_libraries()`
- `.github/copilot-instructions.md`: Documented structure mirroring logic

---

### 2025-11-09: Addon Preferences & Validation System Overhaul

**Context:** User requested professional addon preferences with validation customization.

**Key Decisions:**
1. **Auto-Load Pattern:** Preferences auto-populate scene properties on file open (NO manual "Load" button)
2. **Texture Resolution:** Dynamic threshold (1K/2K/4K/8K dropdown), check uses `>` operator (strict greater than)
3. **Validation Philosophy:** Every check must match existing tool (e.g., high poly → check_highpoly.py)
4. **Library Scan Logic:** NO publish_path required - checkbox depends on `publish_check_done` only
5. **Scene Analysis:** Opt-in auto-save (default False), plain text format, always overwrite

**Critical Learning:**
- User emphasized: "CHECKBOX publish lib hanya bisa dicentang setelah run pre-publish validasi"
- Dependency chain: Pre-publish → Checkbox → Scan (NOT: Publish_path → Scan)
- Texture check: `if size > max_res` (NOT `>=`), so 2048px texture with 2K limit = IGNORED

**Files Modified:**
- `__init__.py`: Added 6 new preference properties
- `operators/check_publish.py`: 5 new validation checks, library scan rewrite
- `operators/publish.py`: 5 new scene properties registered
- `panels/publish_panel.py`: Checkbox disable logic, validation results display
- `operators/check_scene.py`: Auto-save reports feature

---

### 2025-11-17: v1.5 Release - Auto-Validation & Reload Library

**Context:** User requested removal of manual "Scan & Validate Libraries" button and fix for reload library functionality.

**Key Decisions:**
1. **Auto-Validation on Checkbox:** Move validation logic to `publish_include_libraries` property's `update` function
2. **Remove Manual Button:** Delete separate "Scan & Validate Libraries" button from UI
3. **Reload Library Fix:** Implement path normalization for relative/absolute path matching
4. **UI Improvements:** Remove excessive separators to prevent white space when no errors

**Implementation:**

**1. Auto-Validation Pattern:**
```python
def update_include_libraries(self, context):
    """Auto-validate libraries when checkbox is toggled ON"""
    if context.scene.publish_include_libraries:
        from .check_publish import quick_validate_linked_libraries
        total, errors, warnings = quick_validate_linked_libraries(context)
    else:
        # Reset when unchecked
        context.scene.publish_libraries_validated = False
        context.scene.publish_library_selection.clear()

# Property with update function
bpy.types.Scene.publish_include_libraries = BoolProperty(
    name="Include Linked Libraries",
    default=False,
    update=update_include_libraries  # Auto-trigger validation
)
```

**2. Reload Library Path Normalization:**
```python
# Panel UI - normalize paths before comparison
item_path_norm = os.path.normpath(os.path.abspath(item.filepath))
lib_path_norm = os.path.normpath(os.path.abspath(lib_path_abs))

if lib_path_norm == item_path_norm:
    reload_op = row.operator("asset.reload_library", ...)
    reload_op.library_path = item.filepath

# Operator - normalize paths in execute
target_path_norm = os.path.normpath(os.path.abspath(self.library_path))
lib_path_norm = os.path.normpath(os.path.abspath(lib_abs_path))

if lib_path_norm == target_path_norm:
    lib_to_reload.reload()  # Match found!
```

**Why Path Normalization:**
- Handles relative paths: `//..\..\character\chr.blend`
- Handles absolute paths: `G:\assets\character\chr.blend`
- Handles mixed slashes: `/` vs `\`
- Blender libraries use relative paths by default

**3. UI Improvements:**
- Removed separator after checkbox (prevents white space when no libraries)
- Validation results show immediately on checkbox toggle
- No manual scan button needed

**New User Flow:**
```
1. Run "Check Publish Readiness" ✓
2. Check "Publish Linked Libraries" → Auto-validates instantly ⚡
3. Results appear immediately (no scan button)
4. Reload button works for all libraries (path normalization)
```

**Files Modified:**
- `operators/publish.py`: Added `update_include_libraries()` function, path normalization in reload operator
- `panels/publish_panel.py`: Removed scan button, added path normalization for reload button
- `__init__.py`: Library selection reset on file load (already exists)

**Benefits:**
- ✅ Faster workflow (1 less click)
- ✅ More intuitive (checkbox = action)
- ✅ Cleaner UI (no white space)
- ✅ Reliable reload (path normalization)

---

**Last Updated:** 2025-11-17  
**Version:** 1.5.0  
**Blender Version:** 3.6+  
**Python Version:** 3.10+

# Linked Libraries Publishing - Implementation Guide

**Date:** November 5, 2025  
**Version:** 2.0.0 (Current Implementation)  
**Status:** ✅ Implemented & Active

---

## 🎯 Overview

The publishing system supports linked libraries with automatic structure detection and dual versioning modes.

**Implemented Features:**
- ✅ **Dual versioning modes** (Overwrite vs Versioning)
- ✅ **Linked library detection** (1 level deep - direct links only)
- ✅ **Auto structure extraction** (from file paths)
- ✅ **Relative path preservation** (no remapping needed)
- ✅ **Clean delivery** (no metadata in published folders)

**Future Features:**
- ⏳ Recursive scanning (requires opening nested .blend files)
- ⏳ Circular dependency validation
- ⏳ Deep library validation (orphan data, textures, etc.)

---

## 📐 Publishing Modes

### **Mode 1: Overwrite (Default)**
Always replaces existing file - ideal for iterative updates.

```
Source: G:/Assets/furniture/chair/Chair.blend

Publish to:
D:/Publish/furniture/chair/
├── textures/                ← Updated each publish
│   ├── BaseColor.png
│   └── Normal.png
└── Chair.blend              ← Same filename, always overwritten
```

**Use Cases:**
- Daily WIP updates
- Single "latest version" workflow
- Quick asset iterations

---

### **Mode 2: Versioning**
Creates incremental versions - ideal for milestone tracking.

```
Source: G:/Assets/furniture/chair/Chair.blend

Publish to:
D:/Publish/furniture/chair/
├── textures/                ← Shared (not versioned)
│   ├── BaseColor.png
│   └── Normal.png
├── Chair_v001.blend         ← Version 1 (milestone)
├── Chair_v002.blend         ← Version 2 (milestone)
└── Chair_v003.blend         ← Version 3 (latest)
```

**Use Cases:**
- Client deliveries with history
- Milestone tracking
- Rollback capability needed
- Archive important iterations

**Important:**
- Only `.blend` files are versioned
- Textures are shared (always updated, not versioned)
- Version numbers auto-increment (v001, v002, v003...)

---

## 🗂️ File Structure Examples

### **Example 1: Simple Asset (No Links)**

**Source:**
```
G:/MyAssets/
└── assets/
    └── furniture/
        └── chair/
            ├── raw/                ← Not published
            ├── versions/           ← Not published
            ├── textures/           ← Published
            │   ├── BaseColor.png
            │   └── Normal.png
            └── Chair.blend         ← Published
```

**Published (Overwrite Mode):**
```
D:/Publish/
└── furniture/
    └── chair/
        ├── textures/
        │   ├── BaseColor.png
        │   └── Normal.png
        └── Chair.blend
```

**Published (Versioning Mode):**
```
D:/Publish/
└── furniture/
    └── chair/
        ├── textures/
        │   ├── BaseColor.png
        │   └── Normal.png
        ├── Chair_v001.blend
        ├── Chair_v002.blend
        └── Chair_v003.blend
```

---

### **Example 2: Asset with Linked Libraries**

**Source:**
```
G:/MyAssets/
└── assets/
    ├── furniture/
    │   ├── chair/
    │   │   ├── textures/
    │   │   └── Chair.blend
    │   │
    │   └── table/
    │       ├── textures/
    │       └── Table.blend
    │
    ├── environment/
    │   └── wood_floor/
    │       ├── textures/
    │       └── WoodFloor.blend
    │
    └── sets/
        └── office/
            ├── textures/
            └── Office.blend        [CURRENT FILE]
                ├─→ //../../furniture/chair/Chair.blend
                ├─→ //../../furniture/table/Table.blend
                └─→ //../../environment/wood_floor/WoodFloor.blend
```

**Published (with "Include Linked Libraries" enabled):**
```
D:/Publish/
├── .publish_activity.log           ← Centralized log (root only)
│
├── furniture/
│   ├── chair/
│   │   ├── textures/
│   │   └── Chair.blend             ← Always overwrite (no versioning)
│   │
│   └── table/
│       ├── textures/
│       └── Table.blend             ← Always overwrite
│
├── environment/
│   └── wood_floor/
│       ├── textures/
│       └── WoodFloor.blend         ← Always overwrite
│
└── sets/
    └── office/
        ├── textures/
        └── Office_v001.blend       ← Versioned (if mode = Versioning)

Links preserved:
Office_v001.blend → //../../furniture/chair/Chair.blend (still works!)
```

**Key Points:**
- 🎯 **Master file** (Office.blend): Follows chosen mode (Overwrite or Versioning)
- 📚 **Linked libraries**: Always use Overwrite mode (no versioning)
- 🔗 **Relative paths**: Preserved automatically
- 📁 **Folder structure**: Maintained from source

---

## 🔧 Technical Implementation

### **1. PathResolver Class**

**Purpose:** Auto-detect folder structure and resolve publish paths

**Location:** `operators/publish.py`

```python
class PathResolver:
    def __init__(self, publish_root):
        self.publish_root = os.path.normpath(publish_root)
        self.master_root = None  # Auto-detected on first use
```

**Key Methods:**

#### `detect_master_root(current_file_path)`
Automatically detects the master root folder by searching for `assets/` subfolder.

**Algorithm:**
1. Start from current file location
2. Go up directories (max 5 levels)
3. Check if `assets/` subfolder exists at each level
4. If found → parent is master root
5. Cache result for reuse

**Example:**
```python
File: G:/MyProject/assets/furniture/chair/Chair.blend

Search path:
  chair/ → No assets/ subfolder
  furniture/ → No assets/ subfolder
  assets/ → Check parent (MyProject/)
  MyProject/ → Has assets/ subfolder? YES!

Master root: G:/MyProject/
```

#### `extract_structure_from_link(lib_filepath)`
Extracts publish folder structure from a linked library path.

**Example:**
```python
Input:
  Link: //../../furniture/chair/Chair.blend
  Resolved: G:/MyProject/assets/furniture/chair/Chair.blend

Output:
  {
    'structure': 'furniture/chair',           # Publish folder path
    'folder_name': 'chair',                   # Asset folder name
    'absolute': 'G:/.../Chair.blend',         # Absolute .blend path
    'textures_dir': 'G:/.../textures'         # Textures folder path
  }
```

**Logic:**
1. Resolve relative link to absolute path
2. Find master root
3. Find `assets/` folder
4. Extract path between `assets/` and file
5. Remove filename, keep folder structure

#### `get_publish_structure_current(current_file_path)`
Gets publish structure for the currently open file.

**Example:**
```python
Input:
  File: G:/MyProject/assets/sets/office/Office.blend
  Master root: G:/MyProject/
  Assets folder: G:/MyProject/assets/

Output:
  'sets/office'
```

---

### **2. LinkedLibraryScanner Class**

**Purpose:** Scan and collect linked libraries from current file

**Location:** `operators/publish.py`

```python
class LinkedLibraryScanner:
    def __init__(self, publish_root, max_depth=3):
        self.publish_root = publish_root
        self.max_depth = max_depth  # Currently only depth 1 supported
        self.visited = set()        # For circular dependency prevention
        self.libraries = []         # Collected library info
        self.path_resolver = PathResolver(publish_root)
```

**Key Method:**

#### `scan(current_depth=0)`
Scans linked libraries from currently open file.

**Process:**
1. Iterate `bpy.data.libraries` (Blender's linked libraries)
2. For each library:
   - Extract structure using `PathResolver`
   - Check if file exists
   - Check if textures folder exists
   - Add to libraries list
3. Return library info list

**Returns:**
```python
[
  {
    'structure': 'furniture/chair',      # Publish folder structure
    'folder_name': 'chair',              # Asset folder name
    'absolute': 'G:/Assets/.../Chair.blend',
    'textures_dir': 'G:/Assets/.../textures',
    'exists': True,                      # File exists check
    'has_textures': True,                # Textures folder exists
    'depth': 1,                          # Nesting level
    'library_name': 'Chair.blend'        # Library name in Blender
  },
  # ... more libraries
]
```

**Current Limitations:**
- ⚠️ Only scans **direct links** (1 level deep)
- ⚠️ No recursive scanning (would require opening each .blend file)
- ⚠️ Circular dependency detection not active
- ✅ Sufficient for most production workflows

---

### **3. Publishing Process**

**Location:** `operators/publish.py` - `ASSET_OT_Publish.execute()`

**Complete Workflow:**

```python
def execute(self, context):
    # === STEP 1: Setup ===
    publish_root = context.scene.publish_path
    mode = context.scene.publish_versioning_mode  # 'OVERWRITE' or 'VERSIONING'
    
    # Create PathResolver
    path_resolver = PathResolver(publish_root)
    
    # === STEP 2: Detect Master File Structure ===
    master_structure = path_resolver.get_publish_structure_current(bpy.data.filepath)
    # Example result: 'sets/office'
    
    master_target_folder = os.path.join(publish_root, master_structure)
    # Example: D:/Publish/sets/office/
    
    # === STEP 3: Scan Linked Libraries (if enabled) ===
    libraries_to_publish = []
    
    if context.scene.publish_include_libraries:
        scanner = LinkedLibraryScanner(publish_root)
        all_libraries = scanner.scan()
        
        # Filter only selected libraries
        for lib_info in all_libraries:
            if self.is_library_selected(lib_info, context):
                libraries_to_publish.append(lib_info)
    
    # === STEP 4: Publish Linked Libraries ===
    # Libraries are ALWAYS published in OVERWRITE mode (no versioning)
    for lib_info in libraries_to_publish:
        lib_target_folder = os.path.join(publish_root, lib_info['structure'])
        # Example: D:/Publish/furniture/chair/
        
        # Publish library (overwrite mode only)
        self.publish_library_overwrite(lib_info, lib_target_folder)
        # - Creates target folder
        # - Copies .blend file (cleaned)
        # - Copies used textures
    
    # === STEP 5: Publish Master File ===
    if mode == 'VERSIONING':
        # Create versioned file: Office_v001.blend, Office_v002.blend, etc.
        self.publish_master_versioned(master_target_folder)
    else:
        # Always use same filename: Office.blend (overwrite)
        self.publish_master_overwrite(master_target_folder)
    
    # === STEP 6: Copy Textures for Master File ===
    self.copy_textures(master_target_folder)
    
    # === STEP 7: Write Centralized Log ===
    self.write_publish_log(
        publish_path=publish_root,
        asset_path=bpy.data.filepath,
        target_path=master_target_path,
        texture_count=len(self.textures_to_copy),
        status="SUCCESS"
    )
    
    return {'FINISHED'}
```

---

### **4. Versioning Logic**

#### Version Number Detection

```python
def get_next_version_number(self, target_folder, base_filename):
    """
    Find next version number by scanning existing files.
    
    Args:
        target_folder: D:/Publish/sets/office/
        base_filename: Office.blend
    
    Returns: Next version number (int)
    """
    name, ext = os.path.splitext(base_filename)  # 'Office', '.blend'
    pattern = f"{name}_v*.blend"
    
    # Find all existing versioned files
    existing_files = glob.glob(os.path.join(target_folder, pattern))
    # Example: ['Office_v001.blend', 'Office_v002.blend']
    
    # Extract version numbers
    version_numbers = []
    for filepath in existing_files:
        match = re.search(r'_v(\d{3})\.blend$', filepath)
        if match:
            version_numbers.append(int(match.group(1)))
    
    # Return max + 1 (or 1 if none exist)
    return max(version_numbers) + 1 if version_numbers else 1
```

#### Filename Generation

```python
def get_version_filename(self, filename, version_number):
    """
    Generate versioned filename.
    
    Example:
        filename: Office.blend
        version_number: 3
        returns: Office_v003.blend
    """
    name, ext = os.path.splitext(filename)
    return f"{name}_v{version_number:03d}{ext}"
```

**Result:**
- Version 1: `Office_v001.blend`
- Version 2: `Office_v002.blend`
- Version 3: `Office_v003.blend`
- ...
- Version 99: `Office_v099.blend`

---

### **5. Logging System**

**Location:** Single centralized log file

**File:** `{publish_path}/.publish_activity.log`

**Format:**
```
[2025-11-05 14:30:22] PUBLISH | Asset: Chair | Path: D:/Publish/furniture/chair/Chair.blend | Source: G:/Assets/furniture/chair/Chair.blend | User: artist | Mode: Overwrite | Textures: 12 | Status: SUCCESS

[2025-11-05 15:20:45] PUBLISH | Asset: Office | Path: D:/Publish/sets/office/Office_v001.blend | Source: G:/Assets/sets/office/Office.blend | User: artist | Mode: Versioning | Textures: 8 | Status: SUCCESS

[2025-11-05 16:10:33] PUBLISH | Asset: Table | Path: D:/Publish/furniture/table/Table.blend | Source: G:/Assets/furniture/table/Table.blend | User: artist | Mode: Overwrite | Textures: 0 | Status: FAILED | Notes: Permission denied
```

**Fields:**
- `[Timestamp]`: Date and time of publish
- `Asset`: Asset name (from folder)
- `Path`: Full path to published file
- `Source`: Full path to original source file
- `User`: System username
- `Mode`: Overwrite or Versioning
- `Textures`: Number of textures copied
- `Status`: SUCCESS or FAILED
- `Notes`: Optional (for force publish or errors)

**Benefits:**
- ✅ Single source of truth
- ✅ Clean delivery (no logs in published folders)
- ✅ Easy to parse for detection
- ✅ Complete audit trail

---

## 🎓 User Workflow

### **Scenario 1: Simple Asset Publish**

```
1. Open Chair.blend
2. Select Publishing panel
3. Set Publish Path: D:/Publish/
4. Run "Check Publish Readiness"
5. Review validation results
6. Click "Publish File"
7. Result: D:/Publish/furniture/chair/Chair.blend created
```

---

### **Scenario 2: Versioned Publish**

```
1. Open Office.blend
2. Set Publish Path: D:/Publish/
3. Enable "Versioning Mode"
4. Run validation
5. Publish
6. Result: D:/Publish/sets/office/Office_v001.blend created

Later (after changes):
7. Open same Office.blend
8. Run validation
9. Publish again
10. Result: D:/Publish/sets/office/Office_v002.blend created
```

---

### **Scenario 3: Publish with Linked Libraries**

```
1. Open Office.blend (has 3 linked libraries)
2. Set Publish Path: D:/Publish/
3. Enable "Include Linked Libraries"
4. Panel shows:
   ✓ furniture/chair/Chair.blend
   ✓ furniture/table/Table.blend
   ✓ environment/wood_floor/WoodFloor.blend
5. Select which libraries to include (default: all)
6. Run validation
7. Publish
8. Result:
   - D:/Publish/furniture/chair/Chair.blend (overwrite)
   - D:/Publish/furniture/table/Table.blend (overwrite)
   - D:/Publish/environment/wood_floor/WoodFloor.blend (overwrite)
   - D:/Publish/sets/office/Office_v001.blend (versioned)
```

**Important:**
- 📚 Linked libraries always use Overwrite mode
- 🎯 Master file uses chosen mode (Overwrite or Versioning)
- 🔗 Relative links preserved automatically

---

## 🛡️ Safety Features

### **1. Published File Detection**

**Prevents recursive publishing:**
```
Opening: D:/Publish/sets/office/Office_v001.blend

Detection:
  1. Check filename pattern: Office_v001.blend → Versioned format ✓
  2. Check .publish_activity.log for this path
  3. Extract source path: G:/Assets/sets/office/Office.blend

Result:
  ⚠️ PUBLISHED FILE DETECTED
  Source: G:/Assets/sets/office/Office.blend
  Publish button: DISABLED
```

**User must open source file to publish again.**

---

### **2. Validation Requirements**

**Publish button disabled if:**
- ❌ File not saved
- ❌ Publish path not set
- ❌ Validation not run
- ❌ Published file detected
- ❌ Warnings exist (without Force Publish)

**See:** `PUBLISH_VALIDATION_REQUIREMENTS.md` for complete details

---

### **3. Force Publish System**

**Allows bypassing warnings (not errors):**

**Can bypass:**
- ⚠️ Missing textures
- ⚠️ External textures
- ⚠️ Orphan data
- ⚠️ Packed textures

**Cannot bypass:**
- ❌ File not saved (critical)
- ❌ Publish path not set (critical)
- ❌ Published file detected (prevents recursive versioning)

**See:** `PUBLISH_SYSTEM_V2.md` for complete details

---

## 📊 Scene Properties

**Publishing Settings:**
```python
bpy.types.Scene.publish_path: StringProperty
    # Target publish root folder

bpy.types.Scene.publish_versioning_mode: EnumProperty
    # 'OVERWRITE' or 'VERSIONING'

bpy.types.Scene.publish_include_libraries: BoolProperty
    # Include linked libraries in publish
```

**Validation State:**
```python
bpy.types.Scene.publish_check_done: BoolProperty
    # Validation completed flag

bpy.types.Scene.publish_is_published_file: BoolProperty
    # Current file is a published file

bpy.types.Scene.publish_source_path: StringProperty
    # Original source path (if published file)

bpy.types.Scene.publish_force: BoolProperty
    # Force publish mode (bypass warnings)
```

**Library Selection:**
```python
bpy.types.Scene.publish_library_selection: CollectionProperty
    # List of LibrarySelectionItem

class LibrarySelectionItem(PropertyGroup):
    name: StringProperty()           # Library name
    filepath: StringProperty()       # Absolute path
    structure: StringProperty()      # Publish structure (e.g., 'furniture/chair')
    selected: BoolProperty()         # Include in publish
    depth: IntProperty()             # Nesting level
    status: StringProperty()         # Validation status
    folder_name: StringProperty()    # Folder name
    has_textures: BoolProperty()     # Has textures folder
```

---

## 🧪 Testing Scenarios

### **Test 1: Simple Publish (No Links)**
```
✅ Open Chair.blend (no linked libraries)
✅ Set publish path
✅ Run validation → All green
✅ Publish → D:/Publish/furniture/chair/Chair.blend created
✅ Textures copied correctly
✅ Log entry created
```

### **Test 2: Versioned Publish**
```
✅ Open Office.blend
✅ Enable Versioning mode
✅ Publish → Office_v001.blend created
✅ Publish again → Office_v002.blend created
✅ Publish again → Office_v003.blend created
✅ All versions preserved
✅ Textures shared (not versioned)
```

### **Test 3: Publish with 1 Linked Library**
```
✅ Open Office.blend (links Chair.blend)
✅ Enable "Include Linked Libraries"
✅ Panel shows Chair.blend in list
✅ Publish
✅ Result:
   - D:/Publish/furniture/chair/Chair.blend (overwrite)
   - D:/Publish/sets/office/Office_v001.blend (versioned)
✅ Links still work in published file
```

### **Test 4: Published File Detection**
```
✅ Publish Office.blend → Office_v001.blend
✅ Close file
✅ Open D:/Publish/sets/office/Office_v001.blend
✅ Panel shows "PUBLISHED FILE DETECTED"
✅ Source path shown: G:/Assets/sets/office/Office.blend
✅ Publish button disabled
```

### **Test 5: Library Selection**
```
✅ Open Office.blend (links 3 libraries)
✅ Enable "Include Linked Libraries"
✅ Uncheck Chair.blend
✅ Keep Table.blend and WoodFloor.blend checked
✅ Publish
✅ Result: Only selected libraries published
```

---

## ⚠️ Known Limitations

### **1. Single-Level Scanning Only**
- Currently scans only **direct links** (1 level deep)
- Nested libraries (Chair.blend links Cushion.blend) not detected
- **Workaround:** Publish nested libraries separately first
- **Future:** Recursive scanning (requires opening files - slow)

### **2. No Circular Dependency Detection**
- System doesn't check for circular references
- Theoretically possible but rare in practice
- **Future:** Implement when recursive scanning is added

### **3. Libraries Always Overwrite**
- Linked libraries don't support versioning
- Always published in Overwrite mode
- **Reason:** Prevents version mismatches in complex scenes
- **Workaround:** Manually version library source files if needed

### **4. Structure Detection Requirements**
- Requires `assets/` folder in source structure
- Falls back to path extraction if not found
- **Best Practice:** Use standard folder structure

---

## 🎁 Benefits

### **For Artists:**
- ✅ Automatic structure detection (no manual setup)
- ✅ Linked libraries published together
- ✅ Relative paths preserved (no broken links)
- ✅ Choose versioning per project needs

### **For Production:**
- ✅ Clean delivery packages (no metadata)
- ✅ Complete audit trail (centralized log)
- ✅ Flexible versioning (Overwrite or Versioning)
- ✅ Batch library publishing

### **For Clients:**
- ✅ Professional deliverables
- ✅ No internal metadata exposed
- ✅ Ready-to-use packages
- ✅ No cleanup needed

---

## 🚀 Future Enhancements

### **Planned:**
- [ ] Recursive library scanning (2-3 levels deep)
- [ ] Circular dependency detection
- [ ] Deep library validation (orphan data, textures)
- [ ] Progress indicator for multi-library publish
- [ ] Library dependency graph visualization

### **Possible:**
- [ ] Parallel publishing (multiple libraries simultaneously)
- [ ] Incremental publishing (only changed files)
- [ ] Auto-remap absolute paths to relative
- [ ] Version diff viewer (compare v001 vs v002)
- [ ] Publish history viewer in panel

---

## 📝 Related Documentation

- **`PUBLISH_SYSTEM_V2.md`** - Complete publish system overview
- **`PUBLISH_VALIDATION_REQUIREMENTS.md`** - Validation workflow
- **`README.md`** - User guide and installation
- **`copilot-instructions.md`** - Development architecture

---

**Document Version:** 2.0  
**Last Updated:** November 5, 2025  
**Status:** ✅ Current Implementation (Accurate)

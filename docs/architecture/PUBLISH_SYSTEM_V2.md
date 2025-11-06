# Publish System v2.0 - Clean Delivery Implementation

## 🎯 Overview

Updated publish system with **clean client delivery**, **published file detection**, and **dual versioning modes**.

---

## 📋 Key Features

### 1. **Dual Versioning Modes**

The publish system supports two distinct modes for different workflows:

#### **Overwrite Mode**
Always replaces existing file with same name - ideal for iterative updates.

```
PublishPath/
├── .publish_activity.log        ← Centralized tracking
└── Chair/                        ← Asset folder
    ├── Chair.blend               ← Always updated (same filename)
    └── textures/
        ├── BaseColor.png
        └── Normal.png
```

**Use Cases:**
- Daily work-in-progress updates
- Single "latest version" workflow
- Quick asset updates without history

#### **Versioning Mode**
Creates incremental versioned files - ideal for milestone tracking.

```
PublishPath/
├── .publish_activity.log        ← Centralized tracking
└── Chair/                        ← Asset folder
    ├── Chair_v001.blend          ← Version 1
    ├── Chair_v002.blend          ← Version 2
    ├── Chair_v003.blend          ← Version 3 (latest)
    └── textures/                 ← Shared textures (not versioned)
        ├── BaseColor.png
        └── Normal.png
```

**Use Cases:**
- Client deliveries with history
- Milestone tracking
- Rollback capability needed
- Archive important iterations

**Important Notes:**
- Only `.blend` files are versioned
- Textures are shared in single `textures/` folder (always updated)
- Version numbers are auto-incremented (v001, v002, v003...)
- Both modes use same folder structure (only filename differs)

---

### 2. **Clean Published Folders**
Published folders are now **100% clean** - no internal metadata files.

```
PublishPath/
├── .publish_activity.log         ← Hidden file (publish root only)
└── Chair/                         ← CLEAN for client delivery
    ├── Chair_v001.blend
    ├── Chair_v002.blend
    └── textures/
```

**Benefits:**
- ✅ Ready to zip and send to client
- ✅ No internal company metadata exposed
- ✅ Professional delivery package
- ✅ No cleanup needed before delivery

---

### 3. **Centralized Activity Log**

**File:** `.publish_activity.log` (in publish root)

**Format:**
```
[2025-11-04 14:30:22] PUBLISH | Asset: Chair | Path: D:/Publish/Chair/Chair_v001.blend | Source: D:/Projects/Chair/Chair.blend | User: artist | Textures: 12 | Linked: 0 | Status: SUCCESS
[2025-11-04 15:20:45] PUBLISH | Asset: Table | Path: D:/Publish/Table/Table.blend | Source: D:/Projects/Table/Table.blend | User: artist | Textures: 8 | Linked: 2 | Status: SUCCESS (FORCED) | Notes: 2 warnings ignored
```

**Fields:**
- Timestamp
- Asset name
- Published path (full path including filename)
- Source path (link back to original)
- Username
- Texture count
- Linked libraries count
- Status (SUCCESS/FAILED)
- Notes (optional - for force publish)

**Versioning Mode Detection:**
- Overwrite mode: Path ends with `Chair.blend`
- Versioning mode: Path ends with `Chair_v001.blend`, `Chair_v002.blend`, etc.

---

### 4. **Published File Detection**

**Multi-Layer Detection System:**

#### Method 1: Filename Pattern Match
```python
# Detect versioned filename: Chair_v001.blend, Chair_v002.blend
filename = "Chair_v001.blend"
if re.match(r'.+_v\d{3}\.blend$', filename):
    # This is a versioned published file
```

#### Method 2: Log Parsing
```python
# Parse .publish_activity.log
# Search for current file path
# Extract source path if found
```

#### Method 3: Fallback Check
```python
# Check parent folder for log
# Handle nested structures
```

**Result:**
- ✅ Detects published files reliably
- ✅ Extracts source path for reference
- ✅ Works for both Overwrite and Versioning modes
- ✅ Works even if user changes publish path setting

---

### 5. **Force Publish System**

**UI States:**

#### State 1: Has Warnings + Force Unchecked
```
[Validation Results]
❌ 3 missing textures         [RED/ERROR icon]
❌ 2 external textures         [RED/ERROR icon]

[Ready Status]
❌ Warnings detected - Publish disabled

[ ] Force Publish (ignore all warnings)

[Publish Button]               [DISABLED/GREY]
```

#### State 2: Has Warnings + Force Checked
```
[Validation Results]
ℹ️ 3 missing textures          [INFO icon - not red]
ℹ️ 2 external textures          [INFO icon - not red]

[Ready Status]
✅ Ready to publish (FORCED)
⚠️ All warnings will be ignored
⚠️ You take full responsibility

[✓] Force Publish (ignore all warnings)

[Publish Button]               [ENABLED/ACTIVE]
```

---

### 5. **Published File Warning**

**When opening published file:**

```
⚠️ PUBLISHED FILE DETECTED
Source: G:/MyAssets/Kursi
This file is in the publish directory!

[ ] Block re-publish of published files

[If checked → Publish button DISABLED]
[If unchecked → Publish allowed with warning]
```

**Use Cases:**
- ✅ Prevent accidental re-publish (Kursi_v002 → Kursi_v002_v001)
- ✅ Allow intentional re-publish if needed
- ✅ Show source path for reference

---

## 🔧 Technical Implementation

### Modified Files:

1. **`operators/publish.py`**
   - Renamed log: `.publish_log.log` → `.publish_activity.log`
   - Enhanced log format with Path and Source fields
   - Removed per-asset history log (clean delivery)

2. **`operators/check_publish.py`**
   - Added `is_published_file()` method
   - Added `parse_log_for_path()` method
   - Multi-layer detection logic
   - New scene properties:
     - `publish_is_published_file`
     - `publish_source_path`
     - `publish_block_published_files`

3. **`panels/publish_panel.py`**
   - Published file warning box
   - Block re-publish checkbox
   - Force publish checkbox (always visible when warnings exist)
   - Dynamic validation icons (RED when not forced, INFO when forced)
   - Smart publish button disable logic:
     - No file/path → Disabled
     - Has warnings + no force → Disabled
     - Published file + block checked → Disabled
     - Otherwise → Enabled

---

## 🎓 Validation Categories

### 🚫 **Critical Errors** (Cannot Force)
1. File not saved
2. No publish path set

**These ALWAYS block publish!**

### ⚠️ **Warnings** (Can Force)
1. No textures folder
2. External textures
3. Missing textures
4. Packed textures
5. Orphan data

**Can be bypassed with Force Publish checkbox!**

### 📁 **Published File Detection** (User Choice)
- Default: Warning only (can still publish)
- If "Block re-publish" checked: Total block

---

## 🧪 Testing Scenarios

### Scenario 1: Clean Publish
```
1. Asset with all textures consolidated
2. Run Check → All green
3. Publish → Success
4. Check published folder → Clean (blend + textures only)
5. Check .publish_activity.log → Entry added
```

### Scenario 2: Force Publish with Warnings
```
1. Asset with 3 missing textures
2. Run Check → Red errors shown
3. Publish button → DISABLED (grey)
4. Check "Force Publish" → Button ENABLED
5. Publish → Success with notes "3 warnings ignored"
```

### Scenario 3: Published File Detection
```
1. Open G:/Publish/Kursi_v001/Kursi.blend
2. Run Check → "PUBLISHED FILE DETECTED" warning
3. Source shown: G:/MyAssets/Kursi
4. Check "Block re-publish" → Publish button DISABLED
5. Uncheck → Publish allowed
```

### Scenario 4: Client Delivery
```
1. Publish Kursi → G:/Publish/Kursi_v001/
2. Right-click folder → Send to → Compressed (zip)
3. Upload Kursi_v001.zip to client
4. Client extracts → Clean files, no metadata
```

---

## 📊 Publish Button States

| Condition | Button State |
|-----------|-------------|
| No file saved | ❌ Disabled |
| No publish path | ❌ Disabled |
| Validation not run | ✅ Enabled |
| Clean validation | ✅ Enabled |
| Warnings + No force | ❌ Disabled |
| Warnings + Force checked | ✅ Enabled |
| Published file + Block checked | ❌ Disabled |
| Published file + Block unchecked | ✅ Enabled |

---

## 🎯 Workflow Examples

### Production Workflow
```
1. Work on asset in G:/MyAssets/Kursi/
2. Consolidate textures
3. Run Check Publish
4. Publish to G:/Publish/ (versioned)
5. Zip G:/Publish/Kursi_v001/
6. Send to client
```

### Iterative Development
```
1. Work on v001, publish
2. Continue work, improve asset
3. Publish → Auto creates v002
4. Both versions preserved
5. Client gets latest version
```

### Emergency Force Publish
```
1. Asset has missing textures (deadline!)
2. Check Force Publish
3. Publish anyway (logged as FORCED)
4. Fix textures later, publish v002 clean
```

---

## 🔍 Detection Algorithm

```python
is_published_file(current_blend_path, publish_path_setting):
    # 1. Check folder pattern (AssetName_vXXX)
    if matches_version_pattern(current_folder):
        parent = get_parent_folder()
        if has_activity_log(parent):
            if log_contains(current_path):
                return True, source_path
    
    # 2. Check using publish path setting
    if publish_path_setting:
        if has_activity_log(publish_path_setting):
            if log_contains(current_path):
                return True, source_path
    
    # 3. Fallback: check parent
    if has_activity_log(parent_of_current):
        if log_contains(current_path):
            return True, source_path
    
    return False, None
```

---

## 🎁 Benefits Summary

### For Artists:
- ✅ Clear visual feedback (red errors → grey button)
- ✅ Force option for emergencies
- ✅ Published file detection prevents mistakes
- ✅ No confusion about what can be forced

### For Production:
- ✅ Clean delivery packages
- ✅ Complete activity tracking
- ✅ Source path linkage
- ✅ Forced publish logging

### For Clients:
- ✅ Clean professional deliverables
- ✅ No internal metadata
- ✅ Ready-to-use packages
- ✅ No cleanup needed

---

## 📝 Log Example

```log
[2025-10-29 10:30:15] PUBLISH | Asset: Chair_Modern | Path: G:/Publish/Chair_Modern_v001 | Source: G:/Assets/Chair_Modern | User: john | Mode: Versioning | Textures: 15 | Status: SUCCESS
[2025-10-29 11:45:22] PUBLISH | Asset: Table_Wood | Path: G:/Publish/Table_Wood_v001 | Source: G:/Assets/Table_Wood | User: jane | Mode: Versioning | Textures: 8 | Status: SUCCESS (FORCED) | Notes: 2 warnings ignored
[2025-10-29 14:20:33] PUBLISH | Asset: Sofa_Leather | Path: G:/Publish/Sofa_Leather | Source: G:/Assets/Sofa_Leather | User: john | Mode: Overwrite | Textures: 20 | Status: SUCCESS
[2025-10-29 15:10:45] PUBLISH | Asset: Lamp_Modern | Path: G:/Publish/Lamp_Modern_v001 | Source: G:/Assets/Lamp_Modern | User: jane | Mode: Versioning | Textures: 0 | Status: FAILED | Notes: Permission denied
```

---

## 🚀 Future Enhancements

Possible additions:
- [ ] "Open Source File" button when published file detected
- [ ] Publish history viewer (parse log, show in panel)
- [ ] Export log to CSV for reporting
- [ ] Auto-cleanup old versions (keep last N)
- [ ] Publish templates/presets

---

**Version:** 2.0  
**Date:** October 29, 2025  
**Status:** ✅ Implemented & Ready for Testing

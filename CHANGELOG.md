# Changelog

All notable changes to Blender Asset Management addon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.1] - 2025-11-23

### 🎯 Focus: Operation Scope Refinement

This release focuses on **operation scope management** - ensuring all file operations target only the current blend file, not external linked libraries. This prevents conflicts between packed textures and linked library workflows.

### ✨ Added

**Consolidate Textures - Enhanced Conflict Detection:**
- **Smart file comparison** - Detects identical files using modification time + file size matching
- **Batch conflict resolution** - Single action applies to all conflicts (Relink/Overwrite/Skip modes)
- **Optional unpacking** - Toggle to unpack embedded textures to textures/ folder during consolidate
- **Simplified UI** - Removed per-file action buttons, streamlined to batch operation

**Publish Dialog Improvements:**
- **Limited library list** - Shows max 4 linked libraries (was 10), rest shown as "... and X more"
- **Consistent target folder** - Shows parent folder name for include libraries (same as single publish)

### 🔧 Changed

**Operation Scope - Current Blend Only:**
- **File Management panel** - All texture statistics now ignore external linked images (`img.library` check)
- **Consolidate textures** - Only processes current file textures, skips library images
- **Cleanup unused textures** - Only checks current file usage, preserves library textures
- **Result**: External link images completely invisible to file operations

**Publishing System:**
- **Removed auto-unpack feature** - Packed textures now remain embedded during publish
- **Rationale**: Auto-unpacking modified source files, causing conflicts with linked library workflow
- **Alternative**: Use optional unpack toggle in Consolidate Textures operator instead

**Single Publish Structure:**
- **Added asset folder level** - Single publish now creates `publish/AssetName/AssetName.blend` structure
- **Consistent behavior** - Matches structure mirroring logic used for library publishing

### 🐛 Fixed

**Batch Rename - Suffix Placement:**
- Fixed suffix placement to be **before file extension** (was after)
- Example: `char_BaseColor.png` + `_4k` → `char_BaseColor_4k.png` ✅ (was `char_BaseColor.png_4k` ❌)

**Consolidate Textures - Conflict Detection:**
- Added file conflict detection to prevent unnecessary overwrites
- Uses modification time + size comparison (not hash - performance optimized)
- Auto-suggests "Relink Only" when source and destination are identical files

**Publish System - Recursive Texture Scanning:**
- Fixed texture folder scanning to support **nested subfolders** (wood/, metal/, etc)
- Preserves subfolder structure during publish (was flattening all textures to root)
- Example: `textures/wood/wood_BaseColor.png` → `publish/.../textures/wood/wood_BaseColor.png` ✅

### 🗑️ Removed

**Publish System:**
- Deleted `publish_auto_unpack` property (scene property)
- Removed auto-unpack UI section (checkbox + info labels)
- Removed auto-unpack execution loop (30 lines)
- Updated validation warnings: "will be auto-unpacked" → "will remain packed"

### 📋 Technical Changes

**Library Filtering Pattern:**
```python
# Applied to 3 operators:
for img in bpy.data.images:
    if img.library:
        continue  # Skip external link images
    # Process only current file images
```

**Conflict Detection Logic:**
```python
source_mtime = os.path.getmtime(source_path)
dest_mtime = os.path.getmtime(dest_path)
is_same_file = (source_mtime == dest_mtime and source_size == dest_size)
```

**Recursive Texture Scanning:**
```python
# OLD: Only scans root level
glob.glob(os.path.join(textures_dir, f"*.{ext}"))

# NEW: Recursive scan with os.walk
for root, dirs, files in os.walk(textures_dir):
    dirs[:] = [d for d in dirs if not d.startswith('.')]  # Skip .backup, .trash
    # ... scan all subfolders
    
# Preserve structure during copy
rel_path = os.path.relpath(tex_path, master_textures_dir)
target_tex = os.path.join(target_textures, rel_path)
os.makedirs(os.path.dirname(target_tex), exist_ok=True)
```

### 🔒 Safety & Workflow

- **Cleaner client delivery** - Published files keep packed textures as-is (no source file modification)
- **Focused operations** - File Management panel operations only affect current blend file
- **Conflict prevention** - Smart detection prevents accidental texture overwrites
- **Batch efficiency** - Single decision for all conflicts (faster workflow)

---

## [1.2.0] - 2025-11-20

### 🎯 Major Features

#### Published File Auto-Detection System
- **Auto-detection on file open** - No manual validation needed, instant detection when opening any .blend file
- **4-layer detection algorithm**:
  1. **File Pattern**: Detects `AssetName_v###.blend` naming convention
  2. **Folder Pattern**: Detects `AssetName_v###/` directory structure
  3. **Log Parsing**: Reads `.publish_activity.log` in publish path
  4. **Recursive Search**: Scans up to 5 parent directories for publish logs
- **Performance-optimized caching** - Prevents repeated I/O operations on panel redraws
- **App handler integration** - Auto-resets validation state on file load

#### Published Library Detection
- **Validates linked libraries** during pre-publish check
- **Recursive log parsing** - Searches library source paths in publish activity logs
- **Error reporting** - Shows which linked libraries are published files (prevents nested versioning)
- **Source path extraction** - Displays original source file location for published libraries

#### Enhanced UI/UX

**Clickable Source Paths:**
- All 5 panels now show **clickable source file paths**
- **Copy to clipboard** with single click (no need to manually type paths)
- **Enlarged buttons** (`scale_y=1.2`) for better visibility and accessibility
- Consistent pattern across Publishing, Versioning, File Management, Batch Rename, and Main panels

**Inline Warnings:**
- **Non-intrusive alerts** - Shows warnings without blocking entire UI
- **Contextual information** - Each panel displays relevant published file warnings
- **Disable operations** - Buttons automatically disabled when published file detected
- **Source file reference** - Always shows where the original file is located

### ✨ Added

**Core Detection:**
- New utility module: `utils/published_file_detector.py` (4-layer detection system)
- New function: `detect_published_file_status()` - Main file detection with recursive search
- New function: `detect_library_published_status()` - Library-specific detection
- New function: `parse_log_for_file()` - Extract Source field from PUBLISH and LINKED log entries
- New function: `update_published_file_cache()` - Cache detection results for performance

**Operators:**
- New operator: `ASSET_OT_CopySourcePath` - Copy source file path to clipboard
- New operator: `ASSET_OT_CopyLogPath` - Copy publish log path to clipboard
- Enhanced: `ASSET_OT_CheckPublish` - Now validates linked libraries for published file status
- Enhanced: `ASSET_OT_Publish` - Includes `'source'` field in published_libraries list

**UI Components:**
- All 5 panels now check published file status at draw time
- Clickable source path buttons in all panels (consistent UX)
- Inline warning system (per-row alerts instead of box-level)
- Auto-disable operators when published file detected

**App Handlers:**
- Enhanced: `reset_publish_validation_on_load()` - Now calls detection system on file open
- Auto-clears cached detection results on new file load

**Log Format:**
- Updated publish log format to include Source field for LINKED entries:
  ```
  └─ LINKED | Library: name | Structure: path | Path: published | Source: original
  ```

### 🔧 Changed

**Detection System:**
- Moved from 3-layer to **4-layer detection** (added recursive parent directory search)
- Detection now runs **automatically on file open** (no validation button needed)
- Parser now **skips old log entries** without Source field (backward compatibility)
- Cache attribute renamed: `_publish_detection_cached` (prevents repeated checks)

**UI Behavior:**
- Published file warnings now use **individual row alerts** (not box-level)
- Operators **disabled instead of hidden** when published file detected
- Removed early returns in panels - **always show UI**, just disable buttons
- Source path **always clickable** (better UX than plain text)

**Code Architecture:**
- Circular import prevention: Detection logic moved to `utils/` (not in `operators/`)
- Consistent import pattern: All panels import from `utils.published_file_detector`
- Scene properties for persistent state: `publish_is_published_file`, `publish_source_path`

### 🐛 Fixed

- **Library source path** - Fixed "LINKED_LIBRARY" hardcoded text, now shows actual source path
- **Parser accuracy** - Regex updated to correctly extract Source field: `\|\s*Source:\s*(.+?)(?:\s*\n|$)`
- **Old log compatibility** - Parser continues searching if Source field not found (doesn't fail on old entries)
- **Cache invalidation** - Detection cache properly cleared on file load (no stale results)
- **Panel redraw performance** - Caching prevents repeated I/O on every draw cycle

### 📚 Documentation

- Updated README.md:
  - Removed references to deleted `docs/` folder
  - Added v1.2.0 feature highlights (auto-detection, 4-layer system, clickable paths)
  - Updated "Work Safely" section with new detection methods
  - Added v2.0 PRO roadmap (nested libraries support)
  - Cleaned up support section (removed redundant links)
- Updated version footer: November 20, 2025
- Updated architecture diagram: Removed docs folder, kept .github/copilot-instructions.md

### 🗑️ Removed

- Deleted `docs/` folder (17 files) - Moved architecture guide to .github/copilot-instructions.md
- Removed Documentation section from README (redundant with inline links)
- Removed optional support links (ko-fi, forum) from README

### 🔒 Security & Safety

- **Total operator blocking** - All destructive operations disabled on published files
- **Prevents recursive versioning** - Cannot create v001_v001 scenarios
- **Source tracking** - Always know where published files came from
- **Library validation** - Catches published libraries before publish (prevents broken links)

---

## [1.0.0] - 2025-11-17

### 🎯 Initial Release

Complete asset management system for Blender 4.0+ with professional publishing workflow, texture optimization, and version control.

### ✨ Features

#### Publishing System
- **Pre-publish validation** - Checks texture folder, missing textures, external files, orphan data
- **Force Publish mode** - Bypass warnings (critical errors still block)
- **Automatic versioning** - Incremental numbering (v001, v002, v003...)
- **Overwrite mode** - Replace existing published file (default mode)
- **Clean delivery structure** - Organized folder hierarchy
- **Centralized logging** - `.publish_activity.log` in publish root
- **Linked library support** - Include/exclude libraries in publish
- **Structure mirroring** - Preserves folder hierarchy from master folder
- **External library detection** - Handles libraries on different drives
- **Texture consolidation** - Copies textures to publish directory

#### Scene Analysis & Statistics
- **Real-time metrics** - Object, material, texture counts
- **Library tracking** - Linked objects and node groups
- **Orphan data detection** - Unused data blocks
- **Deep scene analysis** - Multi-threaded scanning with progress bar
- **Report generation**:
  1. **Material Usage Report** - Grouped by source file (current file first, then linked libraries)
  2. **Texture Usage Report** - Grouped by source file (current file first, then linked libraries)
  3. **Texture Paths Report** - Current file sections first, [LINKED] sections at bottom
- **Dialog preview** - Shows report summary before opening full reports
- **Auto-save option** - Save reports to disk (opt-in via preferences)

#### High Poly Analysis
- **Configurable threshold** - Set triangle count limit in preferences
- **Modifier-aware counting** - Accurate tri count with modifiers
- **Isolate/select tools** - Focus on high-poly objects
- **Real-time display** - Shows tri count per object

#### Transform Safety
- **Detect unapplied transforms** - Rotation, scale issues
- **Extreme scale detection** - Find problematic scale values
- **Bulk apply** - Apply all transforms with one click
- **Safety checks** - Warns before modifying objects

#### Texture Optimization Tools

**Resolution Management:**
- **Downgrade resolution** - 4K → 2K → 1K → 512px step-down
- **Restore resolution** - Revert to previous resolution
- **Configurable limits** - Set max resolution in preferences
- **Validation check** - Detects textures exceeding threshold

**Format Conversion:**
- **PNG ↔ JPEG** conversion
- **Quality settings** - Per-format quality control
- **Transparency handling** - Smart alpha channel detection

**Optimization:**
- **Consolidate duplicates** - Merge identical textures
- **Cleanup unused** - Remove textures not in use
- **External texture consolidation** - Copy external files to project

**Statistics:**
- Total texture count
- External textures warning
- Unused textures tracking
- Packed textures detection

#### Material & Asset Optimization
- **Optimize linked objects** - Clean up linked data
- **Consolidate materials** - Merge duplicate materials
- **Merge duplicate textures** - Texture deduplication
- **Clear unused slots** - Remove empty material slots
- **Remove orphan data** - Deep cleanup

#### Batch Rename Tools
- **Find & Replace** - Multiple search-replace rules
- **Prefix/Suffix** - Add consistent naming
- **Auto-Correct Maps** - Smart texture type detection (BaseColor, Normal, Roughness, etc.)
- **Batch File Save** - Apply renames to disk
- **Pattern Support** - Flexible naming conventions

#### Versioning System
- **Auto-increment** - Automatic version numbering (v001, v002...)
- **Version descriptions** - Add notes to each version
- **Restore system** - Revert to any previous version
- **Version browser** - List all versions with creation dates
- **Safety checks** - Prevents versioning on unsaved files

#### Published File Protection
- **3-layer detection**:
  1. Folder pattern (`AssetName_v001/`)
  2. Log parsing (`.publish_activity.log`)
  3. Parent directory fallback
- **Total operator blocking** - Prevents all modifications on published files
- **Inline warnings** - Shows alerts in all relevant panels
- **Source file reference** - Displays original file location

### 🎨 UI/UX Improvements

**Publishing Panel:**
- **Disable 'Publish Linked Libraries' checkbox** until pre-publish check is run (prevents errors)
- **Default mode: OVERWRITE** - More intuitive for first-time users (versioning requires base file)
- **Validation required** - Must run check before publish (auto-resets on file load)
- **Force Publish toggle** - Bypass warnings with clear indication

**Scene Reports - Source File Grouping:**
- **Material Usage Report**: Current file first, then linked libraries (clear data ownership)
- **Texture Usage Report**: Current file first, then linked libraries (easier navigation)
- **Texture Paths Report**: Current file sections first, [LINKED] sections at bottom (consistent structure)

**Benefits:**
- ✅ Clear data ownership (current file vs libraries)
- ✅ Better workflow (check before link, overwrite before version)
- ✅ Easier navigation (grouped by source)
- ✅ Consistent structure across all 3 reports

**N-Panel Organization:**
- 5 main panels: Publishing, Versioning, File Management, Batch Rename, Main
- Collapsible sections with clear icons
- Contextual operators (show/hide based on state)
- Real-time status updates

### ⚙️ Addon Preferences

**Default Paths:**
- Default publish path (auto-loaded on file open)

**Validation Thresholds:**
- High poly threshold (default: 10,000 triangles) - Always checked
- Max texture resolution (1K/2K/4K/8K) - Optional check
- Enable/disable individual validation checks

**Validation Checks (Toggle):**
- Transform issues detection
- Empty material slots check
- Duplicate textures detection
- Duplicate materials detection
- Large texture resolution warning

**Scene Analysis:**
- Auto-save reports (opt-in, default: False)
- Report format: Plain text

### 🔧 Technical Details

**Architecture:**
- Modular separation: `operators/`, `panels/`, `utils/`
- Circular import prevention: Shared code in `utils/`
- Scene property-based state management
- App handlers for auto-reset on file load

**Performance:**
- Multi-threaded scene analysis
- Optimized texture scanning
- Efficient orphan data detection
- Caching for repeated operations

**Compatibility:**
- Blender 4.0+ (tested up to 4.5.1)
- Python 3.10+
- Cross-platform (Windows, macOS, Linux)

### 📚 Documentation

- Comprehensive README.md with:
  - Feature overview
  - Installation guide
  - Quick start tutorial
  - Publishing workflow diagram
  - Troubleshooting section
  - Architecture overview
- Architecture guide in `.github/copilot-instructions.md`
- Inline code documentation

### 🔒 Safety Features

- Published file protection (prevents recursive versioning)
- Validation required before publish
- Force publish safeguards (only bypasses warnings)
- Auto-reset on file load (prevents stale validation)
- Transform safety checks
- Orphan data warnings

---

## Version History

- **[1.2.0]** - 2025-11-20 - Published file auto-detection & UI improvements
- **[1.0.0]** - 2025-11-17 - Initial release with complete publishing system

---

## Links

- **Repository**: [github.com/alfajririzqi/asset_management](https://github.com/alfajririzqi/asset_management)
- **Releases**: [github.com/alfajririzqi/asset_management/releases](https://github.com/alfajririzqi/asset_management/releases)
- **Issues**: [github.com/alfajririzqi/asset_management/issues](https://github.com/alfajririzqi/asset_management/issues)
- **Discussions**: [github.com/alfajririzqi/asset_management/discussions](https://github.com/alfajririzqi/asset_management/discussions)

---

**License**: GPL-3.0  
**Author**: Rizqi Alfajri  
**Status**: Production-ready, 100% FREE forever

# Changelog

All notable changes to the Blender Asset Management addon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-04

### Added
- **Scene Analysis System**: Deep multi-threaded scene analysis with Material Usage and Texture Paths reports
  - Modal progress bar with percentage (0-100%)
  - 600px dialog popup showing report previews (15 lines each, skipping stats section)
  - Auto-switch to Scripting workspace with Text Editor pre-loaded
  - Multi-attempt Text Editor loading with verification (max 3 attempts)
  - Smart preview: Skip stats headers, show actual content (OBJECT lists, [FOUND] sections)

- **Transform Safety Auto-Workflow**: Intelligent transform application with modifier handling
  - Automatic detection of dangerous modifiers (MIRROR, ARRAY, BEVEL, etc.)
  - ARMATURE exclusion: Rigged objects completely skipped from processing
  - Auto-backup to `.temp` collection before applying transforms
  - View layer exclusion for backup collection (clean visibility management)
  - Sequential workflow: Backup → Apply Modifiers → Apply Transforms
  - Dialog explanation showing dangerous modifiers and workflow steps

- **High Poly Analysis**: Count high poly objects with configurable vertex threshold
  - Table column layout: [Select All | Isolate | Refresh] buttons
  - Equal-width aligned buttons for consistent UI
  - Hidden object count always visible (info label with ℹ icon)
  - Removed "Include Hidden" checkbox (analysis always uses view_layer.objects)

- **Transform Analysis**: Check objects with non-default transforms
  - Table column layout: [Select Issues | Apply | Refresh] buttons
  - Hidden object count info label
  - Integration with auto-workflow system

- **Publishing Versioning Mode**: Two publish modes for different workflows
  - **Overwrite Mode**: Always replaces existing file (e.g., `Chair.blend`)
  - **Versioning Mode**: Creates incremental versions (e.g., `Chair_v001.blend`, `Chair_v002.blend`)
  - UI toggle in Publishing panel for mode selection
  - Automatic version number detection (finds next available v###)
  - Shared textures folder (not versioned separately)

- **Texture File Size Display**: Enhanced texture information across the addon
  - **Publish Dialog**: Shows file sizes for texture previews (e.g., "BaseColor.png (2.4 MB)")
  - **Scene Analysis Reports**: Texture Paths report includes file sizes for FOUND and UNUSED textures
  - Smart formatting: Bytes, KB, or MB based on size
  - Helps estimate total publish size and identify oversized textures
  - Enables quick audit for texture optimization needs

### Changed
- **UI Improvements**: Consistent table column layouts across all analysis panels
  - Changed from `split(factor=0.65)` to `row(align=True)` for equal button widths
  - Integrated refresh button into action rows (no separate row)
  - Always-visible hidden count labels instead of toggleable checkbox

- **Collection Management**: View layer exclusion for `.temp` collection

- **Publish Panel Simplification**: Removed redundant validation status section
  - Eliminated confusing "Ready Status" box that duplicated publish button state
  - Streamlined workflow: Validation button → Results → Publish button
  - Clearer user flow with less UI clutter

- **Versioning Mode Logic**: Smart disabling based on master file existence
  - Versioning mode disabled if no published master exists yet
  - First publish must use Overwrite mode to create master
  - Tooltip explanation: "Versioning requires master file (publish with Overwrite first)"
  - Prevents logical errors and improves UX
  - Removed individual object `hide_set()` calls (caused RuntimeError)
  - Use `layer_collection.exclude = True` for cleaner hierarchy management
  - No redundant properties on backup objects

- **Publishing System**: Fixed versioning mode implementation
  - Previously versioning mode was defined in UI but ignored in execution
  - Now properly respects OVERWRITE vs VERSIONING mode selection
  - Both master file and linked libraries support versioning
  - Cleaner folder structure (no versioned folders, just versioned filenames)

### Fixed
- **Versioning Mode Bug**: Publishing always used overwrite mode regardless of UI selection
  - `publish_master_file()` now checks `publish_versioning_mode` property
  - `publish_linked_library()` now respects versioning mode
  - Proper incremental naming: `asset_v001.blend`, `asset_v002.blend`

- **Duplicate Texture Detection**: Fixed Windows case-insensitive filesystem issue
  - glob.glob() was finding same file twice (*.png and *.PNG)
  - Added deduplication: `all_files = list(set(all_files))`
  - Eliminated misleading duplicate textures in publish dialog

- **Text Editor Loading**: Multi-attempt loading with window redraw and verification
  - Fixed fallback warning appearing incorrectly
  - Ensured `space.text == data_usage_text` after workspace switch
  - Maximum 3 attempts with proper error handling

- **Icon Compatibility**: Changed 'LIGHTPROBE_GRID' to 'SETTINGS' for Blender 4.5.1 compatibility

- **Backup Object Hiding**: Removed `hide_set()` RuntimeError
  - Use only `hide_viewport` and `hide_render` properties
  - Collection-level exclusion handles visibility

### Documentation
- Moved development docs to organized structure:
  - `docs/architecture/`: System design documents (PUBLISH_SYSTEM_V2, etc.)
  - `docs/development/`: Implementation progress and technical fixes
  - `docs/guides/`: User-facing guides (Testing, Transform Safety)
- Created comprehensive Scene Analysis UI documentation
- Updated copilot-instructions.md with latest architecture patterns
- **Updated README.md**: New versioning mode examples with English naming (Chair, House, etc.)
- **All documentation now uses English examples** (Chair, House, Prop) instead of mixed languages

## [1.0.0] - 2025-10-30

### Added
- **Publishing System V2**: Production-ready publish workflow
  - Pre-publish validation with comprehensive checks
  - Force Publish mode (bypass warnings, block critical errors only)
  - Automatic versioning (v001, v002, etc.)
  - Clean delivery: Single `.publish_activity.log` in root
  - Published file protection (3-layer detection, total operator blocking)

- **Texture Management**: Complete texture optimization toolkit
  - Optimize textures (resolution, format)
  - Consolidate duplicate textures
  - Auto-correct texture mapping
  - Batch rename with patterns
  - Cleanup unused textures
  - Convert image formats (PNG ↔ JPEG)
  - Downgrade/restore resolution
  - Restore original formats

- **Version Control**: File versioning system
  - Create numbered versions with descriptions
  - Restore previous versions
  - Version history tracking

- **File Cleanup**: Scene optimization tools
  - Clear orphan data
  - Optimize materials
  - Optimize linked libraries

- **Published File Detection**: Multi-layer detection system
  - Folder pattern matching (`AssetName_v###`)
  - Log file parsing (`.publish_activity.log`)
  - Parent directory fallback
  - Session-based caching for performance

### Architecture
- **Modular Design**: Operators, Panels, Utils separation
  - `operators/`: Business logic (publish, versioning, optimization)
  - `panels/`: UI components (publish, versioning, file management, batch rename)
  - `utils/`: Shared utilities (published file detector)

- **Circular Import Prevention**: Shared code in `utils/` module
- **Scene Properties**: Persistent state management for validation results
- **App Handlers**: Auto-reset validation on file load

### Safety Features
- **Published File Protection**: 
  - Inline warnings in all panels
  - Total operator blocking (publish, versioning, all texture ops, batch rename)
  - Shows source file path reference

- **Force Publish Option A (Total Bypass)**:
  - Only 2 absolute blocks: File not saved, No publish path
  - All other checks = warnings (force-able)

- **Validation Required**: Must run before publish, auto-resets on load

### UI/UX
- **Consistent Warnings**: Individual row alerts (not box-level)
- **Validation Results**: Per-item colors (red for errors/warnings, green for pass)
- **Priority-based Button Disable**: Published file → Validation → Errors
- **Clean Panels**: Organized into Publishing, Versioning, File Management, Batch Rename

---

**Legend:**
- `Added`: New features
- `Changed`: Changes in existing functionality  
- `Deprecated`: Soon-to-be removed features
- `Removed`: Removed features
- `Fixed`: Bug fixes
- `Security`: Vulnerability fixes

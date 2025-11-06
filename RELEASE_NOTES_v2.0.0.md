# 🎨 Asset Management v2.0.0 - Production Ready

*November 4, 2025*

Production-ready Blender addon for asset publishing with dual versioning modes, scene analysis, and transform safety.

---

## ✨ Highlights

- 🚀 **Dual Versioning Modes**: Choose between Overwrite (daily updates) or Versioning (milestone tracking)
- 📊 **Deep Scene Analysis**: Multi-threaded scanning with Material Usage and Texture Paths reports
- 🛡️ **Transform Safety**: Auto-workflow with dangerous modifier detection and ARMATURE protection
- 🔒 **Published File Protection**: Prevents accidental edits to released assets (3-layer detection)
- 🎨 **Texture Optimization**: Batch resolution, format conversion, consolidation toolkit

---

## 🆕 What's New

### Publishing System
- **Versioning Mode** now works correctly (was broken - always used overwrite)
  - **Overwrite Mode**: `Chair.blend` (always same file, quick updates)
  - **Versioning Mode**: `Chair_v001.blend`, `Chair_v002.blend` (incremental milestones)
- Auto-increment version detection (finds next available v###)
- Clean folder structure (shared textures, versioned .blend files only)
- Both master file and linked libraries support versioning

### Scene Analysis
- Multi-threaded deep scanning (modal progress bar 0-100%)
- 600px dialog popup with report previews (15 lines each)
- Auto-switch to Scripting workspace with Text Editor pre-loaded
- Smart preview: Skips stats headers, shows actual content (OBJECT lists, [FOUND] sections)
- Multi-attempt loading with verification (max 3 attempts)

### Transform Safety Auto-Workflow
- Automatic detection of dangerous modifiers (MIRROR, ARRAY, BEVEL, etc.)
- **ARMATURE exclusion**: Rigged objects completely skipped from processing (safe!)
- Auto-backup to `.temp` collection before applying transforms
- View layer exclusion for backup collection (clean visibility)
- Sequential workflow: Backup → Apply Modifiers → Apply Transforms
- Dialog shows dangerous modifiers and workflow explanation

### High Poly & Transform Analysis
- Table column layouts with equal-width aligned buttons
- **[Select All | Isolate | Refresh]** for High Poly panel
- **[Select Issues | Apply | Refresh]** for Transform panel
- Always-visible hidden object count (info label with ℹ icon)
- Removed "Include Hidden" checkbox (analysis always uses view_layer.objects)

### UI/UX Improvements
- Consistent table column layouts across all panels
- Integrated refresh buttons into action rows (no separate row)
- Equal-width aligned buttons (changed from split to row)
- Individual row alerts (not box-level) for consistent warnings
- Cleaner visual hierarchy

---

## 🐛 Bug Fixes

- **CRITICAL:** Fixed versioning mode being ignored in publish execution
  - UI toggle existed but code always used overwrite mode
  - Now properly respects OVERWRITE vs VERSIONING selection
  - Both `publish_master_file()` and `publish_linked_library()` fixed
  
- **Fixed:** Text Editor not loading Scene_DataUsage after workspace switch
  - Multi-attempt loading with window redraw
  - Verification that correct text is loaded (max 3 attempts)
  
- **Fixed:** Icon compatibility for Blender 4.5.1
  - Changed 'LIGHTPROBE_GRID' → 'SETTINGS'
  
- **Fixed:** hide_set() RuntimeError with backup objects
  - Use only hide_viewport and hide_render properties
  - Collection-level exclusion handles visibility

---

## 📥 Installation

### Quick Install

1. **Download** `asset_management_v2.0.0.zip` below ⬇️
2. **Open Blender** → `Edit` → `Preferences` → `Add-ons`
3. **Click** `Install...` → Select downloaded ZIP
4. **Enable** "Asset Management" checkbox
5. **Access** from `N-panel` → `Asset Management` tab

### Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| **Blender** | 4.0+ | Tested on 4.0 - 4.5.1 |
| **Python** | 3.10+ | Bundled with Blender |
| **OS** | Any | Windows, macOS, Linux |

---

## 🔄 Upgrading from v1.x

### Migration Steps

1. **Disable** old addon in Preferences → Add-ons
2. **Restart** Blender
3. **Install** v2.0.0 ZIP (see Installation above)
4. **Re-enable** addon checkbox
5. **Test** publishing with new versioning mode toggle

### Breaking Changes

⚠️ **Versioning Mode Behavior Changed**
- **Before:** UI toggle existed but was ignored (always overwrite)
- **After:** Toggle actually works! Choose mode before publishing.

⚠️ **Published File Detection Enhanced**
- Now uses 3-layer detection (filename pattern, log parsing, fallback)
- More reliable prevention of recursive versioning

⚠️ **Validation Auto-Reset**
- Validation results now auto-reset on file load
- Must re-run "Check Publish Readiness" after opening file

### No Data Loss
- Your existing published files are **100% safe**
- No changes to folder structures
- All previous versions remain accessible

---

## 📚 Documentation

| Resource | Description |
|----------|-------------|
| **[README.md](README.md)** | Installation, usage guide, quick start |
| **[CHANGELOG.md](CHANGELOG.md)** | Full version history and changes |
| **[docs/architecture/](docs/architecture/)** | System design documents |
| **[docs/development/](docs/development/)** | Implementation notes |
| **[docs/guides/](docs/guides/)** | User tutorials (testing, transform safety) |

### Quick Links

- 📖 [Publishing Workflow Guide](README.md#-quick-start)
- 🔍 [Scene Analysis Tutorial](README.md#️⃣-scene-analysis)
- 🛡️ [Transform Safety Guide](docs/guides/TRANSFORM_SAFETY_IMPLEMENTATION.md)
- 🧪 [Testing Checklist](docs/guides/TESTING_CHECKLIST.md)

---

## 🎯 Key Features Overview

### Publishing Modes

```
OVERWRITE Mode:                    VERSIONING Mode:
PublishPath/Chair/                 PublishPath/Chair/
├── Chair.blend (updated)          ├── Chair_v001.blend
└── textures/                      ├── Chair_v002.blend
                                   ├── Chair_v003.blend
                                   └── textures/ (shared)
```

**When to use:**
- **Overwrite:** Daily WIP updates, single "latest" version
- **Versioning:** Client deliveries, milestones, rollback capability

### Validation System

| Check | Type | Force-able? |
|-------|------|-------------|
| File not saved | ❌ Critical | NO - Must fix |
| No publish path | ❌ Critical | NO - Must fix |
| Missing textures | ⚠️ Warning | YES - Force publish |
| External textures | ⚠️ Warning | YES - Force publish |
| Orphan data | ⚠️ Warning | YES - Force publish |

### Safety Features

- ✅ **Published file protection** - Total operator blocking
- ✅ **ARMATURE protection** - Rigged objects never touched
- ✅ **Auto-backup** - .temp collection before transforms
- ✅ **Validation required** - Must check before publish
- ✅ **Force publish option** - Bypass warnings (not errors)

---

## 🙏 Acknowledgments

- Built for the **Blender community** with ❤️
- Tested in **production environments** for reliability
- Inspired by **real-world pipeline needs**

---

## 📄 License

**GNU General Public License v3.0** - see [LICENSE](LICENSE)

- ✅ Free to use, modify, and distribute
- ✅ Source code must remain open
- ✅ Changes must be documented
- ℹ️ No warranty provided

---

## 🐛 Known Issues

None! This is a stable production release. 

If you find any bugs, please [report them](../../issues).

---

## 🔮 Roadmap (Future Versions)

Potential features being considered:

- 💡 Selection buttons in Scene Analysis dialog (per-object/material/texture)
- 📦 Batch publish multiple assets
- 🔗 Improved linked library dependency visualization
- 📊 Publish history browser
- ⚙️ Custom validation rules

Vote on features or suggest new ones in [Discussions](../../discussions)!

---

**Full Changelog**: [v1.7.5...v2.0.0](../../compare/v1.7.5...v2.0.0)

**Download Asset**: `asset_management_v2.0.0.zip` ⬇️

[🐛 Report Bug](../../issues) • [📖 Documentation](../../tree/main/docs) • [⭐ Star if helpful!](../../stargazers)

---

<div align="center">

**Made with ❤️ for Blender Artists**

*If this addon saves you time, consider starring the repo! ⭐*

</div>

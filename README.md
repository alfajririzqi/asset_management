<div align="center">

# 🎨 Blender Asset Management

### Professional Asset Publishing & Texture Tools — **100% FREE**

*Streamline your workflow with intelligent validation, texture optimization, and automatic versioning*

[![Blender](https://img.shields.io/badge/Blender-4.0+-orange?logo=blender&logoColor=white)](https://www.blender.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL--3.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-brightgreen)](https://github.com/alfajririzqi/asset_management/releases)
[![Free](https://img.shields.io/badge/💎-100%25_FREE-success)](https://github.com/alfajririzqi/asset_management)

[✨ Features](#-features) • [📥 Installation](#-installation) • [🚀 Quick Start](#-quick-start) • [📚 Documentation](#-documentation) • [💬 Support](#-support)

---

</div>

## 🌟 Why Asset Management?

Stop wasting time on manual asset publishing and texture cleanup. This addon automates your entire production workflow:

- ✅ **Prevent Mistakes**: Pre-publish validation catches errors before delivery
- ✅ **Save Time**: One-click publishing with automatic versioning
- ✅ **Optimize Assets**: Smart texture consolidation reduces file sizes
- ✅ **Stay Organized**: Clean folder structure and version tracking
- ✅ **Work Safely**: Published file protection prevents accidental edits

**Perfect for:** Freelancers, Asset Creators, Hobbyists, Small Studios

**Blender Asset Management** is a comprehensive addon designed for production workflows, offering intelligent analysis, automated optimization, and foolproof publishing. Perfect for studios, freelancers, and technical artists who demand reliability and safety.

---

## ✨ Features

### 1️⃣ Asset Management

<table>
<tr>
<td width="33%">

#### 📊 Statistics
- Real-time scene metrics
- Object, material, texture counts
- Library & node group tracking
- Orphan data detection
- Quick scene overview

</td>
<td width="33%">

#### 🔍 Analysis Tools
**High Poly Analysis**
- Configurable triangle threshold
- Modifier-aware counting
- Isolate/select high-poly objects
- Real-time tri count display

**Transform Check**
- Detect unapplied transforms
- Find extreme scale values
- Identify rotation issues
- Bulk apply with safety

</td>
<td width="33%">

#### ⚡ Optimization Tools
**Asset Optimization**
- Optimize linked objects
- Consolidate material duplicates
- Merge texture duplicates

**Cleanup Operations**
- Clear unused material slots
- Remove orphan data blocks
- Deep scene cleanup

</td>
</tr>
</table>

---

### 2️⃣ Batch Rename Texture Tools

- **Find & Replace**: Multiple search-replace rules
- **Prefix/Suffix**: Add consistent naming
- **Auto-Correct Maps**: Smart texture type detection
- **Batch File Save**: Apply renames to disk
- **Pattern Support**: Flexible naming conventions

---

### 3️⃣ File Management

**Texture Optimization:**
- Downgrade/restore resolution (2K → 1K → 512px...)
- Format conversion (PNG ↔ JPEG)
- Consolidate duplicate textures
- Cleanup unused textures from project

**Statistics Display:**
- Total texture count
- External textures warning
- Unused textures count
- Packed textures tracking

---

### 4️⃣ Versioning

- **Auto-Increment**: Automatic version numbering (v001, v002...)
- **Version Descriptions**: Add notes to each version
- **Restore System**: Revert to any previous version
- **Version Browser**: List all versions with dates
- **Safety Checks**: Prevents versioning published files

---

### 5️⃣ Publishing

**Pre-Publish Validation:**
- Texture folder verification
- Missing texture detection
- External texture warnings
- Orphan data checks
- Packed texture alerts

**Publishing Features:**
- Force Publish mode (bypass warnings)
- Automatic versioning (v001, v002...)
- Clean delivery structure
- Centralized logging (`.publish_activity.log`)
- Linked library support (optional)

**Linked Libraries:**
- Include/exclude in publish
- Validate library paths
- Deep copy library assets
- Texture consolidation for libraries

---

### 🛡️ Work Safely - Published File Protection

**3-Layer Detection System:**
1. **Folder Pattern**: Detects `AssetName_v###` naming
2. **Log Parsing**: Checks `.publish_activity.log`
3. **Parent Fallback**: Scans parent directories

**Protection Features:**
- ⛔ Blocks all operations on published files
- 🚫 Prevents recursive versioning (v001_v001)
- 📍 Shows source file path
- 🔒 Automatic detection on file open
- ⚡ Performance-optimized caching

**Disabled Operations When Published File Detected:**
- ❌ Publishing
- ❌ Versioning
- ❌ Texture optimization
- ❌ Batch rename
- ❌ All file modifications

---

## � Installation

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Blender** | 4.0+ | Tested on 4.0 - 4.5.1 |
| **Python** | 3.10+ | Bundled with Blender |
| **OS** | Any | Windows, macOS, Linux |

### Quick Install

1. **Download** the latest release from [Releases](../../releases) page
2. **Open Blender** → `Edit` → `Preferences` → `Add-ons`
3. **Click** `Install...` → Select downloaded ZIP file
4. **Enable** checkbox next to "Asset Management"
5. **Access** from `N-panel` → `Asset Management` tab

<details>
<summary><b>🔧 Alternative: Git Clone (for developers)</b></summary>

```bash
# Navigate to Blender addons directory
cd %APPDATA%\Blender Foundation\Blender\4.0\scripts\addons  # Windows
cd ~/Library/Application Support/Blender/4.0/scripts/addons # macOS

# Clone repository
git clone https://github.com/YOUR_USERNAME/blender-asset-management.git asset_management

# Restart Blender and enable addon
```

</details>

---

## � Quick Start

### 1️⃣ First-Time Setup

Open `N-panel` → **Asset Management** tab, then:

```
📂 Set Publish Path
   └─ Publishing Panel → "Publish Path" → Choose output directory

📁 Organize Asset Structure
   Chair/
   ├── Chair.blend
   └── textures/          ← Important: textures must be in this folder
       ├── BaseColor.png
       ├── Normal.png
       └── ...
```

### 2️⃣ Publishing Workflow

```mermaid
graph LR
    A[Check Readiness] --> B{Validation}
    B -->|Pass ✓| C[Choose Mode]
    C -->|Overwrite| D[Publish]
    C -->|Versioning| E[Publish]
    B -->|Warnings ⚠| F[Force Publish]
    B -->|Errors ✗| G[Fix Issues]
    G --> A
    D --> H[Published ✓]
    E --> H
    F --> H
```

**Steps:**

1. **Validate** → Click `Check Publish Readiness`
2. **Review** → Check validation results
   - 🟢 Green = Ready
   - 🔴 Red Warning = Force-able
   - 🔴 Red Error = Must fix
3. **Choose Mode**:
   - **Overwrite**: Always replaces existing file (for updates)
   - **Versioning**: Creates incremental versions (v001, v002...)
4. **Publish** → Click `Publish Asset` (or enable `Force Publish`)

**Output Examples:**

**Overwrite Mode:**
```
PublishPath/
└── Chair/
    ├── Chair.blend         ← Always updated (same filename)
    └── textures/
        ├── BaseColor.png
        └── Normal.png
```

**Versioning Mode:**
```
PublishPath/
└── Chair/
    ├── Chair_v001.blend    ← Version 1
    ├── Chair_v002.blend    ← Version 2
    ├── Chair_v003.blend    ← Latest version
    └── textures/           ← Shared textures folder
        ├── BaseColor.png
        └── Normal.png
```

> **Note:** Textures are always in a shared `textures/` folder, not versioned separately. Only `.blend` files are versioned.

### 3️⃣ Scene Analysis

**Deep Scan Your Project:**

1. Click `Analyze Scene Deeply` (High Poly panel)
2. Watch progress bar (multi-threaded)
3. Review **Dialog Popup**:
   - 📄 Material Usage Report preview
   - 📄 Texture Paths Report preview
4. Click `Switch to Scripting Workspace`
5. Full reports loaded in Text Editor

**Use Cases:**
- 🔍 Audit texture usage before publish
- 📊 Find linked library dependencies  
- 🧹 Identify missing/external files

### 4️⃣ Versioning Modes Explained

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Overwrite** | Always replaces `Chair.blend` | Quick updates, work-in-progress |
| **Versioning** | Creates `Chair_v001.blend`, `v002`, etc. | Milestone tracking, client deliveries |

**When to use Overwrite:**
- Daily updates to published assets
- Work-in-progress iterations
- Single "latest" version needed

**When to use Versioning:**
- Client deliveries (keep history)
- Milestone tracking
- Need rollback capability

---

## 🛡️ Safety Features

### Published File Protection

**The addon prevents editing published assets:**

```
⚠️ Published File Detected
   Source: D:/Projects/MyAsset/MyAsset.blend
   
   [All operators disabled]  ← Prevents recursive versioning
```

- 3-layer detection (folder pattern, log parsing, parent fallback)
- Inline warnings in all panels
- Total operator blocking
- Source file reference for context

### Smart Validation

| Check Type | Behavior |
|------------|----------|
| 🔴 **Critical Errors** | Must fix (file not saved, no publish path) |
| 🟡 **Warnings** | Force-able (missing textures, orphan data, etc.) |
| ✅ **Validation Required** | Auto-reset on file load |

**Force Publish** bypasses warnings but **never** critical errors.

---

## 📂 Architecture

<details>
<summary><b>🏗️ Project Structure</b></summary>

```
asset_management/
├── 📄 __init__.py                      # Addon registration
│
├── 📁 operators/                       # Business logic (18 operators)
│   ├── publish.py                     # Main publish with logging
│   ├── check_publish.py               # Pre-publish validation
│   ├── check_scene.py                 # Deep scene analysis
│   ├── check_transform.py             # Transform safety
│   ├── versioning.py                  # Version management
│   └── optimize_*.py                  # Texture optimization
│
├── 📁 panels/                          # UI components (5 panels)
│   ├── main_panel.py                  # Root panel
│   ├── publish_panel.py               # Publishing UI
│   ├── versioning_panel.py            # Version control UI
│   ├── file_management_panel.py       # Texture operations UI
│   └── batch_rename_panel.py          # Batch rename UI
│
├── 📁 utils/                           # Shared utilities
│   └── published_file_detector.py     # Multi-layer detection
│
├── 📁 docs/                            # Documentation
│   ├── architecture/                  # System design
│   ├── development/                   # Implementation notes
│   └── guides/                        # User tutorials
│
└── 📁 .github/
    └── copilot-instructions.md        # Architecture guide
```

**Design Principles:**
- ✅ Modular separation (operators/panels/utils)
- ✅ Circular import prevention (shared code in `utils/`)
- ✅ Scene property-based state management
- ✅ App handlers for auto-reset on file load

</details>



---

## 📚 Documentation

| Resource | Description |
|----------|-------------|
| **[CHANGELOG.md](CHANGELOG.md)** | Version history and updates |
| **[docs/](docs/)** | Comprehensive documentation |



### For Users
- 📖 [Testing Checklist](docs/guides/TESTING_CHECKLIST.md)
- 🛡️ [Transform Safety Guide](docs/guides/TRANSFORM_SAFETY_IMPLEMENTATION.md)

### For Developers
- 🏗️ [Publish System Design](docs/architecture/PUBLISH_SYSTEM_V2.md)
- 🔧 [Implementation Summary](docs/development/IMPLEMENTATION_SUMMARY.md)

---

## 🐛 Troubleshooting

<details>
<summary><b>Common Issues & Solutions</b></summary>

### Panels Not Showing
```
Problem: N-panel empty or "Asset Management" tab missing
Solution: Press F3 → Type "Reload Scripts" → Enter
```

### Validation Results Don't Reset
```
Problem: Old validation results persist after opening new file
Solution: Validation auto-resets on file load. If stuck, re-run "Check Publish Readiness"
```

### Published File Not Detected
```
Problem: Editing published file but no warning appears
Solutions:
  1. Check folder matches pattern: AssetName_v001, AssetName_v002, etc.
  2. Verify .publish_activity.log exists in publish root directory
  3. Reload file to clear detection cache
```

### Force Publish Still Blocked
```
Problem: Force Publish enabled but button still disabled
Reason: Only 2 absolute blocks exist (no bypasses):
  - File not saved → Save your .blend file
  - No publish path set → Set path in Publishing panel

All other checks are warnings that Force Publish bypasses.
```

### Script Errors After Update
```
Problem: Errors in console after updating addon
Solution: 
  1. Disable addon in Preferences
  2. Restart Blender
  3. Re-enable addon
```

Still stuck? [Open an issue](../../issues) with your Blender version and error log.

</details>

---

## 🤝 Contributing

Found a bug or have a feature request? **[Open an issue](../../issues)**!

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

### Reporting Issues

Please include:
- Blender version
- Steps to reproduce
- Expected vs actual behavior
- Screenshots/error logs (if applicable)

### Development

For architecture details and coding guidelines, see:
- **[docs/](docs/)** - Technical documentation

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see [LICENSE](LICENSE) file for details.

### Summary
- ✅ Free to use, modify, and distribute
- ✅ Source code must remain open
- ✅ Changes must be documented
- ℹ️ No warranty provided

---

## � Support

### 🐛 Found a Bug?
[Open an issue](https://github.com/alfajririzqi/asset_management/issues) with:
- Blender version
- Steps to reproduce
- Expected vs actual behavior

### 💡 Feature Requests
Share your ideas on [GitHub Discussions](https://github.com/alfajririzqi/asset_management/discussions)

### ⭐ Show Your Support
If this addon saves you time:
- ⭐ **Star this repo** on GitHub
- 📢 **Share** with fellow Blender artists
- 💬 **Leave feedback** on [Blender Artists Forum](https://blenderartists.org/)

### ☕ Support Development
This addon is **100% free** and always will be. If you'd like to support development:
- 💙 [Buy me a coffee](https://ko-fi.com/yourusername) *(optional link)*
- 🎓 Share tutorials/workflows using this addon
- 🤝 Contribute code or documentation

---

## 🗺️ Roadmap

### v1.0 (Current) ✅
- ✅ Complete publishing system with validation
- ✅ Texture optimization & consolidation tools
- ✅ Automatic version control
- ✅ Published file protection (3-layer detection)
- ✅ High-poly & transform analysis
- ✅ Material & asset optimization
- ✅ Batch rename with patterns

**Status:** Production-ready, 100% FREE forever

---

### v2.0 PRO (Planned - Optional Upgrade ~$15-19)

#### 🚀 Core Pro Features

**1. Batch Publishing System** ⭐⭐⭐⭐⭐
- Queue multiple assets for one-click publishing
- Background processing with progress tracking
- Publish presets (Game-ready, Archviz, Preview)
- Schedule overnight batch publishing
- Auto-retry failed items

**2. Smart Asset Library & Browser** ⭐⭐⭐⭐⭐
- Visual thumbnail browser for published assets
- Search by tags, type, date, project
- Drag-and-drop import to scene
- Track asset usage across projects
- Quick 360° preview rotation
- Favorite/bookmark system

**3. Template Publishing Workflows** ⭐⭐⭐⭐⭐
- Save/load client-specific publish profiles
- Pre-configured export standards:
  - Game Engine (2K textures, optimized mesh)
  - Archviz (4K textures, high-poly)
  - Web/AR (1K textures, decimated)
- Custom validation rules per template
- Share templates across projects

**4. Asset Health Dashboard** ⭐⭐⭐⭐
- Real-time quality score (0-100)
- Detect common issues before delivery:
  - High poly count warnings
  - Missing UV maps
  - Non-manifold geometry
  - Texture optimization opportunities
- One-click auto-fix suggestions
- Export validation reports (PDF/HTML)

**5. Material Library Manager** ⭐⭐⭐⭐
- Save materials with preview thumbnails
- Categorize by type (Metal, Wood, Fabric, etc.)
- Material versioning (update all instances)
- Export/import material packs
- Drag-and-drop application

**6. Multi-Format Export Hub** ⭐⭐⭐⭐
- One-click export to multiple formats:
  - FBX (Unity, Unreal Engine)
  - USD (Pixar pipeline)
  - GLTF/GLB (Web, AR/VR)
  - OBJ (Universal compatibility)
  - Alembic (VFX workflows)
- Per-format settings profiles
- Batch export entire collections

#### 📊 Additional Pro Features

**7. Asset Analytics & Reporting**
- Project statistics dashboard
- Generate client delivery reports (PDF)
- Asset thumbnails with technical specs
- Optimization summaries
- Export history tracking

**8. Automated Quality Control**
- N-gon detection with auto-fix
- Zero-area faces cleanup
- Normal map direction validation
- Naming convention enforcement
- Custom QC checklists

---

### Why Pro Features Are Worth It?

**Time Savings:**
- Batch Publishing: **2-3 hours saved per project**
- Asset Library: **Find & reuse assets in seconds** vs. hunting folders for 10+ minutes
- Templates: **Switch client standards instantly** vs. manual reconfiguration

**Quality Improvements:**
- Health Dashboard: **Catch errors before client delivery**
- Auto QC: **Professional output every time**
- Validation Reports: **Show clients you care about quality**

**ROI Calculation:**
```
Freelancer Rate:        $30/hour
Time Saved Per Project: 2-3 hours
Projects Per Year:      10-20

Annual Savings:         $600-1,800
Pro Version Cost:       $19 one-time

Break-even: First project! 🎉
```

---

### Development Timeline

**Phase 1 (Months 1-3):** Gather v1.0 user feedback  
**Phase 2 (Months 4-6):** Design Pro features based on demand  
**Phase 3 (Months 7-9):** Develop core Pro features (Batch, Library, Templates)  
**Phase 4 (Month 10-12):** Beta testing with early adopters  
**Phase 5 (Month 12+):** Pro version launch

**Note:** All v1.0 features remain **100% FREE forever**. Pro is an optional upgrade for power users who need advanced workflow automation.

---

## 🙏 Acknowledgments

- Built with ❤️ for the Blender community
- Inspired by real production pipeline workflows
- Thank you to all contributors and testers!

---

<div align="center">

**Free Forever • No Ads • No Watermarks**

Made by [Rizqi Alfajri](https://github.com/alfajririzqi) for Blender Artists Worldwide



⭐ **Star this repo** if it helps your workflow!

[Report Bug](../../issues) • [Request Feature](../../issues) • [Documentation](docs/)

---

**Version 2.0.0** • Last Updated: November 4, 2025 • Blender 4.0+

</div>

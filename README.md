<div align="center">

# 🎨 Blender Asset Management

### Professional Asset Publishing & Texture Tools — **100% FREE**

*Streamline your workflow with intelligent validation, texture optimization, and automatic versioning*

[![Blender](https://img.shields.io/badge/Blender-4.0+-orange?logo=blender&logoColor=white)](https://www.blender.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL--3.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.2.1-brightgreen)](https://github.com/alfajririzqi/asset_management/releases)
[![Free](https://img.shields.io/badge/💎-100%25_FREE-success)](https://github.com/alfajririzqi/asset_management)

[✨ Features](#-features) • [📥 Installation](#-installation) • [🚀 Quick Start](#-quick-start) • [💬 Support](#-support)

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
- Scan & validate library paths
- Deep copy library assets with textures
- Structure mirroring (preserves folder hierarchy)
- External library detection (different drives)
- ⚠️ **Limitation:** Only supports 1 level of nesting (link-in-link not supported)

---

### 🛡️ Work Safely - Published File Protection (NEW in v1.2.0)

**4-Layer Auto-Detection System:**
1. **File Pattern**: Detects `AssetName_v###.blend` naming
2. **Folder Pattern**: Detects `AssetName_v###/` directories
3. **Log Parsing**: Checks `.publish_activity.log` in publish path
4. **Recursive Search**: Scans up to 5 parent directories for logs

**Protection Features:**
- 🚀 **Auto-detection on file open** (no manual validation needed)
- ⛔ Blocks all operations on published files
- 🚫 Prevents recursive versioning (v001_v001)
- 📍 **Clickable source path** (copies to clipboard)
- 🔗 **Published library detection** (validates linked files)
- 🔒 Inline warnings in all 5 panels
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
└── 📁 .github/
    └── copilot-instructions.md        # Architecture guide for developers
```

**Design Principles:**
- ✅ Modular separation (operators/panels/utils)
- ✅ Circular import prevention (shared code in `utils/`)
- ✅ Scene property-based state management
- ✅ App handlers for auto-reset on file load

</details>



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
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Architecture guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

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

### ☕ Support Development
This addon is **100% free** and always will be. If you'd like to support development:
- 🎓 Share tutorials/workflows using this addon
- 🤝 Contribute code or documentation

---

## 🗺️ Roadmap

### v1.2.0 (Current) ✅
- ✅ Complete publishing system with validation
- ✅ Texture optimization & consolidation tools
- ✅ Automatic version control
- ✅ **NEW:** Auto-detection on file open (no validation needed)
- ✅ **NEW:** 4-layer published file detection (file/folder/log/recursive)
- ✅ **NEW:** Published library detection (validates linked files)
- ✅ **NEW:** Clickable source paths (copy to clipboard)
- ✅ **NEW:** Inline warnings in all 5 panels
- ✅ High-poly & transform analysis
- ✅ Material & asset optimization
- ✅ Batch rename with patterns
- ✅ Linked library support with structure mirroring

**Status:** Production-ready, 100% FREE forever

---

### v2.0 PRO (Planned - Optional Upgrade ~$15-19)

**Theme:** Automate Batch Operations for Large-Scale Projects

Pro version focuses on **batch automation** - transforming manual one-by-one workflows into powerful bulk operations. Perfect for freelancers and asset creators working with 10-50+ assets per project.

---

#### 🚀 Core Pro Features

**1. Batch Publishing System** ⭐⭐⭐⭐⭐

**What it does:**
- Queue multiple blend files for simultaneous publishing
- Background processing with real-time progress tracking
- Process entire project folders with one click
- Auto-retry failed publishes
- Success/failure summary report

**Use Case:**
```
Scenario: You finished 20 props for a game asset pack

v1.0 FREE (Manual):
• Open file 1 → Validate → Publish → Close
• Open file 2 → Validate → Publish → Close
• ... repeat 18 more times
• Time: 2-3 hours ⏰

v2.0 PRO (Batch):
• Select all 20 blend files
• Click "Batch Publish"
• Go make coffee ☕
• Come back to 20 published assets
• Time: 5 minutes setup + background processing 🚀

Time Saved: 2-3 hours per batch
```

---

**2. Batch Downgrade Texture** ⭐⭐⭐⭐⭐

**What it does:**
- Downgrade all textures in multiple files at once
- Select target resolution (4K → 2K → 1K → 512px)
- Process entire project folders
- Preview before/after file sizes
- Rollback option (restore original resolution)

**Use Case:**
```
Scenario: Client wants web-optimized version (1K textures) of 50 assets

v1.0 FREE (Manual):
• Open asset 1
• Select texture 1 → Downgrade → Save
• Select texture 2 → Downgrade → Save
• ... repeat for 4 textures per asset × 50 assets
• Time: 30-60 minutes ⏰

v2.0 PRO (Batch):
• Select all 50 blend files
• Choose "Downgrade to 1K"
• Click "Batch Process"
• All textures downgraded automatically
• Time: 2 minutes 🚀

Time Saved: 30-60 minutes per batch
File Size Reduction: 50-75% average
```

---

**3. Batch Convert Image Format** ⭐⭐⭐⭐⭐

**What it does:**
- Convert all textures to different formats in bulk
- Support for multiple formats:
  - **PNG** (lossless, transparency)
  - **JPEG** (compressed, smaller size)
  - **TIFF** (high-quality archival)
  - **TGA** (game engines like Unity/Unreal)
  - **EXR** (HDR workflows)
  - **WebP** (web optimization, smaller than PNG)
- Per-format quality settings
- Batch convert for different delivery targets

**Use Case:**
```
Scenario: Multi-platform delivery
• Unity needs TGA
• Unreal needs PNG
• Web needs WebP

v1.0 FREE (Not Support):
• Does not support convert any format except PNG and JPEG/JPG

v2.0 PRO (Batch):
• Select all project files
• Choose "Export Unity (TGA)"
• Choose "Export Unreal (PNG)"
• Choose "Export Web (WebP)"
• 3 clicks, all textures converted
• Time: 5 minutes 🚀

Time Saved: 45-90 minutes per multi-format delivery
```

---

**4. Nested Linked Libraries Support** ⭐⭐⭐⭐

**What it does:**
- Support for multi-level library dependencies (link-in-link)
- Automatic dependency tree resolution
- Recursive library scanning (unlimited depth)
- Smart publish order (dependencies first)
- Prevent circular dependency errors

**Current Limitation in v1.2.0 FREE:**
```
❌ Only 1 level supported:
   Master.blend → Library.blend ✅
   Master.blend → Library.blend → SubLibrary.blend ❌
```

**v2.0 PRO Solution:**
```
✅ Unlimited nesting:
   Master.blend
   └─ Character.blend
      └─ Body.blend
         └─ Head.blend (all published automatically!)

Auto-detects dependency chain:
1. Publish Head.blend first
2. Publish Body.blend (relink to published Head)
3. Publish Character.blend (relink to published Body)
4. Publish Master.blend (relink to published Character)
```

**Use Case:**
```
Scenario: Complex character rig with nested libraries

Structure:
• chr_hero.blend (master)
  ├─ chr_hero_body.blend (body mesh)
  │  └─ chr_hero_head.blend (head detail)
  └─ chr_hero_rig.blend (armature)
     └─ chr_hero_controls.blend (rig controls)

v1.2.0 FREE:
• ERROR: "Nested libraries not supported"
• Must manually flatten structure first
• Time: 1-2 hours restructuring ⏰

v2.0 PRO:
• Check "Include Linked Libraries"
• Addon auto-detects 5 files in dependency chain
• Click "Publish" → All 5 files published in correct order
• All internal paths relinked automatically
• Time: 2 minutes 🚀

Time Saved: 1-2 hours per complex asset
Reliability: 100% (no manual relink errors)
```

---

**5. Batch Cleanup Operations** ⭐⭐⭐⭐⭐

**What it does:**
- Run cleanup operations on multiple files simultaneously
- Operations included:
  - Clear orphan data (unused meshes, materials, images)
  - Remove unused material slots
  - Delete packed textures (if external exist)
  - Purge all unused data blocks
  - Optimize file sizes
- Before/after file size comparison
- Cleanup summary report

**Use Case:**
```
Scenario: Pre-delivery cleanup of 30 assets

v1.0 FREE (Manual):
• Open file 1
• Clear orphan data
• Remove unused slots
• Save → Close
• ... repeat 30 times
• Time: 1-2 hours ⏰

v2.0 PRO (Batch):
• Select all 30 blend files
• Choose cleanup operations
• Click "Batch Cleanup"
• All files optimized automatically
• Time: 3 minutes 🚀

Time Saved: 1-2 hours per batch
File Size Reduction: 30-50% average
Client Delivery: Cleaner, more professional
```

---

### 💰 Pro Version Value Proposition

**Total Time Saved Per Large Project:**
- Batch Publishing: 2-3 hours
- Batch Downgrade: 30-60 minutes
- Batch Convert: 45-90 minutes
- Nested Libraries: 1-2 hours
- Batch Cleanup: 1-2 hours

**Total: 5-9 hours saved per project** ⏰

**ROI Calculation:**
```
Freelancer Rate:        $30/hour
Time Saved:             5-9 hours per project
Value Per Project:      $150-270

Pro Version Cost:       $19 one-time
Break-even:             First project pays 8-14x! 🎉

Annual Savings (10 projects/year):
$1,500 - $2,700 in time saved
```

---

### 🎯 Why Batch Focus is Perfect

**1. Clear Value:** "v1.0 = manual, v2.0 = batch" (easy to understand)  
**2. Immediate ROI:** Hours saved from day one  
**3. Target Market Fit:** Freelancers handle 10-50+ assets per project  
**4. Low Learning Curve:** Same operations, just automated  
**5. Affordable:** $19 is lunch money vs. hours of manual work  

---

### 📅 Development Timeline

**Phase 1 (Months 1-3):** v1.0 user feedback & community building  
**Phase 2 (Months 4-6):** Design batch operation architecture  
**Phase 3 (Months 7-9):** Develop 4 core batch features  
**Phase 4 (Months 10-11):** Beta testing with power users  
**Phase 5 (Month 12):** Pro version launch + marketing  

**Estimated Development Time:** 3-4 weeks full-time coding

**Note:** All v1.0 features remain **100% FREE forever**. Pro is purely additive - no features removed or paywalled.

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

[Report Bug](../../issues) • [Request Feature](../../issues) • [Discussions](../../discussions)

---

**Version 1.2.1** • Last Updated: November 20, 2025 • Blender 4.0+

</div>

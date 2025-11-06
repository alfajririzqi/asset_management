# How to Create GitHub Release v2.0.0

## 📋 Prerequisites

✅ Repository pushed to GitHub  
✅ ZIP file created: `asset_management_v2.0.0.zip` (160 KB)  
✅ Release notes prepared: `RELEASE_NOTES_v2.0.0.md`

---

## 🚀 Step-by-Step Release Creation

### 1. Navigate to Releases Page

```
https://github.com/YOUR_USERNAME/blender-asset-management/releases
```

Or: Repository page → **Releases** (right sidebar) → **Draft a new release**

---

### 2. Create Release Tag

**Tag version:** `v2.0.0`

**Target:** `main` branch

**Release title:** `🎨 Asset Management v2.0.0 - Production Ready`

---

### 3. Copy Release Notes

Open `RELEASE_NOTES_v2.0.0.md` and **copy the entire content** (Ctrl+A, Ctrl+C).

Paste into the **"Describe this release"** text area.

**Preview** to check formatting looks good.

---

### 4. Upload Release Asset

Click **"Attach binaries by dropping them here or selecting them"**

**Upload:** `asset_management_v2.0.0.zip` (from parent directory)

**Result:** File will appear with download counter

---

### 5. Optional: Generate Changelog

Click **"Generate release notes"** button (GitHub auto-generates from commits)

**Then:** Merge auto-generated notes with your custom notes (if desired)

---

### 6. Set as Latest Release

✅ Check **"Set as the latest release"**

⬜ Leave **"This is a pre-release"** unchecked (this is production!)

---

### 7. Publish Release

Click **"Publish release"** button

**Result:**
- Release page created: `https://github.com/YOUR_USERNAME/blender-asset-management/releases/tag/v2.0.0`
- ZIP available for download
- Tag `v2.0.0` created in repository
- Notification sent to watchers (if any)

---

## 📸 Post-Release (Optional)

### Add Repository Topics

Go to repository main page → Click **⚙️ Settings icon** next to About

**Add topics:**
```
blender
addon
asset-management
texture-optimization
version-control
blender-4-0
python
production-ready
3d
pipeline
```

### Update Repository Description

**Short description:**
```
Production-ready Blender addon for asset management with publishing workflow, texture optimization, and version control
```

**Website (optional):**
```
https://github.com/YOUR_USERNAME/blender-asset-management
```

### Social Preview Image (Optional)

Create a 1280x640 banner image showing:
- Addon name + version
- Key features
- Blender logo

Upload in: Repository Settings → Social preview → Upload an image

---

## ✅ Verification Checklist

After publishing, verify:

- [ ] Release page loads correctly
- [ ] ZIP file downloads (test it!)
- [ ] Release notes formatting is good (no broken Markdown)
- [ ] Tag `v2.0.0` visible in repository tags
- [ ] Latest release badge updated
- [ ] ZIP file is installable in Blender (extract and test!)

---

## 🎯 Release Page URL Pattern

Your release will be at:
```
https://github.com/YOUR_USERNAME/blender-asset-management/releases/tag/v2.0.0
```

Direct ZIP download:
```
https://github.com/YOUR_USERNAME/blender-asset-management/releases/download/v2.0.0/asset_management_v2.0.0.zip
```

---

## 📢 Promote Your Release

After publishing, share on:

- **Blender Artists Forum**: https://blenderartists.org/
- **Reddit**: r/blender, r/blenderdev
- **BlenderNation**: Submit addon for review
- **Twitter/X**: Tag @blender, use #b3d #blenderaddon
- **Discord**: Blender Community servers

**Sample announcement:**

```
🎨 Asset Management v2.0.0 Released!

Production-ready Blender addon for asset publishing:
✅ Dual versioning modes (overwrite/incremental)
✅ Deep scene analysis with reports
✅ Transform safety with ARMATURE protection
✅ Texture optimization toolkit

Free & Open Source (GPL-3.0)
Download: [link to release]

#b3d #blender #addon
```

---

## 🔄 Future Releases

For subsequent releases (v2.0.1, v2.1.0, etc):

1. Update version in `__init__.py` → `bl_info["version"]`
2. Update `CHANGELOG.md` with new changes
3. Create new `RELEASE_NOTES_vX.X.X.md`
4. Create new ZIP with updated version number
5. Follow same release process above

---

## 🐛 If Something Goes Wrong

**Release has mistakes?**
- You can **Edit release** (top right on release page)
- Update description, add/remove files
- Cannot change tag name after publishing (must delete and recreate)

**Need to delete release?**
- Release page → **Delete** button (bottom)
- Tag will remain (delete separately if needed: `git push --delete origin v2.0.0`)

**ZIP file is wrong?**
- Edit release → Delete old ZIP → Upload new one
- Rename new ZIP to match version (important for consistency)

---

**Ready?** Go create that release! 🚀

Remember: Copy content from `RELEASE_NOTES_v2.0.0.md`, upload `asset_management_v2.0.0.zip`, and publish!

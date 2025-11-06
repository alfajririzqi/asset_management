# Testing Checklist - Linked Libraries Publishing v2.0

## 🚀 Quick Setup

### 1. Enable Addon
1. Open Blender 4.0+
2. Edit → Preferences → Add-ons
3. Install addon from ZIP or enable if installed
4. Check for errors in System Console (Window → Toggle System Console)

### 2. Prepare Test Environment
Create test structure:
```
D:/Test_Publish/          (publish target)
D:/Test_Assets/
├── sets/
│   └── rumah/
│       ├── rumah.blend
│       └── textures/
├── props/
│   └── meja/
│       ├── meja.blend
│       └── textures/
└── environment/
    ├── kayu/
    │   ├── kayu.blend
    │   └── textures/
    └── batu/
        ├── batu.blend
        └── textures/
```

---

## ✅ Test Scenarios

### **TEST 1: Basic Single File Publish** ⚪
**Goal:** Verify file-based versioning works

**Steps:**
1. Open `rumah.blend`
2. N-Panel → Asset Management → Publishing
3. Click "Run Pre-Publish Checks"
4. Set Publish Path: `D:/Test_Publish/`
5. Mode: Versioning
6. Click "Publish File"

**Expected Result:**
```
D:/Test_Publish/sets/rumah/
├── rumah.blend         (latest copy)
├── rumah_v001.blend    (versioned)
├── textures/
└── .publish_activity.log
```

**Verify:**
- [ ] Both files created (rumah.blend + rumah_v001.blend)
- [ ] Textures copied
- [ ] Log entry: `Version: .../rumah_v001.blend | Latest: .../rumah.blend`
- [ ] Console shows: "Published rumah (versioned)"

---

### **TEST 2: Version Increment** ⚪
**Goal:** Verify version numbering works

**Steps:**
1. Modify `rumah.blend` (add cube or change something)
2. Save file
3. Run validation again
4. Publish again

**Expected Result:**
```
D:/Test_Publish/sets/rumah/
├── rumah.blend         (latest - updated)
├── rumah_v001.blend    (old version)
├── rumah_v002.blend    (new version)
└── textures/
```

**Verify:**
- [ ] v002 created
- [ ] rumah.blend updated (same as v002)
- [ ] v001 unchanged
- [ ] Log has 2 entries

---

### **TEST 3: Linked Libraries (1 Level)** ⚪
**Goal:** Test basic library publishing

**Setup:**
1. Open `rumah.blend`
2. Link `kayu.blend`: File → Link → kayu.blend → Collection
3. Save `rumah.blend`

**Steps:**
1. Run validation
2. Enable "Publish Linked Libraries" ✅
3. Click "Scan & Validate Libraries"
4. Verify library shows in list: `kayu` (depth 1)
5. Publish

**Expected Result:**
```
D:/Test_Publish/
├── sets/rumah/
│   ├── rumah.blend
│   ├── rumah_v003.blend
│   └── textures/
└── environment/kayu/
    ├── kayu.blend       (overwritten, no version)
    └── textures/
```

**Verify:**
- [ ] Master file versioned (v003)
- [ ] Library file copied (NO versioning)
- [ ] Library textures copied
- [ ] Log shows LINKED entry: `└─ LINKED | Library: kayu | ...`
- [ ] Console: "Published rumah (versioned) + 1 libraries"

---

### **TEST 4: Nested Libraries (2-3 Levels)** ⚪
**Goal:** Test deep dependency tree

**Setup:**
1. `meja.blend` links `kayu.blend`
2. `rumah.blend` links `meja.blend` (which links `kayu.blend`)

**Steps:**
1. Open `rumah.blend`
2. Scan libraries
3. Verify list shows:
   - `meja` (depth 1)
   - `kayu` (depth 2) - indented

**Expected Result:**
- [ ] Both libraries detected
- [ ] Depth levels correct
- [ ] Both published to correct structure
- [ ] Log shows both LINKED entries

---

### **TEST 5: Circular Dependency Detection** ⚪
**Goal:** Prevent infinite loops

**Setup:**
1. `fileA.blend` links `fileB.blend`
2. `fileB.blend` links `fileA.blend` (circular!)

**Expected Result:**
- [ ] Validation shows error: "Circular dependency detected"
- [ ] Publish blocked
- [ ] Error count = 1

---

### **TEST 6: Force Publish with Warnings** ⚪
**Goal:** Test force publish bypass

**Setup:**
1. Open `rumah.blend`
2. Delete `textures/` folder
3. Run validation

**Steps:**
1. Check shows warning: "Textures folder missing"
2. Publish button disabled
3. Enable "Force Publish" ☑️
4. Publish button enabled
5. Click Publish

**Expected Result:**
- [ ] Publishes without textures
- [ ] Log: `Status: SUCCESS (FORCED)`
- [ ] Console warning shown

---

### **TEST 7: Published File Detection (NEW Pattern)** ⚪
**Goal:** Verify file-based pattern detected

**Steps:**
1. Close Blender
2. Open `D:/Test_Publish/sets/rumah/rumah_v001.blend`
3. N-Panel → Publishing
4. Run validation

**Expected Result:**
- [ ] Red warning: "🚫 PUBLISHED FILE DETECTED"
- [ ] Shows source path
- [ ] ALL operators disabled
- [ ] Publish button disabled
- [ ] Message: "Cannot publish from publish directory"

---

### **TEST 8: Published File Detection (OLD Pattern)** ⚪
**Goal:** Backward compatibility

**Setup:**
1. Manually create: `D:/Test_Publish/sets/rumah_v001/rumah.blend`
2. Create `.publish_activity.log` in parent with old format

**Expected Result:**
- [ ] Old pattern detected
- [ ] Same protection as new pattern

---

### **TEST 9: Library Selection (UI)** ⚪
**Goal:** Test selective publishing

**Setup:**
1. `rumah.blend` links `kayu.blend` AND `batu.blend`

**Steps:**
1. Scan libraries
2. Uncheck `batu` ☐
3. Keep `kayu` ☑️
4. Publish

**Expected Result:**
- [ ] Only `kayu` published
- [ ] `batu` skipped
- [ ] Log shows 1 LINKED entry (kayu only)

---

### **TEST 10: Select All Checkbox** ⚪
**Goal:** Test bulk selection

**Steps:**
1. Scan libraries (2+ libraries)
2. Click "Select All" ☐ (uncheck)
3. All libraries uncheck
4. Click "Select All" ☑️ (check)
5. All libraries check

**Expected Result:**
- [ ] Bulk toggle works
- [ ] All checkboxes sync

---

## 🐛 Common Issues & Fixes

### Issue: "Import error: bpy could not be resolved"
**Fix:** This is Pylance false positive. Ignore or disable Pylance for Blender projects.

### Issue: Addon won't enable
**Fix:** 
1. Check System Console for errors
2. Verify Python 3.10+ 
3. Check `bl_info` version matches Blender

### Issue: Libraries not detected
**Fix:**
1. Verify libraries are linked (not appended)
2. Check `bpy.data.libraries` is not empty
3. Verify relative paths: `//../../path/to/file.blend`

### Issue: Textures not copied
**Fix:**
1. Check `textures/` folder exists next to .blend file
2. Verify textures are referenced in materials
3. Check file permissions

---

## 📊 Performance Metrics

**Target:**
- Validation: < 1 second
- Single file publish: < 3 seconds
- Library scan (10 libs): < 2 seconds
- Publish with 5 libraries: < 10 seconds

---

## ✅ Final Validation

After all tests pass:
- [ ] No errors in System Console
- [ ] All operators work without crashes
- [ ] Published files are valid .blend files (can be opened)
- [ ] Textures are intact
- [ ] Logs are correctly formatted
- [ ] Version numbering is sequential

---

## 🎯 Ready for Production

Mark complete when:
- ✅ All 10 tests pass
- ✅ No critical bugs
- ✅ Documentation updated
- ✅ Copilot instructions updated (if needed)

**Testing Date:** ___________  
**Tested By:** ___________  
**Blender Version:** ___________  
**Result:** ⚪ PASS / ⚪ FAIL

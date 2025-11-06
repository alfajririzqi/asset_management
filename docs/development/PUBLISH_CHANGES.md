# Publish Operator - Texture Folder Handling

## 🔧 Problem yang Diselesaikan

**Issue:** "Texture folder not found" dikategorikan sebagai critical error (blocking), tidak ada opsi untuk force publish.

**User Impact:** User tidak bisa publish asset yang memang tidak memiliki textures (misalnya: procedural material, simple geometry untuk testing, dll).

---

## ✅ Solusi yang Diimplementasikan

### 1. **Downgrade ke Warning**
- "No textures folder" sekarang menjadi **WARNING** (bukan critical error)
- Bisa di-bypass dengan checkbox "Publish Anyway"
- Tetap memberikan informasi ke user bahwa asset akan publish tanpa textures

### 2. **Graceful Handling**
- Jika textures folder tidak ada, publish tetap berjalan
- Target textures folder tetap dibuat (untuk konsistensi struktur)
- Hanya blend file yang di-copy, textures di-skip
- Log mencatat "0 textures" dengan notes jika forced

### 3. **Improved UX**
- Panel menunjukkan "Textures folder missing (will publish without textures)" dengan icon INFO (bukan CANCEL)
- Validation message lebih informatif: "will be auto-created if needed"
- Force publish checkbox muncul saat ada warning ini

---

## 📋 Validation Categories (Updated)

### ❌ **Critical Errors** (Blocking - tidak bisa force)
1. **File not saved** - Harus save dulu
2. **No publish path** - Harus set publish path
3. **External textures** - Harus run Consolidate Textures dulu
4. **Missing textures** - Texture direferensi tapi file tidak ada

### ⚠️ **Warnings** (Bypassable dengan Force Publish)
1. **No textures folder** - Asset bisa tidak punya textures (procedural, etc.)
2. **Packed textures** - Akan di-skip saat publish
3. **Orphan data** - Akan di-purge saat publish

---

## 🎯 Use Cases yang Didukung

### ✅ Valid Publishing Scenarios

1. **Procedural Material Asset**
   ```
   MyAsset/
   ├── MyAsset.blend (hanya geometry + shader nodes)
   └── (no textures folder)
   ```
   → Force publish = OK, asset procedural tidak butuh textures

2. **Work in Progress Asset**
   ```
   MyAsset/
   ├── MyAsset.blend (masih development)
   └── (textures belum siap)
   ```
   → Force publish = OK, untuk backup/versioning purposes

3. **Simple Geometry**
   ```
   Cube_Highpoly/
   ├── Cube_Highpoly.blend (pure geometry)
   └── (no materials/textures)
   ```
   → Force publish = OK, asset memang tidak perlu textures

### ❌ Invalid Publishing Scenarios (Tetap Blocked)

1. **External Textures**
   ```
   MyAsset/
   ├── MyAsset.blend
   ├── textures/ (kosong atau partial)
   └── (textures di D:/TextureLibrary/)
   ```
   → Force publish = BLOCKED, harus consolidate dulu

2. **Missing Referenced Textures**
   ```
   MyAsset/
   ├── MyAsset.blend (reference ke Base_Color.png)
   └── textures/
       └── (Base_Color.png tidak ada)
   ```
   → Force publish = BLOCKED, texture hilang/corrupt

---

## 🔍 Technical Changes

### Modified Files

1. **`operators/check_publish.py`**
   ```python
   # BEFORE
   has_critical_errors = (not textures_exist or 
                         external_count > 0 or 
                         missing_count > 0)
   
   # AFTER
   has_critical_errors = (external_count > 0 or 
                         missing_count > 0)
   has_warnings = (not textures_exist or 
                  packed_count > 0 or 
                  orphan_count > 0)
   ```

2. **`operators/publish.py`**
   ```python
   # BEFORE
   if not os.path.exists(textures_dir):
       self.validation_errors.append("Textures folder not found")
       return False
   
   # AFTER
   if not os.path.exists(textures_dir):
       self.validation_warnings.append("Textures folder not found (will be auto-created if needed)")
       # Early return - skip texture validation
       return len(self.validation_errors) == 0
   ```

3. **`panels/publish_panel.py`**
   ```python
   # BEFORE
   col.label(text="Textures folder missing", icon='CANCEL')
   
   # AFTER
   col.label(text="Textures folder missing (will publish without textures)", icon='INFO')
   ```

### Execute Flow Update

```python
# Step 5: Copy textures (if textures folder exists and has files)
copied_count = 0
if os.path.exists(textures_dir) and self.textures_to_copy:
    # Copy textures
    for tex_path in self.textures_to_copy:
        shutil.copy2(tex_path, target_tex)
        copied_count += 1
elif not os.path.exists(textures_dir):
    self.report({'INFO'}, "No textures folder found - publishing without textures")
```

---

## 🧪 Testing Checklist

### Scenario 1: No Textures Folder + Force Publish
- [ ] Create asset without textures folder
- [ ] Run validation → Should show warning (not error)
- [ ] Force publish checkbox appears
- [ ] Enable force publish → Publish succeeds
- [ ] Check log: `0 textures | SUCCESS (FORCED) | 1 warnings ignored`

### Scenario 2: Empty Textures Folder
- [ ] Create empty textures folder
- [ ] Run validation → Should pass (0 textures)
- [ ] Publish → Succeeds with 0 textures copied

### Scenario 3: External Textures (Should Still Block)
- [ ] Use texture outside textures folder
- [ ] Run validation → Critical error
- [ ] Force publish checkbox should NOT appear
- [ ] Publish button disabled

### Scenario 4: Missing Referenced Texture (Should Still Block)
- [ ] Material references Base_Color.png
- [ ] File doesn't exist in textures/
- [ ] Run validation → Critical error
- [ ] Cannot force publish

---

## 📝 Log Examples

**Success without textures:**
```
2025-10-29 10:30:15 | ProceduralCube | username | Versioning | 0 | SUCCESS | 
```

**Forced publish without textures:**
```
2025-10-29 10:32:40 | SimpleGeo | username | Overwrite | 0 | SUCCESS (FORCED) | 1 warnings ignored
```

**Success with textures:**
```
2025-10-29 10:35:20 | Chair_Modern | username | Versioning | 15 | SUCCESS | 
```

---

## 🎓 Best Practices

### When to Force Publish
✅ **Safe to Force:**
- Asset memang tidak butuh textures (procedural/simple geo)
- Development/testing purposes
- Backup intermediate work

❌ **Jangan Force:**
- Ada external textures (consolidate dulu!)
- Ada missing textures (fix path dulu!)
- Production-ready asset harus complete

### Workflow Recommendation
1. **Development Phase:** Boleh force publish untuk backup
2. **Pre-Production:** Fix all warnings
3. **Production Ready:** Clean publish (no warnings/errors)

---

## 🔄 Backward Compatibility

✅ **Existing workflows tetap bekerja:**
- Asset dengan textures folder lengkap → Tidak ada perubahan
- Validation masih ketat untuk external/missing textures
- Publish confirmation dialog tetap ada
- Logging format sama

✅ **New flexibility:**
- Asset tanpa textures sekarang bisa publish
- User punya kontrol lebih (force option)
- Lebih jelas antara critical error vs warning

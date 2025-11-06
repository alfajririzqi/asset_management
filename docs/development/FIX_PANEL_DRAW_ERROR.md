# Fix: Panel Draw AttributeError

## Problem
```
AttributeError: Writing to ID classes in this context is not allowed: Scene, Scene datablock, error setting Scene.publish_is_published_file
```

**Root Cause**: Blender tidak mengizinkan modifikasi scene properties saat UI sedang di-render (di dalam `panel.draw()`).

## Solution

### Architecture Change
Pisahkan detection logic menjadi 2 fungsi:

#### 1. `detect_published_file_status(context)` - READ-ONLY
- **Safe untuk panel.draw()** ✅
- TIDAK menulis ke scene properties
- Hanya membaca cache yang sudah ada
- Jika cache kosong, run detection dan return hasil (tanpa menyimpan)

```python
# Safe to call from panels
is_published, source_path = detect_published_file_status(context)
```

#### 2. `update_published_file_cache(context, is_published, source_path)` - WRITE
- **Hanya untuk operators** (execute/invoke) ✅
- Menulis hasil detection ke scene properties
- Set cache flag untuk performa

```python
# Only call from operators
is_published, source_path = detect_published_file_status(context)
update_published_file_cache(context, is_published, source_path)
```

## Files Changed

### 1. `utils/published_file_detector.py`
- ✅ `detect_published_file_status()` - Removed ALL scene property writes
- ✅ Added `update_published_file_cache()` - New function for operators

### 2. `operators/check_publish.py`
- ✅ Updated to use both functions
- ✅ Removed `is_published_file()` method
- ✅ Now calls `update_published_file_cache()` after detection

### 3. `__init__.py`
- ✅ Fixed app handler to use `delattr()` instead of `del`

### 4. Panels (NO CHANGES NEEDED)
- ✅ `versioning_panel.py` - Already using correct function
- ✅ `file_management_panel.py` - Already using correct function
- ✅ `batch_rename_panel.py` - Already using correct function
- ✅ `publish_panel.py` - No import needed (uses scene properties directly)

## Testing Checklist

After reload addon in Blender:

- [ ] Open any file → Panels load without errors
- [ ] Versioning panel shows published file warning correctly
- [ ] File Management panel shows published file warning correctly
- [ ] Batch Rename panel shows published file warning correctly
- [ ] Run "Check Publish" → Cache is updated
- [ ] Open published file → All operations disabled
- [ ] Open source file → All operations enabled

## Technical Details

### Cache Behavior

**Before (BROKEN)**:
```python
# Panel.draw() tries to write → ERROR
context.scene.publish_is_published_file = True  # ❌ Not allowed in draw()
```

**After (FIXED)**:
```python
# Panel.draw() only reads
if hasattr(context.scene, '_publish_detection_cached'):
    return context.scene.publish_is_published_file, ...  # ✅ Read-only

# Operator execute() writes
update_published_file_cache(context, True, "/path/to/source")  # ✅ Allowed
```

### Performance Impact
**None** - Cache still works the same way:
1. First call: Run detection, return result (no cache write in panel)
2. Operator runs: Update cache
3. Subsequent panel draws: Use cached values

## Related Documentation
- See `.github/copilot-instructions.md` for full architecture
- Blender API: `bpy.types.Panel.draw()` is read-only context

---

**Fixed**: October 30, 2025  
**Blender Version**: 4.5+  
**Issue**: AttributeError when writing to scene properties in panel.draw()

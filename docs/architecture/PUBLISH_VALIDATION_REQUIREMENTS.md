# Publish Validation Requirements - Option A Implementation

## 🎯 Overview

Implemented **mandatory pre-publish validation** with auto-reset on file load for maximum safety.

---

## ✅ Key Features

### 1️⃣ **Auto-Reset on File Load**

**Behavior:**
- Every time file is opened/loaded → Validation resets
- User MUST run "Check Publish" again
- Prevents publishing with outdated validation

**Implementation:**
```python
@persistent
def reset_publish_validation_on_load(dummy):
    scene.publish_check_done = False
    scene.publish_is_published_file = False
    scene.publish_source_path = ""
    scene.publish_force = False
```

**Registered in:** `__init__.py` → `bpy.app.handlers.load_post`

---

### 2️⃣ **Mandatory Validation Check**

**Publish Button States:**

| Condition | Button State | Reason |
|-----------|-------------|---------|
| File not saved | ❌ Disabled | "File not saved" |
| No publish path | ❌ Disabled | "Publish path not set" |
| **Validation not run** | ❌ Disabled | **"Run validation check first"** |
| Published file detected | ❌ Disabled | "Cannot publish from publish directory" |
| Warnings without force | ❌ Disabled | "Enable Force Publish to continue" |
| All clear | ✅ Enabled | Ready to publish |

**Priority Order:**
1. File saved ✅
2. Path set ✅
3. **Validation run** ✅ ← NEW REQUIREMENT
4. Not published file ✅
5. Pass validation or force ✅

---

### 3️⃣ **Simplified Validation UI**

**Design Philosophy:**
- Removed redundant "Ready Status" section
- Focus on validation results and publish button state
- Publish button itself shows clear status

**Workflow:**
```
┌────────────────────────────────┐
│ [Run Pre-Publish Checks]       │ ← Step 1: Run validation
└────────────────────────────────┘

┌────────────────────────────────┐
│ 📋 Validation Results          │ ← Step 2: Review results
│ ✅ 12 textures found           │
│ ✅ All consolidated            │
│ ⚠ 2 orphan data blocks         │
└────────────────────────────────┘

┌────────────────────────────────┐
│ [Publish File]                 │ ← Step 3: Publish (enabled if ready)
│ Status: Ready to publish       │
└────────────────────────────────┘
```

**Removed (Redundant):**
- ❌ "Ready Status" box
- ❌ Intermediate "Fix errors before publishing" messages
- ❌ Duplicate validation state display

**Why Simplified:**
- Publish button already shows proper status
- Reduces UI clutter
- Less confusing for users
- Clear 3-step workflow: Check → Review → Publish

---

## 🔒 Safety Layers

### Layer 1: UI Button Disabled
```python
if not scene.publish_check_done:
    can_publish = False
    disable_reason = "Run validation check first"
```

### Layer 2: Operator Early Return
```python
def invoke(self, context, event):
    if not context.scene.publish_check_done:
        self.report({'ERROR'}, "Run 'Check Publish' first")
        return {'CANCELLED'}
```

### Layer 3: App Handler Reset
```python
@persistent
def reset_publish_validation_on_load(dummy):
    # Auto-reset on every file load
    context.scene.publish_check_done = False
```

---

## 🎬 User Workflow

### Normal Workflow:
```
1. Open file (Chair.blend)
   ↓
2. Validation auto-resets
   Panel shows: "⚠️ VALIDATION REQUIRED"
   Publish button: DISABLED
   ↓
3. Click "Run Pre-Publish Checks"
   ↓
4. Validation runs, results shown
   ↓
5. If pass or forced:
   Publish button: ENABLED
   ↓
6. Click "Publish File"
   ↓
7. Success!
```

### Re-open Same File:
```
1. Close Chair.blend
   ↓
2. Re-open Chair.blend
   ↓
3. Validation RESET (auto)
   Panel shows: "⚠️ VALIDATION REQUIRED"
   Publish button: DISABLED
   ↓
4. MUST run check again
   (File may have changed!)
```

### Published File Workflow:
```
1. Open G:/Publish/Chair_v001/Chair.blend
   ↓
2. Run validation check
   ↓
3. Detection: "🚫 PUBLISHED FILE DETECTED"
   Source shown: G:/MyAssets/Chair
   ↓
4. Publish button: PERMANENTLY DISABLED
   Reason: "Cannot publish from publish directory"
   ↓
5. User must open source file instead
```

---

## 🧪 Testing Scenarios

### Test 1: Fresh File Open
```
✅ Open file
✅ Panel shows "VALIDATION REQUIRED"
✅ Publish button disabled
✅ Info shows "Run validation check first"
✅ Can't click publish (grey)
```

### Test 2: After Running Check
```
✅ Click "Run Pre-Publish Checks"
✅ Validation results appear
✅ If clean: Publish button enabled
✅ If warnings: Show force checkbox
✅ Can publish (green)
```

### Test 3: Re-open File
```
✅ Save & close file
✅ Re-open same file
✅ Validation reset (back to required)
✅ Publish button disabled again
✅ Must run check again
```

### Test 4: Published File
```
✅ Open published file
✅ Run check
✅ "PUBLISHED FILE DETECTED" shown
✅ Publish button ALWAYS disabled
✅ No bypass option
```

### Test 5: Button Disable Reasons
```
✅ No file → "File not saved"
✅ No path → "Publish path not set"
✅ No check → "Run validation check first"
✅ Published file → "Cannot publish from publish directory"
✅ Warnings → "Enable Force Publish to continue"
```

---

## 🔧 Technical Implementation

### Modified Files:

**1. `__init__.py`**
```python
@persistent
def reset_publish_validation_on_load(dummy):
    """Reset validation on file load"""
    scene.publish_check_done = False
    scene.publish_is_published_file = False
    scene.publish_source_path = ""
    scene.publish_force = False

def register():
    # Register app handler
    bpy.app.handlers.load_post.append(reset_publish_validation_on_load)

def unregister():
    # Unregister app handler
    bpy.app.handlers.load_post.remove(reset_publish_validation_on_load)
```

**2. `panels/publish_panel.py`**
```python
# Warning when not checked
if not scene.publish_check_done:
    warning_box.label(text="⚠️ VALIDATION REQUIRED")
    # ... show warning message

# Button disable logic
if not scene.publish_check_done:
    can_publish = False
    disable_reason = "Run validation check first"

# Show disable reason
if not can_publish:
    layout.label(text=f"⚠️ {disable_reason}")
```

**3. `operators/publish.py`**
```python
def invoke(self, context, event):
    # Safety check: Require validation
    if not context.scene.publish_check_done:
        self.report({'ERROR'}, "Run 'Check Publish' first")
        return {'CANCELLED'}
    
    # Safety check: Block published files
    if context.scene.publish_is_published_file:
        self.report({'ERROR'}, "Cannot publish from publish directory")
        return {'CANCELLED'}
```

---

## 📊 Validation Reset Triggers

| Event | Reset? | Reason |
|-------|--------|--------|
| File opened/loaded | ✅ YES | File may have changed |
| File saved | ❌ NO | Don't interrupt workflow |
| Scene changed | ❌ NO | Keep validation |
| Addon reload | ✅ YES | Fresh state |
| New file created | ✅ YES | No validation yet |

**Note:** Only resets on file LOAD, not on save (per Option A recommendation)

---

## 🎁 Benefits

### For Artists:
- ✅ **Clear guidance** - Always know if check needed
- ✅ **Prevent mistakes** - Can't publish outdated validation
- ✅ **Visual feedback** - Big warning when not checked
- ✅ **Simple workflow** - Just run check before publish

### For Production:
- ✅ **Quality assurance** - Always validated before publish
- ✅ **No shortcuts** - Can't bypass check requirement
- ✅ **Audit trail** - Log shows all checks run
- ✅ **Consistent** - Same workflow for everyone

### For Safety:
- ✅ **Triple protection** - UI + Operator + Handler
- ✅ **Auto-reset** - Fresh validation every session
- ✅ **Published file block** - Prevents recursive versioning
- ✅ **Force awareness** - User explicitly enables bypass

---

## 🚫 What Users CANNOT Do

❌ Publish without running check (button disabled)
❌ Bypass validation requirement (operator blocks)
❌ Publish with old validation after re-open (auto-reset)
❌ Publish from published directory (total block)
❌ Ignore warnings without force checkbox (explicit choice)

---

## ✅ What Users CAN Do

✅ Run check multiple times (re-validate)
✅ Fix issues and re-check (iterative)
✅ Force publish warnings (explicit checkbox)
✅ See clear disable reasons (tooltips)
✅ Know validation status (visual indicators)

---

## 🎯 Success Criteria

**Validation is considered successful when:**
1. ✅ Check has been run (`publish_check_done = True`)
2. ✅ Not a published file (`publish_is_published_file = False`)
3. ✅ Either:
   - No warnings/errors, OR
   - Has warnings BUT force enabled

**Then:** Publish button enabled ✅

---

## 💡 Design Philosophy

**Option A (Implemented):**
- ✅ **Safety first** - Prevent mistakes through design
- ✅ **Balance** - Not too aggressive (no reset on save)
- ✅ **Clear** - Visual feedback at every step
- ✅ **Consistent** - Same rules for everyone
- ✅ **Flexible** - Force option for emergencies

**Not implemented:**
- ❌ Reset on save (too aggressive)
- ❌ Auto-check on panel open (performance concern)
- ❌ Validation age tracking (complexity)
- ❌ Manual reset button (auto-reset is clearer)

---

**Version:** 2.1  
**Date:** October 29, 2025  
**Status:** ✅ Implemented - Option A (Recommended)

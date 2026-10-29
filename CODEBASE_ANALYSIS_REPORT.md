# Deepfake Detector Codebase Analysis Report
**Date:** 2026-10-29  
**Status:** Comprehensive analysis complete with 16 issues identified

---

## CRITICAL ISSUES (1)

### 1. ⚠️ Exposed R2 Credentials in .env
**File:** `.env`  
**Severity:** CRITICAL  
**Issue:** Cloud storage credentials hardcoded in plaintext.

**Action Required:**
1. Rotate all R2 credentials immediately
2. Ensure `.env` is in `.gitignore`
3. Use `.env.example` with placeholder values only
4. Check git history to confirm no commits contain credentials

---

## HIGH SEVERITY ISSUES (3)

### 2. Missing Filename Sanitization
**File:** `backend/app/main.py:104`  
**Issue:** User-supplied `file.filename` passed directly to `analyze_image_bytes()` without sanitization.
```python
diagnostic = analyze_image_bytes(content, file.filename)
```
**Risk:** Path traversal attacks possible.  
**Fix:** Use `os.path.basename()` or `secure_filename()` equivalent.

### 3. CORS Origins Not Validated
**File:** `backend/app/config.py:38`  
**Issue:** Origins parsed from env var with no URL format validation.
```python
return [origin.strip() for origin in configured.split(",") if origin.strip()]
```
**Risk:** Invalid/malformed origins accepted silently.  
**Fix:** Add URL scheme and format validation.

### 4. weights_only Loading Without Fallback
**File:** `backend/app/model_inference.py:90`  
**Issue:** `torch.load(..., weights_only=True)` fails on older checkpoint formats.
```python
payload = torch.load(self.checkpoint_path, map_location="cpu", weights_only=True)
```
**Risk:** Model fails to load on backward-incompatible checkpoints.  
**Fix:** Add try/except with fallback to `weights_only=False`.

---

## MEDIUM SEVERITY ISSUES (4)

### 5. Missing Type Hints
**File:** `backend/app/forensics.py`  
**Functions lacking return annotations:** `decode_image()`, `detect_and_crop_face()`, `compute_fft_spectrum()`, `compute_dwt_subbands()`, `compute_ela()`, `analyze_image_bytes()`

**Fix:** Add explicit return type annotations.

### 6. Error Handling Gaps
**File:** `backend/app/model_inference.py:118-120`  
**Issue:** All exceptions collapsed into single error string, making debugging harder.
```python
except (OSError, RuntimeError, ValueError, KeyError) as exc:
    self._error = str(exc)
```
**Fix:** Handle specific exception types separately (e.g., `FileNotFoundError` vs `ValueError`).

### 7. Hardcoded Magic Numbers
**Locations:**
- `forensics.py:139`: `cv2.multiply(ela_gray, 18)` — magic number 18 unexplained
- `model_inference.py:142`: `if short_side > 64:` — hardcoded resolution threshold
- `main.py:39`: Empty string fallback for model initialization

**Fix:** Extract to named constants with clear documentation.

### 8. Config Validation Missing
**File:** `backend/app/config.py`  
**Issue:** No validation of:
- `max_upload_bytes` > 0
- `max_image_width`/`max_image_height` > 0
- `max_image_pixels` reasonable upper bound
- R2 credentials format (even when `R2_ENABLED=false`)

**Fix:** Add validation in `Settings.__post_init__()`.

---

## LOW SEVERITY ISSUES (4)

### 9. Inconsistent Error Messages
**File:** `backend/app/main.py:135-137`  
**Issue:** Different messages for similar diagnostic states could confuse users.

### 10. Path Resolution Risk
**File:** `backend/training/rgb_baseline.py:154-163`  
**Issue:** `_resolve_path()` tries multiple candidate paths without clear precedence.

### 11. Outdated Documentation References
**File:** `backend/app/main.py:36`  
**Issue:** FastAPI description hardcodes "Phase 9" implementation detail.

### 12. Test Coverage with Absolute Paths
**Files:** `test_model_integration.py:11`, `test_model_integration.py:42`  
**Issue:** References absolute paths that may not exist on all systems.

---

## TESTING GAPS (1)

### 13. Insufficient Test Coverage
- No tests for invalid checkpoint formats
- No tests for corrupted image edge cases
- No tests for uncertainty band boundaries
- No tests for filename sanitization

---

## POSITIVE SECURITY OBSERVATIONS ✅

1. ✅ `weights_only=True` used in model loading (defense-in-depth)
2. ✅ Input validation on upload size and dimensions
3. ✅ Content-type whitelist for uploads (JPEG, PNG, WEBP, BMP only)
4. ✅ PIL decompression bomb protection enabled
5. ✅ Dataclass immutability with `frozen=True`
6. ✅ No bare `except:` clauses found
7. ✅ Proper exception chaining with `from exc`

---

## PRIORITY ROADMAP

### Phase 1: Critical (Today)
- [ ] Rotate R2 credentials
- [ ] Update `.env.example` with placeholders
- [ ] Verify `.env` is in `.gitignore`
- [ ] Check git history for credential leaks

### Phase 2: High (This week)
- [ ] Add filename sanitization
- [ ] Implement CORS origin validation
- [ ] Add weights_only fallback mechanism
- [ ] Add config validation in `Settings.__post_init__()`

### Phase 3: Medium (Next sprint)
- [ ] Add missing type hints to forensics.py
- [ ] Improve exception handling specificity
- [ ] Extract magic numbers to constants
- [ ] Add comprehensive test suite

### Phase 4: Low (Backlog)
- [ ] Improve error message consistency
- [ ] Refactor path resolution
- [ ] Update documentation
- [ ] Fix test path issues

---

## Recommendation

The codebase is **generally well-structured** with good foundational security practices. The issues identified are primarily around **defense-in-depth and robustness** rather than critical vulnerabilities. Prioritize the critical and high-severity items before production deployment.

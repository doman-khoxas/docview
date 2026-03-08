# Logging & Crash Reporting — Coverage Matrix

This document maps every component's logging and error handling coverage to help identify gaps and ensure operational visibility.

---

## Logging Levels Used

| Level | Purpose | Examples |
|-------|---------|---------|
| `CRITICAL` | Fatal crash, app cannot continue | Unhandled exception in main loop |
| `ERROR` | Operation failed, user notified | File save failure, print failure |
| `WARNING` | Recoverable issue, degraded behavior | TOC load failure, missing icon |
| `INFO` | Key operational events | File open/save/close, search, redaction, compression |
| `DEBUG` | Detailed diagnostic info | Tool activation, undo push, cache hits, page rendering |

---

## Component Coverage Matrix

| Component | File | INFO | DEBUG | WARNING | ERROR | Notes |
|-----------|------|:----:|:-----:|:-------:|:-----:|-------|
| **Entry Point** | `main.py` | Start/end session, CLI args | — | — | CRITICAL crash | Crash report to file + stderr |
| **App Hub** | `app/app.py` | Open/save/print/redact | Tool, undo, cancel | — | Open/save/print failures | Central operation logging |
| **Document Manager** | `app/document_manager.py` | Open/close tabs | Already-open switch | — | — | Tab lifecycle tracking |
| **PDF Document** | `app/core/pdf_document.py` | Open/close/save/commit | — | — | — | Document lifecycle + save mode |
| **Annotation Model** | `app/core/annotation_model.py` | — | Commit per annotation | — | — | Per-annotation tracking |
| **Page Operations** | `app/core/page_operations.py` | Merge/split/rotate/delete/compress | Image skip during compress | — | — | All page-level ops tracked |
| **PDF Renderer** | `app/core/pdf_renderer.py` | — | — | — | — | Pure functions, errors propagate |
| **Viewport** | `app/ui/continuous_viewport.py` | — | Document load | — | — | Rendering diagnostics |
| **Search Panel** | `app/ui/search_panel.py` | Search query + results | — | — | — | Search audit trail |
| **Sidebar** | `app/ui/sidebar.py` | Page extraction | TOC load | TOC failure | Extract failure | Page management ops |
| **Toolbar** | `app/ui/toolbar.py` | Metadata strip | — | — | Compress/strip failure | Security operations |
| **Tools** | `app/tools/*.py` | — | — | — | — | Logged through app.push_undo |

---

## Error Handling Patterns

### Pattern 1: User-Facing Error (messagebox + log)
```python
try:
    doc.save()
except Exception as e:
    log_exception(logger, "Failed to save", e)
    messagebox.showerror("Error", f"Failed to save:\n{e}")
```
**Used in:** File open, save, save-as, print, extract, compress, metadata strip

### Pattern 2: Silent Recovery (log + continue)
```python
except Exception as e:
    logger.debug("Skipping image xref=%d: %s", xref, e)
    continue
```
**Used in:** Image compression, icon loading

### Pattern 3: Graceful Degradation (warn + fallback)
```python
try:
    toc = doc.doc.get_toc()
except Exception as e:
    logger.warning("Failed to load TOC: %s", e)
    toc = []
```
**Used in:** TOC loading, incremental save fallback

### Pattern 4: Crash Capture (critical + file)
```python
except Exception:
    logger.critical("FATAL CRASH")
    # Write crashlog.txt
```
**Used in:** main.py entry point only

---

## Log File Locations

| File | Location | Purpose |
|------|----------|---------|
| `docview.log` | `~/.pdf_editor/logs/docview.log` | Structured rotating log (5MB x 3) |
| `crashlog.txt` | Next to executable/script | Fatal crash reports (append-only) |

---

## Recommended Future Additions

| Component | Missing Coverage | Priority |
|-----------|-----------------|----------|
| **Tools (all)** | No per-tool creation logging | Medium — add DEBUG on annotation create |
| **PDF Renderer** | No render timing | Low — useful for performance profiling |
| **Properties Panel** | No property change logging | Low — useful for debugging annotation issues |
| **Overview Panel** | No grid/selection logging | Low |
| **Digital Signature** | Signing success/failure | High — security audit trail |
| **Recent Files** | No persistence failure logging | Low |

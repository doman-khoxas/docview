# Tools Module — `app/tools/`

The tools module implements the annotation tool system — a set of interactive drawing/editing tools that respond to mouse events on the PDF canvas.

---

## Architecture

All tools extend `BaseTool` (abstract base class) and implement three methods:
- `on_press(x, y)` — Mouse button down (page-relative canvas coords)
- `on_drag(x, y)` — Mouse move while pressed
- `on_release(x, y)` — Mouse button up (creates the annotation)

**Tool Lifecycle:**
1. User selects tool from toolbar → `app.set_tool("name")`
2. Tool instance cached in `app._tool_instances`
3. Mouse events on viewport delegated to active tool
4. Tool creates annotation dataclass on release
5. Annotation stored via `pdf_doc.add_pending_annotation()`
6. Undo entry pushed via `app.push_undo()`
7. Page re-rendered to show the new annotation

---

## `base_tool.py` — BaseTool

**Purpose:** Abstract base providing shared infrastructure for all tools.

| Property/Method | Description |
|-----------------|-------------|
| `viewport` | Access to the ContinuousViewport instance |
| `canvas` | Returns `_PageCanvasProxy` (offset-adjusted for page position) |
| `properties` | Access to PropertiesPanel (color, opacity, stroke settings) |
| `canvas_to_pdf(cx, cy)` | Convert page-relative canvas coords to `(page_num, pdf_x, pdf_y)` |
| `_clear_temp()` | Remove temporary preview canvas items |
| `_temp_items` | List of canvas item IDs for cleanup on release |

**Coordinate Flow:**
```
Screen event → viewport._on_press() → subtract page offset → tool.on_press(page_cx, page_cy)
                                                                        ↓
                                                        canvas_to_pdf_coords() → PDF space
```

---

## Tool Implementations

### `highlight_tool.py` — HighlightTool
- **Type:** Text-snapping highlight
- **Creates:** `HighlightAnnotation`
- **Behavior:** Drag to select area, snaps to actual text words via `page.get_text("words")`
- **Fallback:** If no text found, uses raw rectangle as a single quad
- **Properties Used:** `highlight_color`, `opacity`

### `line_tool.py` — LineTool
- **Type:** Single line stroke
- **Creates:** `LineAnnotation`
- **Behavior:** Draw line from start point to end point
- **Preview:** Dashed line during drag
- **Properties Used:** `stroke_color`, `opacity`, `border_width`

### `rect_tool.py` — RectTool
- **Type:** Rectangle shape
- **Creates:** `RectAnnotation`
- **Behavior:** Drag to define rectangle bounds
- **Preview:** Dashed rectangle during drag
- **Properties Used:** `stroke_color`, `fill_color`, `opacity`, `border_width`

### `circle_tool.py` — CircleTool
- **Type:** Ellipse/circle shape
- **Creates:** `CircleAnnotation`
- **Behavior:** Drag to define bounding box for ellipse
- **Preview:** Dashed oval during drag
- **Properties Used:** `stroke_color`, `fill_color`, `opacity`, `border_width`

### `freehand_tool.py` — FreehandTool
- **Type:** Ink/freehand drawing
- **Creates:** `InkAnnotation`
- **Behavior:** Captures mouse path with point decimation (`MIN_DISTANCE=3px`)
- **Preview:** Smooth polyline during draw
- **Properties Used:** `stroke_color`, `opacity`, `border_width`

### `text_tool.py` — TextTool
- **Type:** Click-to-place text
- **Creates:** `FreetextAnnotation`
- **Behavior:** Click location → opens `TextInputDialog` → places text at click point
- **Properties Used:** `text_color`, `font_size`, `opacity`

### `redact_tool.py` — RedactTool
- **Type:** Redaction rectangle
- **Creates:** `RedactAnnotation`
- **Behavior:** Drag to define redaction area (displayed as red striped overlay)
- **Important:** Redactions are NOT applied on creation — user must explicitly apply via toolbar
- **Preview:** Red stippled rectangle during drag

### `image_tool.py` — ImageTool
- **Type:** Image embedding
- **Creates:** `ImageAnnotation`
- **Behavior:** Click → file picker → drag to place image at selected rectangle
- **Properties Used:** None (image from file)

### `select_tool.py` — SelectTool
- **Type:** Selection/move/delete
- **Creates:** Nothing (modifies existing annotations)
- **Behavior:** Click to select annotation, drag to move, Delete key to remove
- **Special:** Has `delete_selected()` method bound to Delete key

### `hand_tool.py` — HandTool
- **Type:** Navigation/panning
- **Creates:** Nothing
- **Behavior:** Drag to pan the viewport (uses canvas `scan_mark`/`scan_dragto`)
- **Cursor:** Changes to "fleur" (move cursor) on press

---

## Logging Coverage

Tools currently have no direct logging. Key operations are logged through:
- `app.push_undo()` — logs annotation type and page (DEBUG)
- `pdf_document.add_pending_annotation()` — marks document as modified
- `viewport.render_current_page()` — triggers re-render

**Recommendation:** Add DEBUG-level logging to each tool's `on_release` for annotation creation tracking.

---

## Error Handling

- Tools generally assume a document is open (guard checks in viewport event handlers)
- `HighlightTool` handles empty text selection gracefully (falls back to raw rectangle)
- `ImageTool` catches file dialog cancellation
- `TextTool` handles dialog cancellation (empty result)
- `SelectTool` handles no-annotation-under-cursor silently

# 2026-03-19 Phase 7 Roadmap — Frontend
**Target:** Day 4–5  
**Status:** Complete

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md` — canonical project structure and Definition of Done  
- `aiDocs/prd.md §Chat UI` — UI requirements and disclaimer wording  
- `aiDocs/architecture.md §SSE Event Protocol` — all event types the JS client must handle

---

## Goal
A functional, calm single-page chat UI that consumes the SSE stream correctly. No build system — vanilla HTML/CSS/JS only.

> **No automated tests for this phase.** The phase gate is a manual browser checklist verified in Chrome before proceeding to Phase 8.

---

## Checklist

**`frontend/index.html`**
- [x] Persistent disclaimer banner: *"This tool is not a substitute for professional mental health care."*
- [x] Scrollable message list area
- [x] Text input field + Send button
- [x] Links to `style.css` and `app.js`

**`frontend/style.css`**
- [x] Soft, accessible color palette (blues/greens/greys)
- [x] User bubble — right-aligned; agent bubble — left-aligned
- [x] Tool badge chips — small pill label per tool used
- [x] Crisis card — red/amber border, clear resource link styling
- [x] Loading spinner animation
- [x] Auto-scroll anchored to bottom of message list

**`frontend/app.js`**
- [x] Generate `session_id` (UUID v4) on page load
- [x] `sendMessage(text)` → `POST /chat` → `fetch` + `ReadableStream` line-by-line parse
- [x] Append `token` chunks to current agent bubble in real time
- [x] Add tool badge chip on `tool_use` event
- [x] Render crisis card on `crisis` event (distinct style + resource links as clickable text)
- [x] Show spinner while waiting; hide on `done` or `error`
- [x] Disable input + Send button during active stream; re-enable on completion
- [x] Auto-scroll to newest message after each update
- [x] Display readable error message on `error` event — no crashed/blank UI

---

## Key Files Created
```
frontend/index.html
frontend/style.css
frontend/app.js
```

---

## Phase Gate — Manual Browser Checklist
Start the server (`uvicorn backend.main:app --reload --port 8000`), open `http://localhost:8000` in Chrome, and verify each item before marking done:

- [ ] Disclaimer banner is visible and never disappears on scroll
- [ ] Typing a message and pressing Enter or Send appends user bubble immediately
- [ ] Agent response streams token-by-token — not a single delayed block
- [ ] A RAG question shows a tool badge labeled `rag_search`
- [ ] A math question shows a tool badge labeled `calculator`
- [ ] A crisis keyword message shows the crisis card with red/amber styling and resource links
- [ ] A follow-up question correctly references the previous turn
- [ ] An `error` event displays a readable message — UI does not crash or go blank

> **Note:** These 8 items require manual verification in Chrome. Start the server with `uvicorn backend.main:app --reload --port 8000` and open `http://localhost:8000`.

---

## Previous Phase
[Phase 6 — FastAPI Streaming Endpoint](./2026-03-19-phase-6-api-roadmap.md)

## Next Phase
[Phase 8 — Integration & Polish](./2026-03-19-phase-8-polish-roadmap.md)

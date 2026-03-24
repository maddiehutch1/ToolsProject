# 2026-03-19 Phase 7 Roadmap — Frontend
**Target:** Day 4–5  
**Status:** Not started

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
- [ ] Persistent disclaimer banner: *"This tool is not a substitute for professional mental health care."*
- [ ] Scrollable message list area
- [ ] Text input field + Send button
- [ ] Links to `style.css` and `app.js`

**`frontend/style.css`**
- [ ] Soft, accessible color palette (blues/greens/greys)
- [ ] User bubble — right-aligned; agent bubble — left-aligned
- [ ] Tool badge chips — small pill label per tool used
- [ ] Crisis card — red/amber border, clear resource link styling
- [ ] Loading spinner animation
- [ ] Auto-scroll anchored to bottom of message list

**`frontend/app.js`**
- [ ] Generate `session_id` (UUID v4) on page load
- [ ] `sendMessage(text)` → `POST /chat` → `fetch` + `ReadableStream` line-by-line parse
- [ ] Append `token` chunks to current agent bubble in real time
- [ ] Add tool badge chip on `tool_use` event
- [ ] Render crisis card on `crisis` event (distinct style + resource links as clickable text)
- [ ] Show spinner while waiting; hide on `done` or `error`
- [ ] Disable input + Send button during active stream; re-enable on completion
- [ ] Auto-scroll to newest message after each update
- [ ] Display readable error message on `error` event — no crashed/blank UI

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

---

## Previous Phase
[Phase 6 — FastAPI Streaming Endpoint](./2026-03-19-phase-6-api-roadmap.md)

## Next Phase
[Phase 8 — Integration & Polish](./2026-03-19-phase-8-polish-roadmap.md)

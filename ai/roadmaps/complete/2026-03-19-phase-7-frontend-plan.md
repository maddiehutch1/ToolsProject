# 2026-03-19 Phase 7 Plan — Frontend

---

> **Build only what the checklist requires. No abstractions until you need them twice.**
> If a file, class, or function isn't referenced by something else in this phase, it shouldn't exist yet.
> Do not add compatibility shims, base classes, config flags, or "just in case" error paths not listed here.

---

## `frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mental Health Companion</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <div id="disclaimer">
    This tool is not a substitute for professional mental health care.
  </div>

  <div id="chat-container">
    <div id="messages"></div>
  </div>

  <div id="input-area">
    <input id="user-input" type="text" placeholder="Type a message..." autocomplete="off" />
    <button id="send-btn">Send</button>
  </div>

  <script src="app.js"></script>
</body>
</html>
```

---

## `frontend/style.css`

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: system-ui, sans-serif;
  background: #f0f4f8;
  color: #2d3748;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

#disclaimer {
  background: #ebf8ff;
  border-bottom: 1px solid #bee3f8;
  color: #2b6cb0;
  font-size: 0.85rem;
  padding: 0.5rem 1rem;
  text-align: center;
  flex-shrink: 0;
}

#chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

#messages { display: flex; flex-direction: column; gap: 0.75rem; }

.bubble {
  max-width: 70%;
  padding: 0.65rem 0.9rem;
  border-radius: 1rem;
  line-height: 1.5;
  word-break: break-word;
}

.bubble.user {
  align-self: flex-end;
  background: #3182ce;
  color: #fff;
  border-bottom-right-radius: 0.2rem;
}

.bubble.agent {
  align-self: flex-start;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 0.2rem;
}

.tool-badge {
  display: inline-block;
  font-size: 0.7rem;
  background: #e9d8fd;
  color: #553c9a;
  border-radius: 999px;
  padding: 0.15rem 0.55rem;
  margin-bottom: 0.3rem;
}

.crisis-card {
  align-self: flex-start;
  background: #fff5f5;
  border: 2px solid #fc8181;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  max-width: 70%;
  line-height: 1.6;
}

.crisis-card strong { color: #c53030; }

.spinner {
  align-self: flex-start;
  width: 1.5rem;
  height: 1.5rem;
  border: 3px solid #e2e8f0;
  border-top-color: #3182ce;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

#input-area {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

#user-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e0;
  border-radius: 0.5rem;
  font-size: 1rem;
  outline: none;
}

#user-input:focus { border-color: #3182ce; }

#send-btn {
  padding: 0.5rem 1.1rem;
  background: #3182ce;
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
}

#send-btn:disabled { background: #a0aec0; cursor: not-allowed; }
```

---

## `frontend/app.js`

```javascript
const messagesEl = document.getElementById('messages');
const inputEl    = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
const sessionId  = crypto.randomUUID();

function setInputEnabled(enabled) {
  inputEl.disabled = !enabled;
  sendBtn.disabled = !enabled;
}

function scrollToBottom() {
  const container = document.getElementById('chat-container');
  container.scrollTop = container.scrollHeight;
}

function appendBubble(role, text = '') {
  const div = document.createElement('div');
  div.className = `bubble ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function appendToolBadge(bubbleEl, toolName) {
  const badge = document.createElement('span');
  badge.className = 'tool-badge';
  badge.textContent = toolName;
  bubbleEl.prepend(badge);
}

function appendCrisisCard(content) {
  const card = document.createElement('div');
  card.className = 'crisis-card';
  card.innerHTML = `<strong>Please reach out for support:</strong><br><pre style="white-space:pre-wrap;font-family:inherit">${content}</pre>`;
  messagesEl.appendChild(card);
  scrollToBottom();
}

function appendSpinner() {
  const div = document.createElement('div');
  div.className = 'spinner';
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = '';
  setInputEnabled(false);
  appendBubble('user', text);

  const spinner = appendSpinner();
  const agentBubble = document.createElement('div');
  agentBubble.className = 'bubble agent';
  let bubbleAdded = false;

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const event = JSON.parse(line.slice(6));

        if (event.type === 'token') {
          if (!bubbleAdded) {
            spinner.remove();
            messagesEl.appendChild(agentBubble);
            bubbleAdded = true;
          }
          agentBubble.textContent += event.content;
          scrollToBottom();
        } else if (event.type === 'tool_use') {
          if (!bubbleAdded) {
            spinner.remove();
            messagesEl.appendChild(agentBubble);
            bubbleAdded = true;
          }
          appendToolBadge(agentBubble, event.tool);
        } else if (event.type === 'crisis') {
          spinner.remove();
          appendCrisisCard(event.content);
        } else if (event.type === 'error') {
          spinner.remove();
          appendBubble('agent', `Error: ${event.content}`);
        } else if (event.type === 'done') {
          spinner.remove();
        }
      }
    }
  } catch (err) {
    spinner.remove();
    appendBubble('agent', `Something went wrong. Please try again.`);
  } finally {
    setInputEnabled(true);
    inputEl.focus();
  }
}

sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
```

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

const _renderer = new marked.Renderer();
_renderer.link = ({ href, title, text }) => {
  const titleAttr = title ? ` title="${title}"` : '';
  return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`;
};

function renderMarkdown(text) {
  return marked.parse(text, { breaks: true, renderer: _renderer });
}

function appendBubble(role, text = '') {
  const div = document.createElement('div');
  div.className = `bubble ${role}`;
  if (text) {
    div.innerHTML = renderMarkdown(text);
  }
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
    let rawText = '';

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
          rawText += event.content;
          agentBubble.innerHTML = renderMarkdown(rawText);
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

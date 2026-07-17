// ══════════════════════════════════════════════
// CORE SPA LOGIC
// ══════════════════════════════════════════════
const API = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://localhost:8001'
  : 'https://medimitra-api-05bj.onrender.com';

// In-memory Session State (JWT is NOT stored in localStorage/sessionStorage)
let userSession = {
  jwt: null,
  user_id: null,
  email: null,
  name: null,
  picture: null
};

function googleSignInTrigger() {
  showToast('Please click the "Sign In with Google" button in the top-right corner of the navigation bar.', 'info');
}

function showSection(id) {
  if (id === 'landing') {
    document.body.classList.add('landing-active');
  } else {
    document.body.classList.remove('landing-active');
    location.hash = id;
  }
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const sec = document.getElementById('section-' + id);
  if (sec) { sec.classList.add('active'); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  const navBtn = document.querySelector(`[data-section="${id}"]`);
  if (navBtn) navBtn.classList.add('active');
  if (window.innerWidth < 1024) closeSidebar();
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobile-overlay');
  sidebar.classList.toggle('open');
  overlay.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
}
function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('mobile-overlay').style.display = 'none';
}

function toggleDark() {
  document.body.classList.toggle('light-mode');
  document.getElementById('theme-icon').className = document.body.classList.contains('light-mode') ? 'fas fa-sun' : 'fas fa-moon';
}

// ══════════════════════════════════════════════
// TOAST
// ══════════════════════════════════════════════
function showToast(message, type = 'info', duration = 4000) {
  const icons = { success: 'check-circle', warning: 'exclamation-triangle', error: 'times-circle', info: 'info-circle' };
  const colors = { success: '#4ade80', warning: '#fbbf24', error: '#f87171', info: '#60a5fa' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<i class="fas fa-${icons[type]}" style="color:${colors[type]};font-size:16px;flex-shrink:0;"></i><span style="flex:1;">${message}</span><i class="fas fa-times toast-close" onclick="this.parentElement.remove()"></i>`;
  document.getElementById('toast-container').appendChild(t);
  setTimeout(() => t.remove(), duration);
}

// ══════════════════════════════════════════════
// LOADING
// ══════════════════════════════════════════════
function showLoading(text = 'Analyzing with AI...') {
  document.getElementById('loading-text').textContent = text;
  document.getElementById('loading-overlay').classList.add('show');

  // Show cycling tips to make the wait feel shorter
  const tips = [
    '🧠 AI is thinking...',
    '📊 Processing your data...',
    '🔍 Analyzing patterns...',
    '✨ Almost ready...',
    '⚡ Finalizing results...'
  ];
  let tipIdx = 0;
  window.loadingTipInterval = setInterval(() => {
    tipIdx = (tipIdx + 1) % tips.length;
    document.getElementById('loading-text').textContent = tips[tipIdx];
  }, 3000);
}
function hideLoading() {
  document.getElementById('loading-overlay').classList.remove('show');
  if (window.loadingTipInterval) clearInterval(window.loadingTipInterval);
}

// ══════════════════════════════════════════════
// HISTORY
// ══════════════════════════════════════════════
let currentHistorySection = '';
const HISTORY_KEYS = { symptom: 'medimitra_symptom_history', prescription: 'medimitra_prescription_history', scanner: 'medimitra_scanner_history', lifestyle: 'medimitra_lifestyle_history' };
const HISTORY_LABELS = { symptom: 'Previous Symptom Checks', prescription: 'Previous Prescriptions', scanner: 'Previous Scans', lifestyle: 'Previous Plans' };
const MAX_HISTORY = 20;

function getHistory(section) {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEYS[section])) || []; } catch { return []; }
}
function saveHistory(section, entry) {
  let h = getHistory(section);
  h.unshift({ ...entry, id: Date.now(), timestamp: new Date().toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) });
  if (h.length > MAX_HISTORY) h = h.slice(0, MAX_HISTORY);
  localStorage.setItem(HISTORY_KEYS[section], JSON.stringify(h));
  updateHistoryBadge(section);
}
function updateHistoryBadge(section) {
  const count = getHistory(section).length;
  const badge = document.getElementById(section + '-hist-count');
  if (badge) { badge.textContent = count; badge.style.display = count > 0 ? 'flex' : 'none'; }
}
function openHistory(section) {
  currentHistorySection = section;
  document.getElementById('history-panel-title').textContent = '📋 ' + HISTORY_LABELS[section];
  renderHistoryList(section);
  document.getElementById('history-panel').classList.add('open');
  document.getElementById('history-overlay').classList.add('show');
}
function closeHistory() {
  document.getElementById('history-panel').classList.remove('open');
  document.getElementById('history-overlay').classList.remove('show');
}
function renderHistoryList(section) {
  const entries = getHistory(section);
  const el = document.getElementById('history-list-content');
  if (!entries.length) {
    el.innerHTML = `<div class="history-empty"><i class="fas fa-clock"></i><p style="font-weight:600;margin-bottom:6px;">No history yet</p><p style="font-size:13px;">Your results will appear here after your first analysis.</p></div>`;
    return;
  }
  el.innerHTML = entries.map(e => `
    <div class="history-entry" onclick="loadHistoryEntry('${section}','${e.id}')">
      <div class="history-entry-header">
        <span class="badge badge-${e.badgeType || 'info'}">${e.badge || 'Entry'}</span>
        <span class="history-entry-time">${e.timestamp}</span>
      </div>
      <div class="history-entry-summary">${e.summary}</div>
      <div class="history-entry-footer">
        <button class="btn btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="event.stopPropagation();loadHistoryEntry('${section}','${e.id}')"><i class="fas fa-undo"></i> Load</button>
        <i class="fas fa-trash" style="color:var(--text-muted);cursor:pointer;font-size:13px;" onclick="event.stopPropagation();deleteHistory('${section}','${e.id}')"></i>
      </div>
    </div>`).join('');
}
function deleteHistory(section, id) {
  let h = getHistory(section).filter(e => String(e.id) !== String(id));
  localStorage.setItem(HISTORY_KEYS[section], JSON.stringify(h));
  updateHistoryBadge(section);
  renderHistoryList(section);
}
function loadHistoryEntry(section, id) {
  const entry = getHistory(section).find(e => String(e.id) === String(id));
  if (!entry) return;
  closeHistory();
  showSection(section);

  if (section === 'symptom' && entry.fullData) {
    renderSymptomResult(entry.fullData);
  } else if (section === 'prescription' && entry.fullData) {
    document.getElementById('rx-panel-1').style.display = 'none';
    document.getElementById('rx-panel-3').style.display = 'block';
    renderPrescriptionResult(entry.fullData);
  } else if (section === 'scanner' && entry.fullData) {
    renderScanResult(entry.fullData);
  } else if (section === 'lifestyle' && entry.fullData) {
    renderLifestylePlan(entry.fullData, entry.name || 'User', entry.goal || 'Stay Healthy', entry.activity || 'Sedentary');
  }

  showToast('History entry loaded successfully', 'success');
}
['symptom', 'prescription', 'scanner', 'lifestyle'].forEach(s => updateHistoryBadge(s));

// ══════════════════════════════════════════════
// UTILS
// ══════════════════════════════════════════════
function updateCharCount(inputId, countId, max) {
  const val = document.getElementById(inputId).value.length;
  document.getElementById(countId).textContent = `${val}/${max}`;
}
function switchTab(containerId, index, btn) {
  const c = document.getElementById(containerId);
  c.querySelectorAll('.tab-panel').forEach((p, i) => p.classList.toggle('active', i === index));
  const tabs = btn.closest('.tabs');
  tabs.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}
function toggleChip(input) {
  const chip = input.nextElementSibling;
  chip.classList.toggle('active', input.checked);
}
function startVoice(targetId, btnId) {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) { showToast('Voice input not supported in this browser', 'error'); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const r = new SR();
  r.lang = 'en-IN'; r.interimResults = false;
  const btn = document.getElementById(btnId);
  btn.classList.add('recording');
  r.start();
  r.onresult = e => { document.getElementById(targetId).value += ' ' + e.results[0][0].transcript; updateCharCount(targetId, 'symptom-chars', 500); };
  r.onend = () => btn.classList.remove('recording');
  r.onerror = () => { btn.classList.remove('recording'); showToast('Voice recognition error', 'error'); };
}

// ══════════════════════════════════════════════
// SYMPTOM CHECKER
// ══════════════════════════════════════════════
function addSymptom(el, name) {
  const ta = document.getElementById('symptom-text');
  ta.value += (ta.value ? ', ' : '') + name;
  el.classList.toggle('active');
  updateCharCount('symptom-text', 'symptom-chars', 500);
}
async function checkSymptoms() {
  const symptoms = document.getElementById('symptom-text').value.trim();
  if (!symptoms) { showToast('Please describe your symptoms first', 'warning'); return; }
  const duration = document.querySelector('[name="duration"]:checked')?.value || '1-3 days';
  const severity = document.getElementById('severity-slider').value;

  const payload = { symptoms, duration, severity, language: getActiveLanguage() };
  if (userSession.user_id) payload.user_id = String(userSession.user_id);

  // ── Show streaming skeleton immediately ──
  document.getElementById('symptom-empty').style.display = 'none';
  document.getElementById('symptom-result').style.display = 'block';
  const card = document.getElementById('symptom-result-card');
  card.className = 'result-card safe';
  document.getElementById('symptom-severity-badge').className = 'badge badge-safe';
  document.getElementById('symptom-severity-badge').textContent = 'Analyzing…';
  document.getElementById('symptom-condition').textContent = 'AI is thinking…';
  document.getElementById('symptom-confidence').textContent = '';
  document.getElementById('symptom-conf-bar').style.width = '0%';
  document.getElementById('symptom-conf-label').textContent = '';

  // Live typewriter display in explanation tab
  const liveHtml = `
        <div id="stream-live" style="color:var(--text-secondary);line-height:1.8;font-size:13px;font-family:monospace;white-space:pre-wrap;min-height:80px;">
          <span style="color:var(--primary);font-weight:600;">⚡ AI is analyzing your symptoms…</span>\n
        </div>`;
  document.getElementById('symptom-tab-0').innerHTML = liveHtml;
  document.getElementById('symptom-tab-1').innerHTML = '<div style="color:var(--text-secondary);padding:8px;">Loading remedies…</div>';
  document.getElementById('symptom-tab-2').innerHTML = '<div style="color:var(--text-secondary);padding:8px;">Loading red flags…</div>';

  // Switch to explanation tab so user sees the stream
  const tabs = document.querySelectorAll('#symptom-result .tab-btn');
  const panels = document.querySelectorAll('#symptom-result .tab-panel');
  tabs.forEach((t, i) => { t.classList.toggle('active', i === 0); });
  panels.forEach((p, i) => { p.classList.toggle('active', i === 0); });

  let streamBuffer = '';
  let streamSuccess = false;

  try {
    const response = await fetch(`${API}/api/symptom/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Stream endpoint error');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const liveEl = document.getElementById('stream-live');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value, { stream: true });
      // SSE lines: "data: <content>\n\n"
      const lines = text.split('\n');
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload_str = line.slice(6);

        if (payload_str.startsWith('[DONE]')) {
          // Final event — parse JSON and render
          try {
            const jsonStr = payload_str.slice(7).trim();
            const data = JSON.parse(jsonStr);
            renderSymptomResult(data);
            saveHistory('symptom', {
              summary: symptoms.slice(0, 60) + (symptoms.length > 60 ? '...' : ''),
              badge: data.condition || 'Result',
              badgeType: data.severity === 'Severe' ? 'danger' : data.severity === 'Moderate' ? 'warning' : 'safe',
              fullData: data
            });
            showToast('Analysis complete!', 'success');
            streamSuccess = true;
          } catch (parseErr) {
            console.error('DONE parse error', parseErr);
          }
          break;
        } else if (payload_str.startsWith('[ERROR]')) {
          throw new Error(payload_str.slice(8));
        } else {
          // Raw token chunk — show in live box
          streamBuffer += payload_str.replace(/\\n/g, '\n');
          if (liveEl) {
            liveEl.textContent = '⚡ AI is analyzing your symptoms…\n\n' + streamBuffer;
          }
        }
      }
    }
  } catch (e) {
    console.warn('Streaming failed, falling back to /check:', e.message);
    // ── Graceful fallback to non-streaming endpoint ──
    try {
      showLoading('Analyzing symptoms…');
      const res = await fetch(`${API}/api/symptom/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      renderSymptomResult(data);
      saveHistory('symptom', {
        summary: symptoms.slice(0, 60) + (symptoms.length > 60 ? '...' : ''),
        badge: data.condition || 'Result',
        badgeType: data.severity === 'Severe' ? 'danger' : data.severity === 'Moderate' ? 'warning' : 'safe',
        fullData: data
      });
      showToast('Analysis complete!', 'success');
      streamSuccess = true;
    } catch (fallbackErr) {
      showToast('Could not connect to API. Check if backend is running on port 8001.', 'error');
      // Demo mode
      renderSymptomResult({ condition: 'Viral Fever', severity: 'Moderate', confidence: 78, explanation: 'This appears to be a common viral fever. Your symptoms of fever, headache, and body pain are consistent with viral infection.', home_remedies: ['Rest and stay hydrated', 'Take paracetamol for fever', 'Warm fluids like soup or kadha', 'Sleep well and avoid cold exposure'], red_flags: ['High fever above 103°F for more than 3 days', 'Difficulty breathing', 'Severe chest pain or confusion'] });
    }
    hideLoading();
  }
}

function renderSymptomResult(data) {
  document.getElementById('symptom-empty').style.display = 'none';
  document.getElementById('symptom-result').style.display = 'block';
  const severityColor = data.severity === 'Severe' ? 'danger' : data.severity === 'Moderate' ? 'warning' : 'safe';
  const card = document.getElementById('symptom-result-card');
  card.className = `result-card ${severityColor}`;
  document.getElementById('symptom-severity-badge').className = `badge badge-${severityColor}`;
  document.getElementById('symptom-severity-badge').textContent = data.severity || 'Mild';
  document.getElementById('symptom-condition').textContent = data.condition || 'Unknown';
  const conf = data.confidence || 75;
  document.getElementById('symptom-confidence').textContent = `${conf}% match`;
  document.getElementById('symptom-conf-bar').style.width = `${conf}%`;
  document.getElementById('symptom-conf-label').textContent = `Based on AI analysis`;
  document.getElementById('symptom-tab-0').innerHTML = `<p style="color:var(--text-secondary);line-height:1.8;">${data.explanation || ''}</p>`;
  document.getElementById('symptom-tab-1').innerHTML = (data.home_remedies || []).map(r => `<div class="dos-card"><i class="fas fa-check" style="color:#4ade80;margin-top:2px;flex-shrink:0;"></i><span style="font-size:14px;">${r}</span></div>`).join('');
  document.getElementById('symptom-tab-2').innerHTML = (data.red_flags || []).map(r => `<div class="donts-card"><i class="fas fa-exclamation" style="color:#f87171;margin-top:2px;flex-shrink:0;"></i><span style="font-size:14px;">${r}</span></div>`).join('');
}

// ══════════════════════════════════════════════
// PRESCRIPTION READER
// ══════════════════════════════════════════════
let rxFileBase64 = null;
function handleRxFile(e) {
  const file = e.target.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    rxFileBase64 = ev.target.result.split(',')[1];
    document.getElementById('rx-preview-img').src = ev.target.result;
    document.getElementById('rx-file-preview').style.display = 'block';
    document.getElementById('rx-file-name').textContent = '✓ ' + file.name;
    document.getElementById('rx-submit-btn').disabled = false;
  };
  reader.readAsDataURL(file);
}
function handleRxDrop(e) {
  e.preventDefault();
  document.getElementById('rx-upload-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) { document.getElementById('rx-file-input').files = e.dataTransfer.files; handleRxFile({ target: { files: e.dataTransfer.files } }); }
}
async function readPrescription() {
  if (!rxFileBase64) { showToast('Please upload a prescription image first', 'warning'); return; }
  const lang = getActiveLanguage();
  document.getElementById('rx-panel-1').style.display = 'none';
  document.getElementById('rx-panel-2').style.display = 'block';
  document.getElementById('rx-step-2').classList.add('active');
  document.getElementById('rx-line-1').classList.add('done');

  // Start API request in parallel with animations for better speed
  const apiPromise = fetch(`${API}/api/prescription/read`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_base64: rxFileBase64, language: lang })
  }).then(res => res.ok ? res.json() : { medicines: [], explanation: 'Analyze failed. Please ensure the image is a clear prescription.' })
    .catch(() => ({ medicines: [], explanation: 'Network error. Please check your connection.' }));

  // Animate progress (made faster)
  await animateRxStep('rxp-1', 500);
  document.getElementById('rxp-2').style.opacity = '1';
  await animateRxStep('rxp-2', 600);
  document.getElementById('rxp-3').style.opacity = '1';
  await animateRxStep('rxp-3', 400);

  // Wait for API if it hasn't finished yet
  const data = await apiPromise;

  renderPrescriptionResult(data);
  saveHistory('prescription', { summary: `Prescription in ${getActiveLanguage()}`, badge: 'Prescription', badgeType: 'info', fullData: data });

  document.getElementById('rx-panel-2').style.display = 'none';
  document.getElementById('rx-panel-3').style.display = 'block';
  document.getElementById('rx-step-3').classList.add('active');
  document.getElementById('rx-line-2').classList.add('done');
  showToast('Prescription analyzed successfully!', 'success');
}
function animateRxStep(id, duration) {
  return new Promise(resolve => {
    const bar = document.getElementById(id + '-bar');
    const check = document.getElementById(id + '-check');
    let p = 0;
    const interval = setInterval(() => { p += 2; bar.style.width = p + '%'; if (p >= 100) { clearInterval(interval); check.style.display = 'flex'; resolve(); } }, duration / 50);
  });
}
function getDemoPrescriptionData() {
  return { medicines: [{ name: 'Amoxicillin 500mg', dosage: '1 capsule', frequency: '3 times daily', duration: '7 days', timing: 'After meals' }, { name: 'Paracetamol 650mg', dosage: '1 tablet', frequency: 'As needed', duration: '5 days', timing: 'For fever/pain' }], explanation: 'This prescription is for a bacterial infection. The antibiotic must be completed fully. Paracetamol is for fever management.', translated_text: 'This prescription treats a bacterial infection.' };
}
function renderPrescriptionResult(data) {
  const tbody = document.getElementById('rx-table-body');
  const explanations = document.getElementById('rx-explanations');

  if (!data.medicines || data.medicines.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;padding:48px;color:var(--text-muted);">
          <div style="font-size:32px;margin-bottom:12px;opacity:0.5;">📋?</div>
          <p style="font-size:15px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">No medicines detected</p>
          <p style="max-width:300px;margin:0 auto;line-height:1.5;">${data.explanation || 'The uploaded image may not be a clear prescription. Please try again with a better photo.'}</p>
        </td></tr>`;
    explanations.innerHTML = '';
    return;
  }

  const timingColors = { Morning: 'warning', Afternoon: 'info', Night: 'purple', 'After meals': 'safe', 'For fever/pain': 'warning', 'As needed': 'info' };
  tbody.innerHTML = (data.medicines || []).map((m, i) => `
    <tr style="background:${i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'};">
      <td style="padding:10px 14px;font-weight:700;border-bottom:1px solid var(--border);">${m.name}</td>
      <td style="padding:10px 14px;border-bottom:1px solid var(--border);">${m.dosage}</td>
      <td style="padding:10px 14px;border-bottom:1px solid var(--border);">${m.frequency}</td>
      <td style="padding:10px 14px;border-bottom:1px solid var(--border);"><span class="badge badge-${timingColors[m.timing] || 'info'}">${m.timing || m.duration}</span></td>
    </tr>`).join('');
  explanations.innerHTML = (data.medicines || []).map(m => `
    <div class="card card-lg">
      <h4 style="font-family:var(--font-display);font-size:16px;font-weight:700;margin-bottom:12px;color:var(--primary-light);">${m.name}</h4>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:13px;">
        <div><span style="color:var(--text-muted);font-weight:600;">What it is:</span><p style="color:var(--text-secondary);margin-top:2px;">${m.what_it_is || 'An antibiotic/analgesic medicine for treating infection or pain.'}</p></div>
        <div><span style="color:var(--text-muted);font-weight:600;">What it treats:</span><p style="color:var(--text-secondary);margin-top:2px;">${m.what_it_treats || 'Bacterial infections, fever and pain management.'}</p></div>
      </div>
      <div style="margin-top:10px;padding:10px;background:rgba(217,119,6,0.08);border-radius:8px;font-size:12px;color:#fbbf24;">
        ⚠️ <strong>Side effects to watch:</strong> ${m.side_effects || 'Nausea, allergic reactions, stomach upset. Consult doctor if severe.'}
      </div>
    </div>`).join('');
}

// ══════════════════════════════════════════════
// FEEDBACK SYSTEM
// ══════════════════════════════════════════════
let currentRating = 0;
function setRating(n) {
  currentRating = n;
  const stars = document.querySelectorAll('.feedback-star');
  stars.forEach((s, idx) => {
    if (idx < n) {
      s.style.color = '#fbbf24';
      s.classList.replace('far', 'fas');
    } else {
      s.style.color = '#94a3b8';
      s.classList.replace('fas', 'far');
    }
  });
}
async function submitFeedback() {
  if (currentRating === 0) { showToast('Please select a star rating', 'warning'); return; }

  const text = document.getElementById('feedback-text').value;

  try {
    const response = await fetch(`${API}/api/feedback/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rating: currentRating,
        feedback_text: text || ""
      })
    });

    const data = await response.json();
    if (data.status === 'success') {
      showToast('Thank you for your valuable feedback!', 'success');
      document.getElementById('feedback-text').value = '';
      setRating(0);
    } else {
      showToast('Failed to submit: ' + data.message, 'error');
    }
  } catch (error) {
    showToast('Submission error. Please check your connection.', 'error');
  }
}

function toggleReadAloud() {
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    document.getElementById('rx-read-btn').innerHTML = '<i class="fas fa-volume-up"></i> Read Aloud';
    showToast('Speech stopped', 'info');
  } else {
    readAloud();
  }
}

function readAloud() {
  const text = document.getElementById('rx-explanations').innerText || document.getElementById('rx-table').innerText;
  if (!text || text.includes('No medicines detected')) return;

  const lang = getActiveLanguage();
  const u = new SpeechSynthesisUtterance(text);

  // Native Voice Support for 7+ Languages
  const voiceMap = {
    'Hindi': 'hi-IN',
    'Bengali': 'bn-IN',
    'Odia': 'or-IN',
    'Tamil': 'ta-IN',
    'Telugu': 'te-IN',
    'Marathi': 'mr-IN',
    'English': 'en-IN'
  };
  u.lang = voiceMap[lang] || 'en-IN';

  u.onstart = () => {
    document.getElementById('rx-read-btn').innerHTML = '<i class="fas fa-pause"></i> Stop Reading';
  };
  u.onend = () => {
    document.getElementById('rx-read-btn').innerHTML = '<i class="fas fa-volume-up"></i> Read Aloud';
  };

  window.speechSynthesis.speak(u);
  showToast('Reading aloud...', 'info');
}
function rxReset() {
  rxFileBase64 = null;
  document.getElementById('rx-file-input').value = '';
  document.getElementById('rx-file-preview').style.display = 'none';
  document.getElementById('rx-submit-btn').disabled = true;
  ['rx-panel-1', 'rx-panel-2', 'rx-panel-3'].forEach((id, i) => document.getElementById(id).style.display = i === 0 ? 'block' : 'none');
  ['rx-step-1', 'rx-step-2', 'rx-step-3'].forEach((id, i) => { const el = document.getElementById(id); el.classList.toggle('active', i === 0); el.classList.remove('done'); });
  ['rx-line-1', 'rx-line-2'].forEach(id => document.getElementById(id).classList.remove('done'));
  ['rxp-1-bar', 'rxp-2-bar', 'rxp-3-bar'].forEach(id => { const el = document.getElementById(id); if (el) el.style.width = '0%'; });
  ['rxp-1-check', 'rxp-2-check', 'rxp-3-check'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });
  ['rxp-2', 'rxp-3'].forEach(id => { const el = document.getElementById(id); if (el) el.style.opacity = '0.4'; });
}

// ══════════════════════════════════════════════
// DRUG INTERACTION
// ══════════════════════════════════════════════
const commonDrugs = ['Aspirin', 'Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Metformin', 'Atorvastatin', 'Lisinopril', 'Warfarin', 'Omeprazole', 'Cetirizine', 'Azithromycin', 'Metronidazole', 'Doxycycline', 'Ciprofloxacin', 'Pantoprazole', 'Amlodipine', 'Losartan', 'Gabapentin', 'Sertraline', 'Levothyroxine'];
let selectedDrugs = [];
function drugAutocomplete(val) {
  const dd = document.getElementById('drug-dropdown');
  if (!val.trim()) { dd.classList.remove('open'); return; }
  const matches = commonDrugs.filter(d => d.toLowerCase().includes(val.toLowerCase()) && !selectedDrugs.includes(d)).slice(0, 6);
  dd.innerHTML = matches.map(m => `<div class="autocomplete-item" onclick="selectDrug('${m}')">${m}</div>`).join('') || '<div class="autocomplete-item" style="color:var(--text-muted);">No matches found</div>';
  dd.classList.add('open');
}
function selectDrug(name) {
  document.getElementById('drug-search').value = '';
  document.getElementById('drug-dropdown').classList.remove('open');
  addDrug(name);
}
function addDrug(name) {
  if (selectedDrugs.includes(name) || selectedDrugs.length >= 10) return;
  selectedDrugs.push(name);
  renderDrugChips();
}
function addDrugFromInput() {
  const val = document.getElementById('drug-search').value.trim();
  if (val) { addDrug(val); document.getElementById('drug-search').value = ''; document.getElementById('drug-dropdown').classList.remove('open'); }
}
function removeDrug(name) {
  selectedDrugs = selectedDrugs.filter(d => d !== name);
  renderDrugChips();
}
function renderDrugChips() {
  document.getElementById('drug-chips').innerHTML = selectedDrugs.map(d => `<span class="med-chip">${d}<span class="remove" onclick="removeDrug('${d}')"><i class="fas fa-times"></i></span></span>`).join('');
  document.getElementById('drug-check-btn').disabled = selectedDrugs.length < 2;
}
async function checkInteractions() {
  if (selectedDrugs.length < 2) { showToast('Add at least 2 medicines', 'warning'); return; }
  showLoading('Checking drug interactions...');
  try {
    const res = await fetch(`${API}/api/interaction/check`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ medicines: selectedDrugs, language: getActiveLanguage() }) });
    const data = res.ok ? await res.json() : getDemoInteractionData();
    renderInteractionResult(data);
    showToast('Interaction check complete!', 'success');
  } catch {
    renderInteractionResult(getDemoInteractionData());
  }
  hideLoading();
}
function getDemoInteractionData() {
  const drugs = selectedDrugs;
  const interactions = [];
  if (drugs.includes('Warfarin') && drugs.includes('Ibuprofen')) interactions.push({ drug_a: 'Warfarin', drug_b: 'Ibuprofen', risk: 'Dangerous', explanation: 'Significantly increases bleeding risk including gastrointestinal hemorrhage.', recommendation: 'Avoid this combination. Use Acetaminophen as alternative.' });
  if (drugs.includes('Lisinopril') && drugs.includes('Ibuprofen')) interactions.push({ drug_a: 'Lisinopril', drug_b: 'Ibuprofen', risk: 'Moderate', explanation: 'May reduce blood pressure-lowering effect and increase kidney dysfunction risk.', recommendation: 'Monitor blood pressure regularly. Kidney function tests advised.' });
  const riskLevel = interactions.some(i => i.risk === 'Dangerous') ? 'Dangerous' : interactions.length > 0 ? 'Moderate' : 'Safe';
  return { risk_level: riskLevel, interactions, details: interactions };
}
function renderInteractionResult(data) {
  document.getElementById('drug-empty').style.display = 'none';
  document.getElementById('drug-result').style.display = 'block';
  const bannerConfigs = { Safe: { bg: 'rgba(22,163,74,0.1)', border: 'rgba(22,163,74,0.3)', color: '#4ade80', icon: 'check-circle', text: '✅ No dangerous interactions found between your medicines.' }, Moderate: { bg: 'rgba(217,119,6,0.1)', border: 'rgba(217,119,6,0.3)', color: '#fbbf24', icon: 'exclamation-triangle', text: '⚠️ Some moderate interactions detected. Review below.' }, Dangerous: { bg: 'rgba(220,38,38,0.1)', border: 'rgba(220,38,38,0.3)', color: '#f87171', icon: 'times-circle', text: '🚨 Dangerous interaction found! Consult your doctor immediately.' } };
  const cfg = bannerConfigs[data.risk_level] || bannerConfigs.Safe;
  document.getElementById('drug-risk-banner').style.cssText = `background:${cfg.bg};border:1px solid ${cfg.border};padding:18px 20px;display:flex;align-items:center;gap:14px;`;
  document.getElementById('drug-risk-banner').innerHTML = `<i class="fas fa-${cfg.icon}" style="color:${cfg.color};font-size:28px;flex-shrink:0;"></i><div><p style="font-size:16px;font-weight:700;color:${cfg.color};">${data.risk_level} Risk</p><p style="font-size:14px;color:var(--text-secondary);margin-top:2px;">${cfg.text}</p></div>`;
  // Matrix
  const drugs = selectedDrugs;
  let matrix = `<table class="matrix-table"><thead><tr><th></th>${drugs.map(d => `<th>${d}</th>`).join('')}</tr></thead><tbody>`;
  drugs.forEach((d1, i) => {
    matrix += `<tr><th style="text-align:left;">${d1}</th>`;
    drugs.forEach((d2, j) => {
      if (i === j) { matrix += `<td class="cell-na">—</td>`; return; }
      const inter = (data.interactions || []).find(x => (x.drug_a === d1 && x.drug_b === d2) || (x.drug_a === d2 && x.drug_b === d1));
      if (!inter) { matrix += `<td><span class="matrix-cell-safe"><i class="fas fa-check-circle"></i></span></td>`; }
      else if (inter.risk === 'Dangerous') { matrix += `<td title="${inter.explanation}"><span class="matrix-cell-danger"><i class="fas fa-times-circle"></i></span></td>`; }
      else { matrix += `<td title="${inter.explanation}"><span class="matrix-cell-warn"><i class="fas fa-exclamation-circle"></i></span></td>`; }
    });
    matrix += `</tr>`;
  });
  matrix += '</tbody></table>';
  document.getElementById('drug-matrix').innerHTML = matrix;
  // Detail cards
  const riskColors = { Dangerous: 'danger', Moderate: 'warning', Mild: 'warning' };
  document.getElementById('drug-detail-cards').innerHTML = (data.interactions || []).map(i => `
    <div class="result-card ${riskColors[i.risk] || 'warning'}" style="margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <span class="badge badge-${riskColors[i.risk] || 'warning'}">${i.risk} Risk</span>
        <i class="fas fa-${i.risk === 'Dangerous' ? 'times-circle' : 'exclamation-circle'}" style="color:${i.risk === 'Dangerous' ? '#f87171' : '#fbbf24'};"></i>
      </div>
      <h4 style="font-family:var(--font-display);font-size:16px;font-weight:700;margin-bottom:8px;">${i.drug_a} + ${i.drug_b}</h4>
      <p style="font-size:13px;color:var(--text-secondary);margin-bottom:10px;line-height:1.7;">${i.explanation}</p>
      <div style="background:rgba(255,255,255,0.04);padding:10px;border-radius:8px;font-size:12px;"><strong>Recommendation:</strong> ${i.recommendation}</div>
    </div>`).join('');
}
function startVoiceDrug() {
  if (!('webkitSpeechRecognition' in window)) { showToast('Voice not supported', 'error'); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const r = new SR(); r.lang = 'en-IN';
  r.onresult = e => { const words = e.results[0][0].transcript.split(/,|and/i); words.forEach(w => { const t = w.trim(); if (t) addDrug(t); }); };
  r.start();
  showToast('Listening... speak medicine names separated by "and"', 'info');
}

// ══════════════════════════════════════════════
// MEDICINE SCANNER
// ══════════════════════════════════════════════
let scanFileBase64 = null;
function handleScanFile(e) {
  const file = e.target.files[0]; if (!file) return;
  const r = new FileReader();
  r.onload = ev => {
    scanFileBase64 = ev.target.result.split(',')[1];
    document.getElementById('scan-preview-img').src = ev.target.result;
    document.getElementById('scan-preview').style.display = 'block';
    document.getElementById('scan-submit-btn').disabled = false;
  };
  r.readAsDataURL(file);
}
function clearScan() {
  scanFileBase64 = null;
  document.getElementById('scan-file').value = '';
  document.getElementById('scan-preview').style.display = 'none';
  document.getElementById('scan-submit-btn').disabled = true;
  document.getElementById('scan-result').style.display = 'none';
}
async function scanMedicine() {
  if (!scanFileBase64) { showToast('Please upload or capture a medicine image', 'warning'); return; }
  const medName = document.getElementById('scan-med-name').value;
  showLoading('Scanning medicine packaging...');
  try {
    const res = await fetch(`${API}/api/scanner/verify`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ image_base64: scanFileBase64, medicine_name: medName, language: getActiveLanguage() }) });
    const data = res.ok ? await res.json() : getDemoScanData();
    renderScanResult(data);
    saveHistory('scanner', { summary: medName || 'Medicine Scan', badge: data.verdict === 'Genuine' ? 'Genuine' : data.verdict === 'Suspicious' ? 'Suspicious' : 'Counterfeit', badgeType: data.verdict === 'Genuine' ? 'safe' : data.verdict === 'Suspicious' ? 'warning' : 'danger', fullData: data });
    showToast('Scan complete!', 'success');
  } catch {
    const demo = getDemoScanData();
    renderScanResult(demo);
  }
  hideLoading();
}
function getDemoScanData() {
  return { safety_score: 88, verdict: 'Genuine', details: { drug_name: 'Paracetamol 500mg', manufacturer: 'Sun Pharma', batch_number: 'SP-2024-789', expiry: 'Dec 2026', openfda_status: 'Verified' }, actions: ['Medicine appears genuine. Safe to use as prescribed.', 'Always check expiry date before consuming.', 'Store in a cool, dry place away from sunlight.'] };
}
function renderScanResult(data) {
  document.getElementById('scan-result').style.display = 'block';
  const score = data.safety_score || 75;
  const isGenuine = score >= 70;
  const isSuspicious = score >= 40 && score < 70;
  const color = isGenuine ? '#4ade80' : isSuspicious ? '#fbbf24' : '#f87171';
  // Animate score
  let current = 0;
  const scoreEl = document.getElementById('scan-score-num');
  const ring = document.getElementById('scan-score-ring');
  ring.style.stroke = color;
  const circumference = 377;
  const interval = setInterval(() => {
    current = Math.min(current + 2, score);
    scoreEl.textContent = current;
    ring.style.strokeDashoffset = circumference - (circumference * current / 100);
    if (current >= score) clearInterval(interval);
  }, 20);
  const verdicts = { Genuine: { icon: 'check-circle', color: '#4ade80', text: '✅ LIKELY GENUINE' }, Suspicious: { icon: 'exclamation-triangle', color: '#fbbf24', text: '⚠️ SUSPICIOUS — VERIFY BEFORE USE' }, Counterfeit: { icon: 'times-circle', color: '#f87171', text: '❌ LIKELY COUNTERFEIT — DO NOT USE' } };
  const v = verdicts[data.verdict] || verdicts.Genuine;
  document.getElementById('scan-verdict').innerHTML = `<span style="color:${v.color};">${v.text}</span>`;
  const d = data.details || {};
  document.getElementById('scan-details').innerHTML = [
    ['Drug Name', d.drug_name || '—'], ['Manufacturer', d.manufacturer || '—'],
    ['Batch Number', d.batch_number || '—'], ['Expiry Date', d.expiry || '—'],
    ['OpenFDA Status', `<span class="badge badge-${d.openfda_status === 'Verified' ? 'safe' : 'danger'}">${d.openfda_status || 'Unknown'}</span>`]
  ].map((r, i) => `<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border);font-size:13px;"><span style="color:var(--text-muted);">${r[0]}</span><span style="font-weight:600;">${r[1]}</span></div>`).join('');
  document.getElementById('scan-actions').innerHTML = (data.actions || []).map((a, i) => `<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:13px;"><span style="background:var(--primary);color:#fff;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:11px;font-weight:700;">${i + 1}</span>${a}</div>`).join('');
}
function startCamera(type) {
  const constraints = { video: { facingMode: 'environment' } };
  navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => {
      const targetImg = type === 'rx' ? 'rx-preview-img' : 'scan-preview-img';
      const targetPreview = type === 'rx' ? 'rx-file-preview' : 'scan-preview';
      const targetBtn = type === 'rx' ? 'rx-submit-btn' : 'scan-submit-btn';
      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();
      // Capture after 1.5 seconds
      setTimeout(() => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        canvas.getContext('2d').drawImage(video, 0, 0);
        stream.getTracks().forEach(t => t.stop());
        const dataUrl = canvas.toDataURL('image/jpeg');
        document.getElementById(targetImg).src = dataUrl;
        document.getElementById(targetPreview).style.display = 'block';
        document.getElementById(targetBtn).disabled = false;
        if (type === 'rx') {
          rxFileBase64 = dataUrl.split(',')[1];
          document.getElementById('rx-file-name').textContent = '✓ Photo captured';
        } else {
          scanFileBase64 = dataUrl.split(',')[1];
        }
        showToast('Photo captured successfully!', 'success');
      }, 1500);
      showToast('Camera opened — capturing in 1.5 seconds...', 'info');
    })
    .catch(() => {
      showToast('Camera not available. Please use Upload Image instead.', 'warning');
    });
}

// ══════════════════════════════════════════════
// LIFESTYLE ADVISOR
// ══════════════════════════════════════════════
function calcBMI() {
  const h = parseFloat(document.getElementById('ls-height').value);
  const w = parseFloat(document.getElementById('ls-weight').value);
  if (!h || !w) { document.getElementById('bmi-display').style.display = 'none'; return; }
  const bmi = (w / ((h / 100) ** 2)).toFixed(1);
  let cat = 'Normal', cls = 'normal';
  if (bmi < 18.5) { cat = 'Underweight'; cls = 'underweight'; }
  else if (bmi < 25) { cat = 'Normal'; cls = 'normal'; }
  else if (bmi < 30) { cat = 'Overweight'; cls = 'overweight'; }
  else { cat = 'Obese'; cls = 'obese'; }
  document.getElementById('bmi-display').style.display = 'flex';
  document.getElementById('bmi-value').textContent = bmi;
  document.getElementById('bmi-chip').className = `bmi-chip bmi-${cls}`;
  document.getElementById('bmi-chip').textContent = cat;
}
async function generateLifestylePlan() {
  const name = document.getElementById('ls-name').value.trim() || 'User';
  const age = document.getElementById('ls-age').value;
  const height = document.getElementById('ls-height').value;
  const weight = document.getElementById('ls-weight').value;
  if (!age || !height || !weight) { showToast('Please fill in age, height and weight', 'warning'); return; }
  const conditions = Array.from(document.querySelectorAll('.ls-cond-input:checked')).map(i => i.value);
  const activity = document.querySelector('[name="ls-activity"]:checked')?.value || 'Sedentary';
  const goal = document.querySelector('[name="ls-goal"]:checked')?.value || 'Stay Healthy';
  const diet = document.querySelector('[name="ls-diet"]:checked')?.value || 'Vegetarian';
  showLoading('Generating your personalized 7-day plan...');
  try {
    const res = await fetch(`${API}/api/lifestyle/plan`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ age, height, weight, conditions, activity, goal, diet, language: getActiveLanguage() }) });
    const data = res.ok ? await res.json() : getDemoLifestyleData(name, goal, diet);
    renderLifestylePlan(data, name, goal, activity);
    saveHistory('lifestyle', { summary: `${goal} plan for ${name}`, badge: '7-Day Plan', badgeType: 'safe', fullData: data, name, goal, activity });
    showToast('Your 7-day plan is ready!', 'success');
  } catch {
    renderLifestylePlan(getDemoLifestyleData(name, goal, diet), name, goal, activity);
  }
  hideLoading();
}
function getDemoLifestyleData(name, goal, diet) {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  return { bmi: 22.8, plan: days.map((day, i) => ({ day, morning: { time: '6:30 AM', drink: 'Warm lemon water with honey', activity: '10 min light stretching' }, meals: { breakfast: `Oatmeal with nuts and fruits (320 kcal)`, snack1: 'Handful of almonds', lunch: `Mixed dal with brown rice and salad (450 kcal)`, snack2: 'Green tea with a fruit', dinner: `Vegetable soup with 2 chapatis (380 kcal)`, total_calories: 1800 }, exercise: { type: i % 2 === 0 ? 'Cardio' : 'Strength Training', duration: '45 minutes', intensity: i < 4 ? 'Moderate' : 'Low-Moderate', routine: ['Warm up 5 min', 'Main workout 35 min', 'Cool down 5 min'] }, wellness: { water: '2.5 Liters', sleep: '7-8 hours', tip: 'Practice deep breathing for 5 minutes before bed.' } })) }
}
function renderLifestylePlan(data, name, goal, activity) {
  document.getElementById('lifestyle-form').style.display = 'none';
  document.getElementById('lifestyle-result').style.display = 'block';
  const bmi = document.getElementById('bmi-value').textContent;
  const bmiCat = document.getElementById('bmi-chip').textContent;
  document.getElementById('ls-user-bar').innerHTML = `
    <span style="font-weight:700;font-size:15px;margin-right:8px;">${name}</span>
    ${bmi ? `<span class="badge badge-safe">BMI: ${bmi} (${bmiCat})</span>` : ''}
    <span class="badge badge-info">🎯 ${goal}</span>
    <span class="badge badge-purple">🏃 ${activity}</span>`;
  const days = data.plan || [];
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  document.getElementById('ls-day-tabs').innerHTML = days.map((d, i) => `<button class="day-tab ${i === 0 ? 'active' : ''}" onclick="showDayPlan(${i},this)">${dayNames[i] || d.day}</button>`).join('');
  window.lsPlanData = days;
  showDayPlanContent(0);
}
function showDayPlan(idx, btn) {
  document.querySelectorAll('.day-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  showDayPlanContent(idx);
}
function showDayPlanContent(idx) {
  const d = window.lsPlanData[idx];
  if (!d) return;
  document.getElementById('ls-day-content').innerHTML = `
    <div class="day-plan-grid">
      <div class="day-plan-card morning">
        <div class="day-plan-title"><i class="fas fa-sun" style="color:#fbbf24;"></i>🌅 Morning Routine</div>
        <div class="day-plan-item">⏰ Wake up: ${d.morning?.time || '6:30 AM'}</div>
        <div class="day-plan-item">💧 Morning drink: ${d.morning?.drink || 'Warm lemon water'}</div>
        <div class="day-plan-item">🧘 Activity: ${d.morning?.activity || 'Stretching'}</div>
      </div>
      <div class="day-plan-card meal">
        <div class="day-plan-title"><i class="fas fa-utensils" style="color:#4ade80;"></i>🍽️ Meal Plan</div>
        <div class="day-plan-item">🌅 Breakfast: ${d.meals?.breakfast || 'Oatmeal'}</div>
        <div class="day-plan-item">🍎 Snack: ${d.meals?.snack1 || 'Almonds'}</div>
        <div class="day-plan-item">☀️ Lunch: ${d.meals?.lunch || 'Dal rice'}</div>
        <div class="day-plan-item">🌆 Snack: ${d.meals?.snack2 || 'Fruit'}</div>
        <div class="day-plan-item">🌙 Dinner: ${d.meals?.dinner || 'Soup chapati'}</div>
        <div style="margin-top:8px;"><span class="badge badge-safe">~${d.meals?.total_calories || 1800} kcal</span></div>
      </div>
      <div class="day-plan-card exercise">
        <div class="day-plan-title"><i class="fas fa-dumbbell" style="color:#2dd4bf;"></i>🏃 Exercise</div>
        <div class="day-plan-item">Type: <strong>${d.exercise?.type || 'Cardio'}</strong></div>
        <div class="day-plan-item">Duration: ${d.exercise?.duration || '45 min'}</div>
        <div class="day-plan-item">Intensity: ${d.exercise?.intensity || 'Moderate'}</div>
        ${(d.exercise?.routine || []).map((r, i) => `<div class="day-plan-item">${i + 1}. ${r}</div>`).join('')}
      </div>
      <div class="day-plan-card wellness">
        <div class="day-plan-title"><i class="fas fa-droplet" style="color:#60a5fa;"></i>💧 Wellness</div>
        <div class="day-plan-item">💧 Water: <strong>${d.wellness?.water || '2.5L'}</strong></div>
        <div class="day-plan-item">😴 Sleep: <strong>${d.wellness?.sleep || '7-8 hours'}</strong></div>
        <div style="margin-top:10px;padding:10px;background:rgba(96,165,250,0.1);border-radius:8px;font-size:12px;color:#93c5fd;line-height:1.6;">
          💡 ${d.wellness?.tip || 'Practice mindfulness for 5 minutes before bed.'}
        </div>
      </div>
    </div>`;
}
function lsReset() {
  document.getElementById('lifestyle-form').style.display = 'block';
  document.getElementById('lifestyle-result').style.display = 'none';
}

// ══════════════════════════════════════════════
// SEASONAL AWARENESS
// ══════════════════════════════════════════════
function detectSeason() {
  if (!navigator.geolocation) { renderSeasonalContent('Bhubaneswar, Odisha'); return; }
  showLoading('Detecting your location...');
  navigator.geolocation.getCurrentPosition(async pos => {
    hideLoading();
    await loadSeasonalData(pos.coords.latitude, pos.coords.longitude);
  }, () => { hideLoading(); loadSeasonalData(20.2961, 85.8245); });
}
async function loadSeasonalData(lat, lon) {
  const month = new Date().getMonth() + 1;
  showLoading('Loading seasonal health data...');
  try {
    const res = await fetch(`${API}/api/seasonal/alerts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ latitude: lat, longitude: lon, month, language: getActiveLanguage() }) });
    const data = res.ok ? await res.json() : getDemoSeasonalData(month);
    renderSeasonalContent('Your Location', data);
  } catch {
    renderSeasonalContent('Bhubaneswar, Odisha', getDemoSeasonalData(month));
  }
  hideLoading();
}
function getDemoSeasonalData(month) {
  const isMonsoon = month >= 6 && month <= 9, isWinter = month <= 2 || month >= 11, isSummer = month >= 3 && month <= 5;
  if (isMonsoon) return { season: 'Monsoon', alert: '🦟 High risk of Dengue, Malaria & Cholera in your area', diseases: [{ name: 'Dengue Fever', risk: 'High', symptoms: ['High fever', 'Severe headache', 'Joint pain', 'Rash'], prevention: 'Use mosquito repellent, wear full sleeves, eliminate stagnant water' }, { name: 'Malaria', risk: 'High', symptoms: ['Fever with chills', 'Sweating', 'Headache', 'Vomiting'], prevention: 'Sleep under mosquito nets, take prophylaxis if prescribed' }, { name: 'Cholera', risk: 'Medium', symptoms: ['Watery diarrhoea', 'Dehydration', 'Muscle cramps'], prevention: 'Drink only boiled water, avoid street food' }], dos: ['Use mosquito repellent daily', 'Keep surroundings clean and dry', 'Drink only boiled/filtered water', 'Eat freshly cooked food', 'Cover water storage containers'], donts: ['Dont let water stagnate near your home', 'Avoid eating raw food from outside', 'Dont ignore fever lasting more than 2 days', 'Avoid wading in flood water'], diet_tips: ['Eat warm soups and herbal teas', 'Include turmeric in your diet — it boosts immunity', 'Avoid raw salads and uncooked vegetables', 'Eat light, easily digestible meals'], season_css: 'monsoon' };
  if (isWinter) return { season: 'Winter', alert: '🤧 Flu, Cold & Respiratory infections are common this season', diseases: [{ name: 'Influenza (Flu)', risk: 'High', symptoms: ['Fever', 'Cough', 'Body ache', 'Fatigue'], prevention: 'Get annual flu vaccine, wash hands frequently' }, { name: 'Cold & Rhinitis', risk: 'High', symptoms: ['Runny nose', 'Sneezing', 'Sore throat'], prevention: 'Keep warm, avoid cold drinks' }, { name: 'Asthma Attacks', risk: 'Medium', symptoms: ['Wheezing', 'Breathlessness', 'Chest tightness'], prevention: 'Carry inhaler, avoid cold air exposure' }], dos: ['Get flu vaccination', 'Keep yourself warm at all times', 'Drink warm fluids throughout the day', 'Wash hands frequently with soap', 'Exercise indoors to stay active'], donts: ['Dont go out in extreme cold without protective clothing', 'Avoid cold water and ice cream', 'Dont ignore persistent cough or fever', 'Avoid close contact with sick people'], diet_tips: ['Drink hot ginger tea with honey', 'Eat citrus fruits rich in Vitamin C', 'Include garlic and turmeric in cooking', 'Consume warm soups and broths'], season_css: 'winter' };
  return { season: 'Summer', alert: '🥵 Heatstroke, Dehydration & Food poisoning risk is high', diseases: [{ name: 'Heat Stroke', risk: 'High', symptoms: ['High body temperature', 'Confusion', 'No sweating', 'Rapid heartbeat'], prevention: 'Stay hydrated, avoid outdoor activity 12pm–4pm' }, { name: 'Dehydration', risk: 'High', symptoms: ['Dizziness', 'Dark urine', 'Dry mouth', 'Fatigue'], prevention: 'Drink at least 3-4 litres of water daily' }, { name: 'Food Poisoning', risk: 'Medium', symptoms: ['Vomiting', 'Diarrhoea', 'Stomach cramps', 'Fever'], prevention: 'Eat freshly prepared food, refrigerate leftovers' }], dos: ['Drink at least 3-4 litres of water daily', 'Stay indoors between 12pm and 4pm', 'Wear light-coloured loose clothing', 'Eat light, small meals frequently', 'Carry water whenever going out'], donts: ['Dont skip meals or water', 'Avoid heavy outdoor exercise in peak heat', 'Dont eat stale or uncovered food', 'Avoid alcohol and carbonated drinks'], diet_tips: ['Drink coconut water, lassi and buttermilk', 'Eat watermelon and cucumber daily', 'Include mint and coriander in meals', 'Avoid spicy and oily foods'], season_css: 'summer' };
}
function shareSeasonal() {
  const data = window.lastSeasonalData;
  if (!data) return;
  const text = `🏥 MediMitra ${data.season} Health Alert\n\n` +
    `⚠️ Alert: ${data.alert}\n\n` +
    `✅ Top 3 Do's:\n${(data.dos || []).slice(0, 3).map(d => '• ' + d).join('\n')}\n\n` +
    `❌ Top 3 Don'ts:\n${(data.donts || []).slice(0, 3).map(d => '• ' + d).join('\n')}\n\n` +
    `🥗 Diet Tip:\n${(data.diet_tips || [])[0] || 'Eat seasonal fruits'}\n\n` +
    `Stay safe! Check more on MediMitra.`;

  if (navigator.share) {
    navigator.share({
      title: `MediMitra: ${data.season} Health Guide`,
      text: text,
      url: window.location.href
    }).catch(console.error);
  } else {
    // Fallback for browsers without navigator.share
    const dummy = document.createElement('textarea');
    dummy.value = text;
    document.body.appendChild(dummy);
    dummy.select();
    try {
      document.execCommand('copy');
      showToast('Info copied to clipboard! Share it anywhere.', 'success');
    } catch (err) {
      showToast('Could not copy automatically.', 'error');
    }
    document.body.removeChild(dummy);
  }
}
function renderSeasonalContent(location, data) {
  window.lastSeasonalData = data;
  const seasonEmojis = { Monsoon: '🌧️', Winter: '❄️', Summer: '☀️' };
  document.getElementById('seasonal-content').innerHTML = `
    <div class="season-banner ${data.season_css || 'summer'}">
      <div class="season-icon">${seasonEmojis[data.season] || '🌤️'}</div>
      <div class="season-content">
        <div class="season-location">📍 ${location}</div>
        <div class="season-name">${data.season} Season</div>
        <div class="season-alert">${data.alert || ''}</div>
      </div>
    </div>
    <div class="grid-2" style="margin-bottom:24px;">
      ${(data.diseases || []).map(d => `
        <div class="card card-lg">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <h3 style="font-family:var(--font-display);font-size:16px;font-weight:700;">${d.name}</h3>
            <span class="badge badge-${d.risk === 'High' ? 'danger' : d.risk === 'Medium' ? 'warning' : 'safe'}">${d.risk} Risk</span>
          </div>
          <ul style="margin:0 0 12px 0;padding-left:16px;color:var(--text-secondary);font-size:13px;line-height:1.8;">${(d.symptoms || []).map(s => `<li>${s}</li>`).join('')}</ul>
          <div style="background:rgba(26,122,74,0.08);border:1px solid rgba(26,122,74,0.2);border-radius:8px;padding:10px;font-size:12px;color:#4ade80;">
            <strong>Prevention:</strong> ${d.prevention}
          </div>
        </div>`).join('')}
    </div>
    <div class="grid-2" style="margin-bottom:24px;">
      <div>
        <h3 style="font-family:var(--font-display);font-size:17px;font-weight:700;margin-bottom:12px;">✅ Do's This Season</h3>
        ${(data.dos || []).map(d => `<div class="dos-card"><i class="fas fa-check" style="color:#4ade80;flex-shrink:0;margin-top:2px;"></i><span style="font-size:13px;">${d}</span></div>`).join('')}
      </div>
      <div>
        <h3 style="font-family:var(--font-display);font-size:17px;font-weight:700;margin-bottom:12px;">❌ Don'ts This Season</h3>
        ${(data.donts || []).map(d => `<div class="donts-card"><i class="fas fa-times" style="color:#f87171;flex-shrink:0;margin-top:2px;"></i><span style="font-size:13px;">${d}</span></div>`).join('')}
      </div>
    </div>
    <div class="card card-lg">
      <h3 style="font-family:var(--font-display);font-size:17px;font-weight:700;margin-bottom:16px;">🍽️ What to Eat This Season</h3>
      <div class="grid-3">
        ${(data.diet_tips || []).map((t, i) => `
          <div style="background:rgba(26,122,74,0.06);border:1px solid rgba(26,122,74,0.15);border-radius:12px;padding:16px;font-size:13px;color:var(--text-secondary);line-height:1.6;">
            <div style="font-size:24px;margin-bottom:8px;">${['🥗', '🍵', '🌿', '🍊'][i] || '🥦'}</div>${t}
          </div>`).join('')}
      </div>
    </div>
    <div style="margin-top:16px;padding:12px 18px;background:rgba(26,122,74,0.08);border:1px solid rgba(26,122,74,0.2);border-radius:10px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
      <p style="font-size:12px;color:var(--text-muted);">🤖 AI-generated seasonal health alerts based on your location. Last updated: ${new Date().toLocaleDateString('en-IN')}</p>
      <button class="btn btn-secondary" style="font-size:12px;padding:6px 14px;" onclick="shareSeasonal()"><i class="fas fa-share-alt"></i> Share</button>
    </div>`;
}

// ══════════════════════════════════════════════
// NEARBY HEALTHCARE
// ══════════════════════════════════════════════
let nearbyRadius = 1, nearbyFilter = 'all', nearbyData = [];
function detectNearby() {
  showLoading('Detecting your location...');
  if (!navigator.geolocation) { hideLoading(); loadNearbyData(20.2961, 85.8245); return; }
  navigator.geolocation.getCurrentPosition(pos => {
    hideLoading();
    loadNearbyData(pos.coords.latitude, pos.coords.longitude);
  }, () => { hideLoading(); loadNearbyData(20.2961, 85.8245); });
}
async function loadNearbyData(lat, lon) {
  window.lastNearbyLat = lat;
  window.lastNearbyLon = lon;

  showLoading('Finding nearby healthcare...');
  try {
    // Always fetch with 10km (max) so we have all data cached
    const res = await fetch(`${API}/api/nearby/find`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: lat,
        longitude: lon,
        type: 'all',
        radius: 10       // Always fetch max radius
      })
    });

    if (res.ok) {
      const json = await res.json();
      allNearbyData = json.places || [];
    } else {
      allNearbyData = getDemoNearbyData();
    }
  } catch {
    allNearbyData = getDemoNearbyData();
  }

  hideLoading();

  // Apply current radius filter on cached data
  nearbyData = allNearbyData.filter(p => p.distance <= nearbyRadius);

  document.getElementById('nearby-location').style.display = 'block';
  document.getElementById('nearby-location').textContent =
    `📍 Found ${nearbyData.length} locations within ${nearbyRadius} km`;

  renderNearbyList();
  renderNearbyMap(lat, lon);
  showToast(`Found ${allNearbyData.length} total locations nearby`, 'success');
}
// Cache of ALL fetched data (max radius fetch)
let allNearbyData = [];

function getDemoNearbyData() {
  return [
    { name: 'AIIMS Bhubaneswar', type: 'hospital', address: 'Sijua, Patrapada, Bhubaneswar', distance: 1.2, rating: 4.5, open: true, lat: 20.2681, lon: 85.8154 },
    { name: 'Apollo Clinic', type: 'clinic', address: 'Saheed Nagar, Bhubaneswar', distance: 0.8, rating: 4.3, open: true, lat: 20.2961, lon: 85.8402 },
    { name: 'MedPlus Pharmacy', type: 'pharmacy', address: 'Nayapalli, Bhubaneswar', distance: 0.5, rating: 4.1, open: true, lat: 20.2891, lon: 85.8201 },
    { name: 'Capital Hospital', type: 'hospital', address: 'Unit 6, Bhubaneswar', distance: 2.1, rating: 4.2, open: false, lat: 20.2701, lon: 85.8421 },
    { name: 'LifeCare Clinic', type: 'clinic', address: 'Khandagiri, Bhubaneswar', distance: 1.5, rating: 4.0, open: true, lat: 20.2601, lon: 85.7901 },
    { name: 'Jan Aushadhi Store', type: 'pharmacy', address: 'VSS Nagar, Bhubaneswar', distance: 0.9, rating: 4.4, open: true, lat: 20.3011, lon: 85.8351 },
  ];
}
function filterNearby(type, btn) {
  nearbyFilter = type;
  document.querySelectorAll('.type-pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');

  // Filter from ALL cached data using both radius AND type
  nearbyData = allNearbyData.filter(p => {
    const withinRadius = p.distance <= nearbyRadius;
    const matchesType = type === 'all' ? true : p.type === type;
    return withinRadius && matchesType;
  });

  renderNearbyList();
  showToast(`Showing ${nearbyData.length} ${type === 'all' ? 'locations' : type + 's'}`, 'info');
}
function setRadius(km, btn) {
  nearbyRadius = km;
  document.querySelectorAll('.radius-pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');

  if (!window.lastNearbyLat || !window.lastNearbyLon) {
    showToast('Click "Detect My Location" first', 'warning');
    return;
  }

  // Filter locally from cached data — NO new API call
  const filtered = allNearbyData.filter(p => p.distance <= km);
  nearbyData = filtered;

  document.getElementById('nearby-location').textContent =
    `📍 Found ${filtered.length} locations within ${km} km`;

  renderNearbyList();

  if (filtered.length === 0) {
    showToast(`No locations within ${km} km. Try a larger radius.`, 'warning');
  } else {
    showToast(`Showing ${filtered.length} locations within ${km} km`, 'success');
  }
}
// Render list from existing nearbyData with current filter applied
function renderNearbyList() {
  // Apply type filter on existing data
  const filtered = nearbyFilter === 'all'
    ? nearbyData
    : nearbyData.filter(p => p.type === nearbyFilter);

  const typeColors = { hospital: 'danger', clinic: 'warning', pharmacy: 'safe' };
  const typeEmojis = { hospital: '🏥', clinic: '🩺', pharmacy: '💊' };

  if (!filtered.length) {
    // Show helpful message based on why it's empty
    const reason = nearbyData.length === 0
      ? 'No healthcare locations found in this area. Try increasing the radius.'
      : `No ${nearbyFilter}s found within ${nearbyRadius} km. Try "All" or increase radius.`;

    document.getElementById('nearby-places').innerHTML = `
      <div style="text-align:center;padding:32px;color:var(--text-muted);font-size:14px;">
        <i class="fas fa-map-pin" style="font-size:28px;margin-bottom:12px;display:block;opacity:0.4;"></i>
        <p style="font-weight:600;margin-bottom:6px;">No results</p>
        <p style="font-size:12px;">${reason}</p>
      </div>`;
    return;
  }

  document.getElementById('nearby-places').innerHTML = filtered.map(p => `
    <div class="place-card ${p.type}">
      <div class="place-name">${typeEmojis[p.type] || '🏥'} ${p.name}</div>
      <div class="place-address">${p.address}</div>
      <div class="place-meta">
        <span class="badge badge-info">${p.distance} km</span>
        <span class="badge badge-${p.open ? 'safe' : 'danger'}">${p.open ? 'Open' : 'Closed'}</span>
        <span style="font-size:12px;color:#fbbf24;">⭐ ${p.rating}</span>
      </div>
      <div style="display:flex;gap:6px;margin-top:10px;">
        <button class="btn btn-secondary" style="padding:5px 10px;font-size:11px;flex:1;justify-content:center;"
          onclick="showToast('Marker highlighted on map','info')">
          <i class="fas fa-map-marker-alt"></i> View
        </button>
        <a class="btn btn-primary" style="padding:5px 10px;font-size:11px;flex:1;justify-content:center;text-decoration:none;"
          href="https://www.openstreetmap.org/directions?to=${p.lat},${p.lon}"
          target="_blank">
          <i class="fas fa-directions"></i> Directions
        </a>
      </div>
    </div>`).join('');
}
let leafletMap = null;
let leafletMarkers = [];

function renderNearbyMap(lat, lon) {
  const mapPanel = document.getElementById('nearby-map-panel');
  // Create the map div
  mapPanel.innerHTML = `<div id="leaflet-map"></div>`;

  // Small delay to let DOM render
  setTimeout(() => {
    // If map already exists, destroy it first
    if (leafletMap) {
      leafletMap.remove();
      leafletMap = null;
    }

    // Initialize Leaflet map
    leafletMap = L.map('leaflet-map').setView([lat, lon], 14);

    // Free OpenStreetMap tiles — no API key needed!
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(leafletMap);

    // User's current location — blue pulsing marker
    const userIcon = L.divIcon({
      className: '',
      html: `<div style="
        width:16px;height:16px;background:#3b82f6;border-radius:50%;
        border:3px solid #fff;box-shadow:0 0 0 4px rgba(59,130,246,0.3);
        animation:pulse-blue 1.5s infinite;">
      </div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });
    L.marker([lat, lon], { icon: userIcon })
      .addTo(leafletMap)
      .bindPopup('<b>📍 Your Location</b>')
      .openPopup();

    // Place markers for nearby results
    leafletMarkers = [];
    const typeColors = { hospital: '#dc2626', clinic: '#d97706', pharmacy: '#16a34a' };
    const typeEmojis = { hospital: '🏥', clinic: '🩺', pharmacy: '💊' };

    nearbyData.forEach(place => {
      if (!place.lat || !place.lon) return;
      const color = typeColors[place.type] || '#1a7a4a';
      const emoji = typeEmojis[place.type] || '🏥';

      const placeIcon = L.divIcon({
        className: '',
        html: `<div style="
          background:${color};color:#fff;
          border-radius:50% 50% 50% 0;transform:rotate(-45deg);
          width:32px;height:32px;display:flex;align-items:center;justify-content:center;
          box-shadow:0 2px 8px rgba(0,0,0,0.4);border:2px solid #fff;">
          <span style="transform:rotate(45deg);font-size:14px;">${emoji}</span>
        </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });

      const marker = L.marker([place.lat, place.lon], { icon: placeIcon })
        .addTo(leafletMap)
        .bindPopup(`
          <div style="font-family:sans-serif;min-width:180px;">
            <strong style="font-size:14px;">${emoji} ${place.name}</strong><br/>
            <span style="font-size:12px;color:#666;">${place.address}</span><br/><br/>
            <span style="font-size:12px;">📏 ${place.distance} km away</span><br/>
            <span style="font-size:12px;">⭐ ${place.rating}</span>
            <span style="font-size:12px;margin-left:8px;color:${place.open ? 'green' : 'red'};">
              ${place.open ? '✅ Open' : '❌ Closed'}
            </span><br/><br/>
            <a href="https://www.openstreetmap.org/directions?to=${place.lat},${place.lon}"
               target="_blank"
               style="background:#1a7a4a;color:#fff;padding:5px 10px;border-radius:6px;font-size:12px;text-decoration:none;">
              🗺️ Get Directions
            </a>
          </div>`);

      leafletMarkers.push(marker);
    });

  }, 100);
}

function triggerEmergency() {
  alert(
    '🚨 MEDICAL EMERGENCY ALERT\n\n' +
    '📞 Call 112 — National Emergency Helpline\n' +
    '🏥 For MLC (Medico-Legal Case) & Ambulance\n\n' +
    '📞 Call 108 — Free Ambulance Service\n' +
    '📞 Call 102 — National Ambulance Service\n\n' +
    '⚠️ Inform hospital: Patient needs immediate attention.\n' +
    'Carry a valid ID proof for MLC registration.\n\n' +
    'Stay calm. Help is on the way. ✅'
  );
}

// ══════════════════════════════════════════════
// AUTHENTICATION & PROFILE SYSTEM
// ══════════════════════════════════════════════
async function initGoogleSignIn() {
  try {
    const res = await fetch(`${API}/api/auth/config`);
    if (!res.ok) throw new Error('Could not fetch config');
    const config = await res.json();

    if (!config.google_client_id || config.google_client_id === 'your_google_client_id_here') {
      console.warn('Google Client ID not configured.');
      return;
    }

    google.accounts.id.initialize({
      client_id: config.google_client_id,
      callback: handleCredentialResponse
    });

    google.accounts.id.renderButton(
      document.getElementById("google-signin-btn"),
      { theme: "outline", size: "medium", shape: "pill" }
    );
  } catch (e) {
    console.error('Google Sign-In initialization failed:', e);
  }
}

async function handleCredentialResponse(response) {
  showLoading('Signing in with Google...');
  try {
    const res = await fetch(`${API}/api/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: response.credential })
    });

    if (!res.ok) throw new Error('Backend auth failed');

    const data = await res.json();
    userSession.jwt = data.jwt;
    userSession.user_id = data.user_id;
    userSession.email = data.email;
    userSession.name = data.name;
    userSession.picture = data.picture;

    // Update Nav UI
    document.getElementById('google-signin-btn').style.display = 'none';
    document.getElementById('user-profile-nav').style.display = 'flex';
    document.getElementById('user-avatar').src = data.picture || 'https://www.gravatar.com/avatar/?d=mp';
    document.getElementById('user-name').textContent = data.name || 'User';

    // Update Health Profile Tab UI
    document.getElementById('profile-logged-out').style.display = 'none';
    document.getElementById('profile-logged-in').style.display = 'block';

    showToast(`Welcome back, ${data.name}!`, 'success');

    await loadHealthProfile();
  } catch (e) {
    showToast('Authentication failed. Please try again.', 'error');
    console.error(e);
  } finally {
    hideLoading();
  }
}

function signOut() {
  userSession = { jwt: null, user_id: null, email: null, name: null, picture: null };

  document.getElementById('google-signin-btn').style.display = 'block';
  document.getElementById('user-profile-nav').style.display = 'none';

  document.getElementById('profile-logged-out').style.display = 'block';
  document.getElementById('profile-logged-in').style.display = 'none';

  // Reset inputs
  document.getElementById('profile-age').value = '';
  document.getElementById('profile-blood-group').value = '';
  document.getElementById('profile-allergies').value = '';
  document.getElementById('profile-chronic-conditions').value = '';
  document.getElementById('profile-current-medications').value = '';
  document.getElementById('profile-emergency-contact').value = '';

  showToast('Signed out successfully.', 'info');
  showSection('dashboard');
}

async function loadHealthProfile() {
  if (!userSession.jwt) return;
  try {
    const res = await fetch(`${API}/api/profile/me`, {
      headers: { 'Authorization': `Bearer ${userSession.jwt}` }
    });
    if (res.status === 404) return;
    if (!res.ok) throw new Error('Failed to fetch profile');
    const data = await res.json();

    document.getElementById('profile-age').value = data.age || '';
    document.getElementById('profile-blood-group').value = data.blood_group || '';
    document.getElementById('profile-allergies').value = (data.allergies || []).join(', ');
    document.getElementById('profile-chronic-conditions').value = (data.chronic_conditions || []).join(', ');
    document.getElementById('profile-current-medications').value = (data.current_medications || []).join(', ');
    document.getElementById('profile-emergency-contact').value = data.emergency_contact || '';
  } catch (e) {
    showToast('Failed to load health profile.', 'error');
    console.error(e);
  }
}

async function saveHealthProfile() {
  if (!userSession.jwt) {
    showToast('Please sign in first.', 'warning');
    return;
  }
  const ageVal = document.getElementById('profile-age').value;
  const age = ageVal ? parseInt(ageVal, 10) : null;
  const blood_group = document.getElementById('profile-blood-group').value;
  const allergies = document.getElementById('profile-allergies').value.split(',').map(s => s.trim()).filter(s => s);
  const chronic_conditions = document.getElementById('profile-chronic-conditions').value.split(',').map(s => s.trim()).filter(s => s);
  const current_medications = document.getElementById('profile-current-medications').value.split(',').map(s => s.trim()).filter(s => s);
  const emergency_contact = document.getElementById('profile-emergency-contact').value.trim();

  showLoading('Saving health profile...');
  try {
    const res = await fetch(`${API}/api/profile/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userSession.jwt}`
      },
      body: JSON.stringify({
        age,
        blood_group,
        allergies,
        chronic_conditions,
        current_medications,
        emergency_contact
      })
    });
    if (!res.ok) throw new Error('Save failed');
    showToast('Health profile saved successfully!', 'success');
  } catch (e) {
    showToast('Failed to save health profile.', 'error');
    console.error(e);
  } finally {
    hideLoading();
  }
}

// ══════════════════════════════════════════════
// PDF GENERATION SYSTEM
// ══════════════════════════════════════════════
async function triggerBlobDownload(url, payload, filename) {
  showLoading('Generating PDF report...');
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('PDF generation failed');
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
    showToast('PDF downloaded successfully!', 'success');
  } catch (e) {
    showToast('Error generating PDF report.', 'error');
    console.error(e);
  } finally {
    hideLoading();
  }
}

function downloadSymptomPdf() {
  const history = getHistory('symptom');
  if (history.length === 0) {
    showToast('No active report to download.', 'warning');
    return;
  }
  const data = history[0].fullData;
  if (!data) {
    showToast('No report data found.', 'warning');
    return;
  }
  triggerBlobDownload(`${API}/api/symptom/download-pdf`, data, 'symptom_report.pdf');
}

function downloadLifestylePdf() {
  const history = getHistory('lifestyle');
  if (history.length === 0) {
    showToast('No active plan to download.', 'warning');
    return;
  }
  const data = history[0].fullData;
  if (!data) {
    showToast('No plan data found.', 'warning');
    return;
  }
  triggerBlobDownload(`${API}/api/lifestyle/download-pdf`, data, 'lifestyle_plan.pdf');
}

// ══════════════════════════════════════════════
// GLOBAL LANGUAGE SYSTEM
// ══════════════════════════════════════════════

// Language display names for UI
const LANG_NAMES = {
  'English': 'English',
  'Hindi': 'हिन्दी',
  'Odia': 'ଓଡ଼ିଆ',
  'Bengali': 'বাংলা',
  'Tamil': 'தமிழ்',
  'Telugu': 'తెలుగు',
  'Marathi': 'ମରାଠୀ'
};

// Current global language (default English)
let globalLanguage = localStorage.getItem('medimitra_language') || 'English';

// ── UI TRANSLATION DICTIONARY ─────────────────────────────────────────────
const UI_TRANSLATIONS = {
  Hindi: {
    'nav.diagnostic_suite': 'निदान सुविधा', 'nav.dashboard': 'डैशबोर्ड', 'nav.symptom': 'लक्षण जांचकर्ता',
    'nav.prescription': 'पर्चा पाठक', 'nav.drug': 'दवा परस्पर क्रिया', 'nav.health_care': 'स्वास्थ्य सेवा',
    'nav.scanner': 'दवा स्कैनर', 'nav.lifestyle': 'जीवनशैली सलाहकार', 'nav.seasonal': 'मौसमी जागरूकता',
    'nav.nearby': 'पास के अस्पताल', 'nav.personal_space': 'व्यक्तिगत', 'nav.profile': 'स्वास्थ्य प्रोफाइल',
    'nav.disclaimer': '⚕️ केवल AI उपकरण। कोई भी चिकित्सा निर्णय लेने से पहले हमेशा डॉक्टर से सलाह लें।',
    'dash.badge': 'AI-संचालित स्वास्थ्य साथी', 'dash.title': 'आपका स्वास्थ्य,', 'dash.title_span': 'हमारी प्राथमिकता',
    'dash.subtitle': 'बेहतर स्वास्थ्य निर्णयों के लिए 7 AI उपकरण — लक्षण जांच, दवा स्कैनिंग और भी बहुत कुछ। आपकी भाषा में।',
    'dash.ai_features': 'AI सुविधाएं', 'dash.languages': 'भाषाएं', 'dash.realtime': 'रीयल-टाइम परिणाम',
    'dash.what_today': 'आज मैं आपकी कैसे मदद कर सकता हूं?', 'dash.click_feature': 'तुरंत शुरू करने के लिए किसी सुविधा पर क्लिक करें',
    'dash.disclaimer_title': 'चिकित्सा अस्वीकरण:', 'dash.disclaimer_body': 'MediMitra केवल AI-जनित स्वास्थ्य जानकारी प्रदान करता है। यह पेशेवर चिकित्सा सलाह का विकल्प नहीं है।',
    'feat.symptom.title': 'लक्षण जांचकर्ता', 'feat.symptom.desc': 'अपने लक्षण बताएं और तुरंत AI स्वास्थ्य मार्गदर्शन प्राप्त करें।',
    'feat.prescription.title': 'पर्चा पाठक', 'feat.prescription.desc': 'पर्चे की फोटो अपलोड करें और अपनी भाषा में व्याख्या प्राप्त करें।',
    'feat.drug.title': 'दवा परस्पर क्रिया', 'feat.drug.desc': 'जांचें कि आपकी दवाएं एक साथ सुरक्षित हैं या नहीं।',
    'feat.scanner.title': 'दवा स्कैनर', 'feat.scanner.desc': 'दवा पैकेजिंग को स्कैन करें और OpenFDA डेटाबेस में सत्यापित करें।',
    'feat.lifestyle.title': 'जीवनशैली सलाहकार', 'feat.lifestyle.desc': 'आपके लिए व्यक्तिगत 7-दिन का आहार, व्यायाम और स्वास्थ्य योजना प्राप्त करें।',
    'feat.seasonal.title': 'मौसमी जागरूकता', 'feat.seasonal.desc': 'आपके स्थान और मौसम के अनुसार प्रासंगिक स्वास्थ्य अलर्ट दिखाता है।',
    'feat.nearby.title': 'पास के अस्पताल', 'feat.nearby.desc': 'इंटरएक्टिव मानचित्र पर पास के अस्पताल, क्लीनिक और फार्मेसियां खोजें।',
    'feat.feedback.title': 'उपयोगकर्ता प्रतिक्रिया', 'feat.open': 'खोलें →',
    'sec.symptom.title': '🤒 लक्षण जांचकर्ता', 'sec.symptom.subtitle': 'अपने लक्षण बताएं और AI स्वास्थ्य मार्गदर्शन प्राप्त करें',
    'sec.symptom.feeling_label': 'आप कैसा महसूस कर रहे हैं?', 'sec.symptom.placeholder': 'जैसे: 2 दिन से बुखार, सिर दर्द, थकान...',
    'sec.symptom.common_label': 'सामान्य लक्षण (जोड़ने के लिए क्लिक करें)', 'sec.symptom.duration_label': 'आपको ये लक्षण कितने समय से हैं?',
    'sec.symptom.dur_1': '1 दिन से कम', 'sec.symptom.dur_2': '1–3 दिन', 'sec.symptom.dur_3': '3–7 दिन', 'sec.symptom.dur_4': '1 सप्ताह से अधिक',
    'sec.symptom.severity_label': 'गंभीरता (1–10)', 'sec.symptom.mild': 'हल्का', 'sec.symptom.moderate': 'मध्यम', 'sec.symptom.severe': 'गंभीर',
    'sec.symptom.btn': 'लक्षण विश्लेषण करें', 'sec.symptom.ready_title': 'विश्लेषण के लिए तैयार',
    'sec.symptom.ready_desc': 'बाईं तरफ अपने लक्षण भरें और विश्लेषण पर क्लिक करें।',
    'sec.symptom.tab1': 'यह क्या है', 'sec.symptom.tab2': 'क्या करें', 'sec.symptom.tab3': 'डॉक्टर से कब मिलें',
    'sec.symptom.find_clinic': 'पास का क्लीनिक खोजें', 'sec.symptom.check_interactions': 'परस्पर क्रिया जांचें', 'common.download_pdf': 'PDF डाउनलोड करें',
    'sec.rx.title': '📄 पर्चा पाठक', 'sec.rx.subtitle': 'अपना पर्चा अपलोड करें और अपनी भाषा में व्याख्या प्राप्त करें',
    'sec.rx.upload_title': 'अपना पर्चा यहां खींचें और छोड़ें', 'sec.rx.upload_hint': 'या ब्राउज़ करने के लिए क्लिक करें — JPG, PNG, PDF',
    'sec.rx.camera_btn': 'कैमरे से फोटो लें', 'sec.rx.btn': 'मेरा पर्चा पढ़ें',
    'sec.drug.title': '⚠️ दवा परस्पर क्रिया जांच', 'sec.drug.subtitle': 'जांचें कि आपकी दवाएं एक साथ सुरक्षित हैं',
    'sec.drug.add_label': 'अपनी दवाएं जोड़ें', 'sec.drug.speak_btn': 'दवाओं के नाम बोलें', 'sec.drug.check_btn': 'परस्पर क्रिया जांचें',
    'sec.scanner.title': '📸 दवा स्कैनर', 'sec.scanner.subtitle': 'सेवन से पहले अपनी दवा की प्रामाणिकता जांचें',
    'sec.scanner.camera_btn': 'कैमरा खोलें', 'sec.scanner.upload_btn': 'छवि अपलोड करें',
    'sec.scanner.name_label': 'दवा का नाम (वैकल्पिक)', 'sec.scanner.name_placeholder': 'जैसे: Paracetamol 500mg', 'sec.scanner.scan_btn': 'स्कैन और सत्यापित करें',
    'sec.lifestyle.title': '🥗 जीवनशैली सलाहकार', 'sec.lifestyle.subtitle': 'व्यक्तिगत 7-दिन का आहार, व्यायाम और स्वास्थ्य योजना',
    'sec.lifestyle.btn': '✨ मेरी 7-दिन की योजना बनाएं',
    'sec.seasonal.title': '🌦️ मौसमी स्वास्थ्य जागरूकता', 'sec.seasonal.subtitle': 'आपके स्थान और मौसम के अनुसार स्वास्थ्य अलर्ट',
    'sec.seasonal.detect_title': 'आपका स्थान पहचान रहा है...', 'sec.seasonal.detect_desc': 'मौसमी स्वास्थ्य अलर्ट दिखाने के लिए हमें आपके स्थान की आवश्यकता है।',
    'sec.seasonal.allow_btn': 'स्थान की अनुमति दें',
    'sec.nearby.title': '📍 पास के स्वास्थ्य केंद्र खोजें', 'sec.nearby.subtitle': 'पास के अस्पताल, क्लीनिक और फार्मेसियां खोजें',
    'sec.nearby.detect_btn': 'मेरा स्थान पहचानें', 'sec.nearby.filter_all': 'सभी', 'sec.nearby.filter_hospital': '🏥 अस्पताल',
    'sec.nearby.filter_clinic': '🩺 क्लीनिक', 'sec.nearby.filter_pharmacy': '💊 फार्मेसियां',
    'sec.profile.title': '👤 उपयोगकर्ता स्वास्थ्य प्रोफाइल', 'sec.profile.subtitle': 'AI सहायता को व्यक्तिगत बनाने के लिए आपका स्थायी स्वास्थ्य कार्ड',
    'footer.copy': '© 2026 MediMitra', 'footer.disclaimer': 'केवल AI उपकरण — पेशेवर चिकित्सा सलाह का विकल्प नहीं।',
  },
  Odia: {
    'nav.diagnostic_suite': 'ରୋଗ ନିଦାନ', 'nav.dashboard': 'ଡ୍ୟାଶବୋର୍ଡ', 'nav.symptom': 'ଲକ୍ଷଣ ପରୀକ୍ଷା',
    'nav.prescription': 'ପ୍ରେସ୍କ୍ରିପ୍ସନ ପଠକ', 'nav.drug': 'ଔଷଧ ପ୍ରତିକ୍ରିୟା', 'nav.health_care': 'ସ୍ୱାସ୍ଥ୍ୟ ସେବା',
    'nav.scanner': 'ଔଷଧ ସ୍କ୍ୟାନର', 'nav.lifestyle': 'ଜୀବନଶୈଳୀ ସଲାହ', 'nav.seasonal': 'ଋତୁ ସଚେତନତା',
    'nav.nearby': 'ନିକଟ ଚିକିତ୍ସା', 'nav.personal_space': 'ବ୍ୟକ୍ତିଗତ', 'nav.profile': 'ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରୋଫାଇଲ',
    'nav.disclaimer': '⚕️ କେବଳ AI ଉପକରଣ। ଡାକ୍ତରଙ୍କ ସହ ପରାମର୍ଶ କରନ୍ତୁ।',
    'dash.badge': 'AI-ଚାଳିତ ସ୍ୱାସ୍ଥ୍ୟ ସାଥୀ', 'dash.title': 'ଆପଣଙ୍କ ସ୍ୱାସ୍ଥ୍ୟ,', 'dash.title_span': 'ଆମର ଅଗ୍ରାଧିକାର',
    'dash.subtitle': '7 AI ଉପକରଣ — ଲକ୍ଷଣ ଯାଞ୍ଚ, ଔଷଧ ସ୍କ୍ୟାନ ଏବଂ ଅଧିକ। ଆପଣଙ୍କ ଭାଷାରେ।',
    'dash.ai_features': 'AI ସୁବିଧା', 'dash.languages': 'ଭାଷା', 'dash.realtime': 'ତ୍ୱରିତ ଫଳାଫଳ',
    'dash.what_today': 'ଆଜି ମୁଁ ଆପଣଙ୍କୁ କେଉଁ ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି?', 'dash.click_feature': 'ଯେକୌଣସି ସୁବିଧାରେ କ୍ଲିକ କରନ୍ତୁ',
    'dash.disclaimer_title': 'ଚିକିତ୍ସା ଅସ୍ୱୀକୃତି:', 'dash.disclaimer_body': 'MediMitra କେବଳ AI ସ୍ୱାସ୍ଥ୍ୟ ସୂଚନା ପ୍ରଦାନ କରେ। ଏହା ଚିକିତ୍ସା ପରାମର୍ଶର ବିକଳ୍ପ ନୁହେଁ।',
    'feat.symptom.title': 'ଲକ୍ଷଣ ଯାଞ୍ଚ', 'feat.symptom.desc': 'ଆପଣଙ୍କ ଲକ୍ଷଣ ବର୍ଣ୍ଣନା କରନ୍ତୁ ଏବଂ AI ମାର୍ଗଦର୍ଶନ ପାଆନ୍ତୁ।',
    'feat.prescription.title': 'ପ୍ରେସ୍କ୍ରିପ୍ସନ ପଠକ', 'feat.prescription.desc': 'ଆପଣଙ୍କ ଭାଷାରେ ବ୍ୟାଖ୍ୟା ପାଆନ୍ତୁ।',
    'feat.drug.title': 'ଔଷଧ ପ୍ରତିକ୍ରିୟା', 'feat.drug.desc': 'ଔଷଧ ଏକାଠି ନେବା ନିରାପଦ କିନା ଯାଞ୍ଚ।',
    'feat.scanner.title': 'ଔଷଧ ସ୍କ୍ୟାନର', 'feat.scanner.desc': 'ପ୍ରାମାଣିକତା ଯାଞ୍ଚ।',
    'feat.lifestyle.title': 'ଜୀବନଶୈଳୀ ସଲାହ', 'feat.lifestyle.desc': '7-ଦିନ ଆହାର ଓ ବ୍ୟାୟାମ ଯୋଜନା।',
    'feat.seasonal.title': 'ଋତୁ ସଚେତନତା', 'feat.seasonal.desc': 'ଋତୁ ଅନୁଯାୟୀ ସ୍ୱାସ୍ଥ୍ୟ ଅଲର୍ଟ।',
    'feat.nearby.title': 'ନିକଟ ଚିକିତ୍ସା', 'feat.nearby.desc': 'ନିକଟ ଡାକ୍ତରଖାନା ଖୋଜନ୍ତୁ।',
    'feat.feedback.title': 'ଉପଭୋକ୍ତା ମତ', 'feat.open': 'ଖୋଲନ୍ତୁ →',
    'sec.symptom.title': '🤒 ଲକ୍ଷଣ ଯାଞ୍ଚ', 'sec.symptom.subtitle': 'ଲକ୍ଷଣ ବର୍ଣ୍ଣନା କରନ୍ତୁ ଏବଂ AI ମାର୍ଗଦର୍ଶନ ପାଆନ୍ତୁ',
    'sec.symptom.feeling_label': 'ଆପଣ କେମିତି ଅନୁଭବ କରୁଛନ୍ତି?', 'sec.symptom.placeholder': 'ଯଥା: 2 ଦିନ ଧରି ଜ୍ୱର...',
    'sec.symptom.common_label': 'ସାଧାରଣ ଲକ୍ଷଣ (କ୍ଲିକ ଯୋଗ)', 'sec.symptom.duration_label': 'ଏ ଲକ୍ଷଣ କେତେ ଦିନ?',
    'sec.symptom.dur_1': '1 ଦିନ ଠାରୁ କମ', 'sec.symptom.dur_2': '1–3 ଦିନ', 'sec.symptom.dur_3': '3–7 ଦିନ', 'sec.symptom.dur_4': '1 ସପ୍ତାହ ଠାରୁ ଅଧିକ',
    'sec.symptom.severity_label': 'ଗୁରୁତ୍ୱ (1–10)', 'sec.symptom.mild': 'ହାଲୁକା', 'sec.symptom.moderate': 'ମଧ୍ୟମ', 'sec.symptom.severe': 'ଗୁରୁତର',
    'sec.symptom.btn': 'ଲକ୍ଷଣ ବିଶ୍ଳେଷଣ', 'sec.symptom.ready_title': 'ବିଶ୍ଳେଷଣ ପ୍ରସ୍ତୁତ', 'sec.symptom.ready_desc': 'ଲକ୍ଷଣ ପୂରଣ କରି ବିଶ୍ଳେଷଣ ଉପରେ କ୍ଲିକ।',
    'sec.symptom.tab1': 'ଏହା କ\'ଣ', 'sec.symptom.tab2': 'କ\'ଣ କରିବେ', 'sec.symptom.tab3': 'ଡାକ୍ତର ଦରକାର ଯଦି...',
    'sec.symptom.find_clinic': 'ନିକଟ କ୍ଲିନିକ', 'sec.symptom.check_interactions': 'ପ୍ରତିକ୍ରିୟା ଯାଞ୍ଚ', 'common.download_pdf': 'PDF ଡାଉନଲୋଡ',
    'sec.rx.title': '📄 ପ୍ରେସ୍କ୍ରିପ୍ସନ ପଠକ', 'sec.rx.subtitle': 'ଆପଣଙ୍କ ଭାଷାରେ ବ୍ୟାଖ୍ୟା ପାଆନ୍ତୁ',
    'sec.rx.upload_title': 'ପ୍ରେସ୍କ୍ରିପ୍ସନ ଏଠାରେ ଟ୍ୟାଣ', 'sec.rx.upload_hint': 'ବ୍ରାଉଜ — JPG, PNG, PDF',
    'sec.rx.camera_btn': 'କ୍ୟାମେରାରେ ଫଟୋ', 'sec.rx.btn': 'ମୋ ପ୍ରେସ୍କ୍ରିପ୍ସନ ପଢ଼ନ୍ତୁ',
    'sec.drug.title': '⚠️ ଔଷଧ ପ୍ରତିକ୍ରିୟା ଯାଞ୍ଚ', 'sec.drug.subtitle': 'ଔଷଧ ଏକାଠି ସୁରକ୍ଷିତ?',
    'sec.drug.add_label': 'ଔଷଧ ଯୋଗ', 'sec.drug.speak_btn': 'ଔଷଧ ନାମ ବୋଲ', 'sec.drug.check_btn': 'ପ୍ରତିକ୍ରିୟା ଯାଞ୍ଚ',
    'sec.scanner.title': '📸 ଔଷଧ ସ୍କ୍ୟାନର', 'sec.scanner.subtitle': 'ସେବନ ପୂର୍ବରୁ ଯାଞ୍ଚ',
    'sec.scanner.camera_btn': 'କ୍ୟାମେରା ଖୋଲ', 'sec.scanner.upload_btn': 'ଚିତ୍ର ଅପଲୋଡ',
    'sec.scanner.name_label': 'ଔଷଧ ନାମ (ଐଚ୍ଛିକ)', 'sec.scanner.name_placeholder': 'ଯଥା: Paracetamol 500mg', 'sec.scanner.scan_btn': 'ସ୍କ୍ୟାନ ଏବଂ ଯାଞ୍ଚ',
    'sec.lifestyle.title': '🥗 ଜୀବନଶୈଳୀ ସଲାହ', 'sec.lifestyle.subtitle': '7-ଦିନ ଆହାର ଯୋଜନା',
    'sec.lifestyle.btn': '✨ ମୋ 7-ଦିନ ଯୋଜନା',
    'sec.seasonal.title': '🌦️ ଋତୁ ସ୍ୱାସ୍ଥ୍ୟ ସଚେତନତା', 'sec.seasonal.subtitle': 'ଋତୁ ଅନୁଯାୟୀ ସ୍ୱାସ୍ଥ୍ୟ ଅଲର୍ଟ',
    'sec.seasonal.detect_title': 'ସ୍ଥାନ ଚିହ୍ନିହୁଁଛି...', 'sec.seasonal.detect_desc': 'ମୌସୁମୀ ଅଲର୍ଟ ପ୍ରଦର୍ଶନ ପାଇଁ ସ୍ଥାନ ଦରକାର।',
    'sec.seasonal.allow_btn': 'ସ୍ଥାନ ଅନୁମୋଦନ',
    'sec.nearby.title': '📍 ନିକଟ ଚିକିତ୍ସା', 'sec.nearby.subtitle': 'ନିକଟ ଡାକ୍ତରଖାନା ଖୋଜ',
    'sec.nearby.detect_btn': 'ମୋ ସ୍ଥାନ', 'sec.nearby.filter_all': 'ସବୁ', 'sec.nearby.filter_hospital': '🏥 ଡାକ୍ତରଖାନା',
    'sec.nearby.filter_clinic': '🩺 କ୍ଲିନିକ', 'sec.nearby.filter_pharmacy': '💊 ଫାର୍ମାସି',
    'sec.profile.title': '👤 ଉପଭୋକ୍ତା ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରୋଫାଇଲ', 'sec.profile.subtitle': 'AI ସହାୟତା ବ୍ୟକ୍ତିଗତ ପ୍ରୋଫାଇଲ',
    'footer.copy': '© 2026 MediMitra', 'footer.disclaimer': 'କେବଳ AI — ଚିକିତ୍ସା ପରାମର୍ଶ ବିକଳ୍ପ ନୁହେଁ।',
  },
  Bengali: {
    'nav.diagnostic_suite': 'রোগ নির্ণয়', 'nav.dashboard': 'ড্যাশবোর্ড', 'nav.symptom': 'লক্ষণ পরীক্ষক',
    'nav.prescription': 'প্রেসক্রিপশন রিডার', 'nav.drug': 'ওষুধ প্রতিক্রিয়া', 'nav.health_care': 'স্বাস্থ্য সেবা',
    'nav.scanner': 'ওষুধ স্ক্যানার', 'nav.lifestyle': 'জীবনধারা পরামর্শ', 'nav.seasonal': 'মৌসুমী সচেতনতা',
    'nav.nearby': 'কাছের হাসপাতাল', 'nav.personal_space': 'ব্যক্তিগত', 'nav.profile': 'স্বাস্থ্য প্রোফাইল',
    'nav.disclaimer': '⚕️ শুধুমাত্র AI টুল। ডাক্তারের পরামর্শ নিন।',
    'dash.badge': 'AI-চালিত স্বাস্থ্য সহায়ক', 'dash.title': 'আপনার স্বাস্থ্য,', 'dash.title_span': 'আমাদের অগ্রাধিকার',
    'dash.subtitle': '7টি AI টুল — উপসর্গ পরীক্ষা, ওষুধ স্ক্যান ও আরও। আপনার ভাষায়।',
    'dash.ai_features': 'AI বৈশিষ্ট্য', 'dash.languages': 'ভাষা', 'dash.realtime': 'রিয়েল-টাইম ফলাফল',
    'dash.what_today': 'আজ আমি কীভাবে সাহায্য করতে পারি?', 'dash.click_feature': 'যেকোনো বৈশিষ্ট্যে ক্লিক করুন',
    'dash.disclaimer_title': 'চিকিৎসা দাবিত্যাগ:', 'dash.disclaimer_body': 'MediMitra শুধুমাত্র AI স্বাস্থ্য তথ্য প্রদান করে। পেশাদার পরামর্শের বিকল্প নয়।',
    'feat.symptom.title': 'লক্ষণ পরীক্ষক', 'feat.symptom.desc': 'লক্ষণ বর্ণনা করুন এবং AI নির্দেশনা পান।',
    'feat.prescription.title': 'প্রেসক্রিপশন রিডার', 'feat.prescription.desc': 'আপনার ভাষায় ব্যাখ্যা পান।',
    'feat.drug.title': 'ওষুধ প্রতিক্রিয়া', 'feat.drug.desc': 'ওষুধ একসাথে নেওয়া নিরাপদ কিনা।',
    'feat.scanner.title': 'ওষুধ স্ক্যানার', 'feat.scanner.desc': 'প্যাকেজিং স্ক্যান করে সত্যতা যাচাই।',
    'feat.lifestyle.title': 'জীবনধারা পরামর্শ', 'feat.lifestyle.desc': '7-দিনের খাদ্য ও ব্যায়াম পরিকল্পনা।',
    'feat.seasonal.title': 'মৌসুমী সচেতনতা', 'feat.seasonal.desc': 'মৌসুম অনুযায়ী স্বাস্থ্য সতর্কতা।',
    'feat.nearby.title': 'কাছের হাসপাতাল', 'feat.nearby.desc': 'কাছের হাসপাতাল ও ক্লিনিক খুঁজুন।',
    'feat.feedback.title': 'ব্যবহারকারীর মতামত', 'feat.open': 'খুলুন →',
    'sec.symptom.title': '🤒 লক্ষণ পরীক্ষক', 'sec.symptom.subtitle': 'লক্ষণ বর্ণনা করুন এবং AI নির্দেশনা পান',
    'sec.symptom.feeling_label': 'আপনি কেমন অনুভব করছেন?', 'sec.symptom.placeholder': 'যেমন: ২ দিন ধরে জ্বর...',
    'sec.symptom.common_label': 'সাধারণ লক্ষণ (যোগ করতে ক্লিক)', 'sec.symptom.duration_label': 'কতদিন ধরে?',
    'sec.symptom.dur_1': '১ দিনের কম', 'sec.symptom.dur_2': '১–৩ দিন', 'sec.symptom.dur_3': '৩–৭ দিন', 'sec.symptom.dur_4': '১ সপ্তাহের বেশি',
    'sec.symptom.severity_label': 'তীব্রতা (১–১০)', 'sec.symptom.mild': 'হালকা', 'sec.symptom.moderate': 'মাঝারি', 'sec.symptom.severe': 'গুরুতর',
    'sec.symptom.btn': 'লক্ষণ বিশ্লেষণ করুন', 'sec.symptom.ready_title': 'বিশ্লেষণের জন্য প্রস্তুত', 'sec.symptom.ready_desc': 'লক্ষণ পূরণ করুন ও বিশ্লেষণে ক্লিক করুন।',
    'sec.symptom.tab1': 'এটা কী', 'sec.symptom.tab2': 'কী করবেন', 'sec.symptom.tab3': 'ডাক্তার দেখান যদি...',
    'sec.symptom.find_clinic': 'কাছের ক্লিনিক', 'sec.symptom.check_interactions': 'প্রতিক্রিয়া পরীক্ষা', 'common.download_pdf': 'PDF ডাউনলোড',
    'sec.rx.title': '📄 প্রেসক্রিপশন রিডার', 'sec.rx.subtitle': 'আপনার ভাষায় ব্যাখ্যা পান',
    'sec.rx.upload_title': 'প্রেসক্রিপশন টেনে ফেলুন', 'sec.rx.upload_hint': 'বা ব্রাউজ — JPG, PNG, PDF',
    'sec.rx.camera_btn': 'ক্যামেরায় ছবি তুলুন', 'sec.rx.btn': 'প্রেসক্রিপশন পড়ুন',
    'sec.drug.title': '⚠️ ওষুধ প্রতিক্রিয়া পরীক্ষক', 'sec.drug.subtitle': 'একসাথে নেওয়া নিরাপদ?',
    'sec.drug.add_label': 'ওষুধ যোগ করুন', 'sec.drug.speak_btn': 'নাম বলুন', 'sec.drug.check_btn': 'পরীক্ষা করুন',
    'sec.scanner.title': '📸 ওষুধ স্ক্যানার', 'sec.scanner.subtitle': 'আসল কিনা যাচাই করুন',
    'sec.scanner.camera_btn': 'ক্যামেরা খুলুন', 'sec.scanner.upload_btn': 'ছবি আপলোড',
    'sec.scanner.name_label': 'ওষুধের নাম (ঐচ্ছিক)', 'sec.scanner.name_placeholder': 'যেমন: Paracetamol 500mg', 'sec.scanner.scan_btn': 'স্ক্যান ও যাচাই',
    'sec.lifestyle.title': '🥗 জীবনধারা পরামর্শ', 'sec.lifestyle.subtitle': '7-দিনের পরিকল্পনা',
    'sec.lifestyle.btn': '✨ আমার 7-দিনের পরিকল্পনা',
    'sec.seasonal.title': '🌦️ মৌসুমী স্বাস্থ্য সচেতনতা', 'sec.seasonal.subtitle': 'মৌসুম অনুযায়ী স্বাস্থ্য সতর্কতা',
    'sec.seasonal.detect_title': 'অবস্থান শনাক্ত হচ্ছে...', 'sec.seasonal.detect_desc': 'মৌসুমী সতর্কতা দেখাতে অবস্থান প্রয়োজন।',
    'sec.seasonal.allow_btn': 'অবস্থান অনুমতি',
    'sec.nearby.title': '📍 কাছের স্বাস্থ্য কেন্দ্র', 'sec.nearby.subtitle': 'হাসপাতাল ও ক্লিনিক খুঁজুন',
    'sec.nearby.detect_btn': 'অবস্থান শনাক্ত', 'sec.nearby.filter_all': 'সব', 'sec.nearby.filter_hospital': '🏥 হাসপাতাল',
    'sec.nearby.filter_clinic': '🩺 ক্লিনিক', 'sec.nearby.filter_pharmacy': '💊 ফার্মেসি',
    'sec.profile.title': '👤 স্বাস্থ্য প্রোফাইল', 'sec.profile.subtitle': 'AI সহায়তা ব্যক্তিগত করুন',
    'footer.copy': '© 2026 MediMitra', 'footer.disclaimer': 'শুধুমাত্র AI — চিকিৎসা পরামর্শের বিকল্প নয়।',
  },
  Tamil: {
    'nav.diagnostic_suite': 'நோய் கண்டறிதல்', 'nav.dashboard': 'டாஷ்போர்டு', 'nav.symptom': 'அறிகுறி சோதனை',
    'nav.prescription': 'மருந்துச் சீட்டு வாசகர்', 'nav.drug': 'மருந்து தொடர்பு', 'nav.health_care': 'சுகாதார சேவை',
    'nav.scanner': 'மருந்து ஸ்கேனர்', 'nav.lifestyle': 'வாழ்க்கை முறை ஆலோசகர்', 'nav.seasonal': 'பருவகால விழிப்புணர்வு',
    'nav.nearby': 'அருகிலுள்ள மருத்துவமனை', 'nav.personal_space': 'தனிப்பட்டது', 'nav.profile': 'சுகாதார சுயவிவரம்',
    'nav.disclaimer': '⚕️ AI கருவி மட்டுமே. மருத்துவரை அணுகவும்.',
    'dash.badge': 'AI-இயக்கப்படும் சுகாதார துணை', 'dash.title': 'உங்கள் ஆரோக்கியம்,', 'dash.title_span': 'எங்கள் முன்னுரிமை',
    'dash.subtitle': '7 AI கருவிகள் — அறிகுறி சோதனை, மருந்து ஸ்கேன். உங்கள் மொழியில்.',
    'dash.ai_features': 'AI அம்சங்கள்', 'dash.languages': 'மொழிகள்', 'dash.realtime': 'நேரடி முடிவுகள்',
    'dash.what_today': 'இன்று எப்படி உதவ முடியும்?', 'dash.click_feature': 'எந்த அம்சத்தையும் கிளிக் செய்யவும்',
    'dash.disclaimer_title': 'மருத்துவ மறுப்பு:', 'dash.disclaimer_body': 'MediMitra AI தகவல்களை மட்டுமே வழங்குகிறது. தொழில்முறை ஆலோசனையின் மாற்று அல்ல.',
    'feat.symptom.title': 'அறிகுறி சோதனை', 'feat.symptom.desc': 'அறிகுறிகளை விவரித்து AI வழிகாட்டுதல் பெறவும்.',
    'feat.prescription.title': 'மருந்துச் சீட்டு வாசகர்', 'feat.prescription.desc': 'உங்கள் மொழியில் விளக்கம் பெறவும்.',
    'feat.drug.title': 'மருந்து தொடர்பு', 'feat.drug.desc': 'ஒன்றாக எடுப்பது பாதுகாப்பானதா?',
    'feat.scanner.title': 'மருந்து ஸ்கேனர்', 'feat.scanner.desc': 'நம்பகத்தன்மை சரிபார்க்கவும்.',
    'feat.lifestyle.title': 'வாழ்க்கை முறை ஆலோசகர்', 'feat.lifestyle.desc': '7-நாள் உணவு திட்டம் பெறவும்.',
    'feat.seasonal.title': 'பருவகால விழிப்புணர்வு', 'feat.seasonal.desc': 'பருவ அடிப்படை ஆரோக்கிய எச்சரிக்கைகள்.',
    'feat.nearby.title': 'அருகிலுள்ள மருத்துவமனை', 'feat.nearby.desc': 'அருகிலுள்ளவற்றை கண்டுபிடிக்கவும்.',
    'feat.feedback.title': 'பயனர் கருத்து', 'feat.open': 'திற →',
    'sec.symptom.title': '🤒 அறிகுறி சோதனை', 'sec.symptom.subtitle': 'அறிகுறிகளை விவரித்து AI வழிகாட்டுதல் பெறவும்',
    'sec.symptom.feeling_label': 'நீங்கள் எப்படி உணர்கிறீர்கள்?', 'sec.symptom.placeholder': 'எ.கா: 2 நாட்களாக காய்ச்சல்...',
    'sec.symptom.common_label': 'பொதுவான அறிகுறிகள் (சேர்க்க கிளிக்)', 'sec.symptom.duration_label': 'எத்தனை நாட்கள்?',
    'sec.symptom.dur_1': '1 நாளுக்கும் குறைவு', 'sec.symptom.dur_2': '1–3 நாட்கள்', 'sec.symptom.dur_3': '3–7 நாட்கள்', 'sec.symptom.dur_4': '1 வாரத்திற்கும் அதிகம்',
    'sec.symptom.severity_label': 'தீவிரம் (1–10)', 'sec.symptom.mild': 'லேசானது', 'sec.symptom.moderate': 'நடுத்தரம்', 'sec.symptom.severe': 'கடுமையானது',
    'sec.symptom.btn': 'பகுப்பாய்வு செய்யவும்', 'sec.symptom.ready_title': 'பகுப்பாய்வுக்கு தயார்', 'sec.symptom.ready_desc': 'அறிகுறிகளை நிரப்பி பகுப்பாய்வு கிளிக்.',
    'sec.symptom.tab1': 'இது என்ன', 'sec.symptom.tab2': 'என்ன செய்வது', 'sec.symptom.tab3': 'மருத்துவரை பார்க்கவும்...',
    'sec.symptom.find_clinic': 'அருகிலுள்ள கிளினிக்', 'sec.symptom.check_interactions': 'தொடர்பை சரிபார்', 'common.download_pdf': 'PDF பதிவிறக்கம்',
    'sec.rx.title': '📄 மருந்துச் சீட்டு வாசகர்', 'sec.rx.subtitle': 'உங்கள் மொழியில் விளக்கம்',
    'sec.rx.upload_title': 'மருந்துச் சீட்டை இழுக்கவும்', 'sec.rx.upload_hint': 'அல்லது உலாவ கிளிக் — JPG, PNG, PDF',
    'sec.rx.camera_btn': 'கேமராவில் புகைப்படம்', 'sec.rx.btn': 'படிக்கவும்',
    'sec.drug.title': '⚠️ மருந்து தொடர்பு சோதனை', 'sec.drug.subtitle': 'ஒன்றாக எடுப்பது பாதுகாப்பானதா?',
    'sec.drug.add_label': 'மருந்துகளை சேர்க்கவும்', 'sec.drug.speak_btn': 'பெயர்களை சொல்லவும்', 'sec.drug.check_btn': 'சோதிக்கவும்',
    'sec.scanner.title': '📸 மருந்து ஸ்கேனர்', 'sec.scanner.subtitle': 'உண்மையானதா சரிபார்க்கவும்',
    'sec.scanner.camera_btn': 'கேமராவை திறக்கவும்', 'sec.scanner.upload_btn': 'படம் பதிவேற்றவும்',
    'sec.scanner.name_label': 'மருந்தின் பெயர் (விருப்பம்)', 'sec.scanner.name_placeholder': 'எ.கா: Paracetamol 500mg', 'sec.scanner.scan_btn': 'ஸ்கேன் செய்து சரிபார்க்கவும்',
    'sec.lifestyle.title': '🥗 வாழ்க்கை முறை ஆலோசகர்', 'sec.lifestyle.subtitle': '7-நாள் திட்டம்',
    'sec.lifestyle.btn': '✨ என் 7-நாள் திட்டம்',
    'sec.seasonal.title': '🌦️ பருவகால ஆரோக்கிய விழிப்புணர்வு', 'sec.seasonal.subtitle': 'பருவ அடிப்படை ஆரோக்கிய எச்சரிக்கைகள்',
    'sec.seasonal.detect_title': 'இருப்பிடம் கண்டறியப்படுகிறது...', 'sec.seasonal.detect_desc': 'பருவகால எச்சரிக்கைகளை காட்ட இருப்பிடம் தேவை.',
    'sec.seasonal.allow_btn': 'இருப்பிட அனுமதி',
    'sec.nearby.title': '📍 அருகிலுள்ள மருத்துவ மையங்கள்', 'sec.nearby.subtitle': 'மருத்துவமனைகள் கண்டுபிடிக்கவும்',
    'sec.nearby.detect_btn': 'இருப்பிடம் கண்டுபிடி', 'sec.nearby.filter_all': 'அனைத்தும்', 'sec.nearby.filter_hospital': '🏥 மருத்துவமனைகள்',
    'sec.nearby.filter_clinic': '🩺 கிளினிக்குகள்', 'sec.nearby.filter_pharmacy': '💊 மருந்தகங்கள்',
    'sec.profile.title': '👤 சுகாதார சுயவிவரம்', 'sec.profile.subtitle': 'AI உதவியை தனிப்பயனாக்க',
    'footer.copy': '© 2026 MediMitra', 'footer.disclaimer': 'AI கருவி மட்டுமே — மாற்று அல்ல.',
  },
  Telugu: {
    'nav.diagnostic_suite': 'రోగ నిర్ణయం', 'nav.dashboard': 'డ్యాష్‌బోర్డ్', 'nav.symptom': 'లక్షణ పరీక్షకుడు',
    'nav.prescription': 'వైద్య చీటీ పఠకుడు', 'nav.drug': 'మందు పరస్పర చర్య', 'nav.health_care': 'ఆరోగ్య సేవ',
    'nav.scanner': 'మందు స్కానర్', 'nav.lifestyle': 'జీవనశైలి సలహాదారు', 'nav.seasonal': 'కాలానుగుణ అవగాహన',
    'nav.nearby': 'సమీప ఆసుపత్రి', 'nav.personal_space': 'వ్యక్తిగతం', 'nav.profile': 'ఆరోగ్య ప్రొఫైల్',
    'nav.disclaimer': '⚕️ AI సాధనం మాత్రమే. డాక్టర్‌ని సంప్రదించండి.',
    'dash.badge': 'AI-ఆధారిత ఆరోగ్య సహాయకుడు', 'dash.title': 'మీ ఆరోగ్యం,', 'dash.title_span': 'మా ప్రాధాన్యత',
    'dash.subtitle': '7 AI సాధనాలు — లక్షణ తనిఖీ, మందు స్కాన్ మరియు మరిన్ని. మీ భాషలో.',
    'dash.ai_features': 'AI లక్షణాలు', 'dash.languages': 'భాషలు', 'dash.realtime': 'రియల్-టైమ్ ఫలితాలు',
    'dash.what_today': 'నేను ఈరోజు ఎలా సహాయపడగలను?', 'dash.click_feature': 'ఏదైనా లక్షణంపై క్లిక్ చేయండి',
    'dash.disclaimer_title': 'వైద్య నిరాకరణ:', 'dash.disclaimer_body': 'MediMitra AI సమాచారం మాత్రమే. నిపుణుల సలహాకు ప్రత్యామ్నాయం కాదు.',
    'feat.symptom.title': 'లక్షణ పరీక్షకుడు', 'feat.symptom.desc': 'లక్షణాలను వివరించి AI మార్గదర్శకత్వం పొందండి.',
    'feat.prescription.title': 'వైద్య చీటీ పఠకుడు', 'feat.prescription.desc': 'మీ భాషలో వివరణ పొందండి.',
    'feat.drug.title': 'మందు పరస్పర చర్య', 'feat.drug.desc': 'మందులు కలిసి సురక్షితమా?',
    'feat.scanner.title': 'మందు స్కానర్', 'feat.scanner.desc': 'ప్రామాణికతను ధృవీకరించండి.',
    'feat.lifestyle.title': 'జీవనశైలి సలహాదారు', 'feat.lifestyle.desc': '7-రోజుల వ్యాయామ ప్రణాళిక పొందండి.',
    'feat.seasonal.title': 'కాలానుగుణ అవగాహన', 'feat.seasonal.desc': 'కాలానికి అనుగుణంగా ఆరోగ్య హెచ్చరికలు.',
    'feat.nearby.title': 'సమీప ఆసుపత్రి', 'feat.nearby.desc': 'సమీప ఆసుపత్రులు కనుగొనండి.',
    'feat.feedback.title': 'వినియోగదారు అభిప్రాయం', 'feat.open': 'తెరవండి →',
    'sec.symptom.title': '🤒 లక్షణ పరీక్షకుడు', 'sec.symptom.subtitle': 'లక్షణాలను వివరించి AI మార్గదర్శకత్వం పొందండి',
    'sec.symptom.feeling_label': 'మీరు ఎలా అనుభవిస్తున్నారు?', 'sec.symptom.placeholder': 'ఉదా: 2 రోజులుగా జ్వరం...',
    'sec.symptom.common_label': 'సాధారణ లక్షణాలు (జోడించడానికి క్లిక్)', 'sec.symptom.duration_label': 'ఎన్ని రోజులు?',
    'sec.symptom.dur_1': '1 రోజు కంటే తక్కువ', 'sec.symptom.dur_2': '1–3 రోజులు', 'sec.symptom.dur_3': '3–7 రోజులు', 'sec.symptom.dur_4': '1 వారం కంటే ఎక్కువ',
    'sec.symptom.severity_label': 'తీవ్రత (1–10)', 'sec.symptom.mild': 'తేలికపాటి', 'sec.symptom.moderate': 'మధ్యమ', 'sec.symptom.severe': 'తీవ్రమైన',
    'sec.symptom.btn': 'లక్షణాలను విశ్లేషించండి', 'sec.symptom.ready_title': 'విశ్లేషణకు సిద్ధం', 'sec.symptom.ready_desc': 'లక్షణాలు నమోదు చేసి విశ్లేషణపై క్లిక్.',
    'sec.symptom.tab1': 'ఇది ఏమిటి', 'sec.symptom.tab2': 'ఏమి చేయాలి', 'sec.symptom.tab3': 'డాక్టర్‌ని చూడండి...',
    'sec.symptom.find_clinic': 'సమీప క్లినిక్', 'sec.symptom.check_interactions': 'పరస్పర చర్య తనిఖీ', 'common.download_pdf': 'PDF డౌన్‌లోడ్',
    'sec.rx.title': '📄 వైద్య చీటీ పఠకుడు', 'sec.rx.subtitle': 'మీ భాషలో వివరణ పొందండి',
    'sec.rx.upload_title': 'వైద్య చీటీని లాగి వదలండి', 'sec.rx.upload_hint': 'లేదా బ్రౌజ్ — JPG, PNG, PDF',
    'sec.rx.camera_btn': 'కెమెరాతో ఫోటో', 'sec.rx.btn': 'చదవండి',
    'sec.drug.title': '⚠️ మందు పరస్పర చర్య తనిఖీ', 'sec.drug.subtitle': 'కలిసి తీసుకోవడం సురక్షితమా?',
    'sec.drug.add_label': 'మందులు జోడించండి', 'sec.drug.speak_btn': 'పేర్లు చెప్పండి', 'sec.drug.check_btn': 'తనిఖీ',
    'sec.scanner.title': '📸 మందు స్కానర్', 'sec.scanner.subtitle': 'నిజమైనదా ధృవీకరించండి',
    'sec.scanner.camera_btn': 'కెమెరా తెరవండి', 'sec.scanner.upload_btn': 'చిత్రం అప్‌లోడ్',
    'sec.scanner.name_label': 'మందు పేరు (ఐచ్ఛికం)', 'sec.scanner.name_placeholder': 'ఉదా: Paracetamol 500mg', 'sec.scanner.scan_btn': 'స్కాన్ ధృవీకరించండి',
    'sec.lifestyle.title': '🥗 జీవనశైలి సలహాదారు', 'sec.lifestyle.subtitle': '7-రోజుల ప్రణాళిక',
    'sec.lifestyle.btn': '✨ నా 7-రోజుల ప్రణాళిక',
    'sec.seasonal.title': '🌦️ కాలానుగుణ ఆరోగ్య అవగాహన', 'sec.seasonal.subtitle': 'కాలానికి అనుగుణంగా ఆరోగ్య హెచ్చరికలు',
    'sec.seasonal.detect_title': 'స్థానాన్ని గుర్తిస్తోంది...', 'sec.seasonal.detect_desc': 'కాలానుగుణ హెచ్చరికలకు స్థానం అవసరం.',
    'sec.seasonal.allow_btn': 'స్థాన అనుమతి',
    'sec.nearby.title': '📍 సమీప ఆరోగ్య కేంద్రాలు', 'sec.nearby.subtitle': 'ఆసుపత్రులు, క్లినిక్‌లు కనుగొనండి',
    'sec.nearby.detect_btn': 'స్థానాన్ని గుర్తించండి', 'sec.nearby.filter_all': 'అన్నీ', 'sec.nearby.filter_hospital': '🏥 ఆసుపత్రులు',
    'sec.nearby.filter_clinic': '🩺 క్లినిక్‌లు', 'sec.nearby.filter_pharmacy': '💊 ఫార్మసీలు',
    'sec.profile.title': '👤 వినియోగదారు ఆరోగ్య ప్రొఫైల్', 'sec.profile.subtitle': 'AI సహాయాన్ని వ్యక్తిగతీకరించండి',
    'footer.copy': '© 2026 MediMitra', 'footer.disclaimer': 'AI సాధనం మాత్రమే — ప్రత్యామ్నాయం కాదు.',
  },
  Marathi: {
    'nav.diagnostic_suite': 'निदान सुविधा', 'nav.dashboard': 'डॅशबोर्ड', 'nav.symptom': 'लक्षण तपासणी',
    'nav.prescription': 'प्रिस्क्रिप्शन वाचक', 'nav.drug': 'औषध परस्परक्रिया', 'nav.health_care': 'आरोग्य सेवा',
    'nav.scanner': 'औषध स्कॅनर', 'nav.lifestyle': 'जीवनशैली सल्लागार', 'nav.seasonal': 'हंगामी जागरूकता',
    'nav.nearby': 'जवळचे रुग्णालय', 'nav.personal_space': 'वैयक्तिक', 'nav.profile': 'आरोग्य प्रोफाइल',
    'nav.disclaimer': '⚕️ फक्त AI साधन. डॉक्टरांचा सल्ला घ्या.',
    'dash.badge': 'AI-चालित आरोग्य सहाय्यक', 'dash.title': 'आपले आरोग्य,', 'dash.title_span': 'आमची प्राथमिकता',
    'dash.subtitle': '7 AI साधने — लक्षण तपासणी, औषध स्कॅन आणि बरेच काही. आपल्या भाषेत.',
    'dash.ai_features': 'AI वैशिष्ट्ये', 'dash.languages': 'भाषा', 'dash.realtime': 'रिअल-टाइम निकाल',
    'dash.what_today': 'आज मी कशी मदत करू?', 'dash.click_feature': 'कोणत्याही वैशिष्ट्यावर क्लिक करा',
    'dash.disclaimer_title': 'वैद्यकीय अस्वीकरण:', 'dash.disclaimer_body': 'MediMitra फक्त AI माहिती प्रदान करते. व्यावसायिक सल्ल्याचा पर्याय नाही.',
    'feat.symptom.title': 'लक्षण तपासणी', 'feat.symptom.desc': 'लक्षणे सांगा आणि AI मार्गदर्शन मिळवा.',
    'feat.prescription.title': 'प्रिस्क्रिप्शन वाचक', 'feat.prescription.desc': 'आपल्या भाषेत स्पष्टीकरण मिळवा.',
    'feat.drug.title': 'औषध परस्परक्रिया', 'feat.drug.desc': 'एकत्र घेणे सुरक्षित आहे का?',
    'feat.scanner.title': 'औषध स्कॅनर', 'feat.scanner.desc': 'पॅकेजिंग स्कॅन करून सत्यता तपासा.',
    'feat.lifestyle.title': 'जीवनशैली सल्लागार', 'feat.lifestyle.desc': '7-दिवसांची योजना मिळवा.',
    'feat.seasonal.title': 'हंगामी जागरूकता', 'feat.seasonal.desc': 'हंगामानुसार इशारे दाखवते.',
    'feat.nearby.title': 'जवळचे रुग्णालय', 'feat.nearby.desc': 'जवळचे दवाखाने शोधा.',
    'feat.feedback.title': 'वापरकर्ता अभिप्राय', 'feat.open': 'उघडा →',
    'sec.symptom.title': '🤒 लक्षण तपासणी', 'sec.symptom.subtitle': 'लक्षणे सांगा आणि AI मार्गदर्शन मिळवा',
    'sec.symptom.feeling_label': 'आपल्याला कसे वाटत आहे?', 'sec.symptom.placeholder': 'उदा: 2 दिवसांपासून ताप...',
    'sec.symptom.common_label': 'सामान्य लक्षणे (जोडण्यासाठी क्लिक)', 'sec.symptom.duration_label': 'किती दिवसांपासून?',
    'sec.symptom.dur_1': '1 दिवसापेक्षा कमी', 'sec.symptom.dur_2': '1–3 दिवस', 'sec.symptom.dur_3': '3–7 दिवस', 'sec.symptom.dur_4': '1 आठवड्यापेक्षा जास्त',
    'sec.symptom.severity_label': 'तीव्रता (1–10)', 'sec.symptom.mild': 'सौम्य', 'sec.symptom.moderate': 'मध्यम', 'sec.symptom.severe': 'गंभीर',
    'sec.symptom.btn': 'लक्षणे विश्लेषण करा', 'sec.symptom.ready_title': 'विश्लेषणासाठी तयार', 'sec.symptom.ready_desc': 'लक्षणे भरा आणि विश्लेषण क्लिक करा.',
    'sec.symptom.tab1': 'हे काय आहे', 'sec.symptom.tab2': 'काय करावे', 'sec.symptom.tab3': 'डॉक्टरांना भेटा जर...',
    'sec.symptom.find_clinic': 'जवळचा दवाखाना', 'sec.symptom.check_interactions': 'परस्परक्रिया तपासा', 'common.download_pdf': 'PDF डाउनलोड',
    'sec.rx.title': '📄 प्रिस्क्रिप्शन वाचक', 'sec.rx.subtitle': 'आपल्या भाषेत स्पष्टीकरण',
    'sec.rx.upload_title': 'प्रिस्क्रिप्शन येथे ड्रॅग करा', 'sec.rx.upload_hint': 'किंवा ब्राउज — JPG, PNG, PDF',
    'sec.rx.camera_btn': 'कॅमेऱ्याने फोटो', 'sec.rx.btn': 'माझे प्रिस्क्रिप्शन वाचा',
    'sec.drug.title': '⚠️ औषध परस्परक्रिया तपासणी', 'sec.drug.subtitle': 'एकत्र घेणे सुरक्षित आहे का?',
    'sec.drug.add_label': 'औषधे जोडा', 'sec.drug.speak_btn': 'नावे सांगा', 'sec.drug.check_btn': 'परस्परक्रिया तपासा',
    'sec.scanner.title': '📸 औषध स्कॅनर', 'sec.scanner.subtitle': 'खरे आहे का तपासा',
    'sec.scanner.camera_btn': 'कॅमेरा उघडा', 'sec.scanner.upload_btn': 'प्रतिमा अपलोड',
    'sec.scanner.name_label': 'औषधाचे नाव (पर्यायी)', 'sec.scanner.name_placeholder': 'उदा: Paracetamol 500mg', 'sec.scanner.scan_btn': 'स्कॅन करा',
    'sec.lifestyle.title': '🥗 जीवनशैली सल्लागार', 'sec.lifestyle.subtitle': '7-दिवसांची योजना',
    'sec.lifestyle.btn': '✨ माझी 7-दिवसांची योजना',
    'sec.seasonal.title': '🌦️ हंगामी आरोग्य जागरूकता', 'sec.seasonal.subtitle': 'हंगामानुसार इशारे',
    'sec.seasonal.detect_title': 'स्थान ओळखत आहे...', 'sec.seasonal.detect_desc': 'हंगामी इशारे दाखवण्यासाठी स्थान आवश्यक.',
    'sec.seasonal.allow_btn': 'स्थान परवानगी',
    'sec.nearby.title': '📍 जवळचे आरोग्य केंद्र', 'sec.nearby.subtitle': 'जवळचे दवाखाने शोधा',
    'sec.nearby.detect_btn': 'माझे स्थान शोधा', 'sec.nearby.filter_all': 'सर्व', 'sec.nearby.filter_hospital': '🏥 रुग्णालये',
    'sec.nearby.filter_clinic': '🩺 दवाखाने', 'sec.nearby.filter_pharmacy': '💊 फार्मसी',
    'sec.profile.title': '👤 वापरकर्ता आरोग्य प्रोफाइल', 'sec.profile.subtitle': 'AI सहाय्य वैयक्तिकृत करा',
    'footer.copy': '© 2026 MediMitra', 'footer.disclaimer': 'फक्त AI साधन — पर्याय नाही.',
  }
};

// English defaults — used to RESET when user switches back to English
const UI_DEFAULTS = {
  'nav.diagnostic_suite': 'Diagnostic Suite', 'nav.dashboard': 'Dashboard', 'nav.symptom': 'Symptom Checker',
  'nav.prescription': 'Prescription Reader', 'nav.drug': 'Drug Interaction', 'nav.health_care': 'Health Care',
  'nav.scanner': 'Medicine Scanner', 'nav.lifestyle': 'Lifestyle Advisor', 'nav.seasonal': 'Seasonal Awareness',
  'nav.nearby': 'Nearby Healthcare', 'nav.personal_space': 'Personal Space', 'nav.profile': 'Health Profile',
  'nav.disclaimer': '⚕️ AI tool only. Always consult a licensed doctor before taking any medical action.',
  'dash.badge': 'AI-POWERED HEALTH COMPANION', 'dash.title': 'Your Health,', 'dash.title_span': 'Our Priority',
  'dash.subtitle': '7 AI-powered tools for smarter health decisions — symptom checking, medicine scanning, drug interactions, and more. In your language.',
  'dash.ai_features': 'AI Features', 'dash.languages': 'Languages', 'dash.realtime': 'Real-time Results',
  'dash.what_today': 'What can I help you with today?', 'dash.click_feature': 'Click any feature to get started instantly',
  'dash.disclaimer_title': 'Medical Disclaimer:', 'dash.disclaimer_body': 'MediMitra provides AI-generated health information only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed doctor for medical decisions.',
  'feat.symptom.title': 'Symptom Checker', 'feat.symptom.desc': 'Describe your symptoms and get AI-powered health guidance instantly.',
  'feat.prescription.title': 'Prescription Reader', 'feat.prescription.desc': 'Upload prescription photo and get plain language explanation in your language.',
  'feat.drug.title': 'Drug Interaction', 'feat.drug.desc': 'Check if your medicines are safe to take together. Avoid dangerous combinations.',
  'feat.scanner.title': 'Medicine Scanner', 'feat.scanner.desc': 'Scan medicine packaging to verify authenticity and check OpenFDA database.',
  'feat.lifestyle.title': 'Lifestyle Advisor', 'feat.lifestyle.desc': 'Get a personalized 7-day diet, exercise, and wellness plan tailored to you.',
  'feat.seasonal.title': 'Seasonal Awareness', 'feat.seasonal.desc': 'Auto-detects your location and season to show relevant health alerts.',
  'feat.nearby.title': 'Nearby Healthcare', 'feat.nearby.desc': 'Find hospitals, clinics, and pharmacies near you on an interactive map.',
  'feat.feedback.title': 'User Feedback', 'feat.open': 'Open →',
  'sec.symptom.title': '🤒 Symptom Checker', 'sec.symptom.subtitle': 'Describe your symptoms and get AI-powered health guidance',
  'sec.symptom.feeling_label': 'How are you feeling?', 'sec.symptom.placeholder': 'e.g. I have fever since 2 days, headache, body pain...',
  'sec.symptom.common_label': 'Common Symptoms (click to add)', 'sec.symptom.duration_label': 'How long have you had these symptoms?',
  'sec.symptom.dur_1': 'Less than 1 day', 'sec.symptom.dur_2': '1–3 days', 'sec.symptom.dur_3': '3–7 days', 'sec.symptom.dur_4': 'More than a week',
  'sec.symptom.severity_label': 'Severity (1–10)', 'sec.symptom.mild': 'Mild', 'sec.symptom.moderate': 'Moderate', 'sec.symptom.severe': 'Severe',
  'sec.symptom.btn': 'Analyze Symptoms', 'sec.symptom.ready_title': 'Ready to Analyze',
  'sec.symptom.ready_desc': 'Fill in your symptoms on the left and click Analyze. Our AI will identify possible conditions and give you guidance.',
  'sec.symptom.tab1': 'What It Is', 'sec.symptom.tab2': 'What To Do', 'sec.symptom.tab3': 'See A Doctor If...',
  'sec.symptom.find_clinic': 'Find Nearby Clinic', 'sec.symptom.check_interactions': 'Check Interactions', 'common.download_pdf': 'Download PDF',
  'sec.rx.title': '📄 Prescription Reader', 'sec.rx.subtitle': 'Upload your prescription and get a clear explanation in your language',
  'sec.rx.upload_title': 'Drag & drop your prescription', 'sec.rx.upload_hint': 'or click to browse — JPG, PNG, PDF',
  'sec.rx.camera_btn': 'Take Photo with Camera', 'sec.rx.btn': 'Read My Prescription',
  'sec.drug.title': '⚠️ Drug Interaction Checker', 'sec.drug.subtitle': 'Check if your medicines are safe to take together',
  'sec.drug.add_label': 'Add Your Medicines', 'sec.drug.speak_btn': 'Speak Medicine Names', 'sec.drug.check_btn': 'Check Interactions',
  'sec.scanner.title': '📸 Medicine Scanner', 'sec.scanner.subtitle': 'Verify if your medicine is genuine before consuming it',
  'sec.scanner.camera_btn': 'Open Camera', 'sec.scanner.upload_btn': 'Upload Image',
  'sec.scanner.name_label': 'Medicine Name (optional — improves accuracy)', 'sec.scanner.name_placeholder': 'e.g. Paracetamol 500mg', 'sec.scanner.scan_btn': 'Scan & Verify Medicine',
  'sec.lifestyle.title': '🥗 Lifestyle Advisor', 'sec.lifestyle.subtitle': 'Get a personalized 7-day diet, exercise & wellness plan',
  'sec.lifestyle.btn': '✨ Generate My 7-Day Plan',
  'sec.seasonal.title': '🌦️ Seasonal Health Awareness', 'sec.seasonal.subtitle': 'Health alerts based on your location and current season',
  'sec.seasonal.detect_title': 'Detecting Your Location...', 'sec.seasonal.detect_desc': 'We need your location to show relevant seasonal health alerts.',
  'sec.seasonal.allow_btn': 'Allow Location Access',
  'sec.nearby.title': '📍 Nearby Healthcare Finder', 'sec.nearby.subtitle': 'Find hospitals, clinics & pharmacies near you',
  'sec.nearby.detect_btn': 'Detect My Location', 'sec.nearby.filter_all': 'All', 'sec.nearby.filter_hospital': '🏥 Hospitals',
  'sec.nearby.filter_clinic': '🩺 Clinics', 'sec.nearby.filter_pharmacy': '💊 Pharmacies',
  'sec.profile.title': '👤 User Health Profile', 'sec.profile.subtitle': 'Your permanent health card to personalize AI assistance',
  'footer.copy': '© 2026 MediMitra', 'footer.disclaimer': 'AI tool only — not a substitute for professional medical advice.',
};

/** Apply UI translations — walks all [data-i18n] and [data-i18n-placeholder] elements */
function applyUITranslations(lang) {
  const dict = lang === 'English' ? UI_DEFAULTS : (UI_TRANSLATIONS[lang] || {});
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const val = dict[el.getAttribute('data-i18n')];
    if (val !== undefined) el.textContent = val;
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const val = dict[el.getAttribute('data-i18n-placeholder')];
    if (val !== undefined) el.placeholder = val;
  });
}

function setGlobalLanguage(lang) {
  globalLanguage = lang;
  localStorage.setItem('medimitra_language', lang);

  // Sync prescription language dropdown
  const rxLang = document.getElementById('rx-language');
  if (rxLang) rxLang.value = lang;

  // Apply UI translations to all tagged elements
  applyUITranslations(lang);

  // Show language indicator toast
  const langName = LANG_NAMES[lang] || lang;
  showToast(`🌐 Language set to ${langName} — AI responses will now be in ${langName}`, 'info');

  // Update language badge on affected sections
  updateLanguageBadges(lang);
}

function updateLanguageBadges(lang) {
  const langName = LANG_NAMES[lang] || lang;
  const affectedSections = ['symptom', 'prescription', 'lifestyle', 'seasonal'];

  affectedSections.forEach(section => {
    // Remove existing badge if any
    const existing = document.getElementById(`lang-badge-${section}`);
    if (existing) existing.remove();

    if (lang === 'English') return; // No badge needed for English

    // Find section header subtitle
    const subtitle = document.querySelector(`#section-${section} .section-subtitle`);
    if (subtitle) {
      const badge = document.createElement('span');
      badge.id = `lang-badge-${section}`;
      badge.style.cssText = `
        display:inline-flex;align-items:center;gap:4px;
        background:rgba(26,122,74,0.15);border:1px solid rgba(26,122,74,0.3);
        color:#4ade80;font-size:11px;font-weight:700;
        padding:2px 10px;border-radius:20px;margin-left:10px;
      `;
      badge.innerHTML = `🌐 ${langName}`;
      subtitle.appendChild(badge);
    }
  });
}

function getActiveLanguage() {
  return globalLanguage;
}

function dismissSplash() {
  const splash = document.getElementById('splash-screen');
  if (splash) splash.classList.add('hidden');
  // Re-trigger dashboard animations if needed
  showToast('Welcome back to MediMitra!', 'success');
}

// Apply saved language on page load
function initLanguage() {
  const saved = localStorage.getItem('medimitra_language') || 'English';
  globalLanguage = saved;
  const selector = document.getElementById('global-language');
  if (selector) selector.value = saved;
  const rxLang = document.getElementById('rx-language');
  if (rxLang) rxLang.value = saved;
  applyUITranslations(saved);
  if (saved !== 'English') updateLanguageBadges(saved);
}

// ══════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════
function initApp() {
  const hash = location.hash.replace('#', '') || 'landing';
  showSection(hash);
  initLanguage();
  initGoogleSignIn();

  // Enforce 4-column grid on desktop to avoid gaps
  const grid = document.getElementById('grid-features');
  if (grid) {
    const resizeGrid = () => {
      if (window.innerWidth > 1024) {
        grid.style.gridTemplateColumns = 'repeat(4, 1fr)';
      } else {
        grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(220px, 1fr))';
      }
    };
    window.addEventListener('resize', resizeGrid);
    resizeGrid();
  }

  // Auto-detect season on seasonal section click
  const seasonalBtn = document.querySelector('[data-section="seasonal"]');
  if (seasonalBtn) {
    seasonalBtn.addEventListener('click', () => {
      setTimeout(() => {
        const content = document.getElementById('seasonal-content');
        if (content && content.querySelector('.card')) detectSeason();
      }, 100);
    });
  }

  // Scroll-reveal for landing page sections (.lp-reveal)
  const revealObs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); revealObs.unobserve(e.target); }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.lp-reveal').forEach(el => revealObs.observe(el));
}
// Also keep DOMContentLoaded listener as fallback
document.addEventListener('DOMContentLoaded', initApp);


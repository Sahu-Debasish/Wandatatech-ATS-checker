/* ═══════════════════════════════════════════════════════════
   WANDATA ATS Checker — Frontend Logic
═══════════════════════════════════════════════════════════ */

const API = 'http://localhost:5000';
let files = { general: null, job: null };
let currentMode = 'general';
let loadingTimer = null;

// ── Particle Canvas ──────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById('particleCanvas');
  const ctx    = canvas.getContext('2d');
  let particles = [];

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function createParticle() {
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.4 + 0.05,
      color: Math.random() > 0.6 ? '#c8a96e' : '#1b3a6b'
    };
  }

  for (let i = 0; i < 80; i++) particles.push(createParticle());

  function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = p.color + Math.round(p.opacity * 255).toString(16).padStart(2, '0');
      ctx.fill();
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    });

    // Draw lines between close particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(200,169,110,${0.06 * (1 - d / 120)})`;
          ctx.lineWidth   = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(drawParticles);
  }
  drawParticles();
})();

// ── Mode Switching ───────────────────────────────────────────
function switchMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.mode-tab').forEach(t => t.classList.toggle('active', t.dataset.mode === mode));
  document.getElementById('generalMode').classList.toggle('active', mode === 'general');
  document.getElementById('jobMode').classList.toggle('active', mode === 'job');
  hideResults();
}

// ── File Handling ────────────────────────────────────────────
function handleFileSelect(e, mode) {
  const file = e.target.files[0];
  if (file) setFile(file, mode);
}

function handleDrop(e, mode) {
  e.preventDefault();
  const zone = e.currentTarget;
  zone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file, mode);
}

function handleDragOver(e) {
  e.preventDefault();
  e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
  e.currentTarget.classList.remove('drag-over');
}

function setFile(file, mode) {
  const allowed = ['pdf', 'doc', 'docx', 'txt'];
  const ext     = file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast('❌ Invalid file type. Please upload PDF, DOCX, or TXT', 'error');
    return;
  }

  files[mode] = file;
  const infoEl = document.getElementById(`fileInfo${mode === 'general' ? 'General' : 'Job'}`);
  const zoneEl = document.getElementById(`uploadZone${mode === 'general' ? 'General' : 'Job'}`);
  const btnEl  = document.getElementById(`analyzeBtn${mode === 'general' ? 'General' : 'Job'}`);

  infoEl.style.display = 'flex';
  infoEl.innerHTML     = `✅ ${file.name} <span style="color:var(--text-dim)">(${formatBytes(file.size)})</span>`;
  zoneEl.classList.add('has-file');
  btnEl.disabled = false;

  // For job mode, check if title and desc also filled
  if (mode === 'job') updateJobBtnState();
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// ── Job Mode Inputs ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const titleInput = document.getElementById('jobTitleInput');
  const descInput  = document.getElementById('jobDescInput');
  const counter    = document.getElementById('charCounter');

  if (titleInput) titleInput.addEventListener('input', updateJobBtnState);
  if (descInput) {
    descInput.addEventListener('input', () => {
      counter.textContent = descInput.value.length + ' characters';
      updateJobBtnState();
    });
  }
});

function updateJobBtnState() {
  const title = document.getElementById('jobTitleInput').value.trim();
  const desc  = document.getElementById('jobDescInput').value.trim();
  const hasFile = !!files.job;
  document.getElementById('analyzeBtnJob').disabled = !(title && desc.length >= 50 && hasFile);
}

// ── Loading ──────────────────────────────────────────────────
function showLoading() {
  document.getElementById('loadingOverlay').style.display = 'flex';
  document.getElementById('resultsContainer').style.display = 'none';

  const steps = ['step1', 'step2', 'step3', 'step4'];
  let i = 0;
  steps.forEach(id => {
    document.getElementById(id).className = 'l-step';
  });
  document.getElementById('step1').className = 'l-step active';

  loadingTimer = setInterval(() => {
    if (i < steps.length - 1) {
      document.getElementById(steps[i]).className = 'l-step done';
      i++;
      document.getElementById(steps[i]).className = 'l-step active';
    }
  }, 900);
}

function hideLoading() {
  clearInterval(loadingTimer);
  document.getElementById('loadingOverlay').style.display = 'none';
}

function hideResults() {
  document.getElementById('resultsContainer').style.display = 'none';
}

// ── Toast ────────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:9999;
    background:${type === 'error' ? 'rgba(248,113,113,0.15)' : 'rgba(200,169,110,0.15)'};
    border:1px solid ${type === 'error' ? 'rgba(248,113,113,0.4)' : 'rgba(200,169,110,0.4)'};
    color:${type === 'error' ? '#f87171' : '#e8c87a'};
    padding:14px 20px; border-radius:10px; font-family:'Rajdhani',sans-serif;
    font-size:15px; font-weight:600; letter-spacing:0.5px;
    backdrop-filter:blur(10px); animation:slideUp 0.3s ease;
    max-width:360px; line-height:1.5;
  `;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.4s'; setTimeout(() => t.remove(), 400); }, 4000);
}

// ── Analyze General ──────────────────────────────────────────
async function analyzeGeneral() {
  if (!files.general) { showToast('❌ Please upload a resume first', 'error'); return; }

  const formData = new FormData();
  formData.append('resume', files.general);

  showLoading();
  document.getElementById('resultsContainer').style.display = 'none';

  try {
    const resp = await fetch(`${API}/analyze/general`, { method: 'POST', body: formData });
    const data = await resp.json();
    hideLoading();
    if (data.success) {
      renderGeneralResults(data.result);
    } else {
      showToast('❌ ' + (data.error || 'Analysis failed'), 'error');
    }
  } catch (err) {
    hideLoading();
    showToast('❌ Cannot connect to server. Make sure app.py is running.', 'error');
  }
}

// ── Analyze Job ──────────────────────────────────────────────
async function analyzeJob() {
  if (!files.job) { showToast('❌ Please upload a resume first', 'error'); return; }

  const title = document.getElementById('jobTitleInput').value.trim();
  const desc  = document.getElementById('jobDescInput').value.trim();

  if (!title || desc.length < 50) {
    showToast('❌ Please fill in job title and full description', 'error'); return;
  }

  const formData = new FormData();
  formData.append('resume', files.job);
  formData.append('job_title', title);
  formData.append('job_description', desc);

  showLoading();
  document.getElementById('resultsContainer').style.display = 'none';

  try {
    const resp = await fetch(`${API}/analyze/job`, { method: 'POST', body: formData });
    const data = await resp.json();
    hideLoading();
    if (data.success) {
      renderJobResults(data.result);
    } else {
      showToast('❌ ' + (data.error || 'Analysis failed'), 'error');
    }
  } catch (err) {
    hideLoading();
    showToast('❌ Cannot connect to server. Make sure app.py is running.', 'error');
  }
}

// ── Render General Results ───────────────────────────────────
function renderGeneralResults(r) {
  const container = document.getElementById('resultsContainer');
  container.style.display = 'block';
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Score
  animateScore(r.score);
  document.getElementById('resultGrade').textContent   = r.grade;
  document.getElementById('resultVerdict').textContent = r.verdict;
  document.getElementById('resultFilename').textContent = `📄 ${r.filename} · ${r.word_count} words`;

  // Badges
  const badges = [];
  if (r.sections_found?.length)
    badges.push({ text: `${r.sections_found.length} Sections`, cls: 'badge-blue' });
  if (r.tech_skills?.length)
    badges.push({ text: `${r.tech_skills.length} Tech Skills`, cls: 'badge-gold' });
  if (r.action_verbs_found?.length)
    badges.push({ text: `${r.action_verbs_found.length} Action Verbs`, cls: 'badge-green' });
  renderBadges(badges);

  // Components
  renderComponents(r.components);

  // Tab: Skills
  let skillsHTML = '';
  if (r.tech_skills?.length) {
    skillsHTML += `<div class="tag-section"><div class="tag-section-title">TECHNICAL SKILLS DETECTED</div><div class="tags">${r.tech_skills.map(s => `<span class="tag tag-tech">${s}</span>`).join('')}</div></div>`;
  }
  if (r.soft_skills?.length) {
    skillsHTML += `<div class="tag-section"><div class="tag-section-title">SOFT SKILLS</div><div class="tags">${r.soft_skills.map(s => `<span class="tag tag-soft">${s}</span>`).join('')}</div></div>`;
  }
  if (r.action_verbs_found?.length) {
    skillsHTML += `<div class="tag-section"><div class="tag-section-title">ACTION VERBS</div><div class="tags">${r.action_verbs_found.map(v => `<span class="tag tag-verb">${v}</span>`).join('')}</div></div>`;
  }
  if (r.sections_found?.length) {
    skillsHTML += `<div class="tag-section"><div class="tag-section-title">DETECTED SECTIONS</div><div class="tags">${r.sections_found.map(s => `<span class="tag tag-section">${s}</span>`).join('')}</div></div>`;
  }
  document.getElementById('tabSkills').innerHTML = skillsHTML || '<p style="color:var(--text-dim);padding:20px">No skills data extracted.</p>';

  // Tab: Keywords
  document.getElementById('tabKeywords').innerHTML = `
    <div class="tag-section">
      <div class="tag-section-title">KEYWORDS FOUND IN RESUME</div>
      <div class="tags">
        ${(r.tech_skills || []).concat(r.soft_skills || []).map(k => `<span class="tag tag-matched">${k}</span>`).join('') || '<span style="color:var(--text-dim)">None detected</span>'}
      </div>
    </div>`;

  // Tab: Tips
  renderTips(r.tips);

  showResultTab('skills');
}

// ── Render Job Results ───────────────────────────────────────
function renderJobResults(r) {
  const container = document.getElementById('resultsContainer');
  container.style.display = 'block';
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });

  animateScore(r.score);
  document.getElementById('resultGrade').textContent   = r.grade;
  document.getElementById('resultVerdict').textContent = r.verdict;
  document.getElementById('resultFilename').textContent = `📄 ${r.filename} → ${r.job_title}`;

  const badges = [
    { text: `${r.keyword_match_pct}% Keywords`, cls: r.keyword_match_pct >= 60 ? 'badge-green' : 'badge-red' },
    { text: `${r.matched_skills?.length || 0} Skills Match`, cls: 'badge-gold' },
    { text: `${r.similarity}% Similarity`, cls: 'badge-blue' },
  ];
  renderBadges(badges);
  renderComponents(r.components);

  // Skills tab
  let skillsHTML = `
    <div class="job-match-header">
      <div><div class="jm-label">JOB TITLE</div><div class="jm-value">${r.job_title}</div></div>
      <div style="text-align:right"><div class="jm-label">KEYWORD MATCH</div><div class="jm-pct">${r.keyword_match_pct}%</div></div>
    </div>`;
  if (r.matched_skills?.length) {
    skillsHTML += `<div class="tag-section"><div class="tag-section-title">✅ SKILLS YOU HAVE</div><div class="tags">${r.matched_skills.map(s => `<span class="tag tag-matched">${s}</span>`).join('')}</div></div>`;
  }
  if (r.missing_skills?.length) {
    skillsHTML += `<div class="tag-section"><div class="tag-section-title">❌ SKILLS TO ADD</div><div class="tags">${r.missing_skills.map(s => `<span class="tag tag-missing">${s}</span>`).join('')}</div></div>`;
  }
  document.getElementById('tabSkills').innerHTML = skillsHTML;

  // Keywords tab
  document.getElementById('tabKeywords').innerHTML = `
    <div class="keyword-split">
      <div>
        <div class="kw-group-title kw-matched-title">✅ MATCHED KEYWORDS (${r.matched_keywords?.length || 0})</div>
        <div class="tags">${(r.matched_keywords || []).map(k => `<span class="tag tag-matched">${k}</span>`).join('') || '<span style="color:var(--text-dim)">None</span>'}</div>
      </div>
      <div>
        <div class="kw-group-title kw-missing-title">❌ MISSING KEYWORDS (${r.missing_keywords?.length || 0})</div>
        <div class="tags">${(r.missing_keywords || []).map(k => `<span class="tag tag-missing">${k}</span>`).join('') || '<span style="color:var(--text-dim)">None</span>'}</div>
      </div>
    </div>`;

  renderTips(r.tips);
  showResultTab('skills');
}

// ── Helpers ──────────────────────────────────────────────────
function animateScore(target) {
  const numEl  = document.getElementById('scoreNumber');
  const arcEl  = document.getElementById('scoreRingArc');
  const circum = 540;

  let current = 0;
  const step  = target / 60;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    numEl.textContent = Math.round(current);
    const offset = circum - (current / 100) * circum;
    arcEl.style.strokeDashoffset = offset;

    // Color
    const color = current >= 70 ? '#4ade80' : current >= 50 ? '#c8a96e' : current >= 30 ? '#fb923c' : '#f87171';
    arcEl.style.stroke = color;
    numEl.style.backgroundImage = `linear-gradient(135deg, ${color}, ${color}aa)`;

    if (current >= target) clearInterval(timer);
  }, 30);
}

function renderBadges(badges) {
  document.getElementById('resultBadges').innerHTML =
    badges.map(b => `<span class="badge ${b.cls}">${b.text}</span>`).join('');
}

function renderComponents(comps) {
  const grid = document.getElementById('componentsGrid');
  grid.innerHTML = '';

  Object.entries(comps).forEach(([name, data]) => {
    const score = data.score;
    const cls   = score >= 75 ? 'score-high' : score >= 50 ? 'score-mid' : score >= 30 ? 'score-low' : 'score-poor';
    const bar   = score >= 75 ? 'bar-high'   : score >= 50 ? 'bar-mid'   : score >= 30 ? 'bar-low'   : 'bar-poor';

    const card = document.createElement('div');
    card.className = 'component-card';
    card.innerHTML = `
      <div class="comp-name">${name.toUpperCase()}</div>
      <div class="comp-score-row">
        <span class="comp-score-num ${cls}">${score}</span>
        <span class="comp-score-max">/100</span>
      </div>
      <div class="comp-weight">Weight: ${data.weight || ''}</div>
      <div class="comp-bar"><div class="comp-bar-fill ${bar}" style="width:0%" data-target="${score}%"></div></div>`;
    grid.appendChild(card);

    // Animate bar
    setTimeout(() => {
      card.querySelector('.comp-bar-fill').style.width = score + '%';
    }, 100);
  });
}

function renderTips(tips) {
  if (!tips || !tips.length) {
    document.getElementById('tabTips').innerHTML = '<p style="color:var(--success);padding:20px">🎉 Excellent! No major issues detected.</p>';
    return;
  }
  document.getElementById('tabTips').innerHTML = `
    <div class="tips-list">
      ${tips.map((t, i) => `
        <div class="tip-item">
          <span class="tip-num">${i + 1}</span>
          <span class="tip-text">${t}</span>
        </div>`).join('')}
    </div>`;
}

function showResultTab(tab) {
  document.querySelectorAll('.result-tab').forEach((t, i) => {
    const tabs = ['skills', 'keywords', 'tips'];
    t.classList.toggle('active', tabs[i] === tab);
  });
  document.getElementById('tabSkills').classList.toggle('active', tab === 'skills');
  document.getElementById('tabKeywords').classList.toggle('active', tab === 'keywords');
  document.getElementById('tabTips').classList.toggle('active', tab === 'tips');
}

function resetApp() {
  files = { general: null, job: null };
  document.getElementById('resultsContainer').style.display = 'none';
  document.getElementById('fileInputGeneral').value = '';
  document.getElementById('fileInputJob').value = '';
  ['General', 'Job'].forEach(m => {
    const info = document.getElementById(`fileInfo${m}`);
    const zone = document.getElementById(`uploadZone${m}`);
    info.style.display = 'none';
    zone.classList.remove('has-file');
  });
  document.getElementById('analyzeBtnGeneral').disabled = true;
  document.getElementById('analyzeBtnJob').disabled = true;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Server Health Check ──────────────────────────────────────
async function checkServer() {
  try {
    const resp = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    if (!resp.ok) throw new Error();
    // Server is up — update badge
    const badge = document.querySelector('.nav-badge');
    if (badge) {
      badge.innerHTML = '<span class="pulse-dot"></span> Engine Online';
    }
  } catch {
    const badge = document.querySelector('.nav-badge');
    if (badge) {
      badge.style.color = '#fb923c';
      badge.style.background = 'rgba(251,146,60,0.08)';
      badge.style.borderColor = 'rgba(251,146,60,0.2)';
      badge.innerHTML = '⚠️ Start app.py';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  checkServer();
  setTimeout(checkServer, 5000);
});

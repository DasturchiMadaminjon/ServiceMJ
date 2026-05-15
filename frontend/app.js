'use strict';

// ─── KONFIGURATSIYA ────────────────────────────────
const API = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8000/api'
  : '/api';

// ─── HOLAT ─────────────────────────────────────────
let state = {
  access:            localStorage.getItem('access')  || null,
  refresh:           localStorage.getItem('refresh') || null,
  user:              JSON.parse(localStorage.getItem('user') || 'null'),
  providerProfileId: null,
  selectedSkillIds:  [],
  currentPage:       1,
  currentStatus:     '',
  providerPage:      1,
  providerOrdering:  '-rating',
  myPortfolioItems:  [],
};

// ─── TOKEN YANGILASH ───────────────────────────────
async function refreshToken() {
  if (!state.refresh) return false;
  try {
    const r = await fetch(`${API}/accounts/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: state.refresh }),
    });
    if (!r.ok) { logout(); return false; }
    const d = await r.json();
    state.access = d.access;
    localStorage.setItem('access', d.access);
    return true;
  } catch { return false; }
}

// ─── API SO'ROV ─────────────────────────────────────
async function api(path, opts = {}, retry = true) {
  const headers = { ...(opts.headers || {}) };
  if (!(opts.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (state.access) headers['Authorization'] = 'Bearer ' + state.access;

  let r = await fetch(`${API}${path}`, { ...opts, headers });

  if (r.status === 401 && retry) {
    const ok = await refreshToken();
    if (ok) return api(path, opts, false);
    logout(); return r;
  }
  return r;
}

// ─── TOAST ─────────────────────────────────────────
let toastTimer;
function toast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add('hidden'), 3000);
}

// ─── SAHIFALAR ─────────────────────────────────────
const PAGE_LOADERS = {
  'home':               loadHome,
  'providers':          () => loadProviders(1, state.providerOrdering),
  'my-requests':        loadMyRequests,
  'available-requests': () => loadAvailableRequests('pending'),
  'profile':            loadProfile,
  'my-portfolio':       loadMyPortfolio,
  'admin-stats':        loadAdminStats,
  'create-request':     loadCategories,
};

function showPage(name) {
  document.querySelectorAll('.page,.page-center').forEach(p => p.classList.add('hidden'));
  const el = document.getElementById(`page-${name}`);
  if (el) el.classList.remove('hidden');
  if (PAGE_LOADERS[name]) PAGE_LOADERS[name]();
  window.scrollTo(0, 0);
  // nav burger yopish
  document.getElementById('nav-links').classList.remove('open');
}

// ─── AUTH ──────────────────────────────────────────
function switchTab(tab) {
  document.getElementById('form-login').classList.toggle('hidden', tab !== 'login');
  document.getElementById('form-register').classList.toggle('hidden', tab !== 'register');
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-reg').classList.toggle('active', tab === 'register');
}

async function doLogin() {
  const errEl = document.getElementById('l-err');
  errEl.classList.add('hidden');
  const r = await fetch(`${API}/accounts/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: document.getElementById('l-username').value.trim(),
      password: document.getElementById('l-password').value,
    }),
  });
  const d = await r.json();
  if (!r.ok) { showErr(errEl, 'Login yoki parol noto\'g\'ri'); return; }
  state.access = d.access; state.refresh = d.refresh;
  localStorage.setItem('access', d.access);
  localStorage.setItem('refresh', d.refresh);
  await loadCurrentUser();
  initApp();
}

async function doRegister() {
  const errEl = document.getElementById('r-err');
  errEl.classList.add('hidden');
  const body = {
    username:     document.getElementById('r-username').value.trim(),
    phone_number: document.getElementById('r-phone').value.trim(),
    email:        document.getElementById('r-email').value.trim(),
    role:         document.getElementById('r-role').value,
    password:     document.getElementById('r-password').value,
  };
  const r = await fetch(`${API}/accounts/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const d = await r.json();
  if (!r.ok) { showErr(errEl, Object.values(d).flat().join(' | ')); return; }
  toast('Ro\'yxatdan o\'tdingiz! Endi kiring.', 'success');
  switchTab('login');
}

async function loadCurrentUser() {
  const r = await api('/accounts/profile/');
  if (!r.ok) return;
  const u = await r.json();
  state.user = u;
  localStorage.setItem('user', JSON.stringify(u));
}

function logout() {
  state.access = state.refresh = state.user = null;
  state.providerProfileId = null; state.selectedSkillIds = [];
  localStorage.clear();
  document.getElementById('navbar').classList.add('hidden');
  showPage('auth');
}

// ─── INIT ──────────────────────────────────────────
function initApp() {
  if (!state.user) return showPage('auth');
  document.getElementById('navbar').classList.remove('hidden');
  const role = state.user.role;
  document.getElementById('nav-client').classList.toggle('hidden',  role !== 'client');
  document.getElementById('nav-client2').classList.toggle('hidden', role !== 'client');
  document.getElementById('nav-provider').classList.toggle('hidden',  role !== 'provider');
  document.getElementById('nav-provider2').classList.toggle('hidden', role !== 'provider');
  document.getElementById('nav-admin').classList.toggle('hidden',   !state.user.is_staff && role !== 'admin');
  document.getElementById('home-client-btn')?.classList.toggle('hidden', role !== 'client');
  showPage('home');
}

// ─── HOME ──────────────────────────────────────────
async function loadHome() {
  const r = await api('/services/categories/');
  if (!r.ok) return;
  const d = await r.json();
  const cats = d.results || d;
  const icons = ['🔧','⚡','🪟','🏗️','🎨','🌿','🚿','🔌','🛠️','🏠'];
  document.getElementById('home-categories').innerHTML = cats.map((c, i) => `
    <div class="cat-card" onclick="loadProviders(1,'-rating')">
      <div class="cat-icon">${icons[i % icons.length]}</div>
      <div class="cat-name">${c.name}</div>
    </div>`).join('') || '<p style="color:var(--text-soft);text-align:center;padding:2rem">Kategoriyalar yuklanmoqda...</p>';
}

// ─── PROVIDERS ─────────────────────────────────────
let searchTimer;
function searchProviders() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadProviders(1, state.providerOrdering), 400);
}

async function loadProviders(page = 1, ordering = '-rating') {
  state.providerPage = page; state.providerOrdering = ordering;
  document.querySelectorAll('.sort-row .chip').forEach(c => {
    c.classList.toggle('active', c.getAttribute('onclick')?.includes(ordering));
  });
  const q = document.getElementById('prov-search')?.value.trim() || '';
  const r = await api(`/services/providers/?page=${page}&ordering=${ordering}${q ? '&search=' + encodeURIComponent(q) : ''}`);
  if (!r.ok) return;
  const d = await r.json();
  const list = document.getElementById('providers-list');
  list.innerHTML = (d.results || []).map(provCard).join('') ||
    '<div class="empty"><div class="empty-icon">😔</div>Usta topilmadi</div>';
  renderPagination('providers-pagination', d, p => loadProviders(p, ordering));
}

function provCard(p) {
  const stars = '⭐'.repeat(Math.round(Number(p.rating || 0)));
  const skills = (p.skills || []).slice(0, 3).map(s =>
    `<span class="skill-tag">${s.name}</span>`).join('');
  const avatar = p.user?.avatar_url ||
    `https://ui-avatars.com/api/?name=${encodeURIComponent(p.user?.username||'U')}&background=6366f1&color=fff&size=60`;
  return `
    <div class="card prov-card" onclick="showProviderDetail(${p.id})">
      <div class="prov-header">
        <img class="prov-avatar" src="${avatar}" alt="">
        <div>
          <div class="prov-name">${p.user?.username || '—'}</div>
          <div class="prov-rating">${stars || '☆☆☆☆☆'} (${p.review_count || 0} sharh)</div>
        </div>
      </div>
      ${skills ? `<div class="skill-tags" style="margin-bottom:.5rem">${skills}</div>` : ''}
      <div class="card-meta">
        📅 ${p.experience_years} yil tajriba
        ${p.hourly_rate ? ` · 💰 ${Number(p.hourly_rate).toLocaleString()} so'm/soat` : ''}
      </div>
      <div style="font-size:.82rem;color:var(--text-soft)">${(p.bio||'').slice(0,80)}${p.bio?.length>80?'...':''}</div>
    </div>`;
}

async function showProviderDetail(id) {
  showPage('provider-detail');
  const [pr, rv] = await Promise.all([
    api(`/services/providers/${id}/`),
    api(`/services/providers/${id}/reviews/`),
  ]);
  if (!pr.ok) return;
  const p = await pr.json();
  const reviews = rv.ok ? ((await rv.json()).results || []) : [];
  const avatar = p.user?.avatar_url ||
    `https://ui-avatars.com/api/?name=${encodeURIComponent(p.user?.username||'U')}&background=6366f1&color=fff&size=90`;

  const skills = (p.skills || []).map(s => `<span class="skill-tag">${s.name}</span>`).join('') ||
    '<span style="color:var(--text-soft)">Ko\'nikmalar ko\'rsatilmagan</span>';

  const portfolio = (p.portfolio_items || []).map(item => `
    <div class="portfolio-item">
      ${item.image_url
        ? `<img class="portfolio-img" src="${item.image_url}" alt="${item.title}">`
        : `<div class="portfolio-img-placeholder">🖼️</div>`}
      <div class="portfolio-item-body">
        <div class="portfolio-item-title">${item.title}</div>
        ${item.description ? `<div class="portfolio-item-desc">${item.description}</div>` : ''}
      </div>
    </div>`).join('') || '<p style="color:var(--text-soft)">Portfolio yo\'q</p>';

  const revHTML = reviews.map(rv => `
    <div class="review-card">
      <div class="review-header">
        <span class="review-author">@${rv.reviewer_name}</span>
        <span class="review-stars">${'⭐'.repeat(rv.rating)}</span>
      </div>
      ${rv.comment ? `<div class="review-text">${rv.comment}</div>` : ''}
    </div>`).join('') || '<p style="color:var(--text-soft)">Hali sharh yo\'q</p>';

  document.getElementById('provider-detail-content').innerHTML = `
    <div class="detail-hero">
      <img class="detail-avatar" src="${avatar}" alt="">
      <div>
        <div class="detail-name">${p.user?.username || '—'}</div>
        <div class="detail-meta">
          ⭐ ${Number(p.rating||0).toFixed(1)} · 📅 ${p.experience_years} yil · 
          ${p.hourly_rate ? `💰 ${Number(p.hourly_rate).toLocaleString()} so'm/soat` : ''}
        </div>
        ${p.bio ? `<p style="margin-top:.5rem;font-size:.9rem">${p.bio}</p>` : ''}
      </div>
    </div>
    <div class="section-title">Ko'nikmalar</div>
    <div class="skill-tags">${skills}</div>
    <div class="section-title">Portfolio (${(p.portfolio_items||[]).length})</div>
    <div class="portfolio-grid">${portfolio}</div>
    <div class="section-title">Sharhlar (${reviews.length})</div>
    <div>${revHTML}</div>`;
}

// ─── MY REQUESTS (client) ──────────────────────────
function filterMyRequests(s) {
  state.currentStatus = s;
  document.querySelectorAll('#page-my-requests .chip').forEach(c =>
    c.classList.toggle('active', c.getAttribute('onclick')?.includes(`'${s}'`)));
  loadMyRequests();
}

async function loadMyRequests(page = 1) {
  const url = `/services/my-requests/?page=${page}${state.currentStatus ? '&status='+state.currentStatus : ''}`;
  const r = await api(url);
  if (!r.ok) return;
  const d = await r.json();
  const items = d.results !== undefined ? d.results : d;
  const count = d.count !== undefined ? d.count : items.length;
  document.getElementById('my-requests-list').innerHTML = items.map(clientReqCard).join('') ||
    '<div class="empty"><div class="empty-icon">📋</div>So\'rovlar yo\'q</div>';
  if (d.results !== undefined)
    renderPagination('my-requests-pagination', d, loadMyRequests);
}

function clientReqCard(req) {
  const canReview = req.status === 'completed' && req.can_review;
  const canCancel = ['pending', 'accepted'].includes(req.status);
  return `
    <div class="card">
      <div class="card-title">${req.category_name || 'Kategoriyasiz'}</div>
      <div class="card-meta">📅 ${new Date(req.created_at).toLocaleDateString('uz-UZ')}
        ${req.budget ? ` · 💰 ${Number(req.budget).toLocaleString()} so'm` : ''}
        ${req.provider_info ? ` · 🔧 ${req.provider_info.username}` : ''}</div>
      <div style="font-size:.83rem;margin-bottom:.5rem">${req.description.slice(0,100)}...</div>
      <span class="status status-${req.status}">${statusLabel(req.status)}</span>
      <div class="card-actions">
        ${canCancel ? `<button class="btn btn-sm btn-outline" onclick="changeStatus(${req.id},'cancelled')">Bekor qilish</button>` : ''}
        ${canReview ? `<button class="btn btn-sm btn-primary" onclick="openReview(${req.id})">⭐ Sharh yozish</button>` : ''}
      </div>
    </div>`;
}

// ─── AVAILABLE REQUESTS (provider) ─────────────────
function filterProviderRequests(s) {
  document.querySelectorAll('#page-available-requests .chip').forEach(c =>
    c.classList.toggle('active', c.getAttribute('onclick')?.includes(`'${s}'`)));
  loadAvailableRequests(s);
}

async function loadAvailableRequests(statusFilter = 'pending', page = 1) {
  const r = await api(`/services/requests/?status=${statusFilter}&page=${page}`);
  if (!r.ok) return;
  const d = await r.json();
  document.getElementById('available-requests-list').innerHTML =
    (d.results || []).map(req => providerReqCard(req, statusFilter)).join('') ||
    '<div class="empty"><div class="empty-icon">📭</div>Buyurtmalar yo\'q</div>';
  renderPagination('available-requests-pagination', d, p => loadAvailableRequests(statusFilter, p));
}

function providerReqCard(req, tab) {
  const actions = {
    pending:    `<button class="btn btn-sm btn-success" onclick="changeStatus(${req.id},'accepted')">✅ Qabul qilish</button>`,
    accepted:   `<button class="btn btn-sm btn-primary" onclick="changeStatus(${req.id},'in_progress')">🔧 Ishni boshlash</button>
                 <button class="btn btn-sm btn-outline" onclick="changeStatus(${req.id},'cancelled')">Bekor</button>`,
    in_progress:`<button class="btn btn-sm btn-success" onclick="changeStatus(${req.id},'completed')">🎉 Tugatdim</button>`,
    completed:  '',
  };
  return `
    <div class="card">
      <div class="card-title">${req.category_name || 'Kategoriyasiz'}</div>
      <div class="card-meta">👤 ${req.customer?.username}
        · 📅 ${new Date(req.created_at).toLocaleDateString('uz-UZ')}
        ${req.budget ? ` · 💰 ${Number(req.budget).toLocaleString()} so'm` : ''}
        ${req.address ? ` · 📍 ${req.address}` : ''}</div>
      <div style="font-size:.83rem;margin-bottom:.5rem">${req.description.slice(0,120)}</div>
      <span class="status status-${req.status}">${statusLabel(req.status)}</span>
      <div class="card-actions">${actions[tab] || ''}</div>
    </div>`;
}

// ─── STATUS O'ZGARTIRISH ────────────────────────────
async function changeStatus(reqId, newStatus) {
  const r = await api(`/services/requests/${reqId}/status/`, {
    method: 'PATCH',
    body: JSON.stringify({ status: newStatus }),
  });
  const d = await r.json();
  if (!r.ok) { toast(Object.values(d).flat().join(' '), 'error'); return; }
  toast('Holat yangilandi!', 'success');
  // Sahifani qayta yuklash
  const cur = document.querySelector('.page:not(.hidden)');
  if (cur?.id === 'page-my-requests') loadMyRequests();
  else if (cur?.id === 'page-available-requests') loadAvailableRequests(newStatus);
}

// ─── CREATE REQUEST ─────────────────────────────────
async function loadCategories() {
  const r = await api('/services/categories/');
  if (!r.ok) return;
  const d = await r.json();
  const sel = document.getElementById('cr-category');
  sel.innerHTML = '<option value="">— tanlang —</option>' +
    (d.results || d).map(c => `<option value="${c.id}">${c.name}</option>`).join('');
}

async function createRequest() {
  const errEl = document.getElementById('cr-err');
  errEl.classList.add('hidden');
  const body = {
    description: document.getElementById('cr-desc').value.trim(),
    category:    document.getElementById('cr-category').value || null,
    address:     document.getElementById('cr-address').value.trim(),
    budget:      document.getElementById('cr-budget').value || null,
  };
  if (!body.description) { showErr(errEl, 'Tavsif kiritish shart'); return; }
  const r = await api('/services/requests/', { method: 'POST', body: JSON.stringify(body) });
  const d = await r.json();
  if (!r.ok) { showErr(errEl, Object.values(d).flat().join(' ')); return; }
  toast('Buyurtma yuborildi!', 'success');
  document.getElementById('cr-desc').value = '';
  document.getElementById('cr-address').value = '';
  document.getElementById('cr-budget').value = '';
  showPage('my-requests');
}

// ─── PROFILE ────────────────────────────────────────
async function loadProfile() {
  const r = await api('/accounts/profile/');
  if (!r.ok) return;
  const u = await r.json();
  state.user = u;
  document.getElementById('p-username').value = u.username || '';
  document.getElementById('p-email').value    = u.email || '';
  document.getElementById('p-phone').value    = u.phone_number || '';
  document.getElementById('p-role').value     = u.role;
  document.getElementById('p-password').value = ''; // Parol maydonini tozalash
  
  // Tasdiqlash holatini ko'rsatish
  document.getElementById('verify-section').classList.toggle('hidden', u.is_verified);
  document.getElementById('verified-section').classList.toggle('hidden', !u.is_verified);

  document.getElementById('profile-avatar').src = u.avatar_url ||
    `https://ui-avatars.com/api/?name=${encodeURIComponent(u.username)}&background=6366f1&color=fff&size=80`;
  
  if (u.role === 'provider') {
    document.getElementById('provider-profile-section').classList.remove('hidden');
    loadProviderProfile();
  } else {
    document.getElementById('provider-profile-section').classList.add('hidden');
  }
}

async function sendOTP() {
  const r = await api('/accounts/send-otp/', { method: 'POST' });
  if (r.ok) {
    toast('Kod yuborildi!', 'success');
    document.getElementById('otp-code').value = '';
    document.getElementById('otp-err').classList.add('hidden');
    document.getElementById('otp-modal').classList.remove('hidden');
  } else {
    toast('Xatolik yuz berdi', 'error');
  }
}

async function verifyOTP() {
  const code = document.getElementById('otp-code').value.trim();
  const errEl = document.getElementById('otp-err');
  errEl.classList.add('hidden');
  
  if (code.length !== 4) {
    showErr(errEl, '4 xonali kodni kiriting');
    return;
  }
  
  const r = await api('/accounts/verify-otp/', { 
    method: 'POST', 
    body: JSON.stringify({ code }) 
  });
  const d = await r.json();
  
  if (r.ok) {
    toast('Muvaffaqiyatli tasdiqlandi!', 'success');
    closeModal('otp-modal');
    loadProfile(); // Profilni yangilash (yashil belgi chiqishi uchun)
  } else {
    showErr(errEl, d.detail || 'Kod noto\'g\'ri');
  }
}

async function saveProfile() {
  const body = {
    username:     document.getElementById('p-username').value.trim(),
    email:        document.getElementById('p-email').value.trim(),
    phone_number: document.getElementById('p-phone').value.trim(),
    role:         document.getElementById('p-role').value,
  };
  
  const pass = document.getElementById('p-password').value;
  if (pass) {
    if (pass.length < 8) {
      toast('Parol kamida 8 ta belgidan iborat bo\'lishi kerak', 'error');
      return;
    }
    body.password = pass;
  }

  const errEl = document.getElementById('p-err');
  const okEl  = document.getElementById('p-ok');
  errEl.classList.add('hidden'); okEl.classList.add('hidden');
  
  const r = await api('/accounts/profile/', { method: 'PATCH', body: JSON.stringify(body) });
  const d = await r.json();
  
  if (!r.ok) { showErr(errEl, Object.values(d).flat().join(', ')); return; }
  
  state.user = d;
  localStorage.setItem('user', JSON.stringify(d));
  
  document.getElementById('p-password').value = '';
  okEl.textContent = '✅ Ma\'lumotlar saqlandi!'; okEl.classList.remove('hidden');
  toast('Profil yangilandi!', 'success');
  
  // Navbarni va rollarni qayta yuklash
  initApp();
  // Agar rol o'zgargan bo'lsa, profil sahifasini qayta yuklash (Usta bo'limi chiqishi uchun)
  loadProfile();
}

async function uploadAvatar(input) {
  const file = input.files[0];
  if (!file) return;
  // 10 MB tekshiruv
  if (file.size > 10 * 1024 * 1024) {
    toast(`Rasm ${(file.size/1024/1024).toFixed(1)} MB — 10 MB dan oshmasin`, 'error');
    return;
  }
  const progressWrap = document.getElementById('avatar-progress');
  const bar          = document.getElementById('avatar-bar');
  const statusTxt    = document.getElementById('avatar-status');
  progressWrap.classList.remove('hidden');
  bar.style.width = '30%';
  statusTxt.textContent = 'Yuklanmoqda...';

  const fd = new FormData();
  fd.append('avatar', file);
  const r = await api('/accounts/profile/', { method: 'PATCH', body: fd });
  bar.style.width = '100%';
  if (!r.ok) {
    const d = await r.json();
    statusTxt.textContent = 'Xato!';
    toast(Object.values(d).flat().join(' '), 'error');
    return;
  }
  const u = await r.json();
  document.getElementById('profile-avatar').src = u.avatar_url || '';
  statusTxt.textContent = '✅ Rasm yuklandi!';
  setTimeout(() => progressWrap.classList.add('hidden'), 2000);
  toast('Avatar yangilandi!', 'success');
}

// ─── PROVIDER PROFILE ──────────────────────────────
async function loadProviderProfile() {
  const [pr, sk] = await Promise.all([
    api('/services/providers/'),
    api('/services/skills/'),
  ]);
  // Skills select
  if (sk.ok) {
    const sd = await sk.json();
    const skillSel = document.getElementById('pp-skills-select');
    skillSel.innerHTML = '<option value="">— ko\'nikma qo\'shish —</option>' +
      (sd.results || []).map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  }
  if (!pr.ok) return;
  const d = await pr.json();
  const my = (d.results || []).find(p => p.user?.id === state.user?.id);
  if (my) {
    state.providerProfileId = my.id;
    state.selectedSkillIds = (my.skills || []).map(s => ({ id: s.id, name: s.name }));
    document.getElementById('pp-bio').value  = my.bio || '';
    document.getElementById('pp-exp').value  = my.experience_years || 0;
    document.getElementById('pp-rate').value = my.hourly_rate || '';
    renderSelectedSkills();
  }
}

function renderSelectedSkills() {
  document.getElementById('pp-skills-selected').innerHTML =
    state.selectedSkillIds.map(s => `
      <span class="skill-tag">${s.name}
        <span class="remove-skill" onclick="removeSkill(${s.id})">×</span>
      </span>`).join('');
}

function addSkillFromSelect(sel) {
  const id   = parseInt(sel.value);
  const name = sel.options[sel.selectedIndex].text;
  if (!id) return;
  if (!state.selectedSkillIds.find(s => s.id === id))
    state.selectedSkillIds.push({ id, name });
  sel.value = '';
  renderSelectedSkills();
}

function removeSkill(id) {
  state.selectedSkillIds = state.selectedSkillIds.filter(s => s.id !== id);
  renderSelectedSkills();
}

async function saveProviderProfile() {
  const body = {
    bio:              document.getElementById('pp-bio').value.trim(),
    experience_years: parseInt(document.getElementById('pp-exp').value) || 0,
    hourly_rate:      document.getElementById('pp-rate').value || null,
    skill_ids:        state.selectedSkillIds.map(s => s.id),
  };
  const errEl = document.getElementById('pp-err');
  const okEl  = document.getElementById('pp-ok');
  errEl.classList.add('hidden'); okEl.classList.add('hidden');
  const method = state.providerProfileId ? 'PATCH' : 'POST';
  const path   = state.providerProfileId
    ? `/services/providers/${state.providerProfileId}/`
    : '/services/providers/';
  const r = await api(path, { method, body: JSON.stringify(body) });
  const d = await r.json();
  if (!r.ok) { showErr(errEl, Object.values(d).flat().join(', ')); return; }
  state.providerProfileId = d.id;
  okEl.textContent = '✅ Profil saqlandi!'; okEl.classList.remove('hidden');
  toast('Usta profili yangilandi!', 'success');
}

// ─── MY PORTFOLIO (provider) ───────────────────────
async function loadMyPortfolio() {
  if (!state.providerProfileId) {
    const r = await api('/services/providers/');
    if (r.ok) {
      const d = await r.json();
      const my = (d.results || []).find(p => p.user?.id === state.user?.id);
      if (my) state.providerProfileId = my.id;
    }
  }
  if (!state.providerProfileId) {
    document.getElementById('my-portfolio-list').innerHTML =
      '<div class="empty"><div class="empty-icon">👷</div>Avval profilingizni yarating</div>';
    return;
  }
  const r = await api(`/services/providers/${state.providerProfileId}/portfolio/`);
  if (!r.ok) return;
  const items = await r.json();
  state.myPortfolioItems = Array.isArray(items) ? items : (items.results || []);
  renderMyPortfolio();
}

function renderMyPortfolio() {
  document.getElementById('my-portfolio-list').innerHTML =
    state.myPortfolioItems.map(item => `
      <div class="portfolio-item">
        ${item.image_url
          ? `<img class="portfolio-img" src="${item.image_url}" alt="${item.title}">`
          : `<div class="portfolio-img-placeholder">🖼️</div>`}
        <div class="portfolio-item-body">
          <div class="portfolio-item-title">${item.title}</div>
          ${item.description ? `<div class="portfolio-item-desc">${item.description}</div>` : ''}
          <div class="portfolio-item-actions">
            <button class="btn btn-sm btn-outline" onclick="deletePortfolioItem(${item.id})">🗑️ O'chirish</button>
          </div>
        </div>
      </div>`).join('') ||
    '<div class="empty"><div class="empty-icon">📁</div>Portfolio bo\'sh. Ish namunangizni qo\'shing!</div>';
}

function openPortfolioModal() {
  document.getElementById('port-title').value = '';
  document.getElementById('port-desc').value  = '';
  document.getElementById('port-image').value = '';
  document.getElementById('port-err').classList.add('hidden');
  document.getElementById('portfolio-modal').classList.remove('hidden');
}

async function savePortfolioItem() {
  const title = document.getElementById('port-title').value.trim();
  const errEl = document.getElementById('port-err');
  const btn   = document.querySelector('#portfolio-modal .btn-primary');
  
  if (!title) { showErr(errEl, 'Sarlavha kiritish shart'); return; }

  const fd = new FormData();
  fd.append('title', title);
  fd.append('description', document.getElementById('port-desc').value.trim());
  const imgFile = document.getElementById('port-image').files[0];
  if (imgFile) {
    if (imgFile.size > 10 * 1024 * 1024) { showErr(errEl, 'Rasm 10 MB dan oshmasin'); return; }
    fd.append('image', imgFile);
  }

  // Visual feedback
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Yuklanmoqda...';
  errEl.classList.add('hidden');

  try {
    const r = await api(
      `/services/providers/${state.providerProfileId}/portfolio/`,
      { method: 'POST', body: fd }
    );
    const d = await r.json();
    if (!r.ok) { 
      showErr(errEl, Object.values(d).flat().join(', ')); 
      btn.disabled = false;
      btn.textContent = originalText;
      return; 
    }
    toast('Portfolio qo\'shildi!', 'success');
    closeModal('portfolio-modal');
    loadMyPortfolio();
  } catch (e) {
    showErr(errEl, 'Server bilan ulanishda xato');
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

async function deletePortfolioItem(id) {
  if (!confirm('Portfolio elementini o\'chirmoqchimisiz?')) return;
  const r = await api(
    `/services/providers/${state.providerProfileId}/portfolio/${id}/`,
    { method: 'DELETE' }
  );
  if (r.status === 204) {
    toast('O\'chirildi', 'success');
    loadMyPortfolio();
  } else {
    toast('Xato yuz berdi', 'error');
  }
}

// ─── ADMIN STATS ────────────────────────────────────
async function loadAdminStats() {
  const r = await api('/services/dashboard/stats/');
  if (!r.ok) { document.getElementById('admin-stats-content').innerHTML =
    '<p style="color:var(--danger)">Ruxsat yo\'q yoki xato yuz berdi</p>'; return; }
  const d = await r.json();
  const statusColors = {
    pending:'#f59e0b', accepted:'#3b82f6',
    in_progress:'#8b5cf6', completed:'#10b981', cancelled:'#ef4444'
  };
  const byStatus = Object.entries(d.requests_by_status || {}).map(([s, cnt]) =>
    `<div class="stat-card">
      <div class="stat-num" style="color:${statusColors[s]||'var(--primary)'}">${cnt}</div>
      <div class="stat-label">${statusLabel(s)}</div>
    </div>`).join('');

  document.getElementById('admin-stats-content').innerHTML = `
    <div class="stat-card"><div class="stat-num">${d.total_users}</div><div class="stat-label">Foydalanuvchilar</div></div>
    <div class="stat-card"><div class="stat-num">${d.total_clients}</div><div class="stat-label">Mijozlar</div></div>
    <div class="stat-card"><div class="stat-num">${d.total_providers}</div><div class="stat-label">Ustalar</div></div>
    <div class="stat-card"><div class="stat-num">${d.total_requests}</div><div class="stat-label">Jami so'rovlar</div></div>
    <div class="stat-card"><div class="stat-num">${d.total_reviews}</div><div class="stat-label">Sharhlar</div></div>
    <div class="stat-card"><div class="stat-num">${Number(d.avg_rating||0).toFixed(1)}⭐</div><div class="stat-label">O'rtacha reyting</div></div>
    ${byStatus}`;

  // Admin barcha so'rovlarni ko'radi
  const reqR = await api('/services/requests/?page=1');
  if (reqR.ok) {
    const rd = await reqR.json();
    document.getElementById('admin-requests-list').innerHTML =
      (rd.results || []).map(req => `
        <div class="card">
          <div class="card-title">${req.category_name || 'Kategoriyasiz'}</div>
          <div class="card-meta">👤 ${req.customer?.username}
            ${req.provider_info ? ` · 🔧 ${req.provider_info.username}` : ''}
            · 📅 ${new Date(req.created_at).toLocaleDateString('uz-UZ')}</div>
          <div style="font-size:.82rem;margin-bottom:.4rem">${req.description.slice(0,80)}</div>
          <span class="status status-${req.status}">${statusLabel(req.status)}</span>
        </div>`).join('');
    renderPagination('admin-requests-pagination', rd, p => {
      api(`/services/requests/?page=${p}`).then(r => r.json()).then(d2 => {
        document.getElementById('admin-requests-list').innerHTML =
          (d2.results || []).map(req => `
            <div class="card">
              <div class="card-title">${req.category_name || 'Kategoriyasiz'}</div>
              <div class="card-meta">👤 ${req.customer?.username}</div>
              <span class="status status-${req.status}">${statusLabel(req.status)}</span>
            </div>`).join('');
      });
    });
  }
}

// ─── REVIEW ─────────────────────────────────────────
let currentStar = 0;
function openReview(reqId) {
  document.getElementById('review-req-id').value = reqId;
  document.getElementById('review-comment').value = '';
  document.getElementById('review-rating').value  = '0';
  document.getElementById('rev-err').classList.add('hidden');
  currentStar = 0; updateStars(0);
  document.getElementById('review-modal').classList.remove('hidden');
}

function setStar(n) {
  currentStar = n;
  document.getElementById('review-rating').value = n;
  updateStars(n);
}

function updateStars(n) {
  document.querySelectorAll('#star-picker span').forEach((s, i) => {
    s.classList.toggle('active', i < n);
    s.style.color = i < n ? 'var(--warn)' : '#d1d5db';
  });
}

async function submitReview() {
  const rating = parseInt(document.getElementById('review-rating').value);
  const errEl  = document.getElementById('rev-err');
  if (!rating) { showErr(errEl, 'Reyting tanlang (1–5)'); return; }
  const body = {
    service_request: document.getElementById('review-req-id').value,
    rating,
    comment: document.getElementById('review-comment').value.trim(),
  };
  const r = await api('/services/reviews/', { method: 'POST', body: JSON.stringify(body) });
  const d = await r.json();
  if (!r.ok) { showErr(errEl, Object.values(d).flat().join(' ')); return; }
  toast('Sharh yuborildi! Rahmat ⭐', 'success');
  closeModal('review-modal');
  loadMyRequests();
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
}

// ─── PAGINATION ─────────────────────────────────────
function renderPagination(containerId, data, loadFn) {
  const el = document.getElementById(containerId);
  if (!el || !data.count) { el && (el.innerHTML = ''); return; }
  const total = Math.ceil(data.count / 20);
  if (total <= 1) { el.innerHTML = ''; return; }
  const cur = data.next
    ? (new URL(data.next).searchParams.get('page') || 2) - 1
    : total;
  el.innerHTML = '<div class="pagination">' +
    (data.previous ? `<button onclick="(${loadFn})(${Number(cur)-1})">←</button>` : '') +
    `<button class="active">${cur} / ${total}</button>` +
    (data.next ? `<button onclick="(${loadFn})(${Number(cur)+1})">→</button>` : '') +
    '</div>';
}

// ─── YORDAMCHILAR ────────────────────────────────────
function showErr(el, msg) { el.textContent = msg; el.classList.remove('hidden'); }

function statusLabel(s) {
  return { pending:'Kutilmoqda', accepted:'Qabul qilindi',
           in_progress:'Jarayonda', completed:'Tugallandi',
           cancelled:'Bekor qilindi' }[s] || s;
}

function toggleMenu() {
  document.getElementById('nav-links').classList.toggle('open');
}

// ─── ISHGA TUSHIRISH ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (state.access && state.user) initApp();
  else showPage('auth');
});

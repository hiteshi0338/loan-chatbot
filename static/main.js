let lastIncome         = 0;
let lastCredit         = 0;
let lastEligibility    = "Unknown";
let lastSchemes        = [];
let lastBotReply       = "";
let lastRecommendation = null;
let donutChartInstance = null;
let barChartInstance   = null;
let simTimer           = null;

// ── Animated dots ──
setInterval(() => {
  const dots = document.getElementById("dots");
  if (!dots) return;
  dots.textContent = dots.textContent.length >= 3 ? "" : dots.textContent + ".";
}, 500);

// ── Format helpers ──
function formatCurrency(amount) {
  return "₹" + Number(amount).toLocaleString('en-IN');
}

function formatMarkdown(text) {
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.*?)\*/g,     '<em>$1</em>');
  text = text.replace(/^\* (.+)/gm,    '• $1');
  text = text.replace(/###.*?\n/g,      '');
  text = text.replace(/---/g,           '');
  text = text.replace(/\n/g,            '<br>');
  return text;
}

// ── Eligibility (frontend rule-based) ──
function calculateEligibility(income, credit, emi) {
  const debtRatio = emi / income;
  if (credit >= 750 && income >= 40000 && debtRatio < 0.4) return "High";
  if (credit >= 650 && income >= 25000 && debtRatio < 0.5) return "Medium";
  return "Low";
}

// ── Analyze profile ──
function analyzeProfile() {
  const name       = document.getElementById('name').value || "the user";
  const age        = document.getElementById('age').value;
  const income     = parseFloat(document.getElementById('income').value)     || 0;
  const credit     = parseFloat(document.getElementById('credit').value)     || 0;
  const emi        = parseFloat(document.getElementById('emi').value)        || 0;
  const employment = document.getElementById('employment').value;
  const purpose    = document.getElementById('purpose').value;

  if (!income || !credit) { alert("Please enter Monthly Income and Credit Score."); return; }
  if (income <= 0)         { alert("Income must be greater than 0."); return; }
  if (credit < 300 || credit > 900) { alert("Credit score must be between 300 and 900."); return; }
  if (age && (age < 18 || age > 65)) { alert("Age must be between 18 and 65."); return; }

  const eligibility = calculateEligibility(income, credit, emi);

  let reason = "";
  if (credit >= 750 && income >= 40000 && (emi / income) < 0.4) {
    reason = "Strong credit score, high income, and low existing debt.";
  } else if (credit >= 650 && income >= 25000) {
    reason = "Moderate credit profile with manageable income.";
  } else {
    reason = "Low credit score or high debt ratio affecting eligibility.";
  }

  const badge = document.getElementById('badge');
  badge.style.display = 'block';
  badge.className     = 'eligibility-badge';

  if (eligibility === "High") {
    badge.classList.add('badge-high');
    badge.innerHTML = `✅ High Eligibility<br><small>${reason}</small><br><small>Income: ${formatCurrency(income)}</small>`;
  } else if (eligibility === "Medium") {
    badge.classList.add('badge-medium');
    badge.innerHTML = `⚠️ Medium Eligibility<br><small>${reason}</small>`;
  } else {
    badge.classList.add('badge-low');
    badge.innerHTML = `❌ Low Eligibility<br><small>${reason}</small>`;
  }

  lastIncome = income;
  lastCredit = credit;

  loadDashboard(income, credit, emi, purpose);
  renderCompareTable(income, credit);

  // Lock fields
  ['name','age','income','credit','emi','employment','purpose'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.disabled = true; el.style.opacity = '0.6'; }
  });

  document.getElementById('analyzeBtn').style.display = 'none';
  document.getElementById('editBtn').style.display    = 'block';

  const profileMessage = `My name is ${name}. Age: ${age}.
    Monthly income: ${formatCurrency(income)}. Credit score: ${credit}.
    Existing EMIs: ${formatCurrency(emi)}. Employment: ${employment}.
    Loan purpose: ${purpose}.
    My eligibility is pre-calculated as: ${eligibility}.
    Please analyze my profile and suggest suitable loan options with amounts and interest rates.`;

  sendMessage(profileMessage);
}

// ── Edit mode ──
function enableEditMode() {
  ['name','age','income','credit','emi','employment','purpose'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.disabled = false; el.style.opacity = '1'; el.style.borderColor = '#c9a84c'; }
  });

  document.getElementById('editBtn').style.display       = 'none';
  document.getElementById('analyzeBtn').style.display    = 'block';
  document.getElementById('recommendCard').style.display = 'none';
  document.getElementById('explainCard').style.display   = 'none';
  document.getElementById('returningBanner').style.display = 'none';

  const badge = document.getElementById('badge');
  badge.style.display = 'none';
  badge.className     = 'eligibility-badge';

  const dash = document.getElementById('dashboardPanel');
  dash.style.display  = 'none';
  document.getElementById('dashboardToggleBtn').textContent = 'Dashboard';
  if (donutChartInstance) { donutChartInstance.destroy(); donutChartInstance = null; }
  if (barChartInstance)   { barChartInstance.destroy();   barChartInstance   = null; }

  lastRecommendation = null;
  lastIncome = lastCredit = 0;
  lastEligibility = "Unknown";
  lastSchemes = [];
  lastBotReply = "";

  const simEmpty = document.getElementById('sim_empty');
  const simWrap  = document.getElementById('sim_table_wrap');
  const simLive  = document.getElementById('sim_live');
  if (simEmpty) simEmpty.style.display = 'block';
  if (simWrap)  simWrap.style.display  = 'none';
  if (simLive)  simLive.style.display  = 'none';

  appendMessage('bot', '✏️ Profile unlocked. Update your details and click Analyze again.');
}


async function sendMessage(customMessage = null) {
    const input = document.getElementById('userInput');
    const message = customMessage || input.value.trim();
    if (!message) return;
    if (!customMessage && isBizQuery(message)) {
        appendMessage('user', message);
        input.value = '';
        renderBizPrefsUI(message);
        return;
    }

    // ADD RIGHT AFTER the isBizQuery block
    if (!customMessage && isEduQuery(message)) {
        appendMessage('user', message);
        input.value = '';
        renderEduPrefsUI(message);
        return;
    }

    if (!customMessage) {
        appendMessage('user', message);
        input.value = '';
    } else {
        appendMessage('user', '🔍 Analyzing my financial profile...');
    }

    const typing = document.getElementById('typing');
    typing.style.display = 'block';
    scrollToBottom();

    const income  = document.getElementById('income').value;
    const credit  = document.getElementById('credit').value;
    const emi     = document.getElementById('emi').value;
    const purpose = document.getElementById('purpose').value;

    const payload = { message, income, credit, emi, purpose };

    // ✅ Create bot bubble
    const chatWindow = document.getElementById('chatWindow');

    const botDiv = document.createElement('div');
    botDiv.className = 'message bot';

    // ❌ REMOVE ID (critical fix)
    botDiv.innerHTML = `
        <div class="sender">LoanAdvisor AI</div>
        <span class="streamTarget"></span>
    `;

    chatWindow.appendChild(botDiv);

    // ✅ scope inside this message only
    const streamTarget = botDiv.querySelector('.streamTarget');

    // keep typing visible until response starts
    const streamSuccess = await tryStream(payload, streamTarget);

    typing.style.display = 'none';

    if (!streamSuccess) {
        console.warn('Stream failed — falling back to /chat');
        await tryFallback(payload, streamTarget);
    }

    scrollToBottom();
}



async function tryStream(payload, streamTarget) {
    try {
        const controller = new AbortController();
        // ✅ Timeout — if no data in 8 seconds, abort
        const timeout = setTimeout(() => controller.abort(), 8000);

        const response = await fetch('/chat_stream', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload),
            signal:  controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) return false;

        const reader  = response.body.getReader();
        const decoder = new TextDecoder();
        let   buffer  = '';
        let   fullText = '';
        let   gotChunk = false;

        // ✅ Secondary timeout — if no chunk in 10s, give up
        let chunkTimeout = setTimeout(() => reader.cancel(), 10000);

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            clearTimeout(chunkTimeout);
            chunkTimeout = setTimeout(() => reader.cancel(), 10000);

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const parsed = JSON.parse(line.slice(6));
                    if (parsed.text) {
                        fullText += parsed.text;
                        gotChunk  = true;
                        streamTarget.innerHTML = formatMarkdown(fullText);
                        scrollToBottom();
                    }
                    if (parsed.done) {
                        clearTimeout(chunkTimeout);
                        lastBotReply    = fullText          || lastBotReply;
                        lastEligibility = parsed.eligibility || lastEligibility;
                        lastSchemes     = parsed.schemes     || lastSchemes;
                        if (parsed.recommendation) {
                            showRecommendation(parsed.recommendation);
                            lastRecommendation = parsed.recommendation;
                        }
                        if (parsed.explanation) showExplanation(parsed.explanation);
                        // if (parsed.delta)       showDelta(parsed.delta);
                        if (parsed.delta) {
                              console.log("DELTA RECEIVED:", parsed.delta); // ✅ debug
                              showDelta(parsed.delta);
                          }
                        return true; // ✅ stream succeeded
                    }
                } catch { continue; }
            }
        }
        clearTimeout(chunkTimeout);
        return gotChunk; // ✅ only counts as success if we got real data

    } catch (err) {
        console.warn('Stream error:', err.message);
        return false;
    }
}

async function tryFallback(payload, streamTarget) {
    try {
        streamTarget.innerHTML = '<em style="color:#aaa">Connecting...</em>';
        const response = await fetch('/chat', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload)
        });
        const data = await response.json();

        lastBotReply    = data.reply          || lastBotReply;
        lastEligibility = data.eligibility    || lastEligibility;
        lastSchemes     = data.schemes        || lastSchemes;

        if (data.recommendation) {
            showRecommendation(data.recommendation);
            lastRecommendation = data.recommendation;
        }
        if (data.explanation) showExplanation(data.explanation);
        if (data.delta)       showDelta(data.delta);

        streamTarget.innerHTML = formatMarkdown(data.reply || '⚠️ No response received.');

    } catch (err) {
        streamTarget.innerHTML = '⚠️ Something went wrong. Please try again.';
    }
}





// ── Chat helpers ──
function appendMessage(sender, text) {
  const chatWindow = document.getElementById('chatWindow');
  const div        = document.createElement('div');
  div.className    = `message ${sender}`;
  div.innerHTML    = `
    <div class="sender">${sender === 'bot' ? 'LoanAdvisor AI' : 'You'}</div>
    ${sender === 'bot' ? formatMarkdown(text) : text}
  `;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function scrollToBottom() {
  const cw = document.getElementById('chatWindow');
  cw.scrollTop = cw.scrollHeight;
}

function clearChat() {
  const chatWindow = document.getElementById("chatWindow");
  chatWindow.querySelectorAll('.message, .typing').forEach(m => m.classList.add('fade-out'));
  setTimeout(() => {
    chatWindow.innerHTML = "";
    appendMessage('bot', 'Chat cleared. How can I assist you again?');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing';
    typingDiv.id        = 'typing';
    typingDiv.innerHTML = '⏳ Processing<span id="dots"></span>';
    chatWindow.appendChild(typingDiv);
    fetch('/clear_chat', { method: 'POST' });
  }, 400);
}

// ── Download report ──
async function downloadReport() {
  const btn = document.getElementById('download-btn');
  if (!lastIncome && !lastCredit) {
    alert("Please analyze your profile first before downloading the report.");
    return;
  }
  btn.classList.add('loading');
  btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> ...`;

  try {
    const response = await fetch("/download_report", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        income:      lastIncome,
        credit:      lastCredit,
        eligibility: lastEligibility,
        schemes:     lastSchemes,
        summary:     lastBotReply,
        emi_data:    null
      })
    });
    if (!response.ok) throw new Error("failed");
    const blob = await response.blob();
    const url  = window.URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = "Loan_Eligibility_Report.pdf";
    a.click();
    window.URL.revokeObjectURL(url);
  } catch {
    alert("Could not generate report. Please try again.");
  } finally {
    btn.classList.remove('loading');
    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;
  }
}

// ── Dashboard ──
async function loadDashboard(income, credit, emi, purpose) {
  const res = await fetch('/dashboard_data', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ income, credit, emi, purpose })
  });
  const d = await res.json();
  if (d.error) return;

  const fmt = n => '₹' + Number(n).toLocaleString('en-IN');

  const affordColor = { "Excellent":"#4caf50","Good":"#4caf50","Moderate":"#ffc107","Stretched":"#ff9800","Critical":"#f44336" };
  const creditColor = { "Excellent":"#4caf50","Good":"#4caf50","Fair":"#ffc107","Poor":"#f44336" };

  document.getElementById('db_affordability').textContent = d.affordability;
  document.getElementById('db_affordability').style.color = affordColor[d.affordability] || '#c9a84c';
  document.getElementById('db_credit_health').textContent = d.credit_health;
  document.getElementById('db_credit_health').style.color = creditColor[d.credit_health] || '#c9a84c';
  document.getElementById('db_foir').textContent          = d.foir + '%';
  document.getElementById('db_foir').style.color          = d.foir < 30 ? '#4caf50' : d.foir < 50 ? '#ffc107' : '#f44336';
  document.getElementById('db_after_foir').textContent    = d.after_loan_foir + '%';
  document.getElementById('db_after_foir').style.color    = d.after_loan_foir < 40 ? '#4caf50' : '#f44336';
  document.getElementById('db_safe_limit').textContent    = fmt(d.safe_emi_limit) + ' / month';
  document.getElementById('db_rate').textContent          = d.rate + '% p.a.';

  const free    = d.income - d.safe_emi_limit;
  const usedEmi = d.existing_emi;
  const remain  = Math.max(0, d.safe_emi_limit - d.existing_emi);

  if (donutChartInstance) donutChartInstance.destroy();
  donutChartInstance = new Chart(document.getElementById('donutChart'), {
    type: 'doughnut',
    data: {
      labels: ['Existing EMIs', 'Available for Loan', 'Free Income'],
      datasets: [{ data: [usedEmi, remain, free], backgroundColor: ['#f44336','#c9a84c','#4caf50'], borderWidth: 0 }]
    },
    options: { plugins: { legend: { labels: { color: '#aaa', font: { size: 11 } } } }, cutout: '65%' }
  });

  if (barChartInstance) barChartInstance.destroy();
  barChartInstance = new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: {
      labels: ['Current EMI', 'After New Loan', 'Safe Limit'],
      datasets: [{ data: [d.existing_emi, d.existing_emi + d.new_emi, d.safe_emi_limit], backgroundColor: ['#c9a84c','#4caf50','#4caf5055'], borderRadius: 6, borderWidth: 0 }]
    },
    options: { plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#aaa' }, grid: { display: false } }, y: { ticks: { color: '#aaa' }, grid: { color: '#ffffff11' } } } }
  });
  showDecision(d);
}

function toggleDashboard() {
  const panel     = document.getElementById('dashboardPanel');
  const isVisible = panel.style.display === 'flex';
  panel.style.display          = isVisible ? 'none' : 'flex';
  panel.style.flexDirection    = 'column';
  document.getElementById('dashboardToggleBtn').textContent = isVisible ? 'Dashboard' : '✕ Dashboard';
}

// ── Recommendation card ──
function showRecommendation(r) {
  if (!r || r.error) {
    if (r?.error) {
      document.getElementById('recommendCard').style.display = 'block';
      document.getElementById('recommendContent').innerHTML  = `⚠️ ${r.error}${r.tip ? '<br>💡 ' + r.tip : ''}`;
    }
    return;
  }
  const fmt = n => '₹' + Number(n).toLocaleString('en-IN');
  document.getElementById('recommendCard').style.display = 'block';
  document.getElementById('recommendContent').innerHTML  = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      <div style="background:#2c2c3e;border-radius:8px;padding:10px;text-align:center;">
        <div style="color:#aaa;font-size:10px;margin-bottom:4px;">MAX LOAN</div>
        <div style="color:#c9a84c;font-weight:700;font-size:15px;">${fmt(r.recommended_amount)}</div>
      </div>
      <div style="background:#2c2c3e;border-radius:8px;padding:10px;text-align:center;">
        <div style="color:#aaa;font-size:10px;margin-bottom:4px;">MONTHLY EMI</div>
        <div style="color:#c9a84c;font-weight:700;font-size:15px;">${fmt(r.recommended_emi)}</div>
      </div>
      <div style="background:#2c2c3e;border-radius:8px;padding:10px;text-align:center;">
        <div style="color:#aaa;font-size:10px;margin-bottom:4px;">INTEREST RATE</div>
        <div style="color:#4caf50;font-weight:700;font-size:15px;">${r.recommended_rate}%</div>
      </div>
      <div style="background:#2c2c3e;border-radius:8px;padding:10px;text-align:center;">
        <div style="color:#aaa;font-size:10px;margin-bottom:4px;">TENURE</div>
        <div style="color:#4caf50;font-weight:700;font-size:15px;">${r.recommended_tenure} yrs</div>
      </div>
    </div>
    <div style="margin-top:10px;display:flex;justify-content:space-between;font-size:12px;color:#aaa;padding:0 4px;">
      <span>FOIR: <strong style="color:#f0f0f0;">${r.foir}%</strong></span>
      <span>Risk: <strong style="color:${r.risk_tier==='Low'?'#4caf50':r.risk_tier==='Medium'?'#ffc107':'#f44336'}">${r.risk_tier}</strong></span>
      <span>Total Interest: <strong style="color:#f0f0f0;">${fmt(r.total_interest)}</strong></span>
    </div>`;
}

// ── Explainer card ──
function showExplanation(e) {
  if (!e) return;
  let html = `<div style="background:#2c2c3e;border-radius:8px;padding:10px;margin-bottom:10px;font-size:13px;">${e.summary}</div>`;
  e.sections.forEach(s => {
    html += `<div style="margin-bottom:8px;">
      <div style="font-weight:700;font-size:12px;color:#f0f0f0;margin-bottom:2px;">${s.label}</div>
      <div style="color:#aaa;font-size:12px;padding-left:4px;">${s.detail}</div>
    </div>`;
  });
  if (e.tips && e.tips.length > 0) {
    html += `<div style="margin-top:10px;background:#2c2c3e;border-radius:8px;padding:10px;">
      <div style="color:#ffc107;font-size:11px;font-weight:700;margin-bottom:6px;text-transform:uppercase;">💡 How to Improve</div>`;
    e.tips.forEach(t => { html += `<div style="color:#aaa;font-size:12px;margin-bottom:4px;">${t}</div>`; });
    html += `</div>`;
  }
  document.getElementById('explainCard').style.display = 'block';
  document.getElementById('explainContent').innerHTML  = html;
}

// ── Returning user delta banner ──
function showDelta(delta) {
  const banner = document.getElementById('returningBanner');

  // ✅ ALWAYS reset first
  banner.style.display = 'none';
  banner.innerHTML = '';

  if (!delta || delta.visits <= 1) return;

  const fmt = n => '₹' + Number(n).toLocaleString('en-IN');

  let html = `👋 Welcome back! Visit #${delta.visits}<br>`;

  if (delta.credit_delta > 0)
    html += `📈 Credit improved by <strong>+${delta.credit_delta}</strong><br>`;
  else if (delta.credit_delta < 0)
    html += `📉 Credit dropped by <strong>${delta.credit_delta}</strong><br>`;

  if (delta.income_delta > 0)
    html += `💰 Income increased by <strong>${fmt(delta.income_delta)}</strong><br>`;
  else if (delta.income_delta < 0)
    html += `⚠️ Income decreased by <strong>${fmt(Math.abs(delta.income_delta))}</strong><br>`;

  banner.innerHTML = html;
  banner.style.display = 'block';
}
// function showDelta(delta) {
//   if (!delta) return;
//   const fmt    = n => '₹' + Number(n).toLocaleString('en-IN');
//   const banner = document.getElementById('returningBanner');
//   let html     = `👋 Welcome back! This is your visit #${delta.visits}.<br>`;
//   if (delta.credit_delta > 0) html += `📈 Credit improved by <strong>+${delta.credit_delta}</strong> since last visit.<br>`;
//   else if (delta.credit_delta < 0) html += `📉 Credit dropped by <strong>${Math.abs(delta.credit_delta)}</strong>`
//   if (delta.income_delta > 0) html += `💰 Income increased by <strong>${fmt(delta.income_delta)}</strong> since last visit.<br>`;
//   else if (delta.income_delta < 0) html += `⚠️ Income decreased by <strong>${fmt(Math.abs(delta.income_delta))}</strong> since last visit.<br>`;
//   if (delta.previous_eligibility) html += `📋 Previous eligibility: <strong>${delta.previous_eligibility}</strong>`;
//   banner.innerHTML     = html;
//   banner.style.display = 'block';

//   // ALSO add to chat
//     const chatWindow = document.getElementById('chatWindow');

//     const deltaMsg = document.createElement('div');
//     deltaMsg.className = 'message bot';

//     deltaMsg.innerHTML = `
//       <div class="sender">System Insight</div>
//       📊 Your financial profile has been updated.
//     `;

//     chatWindow.appendChild(deltaMsg);
// }

// ── EMI Calculator Modal ──
function toggleEMIModal() {
  const modal = document.getElementById('emiModal');
  if (modal.style.display === 'flex') {
    modal.style.display = 'none';
  } else {
    modal.style.display = 'flex';
    document.getElementById('emiResult').style.display = 'none';
    document.getElementById('emiAmount').value = '';
    document.getElementById('emiRate').value   = '';
    document.getElementById('emiTenure').value = '';
  }
}

function calculateEMIModal() {
  const P = parseFloat(document.getElementById('emiAmount').value);
  const r = parseFloat(document.getElementById('emiRate').value);
  const n = parseFloat(document.getElementById('emiTenure').value);
  if (!P || !r || !n)            { alert("Please fill all fields."); return; }
  if (P <= 0 || r <= 0 || n <= 0) { alert("All values must be greater than 0."); return; }

  const monthlyRate    = r / (12 * 100);
  const months         = n * 12;
  const emi            = (P * monthlyRate * Math.pow(1+monthlyRate, months)) / (Math.pow(1+monthlyRate, months) - 1);
  const totalPayment   = emi * months;
  const totalInterest  = totalPayment - P;

  document.getElementById('emiResult').style.display       = 'block';
  document.getElementById('emiResultAmount').textContent   = '₹' + emi.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
  document.getElementById('emiResultDetails').innerHTML    =
    `Total Payment: ₹${totalPayment.toFixed(0).replace(/\d(?=(\d{3})+$)/g,'$&,')}<br>
     Total Interest: ₹${totalInterest.toFixed(0).replace(/\d(?=(\d{3})+$)/g,'$&,')}`;
}

// ── Loan Compare Modal ──
const loanData = [
  { type:"Home Loan",      rate:"8% – 9.5%",  maxAmount:"₹1 Crore+",  tenure:"30 years", bestFor:"Property purchase",  minIncome:25000, minCredit:700 },
  { type:"Personal Loan",  rate:"10% – 24%",  maxAmount:"₹10 Lakhs",  tenure:"5 years",  bestFor:"Emergency/Medical",  minIncome:20000, minCredit:650 },
  { type:"Car Loan",       rate:"7% – 12%",   maxAmount:"₹20 Lakhs",  tenure:"7 years",  bestFor:"Vehicle purchase",   minIncome:20000, minCredit:650 },
  { type:"Education Loan", rate:"8% – 15%",   maxAmount:"₹20 Lakhs",  tenure:"15 years", bestFor:"Higher education",   minIncome:15000, minCredit:600 },
  { type:"Business Loan",  rate:"12% – 24%",  maxAmount:"₹50 Lakhs",  tenure:"10 years", bestFor:"Business expansion", minIncome:30000, minCredit:680 },
];

function toggleCompareModal() {
  const modal = document.getElementById('compareModal');
  if (modal.style.display === 'flex') {
    modal.style.display = 'none';
  } else {
    modal.style.display = 'flex';
    renderCompareTable(lastIncome, lastCredit);
  }
}

function renderCompareTable(userIncome = 0, userCredit = 0) {
  const tbody    = document.getElementById('compareTableBody');
  const subtitle = document.getElementById('compareSubtitle');
  tbody.innerHTML = '';
  const hasProfile = userIncome > 0 && userCredit > 0;
  subtitle.textContent = hasProfile
    ? `Personalized — Income: ₹${Number(userIncome).toLocaleString('en-IN')}, Credit: ${userCredit}`
    : 'General loan options available in India';

  loanData.forEach(loan => {
    const tr = document.createElement('tr');
    let eligibilityText = '—';
    let isRecommended   = false;
    if (hasProfile) {
      const incomeOk = userIncome >= loan.minIncome;
      const creditOk = userCredit >= loan.minCredit;
      if (incomeOk && creditOk)       { eligibilityText = '✅ Eligible';     isRecommended = true; }
      else if (!incomeOk && !creditOk) { eligibilityText = '❌ Not Eligible'; }
      else if (!creditOk)              { eligibilityText = '⚠️ Low Credit';  }
      else                             { eligibilityText = '⚠️ Low Income';  }
    }
    if (isRecommended) tr.classList.add('recommended-row');
    tr.innerHTML = `
      <td>${loan.type}${isRecommended ? '<span class="recommended-badge">✓ Recommended</span>' : ''}</td>
      <td>${loan.rate}</td><td>${loan.maxAmount}</td>
      <td>${loan.tenure}</td><td>${loan.bestFor}</td>
      <td>${eligibilityText}</td>`;
    tbody.appendChild(tr);
  });
}

function switchCompareTab(tab) {
  document.getElementById('panel_general').style.display = tab === 'general' ? 'block' : 'none';
  document.getElementById('panel_banks').style.display   = tab === 'banks'   ? 'block' : 'none';
  document.getElementById('tab_general').className = 'tab-btn' + (tab === 'general' ? ' tab-active' : '');
  document.getElementById('tab_banks').className   = 'tab-btn' + (tab === 'banks'   ? ' tab-active' : '');
  if (tab === 'banks') loadBankRates();
}

async function loadBankRates() {
  const purpose = document.getElementById('purpose').value || 'personal';
  const res     = await fetch('/bank_rates', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ purpose, credit: lastCredit })
  });
  const data  = await res.json();
  if (data.error || !data.rates) return;
  const tbody = document.getElementById('bankRateBody');
  tbody.innerHTML = '';
  data.rates.forEach(r => {
    const tr = document.createElement('tr');
    if (r.recommended) tr.classList.add('recommended-row');
    tr.innerHTML = `
      <td>${r.bank}${r.recommended ? '<span class="recommended-badge">✓ Best Pick</span>' : ''}</td>
      <td style="color:#4caf50;font-weight:700;">${r.min}%</td>
      <td>${r.max}%</td><td>${r.processing}</td>
      <td>${r.recommended ? '⭐ Yes' : '—'}</td>`;
    tbody.appendChild(tr);
  });
}

// ── Simulator Modal ──
function toggleSimulatorModal() {
  const modal  = document.getElementById('simulatorModal');
  const isOpen = modal.style.display === 'flex';
  modal.style.display = isOpen ? 'none' : 'flex';
  if (!isOpen && lastRecommendation && !lastRecommendation.error) {
    document.getElementById('sim_amount').value  = lastRecommendation.recommended_amount;
    document.getElementById('sim_rate').value    = lastRecommendation.recommended_rate;
    document.getElementById('sim_tenure').value  = lastRecommendation.recommended_tenure;
    runSimulator();
  }
}

function runSimulator() {
  clearTimeout(simTimer);
  simTimer = setTimeout(async () => {
    const amount = parseFloat(document.getElementById('sim_amount').value);
    const rate   = parseFloat(document.getElementById('sim_rate').value);
    const tenure = parseFloat(document.getElementById('sim_tenure').value);
    if (!amount || !rate || !tenure) return;

    const r             = rate / (12 * 100);
    const n             = tenure * 12;
    const emi           = (amount * r * Math.pow(1+r, n)) / (Math.pow(1+r, n) - 1);
    const totalInterest = (emi * n) - amount;
    const burden        = lastIncome ? (emi / lastIncome * 100) : 0;
    const verdict       = burden < 30 ? {t:"✅ Safe", c:"#4caf50"} :
                          burden < 40 ? {t:"⚠️ Moderate", c:"#ffc107"} :
                          burden < 55 ? {t:"⚠️ Risky", c:"#ff9800"} :
                                        {t:"❌ Avoid", c:"#f44336"};
    const fmt = v => '₹' + Number(Math.round(v)).toLocaleString('en-IN');

    const liveEl = document.getElementById('sim_live');
    liveEl.style.display = 'grid';
    document.getElementById('sim_emi_val').textContent      = fmt(emi);
    document.getElementById('sim_burden_val').textContent   = burden.toFixed(1) + '%';
    document.getElementById('sim_burden_val').style.color   = verdict.c;
    document.getElementById('sim_interest_val').textContent = fmt(totalInterest);
    document.getElementById('sim_verdict_val').textContent  = verdict.t;
    document.getElementById('sim_verdict_val').style.color  = verdict.c;

    if (!lastIncome || !lastCredit) {
      document.getElementById('sim_empty').textContent = '⚠️ Please analyze your profile first.';
      return;
    }

    const res  = await fetch('/simulate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ income: lastIncome, credit: lastCredit, amount, rate, tenure })
    });
    const data = await res.json();
    if (data.error || !data.scenarios) return;

    document.getElementById('sim_empty').style.display      = 'none';
    document.getElementById('sim_table_wrap').style.display = 'block';
    const tbody = document.getElementById('sim_table_body');
    tbody.innerHTML = '';
    data.scenarios.forEach(s => {
      const tr = document.createElement('tr');
      if (s.is_base) tr.style.background = '#1a3a2a';
      tr.style.borderBottom = '1px solid #c9a84c22';
      tr.innerHTML = `
        <td style="padding:10px;color:#f0f0f0;">${fmt(s.amount)}${s.is_base?'<span style="background:#c9a84c;color:#1a1a2e;font-size:10px;padding:2px 6px;border-radius:8px;margin-left:6px;font-weight:700;">BASE</span>':''}</td>
        <td style="padding:10px;color:#f0f0f0;">${s.tenure} yrs</td>
        <td style="padding:10px;color:#f0f0f0;">${s.rate}%</td>
        <td style="padding:10px;color:#c9a84c;font-weight:700;">${fmt(s.emi)}</td>
        <td style="padding:10px;color:${s.verdict_color};">${s.burden}%</td>
        <td style="padding:10px;color:${s.verdict_color};font-weight:700;">${s.verdict}</td>`;
      tbody.appendChild(tr);
    });
  }, 400);
}

function showDecision(d) {
  const el = document.getElementById('decisionBanner');

  let msg = '';

  if (d.after_loan_foir > 50) {
    msg = '🔴 Not Recommended: Your EMI burden is too high.';
  } 
  else if (d.after_loan_foir > 40) {
    msg = '🟡 Risky: Loan may strain your finances.';
  } 
  else {
    msg = '🟢 Recommended: You can safely take this loan.';
  }

  el.innerHTML = msg;
  el.style.display = 'block';
}


// ── Business Advisor ─────────────────────────────────────────────────────────

const bizPrefs = { budget: null, city: null, risk: null };

  function isBizQuery(msg) {
  const triggers = [
    "business idea", "business ideas", "small business", "profitable business",
    "start a business", "suggest business", "recommend business",
    "startup idea", "low investment business", "high profit business",
    "which business", "what business", "business to start"
  ];
  return triggers.some(t => msg.toLowerCase().includes(t));
};


function renderBizPrefsUI(userMessage) {
  const wrap = document.createElement("div");
  wrap.className = "business-advisor-wrap";
  wrap.innerHTML = `
    <div style="font-size:14px;font-weight:600;margin-bottom:12px;color:#c9a84c;">
      🏢 Let me personalize business ideas for you. Pick your preferences:
    </div>
    <div class="business-pref-bar">
      <div class="pref-group">
        <div class="pref-label">💰 Budget</div>
        <div class="pref-chips" id="chips-budget">
          ${["Under ₹50K","₹50K–2L","₹2L–5L","₹5L+"].map(b =>
            `<div class="pref-chip" onclick="selectChip('budget','${b}',this)">${b}</div>`
          ).join("")}
        </div>
      </div>
      <div class="pref-group">
        <div class="pref-label">📍 Location Type</div>
        <div class="pref-chips" id="chips-city">
          ${["Metro City","Small City","Town/Village","Online Only"].map(c =>
            `<div class="pref-chip" onclick="selectChip('city','${c}',this)">${c}</div>`
          ).join("")}
        </div>
      </div>
      <div class="pref-group">
        <div class="pref-label">⚖️ Risk Appetite</div>
        <div class="pref-chips" id="chips-risk">
          ${["Low Risk","Moderate","High Risk"].map(r =>
            `<div class="pref-chip" onclick="selectChip('risk','${r}',this)">${r}</div>`
          ).join("")}
        </div>
      </div>
    </div>
    <button onclick="submitBizPrefs('${userMessage.replace(/'/g,"\\'")}', this.closest('.business-advisor-wrap'))"
      class="download-btn">
      Show Business Ideas →
    </button>`;

  const chatWindow = document.getElementById('chatWindow');
  const botDiv = document.createElement('div');
  botDiv.className = 'message bot';
  botDiv.innerHTML = `<div class="sender">LoanAdvisor AI</div>`;
  botDiv.appendChild(wrap);
  chatWindow.appendChild(botDiv);
  scrollToBottom();
}

function selectChip(group, value, el) {
  document.querySelectorAll(`#chips-${group} .pref-chip`).forEach(c => c.classList.remove("active"));
  el.classList.add("active");
  bizPrefs[group] = value;
}

async function submitBizPrefs(userMessage, wrapEl) {
  // Replace pref UI with loading spinner
  wrapEl.innerHTML = `<div class="biz-loading"><div class="biz-spinner"></div>Finding best business ideas for you…</div>`;

  try {
    const res  = await fetch("/business_advice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage, preferences: bizPrefs })
    });
    const data = await res.json();

    if (data.error) {
      wrapEl.innerHTML = `<div style="color:red">⚠️ ${data.error}</div>`;
      return;
    }
    wrapEl.innerHTML = renderBizCards(data);

  } catch (err) {
    wrapEl.innerHTML = `<div style="color:red">⚠️ Could not load business ideas. Try again.</div>`;
  }
}

function renderBizCards(data) {
  const businesses = data.businesses || [];
  const summary    = data.summary    || {};
  const note       = data.advisor_note || "";

  const cards = businesses.map(b => `
    <div class="biz-card">
      <div class="biz-card-header">
        <div>
          <div class="biz-name">${b.business_name}</div>
          <div class="biz-tag">${b.tagline}</div>
        </div>
        <span class="risk-badge risk-${b.risk_level}">${b.risk_level} Risk</span>
      </div>
      <div class="biz-meta">
        <div class="biz-meta-item">💰 <span>${b.investment_range}</span></div>
        <div class="biz-meta-item">📈 <span>${b.monthly_profit_range}</span></div>
        <div class="biz-meta-item">⏱ <span>${b.time_to_profit}</span></div>
      </div>
      <div class="biz-why">${b.why_profitable}</div>
      <div class="biz-tip">🏦 <strong>Loan Tip:</strong> ${b.loan_approval_reason}</div>
    </div>`).join("");

  const summaryHTML = `
    <div class="biz-summary">
      <div class="biz-summary-box quick">
        <div class="s-icon">🚀</div>
        <div class="s-title">Best for Quick Profit</div>
        <div class="s-text">${summary.best_for_quick_profit}</div>
      </div>
      <div class="biz-summary-box long">
        <div class="s-icon">📈</div>
        <div class="s-title">Best for Long-Term</div>
        <div class="s-text">${summary.best_for_long_term}</div>
      </div>
      <div class="biz-summary-box safe">
        <div class="s-icon">✅</div>
        <div class="s-title">Safest for Loan</div>
        <div class="s-text">${summary.safest_for_loan}</div>
      </div>
    </div>`;

  const followups = `
    <div class="biz-followup">
      <button onclick="sendFollowup('How to apply for loan for the first business?')">Loan process</button>
      <button onclick="sendFollowup('What government schemes apply for these businesses?')">Govt schemes</button>
      <button onclick="sendFollowup('What documents do I need for business loan?')">Documents needed</button>
    </div>`;

  return `
    <div class="business-advisor-wrap">
      <div style="font-weight:700;font-size:15px;margin-bottom:12px;">
        💼 Here are 3 business ideas tailored for you:
      </div>
      <div class="biz-cards-grid">${cards}</div>
      ${summaryHTML}
      <div class="biz-note">💡 <strong>Advisor Note:</strong> ${note}</div>
      ${followups}
    </div>`;
}

function sendFollowup(text) {
  // Put text in your chat input and submit
  const input = document.getElementById("userInput"); // change to your input's actual ID
  if (input) {
    input.value = text;
       sendMessage(text);
    // input.dispatchEvent(new Event("input"));
    // // If you have a send button:
    // document.getElementById("sendBtn").click(); // change to your send button's actual ID
  }
}


// ── Education Advisor ────────────────────────────────────────────────────────

const eduPrefs = { budget: null, field: null, goal: null };

function isEduQuery(msg) {
  const triggers = [
    "education loan", "course", "college", "degree", "study",
    "university", "fees", "tuition", "skill course", "certification",
    "diploma", "mba", "engineering", "btech", "which course",
    "what course", "course suggestion", "higher education",
    "career course", "best course", "career advice", "abroad study"
  ];
  return triggers.some(t => msg.toLowerCase().includes(t));
}

function renderEduPrefsUI(userMessage) {
  const wrap = document.createElement("div");
  wrap.className = "business-advisor-wrap";
  wrap.innerHTML = `
    <div style="font-size:14px;font-weight:600;margin-bottom:10px;color:#f0f0f0;">
      🎓 Let me find the best courses for your education loan. Pick your preferences:
    </div>
    <div class="business-pref-bar">
      <div class="pref-group">
        <div class="pref-label">Loan Budget</div>
        <div class="pref-chips" id="edu-chips-budget">
          ${["Under ₹2L","₹2L–5L","₹5L–10L","₹10L+"].map(b =>
            `<div class="pref-chip" onclick="selectEduChip('budget','${b}',this)">${b}</div>`
          ).join("")}
        </div>
      </div>
      <div class="pref-group">
        <div class="pref-label">Field of Interest</div>
        <div class="pref-chips" id="edu-chips-field">
          ${["Technology","Business","Medical","Arts & Design","Any Field"].map(f =>
            `<div class="pref-chip" onclick="selectEduChip('field','${f}',this)">${f}</div>`
          ).join("")}
        </div>
      </div>
      <div class="pref-group">
        <div class="pref-label">Career Goal</div>
        <div class="pref-chips" id="edu-chips-goal">
          ${["High Salary","Quick Job","Own Business","Abroad Opportunities"].map(g =>
            `<div class="pref-chip" onclick="selectEduChip('goal','${g}',this)">${g}</div>`
          ).join("")}
        </div>
      </div>
    </div>
    <button onclick="submitEduPrefs('${userMessage.replace(/'/g,"\\'")}', this.closest('.business-advisor-wrap'))"
      style="padding:8px 20px;background:#c9a84c;color:#1a1a2e;border:none;border-radius:8px;
             font-size:13px;cursor:pointer;font-weight:700;margin-top:4px;">
      Show Course Recommendations →
    </button>`;

  const chatWindow = document.getElementById('chatWindow');
  const botDiv = document.createElement('div');
  botDiv.className = 'message bot';
  botDiv.innerHTML = `<div class="sender">LoanAdvisor AI</div>`;
  botDiv.appendChild(wrap);
  chatWindow.appendChild(botDiv);
  scrollToBottom();
}

function selectEduChip(group, value, el) {
  document.querySelectorAll(`#edu-chips-${group} .pref-chip`).forEach(c => c.classList.remove("active"));
  el.classList.add("active");
  eduPrefs[group] = value;
}

async function submitEduPrefs(userMessage, wrapEl) {
  wrapEl.innerHTML = `<div class="biz-loading"><div class="biz-spinner"></div>Finding best courses for your education loan…</div>`;
  try {
    const res  = await fetch("/education_advice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage, preferences: eduPrefs })
    });
    const data = await res.json();
    if (data.error) {
      wrapEl.innerHTML = `<div style="color:#f44336">⚠️ ${data.error}</div>`;
      return;
    }
    wrapEl.outerHTML = renderEduCards(data);
  } catch (err) {
    wrapEl.innerHTML = `<div style="color:#f44336">⚠️ Could not load recommendations. Try again.</div>`;
  }
}

function renderEduCards(data) {
  const courses = data.courses || [];
  const summary = data.summary || {};
  const note    = data.advisor_note || "";

  const cards = courses.map(c => `
    <div class="biz-card">
      <div class="biz-card-header">
        <div>
          <div class="biz-name">${c.course_name}</div>
          <div class="biz-tag">${c.institution} · ${c.tagline}</div>
        </div>
        <span class="risk-badge risk-${c.difficulty_level}">${c.difficulty_level}</span>
      </div>
      <div class="biz-meta">
        <div class="biz-meta-item">💰 <span>${c.total_fees}</span></div>
        <div class="biz-meta-item">📈 <span>${c.avg_starting_salary} avg</span></div>
        <div class="biz-meta-item">⏱ <span>${c.duration}</span></div>
      </div>
      <div class="biz-why">${c.why_worth_it}</div>
      <div class="biz-tip">🏦 <strong>Loan Tip:</strong> ${c.loan_approval_reason}</div>
    </div>`).join("");

  const summaryHTML = `
    <div class="biz-summary">
      <div class="biz-summary-box quick">
        <div class="s-icon">🚀</div>
        <div class="s-title">Best ROI</div>
        <div class="s-text">${summary.best_roi || "—"}</div>
      </div>
      <div class="biz-summary-box long">
        <div class="s-icon">⚡</div>
        <div class="s-title">Fastest Career</div>
        <div class="s-text">${summary.fastest_career || "—"}</div>
      </div>
      <div class="biz-summary-box safe">
        <div class="s-icon">✅</div>
        <div class="s-title">Easiest Loan Approval</div>
        <div class="s-text">${summary.easiest_loan_approval || "—"}</div>
      </div>
    </div>`;

  const followups = `
    <div class="biz-followup">
      <button onclick="sendFollowup('Tell me more about course #1')">More on #1</button>
      <button onclick="sendFollowup('How to apply for education loan?')">Loan process</button>
      <button onclick="sendFollowup('What scholarships are available for these courses?')">Scholarships</button>
      <button onclick="sendFollowup('What documents needed for education loan?')">Documents</button>
    </div>`;

  return `
    <div class="business-advisor-wrap">
      <div style="font-weight:700;font-size:14px;margin-bottom:12px;color:#f0f0f0;">
        🎓 Here are 3 course recommendations for your education loan:
      </div>
      <div class="biz-cards-grid">${cards}</div>
      ${summaryHTML}
      <div class="biz-note">💡 <strong>Advisor Note:</strong> ${note}</div>
      ${followups}
    </div>`;
}
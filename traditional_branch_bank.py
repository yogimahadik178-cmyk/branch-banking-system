import json
import os
import random
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB_FILE = "branch_database.json"
AUTHORIZED_TELLERS = {"TELLER_01", "TELLER_02", "MANAGER_01"}


def load_ledger():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_ledger(ledger):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)


branch_ledger = load_ledger()

# १. शाखा काऊंटर पोर्टल (Branch Teller Portal + Net Banking Activation + Passbook)
BRANCH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Core Branch Banking System</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { margin: 0; background: #f1f5f9; color: #1e293b; }
        .navbar { background: #0f294a; color: white; padding: 14px 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .navbar h1 { margin: 0; font-size: 20px; }
        .nav-right { display: flex; align-items: center; gap: 12px; }
        .nb-btn { background: #16a34a; color: white; text-decoration: none; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 13px; }
        .nb-btn:hover { background: #15803d; }
        .navbar select { background: #1e4273; color: white; border: 1px solid #60a5fa; padding: 8px 12px; border-radius: 6px; font-weight: bold; }
        #toast { position: fixed; top: 20px; right: 20px; padding: 14px 22px; border-radius: 8px; color: white; font-weight: bold; display: none; z-index: 9999; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .container { max-width: 1280px; margin: 25px auto; padding: 0 20px; display: grid; grid-template-columns: 400px 1fr; gap: 24px; }
        @media (max-width: 900px) { .container { grid-template-columns: 1fr; } }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); overflow: hidden; border: 1px solid #e2e8f0; }
        .tabs { display: flex; background: #e2e8f0; flex-wrap: wrap; }
        .tab-btn { flex: 1; padding: 12px 5px; border: none; background: transparent; font-weight: bold; font-size: 12px; cursor: pointer; color: #475569; border-bottom: 3px solid transparent; }
        .tab-btn.active { background: white; color: #0f294a; border-bottom: 3px solid #0284c7; }
        .tab-content { padding: 20px; display: none; }
        .tab-content.active { display: block; }
        label { display: block; font-size: 13px; font-weight: 600; margin: 12px 0 5px; }
        input { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; }
        .btn { width: 100%; padding: 12px; margin-top: 15px; border: none; border-radius: 6px; color: white; font-weight: bold; font-size: 14px; cursor: pointer; }
        .btn-blue { background: #0f294a; } .btn-blue:hover { background: #1e4273; }
        .btn-green { background: #15803d; } .btn-green:hover { background: #166534; }
        .btn-red { background: #b91c1c; } .btn-red:hover { background: #991b1b; }
        .btn-sky { background: #0284c7; } .btn-sky:hover { background: #0369a1; }
        .pb-header { background: linear-gradient(135deg, #0f294a, #1e4273); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .bal-card { background: rgba(255,255,255,0.12); padding: 10px 18px; border-radius: 8px; text-align: right; }
        .bal-card strong { font-size: 24px; color: #4ade80; display: block; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { background: #f8fafc; padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0; color: #475569; }
        td { padding: 12px; border-bottom: 1px solid #f1f5f9; }
        .cr { color: #15803d; font-weight: bold; } .dr { color: #b91c1c; font-weight: bold; }
        .chip { display: inline-block; background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; padding: 8px 14px; border-radius: 8px; margin: 5px; cursor: pointer; font-weight: bold; font-size: 13px; }
        .chip:hover { background: #bae6fd; }
    </style>
</head>
<body>

<div id="toast"></div>

<div class="navbar">
    <h1>🏛️ CORE BRANCH BANKING SYSTEM</h1>
    <div class="nav-right">
        <a href="/netbanking" target="_blank" class="nb-btn">🌐 Open Net Banking Portal ↗</a>
        <select id="tellerId">
            <option value="TELLER_01">Counter 1: TELLER_01</option>
            <option value="TELLER_02">Counter 2: TELLER_02</option>
            <option value="MANAGER_01">Manager: MANAGER_01</option>
        </select>
    </div>
</div>

<div class="container">
    <div class="card" style="height: fit-content;">
        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('open', this)">+ New A/C</button>
            <button class="tab-btn" onclick="showTab('deposit', this)">Deposit</button>
            <button class="tab-btn" onclick="showTab('withdraw', this)">Withdraw</button>
            <button class="tab-btn" onclick="showTab('netbank', this)">🌐 NetBank</button>
            <button class="tab-btn" onclick="showTab('passbook', this)">Passbook</button>
        </div>

        <!-- 1. Open Account -->
        <div id="tab-open" class="tab-content active">
            <h3 style="margin:0 0 10px; color:#0f294a;">नवीन खाते उघडा</h3>
            <label>ग्राहकाचे नाव (Name)</label>
            <input type="text" id="openName" placeholder="उदा. Yogiraj">
            <label>ओळखपत्र क्रमांक (Gov ID)</label>
            <input type="text" id="openGovId" placeholder="उदा. 707847">
            <label>सुरुवातीची रक्कम (Min ₹500)</label>
            <input type="number" id="openDeposit" value="5000">
            <button class="btn btn-blue" onclick="openAccount()">खाते उघडा (Create Account)</button>
        </div>

        <!-- 2. Deposit -->
        <div id="tab-deposit" class="tab-content">
            <h3 style="margin:0 0 10px; color:#15803d;">रोख पैसे जमा करा</h3>
            <label>खाते क्रमांक (Account Number)</label>
            <input type="text" id="depAccNo" placeholder="BR-XXXXXX">
            <label>जमा रक्कम (Amount ₹)</label>
            <input type="number" id="depAmount" placeholder="उदा. 2000">
            <button class="btn btn-green" onclick="depositCash()">पैसे जमा करा (Deposit)</button>
        </div>

        <!-- 3. Withdraw -->
        <div id="tab-withdraw" class="tab-content">
            <h3 style="margin:0 0 10px; color:#b91c1c;">रोख पैसे काढा</h3>
            <label>खाते क्रमांक (Account Number)</label>
            <input type="text" id="withAccNo" placeholder="BR-XXXXXX">
            <label>ओळखपत्र तपासा (Verify Gov ID)</label>
            <input type="text" id="withGovId" placeholder="खाते उघडताना दिलेला ID">
            <label>काढायची रक्कम (Amount ₹)</label>
            <input type="number" id="withAmount" placeholder="उदा. 1000">
            <button class="btn btn-red" onclick="withdrawCash()">पैसे काढा (Withdraw)</button>
        </div>

        <!-- 4. Activate Net Banking -->
        <div id="tab-netbank" class="tab-content">
            <h3 style="margin:0 0 10px; color:#0284c7;">🌐 Net Banking चालू करा</h3>
            <label>खाते क्रमांक (Account Number)</label>
            <input type="text" id="nbAccNo" placeholder="BR-XXXXXX">
            <label>ओळखपत्र तपासा (Verify Gov ID)</label>
            <input type="text" id="nbGovId" placeholder="खाते उघडताना दिलेला ID">
            <label>नवीन Net Banking पासवर्ड सेट करा</label>
            <input type="password" id="nbPassword" placeholder="उदा. pass123">
            <button class="btn btn-sky" onclick="enableNetBanking()">Net Banking Activate करा</button>
        </div>

        <!-- 5. Passbook -->
        <div id="tab-passbook" class="tab-content">
            <h3 style="margin:0 0 10px; color:#0f294a;">पासबुक उघडा (Open Passbook)</h3>
            <label>खाते क्रमांक टाका (Account Number)</label>
            <input type="text" id="passAccNo" placeholder="उदा. BR-383823">
            <button class="btn btn-blue" onclick="openPassbook()">पासबुक बघा (View Passbook)</button>
        </div>
    </div>

    <div style="display:flex; flex-direction:column; gap:20px;">
        <div class="card">
            <div class="pb-header">
                <div>
                    <h2 id="pbName" style="margin:0 0 5px;">पासबुक निवडलेले नाही</h2>
                    <p id="pbDetails" style="margin:0; font-size:13px; color:#cbd5e1;">नवीन खाते उघडा किंवा खालील खात्यावर क्लिक करा</p>
                </div>
                <div style="display:flex; align-items:center; gap:12px;">
                    <div class="bal-card">
                        <span style="font-size:11px; color:#93c5fd;">AVAILABLE BALANCE</span>
                        <strong id="pbBalance">₹ 0.00</strong>
                    </div>
                    <button id="printBtn" onclick="window.print()" style="display:none; padding:10px 14px; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">🖨️ Print</button>
                </div>
            </div>
            <table>
                <thead>
                    <tr><th>Date & Time</th><th>Details</th><th>Type</th><th>Amount</th><th>Balance</th></tr>
                </thead>
                <tbody id="pbRows">
                    <tr><td colspan="5" style="text-align:center; padding:30px; color:#64748b;">पासबुक नोंदी येथे दिसतील...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card" style="padding:18px;">
            <strong style="color:#0f294a;">📂 शाखेतील सर्व खातेदार (खात्यावर क्लिक करून पासबुक उघडा):</strong>
            <div id="accountsContainer" style="margin-top:10px; color:#64748b;">लोड होत आहे...</div>
        </div>
    </div>
</div>

<script>
    function toast(msg, err = false) {
        const t = document.getElementById('toast');
        t.textContent = (err ? '❌ ' : '✅ ') + msg;
        t.style.background = err ? '#dc2626' : '#15803d';
        t.style.display = 'block';
        setTimeout(() => t.style.display = 'none', 4000);
    }

    function showTab(name, btn) {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + name).classList.add('active');
    }

    function displayPassbook(acc) {
        const nbText = acc.netBankingEnabled ? '🟢 Net Banking ACTIVE' : '🔴 Net Banking OFF';
        document.getElementById('pbName').textContent = acc.holderName + ' (' + acc.accountNumber + ')';
        document.getElementById('pbDetails').textContent = 'Gov ID: ' + acc.govId + ' | ' + nbText;
        document.getElementById('pbBalance').textContent = '₹ ' + Number(acc.balance).toFixed(2);
        document.getElementById('printBtn').style.display = 'inline-block';

        ['depAccNo', 'withAccNo', 'passAccNo', 'nbAccNo'].forEach(id => {
            document.getElementById(id).value = acc.accountNumber;
        });

        const tbody = document.getElementById('pbRows');
        tbody.innerHTML = '';
        const txs = acc.transactions || [];
        txs.slice().reverse().forEach(tx => {
            const isCr = tx.type === 'CREDIT';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${tx.time}</td>
                <td>${tx.desc}</td>
                <td class="${isCr ? 'cr' : 'dr'}">${tx.type}</td>
                <td class="${isCr ? 'cr' : 'dr'}">${isCr ? '+' : '-'} ₹${Number(tx.amount).toFixed(2)}</td>
                <td><strong>₹${Number(tx.balance).toFixed(2)}</strong></td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function callApi(url, method) {
        try {
            const res = await fetch(url, { method: method });
            const data = await res.json();
            if (!res.ok) {
                toast(data.error || 'Error occurred', true);
                return;
            }
            if (data.message) toast(data.message, false);
            if (data.account) {
                displayPassbook(data.account);
            } else if (data.accountNumber) {
                displayPassbook(data);
                toast('पासबुक उघडले: ' + data.accountNumber, false);
            }
            loadAccounts();
        } catch (e) {
            toast('Server शी संपर्क होऊ शकला नाही!', true);
        }
    }

    function openAccount() {
        const teller = document.getElementById('tellerId').value;
        const name = encodeURIComponent(document.getElementById('openName').value.trim());
        const govId = encodeURIComponent(document.getElementById('openGovId').value.trim());
        const deposit = document.getElementById('openDeposit').value;
        callApi(`/api/branch/open-account?tellerId=${teller}&name=${name}&govId=${govId}&initialDeposit=${deposit}`, 'POST');
    }

    function depositCash() {
        const teller = document.getElementById('tellerId').value;
        const acc = encodeURIComponent(document.getElementById('depAccNo').value.trim());
        const amount = document.getElementById('depAmount').value;
        callApi(`/api/branch/deposit?tellerId=${teller}&accNo=${acc}&amount=${amount}`, 'POST');
    }

    function withdrawCash() {
        const teller = document.getElementById('tellerId').value;
        const acc = encodeURIComponent(document.getElementById('withAccNo').value.trim());
        const govId = encodeURIComponent(document.getElementById('withGovId').value.trim());
        const amount = document.getElementById('withAmount').value;
        callApi(`/api/branch/withdraw?tellerId=${teller}&accNo=${acc}&govId=${govId}&amount=${amount}`, 'POST');
    }

    function enableNetBanking() {
        const teller = document.getElementById('tellerId').value;
        const acc = encodeURIComponent(document.getElementById('nbAccNo').value.trim());
        const govId = encodeURIComponent(document.getElementById('nbGovId').value.trim());
        const pwd = encodeURIComponent(document.getElementById('nbPassword').value.trim());
        callApi(`/api/branch/enable-netbanking?tellerId=${teller}&accNo=${acc}&govId=${govId}&password=${pwd}`, 'POST');
    }

    function openPassbook(accOverride) {
        const teller = document.getElementById('tellerId').value;
        const rawAcc = accOverride ? accOverride : document.getElementById('passAccNo').value;
        const acc = encodeURIComponent(rawAcc.trim());
        if (!acc) {
            toast('कृपया खाते क्रमांक टाका!', true);
            return;
        }
        callApi(`/api/branch/passbook?tellerId=${teller}&accNo=${acc}`, 'GET');
    }

    async function loadAccounts() {
        try {
            const res = await fetch('/api/branch/accounts');
            const list = await res.json();
            const box = document.getElementById('accountsContainer');
            if (!list.length) {
                box.innerHTML = 'सध्या एकही खाते नाही. डाव्या बाजूला नवीन खाते उघडा.';
                return;
            }
            box.innerHTML = list.map(a =>
                `<span class="chip" onclick="openPassbook('${a.accountNumber}')">${a.netBankingEnabled ? '🌐' : '🏦'} ${a.holderName} (${a.accountNumber}) — ₹${a.balance}</span>`
            ).join('');
        } catch (e) {}
    }

    window.onload = loadAccounts;
</script>
</body>
</html>
"""

# २. ग्राहकासाठी Net Banking पोर्टल
NETBANKING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer Net Banking Portal</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { margin: 0; background: #0f172a; color: #1e293b; min-height: 100vh; }
        .top-bar { background: #1e293b; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; }
        .top-bar h2 { margin: 0; font-size: 18px; color: #38bdf8; }
        .top-bar a { color: #94a3b8; text-decoration: none; font-size: 13px; }
        .login-box { max-width: 400px; margin: 70px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
        label { display: block; font-size: 13px; font-weight: 600; margin: 12px 0 5px; }
        input { width: 100%; padding: 11px; border: 1px solid #cbd5e1; border-radius: 7px; font-size: 14px; }
        button { width: 100%; padding: 12px; margin-top: 18px; background: #0284c7; color: white; border: none; border-radius: 7px; font-weight: 700; font-size: 15px; cursor: pointer; }
        .dashboard { max-width: 1000px; margin: 30px auto; padding: 0 20px; display: none; }
        .dash-grid { display: grid; grid-template-columns: 340px 1fr; gap: 20px; }
        @media (max-width: 800px) { .dash-grid { grid-template-columns: 1fr; } }
        .card { background: white; padding: 22px; border-radius: 12px; }
        .bal-banner { background: linear-gradient(135deg, #0284c7, #0f294a); color: white; padding: 22px; border-radius: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
        th, td { padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }
        .cr { color: #15803d; font-weight: bold; } .dr { color: #dc2626; font-weight: bold; }
    </style>
</head>
<body>
<div class="top-bar">
    <h2>🌐 ONLINE NET BANKING PORTAL</h2>
    <a href="/">← Back to Branch Counter</a>
</div>

<div class="login-box" id="loginScreen">
    <h3 style="margin-top:0; text-align:center; color:#0f294a;">ग्राहक लॉगिन (Customer Login)</h3>
    <label>खाते क्रमांक (Account Number)</label>
    <input type="text" id="loginAcc" placeholder="उदा. BR-383823">
    <label>Net Banking पासवर्ड</label>
    <input type="password" id="loginPwd" placeholder="पासवर्ड टाका">
    <button onclick="login()">लॉगिन करा (Login)</button>
    <div id="msg" style="text-align:center; margin-top:12px; font-weight:bold; font-size:13px;"></div>
</div>

<div class="dashboard" id="dashScreen">
    <div class="bal-banner">
        <div>
            <h2 id="custName" style="margin:0;">Welcome</h2>
            <p id="custAcc" style="margin:5px 0 0; color:#bae6fd; font-size:13px;"></p>
        </div>
        <div style="text-align:right;">
            <span style="font-size:12px; color:#bae6fd;">AVAILABLE BALANCE</span>
            <h1 id="custBal" style="margin:4px 0 0; color:#4ade80;">₹ 0.00</h1>
        </div>
    </div>

    <div class="dash-grid">
        <div class="card">
            <h3 style="margin-top:0; color:#0f294a;">💸 पैसे ट्रान्सफर करा (Fund Transfer)</h3>
            <label>समोरच्या व्यक्तीचा खाते क्रमांक (To Account)</label>
            <input type="text" id="toAcc" placeholder="BR-XXXXXX">
            <label>रक्कम (Amount ₹)</label>
            <input type="number" id="trAmount" placeholder="उदा. 500">
            <label>तुमचा पासवर्ड कन्फर्म करा</label>
            <input type="password" id="trPwd" placeholder="पासवर्ड टाका">
            <button onclick="transferMoney()" style="background:#16a34a;">पैसे पाठवा (Transfer Now)</button>
            <div id="trMsg" style="margin-top:10px; font-size:13px; font-weight:bold;"></div>
        </div>

        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0; color:#0f294a;">📄 ऑनलाइन स्टेटमेंट</h3>
                <button onclick="location.reload()" style="width:auto; margin:0; padding:6px 12px; background:#dc2626; font-size:12px;">Logout</button>
            </div>
            <table>
                <thead><tr><th>Date</th><th>Details</th><th>Type</th><th>Amount</th><th>Balance</th></tr></thead>
                <tbody id="stmtRows"></tbody>
            </table>
        </div>
    </div>
</div>

<script>
    let currentAcc = '';
    async function login() {
        const acc = document.getElementById('loginAcc').value.trim();
        const pwd = document.getElementById('loginPwd').value.trim();
        const res = await fetch(`/api/netbanking/login?accNo=${encodeURIComponent(acc)}&password=${encodeURIComponent(pwd)}`, { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
            document.getElementById('msg').style.color = '#dc2626';
            document.getElementById('msg').textContent = '❌ ' + data.error;
            return;
        }
        currentAcc = acc;
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('dashScreen').style.display = 'block';
        updateDash(data.account);
    }

    function updateDash(acc) {
        document.getElementById('custName').textContent = 'नमस्कार, ' + acc.holderName;
        document.getElementById('custAcc').textContent = 'Account No: ' + acc.accountNumber;
        document.getElementById('custBal').textContent = '₹ ' + Number(acc.balance).toFixed(2);
        document.getElementById('stmtRows').innerHTML = acc.transactions.slice().reverse().map(tx => {
            const isCr = tx.type === 'CREDIT';
            return `<tr><td>${tx.time}</td><td>${tx.desc}</td><td class="${isCr ? 'cr' : 'dr'}">${tx.type}</td><td class="${isCr ? 'cr' : 'dr'}">${isCr ? '+' : '-'}₹${tx.amount}</td><td><strong>₹${tx.balance}</strong></td></tr>`;
        }).join('');
    }

    async function transferMoney() {
        const toAcc = document.getElementById('toAcc').value.trim();
        const amount = document.getElementById('trAmount').value;
        const pwd = document.getElementById('trPwd').value.trim();
        const res = await fetch(`/api/netbanking/transfer?fromAcc=${encodeURIComponent(currentAcc)}&toAcc=${encodeURIComponent(toAcc)}&amount=${amount}&password=${encodeURIComponent(pwd)}`, { method: 'POST' });
        const data = await res.json();
        const msgBox = document.getElementById('trMsg');
        if (!res.ok) { msgBox.style.color = '#dc2626'; msgBox.textContent = '❌ ' + data.error; return; }
        msgBox.style.color = '#15803d'; msgBox.textContent = '✅ ' + data.message;
        updateDash(data.account);
    }
</script>
</body>
</html>
"""


class BankHandler(BaseHTTPRequestHandler):
    def _send_html(self, html):
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, code, payload):
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _params(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        return parsed.path, {k: v[0] for k, v in qs.items()}

    def do_GET(self):
        path, params = self._params()
        if path in ("/", "/index.html"):
            return self._send_html(BRANCH_HTML)
        if path == "/netbanking":
            return self._send_html(NETBANKING_HTML)

        if path == "/api/branch/accounts":
            items = [
                {
                    "accountNumber": k,
                    "holderName": v["holderName"],
                    "balance": v["balance"],
                    "netBankingEnabled": v.get("netBankingEnabled", False),
                }
                for k, v in branch_ledger.items()
            ]
            return self._send_json(200, items)

        if path == "/api/branch/passbook":
            if params.get("tellerId") not in AUTHORIZED_TELLERS:
                return self._send_json(403, {"error": "Unauthorized Teller"})
            acc_no = params.get("accNo", "").strip().upper()
            acc = branch_ledger.get(acc_no)
            if not acc:
                return self._send_json(404, {"error": f"खाते {acc_no} सापडले नाही!"})
            return self._send_json(200, acc)

        return self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        path, params = self._params()
        now = datetime.now().strftime("%d-%b-%Y %I:%M %p")

        if path == "/api/netbanking/login":
            acc_no = params.get("accNo", "").strip().upper()
            pwd = params.get("password", "").strip()
            acc = branch_ledger.get(acc_no)
            if not acc:
                return self._send_json(404, {"error": "खाते क्रमांक सापडला नाही!"})
            if not acc.get("netBankingEnabled"):
                return self._send_json(403, {"error": "या खात्यासाठी Net Banking चालू नाही! आधी 🌐 NetBank टॅबमधून Activate करा."})
            if acc.get("netBankingPassword") != pwd:
                return self._send_json(401, {"error": "चुकीचा पासवर्ड!"})
            return self._send_json(200, {"message": "Login Successful", "account": acc})

        if path == "/api/netbanking/transfer":
            from_no = params.get("fromAcc", "").strip().upper()
            to_no = params.get("toAcc", "").strip().upper()
            pwd = params.get("password", "").strip()
            try:
                amt = float(params.get("amount", 0))
            except ValueError:
                amt = 0

            sender = branch_ledger.get(from_no)
            receiver = branch_ledger.get(to_no)
            if not sender or not receiver:
                return self._send_json(404, {"error": "खाते क्रमांक चुकीचा आहे!"})
            if from_no == to_no:
                return self._send_json(400, {"error": "स्वतःच्याच खात्यावर ट्रान्सफर करता येणार नाही!"})
            if not sender.get("netBankingEnabled") or sender.get("netBankingPassword") != pwd:
                return self._send_json(401, {"error": "पासवर्ड चुकीचा आहे!"})
            if amt <= 0 or amt > sender["balance"]:
                return self._send_json(400, {"error": "पुरेशी शिल्लक नाही!"})

            sender["balance"] = round(sender["balance"] - amt, 2)
            sender["transactions"].append({"time": now, "desc": f"NetBanking to {to_no} ({receiver['holderName']})", "type": "DEBIT", "amount": round(amt, 2), "balance": sender["balance"]})
            receiver["balance"] = round(receiver["balance"] + amt, 2)
            receiver["transactions"].append({"time": now, "desc": f"NetBanking from {from_no} ({sender['holderName']})", "type": "CREDIT", "amount": round(amt, 2), "balance": receiver["balance"]})
            save_ledger(branch_ledger)
            return self._send_json(200, {"message": f"₹{amt} ट्रान्सफर झाले!", "account": sender})

        teller = params.get("tellerId")
        if teller not in AUTHORIZED_TELLERS:
            return self._send_json(403, {"error": "Unauthorized Teller"})

        if path == "/api/branch/open-account":
            name = params.get("name", "").strip()
            gov_id = params.get("govId", "").strip()
            try:
                dep = float(params.get("initialDeposit", 0))
            except ValueError:
                dep = 0
            if not name or not gov_id or dep < 500:
                return self._send_json(400, {"error": "नाव, ID आणि किमान ₹500 रक्कम आवश्यक आहे!"})

            acc_no = f"BR-{random.randint(100000, 999999)}"
            acc = {
                "accountNumber": acc_no,
                "holderName": name,
                "govId": gov_id,
                "netBankingEnabled": False,
                "netBankingPassword": "",
                "balance": round(dep, 2),
                "transactions": [{"time": now, "desc": f"Account Opened ({teller})", "type": "CREDIT", "amount": round(dep, 2), "balance": round(dep, 2)}],
            }
            branch_ledger[acc_no] = acc
            save_ledger(branch_ledger)
            return self._send_json(201, {"message": f"नवीन खाते {acc_no} उघडले!", "account": acc})

        if path == "/api/branch/enable-netbanking":
            acc_no = params.get("accNo", "").strip().upper()
            gov_id = params.get("govId", "").strip().lower()
            pwd = params.get("password", "").strip()
            acc = branch_ledger.get(acc_no)
            if not acc:
                return self._send_json(404, {"error": f"खाते {acc_no} सापडले नाही!"})
            if acc["govId"].strip().lower() != gov_id:
                return self._send_json(401, {"error": f"Gov ID जुळत नाही! (योग्य ID: {acc['govId']})"})
            if len(pwd) < 4:
                return self._send_json(400, {"error": "किमान ४ अक्षरी पासवर्ड सेट करा!"})

            acc["netBankingEnabled"] = True
            acc["netBankingPassword"] = pwd
            acc["transactions"].append({"time": now, "desc": f"Net Banking Activated ({teller})", "type": "CREDIT", "amount": 0.0, "balance": acc["balance"]})
            save_ledger(branch_ledger)
            return self._send_json(200, {"message": f"खाते {acc_no} साठी Net Banking चालू झाली!", "account": acc})

        if path == "/api/branch/deposit":
            acc_no = params.get("accNo", "").strip().upper()
            acc = branch_ledger.get(acc_no)
            if not acc:
                return self._send_json(404, {"error": f"खाते {acc_no} सापडले नाही!"})
            try:
                amt = float(params.get("amount", 0))
            except ValueError:
                amt = 0
            if amt <= 0:
                return self._send_json(400, {"error": "योग्य रक्कम टाका!"})

            acc["balance"] = round(acc["balance"] + amt, 2)
            acc["transactions"].append({"time": now, "desc": f"Cash Deposit ({teller})", "type": "CREDIT", "amount": round(amt, 2), "balance": acc["balance"]})
            save_ledger(branch_ledger)
            return self._send_json(200, {"message": f"₹{amt} जमा झाले!", "account": acc})

        if path == "/api/branch/withdraw":
            acc_no = params.get("accNo", "").strip().upper()
            acc = branch_ledger.get(acc_no)
            if not acc:
                return self._send_json(404, {"error": f"खाते {acc_no} सापडले नाही!"})
            if acc["govId"].strip().lower() != params.get("govId", "").strip().lower():
                return self._send_json(401, {"error": f"Gov ID जुळत नाही! (योग्य ID: {acc['govId']})"})
            try:
                amt = float(params.get("amount", 0))
            except ValueError:
                amt = 0
            if amt <= 0 or amt > acc["balance"]:
                return self._send_json(400, {"error": "पुरेशी शिल्लक नाही!"})

            acc["balance"] = round(acc["balance"] - amt, 2)
            acc["transactions"].append({"time": now, "desc": f"Cash Withdrawal ({teller})", "type": "DEBIT", "amount": round(amt, 2), "balance": acc["balance"]})
            save_ledger(branch_ledger)
            return self._send_json(200, {"message": f"₹{amt} काढले गेले!", "account": acc})

        return self._send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    port = 9090
    server = HTTPServer(("127.0.0.1", port), BankHandler)
    print("=" * 55)
    print(f"Branch Counter : http://127.0.0.1:{port}")
    print(f"Net Banking    : http://127.0.0.1:{port}/netbanking")
    print("=" * 55)
    server.serve_forever()

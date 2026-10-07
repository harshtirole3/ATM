const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const currency = value => new Intl.NumberFormat("en-IN", {
  style: "currency", currency: "INR", maximumFractionDigits: 2
}).format(Number(value || 0));
const state = { account: null, transactions: [], inventory: [] };
const viewTitles = {
  overview: "Overview", withdraw: "Withdraw cash", deposit: "Deposit cash",
  transfer: "Transfer", "qr-cash": "QR to cash", transactions: "Transactions"
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.error || "Something went wrong. Please try again.");
    error.code = data.code;
    error.status = response.status;
    throw error;
  }
  return data;
}

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  $("#toast-region").append(toast);
  window.setTimeout(() => toast.remove(), 4200);
}

function setSignedIn(signedIn) {
  $("#login-screen").classList.toggle("hidden", signedIn);
  $("#app-screen").classList.toggle("hidden", !signedIn);
  if (!signedIn) {
    state.account = null;
    state.transactions = [];
  }
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function transactionMeta(type) {
  if (type.includes("DEPOSIT") || type.includes("RECEIVED")) {
    return { symbol: "↙", income: true };
  }
  if (type.includes("TRANSFER")) return { symbol: "⇄", income: type === "TRANSFER IN" };
  if (type.includes("QR")) return { symbol: "▦", income: false };
  return { symbol: "↗", income: false };
}

function displayType(type) {
  return type.toLowerCase().split(" ").map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(" ");
}

function formattedDate(date, time) {
  const parsed = new Date(`${date}T${time || "00:00:00"}`);
  if (Number.isNaN(parsed.getTime())) return `${date} ${time || ""}`;
  return parsed.toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

function renderTransactionItem(transaction) {
  const meta = transactionMeta(transaction.transaction_type);
  const amountPrefix = meta.income ? "+" : "−";
  return `<div class="transaction-row">
    <div class="transaction-description">
      <span class="transaction-symbol ${meta.income ? "income" : "outgoing"}">${meta.symbol}</span>
      <span><b>${escapeHTML(displayType(transaction.transaction_type))}</b><small>${escapeHTML(formattedDate(transaction.date, transaction.time))}</small></span>
    </div>
    <span class="transaction-value ${meta.income ? "positive" : ""}">${amountPrefix}${currency(transaction.amount)}</span>
    <span class="reference-cell">#${escapeHTML(transaction.transaction_id)}</span>
  </div>`;
}

function renderDashboard(data) {
  state.account = data.account;
  state.inventory = data.inventory;
  $("#greeting-name").textContent = data.account.name.split(" ")[0];
  $("#topbar-name").textContent = data.account.name;
  $("#avatar").textContent = data.account.name.trim().charAt(0).toUpperCase();
  $("#account-number").textContent = data.account.account_no;
  $("#account-last4").textContent = String(data.account.account_no).slice(-4);
  $("#balance-amount").textContent = currency(data.account.balance);
  $("#spent-today").textContent = currency(data.spent_today);
  $("#transaction-count").textContent = data.total_transactions;
  $$(".inline-balance").forEach(element => element.textContent = currency(data.account.balance));
  $("#recent-transactions").innerHTML = data.recent_transactions.length
    ? data.recent_transactions.map(renderTransactionItem).join("")
    : '<div class="empty-state">Your recent activity will appear here.</div>';
  $("#cash-inventory").innerHTML = data.inventory.map(item =>
    `<div class="cash-note"><span>₹${Number(item.denomination).toLocaleString("en-IN")} notes</span><b>${Number(item.notes).toLocaleString("en-IN")}</b></div>`
  ).join("");
  $("#atm-total-cash").textContent = currency(
    data.inventory.reduce((total, item) => total + Number(item.value), 0)
  );
  renderTransactions(data.recent_transactions);
}

function renderTransactions(transactions) {
  state.transactions = transactions;
  $("#history-count").textContent = `${transactions.length} recent transaction${transactions.length === 1 ? "" : "s"}`;
  $("#transactions-table").innerHTML = transactions.length
    ? transactions.map(transaction => {
      const meta = transactionMeta(transaction.transaction_type);
      return `<tr>
        <td>${escapeHTML(displayType(transaction.transaction_type))}</td>
        <td class="reference-cell">#${escapeHTML(transaction.transaction_id)}</td>
        <td>${escapeHTML(formattedDate(transaction.date, transaction.time))}</td>
        <td class="${meta.income ? "positive" : ""}">${meta.income ? "+" : "−"}${currency(transaction.amount)}</td>
        <td>${currency(transaction.balance_after)}</td>
      </tr>`;
    }).join("")
    : '<tr><td class="table-empty" colspan="5">No transactions found yet.</td></tr>';
}

async function refreshDashboard() {
  renderDashboard(await api("/api/dashboard"));
}

function showView(view) {
  if (!viewTitles[view]) return;
  $$(".page-view").forEach(section =>
    section.classList.toggle("hidden", section.id !== `view-${view}`)
  );
  $$(".nav-link").forEach(button =>
    button.classList.toggle("active", button.dataset.view === view)
  );
  $("#breadcrumb-current").textContent = viewTitles[view];
  if (view === "transactions") {
    api("/api/transactions")
      .then(result => renderTransactions(result.transactions))
      .catch(error => showToast(error.message, "error"));
  }
  if (window.innerWidth <= 620) window.scrollTo({ top: 0, behavior: "smooth" });
}

function showReceipt(result, action) {
  const type = action === "qr-cash" ? "QR cash withdrawal" : displayType(result.type);
  const details = [
    ["Transaction", type],
    ["Reference", `#${result.transaction_id}`],
    ...(result.qr_reference ? [["QR reference", result.qr_reference]] : []),
    ["Amount", currency(result.amount)],
    ["Balance after", currency(result.balance)],
    ...(result.recipient ? [["Sent to", result.recipient]] : []),
    ...(result.denominations ? [["Cash dispensed", Object.entries(result.denominations)
      .map(([note, count]) => `₹${Number(note).toLocaleString("en-IN")} × ${count}`).join(", ") || "—"]] : [])
  ];
  $("#receipt-title").textContent = action === "transfer" ? "Transfer sent!" : "All done!";
  $("#receipt-description").textContent = action === "transfer"
    ? "Your money has been transferred successfully."
    : "Your transaction has been processed successfully.";
  $("#receipt-details").innerHTML = details.map(([label, value]) =>
    `<div class="receipt-line"><span>${escapeHTML(label)}</span><b>${escapeHTML(value)}</b></div>`
  ).join("");
  $("#receipt-modal").classList.remove("hidden");
}

async function performTransaction(form) {
  const action = form.dataset.action;
  const payload = Object.fromEntries(new FormData(form).entries());
  if (action === "withdraw" || action === "qr-cash") {
    payload.confirmed_high_risk = false;
  }
  const endpoint = action === "qr-cash"
    ? "/api/transactions/qr-cash"
    : `/api/transactions/${action}`;
  const button = $(".form-submit", form);
  const originalContent = button.innerHTML;
  button.disabled = true;
  button.textContent = "Processing…";
  try {
    let result;
    try {
      result = await api(endpoint, { method: "POST", body: JSON.stringify(payload) });
    } catch (error) {
      if (error.code !== "HIGH_RISK_CONFIRMATION") throw error;
      if (!window.confirm(`You are withdrawing ${currency(payload.amount)}, which is above ₹10,000. Continue?`)) {
        return;
      }
      payload.confirmed_high_risk = true;
      result = await api(endpoint, { method: "POST", body: JSON.stringify(payload) });
    }
    showReceipt(result, action);
    form.reset();
    $$(".amount-options button", form).forEach(option => option.classList.remove("selected"));
    await refreshDashboard();
  } catch (error) {
    showToast(error.message, "error");
    if (error.status === 401) setSignedIn(false);
  } finally {
    button.disabled = false;
    button.innerHTML = originalContent;
  }
}

$("#login-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = $("#login-button");
  const errorBox = $("#login-error");
  errorBox.textContent = "";
  button.disabled = true;
  button.textContent = "Signing in…";
  try {
    await api("/api/login", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(new FormData(form).entries()))
    });
    setSignedIn(true);
    await refreshDashboard();
    showView("overview");
    form.reset();
  } catch (error) {
    errorBox.textContent = error.message;
  } finally {
    button.disabled = false;
    button.innerHTML = 'Sign in <span>→</span>';
  }
});

$("#toggle-pin").addEventListener("click", event => {
  const pin = $("#pin-input");
  const visible = pin.type === "password";
  pin.type = visible ? "text" : "password";
  event.currentTarget.textContent = visible ? "Hide" : "Show";
});

$$("[data-view]").forEach(button =>
  button.addEventListener("click", () => showView(button.dataset.view))
);
$$("[data-view-link]").forEach(button => button.addEventListener("click", event => {
  event.preventDefault();
  showView(button.dataset.viewLink);
}));

$$(".transaction-form").forEach(form => {
  form.addEventListener("submit", event => {
    event.preventDefault();
    performTransaction(form);
  });
  $$("[data-amount]", form).forEach(button => button.addEventListener("click", () => {
    const amount = form.querySelector('[name="amount"]');
    amount.value = button.dataset.amount;
    $$(".amount-options button", form).forEach(option =>
      option.classList.toggle("selected", option === button)
    );
  }));
  $('[name="amount"]', form).addEventListener("input", () => {
    $$(".amount-options button", form).forEach(option => option.classList.remove("selected"));
  });
});

$("#logout-button").addEventListener("click", async () => {
  try {
    await api("/api/logout", { method: "POST", body: "{}" });
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setSignedIn(false);
    showView("overview");
  }
});

$("#refresh-transactions").addEventListener("click", async () => {
  try {
    const result = await api("/api/transactions");
    renderTransactions(result.transactions);
    showToast("Transaction list updated.");
  } catch (error) {
    showToast(error.message, "error");
  }
});

$("#close-receipt").addEventListener("click", () => $("#receipt-modal").classList.add("hidden"));
$("#done-receipt").addEventListener("click", () => $("#receipt-modal").classList.add("hidden"));
$("#print-receipt").addEventListener("click", () => window.print());
$("#receipt-modal").addEventListener("click", event => {
  if (event.target === event.currentTarget) event.currentTarget.classList.add("hidden");
});

$("#today-label").textContent = new Date().toLocaleDateString("en-IN", {
  weekday: "short", day: "numeric", month: "short", year: "numeric"
});

api("/api/session")
  .then(session => {
    setSignedIn(session.authenticated);
    if (session.authenticated) renderDashboard(session.dashboard);
  })
  .catch(() => setSignedIn(false));

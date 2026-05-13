// /* ============================================================
//    OrderHub — vanilla JS starter
//    Edit the data arrays below to plug in your real data.
//    All state is in-memory and resets on page reload.
//    ============================================================ */

// // ---------- DATA (edit here) ----------
// const customerNames = [
//   "Nord Lens Group","Brillen Partner","Optic House","Vision Markt","ClearView Retail",
//   "Alpine Optical","Metro Eyewear","Urban Lens Lab","Prism Care","Focus Point",
// ];
// //
// let customers = customerNames.map((name, i) => ({
//   id: `CU-${String(i+1).padStart(3,"0")}`,
//   name,
//   contactName: ["Lena Hoffmann","Pavel Novak","Greta Weiss","Jonas Klein","Marta Varga","Sofia Fischer","Tomas Schmidt","Klara Costa","Felix Meyer","Nina Rossi"][i%10],
//   email: `orders@${name.toLowerCase().replaceAll(" ","")}.example`,
//   phone: `+49 ${200000000 + i*6173}`,
//   address: ["Lindenallee 12","Karlova 88","Mariahilfer Str. 4","Leopoldstr. 25","Speersort 9"][i%5],
//   city: ["Berlin","Prague","Vienna","Munich","Hamburg","Zürich","Milan","Warsaw"][i%8],
//   country: ["DE","CZ","AT","DE","DE","CH","IT","PL"][i%8],
//   notes: i%3===0 ? "Preferred VIP partner" : "Standard B2B account",
// }));

// const orderStatuses = ["Draft","In warehouse","Packed","Shipped","Delivered"];
// const paymentMethods = ["Net 14","Prepaid","Net 30","On delivery","Paid"];

// let orders = Array.from({length: 48}, (_,i) => {
//   const seq = 142 - i;
//   const status = ["In warehouse","Draft","Shipped","Packed","Delivered"][i%5];
//   const date = new Date(2026, 3, 30 - (i%60)).toISOString().slice(0,10);
//   const cust = customers[i % customers.length];
//   return {
//     id: `SO-2026-${String(seq).padStart(4,"0")}`,
//     customer: cust.name,
//     customerId: cust.id,
//     owner: ["Marek","Anna","Renata","Lukas","Elena"][i%5],
//     value: 960 + i*185,                        // numeric EUR
//     status,
//     orderDate: date,
//     payment: paymentMethods[i%4],
//     address: `${cust.address}, ${cust.city}`,
//     items: [
//       { sku: ["LEN","FRM","CLN","DSP","LEN"][i%5] + "-" + String(100+i).padStart(4,"0"),
//         name: ["Lens kits","Classic frames","Cleaner sets","Display stands","Premium lenses"][i%5],
//         quantity: (i%18)+4 },
//     ],
//     trackingNumber: status === "Shipped" || status === "Delivered" ? `TRK-${1000+i}` : "",
//     carrier: status === "Shipped" || status === "Delivered" ? "DHL" : "",
//     notes: status === "Awaiting stock" ? "Check stock first." : "Standard handling.",
//   };
// });

// const warehouses = [
//   { id: "wh-berlin", name: "Berlin Main",  location: "Berlin, DE",  isStore: true },
//   { id: "wh-munich", name: "Munich Hub",   location: "Munich, DE",  isStore: false },
//   { id: "wh-vienna", name: "Vienna Store", location: "Vienna, AT",  isStore: true },
// ];

// let warehouseStock = {}; // { warehouseId: [{sku, item, quantity, zone, status, barcode}] }
// warehouses.forEach((w, wi) => {
//   warehouseStock[w.id] = Array.from({length: 14}, (_, idx) => ({
//     sku: `${["LEN","FRM","CLN","DSP","SUN","ACC"][idx%6]}-${String(idx+1+wi*100).padStart(3,"0")}`,
//     item: ["Lens kits","Classic frames","Cleaner sets","Display stands","Sun lenses","Accessories"][idx%6],
//     quantity: ((idx*3+8)%32)+3,
//     unit: idx%4===0 ? "pallets" : "boxes",
//     zone: `${["A","B","C"][idx%3]}-${String((idx%14)+1).padStart(2,"0")}`,
//     status: ["Ready","Picking","Packed","Reserved","Low stock"][idx%5],
//     barcode: `${5400000000000 + wi*1_000_000 + (idx+1)*137}`,
//   }));
// });

// let transferLog = []; // { id, fromId, toId, sku, item, quantity, actor, timestamp }

// const contacts = Array.from({length: 30}, (_,i) => {
//   const fn = ["Lena","Pavel","Greta","Jonas","Marta","Sofia","Tomas","Klara","Felix","Nina"][i%10];
//   const ln = ["Hoffmann","Novak","Weiss","Klein","Varga","Fischer","Schmidt","Costa","Meyer","Rossi"][(i*3)%10];
//   return { id: `CON-${String(i+1).padStart(3,"0")}`, name: `${fn} ${ln}`,
//            email: `${fn}.${ln}@example.com`.toLowerCase(),
//            phone: `+49 ${300000000 + i*7919}` };
// });

// const inventoryProducts = Array.from({length: 50}, (_,i) => ({
//   sku: `${["LEN","FRM","CLN","DSP","ACC","SUN","CAS","KIT"][i%8]}-${String(i+100).padStart(4,"0")}`,
//   product: `${["Premium lens","Classic frame","Cleaner set","Display stand","Travel case","Sun lens","Repair kit","Nose pad set"][i%8]} ${i+1}`,
//   category: ["Lenses","Frames","Accessories","Displays","Service parts"][i%5],
//   unitPrice: 18 + ((i*11)%140),
//   storeStock: (i*7)%34,
//   warehouseStock: 18 + ((i*19)%280),
//   reorder: 8 + (i%12),
// }));

// const loginProfiles = {
//   staff: { name: "Marek Novak", email: "marek@company.com", role: "Staff", store: "Berlin Store" },
//   admin: { name: "Admin User",  email: "admin@company.com",  role: "Admin", store: "All stores" },
// };

// // ---------- STATE ----------
// const state = {
//   user: null,
//   section: "Dashboard",
//   expandedOrderId: null,
//   // sales filters
//   orderSearch: "", orderStatus: "All", orderPayment: "All",
//   orderSortKey: "orderDate", orderSortDir: "desc",
//   orderDateFrom: "", orderDateTo: "",
//   orderPage: 1, orderPageSize: 10,
//   // warehouse
//   selectedWarehouseId: warehouses[0].id,
//   warehouseSearch: "",
//   // customers
//   customerSearch: "",
//   // packing
//   selectedPackingIds: new Set(),
//   packingSession: null, // { orderId, scanned:{sku:n}, scanInput, carrier, trackingNumber, weight }
// };

// const SECTIONS = [
//   { key: "Dashboard", label: "Dashboard" },
//   { key: "Sales",     label: "Sales",     count: () => orders.length },
//   { key: "Warehouse", label: "Warehouse", count: () => warehouses.length },
//   { key: "Packing",   label: "Packing",   count: () => orders.filter(o=>o.status==="In warehouse"||o.status==="Packed").length },
//   { key: "Tracking",  label: "Tracking",  count: () => orders.filter(o=>o.status==="Shipped").length },
//   { key: "Customers", label: "Customers", count: () => customers.length },
//   { key: "Contacts",  label: "Contacts",  count: () => contacts.length },
//   { key: "Inventory", label: "Inventory", count: () => inventoryProducts.length },
//   { key: "Reports",   label: "Reports" },
//   { key: "Transfers", label: "Transfers", count: () => transferLog.length },
// ];

// // ---------- UTILITIES ----------
// const $ = (sel, root=document) => root.querySelector(sel);
// const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
// const fmtEUR = n => new Intl.NumberFormat("en-US",{style:"currency",currency:"EUR"}).format(n);
// const escapeHtml = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
// const badgeClass = s => ({"Shipped":"shipped","Delivered":"delivered","Draft":"draft","In warehouse":"warehouse","Packed":"packed","Awaiting stock":"awaiting"}[s] || "");
// const matchesSearch = (fields, q) => {
//   const n = q.trim().toLowerCase();
//   if (!n) return true;
//   return fields.some(f => String(f ?? "").toLowerCase().includes(n));
// };
// function paginate(arr, page, pageSize) {
//   const totalPages = Math.max(1, Math.ceil(arr.length/pageSize));
//   const safe = Math.min(page, totalPages);
//   const start = (safe-1)*pageSize;
//   return { items: arr.slice(start, start+pageSize), page: safe, totalPages,
//     start: arr.length===0 ? 0 : start+1, end: Math.min(start+pageSize, arr.length), total: arr.length };
// }
// function uid(prefix="ID") { return `${prefix}-${Math.random().toString(36).slice(2,8).toUpperCase()}`; }

// // ---------- LOGIN ----------
// let loginRole = "staff";
// $$("[data-login-tab]").forEach(t => t.addEventListener("click", () => {
//   loginRole = t.dataset.loginTab;
//   $$("[data-login-tab]").forEach(x => x.classList.toggle("active", x===t));
//   $("#login-email").value = loginProfiles[loginRole].email;
// }));
// $("#login-form").addEventListener("submit", e => {
//   e.preventDefault();
//   state.user = loginProfiles[loginRole];
//   $("#login-view").hidden = true;
//   $("#app-view").hidden = false;
//   renderShell();
//   render();
// });
// $("#logout-btn").addEventListener("click", () => {
//   state.user = null;
//   $("#app-view").hidden = true;
//   $("#login-view").hidden = false;
// });

// // ---------- SHELL ----------
// function renderShell() {
//   const nav = $("#nav");
//   nav.innerHTML = SECTIONS.map(s =>
//     `<button class="nav-item ${state.section===s.key?'active':''}" data-section="${s.key}">
//        <span>${s.label}</span>
//        ${s.count ? `<span class="count">${s.count()}</span>` : ""}
//      </button>`).join("");
//   nav.querySelectorAll(".nav-item").forEach(btn => btn.addEventListener("click", () => {
//     state.section = btn.dataset.section;
//     renderShell(); render();
//   }));
//   $("#user-chip").innerHTML = `<strong>${escapeHtml(state.user.name)}</strong><span class="muted small">${escapeHtml(state.user.role)} · ${escapeHtml(state.user.store)}</span>`;
// }

// // ---------- ROUTER ----------
// function render() {
//   $("#page-title").textContent = state.section;
//   const c = $("#content");
//   switch (state.section) {
//     case "Dashboard":  c.innerHTML = renderDashboard();  bindDashboard(); break;
//     case "Sales":      c.innerHTML = renderSales();      bindSales();     break;
//     case "Warehouse":  c.innerHTML = renderWarehouse();  bindWarehouse(); break;
//     case "Packing":    c.innerHTML = renderPacking();    bindPacking();   break;
//     case "Tracking":   c.innerHTML = renderTracking();   break;
//     case "Customers":  c.innerHTML = renderCustomers();  bindCustomers(); break;
//     case "Contacts":   c.innerHTML = renderContacts();   break;
//     case "Inventory":  c.innerHTML = renderInventory();  break;
//     case "Reports":    c.innerHTML = renderReports();    break;
//     case "Transfers":  c.innerHTML = renderTransfers();  bindTransfers(); break;
//   }
// }

// // ---------- DASHBOARD ----------
// function renderDashboard() {
//   return `<div class="dash-grid">${SECTIONS.filter(s=>s.key!=="Dashboard").map(s => `
//     <div class="dash-card" data-go="${s.key}">
//       <div class="label">${s.label}</div>
//       <div class="detail">Open ${s.label.toLowerCase()} workspace</div>
//       <div class="count">${s.count ? s.count() : "—"}</div>
//     </div>`).join("")}</div>`;
// }
// function bindDashboard() {
//   $$("[data-go]").forEach(c => c.addEventListener("click", () => {
//     state.section = c.dataset.go; renderShell(); render();
//   }));
// }

// // ---------- SALES ----------
// function filterSortOrders() {
//   let list = orders.filter(o => {
//     if (state.orderStatus !== "All" && o.status !== state.orderStatus) return false;
//     if (state.orderPayment !== "All" && o.payment !== state.orderPayment) return false;
//     if (state.orderDateFrom && o.orderDate < state.orderDateFrom) return false;
//     if (state.orderDateTo && o.orderDate > state.orderDateTo) return false;
//     const cust = customers.find(c => c.id === o.customerId);
//     return matchesSearch([o.id, o.customer, cust?.city, cust?.contactName, cust?.email, o.owner], state.orderSearch);
//   });
//   const k = state.orderSortKey, dir = state.orderSortDir === "asc" ? 1 : -1;
//   list.sort((a,b) => {
//     const av = a[k], bv = b[k];
//     if (typeof av === "number" && typeof bv === "number") return (av-bv)*dir;
//     return String(av).localeCompare(String(bv))*dir;
//   });
//   return list;
// }
// function renderSales() {
//   const list = filterSortOrders();
//   const pg = paginate(list, state.orderPage, state.orderPageSize);
//   return `<div class="card">
//     <div class="card-header">
//       <h3>Sales orders</h3>
//       <div class="toolbar">
//         <input id="o-search" type="text" placeholder="Search order, customer, city…" value="${escapeHtml(state.orderSearch)}" />
//         <select id="o-status">${["All", ...orderStatuses].map(s=>`<option ${s===state.orderStatus?"selected":""}>${s}</option>`).join("")}</select>
//         <select id="o-payment">${["All", ...paymentMethods].map(s=>`<option ${s===state.orderPayment?"selected":""}>${s}</option>`).join("")}</select>
//         <input id="o-from" type="date" value="${state.orderDateFrom}" title="From" />
//         <input id="o-to"   type="date" value="${state.orderDateTo}"   title="To" />
//         <select id="o-sort">
//           ${[["orderDate","Date"],["id","Order #"],["customer","Customer"],["value","Value"],["status","Status"]]
//             .map(([k,l])=>`<option value="${k}" ${k===state.orderSortKey?"selected":""}>${l}</option>`).join("")}
//         </select>
//         <button class="btn btn-sm" id="o-dir">${state.orderSortDir==="asc"?"↑":"↓"}</button>
//         <button class="btn btn-primary btn-sm" id="o-new">+ New order</button>
//       </div>
//     </div>
//     <table>
//       <thead><tr><th>Order</th><th>Value</th><th>Customer</th><th>City</th><th>Status</th><th></th></tr></thead>
//       <tbody>${pg.items.map(o => {
//         const cust = customers.find(c=>c.id===o.customerId);
//         const expanded = state.expandedOrderId === o.id;
//         return `
//           <tr class="clickable ${expanded?"expanded":""}" data-toggle="${o.id}">
//             <td><strong>${o.id}</strong><div class="muted small">${o.orderDate}</div></td>
//             <td>${fmtEUR(o.value)}</td>
//             <td>${escapeHtml(o.customer)}</td>
//             <td>${escapeHtml(cust?.city ?? "")}</td>
//             <td>
//               <select class="status-select" data-order="${o.id}" onclick="event.stopPropagation()">
//                 ${orderStatuses.concat(["Paid"]).map(s => `<option ${s===o.status?"selected":""}>${s}</option>`).join("")}
//               </select>
//             </td>
//             <td><span class="badge ${badgeClass(o.status)}">${o.status}</span></td>
//           </tr>
//           ${expanded ? `<tr class="expand-row"><td colspan="6">
//             <dl class="kv">
//               <dt>Owner</dt><dd>${escapeHtml(o.owner)}</dd>
//               <dt>Payment</dt><dd>${escapeHtml(o.payment)}</dd>
//               <dt>Address</dt><dd>${escapeHtml(o.address)}</dd>
//               <dt>Items</dt><dd>${o.items.map(i => `${escapeHtml(i.name)} (${escapeHtml(i.sku)}) × ${i.quantity}`).join(", ")}</dd>
//               <dt>Tracking</dt><dd>${escapeHtml(o.trackingNumber || "—")} ${o.carrier?`<span class="muted">(${escapeHtml(o.carrier)})</span>`:""}</dd>
//               <dt>Notes</dt><dd>${escapeHtml(o.notes)}</dd>
//             </dl>
//           </td></tr>` : ""}
//         `;
//       }).join("")}</tbody>
//     </table>
//     ${renderPagination(pg, "order")}
//   </div>`;
// }
// function bindSales() {
//   $("#o-search").addEventListener("input", e => { state.orderSearch = e.target.value; state.orderPage = 1; render(); });
//   $("#o-status").addEventListener("change", e => { state.orderStatus = e.target.value; render(); });
//   $("#o-payment").addEventListener("change", e => { state.orderPayment = e.target.value; render(); });
//   $("#o-from").addEventListener("change", e => { state.orderDateFrom = e.target.value; render(); });
//   $("#o-to").addEventListener("change",   e => { state.orderDateTo   = e.target.value; render(); });
//   $("#o-sort").addEventListener("change", e => { state.orderSortKey = e.target.value; render(); });
//   $("#o-dir").addEventListener("click", () => { state.orderSortDir = state.orderSortDir==="asc"?"desc":"asc"; render(); });
//   $("#o-new").addEventListener("click", openNewOrderModal);
//   $$("[data-toggle]").forEach(r => r.addEventListener("click", () => {
//     state.expandedOrderId = state.expandedOrderId === r.dataset.toggle ? null : r.dataset.toggle;
//     render();
//   }));
//   $$(".status-select").forEach(sel => sel.addEventListener("change", e => {
//     const order = orders.find(o => o.id === sel.dataset.order);
//     const v = e.target.value;
//     if (v === "Paid") { order.payment = "Paid"; order.status = "Delivered"; }
//     else order.status = v;
//     render();
//   }));
//   bindPagination("order");
// }

// // ---------- PAGINATION HELPER ----------
// function renderPagination(pg, ns) {
//   return `<div class="pagination">
//     <span>Showing ${pg.start}–${pg.end} of ${pg.total}</span>
//     <div class="right">
//       <label>Rows
//         <select data-pgsize="${ns}">${[10,25,50].map(n=>`<option ${state[ns+"PageSize"]===n?"selected":""}>${n}</option>`).join("")}</select>
//       </label>
//       <button class="btn btn-sm" data-pg="${ns}-prev" ${pg.page<=1?"disabled":""}>Prev</button>
//       <span>${pg.page} / ${pg.totalPages}</span>
//       <button class="btn btn-sm" data-pg="${ns}-next" ${pg.page>=pg.totalPages?"disabled":""}>Next</button>
//     </div>
//   </div>`;
// }
// function bindPagination(ns) {
//   const sz = $(`[data-pgsize="${ns}"]`); if (sz) sz.addEventListener("change", e => { state[ns+"PageSize"] = +e.target.value; state[ns+"Page"]=1; render(); });
//   const p = $(`[data-pg="${ns}-prev"]`); if (p) p.addEventListener("click", () => { state[ns+"Page"]--; render(); });
//   const n = $(`[data-pg="${ns}-next"]`); if (n) n.addEventListener("click", () => { state[ns+"Page"]++; render(); });
// }

// // ---------- WAREHOUSE ----------
// function renderWarehouse() {
//   const wh = warehouses.find(w => w.id === state.selectedWarehouseId) ?? warehouses[0];
//   const items = (warehouseStock[wh.id] || []).filter(it =>
//     matchesSearch([it.sku, it.item, it.zone, it.status, it.barcode], state.warehouseSearch));
//   return `<div class="card">
//     <div class="card-header">
//       <h3>Warehouse</h3>
//       <div class="toolbar">
//         <select id="wh-pick">${warehouses.map(w => `<option value="${w.id}" ${w.id===wh.id?"selected":""}>${escapeHtml(w.name)} — ${escapeHtml(w.location)}</option>`).join("")}</select>
//         <input id="wh-search" type="text" placeholder="Search SKU, name, barcode…" value="${escapeHtml(state.warehouseSearch)}" />
//         <button class="btn btn-sm" id="wh-transfer">Transfer stock</button>
//         <button class="btn btn-sm" id="wh-history">Transfer history</button>
//       </div>
//     </div>
//     <table>
//       <thead><tr><th>SKU</th><th>Item</th><th>Quantity</th><th>Zone</th><th>Status</th><th>Barcode</th></tr></thead>
//       <tbody>${items.map(it => `
//         <tr><td>${escapeHtml(it.sku)}</td><td>${escapeHtml(it.item)}</td>
//         <td>${it.quantity} ${escapeHtml(it.unit)}</td><td>${escapeHtml(it.zone)}</td>
//         <td><span class="badge">${escapeHtml(it.status)}</span></td>
//         <td class="muted small">${escapeHtml(it.barcode||"")}</td></tr>`).join("")}</tbody>
//     </table>
//   </div>`;
// }
// function bindWarehouse() {
//   $("#wh-pick").addEventListener("change", e => { state.selectedWarehouseId = e.target.value; render(); });
//   $("#wh-search").addEventListener("input", e => { state.warehouseSearch = e.target.value; render(); });
//   $("#wh-transfer").addEventListener("click", openTransferModal);
//   $("#wh-history").addEventListener("click", () => { state.section = "Transfers"; renderShell(); render(); });
// }

// // ---------- TRANSFERS ----------
// function renderTransfers() {
//   return `<div class="card">
//     <div class="card-header"><h3>Transfer history</h3></div>
//     <table>
//       <thead><tr><th>When</th><th>From</th><th>To</th><th>SKU</th><th>Item</th><th>Qty</th><th>Actor</th></tr></thead>
//       <tbody>${transferLog.length === 0
//         ? `<tr><td colspan="7" class="muted" style="text-align:center;padding:24px">No transfers yet.</td></tr>`
//         : transferLog.slice().reverse().map(t => `
//           <tr><td>${escapeHtml(t.timestamp)}</td>
//             <td>${escapeHtml(warehouses.find(w=>w.id===t.fromId)?.name||t.fromId)}</td>
//             <td>${escapeHtml(warehouses.find(w=>w.id===t.toId)?.name||t.toId)}</td>
//             <td>${escapeHtml(t.sku)}</td><td>${escapeHtml(t.item)}</td>
//             <td>${t.quantity}</td><td>${escapeHtml(t.actor)}</td></tr>`).join("")}
//       </tbody>
//     </table>
//   </div>`;
// }
// function bindTransfers() {}

// function openTransferModal() {
//   const fromId = state.selectedWarehouseId;
//   const toId = warehouses.find(w => w.id !== fromId)?.id || fromId;
//   showModal({
//     title: "Transfer stock between warehouses",
//     body: `
//       <div class="row">
//         <label>From <select id="t-from">${warehouses.map(w=>`<option value="${w.id}" ${w.id===fromId?"selected":""}>${escapeHtml(w.name)}</option>`).join("")}</select></label>
//         <label>To <select id="t-to">${warehouses.map(w=>`<option value="${w.id}" ${w.id===toId?"selected":""}>${escapeHtml(w.name)}</option>`).join("")}</select></label>
//       </div>
//       <label>SKU <select id="t-sku"></select></label>
//       <label>Quantity <input id="t-qty" type="number" min="1" value="1" /></label>
//       <div id="t-err"></div>
//     `,
//     confirmLabel: "Transfer",
//     onMount: m => {
//       const refresh = () => {
//         const stock = warehouseStock[$("#t-from").value] || [];
//         $("#t-sku").innerHTML = stock.map(s => `<option value="${s.sku}">${escapeHtml(s.sku)} — ${escapeHtml(s.item)} (${s.quantity} ${escapeHtml(s.unit)})</option>`).join("");
//       };
//       refresh();
//       $("#t-from").addEventListener("change", refresh);
//     },
//     onConfirm: () => {
//       const fromId = $("#t-from").value, toId = $("#t-to").value;
//       const sku = $("#t-sku").value, qty = +$("#t-qty").value;
//       if (fromId === toId) { $("#t-err").innerHTML = `<div class="alert err">Pick different warehouses.</div>`; return false; }
//       const fromStock = warehouseStock[fromId];
//       const item = fromStock.find(s => s.sku === sku);
//       if (!item || qty < 1 || qty > item.quantity) { $("#t-err").innerHTML = `<div class="alert err">Invalid quantity.</div>`; return false; }
//       item.quantity -= qty;
//       const toStock = warehouseStock[toId];
//       let target = toStock.find(s => s.sku === sku);
//       if (target) target.quantity += qty;
//       else toStock.push({ ...item, quantity: qty });
//       transferLog.push({ id: uid("TR"), fromId, toId, sku, item: item.item, quantity: qty,
//         actor: state.user.name, timestamp: new Date().toLocaleString() });
//       closeModal(); render();
//     },
//   });
// }

// // ---------- PACKING ----------
// function renderPacking() {
//   const queue = orders.filter(o => o.status === "In warehouse" || o.status === "Packed");
//   const sel = state.selectedPackingIds;
//   const progress = Array.from(sel).map(id => {
//     const o = orders.find(x => x.id===id); if (!o) return null;
//     const required = o.items.reduce((s,l)=>s+l.quantity,0);
//     let scanned = 0;
//     if (o.status === "Shipped" || o.status === "Delivered") scanned = required;
//     else if (state.packingSession?.orderId === id) {
//       scanned = o.items.reduce((s,l)=>s + Math.min(l.quantity, state.packingSession.scanned[l.sku]||0), 0);
//     }
//     return { o, required, scanned };
//   }).filter(Boolean);

//   return `
//     ${sel.size>0 ? `<div class="card"><div class="card-header"><h3>Packing progress (${sel.size})</h3>
//       <button class="btn btn-sm" id="p-print">Print packing list</button></div>
//       <div class="card-body">
//         ${progress.map(p => `
//           <div style="margin-bottom:10px">
//             <div style="display:flex;justify-content:space-between"><strong>${p.o.id}</strong><span class="muted small">${p.scanned}/${p.required}</span></div>
//             <div class="progress-bar"><div style="width:${p.required?Math.round(p.scanned/p.required*100):0}%"></div></div>
//           </div>`).join("")}
//       </div></div>` : ""}

//     <div class="card">
//       <div class="card-header"><h3>Packing queue</h3></div>
//       <table>
//         <thead><tr><th></th><th>Order</th><th>Customer</th><th>Items</th><th>Status</th><th></th></tr></thead>
//         <tbody>${queue.map(o => `
//           <tr>
//             <td><input type="checkbox" data-pack-sel="${o.id}" ${sel.has(o.id)?"checked":""}></td>
//             <td><strong>${o.id}</strong></td>
//             <td>${escapeHtml(o.customer)}</td>
//             <td>${o.items.reduce((s,l)=>s+l.quantity,0)} units</td>
//             <td><span class="badge ${badgeClass(o.status)}">${o.status}</span></td>
//             <td><button class="btn btn-sm btn-primary" data-pack-start="${o.id}">Start packing</button></td>
//           </tr>`).join("")}</tbody>
//       </table>
//     </div>`;
// }
// function bindPacking() {
//   $$("[data-pack-sel]").forEach(c => c.addEventListener("change", e => {
//     const id = c.dataset.packSel;
//     if (e.target.checked) state.selectedPackingIds.add(id); else state.selectedPackingIds.delete(id);
//     render();
//   }));
//   $$("[data-pack-start]").forEach(b => b.addEventListener("click", () => openPackingModal(b.dataset.packStart)));
//   const print = $("#p-print"); if (print) print.addEventListener("click", () => window.print());
// }
// function openPackingModal(orderId) {
//   const order = orders.find(o => o.id === orderId);
//   if (!order) return;
//   state.packingSession = { orderId, scanned: {}, scanInput: "", carrier: "DHL", trackingNumber: "", weight: "" };
//   showModal({
//     title: `Packing station — ${order.id}`,
//     body: `
//       <div class="row">
//         <label>Scan / type SKU<input id="ps-input" placeholder="Scan barcode or SKU" /></label>
//         <label>Weight (kg)<input id="ps-weight" type="number" step="0.01" min="0" /></label>
//       </div>
//       <div id="ps-feedback"></div>
//       <table><thead><tr><th>SKU</th><th>Product</th><th>Scanned</th><th>Required</th></tr></thead>
//         <tbody id="ps-rows"></tbody></table>
//       <div class="row">
//         <label>Carrier *<select id="ps-carrier"><option>DHL</option><option>UPS</option><option>FedEx</option><option>DPD</option><option>GLS</option></select></label>
//         <label>Tracking number *<input id="ps-tracking" placeholder="e.g. 1Z999AA10123456784" /></label>
//       </div>
//       <div id="ps-err"></div>
//     `,
//     confirmLabel: "Complete & ship",
//     onMount: () => {
//       const refresh = () => {
//         const s = state.packingSession;
//         $("#ps-rows").innerHTML = order.items.map(l =>
//           `<tr><td>${escapeHtml(l.sku)}</td><td>${escapeHtml(l.name)}</td><td>${s.scanned[l.sku]||0}</td><td>${l.quantity}</td></tr>`).join("");
//       };
//       refresh();
//       $("#ps-input").addEventListener("keydown", e => {
//         if (e.key !== "Enter") return;
//         e.preventDefault();
//         const code = e.target.value.trim();
//         const match = order.items.find(l => l.sku.toLowerCase() === code.toLowerCase());
//         const fb = $("#ps-feedback");
//         if (!match) { fb.innerHTML = `<div class="alert err">SKU not in this order</div>`; return; }
//         const cur = state.packingSession.scanned[match.sku] || 0;
//         if (cur >= match.quantity) { fb.innerHTML = `<div class="alert err">Already fully scanned</div>`; }
//         else { state.packingSession.scanned[match.sku] = cur+1; fb.innerHTML = `<div class="alert ok">Scanned ${escapeHtml(match.name)}</div>`; }
//         e.target.value = ""; refresh();
//       });
//     },
//     onConfirm: () => {
//       const tracking = $("#ps-tracking").value.trim();
//       const carrier = $("#ps-carrier").value;
//       const allDone = order.items.every(l => (state.packingSession.scanned[l.sku]||0) >= l.quantity);
//       const trackingValid = /^[A-Za-z0-9-]{6,40}$/.test(tracking);
//       if (!allDone) { $("#ps-err").innerHTML = `<div class="alert err">Scan all items first.</div>`; return false; }
//       if (!trackingValid) { $("#ps-err").innerHTML = `<div class="alert err">Tracking must be 6–40 chars (letters/digits/-).</div>`; return false; }
//       order.status = "Shipped"; order.carrier = carrier; order.trackingNumber = tracking;
//       state.packingSession = null;
//       state.selectedPackingIds.delete(order.id);
//       closeModal(); render();
//     },
//     onCancel: () => { state.packingSession = null; render(); },
//   });
// }

// // ---------- TRACKING ----------
// function renderTracking() {
//   const list = orders.filter(o => o.status === "Shipped" || o.status === "Delivered");
//   return `<div class="card">
//     <div class="card-header"><h3>Shipments</h3></div>
//     <table>
//       <thead><tr><th>Order</th><th>Customer</th><th>Destination</th><th>Tracking</th><th>Carrier</th><th>Status</th></tr></thead>
//       <tbody>${list.map(o => `
//         <tr><td>${o.id}</td><td>${escapeHtml(o.customer)}</td>
//         <td>${escapeHtml(o.address)}</td>
//         <td>${escapeHtml(o.trackingNumber||"—")}</td>
//         <td>${escapeHtml(o.carrier||"—")}</td>
//         <td><span class="badge ${badgeClass(o.status)}">${o.status}</span></td></tr>`).join("")}</tbody>
//     </table>
//   </div>`;
// }

// // ---------- CUSTOMERS ----------
// function renderCustomers() {
//   const list = customers.filter(c => matchesSearch([c.id,c.name,c.contactName,c.email,c.phone,c.city,c.country], state.customerSearch));
//   return `<div class="card">
//     <div class="card-header">
//       <h3>Customers</h3>
//       <div class="toolbar">
//         <input id="c-search" type="text" placeholder="Search…" value="${escapeHtml(state.customerSearch)}" />
//         <button class="btn btn-primary btn-sm" id="c-new">+ New customer</button>
//       </div>
//     </div>
//     <table>
//       <thead><tr><th>ID</th><th>Name</th><th>Contact</th><th>Email</th><th>Phone</th><th>City</th><th></th></tr></thead>
//       <tbody>${list.map(c => `
//         <tr><td>${c.id}</td><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.contactName)}</td>
//         <td>${escapeHtml(c.email)}</td><td>${escapeHtml(c.phone)}</td><td>${escapeHtml(c.city)}</td>
//         <td><button class="btn btn-sm" data-c-edit="${c.id}">Edit</button></td></tr>`).join("")}</tbody>
//     </table>
//   </div>`;
// }
// function bindCustomers() {
//   $("#c-search").addEventListener("input", e => { state.customerSearch = e.target.value; render(); });
//   $("#c-new").addEventListener("click", () => openCustomerModal(null));
//   $$("[data-c-edit]").forEach(b => b.addEventListener("click", () => openCustomerModal(b.dataset.cEdit)));
// }
// function openCustomerModal(id) {
//   const editing = id ? customers.find(c=>c.id===id) : { id: uid("CU"), name:"", contactName:"", email:"", phone:"", address:"", city:"", country:"", notes:"" };
//   showModal({
//     title: id ? `Edit ${editing.name}` : "New customer",
//     body: ["name","contactName","email","phone","address","city","country","notes"].map(f =>
//       `<label>${f}<input data-f="${f}" value="${escapeHtml(editing[f])}" /></label>`).join(""),
//     confirmLabel: "Save",
//     onConfirm: () => {
//       const data = { id: editing.id };
//       $$("[data-f]").forEach(i => data[i.dataset.f] = i.value.trim());
//       if (!data.name) return false;
//       const idx = customers.findIndex(c => c.id === data.id);
//       if (idx >= 0) customers[idx] = { ...customers[idx], ...data };
//       else customers.push(data);
//       closeModal(); render();
//     },
//   });
// }

// // ---------- CONTACTS ----------
// function renderContacts() {
//   return `<div class="card"><div class="card-header"><h3>Contacts</h3></div>
//     <table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th></tr></thead>
//     <tbody>${contacts.map(c=>`<tr><td>${c.id}</td><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.email)}</td><td>${escapeHtml(c.phone)}</td></tr>`).join("")}</tbody>
//     </table></div>`;
// }

// // ---------- INVENTORY ----------
// function renderInventory() {
//   return `<div class="card"><div class="card-header"><h3>Inventory</h3></div>
//     <table><thead><tr><th>SKU</th><th>Product</th><th>Category</th><th>Price</th><th>Store</th><th>Warehouse</th><th>Reorder</th></tr></thead>
//     <tbody>${inventoryProducts.map(p=>`<tr><td>${p.sku}</td><td>${escapeHtml(p.product)}</td><td>${p.category}</td>
//       <td>${fmtEUR(p.unitPrice)}</td><td>${p.storeStock}</td><td>${p.warehouseStock}</td><td>${p.reorder}</td></tr>`).join("")}</tbody>
//     </table></div>`;
// }

// // ---------- REPORTS ----------
// function renderReports() {
//   const totalRevenue = orders.reduce((s,o)=>s+o.value,0);
//   const byStatus = orderStatuses.map(s => ({ s, n: orders.filter(o=>o.status===s).length }));
//   return `<div class="dash-grid">
//     <div class="dash-card"><div class="label">Total revenue</div><div class="count">${fmtEUR(totalRevenue)}</div></div>
//     <div class="dash-card"><div class="label">Orders</div><div class="count">${orders.length}</div></div>
//     <div class="dash-card"><div class="label">Customers</div><div class="count">${customers.length}</div></div>
//     <div class="dash-card"><div class="label">Warehouses</div><div class="count">${warehouses.length}</div></div>
//   </div>
//   <div class="card"><div class="card-header"><h3>Orders by status</h3></div>
//     <table><thead><tr><th>Status</th><th>Count</th></tr></thead>
//     <tbody>${byStatus.map(b=>`<tr><td>${b.s}</td><td>${b.n}</td></tr>`).join("")}</tbody>
//     </table></div>`;
// }

// // ---------- NEW ORDER ----------
// function openNewOrderModal() {
//   let isNewCustomer = false;
//   let lineItems = [{ sku: inventoryProducts[0].sku, quantity: 1 }];
//   showModal({
//     title: "New order",
//     body: `
//       <label><input type="checkbox" id="no-newcust" /> New customer</label>
//       <div id="no-cust-existing">
//         <label>Customer
//           <select id="no-cust">${customers.map(c=>`<option value="${c.id}">${escapeHtml(c.name)} — ${escapeHtml(c.city)}</option>`).join("")}</select>
//         </label>
//         <div id="no-cust-info" class="muted small"></div>
//       </div>
//       <div id="no-cust-new" hidden>
//         <div class="row">
//           <label>Name<input data-nc="name" /></label>
//           <label>Contact<input data-nc="contactName" /></label>
//         </div>
//         <div class="row">
//           <label>Email<input data-nc="email" /></label>
//           <label>Phone<input data-nc="phone" /></label>
//         </div>
//         <div class="row-3">
//           <label>Address<input data-nc="address" /></label>
//           <label>City<input data-nc="city" /></label>
//           <label>Country<input data-nc="country" /></label>
//         </div>
//       </div>
//       <div class="row">
//         <label>Product<select id="no-sku">${inventoryProducts.map(p=>`<option value="${p.sku}">${p.sku} — ${escapeHtml(p.product)}</option>`).join("")}</select></label>
//         <label>Quantity<input id="no-qty" type="number" min="1" value="1" /></label>
//       </div>
//       <label>Payment<select id="no-pay">${paymentMethods.map(p=>`<option>${p}</option>`).join("")}</select></label>
//       <div id="no-err"></div>
//     `,
//     confirmLabel: "Create order",
//     onMount: () => {
//       const showInfo = () => {
//         const c = customers.find(x => x.id === $("#no-cust").value);
//         $("#no-cust-info").innerHTML = c ? `${escapeHtml(c.contactName)} · ${escapeHtml(c.email)} · ${escapeHtml(c.address)}, ${escapeHtml(c.city)}` : "";
//       };
//       showInfo();
//       $("#no-cust").addEventListener("change", showInfo);
//       $("#no-newcust").addEventListener("change", e => {
//         isNewCustomer = e.target.checked;
//         $("#no-cust-existing").hidden = isNewCustomer;
//         $("#no-cust-new").hidden = !isNewCustomer;
//       });
//     },
//     onConfirm: () => {
//       let cust;
//       if (isNewCustomer) {
//         cust = { id: uid("CU"), notes: "" };
//         $$("[data-nc]").forEach(i => cust[i.dataset.nc] = i.value.trim());
//         if (!cust.name) { $("#no-err").innerHTML = `<div class="alert err">Name required.</div>`; return false; }
//         customers.push(cust);
//       } else {
//         cust = customers.find(c => c.id === $("#no-cust").value);
//       }
//       const sku = $("#no-sku").value;
//       const qty = Math.max(1, +$("#no-qty").value);
//       const product = inventoryProducts.find(p => p.sku === sku);
//       const payment = $("#no-pay").value;
//       const status = payment === "Paid" ? "Delivered" : "Draft";
//       const newOrder = {
//         id: `SO-2026-${String(143 + orders.length).padStart(4,"0")}`,
//         customer: cust.name, customerId: cust.id, owner: state.user.name,
//         value: product.unitPrice * qty,
//         status, orderDate: new Date().toISOString().slice(0,10),
//         payment, address: `${cust.address}, ${cust.city}`,
//         items: [{ sku, name: product.product, quantity: qty }],
//         trackingNumber: "", carrier: "", notes: "",
//       };
//       orders.unshift(newOrder);
//       closeModal(); render();
//     },
//   });
// }

// // ---------- MODAL ----------
// function showModal({ title, body, confirmLabel="OK", onConfirm, onCancel, onMount }) {
//   const root = $("#modal-root");
//   root.innerHTML = `<div class="modal-backdrop">
//     <div class="modal" role="dialog">
//       <div class="modal-header"><h3 style="margin:0">${escapeHtml(title)}</h3>
//         <button class="btn btn-quiet" data-x>&times;</button></div>
//       <div class="modal-body">${body}</div>
//       <div class="modal-footer">
//         <button class="btn" data-cancel>Cancel</button>
//         <button class="btn btn-primary" data-ok>${escapeHtml(confirmLabel)}</button>
//       </div>
//     </div>
//   </div>`;
//   const close = () => { closeModal(); onCancel?.(); };
//   $("[data-x]", root).addEventListener("click", close);
//   $("[data-cancel]", root).addEventListener("click", close);
//   $("[data-ok]", root).addEventListener("click", () => onConfirm?.());
//   onMount?.(root);
// }
// function closeModal() { $("#modal-root").innerHTML = ""; }

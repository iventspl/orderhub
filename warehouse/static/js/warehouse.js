'use strict';

function showFlash(message, isSuccess = true) {
	const content = document.getElementById('content');
	if (!content || !message) return;
	const existing = content.querySelector('.ajax-flash');
	if (existing) existing.remove();
	const el = document.createElement('div');
	el.className = `alert active ajax-flash ${isSuccess ? 'ok' : 'err'}`;
	el.textContent = message;
	content.prepend(el);
	setTimeout(() => el.remove(), 5000);
}

function getCookie(name) {
	let cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		const cookies = document.cookie.split(';');
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

class Warehouse {
	#tableBody = document.querySelector('#section-warehouse tbody');
	#warehouseSelect = document.getElementById('wh-pick');
	#warehousesMap = {};
	#detailsModal = null;

	constructor() {
		const mapScript = document.getElementById('warehouse-map');
		if (mapScript?.textContent) {
			try {
				this.#warehousesMap = JSON.parse(mapScript.textContent);
			} catch (_error) {
				this.#warehousesMap = {};
			}
		}

		if (!this.#tableBody) {
			return;
		}

		this.#tableBody.addEventListener('click', (event) => {
			const detailsBtn = event.target.closest('.wh-details-btn');
			if (!detailsBtn) {
				return;
			}

			const warehouseId = detailsBtn.dataset.warehouseId;
			if (!warehouseId) {
				return;
			}

			this.openDetailsModal(warehouseId);
		});

		if (!this.#warehouseSelect) {
			return;
		}

		this.#warehouseSelect.addEventListener('change', async () => {
			const selectedValue = this.#warehouseSelect.value;
			try {
				const response = await fetch('/warehouse/types/', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'X-CSRFToken': getCookie('csrftoken'),
					},
					body: JSON.stringify({ warehouse_type: selectedValue.toUpperCase() }),
				});

				if (response.redirected) {
					window.location.assign(response.url);
					return;
				}

				if (!response.ok) {
					return;
				}

				const payload = await response.json();
				if (payload?.redirect_url) {
					window.location.assign(payload.redirect_url);
				}
			} catch (_error) {
				// ignore
			}
		});
	}

	escapeHtml(value) {
		const text = value == null ? '' : String(value);
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#39;');
	}

	showFlashMessage(message, isSuccess = true) {
		showFlash(message, isSuccess);
	}

	openDetailsModal(warehouseId) {
		const warehouse = this.#warehousesMap[String(warehouseId)];
		if (!warehouse) {
			return;
		}

		if (this.#detailsModal) {
			this.#detailsModal.remove();
		}

		const modalId = `warehouse-details-modal-${warehouseId}`;
		const productRows = warehouse.products.map((product) => `
			<tr data-product-id="${product.id}">
				<td>${this.escapeHtml(product.sku)}</td>
				<td>${this.escapeHtml(product.name)}</td>
				<td>
					<input type="number" value="${product.reserved_quantity}" readonly />
				</td>
				<td>
					<input class="warehouse-stock-input" type="number" min="0" value="${product.stock_quantity}" readonly />
				</td>
				<td>
					<button class="btn btn-sm btn-danger warehouse-delete-product" type="button" disabled>Delete</button>
				</td>
			</tr>
		`).join('');

		const html = `
			<div id="${modalId}" class="modal-backdrop hidden">
				<div class="modal" role="dialog" aria-modal="true" aria-labelledby="warehouse-details-title-${warehouseId}">
					<div class="modal-header">
						<h3 id="warehouse-details-title-${warehouseId}" style="margin:0">${this.escapeHtml(warehouse.name)} details</h3>
						<div style="display:flex; gap:5px; align-items:center;">
							<button class="btn btn-quiet warehouse-lock-btn" type="button" style="width:32px;height:32px;padding:0;display:flex;align-items:center;justify-content:center;line-height:1" aria-label="Unlock edit mode" title="Unlock edit mode">🔒</button>
							<button class="btn btn-quiet" type="button" style="width:32px;height:32px;padding:0;display:flex;align-items:center;justify-content:center;line-height:1" onclick="closeModal('${modalId}')">&times;</button>
						</div>
					</div>
					<div class="modal-body">
						<div class="row-3">
							<label>
								Address
								<input type="text" value="${this.escapeHtml(warehouse.address)}" readonly />
							</label>
							<label>
								City
								<input type="text" value="${this.escapeHtml(warehouse.city)}" readonly />
							</label>
							<label>
								Country
								<input type="text" value="${this.escapeHtml(warehouse.country)}" readonly />
							</label>
						</div>
						<div class="row-3">
							<label>
								Zip code
								<input type="text" value="${this.escapeHtml(warehouse.zip_code)}" readonly />
							</label>
							<label>
								Capacity usage
								<input type="text" value="${this.escapeHtml(warehouse.capacity_usage)}" readonly />
							</label>
							<label>
								Active zones
								<input type="text" value="${this.escapeHtml(warehouse.active_zones)}" readonly />
							</label>
						</div>
						<label>Products currently assigned</label>
						<div class="modal-scroll">
							<table>
								<thead>
									<tr>
										<th>SKU</th>
										<th>Product</th>
										<th>Reserved</th>
										<th>Stock</th>
										<th></th>
									</tr>
								</thead>
								<tbody>
									${productRows || '<tr><td colspan="5" class="muted small">No products in this warehouse.</td></tr>'}
								</tbody>
							</table>
						</div>
						<label>
							Internal notes
							<textarea class="warehouse-notes" rows="3" readonly>${this.escapeHtml(warehouse.notes)}</textarea>
						</label>
					</div>
					<div class="modal-footer">
						<button class="btn" type="button" onclick="closeModal('${modalId}')">Close</button>
						<button class="btn btn-primary warehouse-save-btn" type="button" disabled>Save changes</button>
					</div>
				</div>
			</div>
		`;

		document.body.insertAdjacentHTML('beforeend', html);
		this.#detailsModal = document.getElementById(modalId);
		openModal(modalId);
		this.bindModalActions(warehouseId, this.#detailsModal);
	}

	bindModalActions(warehouseId, modal) {
		const lockBtn = modal.querySelector('.warehouse-lock-btn');
		const saveBtn = modal.querySelector('.warehouse-save-btn');
		const notesInput = modal.querySelector('.warehouse-notes');
		const stockInputs = modal.querySelectorAll('.warehouse-stock-input');

		lockBtn.addEventListener('click', () => {
			const isLocked = lockBtn.textContent === '🔒';
			if (isLocked) {
				lockBtn.textContent = '🔓';
				notesInput.removeAttribute('readonly');
				stockInputs.forEach((input) => input.removeAttribute('readonly'));
				modal.querySelectorAll('.warehouse-delete-product').forEach((button) => button.removeAttribute('disabled'));
				saveBtn.removeAttribute('disabled');
			} else {
				lockBtn.textContent = '🔒';
				notesInput.setAttribute('readonly', '');
				stockInputs.forEach((input) => input.setAttribute('readonly', ''));
				modal.querySelectorAll('.warehouse-delete-product').forEach((button) => button.setAttribute('disabled', ''));
				saveBtn.setAttribute('disabled', '');
			}
		});

		saveBtn.addEventListener('click', async () => {
			const products = [];
			modal.querySelectorAll('tbody tr[data-product-id]').forEach((row) => {
				const stockInput = row.querySelector('.warehouse-stock-input');
				products.push({
					id: Number(row.dataset.productId),
					stock_quantity: stockInput ? stockInput.value : '0',
				});
			});

			const payload = {
				notes: notesInput.value,
				products,
			};

			try {
				const response = await fetch(`/warehouse/${warehouseId}/edit/`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'X-CSRFToken': getCookie('csrftoken'),
					},
					body: JSON.stringify(payload),
				});

				const result = await response.json();
				if (!response.ok) {
					throw new Error(result?.error || 'Failed to update warehouse.');
				}

				this.#warehousesMap[String(warehouseId)] = result.warehouse;
				closeModal(modal.id);
				this.showFlashMessage(result?.message || 'Warehouse updated successfully.');
			} catch (error) {
				console.error('Error updating warehouse:', error);
				this.showFlashMessage(error.message || 'Error updating warehouse.', false);
			}
		});

		modal.addEventListener('click', async (event) => {
			const deleteBtn = event.target.closest('.warehouse-delete-product');
			if (!deleteBtn) {
				return;
			}

			const row = deleteBtn.closest('tr[data-product-id]');
			if (!row) {
				return;
			}

			const productId = row.dataset.productId;
			const sku = row.querySelector('td')?.textContent || '';
			const shouldDelete = window.confirm(`Delete product ${sku} from this warehouse?`);
			if (!shouldDelete) {
				return;
			}

			try {
				const response = await fetch(`/warehouse/${warehouseId}/product/${productId}/delete/`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'X-CSRFToken': getCookie('csrftoken'),
					},
				});
				const result = await response.json();
				if (!response.ok) {
					throw new Error(result?.error || 'Failed to delete product.');
				}

				row.remove();
				const warehouse = this.#warehousesMap[String(warehouseId)];
				if (warehouse) {
					warehouse.products = warehouse.products.filter((p) => String(p.id) !== String(productId));
				}
				this.showFlashMessage(result?.message || 'Product deleted from warehouse.');
			} catch (error) {
				console.error('Error deleting warehouse product:', error);
				this.showFlashMessage(error.message || 'Error deleting product.', false);
			}
		});
	}
}

new Warehouse();


class WarehouseDetail {
	#section = document.getElementById('section-warehouse-detail');
	#lockBtn   = document.getElementById('wh-lock-btn');
	#saveBtn   = document.getElementById('wh-save-btn');
	#deleteBtn = document.getElementById('wh-delete-btn');
	#paginationRows = document.querySelector('.pagination-rows');
	#warehouseId = null;
	#locked = true;

	constructor() {
		if (!this.#section) return;

		this.#warehouseId = this.#section.dataset.warehouseId;

		this.#paginationRows?.addEventListener('change', (e) => {
			const params = new URLSearchParams(window.location.search);
			params.set('rows', e.target.value);
			params.set('page', '1');
			window.location.search = params.toString();
		});

		// Sort on header click — toggle dir if same column, default asc for new column
		this.#section.querySelectorAll('th[data-sort]').forEach(th => {
			th.addEventListener('click', () => {
				const params = new URLSearchParams(window.location.search);
				const field = th.dataset.sort;
				const currentSort = params.get('sort');
				const currentDir  = params.get('dir') || 'asc';
				params.set('sort', field);
				params.set('dir', currentSort === field && currentDir === 'asc' ? 'desc' : 'asc');
				params.set('page', '1');
				window.location.search = params.toString();
			});
		});

		// Search — debounced, resets to page 1
		const searchInput = document.getElementById('wh-product-search');
		let searchTimer = null;
		searchInput?.addEventListener('input', (e) => {
			clearTimeout(searchTimer);
			searchTimer = setTimeout(() => {
				const params = new URLSearchParams(window.location.search);
				if (e.target.value.trim()) {
					params.set('search', e.target.value.trim());
				} else {
					params.delete('search');
				}
				params.set('page', '1');
				window.location.search = params.toString();
			}, 400);
		});

		this.#lockBtn?.addEventListener('click', () => {
			this.#locked = !this.#locked;
			this._setEditMode(!this.#locked);
		});

		this.#saveBtn?.addEventListener('click', () => this._save());

		this.#deleteBtn?.addEventListener('click', () => this._deleteWarehouse());

		this.#section.addEventListener('click', async (e) => {
			const deleteBtn = e.target.closest('.warehouse-delete-product');
			if (!deleteBtn || this.#locked) return;

			const row = deleteBtn.closest('tr[data-product-id]');
			if (!row) return;

			const productId = row.dataset.productId;
			const sku = row.querySelector('td')?.textContent.trim() || '';
			if (!confirm(`Delete product ${sku} from this warehouse?`)) return;

			try {
				const response = await fetch(`/warehouse/${this.#warehouseId}/product/${productId}/delete/`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
				});
				const result = await response.json();
				if (!response.ok) throw new Error(result?.error || 'Failed to delete product.');
				row.remove();
				showFlash(result?.message || 'Product deleted.');
			} catch (error) {
				showFlash(error.message || 'Error deleting product.', false);
			}
		});
	}

	_setEditMode(editable) {
		this.#lockBtn.textContent = editable ? '🔓 Edit' : '🔒 Edit';
		this.#saveBtn.disabled = !editable;
		if (this.#deleteBtn) this.#deleteBtn.hidden = !editable;
		this.#section.querySelectorAll('.wh-editable').forEach(el => {
			if (editable) el.removeAttribute('readonly');
			else el.setAttribute('readonly', '');
		});
		this.#section.querySelectorAll('.warehouse-delete-product').forEach(btn => {
			btn.disabled = !editable;
		});
	}

	async _deleteWarehouse() {
		const name = this.#section.querySelector('h3')?.textContent.trim() || 'this warehouse';
		if (!confirm(`Permanently delete "${name}"? This cannot be undone.`)) return;

		try {
			const response = await fetch(`/warehouse/${this.#warehouseId}/delete/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
			});
			const result = await response.json();
			if (!response.ok) throw new Error(result?.error || 'Failed to delete warehouse.');
			showFlash(result?.message || 'Warehouse deleted.');
			setTimeout(() => { window.location.href = '/warehouse/'; }, 1200);
		} catch (error) {
			showFlash(error.message || 'Error deleting warehouse.', false);
		}
	}

	async _save() {
		const products = [];
		this.#section.querySelectorAll('tbody tr[data-product-id]').forEach(row => {
			const stockInput = row.querySelector('.warehouse-stock-input');
			products.push({ id: Number(row.dataset.productId), stock_quantity: stockInput?.value || '0' });
		});

		const notes = this.#section.querySelector('.warehouse-notes')?.value || '';

		try {
			const response = await fetch(`/warehouse/${this.#warehouseId}/edit/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
				body: JSON.stringify({ notes, products }),
			});
			const result = await response.json();
			if (!response.ok) throw new Error(result?.error || 'Failed to save.');
			this.#locked = true;
			this._setEditMode(false);
			showFlash(result?.message || 'Warehouse updated successfully.');
		} catch (error) {
			showFlash(error.message || 'Error saving.', false);
		}
	}
}

new WarehouseDetail();


class TransferModal {
	#fromSelect     = document.getElementById('id_source_warehouse');
	#container      = document.getElementById('tr-items-container');
	#addBtn         = document.getElementById('tr-add-product');
	#totalForms     = document.getElementById('id_transfer_products-TOTAL_FORMS');

	#timers = {};   // rowIndex → debounce timer id

	constructor() {
		if (!this.#fromSelect) return;

		this.#fromSelect.addEventListener('change', () => this._onWarehouseChange());
		this.#addBtn?.addEventListener('click', () => this._addRow());

		// Delegated: search input typing
		this.#container.addEventListener('input', (e) => {
			const input = e.target.closest('.tr-search-input');
			if (!input) return;
			this._onInput(input.closest('.tr-product-row'), input);
		});

		// Delegated: clear button, remove button
		this.#container.addEventListener('click', (e) => {
			if (e.target.closest('.tr-search-clear')) {
				this._clearRow(e.target.closest('.tr-product-row'));
				return;
			}
			if (e.target.closest('.tr-remove-row')) {
				this._removeRow(e.target.closest('.tr-product-row'));
			}
		});

		// Close all dropdowns on outside click
		document.addEventListener('click', (e) => {
			if (!e.target.closest('.tr-product-row')) this._closeAllResults();
		});
	}

	// ── warehouse change ─────────────────────────────────────────────

	_onWarehouseChange() {
		const enabled = !!this.#fromSelect.value;
		this.#container.querySelectorAll('.tr-product-row').forEach(row => {
			this._clearRow(row);
			const inp = row.querySelector('.tr-search-input');
			inp.disabled    = !enabled;
			inp.placeholder = enabled ? 'Search product by name or SKU…' : 'Select a source warehouse first…';
		});
	}

	// ── search per row ───────────────────────────────────────────────

	_onInput(row, input) {
		const idx = row.dataset.index;
		const q   = input.value.trim();

		// If user edits after selecting, clear the hidden product id
		row.querySelector('.tr-product-id-input').value = '';
		row.querySelector('.tr-search-clear').classList.toggle('hidden', q.length === 0);

		clearTimeout(this.#timers[idx]);
		if (q.length < 2) { this._closeResults(row); return; }

		this.#timers[idx] = setTimeout(() => this._fetch(row, q), 300);
	}

	async _fetch(row, q) {
		const warehouseId = this.#fromSelect.value;
		if (!warehouseId) return;
		try {
			const res  = await fetch(`/transfers/api/get-products/${warehouseId}/?q=${encodeURIComponent(q)}`);
			const data = await res.json();
			this._renderResults(row, data);
		} catch {
			this._closeResults(row);
		}
	}

	_renderResults(row, products) {
		const box = row.querySelector('.tr-search-results');
		box.innerHTML = '';

		if (!products.length) {
			box.innerHTML = '<div class="tr-no-results">No products found</div>';
			box.classList.remove('hidden');
			return;
		}

		products.forEach(p => {
			const qty   = p.stock_quantity ?? 0;
			const cls   = qty === 0 ? 'zero' : qty < 5 ? 'low' : '';
			const label = qty === 0 ? 'Out of stock' : `${qty} in stock`;
			const item  = document.createElement('div');
			item.className = 'tr-result-item';
			item.innerHTML = `
				<div class="tr-result-info">
					<span class="tr-result-name">${this._esc(p.name)}</span>
					<span class="tr-result-sku">SKU: ${this._esc(p.sku)}</span>
				</div>
				<span class="tr-result-stock ${cls}">${label}</span>
			`;
			item.addEventListener('mousedown', (e) => {
				e.preventDefault();   // keep focus on input so blur doesn't close before click
				this._select(row, p);
			});
			box.appendChild(item);
		});

		box.classList.remove('hidden');
	}

	_select(row, product) {
		row.querySelector('.tr-product-id-input').value = product.id;
		row.querySelector('.tr-search-input').value     = `${product.name} (${product.sku})`;
		row.querySelector('.tr-search-clear').classList.remove('hidden');
		this._closeResults(row);
	}

	// ── row management ───────────────────────────────────────────────

	_addRow() {
		const rows = this.#container.querySelectorAll('.tr-product-row');
		const idx  = rows.length;
		const enabled = !!this.#fromSelect.value;

		const div = document.createElement('div');
		div.className    = 'tr-product-row';
		div.dataset.index = idx;
		div.innerHTML = `
			<div class="tr-search-product">
				<input type="text" class="tr-search-input"
				       placeholder="${enabled ? 'Search product by name or SKU…' : 'Select a source warehouse first…'}"
				       autocomplete="off" ${enabled ? '' : 'disabled'} />
				<button type="button" class="tr-search-clear hidden" title="Clear">&times;</button>
				<div class="tr-search-results hidden"></div>
			</div>
			<input type="hidden" name="transfer_products-${idx}-product" class="tr-product-id-input" />
			<input type="number" name="transfer_products-${idx}-quantity" class="tr-qty-input"
			       min="1" step="1" placeholder="Qty" />
			<button type="button" class="btn btn-sm btn-quiet tr-remove-row" title="Remove row">&times;</button>
		`;
		this.#container.appendChild(div);
		this.#totalForms.value = idx + 1;
		div.querySelector('.tr-search-input').focus();
	}

	_removeRow(row) {
		const rows = this.#container.querySelectorAll('.tr-product-row');
		if (rows.length <= 1) { this._clearRow(row); return; }
		row.remove();
		this._reindex();
	}

	_reindex() {
		this.#container.querySelectorAll('.tr-product-row').forEach((row, i) => {
			row.dataset.index = i;
			row.querySelector('.tr-product-id-input').name = `transfer_products-${i}-product`;
			row.querySelector('.tr-qty-input').name        = `transfer_products-${i}-quantity`;
		});
		this.#totalForms.value = this.#container.querySelectorAll('.tr-product-row').length;
	}

	_clearRow(row) {
		row.querySelector('.tr-product-id-input').value = '';
		row.querySelector('.tr-search-input').value     = '';
		row.querySelector('.tr-qty-input').value        = '';
		row.querySelector('.tr-search-clear').classList.add('hidden');
		this._closeResults(row);
	}

	_closeResults(row) {
		const box = row.querySelector('.tr-search-results');
		box.innerHTML = '';
		box.classList.add('hidden');
	}

	_closeAllResults() {
		this.#container.querySelectorAll('.tr-search-results').forEach(box => {
			box.innerHTML = '';
			box.classList.add('hidden');
		});
	}

	_esc(str) {
		return String(str ?? '')
			.replace(/&/g, '&amp;').replace(/</g, '&lt;')
			.replace(/>/g, '&gt;').replace(/"/g, '&quot;');
	}
}

new TransferModal();

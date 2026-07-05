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
	#lockBtn = document.getElementById('wh-lock-btn');
	#saveBtn = document.getElementById('wh-save-btn');
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
		this.#section.querySelectorAll('.wh-editable').forEach(el => {
			if (editable) el.removeAttribute('readonly');
			else el.setAttribute('readonly', '');
		});
		this.#section.querySelectorAll('.warehouse-delete-product').forEach(btn => {
			btn.disabled = !editable;
		});
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

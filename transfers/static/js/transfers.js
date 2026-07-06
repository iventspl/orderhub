'use strict';

class TransferModal {
	#fromSelect = document.getElementById('id_source_warehouse');
	#container  = document.getElementById('tr-items-container');
	#addBtn     = document.getElementById('tr-add-product');
	#totalForms = document.getElementById('id_transfer_products-TOTAL_FORMS');

	#timers = {};

	constructor() {
		if (!this.#fromSelect) return;

		this.#fromSelect.addEventListener('change', () => this._onWarehouseChange());
		this.#addBtn?.addEventListener('click', () => this._addRow());

		this.#container.addEventListener('input', (e) => {
			const input = e.target.closest('.tr-search-input');
			if (!input) return;
			this._onInput(input.closest('.tr-product-row'), input);
		});

		this.#container.addEventListener('click', (e) => {
			if (e.target.closest('.tr-search-clear')) {
				this._clearRow(e.target.closest('.tr-product-row'));
				return;
			}
			if (e.target.closest('.tr-remove-row')) {
				this._removeRow(e.target.closest('.tr-product-row'));
			}
		});

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
				e.preventDefault();
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
		const rows    = this.#container.querySelectorAll('.tr-product-row');
		const idx     = rows.length;
		const enabled = !!this.#fromSelect.value;

		const div = document.createElement('div');
		div.className     = 'tr-product-row';
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

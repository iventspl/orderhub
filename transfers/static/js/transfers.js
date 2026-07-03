class Transfers {
    #transferForm = document.getElementById('transfer-form');
    #sourceWarehouseSelect = document.getElementById('id_source_warehouse');
    #productSelect = document.getElementById('id_product');
    #addProductButton = document.getElementById('add-product-btn');
    #itemsContainer = document.getElementById('transfer-items-container');
    #emptyItemTemplate = document.getElementById('empty-item-form-template');
    #totalFormsInput = document.getElementById('id_transfer_products-TOTAL_FORMS');
    #products = [];

    constructor() {
        if (!this.#transferForm || !this.#sourceWarehouseSelect || !this.#productSelect || !this.#totalFormsInput) {
            return;
        }

        this.#totalFormsInput.value = this.#itemsContainer.querySelectorAll('.transfer-item-row').length;

        this.#sourceWarehouseSelect.addEventListener('change', e => {
            const warehouseId = e.target.value;
            this.updateProductOptions(warehouseId);
        });

        this.#addProductButton?.addEventListener('click', () => {
            this.addProductRow();
        });

        this.#itemsContainer?.addEventListener('click', event => {
            const removeButton = event.target.closest('.remove-transfer-item-btn');
            if (!removeButton) {
                return;
            }

            const row = removeButton.closest('.transfer-item-row');
            row?.remove();
            this.syncTotalForms();
        });

        if (this.#sourceWarehouseSelect.value) {
            this.updateProductOptions(this.#sourceWarehouseSelect.value);
        }
    }

    updateProductOptions(warehouseId) {
        if (!warehouseId) {
            this.#products = [];
            this.populateAllProductSelects([]);
            return;
        }

        (async () => {
            try {
                const response = await fetch(`/transfers/api/get-products/${warehouseId}/`);
                if (!response.ok) {
                    throw new Error('Failed to fetch products for the selected warehouse.');
                }
                this.#products = await response.json();
                this.populateAllProductSelects(this.#products);
            } catch (error) {
                console.error('Error fetching products:', error);
                this.#products = [];
                this.populateAllProductSelects([]);
            }
        })();
    }

    populateAllProductSelects(products) {
        this.getProductSelects().forEach(select => {
            const currentValue = select.value;
            this.populateProductSelect(select, products, currentValue);
        });
    }

    populateProductSelect(select, products, selectedValue = '') {
        select.innerHTML = '<option value="">---------</option>';
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} (SKU: ${product.sku}, Stock: ${product.stock_quantity})`;
            if (String(product.id) === String(selectedValue)) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    addProductRow() {
        if (!this.#emptyItemTemplate || !this.#itemsContainer) {
            return;
        }

        const nextIndex = this.#itemsContainer.querySelectorAll('.transfer-item-row').length;
        const html = this.#emptyItemTemplate.innerHTML.replaceAll('__prefix__', String(nextIndex));
        this.#itemsContainer.insertAdjacentHTML('beforeend', html);
        this.syncTotalForms();

        const rows = this.#itemsContainer.querySelectorAll('.transfer-item-row');
        const newRow = rows[rows.length - 1];
        const select = newRow?.querySelector('select[name$="-product"]');
        if (select) {
            this.populateProductSelect(select, this.#products, '');
        }
    }

    syncTotalForms() {
        if (!this.#totalFormsInput || !this.#itemsContainer) {
            return;
        }

        const rows = Array.from(this.#itemsContainer.querySelectorAll('.transfer-item-row'));
        rows.forEach((row, index) => {
            row.querySelectorAll('[name], [id], label').forEach(element => {
                if (element.name) {
                    element.name = element.name.replace(/transfer_products-\d+-/, `transfer_products-${index}-`);
                }
                if (element.id) {
                    element.id = element.id.replace(/id_transfer_products-\d+-/, `id_transfer_products-${index}-`);
                }
                if (element.htmlFor) {
                    element.htmlFor = element.htmlFor.replace(/id_transfer_products-\d+-/, `id_transfer_products-${index}-`);
                }
            });
        });
        this.#totalFormsInput.value = rows.length;
    }

    getProductSelects() {
        const extraSelects = this.#itemsContainer
            ? Array.from(this.#itemsContainer.querySelectorAll('select[name$="-product"]'))
            : [];
        return [this.#productSelect, ...extraSelects].filter(Boolean);
    }
}

new Transfers();
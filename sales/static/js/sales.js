'use strict';

// Helper function to get CSRF token from cookies (needed for POST requests in Django)
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



function showToast(message, type = 'success') {
    const toast = document.createElement('div')
    toast.className = `alert active ${type === 'error' ? 'err' : 'ok'}`
    toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:260px;max-width:420px;'
    toast.textContent = message
    document.body.appendChild(toast)
    setTimeout(() => toast.remove(), 4000)
}


// Simple modal handling functions

function toggleCustomerForm(){
    const checkbox = document.querySelector('input[name="is_new_customer"]');
    const newCustomerForm = document.querySelector('.modal-new-customer');

    checkbox.addEventListener('change', function() {
        if (this.checked) {
            newCustomerForm.classList.add('active');
        } else {
            newCustomerForm.classList.remove('active');
        }
    });
}


document.addEventListener('DOMContentLoaded', () => {
  const addBtn = document.getElementById('add-product-btn');
  if (!addBtn) return;

  const itemsContainer = document.getElementById('order-items');
  const template = document.getElementById('empty-item-form-template');
    if (!itemsContainer || !template) return;

  // Znajdź TOTAL_FORMS wewnątrz tego formularza
  const form = addBtn.closest('form');
    if (!form) return;
  const totalFormsInput = form.querySelector('input[name$="-TOTAL_FORMS"]');
    if (!totalFormsInput) return;

    function reindexFormRows() {
        const rows = itemsContainer.querySelectorAll('.order-item-row');
        rows.forEach((row, index) => {
            row.querySelectorAll('[name]').forEach((field) => {
                field.name = field.name.replace(/-(\d+)-/g, `-${index}-`);
            });
            row.querySelectorAll('[id]').forEach((field) => {
                field.id = field.id.replace(/-(\d+)-/g, `-${index}-`);
            });
            row.querySelectorAll('label[for]').forEach((label) => {
                label.htmlFor = label.htmlFor.replace(/-(\d+)-/g, `-${index}-`);
            });
        });
        totalFormsInput.value = rows.length;
    }

  addBtn.addEventListener('click', () => {
    const currentIndex = parseInt(totalFormsInput.value, 10);

    // Pobierz HTML template i podmień __prefix__
    const html = template.innerHTML.replace(/__prefix__/g, currentIndex);

    // Dodaj nowy formularz do kontenera
    itemsContainer.insertAdjacentHTML('beforeend', html);

    // Zwiększ TOTAL_FORMS
    totalFormsInput.value = currentIndex + 1;
  });

    itemsContainer.addEventListener('click', (event) => {
        const removeBtn = event.target.closest('.remove-order-item-btn');
        if (!removeBtn) return;

        const row = removeBtn.closest('.order-item-row');
        if (!row) return;

        row.remove();
        reindexFormRows();
    });
});


// testing rest_framework 
// document.querySelector('#order-modal').addEventListener('click', async (e)=>{
//     try{
//         const response = await fetch('/api/sales-orders/');
//         const data = await response.json();
//         console.log('Sales orders data:', data);
//     }catch(error){
//         console.error('Error fetching sales orders:', error);
//     }
// });

class SalesApp{
    #search = document.getElementById('o-search');
    #searchProduct = document.getElementById('search_product');
    #searchResultsContainer = document.getElementById('search_results');
    #searchClearBtn = document.getElementById('search_product-clear');
    #byStatus = document.querySelector('#o-status');
    #statusFilters = document.querySelector('.filters');
    #resetBtn = document.getElementById('reset-filters');
    #salesBody = document.querySelector('.orders-container')
    #rows = document.querySelectorAll('tr.clickable')
    #expandedRows = document.querySelectorAll('tr.expand-row')
    #paginationRows = document.querySelector('.pagination-rows')
    #ship_to_select = document.getElementById('id_ship_to')
    #editModal = null;
    #orderItemsMap = {}
    #customerAddressMap = {}
    constructor(){
        this._restoreControlsFromUrl();
        const itemsMapScript = document.getElementById('order-items-map')
        if (itemsMapScript?.textContent) {
            try {
                this.#orderItemsMap = JSON.parse(itemsMapScript.textContent)
            } catch (_error) {
                this.#orderItemsMap = {}
            }
        }

        const addrMapScript = document.getElementById('customer-address-map')
        if (addrMapScript?.textContent) {
            try {
                this.#customerAddressMap = JSON.parse(addrMapScript.textContent)
            } catch (_error) {
                this.#customerAddressMap = {}
            }
        }

        document.getElementById('use-customer-address')?.addEventListener('change', (e) => {
            if (!e.target.checked) return
            const customerId = document.getElementById('id_customer')?.value
            const addr = this.#customerAddressMap[customerId]
            if (!addr) return
            const form = document.getElementById('order-modal')
            const fill = (nc, val) => {
                const el = form?.querySelector(`[data-nc="${nc}"]`)
                if (el) el.value = val
            }
            fill('shipFirstName', addr.firstName)
            fill('shipLastName',  addr.lastName)
            fill('shipEmail',     addr.email)
            fill('shipPhone',     addr.phone)
            fill('shipAddress',   addr.address)
            fill('shipZipCode',   addr.zipCode)
            fill('shipCity',      addr.city)
            fill('shipState',     addr.state)
            fill('shipCountry',   addr.country)
        })

        document.querySelectorAll('[data-sort]').forEach(col => {
            col.addEventListener('click', () => {
                const params = new URLSearchParams(window.location.search)
                const field = col.dataset.sort
                const currentSort = params.get('sort')
                const currentDir  = params.get('dir') || 'asc'
                params.set('sort', field)
                params.set('dir', currentSort === field && currentDir === 'asc' ? 'desc' : 'asc')
                params.set('page', '1')
                window.location.search = params.toString()
            })
        })

        this.#salesBody.addEventListener('click', (e)=>{

            const clickedEditBtn = e.target.closest('.edit-btn')
            if(clickedEditBtn){
                const orderId = clickedEditBtn.dataset.orderId
                const orderStatus = clickedEditBtn.dataset.orderStatus
                const orderCustomer = clickedEditBtn.dataset.customer
                const orderIsEditable = clickedEditBtn.dataset.isEditable
                const orderPayment = clickedEditBtn.dataset.payment
                const orderProducts = this.#orderItemsMap[String(orderId)] || []
                const orderNotes = clickedEditBtn.dataset.notes

                let html = `
                    <div id="order-edit-modal-${orderId}" class="modal-backdrop hidden">
            <div class="modal"
                 role="dialog"
                 aria-modal="true"
                 aria-labelledby="order-edit-title-${orderId}">
                <div class="modal-header">
                    <h3 id="order-edit-title-${orderId}" style="margin:0">Edit order ${orderId}</h3>
                    <div style="display:flex; gap:5px; align-items:center;">
                        <button class="btn btn-quiet sales-order-lock ${orderIsEditable === 'True' ? 'active' : 'disabled'}"
                                type="button"
                                style="width:32px;
                                       height:32px;
                                       padding:0;
                                       display:flex;
                                       align-items:center;
                                       justify-content:center;
                                       line-height:1"
                                data-sales-lock="${orderIsEditable === 'True' ? 'unlock' : 'lock'}"
                                aria-label="Unlock edit mode"
                                title="Unlock edit mode">🔒</button>
                        <button class="btn btn-quiet"
                                type="button"
                                style="width:32px;
                                       height:32px;
                                       padding:0;
                                       display:flex;
                                       align-items:center;
                                       justify-content:center;
                                       line-height:1"
                                onclick="closeModal('order-edit-modal-${orderId}')">&times;</button>
                    </div>
                </div>
                <div class="modal-body">
                    <div class="row-3">
                        <label>
                            Customer
                            <input type="text" value="${orderCustomer}" readonly />
                        </label>
                        <label>
                            Status
                            <select disabled>
                                <option value="DRAFT" ${orderStatus === 'DRAFT' ? 'selected' : ''}>Draft</option>
                                <option value="IN WAREHOUSE" ${orderStatus === 'IN WAREHOUSE' ? 'selected' : ''}>
                                    In warehouse
                                </option>
                                <option value="PACKED" ${orderStatus === 'PACKED' ? 'selected' : ''}>Packed</option>
                                <option value="SHIPPED" ${orderStatus === 'SHIPPED' ? 'selected' : ''}>Shipped</option>
                                <option value="DELIVERED" ${orderStatus === 'DELIVERED' ? 'selected' : ''}>Delivered</option>
                            </select>
                        </label>
                        <label>
                            Payment
                            <input type="text" value="${orderPayment}" readonly />
                        </label>
                    </div>
                    <label>Order items</label>
                    <div class="modal-scroll">
                        <table>
                            <thead>
                                <tr>
                                    <th>SKU</th>
                                    <th>Product</th>
                                    <th>Qty</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${orderProducts.map(item => `
                                    <tr>
                                        <td>${item.sku || '-'}</td>
                                        <td>${item.name}</td>
                                        <td>
                                            <input class="sales-order-qty"
                                                   type="number"
                                                   min="1"
                                                   value="${item.quantity}"
                                                   readonly />
                                        </td>
                                    </tr>
                                    `).join('')}
                                ${orderProducts.length === 0 ? `
                                    <tr>
                                        <td colspan="3" class="muted small">No items in this order.</td>
                                    </tr>
                                    ` : ''}
                            </tbody>
                        </table>
                    </div>
                    <label>
                        Notes
                        <textarea rows="3" readonly>${orderNotes}</textarea>
                    </label>
                </div>
                <div class="modal-footer">
                    <button class="btn sales-order-delete-btn">Delete</button>
                    <button class="btn"
                            type="button"
                            onclick="closeModal('order-edit-modal-${orderId}')">Close</button>
                    <button class="btn btn-primary sales-order-save" type="button" disabled>Save changes</button>
                </div>
            </div>
        </div>
                `
                if(this.#editModal){
                    this.#editModal.remove()
                }
                document.body.insertAdjacentHTML('beforeend', html)
                this.#editModal = document.getElementById(`order-edit-modal-${orderId}`)
                openModal(`order-edit-modal-${orderId}`)

                const orderLockBtn = this.#editModal.querySelector('button.sales-order-lock')
                const orderSaveBtn = this.#editModal.querySelector('button.sales-order-save')
                const orderDeleteBtn = this.#editModal.querySelector('button.sales-order-delete-btn')
                const qtyInputs = this.#editModal.querySelectorAll('.sales-order-qty')
                const statusSelect = this.#editModal.querySelector('select')
                
                if(orderIsEditable === 'True'){
                    orderLockBtn.addEventListener('click', ()=>{
                        const isLocked = orderLockBtn.textContent === '🔒'
                        if(isLocked){
                            orderLockBtn.textContent = '🔓'
                            qtyInputs.forEach(input => input.removeAttribute('readonly'))
                            statusSelect.removeAttribute('disabled')
                            orderSaveBtn.removeAttribute('disabled')
                        } else {
                            orderLockBtn.textContent = '🔒'
                            qtyInputs.forEach(input => input.setAttribute('readonly', ''))
                            statusSelect.setAttribute('disabled', '')
                            orderSaveBtn.setAttribute('disabled', '')
                        }
                    });
                }

                orderSaveBtn.addEventListener('click', ()=>{
                    // here we would collect changed data and send it to backend via fetch/AJAX
                    let data = {
                        order_id: orderId,
                        new_status: statusSelect.value,
                        items: []
                    }
                    qtyInputs.forEach((input, index) => {
                        const sku = input.closest('tr').querySelector('td:first-child').textContent
                        const quantity = input.value
                        data.items.push({sku, quantity})
                    });
                     (async () => {
                        try{
                            const response = await fetch('/sales/edit/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                body: JSON.stringify(data)
                            })
                            const result = await response.json()
                            if(!response.ok){
                                throw new Error(result?.error || 'Network response was not ok')
                            }
                            if(result?.warnings?.length){
                                console.warn('Reservation warnings:', result.warnings)
                            }
                            if(result.ok){
                                closeModal(`order-edit-modal-${orderId}`)
                                window.location.reload()
                            }
                        }catch(error){
                            console.error('Error updating sales order:', error)
                        }
                    })()
                });

                orderDeleteBtn.addEventListener('click', ()=>{
                    if(!confirm('Are you sure you want to delete this order? This action cannot be undone.')) return;
                    (async ()=>{
                        try{
                            const response = await fetch(`/sales/delete/${orderId}/`, {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': getCookie('csrftoken')
                                }
                            })
                            const result = await response.json()
                            if(!response.ok){
                                window.location.reload()
                                return
                            }
                            if(result.ok){
                                closeModal(`order-edit-modal-${orderId}`)
                                window.location.reload()
                            }
                        }catch(error){
                            console.error('Error deleting sales order:', error)
                            window.location.reload()
                        }
                    })()
                });
            }

            const clickedTransitionBtn = e.target.closest('.btn-transition')
            if (clickedTransitionBtn) {
                e.stopPropagation()
                const orderId = clickedTransitionBtn.dataset.orderId
                const action  = clickedTransitionBtn.dataset.action
                if (action === 'assign_courier') {
                    this._showCourierModal(orderId)
                } else {
                    const labels = { approve: 'approve', mark_packed: 'mark as packed', deliver: 'mark as delivered' }
                    if (!confirm(`Are you sure you want to ${labels[action] ?? action} this order?`)) return
                    this._postTransition(orderId, { action })
                }
                return
            }

            const clickedRow = e.target.closest('tr.clickable')
            if(!clickedRow || e.target.closest('tr.expand-row')) return

            const expandedInfo = document.querySelector(`.expand-row[data-id="${clickedRow.dataset.id}"]`)
            const isAlreadyOpen = clickedRow.classList.contains('expanded')

            // close all
            this.#rows.forEach(row => row.classList.remove('expanded'))
            this.#expandedRows.forEach(row => row.classList.remove('active'))

            // if it wasn't open - open it
            if(!isAlreadyOpen){
                clickedRow.classList.add('expanded')
                if(expandedInfo) expandedInfo.classList.add('active')
            }

            
        });

        this.#paginationRows.addEventListener('change', (e)=>{
            this._changeRowsToRender(e.target.value)
        })

        this.#search.addEventListener('keypress' ,(e) =>{
            if(e.key === 'Enter'){
                e.preventDefault();
                this._setQueryParamsAndReload({'search': this.#search.value});
            }
        })


        this.#statusFilters?.addEventListener('click', (e) => {
            const filterBtn = e.target.closest('[data-filter-status]');
            if (!filterBtn) return;
            this._setQueryParamsAndReload({'filter_status': filterBtn.dataset.filterStatus});
        });

        this.#ship_to_select.addEventListener('change', (e)=>{
            const selectedValue = this.#ship_to_select.value;
            const customerShippementAddress = document.getElementById('customer_shippement_addres');
            if(selectedValue === 'CUSTOMER'){
                customerShippementAddress.classList.remove('hidden');
            } else {
                customerShippementAddress.classList.add('hidden');
                const cb = document.getElementById('use-customer-address')
                if (cb) cb.checked = false
            }
        });

        this.#searchClearBtn?.addEventListener('click', () => {
            this.#searchProduct.value = ''
            this.#searchResultsContainer.innerHTML = ''
            this.#searchClearBtn.classList.remove('visible')
            this.#searchProduct.focus()
        })

        this.#searchProduct.addEventListener('input', async (e) => {
            const query = e.target.value.trim()
            this.#searchClearBtn?.classList.toggle('visible', query.length > 0)

            if (query.length < 2) {
                this.#searchResultsContainer.innerHTML = ''
                return
            }

            try {
                const response = await fetch(`/api/products/search/?q=${encodeURIComponent(query)}`)
                if (!response.ok) throw new Error('Network response was not ok')

                const data = await response.json()
                this.#searchResultsContainer.innerHTML = ''

                if (data.length === 0) {
                    this.#searchResultsContainer.innerHTML = '<div class="no-results">No products found</div>'
                    return
                }

                data.forEach(product => {
                    const qty = product.get_total_quantity ?? 0
                    const stockClass = qty === 0 ? 'zero' : qty < 5 ? 'low' : ''
                    const stockLabel = qty === 0 ? 'Out of stock' : `${qty} in stock`
                    const item = document.createElement('div')
                    item.className = 'search-result-item'
                    item.dataset.productId = product.id
                    item.innerHTML = `
                        <div class="search-result-item__info">
                            <span class="search-result-item__name">${product.name}</span>
                            <span class="search-result-item__sku">SKU: ${product.sku}</span>
                        </div>
                        <span class="search-result-item__stock ${stockClass}">${stockLabel}</span>
                    `
                    item.addEventListener('click', () => {
                        this._addProductToForm(product)
                        this.#searchProduct.value = ''
                        this.#searchClearBtn?.classList.remove('visible')
                        this.#searchResultsContainer.innerHTML = ''
                    })
                    this.#searchResultsContainer.appendChild(item)
                })
            } catch (error) {
                console.error('Error searching products:', error)
            }
        })

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search_product')) {
                this.#searchResultsContainer.innerHTML = ''
            }
        })

        this.#resetBtn.addEventListener('click', (e)=>{
            this._setQueryParamsAndReload({
                'search': '',
                'filter_status': '',
                'sort': '',
                'dir': ''
            });
        });
    }

   _addProductToForm(product){
    const itemsContainer = document.getElementById('order-items');
    const template = document.getElementById('empty-item-form-template');
    const totalFormsInput = document.getElementById(
        'id_salesorderitem_set-TOTAL_FORMS'
    );

    const currentIndex = parseInt(totalFormsInput.value, 10);

    const html = template.innerHTML.replace(/__prefix__/g, currentIndex);

    itemsContainer.insertAdjacentHTML('beforeend', html);

    const newRow = itemsContainer.lastElementChild;

    const productSelect = newRow.querySelector(
        'select[name$="-product"]'
    );

    console.log('Product ID:', product.id);
    console.log('Select found:', productSelect);
    console.log(
    [...productSelect.options].map(o => ({
        value: o.value,
        text: o.text
    }))
);

    if (productSelect) {
        productSelect.value = String(product.id);

        console.log(
            'Selected value:',
            productSelect.value
        );
    }

    totalFormsInput.value = currentIndex + 1;
}

    _setQueryParamsAndReload(params) {
        const urlParams = new URLSearchParams(window.location.search);

        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined || value === '') {
                urlParams.delete(key);
            } else {
                urlParams.set(key, value);
            }
        });

        window.location.search = urlParams.toString();
    }

    _restoreSelectValue(select, value){
        if (!select || value === null) return;
        const optionExists = Array.from(select.options).some(option => option.value === value);
        if (optionExists) {
            select.value = value;
        }
    }

    _restoreControlsFromUrl(){
        const urlParams = new URLSearchParams(window.location.search);

        if (this.#search) {
            this.#search.value = urlParams.get('search') || '';
        }

        this._restoreSelectValue(this.#byStatus, urlParams.get('filter_status'));
    }

    _changeRowsToRender(no_rows){
        this._setQueryParamsAndReload({'rows': no_rows, 'page': 1});
    }

    async _postTransition(orderId, payload) {
        try {
            const response = await fetch(`/sales/transition/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(payload),
            })
            const result = await response.json()
            if (!response.ok) throw new Error(result?.error || 'Request failed')
            if (result.ok) window.location.reload()
        } catch (err) {
            showToast(err.message, 'error')
        }
    }

    _showCourierModal(orderId) {
        const modalId = `courier-modal-${orderId}`
        document.getElementById(modalId)?.remove()

        const carriers = [
            ['UPS', 'UPS'], ['FEDEX', 'FedEx'], ['DHL', 'DHL'],
            ['INPOST', 'InPost'], ['GLS', 'GLS'],
            ['POCZTA POLSKA', 'Poczta Polska'], ['OTHER', 'Other'],
        ]
        const carrierOptions = carriers
            .map(([val, label]) => `<option value="${val}">${label}</option>`)
            .join('')

        const html = `
            <div id="${modalId}" class="modal-backdrop hidden">
                <div class="modal" role="dialog" style="max-width:400px">
                    <div class="modal-header">
                        <h3 style="margin:0">Assign Courier</h3>
                        <button class="btn btn-quiet" type="button" onclick="closeModal('${modalId}')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <label>
                            Carrier
                            <select id="${modalId}-carrier">${carrierOptions}</select>
                        </label>
                        <label>
                            Tracking number
                            <input id="${modalId}-tracking" type="text" placeholder="e.g. 1Z999AA10123456784" />
                        </label>
                    </div>
                    <div class="modal-footer">
                        <button class="btn" type="button" onclick="closeModal('${modalId}')">Cancel</button>
                        <button class="btn btn-primary" id="${modalId}-confirm">Assign &amp; Ship</button>
                    </div>
                </div>
            </div>`

        document.body.insertAdjacentHTML('beforeend', html)
        openModal(modalId)

        document.getElementById(`${modalId}-confirm`).addEventListener('click', () => {
            const carrier        = document.getElementById(`${modalId}-carrier`).value
            const trackingNumber = document.getElementById(`${modalId}-tracking`).value.trim()
            if (!trackingNumber) {
                showToast('Tracking number is required.', 'error')
                return
            }
            closeModal(modalId)
            this._postTransition(orderId, { action: 'assign_courier', carrier, tracking_number: trackingNumber })
        })
    }
}

const salesApp = new SalesApp()

class PackingApp {
    #errorTimer = null
    #successTimer = null
    // Referencje do elementów batch action bara i checkboxów
    #packingList   = document.getElementById('packingTable')
    #batchBar      = document.getElementById('packing-batch-bar')
    #batchCount    = document.getElementById('packing-batch-count')
    #startBtn      = document.getElementById('packing-start-btn')
    #selectAll     = document.getElementById('packing-select-all')
    #rows          = document.querySelectorAll('.clickable')
    #expandedRows  = document.querySelectorAll('.expand-row')

    constructor() {
        // ── Tab switching ────────────────────────────────────────────
        document.querySelectorAll('.tab[data-tab]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab[data-tab]').forEach(t => t.classList.remove('active'))
                btn.classList.add('active')
                const target = btn.dataset.tab
                document.getElementById('tab-panel-active').style.display  = target === 'active'  ? '' : 'none'
                document.getElementById('tab-panel-history').style.display = target === 'history' ? '' : 'none'
            })
        })

        // ── Modale skanowania ────────────────────────────────────────
        // Nasłuchujemy na całej sekcji (nie tylko queue), bo przyciski
        // "Scan items" są też w sekcji Packing Progress.
        document.getElementById('section-packing')?.addEventListener('click', (e) => {
            const clickedBtn = e.target.closest('.order-startPacking')
            const clickedRow = e.target.closest('tr[data-order-id]')

            if(clickedBtn){
                const orderId    = clickedBtn.getAttribute('data-order-id')
                const orderStatus = clickedBtn.getAttribute('data-order-status')
                const orderNumber = clickedBtn.getAttribute('data-order-number') || orderId
                const scriptTag  = document.getElementById(`items-data-${orderId}`)
                if (!scriptTag) return
    
                const orderItems = JSON.parse(scriptTag.textContent)
                if (!document.getElementById(`packing-modal-${orderId}`)) {
                    this._openPackingModal(orderId, orderItems, orderStatus, orderNumber)
                } else {
                    openModal(`packing-modal-${orderId}`)
                }
            }

            if(clickedRow && !e.target.closest('button')){
                const orderId = clickedRow.getAttribute('data-order-id')
                const expandedInfo = document.querySelector('.expand-row[data-order-id="'+orderId+'"]')
                const isExpanded = expandedInfo?.classList.contains('active')
                
                this.#rows.forEach(row=>row.classList.remove('expanded'))
                this.#expandedRows.forEach(row=>row.classList.remove('active'))

                if(isExpanded) return
                clickedRow.classList.add('expanded')
                expandedInfo.classList.add('active')
            }
        })

        // ── Checkboxy w kolejce ──────────────────────────────────────
        // Każda zmiana checkboxa aktualizuje licznik i stan batch bara.
        this.#packingList?.addEventListener('change', (e) => {
            if (e.target.classList.contains('packing-checkbox')) {
                this._updateBatchBar()
                // Synchronizuj "Select all" jeśli wszystkie zaznaczone/odznaczone
                const all = document.querySelectorAll('.packing-checkbox')
                const checked = document.querySelectorAll('.packing-checkbox:checked')
                if (this.#selectAll) {
                    this.#selectAll.indeterminate = checked.length > 0 && checked.length < all.length
                    this.#selectAll.checked = checked.length === all.length && all.length > 0
                }
            }
        })

        // ── Select All ───────────────────────────────────────────────
        this.#selectAll?.addEventListener('change', (e) => {
            document.querySelectorAll('.packing-checkbox').forEach(cb => {
                cb.checked = e.target.checked
            })
            this._updateBatchBar()
        })

        // ── Batch "Start packing" ────────────────────────────────────
        // Zbiera zaznaczone IDs → POST /packing/start/ → reload
        this.#startBtn?.addEventListener('click', () => {
            const selected = [...document.querySelectorAll('.packing-checkbox:checked')]
                .map(cb => parseInt(cb.dataset.id, 10))
            if (selected.length) this._startPacking(selected)
        })
    }

    _normalizeStatus(status) {
        return (status || '').toUpperCase()
    }

    _resolveAction(status) {
        const normalizedStatus = this._normalizeStatus(status)
        if (normalizedStatus === 'PACKED') return 'ship'
        if (normalizedStatus === 'SHIPPED') return 'deliver'
        return 'complete'
    }

    _resolveSubmitLabel(action) {
        if (action === 'ship') return 'Ship order'
        if (action === 'deliver') return 'Mark delivered'
        return 'Complete packing'
    }

    _openPackingModal(id, items, status, orderNumber) {
        const action = this._resolveAction(status)
        const normalizedStatus = this._normalizeStatus(status)
        const canScan = action === 'complete'
        const showScanControls = action === 'complete'
        const showItemsTable = action === 'complete' || action === 'ship'
        const showShippingControls = action === 'ship'

        let html = `
            <div id="packing-modal-${id}" class="modal-backdrop hidden">
                <div class="modal" role="dialog">
                    <div class="modal-header">
                        <h3 style="margin:0">Packing station — ${orderNumber} (${normalizedStatus || 'PENDING'})</h3>
                        <button class="btn btn-quiet"
                                onclick="closeModal('packing-modal-${id}')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="packing-form-${id}">
                            ${showScanControls ? `
                                <div class="row">
                                    <label>
                                        Scan / type SKU
                                        <input class="ps-input" placeholder="Scan barcode or SKU" ${canScan ? '' : 'disabled'} />
                                    </label>
                                    <label>
                                        Weight (kg)
                                        <input class="ps-weight" type="number" step="0.01" min="0" />
                                    </label>
                                </div>
                                <div class="alert ok">Scanned Lens kits</div>
                            ` : ''}
                            ${showItemsTable ? `
                                <table>
                                    <thead>
                                        <tr>
                                            <th>SKU</th>
                                            <th>Product</th>
                                            <th>Scanned</th>
                                            <th>Required</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${items.map(item => `
                                            <tr id="s-item-${id}-${item.sku}">
                                                <td>${item.sku}</td>
                                                <td>${item.name}</td>
                                                <td id="s-quantity-scanned-${id}-${item.sku}">${item.scanned_quantity}</td>
                                                <td id="s-quantity-required-${id}-${item.sku}">${item.quantity}</td>
                                            </tr>`).join('')}
                                    </tbody>
                                </table>
                            ` : '<div class="alert ok active">Order is already shipped. Confirm delivery status.</div>'}
                            ${showShippingControls ? `
                                <div class="row">
                                    <label>
                                        Carrier *
                                        <select class="ps-carrier" required>
                                            <option>DHL</option>
                                            <option>UPS</option>
                                            <option>FedEx</option>
                                            <option>DPD</option>
                                            <option>GLS</option>
                                        </select>
                                    </label>
                                    <label>
                                        Tracking number *
                                        <input class="ps-tracking" placeholder="e.g. 1Z999AA10123456784" required />
                                    </label>
                                </div>
                            ` : ''}
                            <div class="alert err"></div>
                            <div class="modal-footer">
                                <button type="button" class="btn" onclick="closeModal('packing-modal-${id}')">Cancel</button>
                                <button class="btn btn-primary" type="submit">${this._resolveSubmitLabel(action)}</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `
        document.body.insertAdjacentHTML('beforeend', html)

        // get modal elements and add event listeners
        const modal = document.getElementById(`packing-modal-${id}`)
        // add listener for scanning items
        if (showScanControls && canScan) {
            modal.querySelector('.ps-input').addEventListener('keydown', (e)=>{
                if(e.key === 'Enter'){
                    e.preventDefault()
                    this._scanItem(e, id)
                }
            });
        }

        // add listener for form submission
        modal.querySelector(`form`).addEventListener('submit', (e)=>{
            e.preventDefault()
            this._submitByAction(id, action)
        });
        openModal(`packing-modal-${id}`)
    }

    _getCsrfToken() {
        const csrfCookie = document.cookie
            .split('; ')
            .find((item) => item.startsWith('csrftoken='))

        return csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : ''
    }

    _showError(modal, message) {
        const errorBox = modal?.querySelector('.alert.err')
        if (!errorBox) return
        errorBox.textContent = message
        errorBox.classList.add('active')
    }

    async _submitByAction(orderId, action) {
        if (action === 'ship') {
            await this._shipPacking(orderId)
            return
        }
        if (action === 'deliver') {
            await this._deliverPacking(orderId)
            return
        }
        await this._completePacking(orderId)
    }

    // functions for each action: complete, ship, deliver
    async _completePacking(orderId) {
        const modal = document.getElementById(`packing-modal-${orderId}`)
        if (!modal) return

        const items = [...modal.querySelectorAll('tbody tr')].map((row) => {
            const sku = row.querySelector('td')?.textContent?.trim() || ''
            const quantityScanned = parseInt(row.querySelector('[id^="s-quantity-scanned-"]')?.textContent || '0', 10)

            return {
                sku,
                quantity_scanned: Number.isNaN(quantityScanned) ? 0 : quantityScanned,
            }
        })

        try {
            const response = await fetch(`/packing/${orderId}/complete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrfToken(),
                },
                body: JSON.stringify({ items }),
            })

            const data = await response.json()
            if (!response.ok) {
                this._showError(modal, data.error || 'Could not complete packing.')
                return
            }

            if (data.partial && data.shortage?.length) {
                closeModal(`packing-modal-${orderId}`)
                this._showPartialModal(orderId, data.shortage)
                return
            }

            window.location.reload()
        } catch (_error) {
            this._showError(modal, 'Unexpected error while completing packing.')
        }
    }

    _showPartialModal(orderId, shortage) {
        const rows = shortage.map(s => `
            <tr>
                <td>${s.sku}</td>
                <td>${s.name}</td>
                <td>${s.required}</td>
                <td>${s.scanned}</td>
                <td>${s.required - s.scanned}</td>
            </tr>`).join('')

        const html = `
            <div id="partial-modal-${orderId}" class="modal-backdrop hidden">
                <div class="modal" role="dialog">
                    <div class="modal-header">
                        <h3 style="margin:0">Shortage detected</h3>
                        <button class="btn btn-quiet" onclick="closeModal('partial-modal-${orderId}')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>Some items were not fully scanned. How would you like to proceed?</p>
                        <table>
                            <thead>
                                <tr><th>SKU</th><th>Product</th><th>Required</th><th>Scanned</th><th>Short</th></tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                        <div class="alert err" id="partial-modal-err-${orderId}"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn" onclick="closeModal('partial-modal-${orderId}')">Continue packing</button>
                        <button type="button" class="btn btn-warning" id="partial-ship-${orderId}">Ship partial</button>
                        <button type="button" class="btn btn-primary" id="partial-backorder-${orderId}">Create backorder</button>
                    </div>
                </div>
            </div>`

        document.body.insertAdjacentHTML('beforeend', html)

        document.getElementById(`partial-ship-${orderId}`)?.addEventListener('click', () => {
            this._submitPartial(orderId, 'ship_partial')
        })
        document.getElementById(`partial-backorder-${orderId}`)?.addEventListener('click', () => {
            this._submitPartial(orderId, 'create_backorder')
        })

        openModal(`partial-modal-${orderId}`)
    }

    async _submitPartial(orderId, action) {
        try {
            const response = await fetch(`/packing/${orderId}/complete-partial/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrfToken(),
                },
                body: JSON.stringify({ action }),
            })

            const data = await response.json()
            if (!response.ok || !data.ok) {
                const errBox = document.getElementById(`partial-modal-err-${orderId}`)
                if (errBox) {
                    errBox.textContent = data.error || 'Could not complete partial shipment.'
                    errBox.classList.add('active')
                }
                return
            }

            closeModal(`partial-modal-${orderId}`)
            this._showToast(data.message || 'Partial shipment completed.')
            setTimeout(() => location.reload(), 1800)
        } catch (_error) {
            const errBox = document.getElementById(`partial-modal-err-${orderId}`)
            if (errBox) {
                errBox.textContent = 'Unexpected error.'
                errBox.classList.add('active')
            }
        }
    }

    _showToast(message, type = 'success') {
        const el = document.createElement('div')
        el.className = `alert active ${type === 'error' ? 'err' : 'ok'}`
        el.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:260px;max-width:420px;'
        el.textContent = message
        document.body.appendChild(el)
        setTimeout(() => el.remove(), 4000)
    }

    async _shipPacking(orderId) {
        const modal = document.getElementById(`packing-modal-${orderId}`)
        if (!modal) return

        const carrier = modal.querySelector('.ps-carrier')?.value
        const trackingNumber = modal.querySelector('.ps-tracking')?.value?.trim()

        if (!carrier || !trackingNumber) {
            this._showError(modal, 'Carrier and tracking number are required to ship.')
            return
        }
        try {
            const response = await fetch(`/packing/${orderId}/ship/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrfToken(),
                },
                body: JSON.stringify({
                    carrier,
                    tracking_number: trackingNumber,
                    order_id: orderId,
                }),
            })

            const data = await response.json()
            if (!response.ok) {
                this._showError(modal, data.error || 'Could not ship order.')
                return
            }

            window.location.reload()
        } catch (_error) {
            this._showError(modal, 'Unexpected error while shipping order.')
        }
    }

    async _deliverPacking(orderId) {
        const modal = document.getElementById(`packing-modal-${orderId}`)
        if (!modal) return

        try {
            const response = await fetch(`/packing/${orderId}/deliver/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrfToken(),
                },
                body: JSON.stringify({ order_id: orderId }),
            })

            const data = await response.json()
            if (!response.ok) {
                this._showError(modal, data.error || 'Could not mark order as delivered.')
                return
            }

            window.location.reload()
        } catch (_error) {
            this._showError(modal, 'Unexpected error while marking order as delivered.')
        }
    }

    _scanItem(e, orderId){
        const modal = e.target.closest('.modal')
        let scannedQuantityElement = document.getElementById(`s-quantity-scanned-${orderId}-${e.target.value}`)
        const requiredQuantityElement = document.getElementById(`s-quantity-required-${orderId}-${e.target.value}`)
        if(scannedQuantityElement && requiredQuantityElement){
            let scannedQuantity = parseInt(scannedQuantityElement.textContent)
            const requiredQuantity = parseInt(requiredQuantityElement.textContent)
            if(scannedQuantity < requiredQuantity){
                scannedQuantity++
                scannedQuantityElement.textContent = scannedQuantity

                // ── Aktualizuj pasek postępu na żywo ─────────────────
                // Po każdym skanowaniu przelicza procent ze wszystkich
                // wierszy modalu i ustawia width + kolor paska w sekcji
                // Packing Progress (bez przeładowania strony).
                this._refreshProgressBar(orderId, modal)

                if (modal) {
                    modal.querySelector('.alert.ok').textContent = `Scanned ${scannedQuantity} of ${requiredQuantity} for SKU ${e.target.value}`
                    modal.querySelector('.alert.ok').classList.add('active')
                }
                e.target.value = ''

                if(this.#successTimer) clearTimeout(this.#successTimer)
                this.#successTimer = setTimeout(()=>{
                    if (modal) {
                        modal.querySelector('.alert.ok').classList.remove('active')
                    }
                }, 3000)

            } else {
                if (modal) {
                    modal.querySelector('.alert.err').textContent = `All required quantity for SKU ${e.target.value} already scanned!`
                    modal.querySelector('.alert.err').classList.add('active')
                }

                if(this.#errorTimer) clearTimeout(this.#errorTimer)
                this.#errorTimer = setTimeout(()=>{
                    if (modal) {
                        modal.querySelector('.alert.err').classList.remove('active')
                    }
                }, 3000)
            }
        }
    }

    // ── Batch action bar ─────────────────────────────────────────────

    _updateBatchBar() {
        // Zlicza zaznaczone checkboxy i pokazuje/chowa batch bar.
        const checked = document.querySelectorAll('.packing-checkbox:checked')
        const count = checked.length
        if (this.#batchCount) this.#batchCount.textContent = `${count} selected`
        if (this.#startBtn)   this.#startBtn.disabled = count === 0
        if (this.#batchBar)   this.#batchBar.classList.toggle('hidden', count === 0)
    }

    async _startPacking(orderIds) {
        // Wysyła zaznaczone IDs do backendu → PENDING → IN_PROGRESS → reload.
        // Backend: packing/views.py → start_packing()
        try {
            const response = await fetch('/packing/start/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrfToken(),
                },
                body: JSON.stringify({ order_ids: orderIds }),
            })
            const data = await response.json()
            if (!response.ok || !data.ok) {
                console.error('Could not start packing:', data.error)
                return
            }
            // Przeładuj – zlecenia powinny teraz pojawić się w sekcji Progress
            window.location.reload()
        } catch (err) {
            console.error('Error starting packing:', err)
        }
    }

    // ── Progress bar helpers ─────────────────────────────────────────

    /**
     * Przelicza procent ze wszystkich wierszy tabeli modalu
     * i ustawia odpowiedni width + klasę koloru paska w sekcji Progress.
     */
    _refreshProgressBar(orderId, modal) {
        const rows = modal?.querySelectorAll('tbody tr') || []
        let totalScanned = 0
        let totalRequired = 0
        rows.forEach(row => {
            const s = parseInt(row.querySelector('[id^="s-quantity-scanned-"]')?.textContent || '0', 10)
            const r = parseInt(row.querySelector('[id^="s-quantity-required-"]')?.textContent || '0', 10)
            totalScanned  += isNaN(s) ? 0 : s
            totalRequired += isNaN(r) ? 0 : r
        })
        const percent = totalRequired > 0 ? Math.round(totalScanned / totalRequired * 100) : 0

        // Paska w sekcji Progress (data-order-id="...") – może nie istnieć
        // gdy zlecenie jest w trybie PENDING (tylko queue, bez postępu).
        const bar      = document.querySelector(`.progress-bar[data-order-id="${orderId}"] > div`)
        const barWrap  = document.querySelector(`.progress-bar[data-order-id="${orderId}"]`)
        const label    = document.getElementById(`progress-label-${orderId}`)

        if (bar)     bar.style.width = `${percent}%`
        if (label)   label.textContent = `${totalScanned}/${totalRequired}`
        if (barWrap) barWrap.className = `progress-bar ${this._progressColorClass(percent)}`
    }

    /**
     * Mapuje procent na klasę CSS koloru paska:
     *  danger  →  1-49%   (czerwony)
     *  warning → 50-89%  (żółty)
     *  info    → 90-99%  (niebieski / primary)
     *  success → 100%    (zielony)
     * Definicje klas: packing/static/css/packing.css
     */
    _progressColorClass(percent) {
        if (percent === 100) return 'success'
        if (percent >= 90)  return 'info'
        if (percent >= 50)  return 'warning'
        if (percent > 0)    return 'danger'
        return ''
    }

}

const packingApp = new PackingApp()
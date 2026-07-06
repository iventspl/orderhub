class PackingApp {
    #errorTimer = null
    #successTimer = null
    #scanner = null
    #lastScanTime = 0
    #scanCooldown = 2000
    #packingList   = document.getElementById('packingTable')
    #batchBar      = document.getElementById('packing-batch-bar')
    #batchCount    = document.getElementById('packing-batch-count')
    #startBtn      = document.getElementById('packing-start-btn')
    #selectAll     = document.getElementById('packing-select-all')
    #rows          = document.querySelectorAll('.clickable')
    #expandedRows  = document.querySelectorAll('.expand-row')

    constructor() {
        /*
        Wires up all page-level event listeners on first load.
        Does not touch modals — only what is already in the Django-rendered DOM.

        1. Tab switching — Active/History tabs toggle their panels.
        2. Section click delegation — one listener handles both:
              • .order-startPacking button  → opens the packing modal for that order
              • tr[data-order-id] row click → toggles the expandable detail row
        3. Checkbox changes on the queue table → keeps batch bar and Select-All in sync.
        4. "Start packing" button → collects checked IDs and calls _startPacking().
        */
        document.querySelectorAll('.tab[data-tab]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab[data-tab]').forEach(t => t.classList.remove('active'))
                btn.classList.add('active')
                const target = btn.dataset.tab
                document.getElementById('tab-panel-active').style.display  = target === 'active'  ? '' : 'none'
                document.getElementById('tab-panel-history').style.display = target === 'history' ? '' : 'none'
            })
        })

        document.getElementById('section-packing')?.addEventListener('click', (e) => {
            const clickedBtn = e.target.closest('.order-startPacking')
            const clickedRow = e.target.closest('tr[data-order-id]')

            if (clickedBtn) {
                const orderId     = clickedBtn.getAttribute('data-order-id')
                const orderStatus = clickedBtn.getAttribute('data-order-status')
                const orderNumber = clickedBtn.getAttribute('data-order-number') || orderId
                const scriptTag   = document.getElementById(`items-data-${orderId}`)
                if (!scriptTag) return

                const orderItems = JSON.parse(scriptTag.textContent)
                if (!document.getElementById(`packing-modal-${orderId}`)) {
                    this._openPackingModal(orderId, orderItems, orderStatus, orderNumber)
                } else {
                    openModal(`packing-modal-${orderId}`)
                }
            }

            if (clickedRow && !e.target.closest('button')) {
                const orderId = clickedRow.getAttribute('data-order-id')
                const expandedInfo = document.querySelector('.expand-row[data-order-id="'+orderId+'"]')
                const isExpanded = expandedInfo?.classList.contains('active')

                this.#rows.forEach(row => row.classList.remove('expanded'))
                this.#expandedRows.forEach(row => row.classList.remove('active'))

                if (isExpanded) return
                clickedRow.classList.add('expanded')
                expandedInfo.classList.add('active')
            }
        })

        this.#packingList?.addEventListener('change', (e) => {
            if (e.target.classList.contains('packing-checkbox')) {
                this._updateBatchBar()
                const all     = document.querySelectorAll('.packing-checkbox')
                const checked = document.querySelectorAll('.packing-checkbox:checked')
                if (this.#selectAll) {
                    this.#selectAll.indeterminate = checked.length > 0 && checked.length < all.length
                    this.#selectAll.checked = checked.length === all.length && all.length > 0
                }
            }
        })

        this.#selectAll?.addEventListener('change', (e) => {
            document.querySelectorAll('.packing-checkbox').forEach(cb => { cb.checked = e.target.checked })
            this._updateBatchBar()
        })

        this.#startBtn?.addEventListener('click', () => {
            const selected = [...document.querySelectorAll('.packing-checkbox:checked')]
                .map(cb => parseInt(cb.dataset.id, 10))
            if (selected.length) this._startPacking(selected)
        })
    }

    _normalizeStatus(status) {
        /*
        Uppercases the status string and guards against null/undefined.
        Used everywhere status comparisons happen so casing never causes a mismatch.
        */
        return (status || '').toUpperCase()
    }

    _resolveAction(status) {
        /*
        Maps an order status to the modal action that should be performed:
          PACKED  → 'ship'     (show carrier / tracking / weight / notes form)
          SHIPPED → 'deliver'  (confirm delivery button only)
          else    → 'complete' (scanning mode — default for PENDING / IN_PROGRESS)
        */
        const s = this._normalizeStatus(status)
        if (s === 'PACKED')  return 'ship'
        if (s === 'SHIPPED') return 'deliver'
        return 'complete'
    }

    _resolveSubmitLabel(action) {
        /*
        Returns the correct submit button label for each modal action.
        */
        if (action === 'ship')    return 'Ship order'
        if (action === 'deliver') return 'Mark delivered'
        return 'Complete packing'
    }

    _openPackingModal(id, items, status, orderNumber) {
        /*
        Main modal factory. Builds and injects the entire packing station modal
        into the DOM based on the order's current status.

        Four boolean flags control which sections are rendered:
          showScanControls     — SKU text input + Camera button + green alert strip
          showItemsTable       — items table with scanned / required counts
                                 (on 'complete': also renders − / + buttons per row)
          showShippingControls — carrier, tracking, weight, packing notes fields

        After inserting the HTML, attaches five event listeners:
          1. SKU input keydown Enter    → _scanItem() then clears input
          2. +/- button delegation      → _incrementItem() / _decrementItem()
          3. Camera toggle              → _openCameraFullscreen()
          4. Close buttons (× / Cancel) → stop camera + remove fullscreen overlay
          5. Form submit                → _submitByAction()
        */
        const action               = this._resolveAction(status)
        const normalizedStatus     = this._normalizeStatus(status)
        const canScan              = action === 'complete'
        const showScanControls     = action === 'complete'
        const showItemsTable       = action === 'complete' || action === 'ship'
        const showShippingControls = action === 'ship'

        const html = `
            <div id="packing-modal-${id}" class="modal-backdrop hidden">
                <div class="modal" role="dialog">
                    <div class="modal-header">
                        <h3 style="margin:0">Packing station — ${orderNumber} (${normalizedStatus || 'PENDING'})</h3>
                        <button class="btn btn-quiet" onclick="closeModal('packing-modal-${id}')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="packing-form-${id}">
                            ${showScanControls ? `
                                <div class="row" style="align-items:flex-end">
                                    <label style="flex:1">
                                        Scan / type SKU
                                        <input class="ps-input" placeholder="Scan barcode or SKU" ${canScan ? '' : 'disabled'} />
                                    </label>
                                    <div style="padding-bottom:2px">
                                        <button type="button" class="btn btn-sm" id="camera-toggle-${id}">📷 Camera</button>
                                    </div>
                                </div>
                                <div class="alert ok">Scanned items</div>
                            ` : ''}
                            ${showItemsTable ? `
                                <table>
                                    <thead>
                                        <tr>
                                            <th>SKU</th>
                                            <th>Product</th>
                                            <th>Scanned</th>
                                            <th>Required</th>
                                            ${showScanControls ? '<th></th>' : ''}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${items.map(item => `
                                            <tr id="s-item-${id}-${item.sku}">
                                                <td>${item.sku}</td>
                                                <td>${item.name}</td>
                                                <td id="s-quantity-scanned-${id}-${item.sku}">${item.scanned_quantity}</td>
                                                <td id="s-quantity-required-${id}-${item.sku}">${item.quantity}</td>
                                                ${showScanControls ? `
                                                <td style="white-space:nowrap">
                                                    <button type="button" class="btn btn-sm btn-qty-minus" data-sku="${item.sku}" data-order-id="${id}">−</button>
                                                    <button type="button" class="btn btn-sm btn-qty-plus"  data-sku="${item.sku}" data-order-id="${id}">+</button>
                                                </td>` : ''}
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
                                <div class="row">
                                    <label>
                                        Weight (kg)
                                        <input class="ps-weight" type="number" step="0.01" min="0" placeholder="0.00" />
                                    </label>
                                    <label>
                                        Packing notes
                                        <textarea class="ps-notes" rows="2" placeholder="Optional notes about the package..."></textarea>
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

        const modal = document.getElementById(`packing-modal-${id}`)

        if (showScanControls && canScan) {
            modal.querySelector('.ps-input').addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault()
                    this._scanItem(e, id)
                }
            })
        }

        if (showScanControls) {
            modal.addEventListener('click', (e) => {
                const plusBtn  = e.target.closest('.btn-qty-plus')
                const minusBtn = e.target.closest('.btn-qty-minus')
                if (plusBtn)  this._incrementItem(id, plusBtn.dataset.sku, modal)
                if (minusBtn) this._decrementItem(id, minusBtn.dataset.sku, modal)
            })

            modal.querySelector(`#camera-toggle-${id}`)?.addEventListener('click', () => {
                const currentItems = [...modal.querySelectorAll('tbody tr')].map(row => ({
                    sku:              row.querySelector('td')?.textContent?.trim() || '',
                    name:             row.querySelectorAll('td')[1]?.textContent?.trim() || '',
                    scanned_quantity: parseInt(row.querySelector('[id^="s-quantity-scanned-"]')?.textContent || '0'),
                    quantity:         parseInt(row.querySelector('[id^="s-quantity-required-"]')?.textContent || '0'),
                }))
                this._openCameraFullscreen(id, currentItems, orderNumber)
            })
        }

        modal.querySelectorAll('[onclick^="closeModal"]').forEach(btn => {
            btn.addEventListener('click', () => {
                this._stopCameraScanner()
                document.getElementById(`camera-fs-${id}`)?.remove()
            })
        })

        modal.querySelector('form').addEventListener('submit', (e) => {
            e.preventDefault()
            this._submitByAction(id, action)
        })

        openModal(`packing-modal-${id}`)
    }

    // ── Camera fullscreen ────────────────────────────────────────────

    _openCameraFullscreen(orderId, items, orderNumber) {
        /*
        Builds and appends a true fullscreen overlay (position:fixed; inset:0)
        on top of everything. Layout from top to bottom:
          • Dark header bar — order number on the left, "✕ Done" button on the right.
          • Camera viewfinder div — html5-qrcode injects <video> here.
          • Info strip — shows last scan result or error feedback.
          • Scrollable items list — each row has name, SKU, and a live
            #cf-qty-{orderId}-{sku} counter that turns green when complete.

        Quantities in the items list are read from the packing modal's DOM cells
        at the moment Camera is opened, so they reflect any prior +/- or keyboard scans.
        "Done" stops the scanner and removes the overlay. The packing modal behind
        it already has up-to-date quantity cells — no re-sync needed.
        */
        document.getElementById(`camera-fs-${orderId}`)?.remove()

        const itemRows = items.map(item => {
            const done = item.scanned_quantity >= item.quantity
            return `
                <div class="camera-fs-item">
                    <div>
                        <div style="font-weight:500;font-size:14px">${item.name}</div>
                        <div class="muted small">${item.sku}</div>
                    </div>
                    <div class="camera-fs-item-qty ${done ? 'done' : ''}" id="cf-qty-${orderId}-${item.sku}">
                        ${item.scanned_quantity} / ${item.quantity}
                    </div>
                </div>`
        }).join('')

        const html = `
            <div id="camera-fs-${orderId}" class="camera-fs-modal">
                <div class="camera-fs-header">
                    <span style="font-weight:600;font-size:15px">${orderNumber}</span>
                    <button type="button" class="btn btn-sm btn-camera-done" id="camera-fs-done-${orderId}">✕ Done</button>
                </div>
                <div id="ps-camera-full-${orderId}" class="camera-fs-viewfinder"></div>
                <div id="camera-fs-info-${orderId}" class="camera-fs-info">Point camera at barcode or QR code</div>
                <div class="camera-fs-items">${itemRows}</div>
            </div>`

        document.body.insertAdjacentHTML('beforeend', html)

        document.getElementById(`camera-fs-done-${orderId}`)?.addEventListener('click', () => {
            this._stopCameraScanner()
            document.getElementById(`camera-fs-${orderId}`)?.remove()
        })

        this._startCameraScanner(orderId, `ps-camera-full-${orderId}`, `camera-fs-info-${orderId}`)
    }

    _startCameraScanner(orderId, containerId, infoElId) {
        /*
        Stops any previously running scanner, then starts a new Html5Qrcode instance
        inside the given container element.

        Uses { facingMode: 'environment' } instead of enumerateDevices() + deviceId
        because iOS Safari's enumerateDevices() silently returns empty results before
        getUserMedia has been called for the current origin — causing a false
        'no camera' error even when the user has granted permission.

        On a successful decode, calls _processCameraScan(). Errors from the
        scan-frame callback are intentionally swallowed (they fire on every
        unrecognised frame, which is normal). Start failures write the raw error
        string to the info element for debugging.
        */
        this._stopCameraScanner()
        const el     = document.getElementById(containerId)
        const infoEl = document.getElementById(infoElId)
        if (!el || typeof Html5Qrcode === 'undefined') return

        this.#scanner = new Html5Qrcode(containerId)
        this.#scanner.start(
            { facingMode: 'environment' },
            { fps: 10, qrbox: { width: 250, height: 150 } },
            (decodedText) => this._processCameraScan(orderId, decodedText.trim()),
            () => {}
        ).catch(err => {
            if (infoEl) infoEl.textContent = 'Error: ' + String(err)
        })
    }

    _stopCameraScanner() {
        /*
        Releases the camera hardware by calling scanner.stop(), then nulls the
        reference. Errors from stop() are swallowed — the scanner may already be
        in a failed state and throwing would mask the real problem.
        */
        if (this.#scanner) {
            this.#scanner.stop().catch(() => {})
            this.#scanner = null
        }
    }

    _processCameraScan(orderId, sku) {
        /*
        Entry point for every barcode / QR decode event from the camera.

        1. Cooldown gate — if less than #scanCooldown ms have passed since the last
           successful scan, returns immediately. Prevents the same barcode being
           counted multiple times while still in frame.
        2. Records #lastScanTime.
        3. Looks up s-quantity-scanned and s-quantity-required cells in the packing
           modal (which stays in the DOM behind the fullscreen overlay).
        4. SKU not found → writes error to the info strip.
        5. scanned < required → increments the modal cell, refreshes the progress
           bar on the main page, syncs the fullscreen qty counter, writes a green
           confirmation to the info strip and resets its colour after the cooldown.
        6. Already complete → writes 'Already complete' to the info strip.
        */
        const now = Date.now()
        if (now - this.#lastScanTime < this.#scanCooldown) return
        this.#lastScanTime = now

        const scannedEl  = document.getElementById(`s-quantity-scanned-${orderId}-${sku}`)
        const requiredEl = document.getElementById(`s-quantity-required-${orderId}-${sku}`)
        const infoEl     = document.getElementById(`camera-fs-info-${orderId}`)
        const modal      = document.getElementById(`packing-modal-${orderId}`)

        if (!scannedEl || !requiredEl) {
            if (infoEl) infoEl.textContent = `SKU "${sku}" not found in this order.`
            return
        }
        const scanned  = parseInt(scannedEl.textContent)
        const required = parseInt(requiredEl.textContent)

        if (scanned < required) {
            const newQty = scanned + 1
            scannedEl.textContent = newQty
            this._refreshProgressBar(orderId, modal)
            this._syncFullscreenQty(orderId, sku, newQty, required)
            if (infoEl) {
                infoEl.textContent = `✓ ${sku} — ${newQty} / ${required}`
                infoEl.style.color = '#22c55e'
                setTimeout(() => { infoEl.style.color = '' }, this.#scanCooldown)
            }
        } else {
            if (infoEl) infoEl.textContent = `Already complete: ${sku} (${required}/${required})`
        }
    }

    _syncFullscreenQty(orderId, sku, scanned, required) {
        /*
        Updates the #cf-qty-{orderId}-{sku} counter in the fullscreen items list
        to reflect the latest scanned quantity. Adds the 'done' class (green colour)
        when scanned >= required. Called after every increment from any source
        (camera, keyboard, + button) so the fullscreen list stays in sync.
        */
        const el = document.getElementById(`cf-qty-${orderId}-${sku}`)
        if (!el) return
        el.textContent = `${scanned} / ${required}`
        el.classList.toggle('done', scanned >= required)
    }

    // ── Scan / qty helpers ───────────────────────────────────────────

    _scanItem(e, orderId) {
        /*
        Called when the user presses Enter in the SKU text input (keyboard / barcode gun).
        Extracts the typed/scanned value, delegates to _incrementItem(), then clears
        the input so it is ready for the next scan without the user having to delete it.
        */
        const modal = e.target.closest('.modal')
        const sku   = e.target.value
        this._incrementItem(orderId, sku, modal)
        e.target.value = ''
    }

    _incrementItem(orderId, sku, modal) {
        /*
        Shared increment logic used by keyboard scan, + button, and camera scan.

        Reads scanned and required counts from the DOM cells:
          s-quantity-scanned-{orderId}-{sku}
          s-quantity-required-{orderId}-{sku}

        If scanned < required:
          • Increments the scanned cell.
          • Refreshes the progress bar on the main page.
          • Syncs the fullscreen qty counter (if open).
          • Flashes a green success alert in the packing modal.
        If already at max → flashes a red error alert.
        SKU not found    → flashes a red error alert.
        */
        const scannedEl  = document.getElementById(`s-quantity-scanned-${orderId}-${sku}`)
        const requiredEl = document.getElementById(`s-quantity-required-${orderId}-${sku}`)

        if (!scannedEl || !requiredEl) {
            if (modal) this._flashAlert(modal, 'err', `SKU ${sku} not found in this order.`)
            return
        }
        const scanned  = parseInt(scannedEl.textContent)
        const required = parseInt(requiredEl.textContent)

        if (scanned < required) {
            const newQty = scanned + 1
            scannedEl.textContent = newQty
            this._refreshProgressBar(orderId, modal)
            this._syncFullscreenQty(orderId, sku, newQty, required)
            if (modal) this._flashAlert(modal, 'ok', `Scanned ${newQty} of ${required} for SKU ${sku}`)
        } else {
            if (modal) this._flashAlert(modal, 'err', `All required quantity for SKU ${sku} already scanned!`)
        }
    }

    _decrementItem(orderId, sku, modal) {
        /*
        Called by the − button. Decrements the scanned cell by 1 if currently > 0.
        Refreshes the progress bar and syncs the fullscreen qty counter.
        No alert is shown — the change is visible immediately in the cell.
        */
        const scannedEl  = document.getElementById(`s-quantity-scanned-${orderId}-${sku}`)
        const requiredEl = document.getElementById(`s-quantity-required-${orderId}-${sku}`)
        if (!scannedEl) return
        const scanned  = parseInt(scannedEl.textContent)
        const required = parseInt(requiredEl?.textContent || '0')
        if (scanned > 0) {
            const newQty = scanned - 1
            scannedEl.textContent = newQty
            this._refreshProgressBar(orderId, modal)
            this._syncFullscreenQty(orderId, sku, newQty, required)
        }
    }

    _flashAlert(modal, type, message) {
        /*
        Shows a temporary alert inside the packing modal.
        type: 'ok' → green strip, 'err' → red strip.

        Clears any existing timer before setting a new one so rapid successive
        calls never leave a stale timeout that hides the latest message too early.
        Auto-hides after 3 seconds.
        */
        const el = modal.querySelector(`.alert.${type}`)
        if (!el) return
        el.textContent = message
        el.classList.add('active')
        const timer = type === 'err' ? '#errorTimer' : '#successTimer'
        if (this[timer]) clearTimeout(this[timer])
        this[timer] = setTimeout(() => el.classList.remove('active'), 3000)
    }

    // ── Complete / ship / deliver ────────────────────────────────────

    async _submitByAction(orderId, action) {
        /*
        Routes form submission to the correct async method based on the modal action.
        */
        if (action === 'ship')    { await this._shipPacking(orderId);    return }
        if (action === 'deliver') { await this._deliverPacking(orderId); return }
        await this._completePacking(orderId)
    }

    async _completePacking(orderId) {
        /*
        Collects all { sku, quantity_scanned } pairs from the modal's tbody rows
        and POSTs them to /packing/{id}/complete/.

        Backend responses:
          { partial: true, shortage: [...] } → closes packing modal, opens shortage modal.
          { ok: true }                       → reloads the page (order now PACKED).
          HTTP error                         → shows error in modal.
        */
        const modal = document.getElementById(`packing-modal-${orderId}`)
        if (!modal) return

        const items = [...modal.querySelectorAll('tbody tr')].map(row => ({
            sku: row.querySelector('td')?.textContent?.trim() || '',
            quantity_scanned: parseInt(row.querySelector('[id^="s-quantity-scanned-"]')?.textContent || '0', 10) || 0,
        }))

        try {
            const response = await fetch(`/packing/${orderId}/complete/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrfToken() },
                body: JSON.stringify({ items }),
            })
            const data = await response.json()
            if (!response.ok) { this._showError(modal, data.error || 'Could not complete packing.'); return }
            if (data.partial && data.shortage?.length) {
                closeModal(`packing-modal-${orderId}`)
                this._showPartialModal(orderId, data.shortage)
                return
            }
            window.location.reload()
        } catch {
            this._showError(modal, 'Unexpected error while completing packing.')
        }
    }

    _showPartialModal(orderId, shortage) {
        /*
        Injects a second modal listing items that were under-scanned.
        Columns: SKU | Product | Required | Scanned | Short.

        Three action buttons:
          'Continue packing' — closes this modal, user returns to packing modal.
          'Ship partial'     → _submitPartial('ship_partial')
          'Create backorder' → _submitPartial('create_backorder')
        */
        const rows = shortage.map(s => `
            <tr>
                <td>${s.sku}</td><td>${s.name}</td>
                <td>${s.required}</td><td>${s.scanned}</td><td>${s.required - s.scanned}</td>
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
                            <thead><tr><th>SKU</th><th>Product</th><th>Required</th><th>Scanned</th><th>Short</th></tr></thead>
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
        document.getElementById(`partial-ship-${orderId}`)?.addEventListener('click', () => this._submitPartial(orderId, 'ship_partial'))
        document.getElementById(`partial-backorder-${orderId}`)?.addEventListener('click', () => this._submitPartial(orderId, 'create_backorder'))
        openModal(`partial-modal-${orderId}`)
    }

    async _submitPartial(orderId, action) {
        /*
        POSTs { action } to /packing/{id}/complete-partial/.
        action is either 'ship_partial' or 'create_backorder'.

        On success: closes the partial modal, shows a toast message, reloads after 1.8 s.
        On failure: shows the error message inside the partial modal's own error box.
        */
        try {
            const response = await fetch(`/packing/${orderId}/complete-partial/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrfToken() },
                body: JSON.stringify({ action }),
            })
            const data = await response.json()
            if (!response.ok || !data.ok) {
                const errBox = document.getElementById(`partial-modal-err-${orderId}`)
                if (errBox) { errBox.textContent = data.error || 'Could not complete partial shipment.'; errBox.classList.add('active') }
                return
            }
            closeModal(`partial-modal-${orderId}`)
            this._showToast(data.message || 'Partial shipment completed.')
            setTimeout(() => location.reload(), 1800)
        } catch {
            const errBox = document.getElementById(`partial-modal-err-${orderId}`)
            if (errBox) { errBox.textContent = 'Unexpected error.'; errBox.classList.add('active') }
        }
    }

    async _shipPacking(orderId) {
        /*
        Reads the ship modal fields and POSTs to /packing/{id}/ship/.

        Required: carrier (select), tracking_number (text input).
        Optional: weight_kg (number input, parsed as float), notes (textarea).

        Backend saves weight_kg and notes to PackingOrder, creates/updates the
        Tracking record, and transitions the order to SHIPPED. Reloads on success.
        */
        const modal = document.getElementById(`packing-modal-${orderId}`)
        if (!modal) return

        const carrier        = modal.querySelector('.ps-carrier')?.value
        const trackingNumber = modal.querySelector('.ps-tracking')?.value?.trim()
        if (!carrier || !trackingNumber) { this._showError(modal, 'Carrier and tracking number are required to ship.'); return }

        const weightVal = modal.querySelector('.ps-weight')?.value
        const weight_kg = weightVal ? parseFloat(weightVal) : null
        const notes     = modal.querySelector('.ps-notes')?.value?.trim() || ''

        try {
            const response = await fetch(`/packing/${orderId}/ship/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrfToken() },
                body: JSON.stringify({ carrier, tracking_number: trackingNumber, order_id: orderId, weight_kg, notes }),
            })
            const data = await response.json()
            if (!response.ok) { this._showError(modal, data.error || 'Could not ship order.'); return }
            window.location.reload()
        } catch {
            this._showError(modal, 'Unexpected error while shipping order.')
        }
    }

    async _deliverPacking(orderId) {
        /*
        POSTs { order_id } to /packing/{id}/deliver/.
        Backend updates Tracking status to DELIVERED and SalesOrder to DELIVERED.
        Reloads on success.
        */
        const modal = document.getElementById(`packing-modal-${orderId}`)
        if (!modal) return
        try {
            const response = await fetch(`/packing/${orderId}/deliver/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrfToken() },
                body: JSON.stringify({ order_id: orderId }),
            })
            const data = await response.json()
            if (!response.ok) { this._showError(modal, data.error || 'Could not mark order as delivered.'); return }
            window.location.reload()
        } catch {
            this._showError(modal, 'Unexpected error while marking order as delivered.')
        }
    }

    // ── Batch ────────────────────────────────────────────────────────

    _updateBatchBar() {
        /*
        Counts all checked .packing-checkbox inputs and updates the batch action bar.
        Shows the bar when at least one order is selected, hides it otherwise.
        Disables the Start button when count is zero.
        Updates the 'X selected' counter label.
        */
        const checked = document.querySelectorAll('.packing-checkbox:checked')
        const count   = checked.length
        if (this.#batchCount) this.#batchCount.textContent = `${count} selected`
        if (this.#startBtn)   this.#startBtn.disabled = count === 0
        if (this.#batchBar)   this.#batchBar.classList.toggle('hidden', count === 0)
    }

    async _startPacking(orderIds) {
        /*
        POSTs { order_ids: [...] } to /packing/start/.
        Backend transitions each PENDING PackingOrder to IN_PROGRESS.
        Reloads on success so the orders appear in the Packing Progress section.
        */
        try {
            const response = await fetch('/packing/start/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrfToken() },
                body: JSON.stringify({ order_ids: orderIds }),
            })
            const data = await response.json()
            if (!response.ok || !data.ok) { console.error('Could not start packing:', data.error); return }
            window.location.reload()
        } catch (err) {
            console.error('Error starting packing:', err)
        }
    }

    // ── Progress bar ─────────────────────────────────────────────────

    _refreshProgressBar(orderId, modal) {
        /*
        Recalculates packing progress from all tbody rows in the modal and updates
        the progress bar on the main page in real time (without a page reload).

        Reads every s-quantity-scanned-* and s-quantity-required-* cell, sums them,
        and computes a percentage. Then updates three elements on the main page:
          .progress-bar[data-order-id] > div  — bar width (%)
          .progress-bar[data-order-id]        — colour class via _progressColorClass()
          #progress-label-{orderId}           — 'X/Y' text label
        */
        const rows = modal?.querySelectorAll('tbody tr') || []
        let totalScanned = 0, totalRequired = 0
        rows.forEach(row => {
            const s = parseInt(row.querySelector('[id^="s-quantity-scanned-"]')?.textContent || '0', 10)
            const r = parseInt(row.querySelector('[id^="s-quantity-required-"]')?.textContent || '0', 10)
            totalScanned  += isNaN(s) ? 0 : s
            totalRequired += isNaN(r) ? 0 : r
        })
        const percent = totalRequired > 0 ? Math.round(totalScanned / totalRequired * 100) : 0
        const bar     = document.querySelector(`.progress-bar[data-order-id="${orderId}"] > div`)
        const barWrap = document.querySelector(`.progress-bar[data-order-id="${orderId}"]`)
        const label   = document.getElementById(`progress-label-${orderId}`)
        if (bar)     bar.style.width = `${percent}%`
        if (label)   label.textContent = `${totalScanned}/${totalRequired}`
        if (barWrap) barWrap.className = `progress-bar ${this._progressColorClass(percent)}`
    }

    _progressColorClass(percent) {
        /*
        Maps a completion percentage to a CSS colour class for the progress bar.
          100%   → 'success' (green)
          90–99% → 'info'    (blue / primary)
          50–89% → 'warning' (yellow)
          1–49%  → 'danger'  (red)
          0%     → ''        (no class — bar invisible)
        Colour definitions live in packing/static/css/packing.css.
        */
        if (percent === 100) return 'success'
        if (percent >= 90)  return 'info'
        if (percent >= 50)  return 'warning'
        if (percent > 0)    return 'danger'
        return ''
    }

    // ── Utilities ────────────────────────────────────────────────────

    _getCsrfToken() {
        /*
        Reads the Django CSRF token from the csrftoken cookie.
        Required as the X-CSRFToken header on every POST request so Django's
        CSRF middleware does not reject the fetch call with a 403.
        */
        const cookie = document.cookie.split('; ').find(c => c.startsWith('csrftoken='))
        return cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
    }

    _showError(modal, message) {
        /*
        Writes an error message to the .alert.err element inside the given modal
        and makes it visible by adding the 'active' class.
        Does not auto-hide — stays visible until the next action replaces it
        or the modal is closed.
        */
        const box = modal?.querySelector('.alert.err')
        if (!box) return
        box.textContent = message
        box.classList.add('active')
    }

    _showToast(message, type = 'success') {
        /*
        Creates a temporary floating alert in the top-right corner of the page.
        Used for feedback after async actions that close their modal before the
        page reloads (e.g. partial shipment completed).
        Auto-removes itself after 4 seconds.
        type: 'success' → green, 'error' → red.
        */
        const el = document.createElement('div')
        el.className = `alert active ${type === 'error' ? 'err' : 'ok'}`
        el.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:260px;max-width:420px;'
        el.textContent = message
        document.body.appendChild(el)
        setTimeout(() => el.remove(), 4000)
    }
}

const packingApp = new PackingApp()

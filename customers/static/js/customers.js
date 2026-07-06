'use strict';

class CustomersApp {
    #searchInput    = document.getElementById('c-search');
    #paginationRows = document.querySelector('.pagination-rows');
    #createForm     = document.getElementById('customer-create-form');
    #editForm       = document.getElementById('customer-edit-form');
    #editIdInput    = document.getElementById('edit-customer-id');
    #editTitle      = document.getElementById('edit-modal-title');
    #tbody          = document.querySelector('tbody');

    #searchTimer = null;

    constructor() {
        this._bindSortHeaders();
        this._bindSearch();
        this._bindPaginationRows();
        this._bindCreateForm();
        this._bindEditButtons();
        this._bindEditForm();
    }

    // ── helpers ──────────────────────────────────────────────

    _getCsrfToken() {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.trim().split('=')[1]) : '';
    }

    _showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `alert active ${type === 'error' ? 'err' : 'ok'}`;
        toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:260px;max-width:420px;';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    _setFieldError(id, message) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = message;
        el.style.display = message ? 'block' : 'none';
    }

    _clearErrors(prefix) {
        ['first_name', 'last_name', 'email'].forEach(field =>
            this._setFieldError(`${prefix}${field}`, '')
        );
    }

    _applyErrors(errors, prefix) {
        Object.entries(errors).forEach(([field, msg]) =>
            this._setFieldError(`${prefix}${field}`, msg)
        );
    }

    _clientValidate(fields) {
        const errors = {};
        if (!fields.first_name) errors.first_name = 'First name is required.';
        if (!fields.last_name)  errors.last_name  = 'Last name is required.';
        if (!fields.email)      errors.email      = 'Email is required.';
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email))
            errors.email = 'Enter a valid email address.';
        return errors;
    }

    _setQueryParam(params) {
        const url = new URLSearchParams(window.location.search);
        Object.entries(params).forEach(([k, v]) => {
            if (v === '' || v === null || v === undefined) url.delete(k);
            else url.set(k, v);
        });
        window.location.search = url.toString();
    }

    // ── sort ─────────────────────────────────────────────────

    _bindSortHeaders() {
        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const url    = new URLSearchParams(window.location.search);
                const field  = th.dataset.sort;
                const cur    = url.get('sort');
                const curDir = url.get('dir') || 'asc';
                url.set('sort', field);
                url.set('dir', cur === field && curDir === 'asc' ? 'desc' : 'asc');
                url.set('page', '1');
                window.location.search = url.toString();
            });
        });
    }

    // ── search ───────────────────────────────────────────────

    _bindSearch() {
        this.#searchInput?.addEventListener('input', () => {
            clearTimeout(this.#searchTimer);
            this.#searchTimer = setTimeout(() => {
                this._setQueryParam({ search: this.#searchInput.value.trim(), page: 1 });
            }, 400);
        });
    }

    // ── pagination rows ──────────────────────────────────────

    _bindPaginationRows() {
        this.#paginationRows?.addEventListener('change', () => {
            this._setQueryParam({ rows: this.#paginationRows.value, page: 1 });
        });
    }

    // ── create form ──────────────────────────────────────────

    _bindCreateForm() {
        this.#createForm?.addEventListener('submit', async (e) => {
            e.preventDefault();
            this._clearErrors('err-');

            const fd = new FormData(this.#createForm);
            const fields = {
                first_name: fd.get('first_name')?.trim(),
                last_name:  fd.get('last_name')?.trim(),
                email:      fd.get('email')?.trim(),
            };

            const clientErrors = this._clientValidate(fields);
            if (Object.keys(clientErrors).length) {
                this._applyErrors(clientErrors, 'err-');
                return;
            }

            const submitBtn = this.#createForm.querySelector('[type="submit"]');
            submitBtn.disabled = true;

            try {
                const res  = await fetch('/customers/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this._getCsrfToken() },
                    body: fd,
                });
                const data = await res.json();

                if (!res.ok || !data.ok) {
                    if (data.errors) this._applyErrors(data.errors, 'err-');
                    else this._showToast(data.error || 'Something went wrong.', 'error');
                    return;
                }

                this._showToast(data.message);
                closeModal('customer-create-modal');
                this.#createForm.reset();
                setTimeout(() => window.location.reload(), 900);
            } catch {
                this._showToast('Network error. Please try again.', 'error');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    // ── edit buttons ─────────────────────────────────────────

    _bindEditButtons() {
        this.#tbody?.addEventListener('click', (e) => {
            const btn = e.target.closest('.edit-customer-btn');
            if (!btn) return;

            const d = btn.dataset;
            this.#editIdInput.value  = d.id;
            this.#editTitle.textContent = `Edit — ${d.firstName} ${d.lastName}`;

            document.getElementById('e-first-name').value = d.firstName;
            document.getElementById('e-last-name').value  = d.lastName;
            document.getElementById('e-email').value      = d.email;
            document.getElementById('e-phone').value      = d.phone;
            document.getElementById('e-address').value    = d.address;
            document.getElementById('e-zip').value        = d.zip;
            document.getElementById('e-city').value       = d.city;
            document.getElementById('e-state').value      = d.state;
            document.getElementById('e-country').value    = d.country;

            this._clearErrors('e-err-');
            openModal('customer-edit-modal');
        });
    }

    // ── edit form ────────────────────────────────────────────

    _bindEditForm() {
        this.#editForm?.addEventListener('submit', async (e) => {
            e.preventDefault();
            this._clearErrors('e-err-');

            const customerId = this.#editIdInput.value;
            const payload = {
                first_name:   document.getElementById('e-first-name').value.trim(),
                last_name:    document.getElementById('e-last-name').value.trim(),
                email:        document.getElementById('e-email').value.trim(),
                phone_number: document.getElementById('e-phone').value.trim(),
                address:      document.getElementById('e-address').value.trim(),
                zip_code:     document.getElementById('e-zip').value.trim(),
                city:         document.getElementById('e-city').value.trim(),
                state:        document.getElementById('e-state').value.trim(),
                country:      document.getElementById('e-country').value.trim(),
            };

            const clientErrors = this._clientValidate(payload);
            if (Object.keys(clientErrors).length) {
                this._applyErrors(clientErrors, 'e-err-');
                return;
            }

            const submitBtn = this.#editForm.querySelector('[type="submit"]');
            submitBtn.disabled = true;

            try {
                const res  = await fetch(`/customers/${customerId}/edit/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this._getCsrfToken(),
                    },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();

                if (!res.ok || !data.ok) {
                    if (data.errors) this._applyErrors(data.errors, 'e-err-');
                    else this._showToast(data.error || 'Something went wrong.', 'error');
                    return;
                }

                this._showToast(data.message);
                closeModal('customer-edit-modal');
                setTimeout(() => window.location.reload(), 900);
            } catch {
                this._showToast('Network error. Please try again.', 'error');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => new CustomersApp());

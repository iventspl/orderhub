class Inventory{
    #newProductBtn = document.getElementById('inv-new')
    #inventoryBody = document.querySelector('.card-body')
    #paginationRows = document.querySelector('.pagination-rows')

    #editForm = document.querySelector('#inventory-edit-modal form')
    #editSkuInput = document.querySelector('#inventory-edit-modal input[name="product_sku"]')
    #editNameInput = document.querySelector('#inventory-edit-modal input[name="product_name"]')
    #editCategorySelect = document.querySelector('#inventory-edit-modal select[name="product_category"]')
    #editDescriptionTextarea = document.querySelector('#inventory-edit-modal textarea[name="product_description"]')
    #editStockInput = document.querySelector('#inventory-edit-modal input[name="stock_quantity"]')
    #editPriceInput = document.querySelector('#inventory-edit-modal input[name="price"]')
    #editLocationSelect = document.querySelector('#inventory-edit-modal select[name="product_location"]')
    #editBinLocationInput = document.querySelector('#inventory-edit-modal input[name="bin_location"]')
    #editImageInput = document.querySelector('#inventory-edit-modal input[name="product_image"]')
    #editRemoveImageCheckbox = document.querySelector('#inventory-edit-modal input[name="remove_image"]')
    #editPreview = document.querySelector('#edit-product-image-preview')

    #currentProductId = null

    #handleEditFormSubmit = async (event) => {
        event.preventDefault()
        const formData = new FormData(this.#editForm)

        try {
            const response = await fetch(`/inventory/edit/${this.#currentProductId}/`, {
                method: 'POST',
                body: formData
            })
            const data = await response.json()
            console.log('Response:', data)

            if (data.success) {
                const msg = document.createElement('div')
                msg.style.cssText = 'position:fixed;top:20px;right:20px;background:#4caf50;color:white;padding:12px 20px;border-radius:4px;z-index:9999;'
                msg.textContent = data.message
                document.body.appendChild(msg)
                setTimeout(() => msg.remove(), 3000)

                closeModal('inventory-edit-modal')
                setTimeout(() => window.location.reload(), 500)
            } else {
                let errorText = data.message
                if (data.errors) {
                    const errorList = Object.entries(data.errors)
                        .map(([field, error]) => `${field}: ${error}`)
                        .join('\n')
                    errorText += '\n\n' + errorList
                    console.error('Validation errors:', data.errors)
                }
                const msg = document.createElement('div')
                msg.style.cssText = 'position:fixed;top:20px;right:20px;background:#f44336;color:white;padding:12px 20px;border-radius:4px;z-index:9999;white-space:pre-wrap;max-width:400px;'
                msg.textContent = errorText
                document.body.appendChild(msg)
                setTimeout(() => msg.remove(), 5000)
            }
        } catch (error) {
            console.error('Error:', error)
            const msg = document.createElement('div')
            msg.style.cssText = 'position:fixed;top:20px;right:20px;background:#f44336;color:white;padding:12px 20px;border-radius:4px;z-index:9999;'
            msg.textContent = 'Network error. Please try again.'
            document.body.appendChild(msg)
            setTimeout(() => msg.remove(), 5000)
        }
    }

    constructor() {
        this.#newProductBtn.addEventListener('click', e => {
            openModal('inventory-create-modal')
        })

        this.#editForm.addEventListener('submit', this.#handleEditFormSubmit)

        this.#inventoryBody.addEventListener('click', e => {
            if(e.target && e.target.id === 'edit-btn'){
                this.#currentProductId = e.target.dataset.productid
                const sku = e.target.dataset.sku
                const name = e.target.dataset.name
                const price = e.target.dataset.price
                const category = e.target.dataset.category
                const stock = e.target.dataset.stock
                const warehouse = e.target.dataset.warehouse
                const binLocation = e.target.dataset.binlocation || ''
                const description = e.target.dataset.description || ''
                const image = e.target.dataset.image || ''

                this.#editImageInput.value = ''
                if (this.#editRemoveImageCheckbox) this.#editRemoveImageCheckbox.checked = false

                if (image) {
                    this.#editPreview.src = image
                    this.#editPreview.classList.remove('hidden')
                } else {
                    this.#editPreview.src = ''
                    this.#editPreview.classList.add('hidden')
                }

                this.#editSkuInput.value = sku
                this.#editNameInput.value = name
                this.#editCategorySelect.value = category
                this.#editDescriptionTextarea.value = description
                this.#editStockInput.value = stock
                this.#editPriceInput.value = price
                this.#editLocationSelect.value = warehouse
                this.#editBinLocationInput.value = binLocation

                openModal('inventory-edit-modal')
            }
        })

        this.#paginationRows?.addEventListener('change', (e) => {
            const params = new URLSearchParams(window.location.search)
            params.set('rows', e.target.value)
            params.set('page', '1')
            window.location.search = params.toString()
        })

        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const params = new URLSearchParams(window.location.search)
                const field = th.dataset.sort
                const currentSort = params.get('sort')
                const currentDir  = params.get('dir') || 'asc'
                params.set('sort', field)
                params.set('dir', currentSort === field && currentDir === 'asc' ? 'desc' : 'asc')
                params.set('page', '1')
                window.location.search = params.toString()
            })
        })

        let searchTimer = null
        document.getElementById('inv-search')?.addEventListener('input', (e) => {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                const params = new URLSearchParams(window.location.search)
                if (e.target.value.trim()) {
                    params.set('search', e.target.value.trim())
                } else {
                    params.delete('search')
                }
                params.set('page', '1')
                window.location.search = params.toString()
            }, 400)
        })

        this.#editImageInput?.addEventListener('change', (e) => {
            const file = e.target.files[0]
            if (!file) return
            if (this.#editPreview.src.startsWith('blob:')) {
                URL.revokeObjectURL(this.#editPreview.src)
            }
            this.#editPreview.src = URL.createObjectURL(file)
            this.#editPreview.classList.remove('hidden')
        })
    }


}

new Inventory()

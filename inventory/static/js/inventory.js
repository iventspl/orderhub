class Inventory{
    #newProductBtn = document.getElementById('inv-new')
    #inventoryBody = document.querySelector('.card-body')
    constructor() {
        this.#newProductBtn.addEventListener('click', e => {
            openModal('inventory-create-modal')
        })
        // Placeholder for future inventory-related JavaScript functionality
    }


}

new Inventory()
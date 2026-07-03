const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

class HelpCenter{
    #statusSelects = document.querySelectorAll('select[name="status"]');
    #assigneeSelects = document.querySelectorAll('select[name="assignee"]');
    #searchInput = document.querySelector('input[name="search_query"]');
    #sortSelect = document.getElementById('sort');
    #sortDirectionSelect = document.getElementById('sort_direction');
    #statusFilterSelect = document.querySelector('select[name="filter_status"]');
    #departmentFilterSelect = document.querySelector('select[name="filter_department"]');
    #assigneeFilterSelect = document.querySelector('select[name="filter_assignee"]');
    #noRowsSelect = document.getElementById('no_rows_select');
    constructor(){
        this._restoreControlsFromUrl();

        if(this.#statusSelects.length){
            this.#statusSelects.forEach(select => select.addEventListener('change', e => {
                const status = e.target.value;
                const ticketId = e.target.closest('.ticket-card').dataset.ticketId;
                this._updateTicketStatus(status, ticketId);
            }));
        }

        if(this.#assigneeSelects.length){
            this.#assigneeSelects.forEach(select => select.addEventListener('change', e => {
                const assigneeId = e.target.value;
                const ticketId = e.target.closest('.ticket-card').dataset.ticketId;
                this._updateTicketAssignee(assigneeId, ticketId);
            }));
        }

        if(this.#sortSelect){
            this.#sortSelect.addEventListener('change', e => {
                const sortBy = e.target.value;
                const sortDirection = this.#sortDirectionSelect.value;
                this._updateTicketSort(sortBy, sortDirection);
            });
        }

        if(this.#sortDirectionSelect){
            this.#sortDirectionSelect.addEventListener('click', e => {
                const sortBy = this.#sortSelect.value;
                const sortDirection = e.target.value === 'asc' ? 'desc' : 'asc';
                e.target.value = sortDirection;
                e.target.textContent = sortDirection === 'asc' ? 'Asc ↑' : 'Desc ↓';
                this._updateTicketSort(sortBy, sortDirection);
            });
        }

        if(this.#statusFilterSelect){
            this.#statusFilterSelect.addEventListener('change', e => {
                const status = e.target.value;
                this._setQueryParamsAndReload({'filter_status': status});
            });
        }

        if(this.#departmentFilterSelect){
            this.#departmentFilterSelect.addEventListener('change', e => {
                const department = e.target.value;
                this._setQueryParamsAndReload({'filter_department': department});
            });
        }

        if(this.#assigneeFilterSelect){
            this.#assigneeFilterSelect.addEventListener('change', e => {
                const assignee = e.target.value;
                this._setQueryParamsAndReload({'filter_assignee': assignee});
            });
        }

        if(this.#searchInput){
            this.#searchInput.addEventListener('change', e => {
                const searchQuery = e.target.value;
                this._setQueryParamsAndReload({'search_query': searchQuery});
            });

            this.#searchInput.addEventListener('keydown', e => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this._setQueryParamsAndReload({'search_query': e.target.value});
                }
            });
        }

        if(this.#noRowsSelect){
            this.#noRowsSelect.addEventListener('change', e => {
                const noRows = e.target.value;
                this._setQueryParamsAndReload({'no_rows': noRows, 'page': 1});
            });
        }
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

        if (this.#searchInput) {
            this.#searchInput.value = urlParams.get('search_query') || '';
        }

        this._restoreSelectValue(this.#departmentFilterSelect, urlParams.get('filter_department'));
        this._restoreSelectValue(this.#statusFilterSelect, urlParams.get('filter_status'));
        this._restoreSelectValue(this.#assigneeFilterSelect, urlParams.get('filter_assignee'));
        this._restoreSelectValue(this.#sortSelect, urlParams.get('sort_by'));

        if (this.#sortDirectionSelect) {
            const sortDirection = urlParams.get('sort_direction');
            if (sortDirection === 'asc' || sortDirection === 'desc') {
                this.#sortDirectionSelect.value = sortDirection;
                this.#sortDirectionSelect.textContent = sortDirection === 'asc' ? 'Asc ↑' : 'Desc ↓';
            }
        }
    }

    _updateTicketSort(sortBy, sortDirection){
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('sort_by', sortBy);
        urlParams.set('sort_direction', sortDirection);
        window.location.search = urlParams.toString();
    }


    _showErrorModal(message){
        const modal = document.getElementById('errorModal');
        const modalMessage = document.getElementById('errorModalMessage');
        modalMessage.textContent = message;
        modal.style.display = 'block';
        const closeButton = document.getElementById('errorModalClose');
        closeButton.onclick = () => {
            this._closeErrorModal();
        };
    }

    _closeErrorModal(){
        const modal = document.getElementById('errorModal');
        modal.style.display = 'none';
        window.location.reload();
    }


    async _updateTicketStatus(status, ticketId){
        try{
            const response = await fetch(`/helpcenter/api/update-ticket-status/${ticketId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ status })
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to update ticket status.');
            }
            window.location.reload();
        }catch(error){
            console.error('Error updating ticket status:', error);
            this._showErrorModal('Error updating ticket status. Please try again.');
        }
    }

    async _updateTicketAssignee(assigneeId, ticketId){
        try{
            const response = await fetch(`/helpcenter/api/update-ticket-assignee/ticket/${ticketId}/assignee/${assigneeId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ assigneeId })
            });

            if (!response.ok) {
                throw new Error('Failed to update ticket assignee.');
            }
            window.location.reload();
        }catch(error){
            console.error('Error updating ticket assignee:', error);
            this._showErrorModal('Error updating ticket assignee. Please try again.');
        }   
    }

    
}

const helpCenter = new HelpCenter();

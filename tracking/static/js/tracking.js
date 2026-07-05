'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const clickableRows = document.querySelectorAll('tr.clickable');

    clickableRows.forEach(row => {
        row.addEventListener('click', () => {
            const id        = row.dataset.id;
            const expandRow = document.querySelector(`.expand-row[data-id="${id}"]`);
            if (!expandRow) return;

            const isOpen = row.classList.contains('expanded');

            // Close every open row first.
            document.querySelectorAll('tr.clickable').forEach(r => r.classList.remove('expanded'));
            document.querySelectorAll('tr.expand-row').forEach(r => r.classList.remove('active'));

            // Re-open if it wasn't already open.
            if (!isOpen) {
                row.classList.add('expanded');
                expandRow.classList.add('active');
            }
        });
    });
});

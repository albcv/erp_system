// goods_receipt_form.js
(function() {
    'use strict';

    const form = document.getElementById('gr-form');
    const submitBtn = document.getElementById('submit-gr-btn');
    const receiptDate = document.getElementById('receipt_date');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const poPk = parseInt(document.getElementById('po-pk-data').textContent, 10);

    async function submitGoodsReceipt() {
        const rows = document.querySelectorAll('.receipt-item-row');
        const linesData = [];
        let hasError = false;

        rows.forEach(row => {
            const linePk = row.dataset.linePk;
            const qtyInput = row.querySelector('.qty-to-receive');
            const locationSelect = row.querySelector('.location-select');
            const receivedQty = parseFloat(qtyInput.value) || 0;
            const locationPk = locationSelect.value;

            if (receivedQty > 0) {
                if (!locationPk) {
                    alert(`Please select a location for line ${linePk}.`);
                    hasError = true;
                    return;
                }
                linesData.push({
                    line_pk: linePk,
                    received_quantity: receivedQty,
                    location_pk: locationPk
                });
            }
        });

        if (hasError) return;
        if (linesData.length === 0) {
            alert('At least one line must have a quantity to receive.');
            return;
        }

        const payload = {
            po_pk: poPk,
            receipt_date: receiptDate.value,
            lines: linesData
        };

        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        try {
            const response = await fetch('/purchases/post_goods_receipt/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Server error');
            }

            if (result.success) {
                alert(`Goods Receipt ${result.id_goods_receipt} created successfully.`);
                window.location.href = result.redirect_url || '/purchases/purchase_order_list/';
            } else {
                throw new Error(result.error || 'Unknown error');
            }
        } catch (error) {
            alert(`Failed to create receipt: ${error.message}`);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Confirm Receipt';
        }
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        submitGoodsReceipt();
    });

    document.querySelectorAll('.qty-to-receive').forEach(input => {
        input.addEventListener('change', function() {
            const max = parseFloat(this.getAttribute('max'));
            let val = parseFloat(this.value) || 0;
            if (val > max) {
                alert(`Quantity cannot exceed ${max}.`);
                this.value = max;
            }
            if (val < 0) this.value = 0;
        });
    });
})();
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const spinner = document.getElementById('spinner');

    const uploadBtn = document.getElementById('upload-btn');
    const selectedFileText = document.getElementById('selected-file');
    const processingStatus = document.getElementById('processing-status');

    const reviewSection = document.getElementById('review-section');
    const reviewForm = document.getElementById('review-form');

    const receiptPreview = document.getElementById('receipt-preview');

    const merchantName = document.getElementById('merchant-name');
    const receiptDate = document.getElementById('receipt-date');
    const category = document.getElementById('category');
    const paymentMethod = document.getElementById('payment-method');
    const subtotal = document.getElementById('subtotal');
    const tax = document.getElementById('tax');
    const total = document.getElementById('total');

    const itemsTbody = document.getElementById('items-tbody');
    const addItemBtn = document.getElementById('add-item-btn');

    let processedReceipt = null;
    let selectedFile = null;

    // Click drop zone to open file picker
    uploadBtn.addEventListener('click', (event) => {
    event.stopPropagation();
    fileInput.click();
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

    // File selected
    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];

        if (file) {
            processReceipt(file);
        }
    });

    // Drag over
    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.style.borderColor = '#3182ce';
    });

    // Drag leave
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '';
    });

    // Drop file
    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();

        dropZone.style.borderColor = '';

        const file = event.dataTransfer.files[0];

        if (file) {
            processReceipt(file);
        }
    });

    async function processReceipt(file) {
        const allowedTypes = [
            'image/png',
            'image/jpeg',
            'image/webp',
            'image/gif',
            'image/bmp'
        ];

        if (!allowedTypes.includes(file.type)) {
            alert('Please select a valid image file.');
            return;
        }

        selectedFile = file;
        selectedFileText.textContent = `Selected: ${file.name}`;
        processingStatus.textContent = 'Processing receipt...';
        processingStatus.style.display = 'block';
        uploadBtn.disabled = true;

        // Show preview
        receiptPreview.src = URL.createObjectURL(file);

        spinner.style.display = 'block';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const token = localStorage.getItem('token');

            const response = await fetch(
                `${API_BASE_URL}/receipts/process`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to process receipt');
            }

            console.log('Receipt processing response:', data);

            processedReceipt = data;

            const extracted = data.extracted_data || {};

            console.log('EXTRACTED DATA:', extracted);
            console.log('REVIEW SECTION:', reviewSection);

            merchantName.value =
                extracted.merchant_name ||
                extracted.merchant ||
                'Unknown Store';

            const extractedDate =
                extracted.receipt_date ||
                extracted.date ||
                '';

            if (extractedDate) {
                const parts = extractedDate.split('/');

                if (parts.length === 3) {
                    receiptDate.value =
                        `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
                } else {
                    receiptDate.value = extractedDate;
                }
            } else {
                receiptDate.value = '';
            }

            const predictedCategory = extracted.category || 'Other';
            category.value = Array.from(category.options).some(option => option.value === predictedCategory)
                ? predictedCategory
                : 'Other';

            paymentMethod.value =
                extracted.payment_method ||
                'Cash';

            subtotal.value =
                extracted.subtotal ?? 0;

            tax.value =
                extracted.tax ?? 0;

            total.value =
                extracted.total ??
                extracted.total_amount ??
                0;

            // Clear previous items
            itemsTbody.innerHTML = '';

            // Add extracted line items
            const items = extracted.items || [];

            items.forEach(item => {
                addItemRow(
                    item.item_name || item.name || '',
                    item.quantity || 1,
                    item.price ?? item.amount ?? 0
                );
            });

            // Show review section without clearing the selected filename.
            reviewSection.style.display = 'grid';
            processingStatus.textContent = 'Receipt processed successfully. Review the extracted data below.';

            console.log('REVIEW SECTION DISPLAY:', reviewSection.style.display);

        } catch (error) {
            console.error('Receipt processing failed:', error);
            processingStatus.textContent = `Processing failed: ${error.message}`;
            alert(`Receipt processing failed: ${error.message}`);
        } finally {
            spinner.style.display = 'none';
            uploadBtn.disabled = false;
}
    }

    // Add line item
    addItemBtn.addEventListener('click', () => {
        addItemRow('', 1, 0);
    });

    function addItemRow(name, quantity, price) {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>
                <input
                    type="text"
                    class="item-name"
                    value="${name}"
                    required
                >
            </td>

            <td>
                <input
                    type="number"
                    class="item-quantity"
                    value="${quantity}"
                    min="0"
                    step="0.01"
                    required
                >
            </td>

            <td>
                <input
                    type="number"
                    class="item-price"
                    value="${price}"
                    min="0"
                    step="0.01"
                    required
                >
            </td>

            <td>
                <button type="button" class="remove-item-btn">
                    Remove
                </button>
            </td>
        `;

        row.querySelector('.remove-item-btn').addEventListener(
            'click',
            () => {
                row.remove();
            }
        );

        itemsTbody.appendChild(row);
    }

    // Confirm & Save
    reviewForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (!processedReceipt) {
            alert('Please process a receipt first.');
            return;
        }

        const items = [];

        document.querySelectorAll('#items-tbody tr').forEach(row => {
            items.push({
                item_name: row.querySelector('.item-name').value,
                quantity: parseFloat(
                    row.querySelector('.item-quantity').value
                ) || 1,
                price: parseFloat(
                    row.querySelector('.item-price').value
                ) || 0
            });
        });

        const payload = {
            merchant_name: merchantName.value,
            receipt_date: receiptDate.value,
            category: category.value,
            payment_method: paymentMethod.value,
            subtotal: parseFloat(subtotal.value) || 0,
            tax: parseFloat(tax.value) || 0,
            total: parseFloat(total.value) || 0,

            image_filename: processedReceipt.image_filename || '',

            raw_ocr_text: processedReceipt.raw_ocr_text || '',

            items: items
        };

        try {
            const token = localStorage.getItem('token');

            const response = await fetch(
                `${API_BASE_URL}/receipts/save`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || 'Failed to save receipt'
                );
            }

            alert('Receipt saved successfully!');

            window.location.href = 'dashboard.html';

        } catch (error) {
            console.error('Failed to save receipt:', error);
            alert(`Failed to save receipt: ${error.message}`);
        }
    });
});

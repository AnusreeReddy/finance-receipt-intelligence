document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const startDateFilter = document.getElementById('start-date');
    const endDateFilter = document.getElementById('end-date');
    const receiptsTbody = document.getElementById('receipts-tbody');
    const aiInsightsContainer = document.getElementById('ai-insights');

    const editModal = document.getElementById('edit-modal');
    const editForm = document.getElementById('edit-form');
    const closeModalBtn = document.getElementById('close-modal');

    let currentEditingReceiptId = null;

    loadSummary();
    loadReceipts();
    loadAiInsights();
    loadAnomalies();

    // Event listeners for filters
    [searchInput, categoryFilter, startDateFilter, endDateFilter].forEach(el => {
        el.addEventListener('change', loadReceipts);
    });

    async function loadSummary() {
        try {
            const data = await api.request('/analytics/summary', { method: 'GET' });

            document.getElementById('total-spent').textContent =
                `$${data.total_spent.toFixed(2)}`;

            document.getElementById('total-count').textContent =
                data.total_receipts;

            const categoryList =
                document.getElementById('category-breakdown-list');

            categoryList.innerHTML = '';

            data.category_breakdown.forEach(cat => {
                const li = document.createElement('li');

                li.style.marginBottom = '0.5rem';

                li.innerHTML =
                    `<strong>${cat.category}:</strong> $${cat.total.toFixed(2)} (${cat.count} receipts)`;

                categoryList.appendChild(li);
            });

        } catch (err) {
            console.error('Failed to load summary analytics:', err);
        }
    }

    async function loadReceipts() {
        const search = searchInput.value.trim();
        const category = categoryFilter.value;
        const startDate = startDateFilter.value;
        const endDate = endDateFilter.value;

        const queryParams = new URLSearchParams({
            search,
            category,
            start_date: startDate,
            end_date: endDate
        });

        try {
            const data = await api.request(
                `/receipts?${queryParams.toString()}`,
                { method: 'GET' }
            );

            renderReceiptsTable(data.receipts || []);

        } catch (err) {
            console.error('Failed to load receipts:', err);
        }
    }

    function renderReceiptsTable(receipts) {
        receiptsTbody.innerHTML = '';

        if (receipts.length === 0) {
            receiptsTbody.innerHTML =
                `<tr><td colspan="6" style="text-align:center;">No expenses found.</td></tr>`;
            return;
        }

        receipts.forEach(r => {
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td>${r.receipt_date || 'N/A'}</td>
                <td><strong>${r.merchant_name || 'Unknown'}</strong></td>
                <td><span class="badge">${r.category || 'Other'}</span></td>
                <td>${r.payment_method || 'N/A'}</td>
                <td><strong>$${r.total.toFixed(2)}</strong></td>
                <td>
                    <button class="action-btn btn-edit"
                            onclick="openEditModal(${r.id})">
                        Edit
                    </button>

                    <button class="action-btn btn-delete"
                            onclick="deleteReceiptItem(${r.id})">
                        Delete
                    </button>
                </td>
            `;

            receiptsTbody.appendChild(tr);
        });
    }

    async function loadAiInsights() {
        try {
            const data = await api.request(
                '/analytics/insights',
                { method: 'GET' }
            );

            aiInsightsContainer.textContent =
                data.insights || "No insights available.";

        } catch (err) {
            aiInsightsContainer.textContent =
                "Unable to retrieve AI insights.";
        }
    }

    async function loadAnomalies() {
        try {
            const data = await api.request(
                '/analytics/anomalies?sensitivity=0.7',
                { method: 'GET' }
            );

            const anomalyContainer =
                document.getElementById('anomaly-insights');

            if (anomalyContainer) {
                if (data.anomalies && data.anomalies.length > 0) {

                    let anomalyHtml =
                        `<strong>⚠️ Anomalies Detected (${data.total_detected})</strong><br>`;

                    data.anomalies.slice(0, 3).forEach(anom => {

                        const severityEmoji =
                            anom.severity === 'high'
                                ? '🔴'
                                : anom.severity === 'medium'
                                    ? '🟡'
                                    : '🔵';

                        anomalyHtml +=
                            `${severityEmoji} ${anom.reason}<br>`;
                    });

                    anomalyContainer.innerHTML = anomalyHtml;

                } else {
                    anomalyContainer.innerHTML =
                        "✅ No anomalies detected. Your spending looks normal!";
                }
            }

        } catch (err) {
            console.error('Failed to load anomalies:', err);
        }
    }

    window.openEditModal = async function(id) {
        currentEditingReceiptId = id;

        try {
            const data = await api.request(
                `/receipts/${id}`,
                { method: 'GET' }
            );

            const r = data.receipt;

            document.getElementById('edit-merchant').value =
                r.merchant_name || '';

            document.getElementById('edit-date').value =
                r.receipt_date || '';

            document.getElementById('edit-category').value =
                r.category || 'Other';

            document.getElementById('edit-payment').value =
                r.payment_method || '';

            document.getElementById('edit-subtotal').value =
                r.subtotal || 0;

            document.getElementById('edit-tax').value =
                r.tax || 0;

            document.getElementById('edit-total').value =
                r.total || 0;

            editModal.style.display = 'flex';

        } catch (err) {
            alert(`Error loading receipt: ${err.message}`);
        }
    };

    closeModalBtn.addEventListener('click', () => {
        editModal.style.display = 'none';
    });

    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const payload = {
            merchant_name:
                document.getElementById('edit-merchant').value,

            receipt_date:
                document.getElementById('edit-date').value,

            category:
                document.getElementById('edit-category').value,

            payment_method:
                document.getElementById('edit-payment').value,

            subtotal:
                parseFloat(
                    document.getElementById('edit-subtotal').value
                ) || 0,

            tax:
                parseFloat(
                    document.getElementById('edit-tax').value
                ) || 0,

            total:
                parseFloat(
                    document.getElementById('edit-total').value
                ) || 0
        };

        try {
            await api.request(
                `/receipts/${currentEditingReceiptId}`,
                {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                }
            );

            editModal.style.display = 'none';

            loadSummary();
            loadReceipts();
            loadAiInsights();
            loadAnomalies();

        } catch (err) {
            alert(`Failed to update receipt: ${err.message}`);
        }
    });

    window.deleteReceiptItem = async function(id) {
        if (!confirm(
            'Are you sure you want to delete this expense receipt?'
        )) {
            return;
        }

        try {
            await api.request(
                `/receipts/${id}`,
                { method: 'DELETE' }
            );

            loadSummary();
            loadReceipts();
            loadAiInsights();
            loadAnomalies();

        } catch (err) {
            alert(`Failed to delete receipt: ${err.message}`);
        }
    };
});
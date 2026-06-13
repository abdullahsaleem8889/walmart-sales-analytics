// =====================================================================
// INSIGHTS JAVASCRIPT - ENHANCED WITH ERROR HANDLING
// =====================================================================

let topStoresChartInstance, seasonalChartInstance;

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] Insights page initialized');
    loadInsightsData();
});

function loadInsightsData() {
    console.log('[INFO] Fetching insights data...');
    
    fetch('/api/insights')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[SUCCESS] Insights data loaded:', data);
            
            if (data.status === 'success') {
                try {
                    displaySummary(data.summary);
                    displayTopStoresChart(data.top_stores);
                    displaySeasonalPattern(data.seasonal_pattern);
                } catch (e) {
                    console.error('[ERROR] Error rendering insights:', e);
                    showErrorMessage('Error rendering insights: ' + e.message);
                }
            } else {
                console.error('[ERROR] API returned error status:', data.message || data.status);
                showErrorMessage('Failed to load insights: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('[ERROR] Error loading insights:', error);
            showErrorMessage('Error loading insights: ' + error.message);
        });
}

function displaySummary(summary) {
    console.log('[INFO] Displaying summary:', summary);
    
    try {
        if (!summary) {
            throw new Error('Summary data is missing');
        }

        const totalSales = parseFloat(summary.total_sales) || 0;
        const holidayImpact = parseFloat(summary.holiday_impact_percent) || 0;
        
        const totalSalesElem = document.getElementById('totalSales');
        const holidayImpactElem = document.getElementById('holidayImpact');
        
        if (totalSalesElem) {
            totalSalesElem.textContent = '$' + (totalSales / 1000000).toLocaleString(undefined, {maximumFractionDigits: 1}) + 'M';
        }
        
        if (holidayImpactElem) {
            holidayImpactElem.textContent = `+${holidayImpact.toFixed(1)}%`;
        }

        // Update metrics in cards
        const regularWeekAvg = parseFloat(summary.regular_week_avg) || 0;
        const holidayWeekAvg = parseFloat(summary.holiday_week_avg) || 0;
        
        const detailsHtml = `
            <strong>Regular Week:</strong> $${regularWeekAvg.toLocaleString(undefined, {maximumFractionDigits: 0})}<br/>
            <strong>Holiday Week:</strong> $${holidayWeekAvg.toLocaleString(undefined, {maximumFractionDigits: 0})}<br/>
            <strong>Lift:</strong> +${holidayImpact.toFixed(1)}%
        `;
        
        const card = document.querySelector('#holidayImpact')?.closest('.card');
        const details = card?.querySelector('p');
        if (details) {
            details.innerHTML = detailsHtml;
        }
        
        console.log('[SUCCESS] Summary displayed successfully');
    } catch (e) {
        console.error('[ERROR] Error displaying summary:', e);
        showErrorMessage('Error displaying summary');
    }
}

function displayTopStoresChart(topStores) {
    console.log('[INFO] Rendering top stores chart:', topStores);
    
    const ctx = document.getElementById('topStoresChart');
    
    if (!ctx) {
        console.error('[ERROR] Top stores chart canvas not found');
        return;
    }
    
    // Destroy existing chart if it exists
    if (topStoresChartInstance) {
        topStoresChartInstance.destroy();
    }
    
    try {
        if (!topStores || Object.keys(topStores).length === 0) {
            console.warn('[WARNING] No top stores data available');
            ctx.parentElement.innerHTML = '<p class="text-muted">No data available</p>';
            return;
        }
        
        const stores = Object.keys(topStores);
        const values = Object.values(topStores).map(v => parseFloat(v) || 0);

        topStoresChartInstance = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stores.map(s => `Store ${s}`),
                datasets: [{
                    label: 'Average Sales ($)',
                    data: values,
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#fa7921'],
                    borderRadius: 6,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { callback: v => '$' + v.toLocaleString() }
                    }
                }
            }
        });
        
        console.log('[SUCCESS] Top stores chart rendered');
    } catch (e) {
        console.error('[ERROR] Error rendering top stores chart:', e);
        showErrorMessage('Error rendering top stores chart');
    }
}

function displaySeasonalPattern(seasonal) {
    console.log('[INFO] Rendering seasonal pattern chart:', seasonal);
    
    const ctx = document.getElementById('seasonalChart');
    
    if (!ctx) {
        console.error('[ERROR] Seasonal chart canvas not found');
        return;
    }
    
    // Destroy existing chart if it exists
    if (seasonalChartInstance) {
        seasonalChartInstance.destroy();
    }
    
    try {
        if (!seasonal || Object.keys(seasonal).length === 0) {
            console.warn('[WARNING] No seasonal data available');
            ctx.parentElement.innerHTML = '<p class="text-muted">No data available</p>';
            return;
        }
        
        const months = Object.keys(seasonal);
        const values = Object.values(seasonal).map(v => parseFloat(v) || 0);

        seasonalChartInstance = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Monthly Average Sales ($)',
                    data: values,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#764ba2',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: v => '$' + v.toLocaleString() }
                    }
                }
            }
        });
        
        console.log('[SUCCESS] Seasonal pattern chart rendered');
    } catch (e) {
        console.error('[ERROR] Error rendering seasonal pattern chart:', e);
        showErrorMessage('Error rendering seasonal pattern chart');
    }
}

function showErrorMessage(message) {
    console.error('[ERROR] Showing error:', message);
    const container = document.querySelector('.container-fluid');
    if (container) {
        const existingAlert = container.querySelector('.alert-danger');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.role = 'alert';
        alert.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        container.prepend(alert);
    }
}

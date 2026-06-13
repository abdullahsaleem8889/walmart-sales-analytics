// =====================================================================
// ANALYTICS JAVASCRIPT - ENHANCED WITH ERROR HANDLING
// =====================================================================

let distributionChart, storeTypeChart, sizeAnalysisChart;

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] Analytics page initialized');
    loadAnalyticsData();
});

function loadAnalyticsData() {
    console.log('[INFO] Fetching analytics data...');
    
    fetch('/api/analytics')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[SUCCESS] Analytics data loaded:', data);
            
            if (data.status === 'success') {
                try {
                    displaySalesDistribution(data.sales_distribution);
                    displayStatistics(data.sales_distribution);
                    displayStoreTypeAnalysis(data.store_types);
                    displaySizeAnalysis(data.size_analysis);
                } catch (e) {
                    console.error('[ERROR] Error rendering analytics:', e);
                    showErrorMessage('Error rendering analytics: ' + e.message);
                }
            } else {
                console.error('[ERROR] API returned error status:', data.message || data.status);
                showErrorMessage('Failed to load analytics: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('[ERROR] Error loading analytics data:', error);
            showErrorMessage('Error loading analytics: ' + error.message);
        });
}

function displaySalesDistribution(stats) {
    // Create histogram-like visualization
    const ctx = document.getElementById('distributionChart');
    
    if (!ctx) {
        console.error('[ERROR] Distribution chart canvas not found');
        return;
    }
    
    // Destroy existing chart if it exists
    if (distributionChart) {
        distributionChart.destroy();
    }
    
    try {
        if (!stats || typeof stats.min === 'undefined' || typeof stats.max === 'undefined') {
            throw new Error('Invalid statistics data');
        }
        
        distributionChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Min', 'Min+', 'Median', 'Mean', 'Max-', 'Max'],
                datasets: [{
                    label: 'Sales Value ($)',
                    data: [stats.min, stats.min + (stats.median - stats.min) * 0.5, stats.median, stats.mean, stats.max - (stats.max - stats.median) * 0.5, stats.max],
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#fa7921', '#ff9d00'],
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: v => '$' + v.toLocaleString() }
                    }
                }
            }
        });
        
        console.log('[SUCCESS] Sales distribution chart rendered');
    } catch (e) {
        console.error('[ERROR] Error rendering distribution chart:', e);
        showErrorMessage('Error rendering distribution chart');
    }
}

function displayStatistics(stats) {
    const tbody = document.getElementById('statsTable');
    
    if (!tbody) {
        console.error('[ERROR] Statistics table not found');
        return;
    }
    
    try {
        if (!stats) {
            throw new Error('Statistics data is missing');
        }
        
        tbody.innerHTML = `
            <tr>
                <td><strong>Count</strong></td>
                <td>${Number(stats.count || 0).toLocaleString()}</td>
            </tr>
            <tr>
                <td><strong>Mean</strong></td>
                <td>$${(stats.mean || 0).toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
            <tr>
                <td><strong>Median</strong></td>
                <td>$${(stats.median || 0).toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
            <tr>
                <td><strong>Std Dev</strong></td>
                <td>$${(stats.std || 0).toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
            <tr>
                <td><strong>Min</strong></td>
                <td>$${(stats.min || 0).toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
            <tr>
                <td><strong>Max</strong></td>
                <td>$${(stats.max || 0).toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
        `;
        
        console.log('[SUCCESS] Statistics table rendered');
    } catch (e) {
        console.error('[ERROR] Error rendering statistics:', e);
        tbody.innerHTML = '<tr><td colspan="2" class="text-danger">Error loading statistics</td></tr>';
        showErrorMessage('Error rendering statistics');
    }
}

function displayStoreTypeAnalysis(storeTypes) {
    const ctx = document.getElementById('storeTypeChart');
    
    if (!ctx) {
        console.error('[ERROR] Store type chart canvas not found');
        return;
    }
    
    // Destroy existing chart if it exists
    if (storeTypeChart) {
        storeTypeChart.destroy();
    }
    
    try {
        if (!storeTypes || Object.keys(storeTypes).length === 0) {
            console.warn('[WARNING] No store type data available');
            ctx.parentElement.innerHTML = '<p class="text-muted">No data available</p>';
            return;
        }
        
        const types = [];
        const means = [];
        const stds = [];

        Object.entries(storeTypes).forEach(([type, values]) => {
            types.push(type);
            means.push(parseFloat(values.mean) || 0);
            stds.push(parseFloat(values.std) || 0);
        });

        storeTypeChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: types,
                datasets: [{
                    label: 'Average Sales ($)',
                    data: means,
                    backgroundColor: ['#667eea', '#764ba2', '#f5576c'],
                    borderRadius: 6,
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
        
        console.log('[SUCCESS] Store type chart rendered');
    } catch (e) {
        console.error('[ERROR] Error rendering store type chart:', e);
        showErrorMessage('Error rendering store type analysis');
    }
}

function displaySizeAnalysis(sizeData) {
    const ctx = document.getElementById('sizeAnalysisChart');
    
    if (!ctx) {
        console.error('[ERROR] Size analysis chart canvas not found');
        return;
    }
    
    // Destroy existing chart if it exists
    if (sizeAnalysisChart) {
        sizeAnalysisChart.destroy();
    }
    
    try {
        if (!sizeData || Object.keys(sizeData).length === 0) {
            console.warn('[WARNING] No size analysis data available');
            ctx.parentElement.innerHTML = '<p class="text-muted">No data available</p>';
            return;
        }
        
        const labels = Object.keys(sizeData).map((i, idx) => `Size ${idx + 1}`);
        const values = Object.values(sizeData).map(v => parseFloat(v) || 0);

        sizeAnalysisChart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Sales ($)',
                    data: values,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#764ba2',
                    pointRadius: 6,
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
        
        console.log('[SUCCESS] Size analysis chart rendered');
    } catch (e) {
        console.error('[ERROR] Error rendering size analysis chart:', e);
        showErrorMessage('Error rendering size analysis');
    }
}

function showErrorMessage(message) {
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

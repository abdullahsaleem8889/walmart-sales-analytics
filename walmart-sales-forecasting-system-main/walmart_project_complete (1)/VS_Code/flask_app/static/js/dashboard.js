// =====================================================================
// DASHBOARD JAVASCRIPT - ENHANCED WITH ERROR HANDLING
// =====================================================================

let holidayChart, monthlyChart;

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] Dashboard initialized');
    loadDashboardData();
});

function loadDashboardData() {
    console.log('[INFO] Fetching dashboard data...');
    
    fetch('/api/overview')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[SUCCESS] Dashboard data loaded:', data);
            
            if (data.status === 'success') {
                displayHolidayImpact(data.holiday_impact);
                displayMonthlyTrend(data.monthly_trend);
                displayTopStores(data.stores.top);
                displayTopDepartments(data.departments.top);
            } else {
                console.error('[ERROR] API returned error status:', data.message);
                showErrorMessage('Failed to load dashboard data: ' + data.message);
            }
        })
        .catch(error => {
            console.error('[ERROR] Error loading dashboard data:', error);
            showErrorMessage('Error loading data: ' + error.message);
        });
}

function displayHolidayImpact(holiday_impact) {
    const ctx = document.getElementById('holidayChart');
    
    if (!ctx) {
        console.error('[ERROR] Holiday chart canvas not found');
        return;
    }
    
    // Destroy existing chart if it exists
    if (holidayChart) {
        holidayChart.destroy();
    }
    
    // Create beautiful gradients
    const gradientRegular = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradientRegular.addColorStop(0, '#4f46e5'); // Indigo
    gradientRegular.addColorStop(1, '#818cf8');
    
    const gradientHoliday = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradientHoliday.addColorStop(0, '#ec4899'); // Pink
    gradientHoliday.addColorStop(1, '#f472b6');

    holidayChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Regular Weeks', 'Holiday Weeks'],
            datasets: [{
                label: 'Average Sales ($)',
                data: [holiday_impact.regular, holiday_impact.holiday],
                backgroundColor: [gradientRegular, gradientHoliday],
                borderRadius: 8,
                borderSkipped: false,
                barPercentage: 0.6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 2000,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(31, 41, 55, 0.9)',
                    titleFont: { size: 14, family: 'Inter' },
                    bodyFont: { size: 14, family: 'Inter' },
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { borderDash: [5, 5], color: '#e5e7eb', drawBorder: false },
                    ticks: { callback: v => '$' + v.toLocaleString(), font: { family: 'Inter' } }
                },
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { font: { family: 'Inter', weight: '600' } }
                }
            }
        }
    });

    // Display lift percentage
    const wrapper = ctx.parentElement;
    const existingAlert = wrapper.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    const liftDiv = document.createElement('div');
    liftDiv.className = 'alert alert-success mt-3';
    liftDiv.innerHTML = `
        <strong>Holiday Lift: +${holiday_impact.lift.toFixed(2)}%</strong><br/>
        Regular weeks: ${holiday_impact.regular_count} | Holiday weeks: ${holiday_impact.holiday_count}<br/>
        Regular week average: $${holiday_impact.regular.toLocaleString()}<br/>
        Holiday week average: $${holiday_impact.holiday.toLocaleString()}
    `;
    wrapper.appendChild(liftDiv);
    
    console.log('[SUCCESS] Holiday impact chart rendered');
}

function displayMonthlyTrend(monthly_trend) {
    const ctx = document.getElementById('monthlyChart');
    
    if (!ctx) {
        console.error('[ERROR] Monthly trend canvas not found');
        return;
    }
    
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const values = months.map((m, i) => monthly_trend[i + 1] || 0);

    // Destroy existing chart if it exists
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    const gradientFill = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradientFill.addColorStop(0, 'rgba(79, 70, 229, 0.4)');
    gradientFill.addColorStop(1, 'rgba(79, 70, 229, 0.05)');

    monthlyChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: months,
            datasets: [{
                label: 'Average Sales ($)',
                data: values,
                borderColor: '#4f46e5',
                backgroundColor: gradientFill,
                borderWidth: 4,
                fill: true,
                tension: 0.5, // Smooth curves
                pointBackgroundColor: '#ec4899',
                pointBorderColor: '#fff',
                pointBorderWidth: 3,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 2500,
                easing: 'easeOutBounce'
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(31, 41, 55, 0.9)',
                    padding: 12,
                    cornerRadius: 8,
                    bodyFont: { family: 'Inter', size: 14 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { borderDash: [5, 5], color: '#e5e7eb', drawBorder: false },
                    ticks: { callback: v => '$' + v.toLocaleString(), font: { family: 'Inter' } }
                },
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { font: { family: 'Inter' } }
                }
            }
        }
    });
    
    console.log('[SUCCESS] Monthly trend chart rendered');
}

function displayTopStores(stores) {
    const container = document.getElementById('topStoresContainer');
    
    if (!container) {
        console.error('[ERROR] Top stores container not found');
        return;
    }
    
    container.innerHTML = '';

    if (!stores || Object.keys(stores).length === 0) {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
    }

    const storesList = Object.entries(stores).slice(0, 10);
    
    storesList.forEach(([store, data], index) => {
        try {
            const row = document.createElement('div');
            row.className = 'mb-3 pb-3 border-bottom';
            row.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1"><i class="bi bi-shop"></i> Store ${store}</h6>
                        <small class="text-muted">Avg: $${parseFloat(data[0]).toLocaleString(undefined, {maximumFractionDigits: 0})}</small>
                    </div>
                    <span class="badge bg-primary">#${index + 1}</span>
                </div>
            `;
            container.appendChild(row);
        } catch (e) {
            console.error('[ERROR] Error rendering store:', e);
        }
    });
    
    console.log('[SUCCESS] Top stores rendered');
}

function displayTopDepartments(departments) {
    const container = document.getElementById('topDeptsContainer');
    
    if (!container) {
        console.error('[ERROR] Top departments container not found');
        return;
    }
    
    container.innerHTML = '';

    if (!departments || Object.keys(departments).length === 0) {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
    }

    const deptsList = Object.entries(departments).slice(0, 10);
    
    deptsList.forEach(([dept, data], index) => {
        try {
            const row = document.createElement('div');
            row.className = 'mb-3 pb-3 border-bottom';
            row.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1"><i class="bi bi-bag"></i> Department ${dept}</h6>
                        <small class="text-muted">Avg: $${parseFloat(data[0]).toLocaleString(undefined, {maximumFractionDigits: 0})}</small>
                    </div>
                    <span class="badge bg-success">#${index + 1}</span>
                </div>
            `;
            container.appendChild(row);
        } catch (e) {
            console.error('[ERROR] Error rendering department:', e);
        }
    });
    
    console.log('[SUCCESS] Top departments rendered');
}

function showErrorMessage(message) {
    const container = document.querySelector('.container-fluid');
    if (container) {
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


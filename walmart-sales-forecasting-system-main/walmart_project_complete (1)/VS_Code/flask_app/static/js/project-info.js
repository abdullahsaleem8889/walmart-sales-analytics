// =====================================================================
// PROJECT INFO JAVASCRIPT - ENHANCED WITH ERROR HANDLING
// =====================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] Project info page initialized');
    loadProjectInfo();
});

function loadProjectInfo() {
    console.log('[INFO] Fetching project information...');
    
    fetch('/api/project-info')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[SUCCESS] Project info loaded:', data);
            
            try {
                displayProjectOverview(data);
                if (data.data_stats) displayDatasetInfo(data.data_stats);
                if (data.performance) displayPerformance(data.performance);
                if (data.features) displayFeatures(data.features);
                if (data.models) displayModels(data.models);
            } catch (e) {
                console.error('[ERROR] Error rendering project info:', e);
                showErrorMessage('Error rendering project information: ' + e.message);
            }
        })
        .catch(error => {
            console.error('[ERROR] Error loading project info:', error);
            showErrorMessage('Error loading project information: ' + error.message);
        });
}

function displayProjectOverview(data) {
    console.log('[INFO] Displaying project overview');
    
    try {
        const titleElem = document.getElementById('projectTitle');
        const descElem = document.getElementById('projectDesc');
        
        if (titleElem) titleElem.textContent = data.title || 'Walmart Sales Forecasting';
        if (descElem) descElem.textContent = data.description || 'Advanced ML project for sales prediction';
        
        console.log('[SUCCESS] Project overview displayed');
    } catch (e) {
        console.error('[ERROR] Error displaying project overview:', e);
    }
}

function displayDatasetInfo(stats) {
    console.log('[INFO] Displaying dataset info:', stats);
    
    try {
        if (!stats) {
            throw new Error('Dataset statistics are missing');
        }
        
        const html = `
            <table class="table table-sm">
                <tr>
                    <td><strong>Number of Stores:</strong></td>
                    <td>${stats.stores || 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>Departments:</strong></td>
                    <td>${stats.departments || 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>Total Records:</strong></td>
                    <td>${Number(stats.records || 0).toLocaleString()}</td>
                </tr>
                <tr>
                    <td><strong>Date Range:</strong></td>
                    <td>${stats.date_range || 'N/A'}</td>
                </tr>
            </table>
        `;
        
        const container = document.getElementById('datasetInfo');
        if (container) {
            container.innerHTML = html;
        }
        
        console.log('[SUCCESS] Dataset info displayed');
    } catch (e) {
        console.error('[ERROR] Error displaying dataset info:', e);
        const container = document.getElementById('datasetInfo');
        if (container) {
            container.innerHTML = '<p class="text-danger">Error loading dataset information</p>';
        }
    }
}

function displayPerformance(performance) {
    console.log('[INFO] Displaying performance metrics:', performance);
    
    try {
        if (!performance) {
            throw new Error('Performance data is missing');
        }
        
        const html = `
            <table class="table table-sm">
                <tr>
                    <td><strong>RMSE:</strong></td>
                    <td><span class="badge bg-success">${performance.RMSE || 'N/A'}</span></td>
                </tr>
                <tr>
                    <td><strong>MAE:</strong></td>
                    <td><span class="badge bg-success">${performance.MAE || 'N/A'}</span></td>
                </tr>
                <tr>
                    <td><strong>R² Score:</strong></td>
                    <td><span class="badge bg-success">${performance['R² Score'] || 'N/A'}</span></td>
                </tr>
                <tr>
                    <td><strong>MAPE:</strong></td>
                    <td><span class="badge bg-success">${performance.MAPE || 'N/A'}</span></td>
                </tr>
            </table>
        `;
        
        const container = document.getElementById('performanceInfo');
        if (container) {
            container.innerHTML = html;
        }
        
        console.log('[SUCCESS] Performance metrics displayed');
    } catch (e) {
        console.error('[ERROR] Error displaying performance metrics:', e);
        const container = document.getElementById('performanceInfo');
        if (container) {
            container.innerHTML = '<p class="text-danger">Error loading performance information</p>';
        }
    }
}

function displayFeatures(features) {
    console.log('[INFO] Displaying features:', features);
    
    try {
        const container = document.getElementById('featuresContainer');
        
        if (!container) {
            console.error('[ERROR] Features container not found');
            return;
        }
        
        container.innerHTML = '';

        if (!features || features.length === 0) {
            console.warn('[WARNING] No features data available');
            container.innerHTML = '<p class="text-muted">No features available</p>';
            return;
        }

        features.forEach((feature, index) => {
            try {
                const col = document.createElement('div');
                col.className = 'col-md-6 mb-3';
                col.innerHTML = `
                    <div class="card h-100 border-left-primary">
                        <div class="card-body">
                            <h6 class="mb-2">
                                <i class="bi bi-check-circle text-primary"></i> ${feature || 'Feature'}
                            </h6>
                        </div>
                    </div>
                `;
                container.appendChild(col);
            } catch (e) {
                console.error('[ERROR] Error rendering feature:', e);
            }
        });
        
        console.log('[SUCCESS] Features displayed');
    } catch (e) {
        console.error('[ERROR] Error displaying features:', e);
    }
}

function displayModels(models) {
    console.log('[INFO] Displaying models:', models);
    
    try {
        const container = document.getElementById('modelsContainer');
        
        if (!container) {
            console.error('[ERROR] Models container not found');
            return;
        }
        
        container.innerHTML = '';

        if (!models || models.length === 0) {
            console.warn('[WARNING] No models data available');
            container.innerHTML = '<p class="text-muted">No models available</p>';
            return;
        }

        models.forEach((model, index) => {
            try {
                const col = document.createElement('div');
                col.className = 'col-md-4 mb-3';
                col.innerHTML = `
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <i class="bi bi-cpu" style="font-size: 2rem; color: #667eea;"></i>
                            <h6 class="mt-2 mb-0">${model || 'Model'}</h6>
                        </div>
                    </div>
                `;
                container.appendChild(col);
            } catch (e) {
                console.error('[ERROR] Error rendering model:', e);
            }
        });
        
        console.log('[SUCCESS] Models displayed');
    } catch (e) {
        console.error('[ERROR] Error displaying models:', e);
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

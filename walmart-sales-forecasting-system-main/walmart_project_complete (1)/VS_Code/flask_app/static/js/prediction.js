// =====================================================================
// PREDICTION JAVASCRIPT - ENHANCED WITH ERROR HANDLING
// =====================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] Prediction page initialized');
    const predictionForm = document.getElementById('predictionForm');
    const storeSelect = document.getElementById('storeSelect');
    
    if (predictionForm) {
        predictionForm.addEventListener('submit', handlePrediction);
    } else {
        console.error('[ERROR] Prediction form not found');
    }
    
    // Add event listener to store select to load valid departments
    if (storeSelect) {
        storeSelect.addEventListener('change', function() {
            const storeId = this.value;
            if (storeId) {
                loadValidDepartments(storeId);
            }
        });
    }
});

function loadValidDepartments(storeId) {
    console.log('[INFO] Loading valid departments for Store:', storeId);
    
    const deptSelect = document.getElementById('deptSelect');
    if (!deptSelect) {
        console.error('[ERROR] Department select not found');
        return;
    }
    
    // Disable while loading
    deptSelect.disabled = true;
    deptSelect.innerHTML = '<option value="">Loading departments...</option>';
    
    fetch(`/api/combinations/${storeId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[INFO] Valid departments loaded:', data);
            
            if (data.status === 'success') {
                // Populate department dropdown
                deptSelect.innerHTML = '<option value="">Choose a department...</option>';
                data.departments.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept;
                    option.textContent = `Department ${dept}`;
                    deptSelect.appendChild(option);
                });
                deptSelect.disabled = false;
                hideError();
                console.log('[OK] Department dropdown populated');
            } else {
                console.error('[ERROR] Failed to load departments:', data.message);
                deptSelect.innerHTML = '<option value="">Error loading departments</option>';
                deptSelect.disabled = true;
                showError('No valid departments found for this store');
            }
        })
        .catch(error => {
            console.error('[ERROR] Failed to fetch departments:', error);
            deptSelect.innerHTML = '<option value="">Error loading departments</option>';
            deptSelect.disabled = true;
            showError('Error loading departments: ' + error.message);
        });
}

function handlePrediction(e) {
    e.preventDefault();
    console.log('[INFO] Processing prediction request');
    
    const storeSelect = document.getElementById('storeSelect');
    const deptSelect = document.getElementById('deptSelect');
    
    if (!storeSelect || !deptSelect) {
        console.error('[ERROR] Select elements not found');
        showError('Form elements not found');
        return;
    }

    const store = storeSelect.value;
    const dept = deptSelect.value;

    if (!store || !dept) {
        console.warn('[WARNING] Missing required fields');
        showError('Please select both store and department');
        return;
    }

    // Validate numeric values
    const storeNum = parseInt(store);
    const deptNum = parseInt(dept);
    
    if (isNaN(storeNum) || isNaN(deptNum)) {
        console.error('[ERROR] Invalid store or department values:', store, dept);
        showError('Invalid store or department selection');
        return;
    }

    // Show loading state
    const predictions = document.getElementById('predictions');
    if (predictions) {
        predictions.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Generating prediction...</p></div>';
    }

    console.log('[INFO] Sending prediction request - Store:', storeNum, 'Dept:', deptNum);
    
    // Send prediction request
    fetch('/api/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            store: storeNum,
            department: deptNum
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('[SUCCESS] Prediction response received:', data);
        
        if (data.status === 'success') {
            console.log('[SUCCESS] Displaying prediction results');
            displayPrediction(data.prediction);
            hideError();
        } else {
            console.error('[ERROR] API error:', data.message);
            showError(data.message || 'Failed to generate prediction');
        }
    })
    .catch(error => {
        console.error('[ERROR] Prediction request failed:', error);
        showError('Error: ' + error.message);
    });
}

function displayPrediction(prediction) {
    console.log('[INFO] Displaying prediction:', prediction);
    
    const resultCard = document.getElementById('resultCard');
    const noResultCard = document.getElementById('noResultCard');

    if (!resultCard || !noResultCard) {
        console.error('[ERROR] Result card elements not found');
        showError('Unable to display prediction results');
        return;
    }

    try {
        // Validate prediction data
        if (!prediction || prediction.predicted_sales === undefined) {
            throw new Error('Invalid prediction data received');
        }

        // Update prediction values with proper validation
        const predictedSales = parseFloat(prediction.predicted_sales) || 0;
        const confidence = prediction.confidence || 'N/A';
        const historicalAvg = parseFloat(prediction.historical_avg) || 0;
        const trendSales = parseFloat(prediction.trend_sales) || 0;
        const maxSales = parseFloat(prediction.max_sales) || 0;
        const minSales = parseFloat(prediction.min_sales) || 0;

        document.getElementById('predictedSales').textContent = '$' + predictedSales.toLocaleString(undefined, {maximumFractionDigits: 2});
        document.getElementById('confidence').textContent = typeof confidence === 'number' ? confidence.toFixed(2) + '%' : confidence;
        
        document.getElementById('resultStore').textContent = `Store #${prediction.store || 'N/A'}`;
        document.getElementById('resultDept').textContent = `Department #${prediction.department || 'N/A'}`;
        document.getElementById('histAvg').textContent = '$' + historicalAvg.toLocaleString(undefined, {maximumFractionDigits: 2});
        document.getElementById('trendAvg').textContent = '$' + trendSales.toLocaleString(undefined, {maximumFractionDigits: 2});
        document.getElementById('maxSales').textContent = '$' + maxSales.toLocaleString(undefined, {maximumFractionDigits: 2});
        document.getElementById('minSales').textContent = '$' + minSales.toLocaleString(undefined, {maximumFractionDigits: 2});

        // Show result card, hide no result card
        resultCard.style.display = 'block';
        noResultCard.style.display = 'none';

        // Add animation
        if (resultCard.classList) {
            resultCard.classList.add('animate-slide');
        }
        
        console.log('[SUCCESS] Prediction displayed successfully');
    } catch (e) {
        console.error('[ERROR] Error displaying prediction:', e);
        showError('Error displaying prediction: ' + e.message);
    }
}

function showError(message) {
    console.error('[ERROR] Showing error message:', message);
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    
    if (!errorAlert || !errorMessage) {
        console.error('[ERROR] Error alert elements not found');
        alert('Error: ' + message);
        return;
    }
    
    errorMessage.textContent = message;
    errorAlert.style.display = 'block';
}

function hideError() {
    console.log('[INFO] Hiding error message');
    const errorAlert = document.getElementById('errorAlert');
    if (errorAlert) {
        errorAlert.style.display = 'none';
    }
}

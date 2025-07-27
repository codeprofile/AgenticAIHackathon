// Market Dashboard JavaScript

let chartInstance = null;
let marketData = [];
let alerts = [];

// Chart initialization
function initializeChart() {
    const canvas = document.getElementById('chartCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Mock data for demonstration
    const mockData = {
        labels: ['1D ago', '12H ago', '6H ago', '3H ago', '1H ago', 'Now'],
        datasets: [{
            label: 'गेहूं',
            data: [2100, 2120, 2135, 2140, 2145, 2150],
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            tension: 0.4
        }, {
            label: 'मक्का',
            data: [1870, 1865, 1860, 1855, 1850, 1850],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.4
        }, {
            label: 'टमाटर',
            data: [37, 39, 41, 43, 44, 45],
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4
        }]
    };

    // Simple canvas chart implementation
    drawChart(ctx, mockData, canvas.width, canvas.height);
}

function drawChart(ctx, data, width, height) {
    ctx.clearRect(0, 0, width, height);

    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    // Get all values to determine scale
    const allValues = data.datasets.flatMap(dataset => dataset.data);
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const valueRange = maxValue - minValue;

    // Draw grid lines
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;

    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
        const y = padding + (chartHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }

    // Vertical grid lines
    for (let i = 0; i < data.labels.length; i++) {
        const x = padding + (chartWidth / (data.labels.length - 1)) * i;
        ctx.beginPath();
        ctx.moveTo(x, padding);
        ctx.lineTo(x, height - padding);
        ctx.stroke();
    }

    // Draw datasets
    data.datasets.forEach((dataset, datasetIndex) => {
        ctx.strokeStyle = dataset.borderColor;
        ctx.lineWidth = 2;
        ctx.beginPath();

        dataset.data.forEach((value, index) => {
            const x = padding + (chartWidth / (data.labels.length - 1)) * index;
            const y = height - padding - ((value - minValue) / valueRange) * chartHeight;

            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // Draw points
        ctx.fillStyle = dataset.borderColor;
        dataset.data.forEach((value, index) => {
            const x = padding + (chartWidth / (data.labels.length - 1)) * index;
            const y = height - padding - ((value - minValue) / valueRange) * chartHeight;

            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
        });
    });

    // Draw labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '12px Inter';
    ctx.textAlign = 'center';

    data.labels.forEach((label, index) => {
        const x = padding + (chartWidth / (data.labels.length - 1)) * index;
        ctx.fillText(label, x, height - 10);
    });

    // Draw y-axis labels
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
        const value = minValue + (valueRange / 5) * (5 - i);
        const y = padding + (chartHeight / 5) * i;
        ctx.fillText(`₹${Math.round(value)}`, padding - 10, y + 4);
    }

    // Draw legend
    ctx.textAlign = 'left';
    let legendY = 20;
    data.datasets.forEach((dataset, index) => {
        ctx.fillStyle = dataset.borderColor;
        ctx.fillRect(width - 100, legendY + index * 20, 15, 15);
        ctx.fillStyle = '#374151';
        ctx.fillText(dataset.label, width - 80, legendY + index * 20 + 12);
    });
}

function updateChart(period) {
    // In a real implementation, this would fetch new data based on the period
    console.log(`Updating chart for period: ${period}`);

    // Simulate loading
    const canvas = document.getElementById('chartCanvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#6b7280';
        ctx.font = '16px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(`Loading ${period} data...`, canvas.width / 2, canvas.height / 2);

        setTimeout(() => {
            initializeChart();
        }, 1000);
    }
}

// Market data functions
function updateMarketData() {
    fetch('/api/market-data')
        .then(response => response.json())
        .then(data => {
            marketData = data.data;
            updateMarketTable();
        })
        .catch(error => {
            console.error('Failed to update market data:', error);
        });
}

function updateMarketTable() {
    const tableBody = document.querySelector('.market-table tbody');
    if (!tableBody || !marketData.length) return;

    // Update existing rows with new data
    const rows = tableBody.querySelectorAll('.market-row');
    rows.forEach((row, index) => {
        if (marketData[index]) {
            const market = marketData[index];

            // Update price
            const priceCell = row.querySelector('.current-price');
            if (priceCell) {
                priceCell.textContent = `₹${market.current_price}`;
            }

            // Update change
            const changeCell = row.querySelector('.price-change');
            if (changeCell) {
                changeCell.textContent = `${market.price_change > 0 ? '+' : ''}₹${market.price_change}`;
                changeCell.className = `price-change ${market.price_change > 0 ? 'positive' : 'negative'}`;
            }

            // Update percentage
            const percentageCell = row.querySelector('.percentage-change');
            if (percentageCell) {
                percentageCell.textContent = `${market.percentage_change > 0 ? '+' : ''}${market.percentage_change}%`;
                percentageCell.className = `percentage-change ${market.percentage_change > 0 ? 'positive' : 'negative'}`;
            }

            // Update trend
            const trendCell = row.querySelector('.trend-indicator');
            if (trendCell) {
                trendCell.textContent = market.trend === 'up' ? '📈' : '📉';
            }

            // Add flash effect for updated rows
            row.style.backgroundColor = '#f0fdf4';
            setTimeout(() => {
                row.style.backgroundColor = '';
            }, 2000);
        }
    });
}

// Alert functions
function saveAlert(alert) {
    alerts.push(alert);
    localStorage.setItem('marketAlerts', JSON.stringify(alerts));
    updateAlertsList();
}

function loadAlerts() {
    const savedAlerts = localStorage.getItem('marketAlerts');
    if (savedAlerts) {
        alerts = JSON.parse(savedAlerts);
        updateAlertsList();
    }
}

function updateAlertsList() {
    // This would update a UI component showing active alerts
    console.log('Active alerts:', alerts);
}

function checkAlerts() {
    alerts.forEach(alert => {
        const marketItem = marketData.find(item => item.crop_name === alert.crop);
        if (marketItem) {
            const currentPrice = marketItem.current_price;
            const targetPrice = parseFloat(alert.price);

            if ((alert.type === 'above' && currentPrice >= targetPrice) ||
                (alert.type === 'below' && currentPrice <= targetPrice)) {

                showNotification(
                    `🔔 अलर्ट: ${alert.crop} का दाम ₹${currentPrice} हो गया!`,
                    'warning'
                );

                // Remove triggered alert
                alerts = alerts.filter(a => a !== alert);
                localStorage.setItem('marketAlerts', JSON.stringify(alerts));
            }
        }
    });
}

// Detailed analysis functions
function showDetailedAnalysis(data) {
    const modal = document.createElement('div');
    modal.className = 'analysis-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>📊 ${data.crop_name} - विस्तृत विश्लेषण</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="analysis-section">
                    <h4>मूल्य विश्लेषण</h4>
                    <p>वर्तमान भाव: <strong>₹${data.current_price}</strong></p>
                    <p>आज का बदलाव: <strong class="${data.price_change > 0 ? 'positive' : 'negative'}">
                        ${data.price_change > 0 ? '+' : ''}₹${data.price_change} (${data.percentage_change}%)
                    </strong></p>
                </div>

                <div class="analysis-section">
                    <h4>बाजार की स्थिति</h4>
                    <p>ट्रेंड: <strong>${data.trend === 'up' ? '📈 तेजी' : '📉 मंदी'}</strong></p>
                    <p>मुख्य मंडी: <strong>${data.market_location}</strong></p>
                </div>

                <div class="analysis-section">
                    <h4>सुझाव</h4>
                    <ul>
                        ${data.trend === 'up' ?
                            '<li>✅ बेचने का अच्छा समय है</li><li>⏰ कीमतें और बढ़ सकती हैं</li>' :
                            '<li>⏳ कुछ दिन इंतजार करें</li><li>💰 खरीदने का अच्छा समय हो सकता है</li>'
                        }
                    </ul>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.querySelector('.analysis-modal');
    if (modal) {
        modal.remove();
    }
}

// Price prediction functions
function predictPrice(crop, days = 7) {
    // Simple prediction based on current trend
    const marketItem = marketData.find(item => item.crop_name === crop);
    if (!marketItem) return null;

    const currentPrice = marketItem.current_price;
    const changeRate = marketItem.percentage_change / 100;

    // Simulate prediction with some randomness
    const predictions = [];
    let price = currentPrice;

    for (let i = 1; i <= days; i++) {
        // Add some randomness to the prediction
        const randomFactor = (Math.random() - 0.5) * 0.1; // ±5% random variation
        const dailyChange = (changeRate / 7) + randomFactor; // Assume weekly change spreads over 7 days
        price = price * (1 + dailyChange);

        predictions.push({
            day: i,
            price: Math.round(price),
            change: Math.round(((price - currentPrice) / currentPrice) * 100 * 100) / 100
        });
    }

    return predictions;
}

// Export functions
function exportMarketData(format = 'csv') {
    if (format === 'csv') {
        let csv = 'फसल,वर्तमान भाव,परिवर्तन,प्रतिशत परिवर्तन,मंडी\n';
        marketData.forEach(item => {
            csv += `${item.crop_name},${item.current_price},${item.price_change},${item.percentage_change},${item.market_location}\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `market_data_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
    }
}

// Comparison functions
function compareMarkets(crop) {
    // This would show price comparison across different markets
    const comparisons = [
        { market: 'दिल्ली मंडी', price: 2150, change: 2.4 },
        { market: 'मुंबई मंडी', price: 2180, change: 3.1 },
        { market: 'चेन्नई मंडी', price: 2120, change: 1.8 },
        { market: 'कोलकाता मंडी', price: 2160, change: 2.7 }
    ];

    showMarketComparison(crop, comparisons);
}

function showMarketComparison(crop, comparisons) {
    const modal = document.createElement('div');
    modal.className = 'comparison-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>🏪 ${crop} - मंडी तुलना</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="comparison-table">
                    <div class="comparison-header">
                        <div>मंडी</div>
                        <div>भाव</div>
                        <div>बदलाव</div>
                    </div>
                    ${comparisons.map(comp => `
                        <div class="comparison-row">
                            <div>${comp.market}</div>
                            <div>₹${comp.price}</div>
                            <div class="${comp.change > 0 ? 'positive' : 'negative'}">
                                ${comp.change > 0 ? '+' : ''}${comp.change}%
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="best-market">
                    <h4>सबसे अच्छा दाम: ${comparisons.reduce((best, current) =>
                        current.price > best.price ? current : best
                    ).market}</h4>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = 'flex';
}

// Weather integration
function getWeatherImpact() {
    // Mock weather impact data
    const weatherImpacts = [
        { crop: 'गेहूं', impact: 'positive', reason: 'अनुकूल तापमान' },
        { crop: 'टमाटर', impact: 'negative', reason: 'बारिश की संभावना' },
        { crop: 'मक्का', impact: 'neutral', reason: 'सामान्य मौसम' }
    ];

    return weatherImpacts;
}

// Initialize market dashboard
function initializeMarketDashboard() {
    // Load saved alerts
    loadAlerts();

    // Start periodic updates
    setInterval(updateMarketData, 30000); // Update every 30 seconds
    setInterval(checkAlerts, 60000); // Check alerts every minute

    // Initialize chart if on market page
    if (document.getElementById('chartCanvas')) {
        initializeChart();
    }

    console.log('Market dashboard initialized');
}

// Event listeners for market page
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/market') {
        initializeMarketDashboard();
    }
});

// Global functions for HTML onclick handlers
window.changeChartPeriod = function(period) {
    document.querySelectorAll('.chart-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    updateChart(period);
};

window.getDetailedAnalysis = function(crop) {
    const marketItem = marketData.find(item => item.crop_name === crop) || {
        crop_name: crop,
        current_price: 2150,
        price_change: 50,
        percentage_change: 2.4,
        market_location: 'नई दिल्ली मंडी',
        trend: 'up'
    };

    showDetailedAnalysis(marketItem);
};

window.setAlert = function() {
    const crop = document.getElementById('alertCrop').value;
    const price = document.getElementById('alertPrice').value;
    const type = document.getElementById('alertType').value;

    if (!price) {
        showNotification('कृपया टारगेट प्राइस डालें', 'warning');
        return;
    }

    const alert = { crop, price, type, timestamp: new Date() };
    saveAlert(alert);
    showNotification(`${crop} के लिए अलर्ट सेट हो गया`, 'success');

    // Clear form
    document.getElementById('alertPrice').value = '';
};

window.closeModal = closeModal;
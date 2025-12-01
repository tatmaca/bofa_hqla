// Dashboard JavaScript
let currentDate = document.getElementById('date-select').value;
let charts = {};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadDates();
    loadData(currentDate);
    
    document.getElementById('date-select').addEventListener('change', function() {
        currentDate = this.value;
        loadData(currentDate);
    });
    
    document.getElementById('refresh-btn').addEventListener('click', function() {
        loadData(currentDate);
    });
});

async function loadDates() {
    try {
        const response = await fetch('/api/dates');
        const data = await response.json();
        const select = document.getElementById('date-select');
        select.innerHTML = '';
        data.dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = date;
            if (date === currentDate) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading dates:', error);
    }
}

async function loadData(date) {
    try {
        // Load all data in parallel
        const [curveData, analysisData, statsData, newsData, predictionData, attributionData, xgboostData, linearPredData] = await Promise.all([
            fetch(`/api/curve/${date}`).then(r => r.json()),
            fetch(`/api/analysis/${date}`).then(r => r.json()).catch(() => null),
            fetch(`/api/stats/${date}`).then(r => r.json()),
            fetch(`/api/news/top/${date}?limit=5`).then(r => r.json()),
            fetch(`/api/prediction/${date}`).then(r => r.json()).catch(() => null),
            fetch(`/api/attribution/${date}`).then(r => r.json()).catch(() => null),
            fetch(`/api/xgboost/${date}`).then(r => r.json()).catch(() => null),
            fetch(`/api/linear-prediction/${date}`).then(r => r.json()).catch(() => null)
        ]);
        
        updateStats(statsData);
        updateCurveChart(curveData);
        updateDeltaChart(curveData);
        updateSpreadsChart(curveData);
        if (predictionData && !predictionData.error) {
            updatePredictionChart(predictionData);
        }
        updateNews(newsData.articles || []);
        updatePredictionSummary(analysisData);
        updateRisks(curveData.risks || []);
        
        // Update new modules
        if (attributionData && !attributionData.error) {
            updateFactorAttribution(attributionData);
        }
        if (xgboostData && !xgboostData.error) {
            updateXGBoostPredictions(xgboostData);
        }
        if (linearPredData && !linearPredData.error) {
            // Can be used for comparison if needed
        }
        
    } catch (error) {
        console.error('Error loading data:', error);
        document.querySelector('.container').innerHTML += 
            '<div class="error">Error loading data. Please try again.</div>';
    }
}

function updateStats(stats) {
    document.getElementById('stat-2y').textContent = stats.yields['2y'].toFixed(2) + '%';
    document.getElementById('stat-10y').textContent = stats.yields['10y'].toFixed(2) + '%';
    document.getElementById('stat-30y').textContent = stats.yields['30y'].toFixed(2) + '%';
    document.getElementById('stat-2s10s').textContent = stats.spreads['2s10s'].toFixed(2) + '%';
    
    const change2y = document.getElementById('change-2y');
    const change10y = document.getElementById('change-10y');
    const change30y = document.getElementById('change-30y');
    const change2s10s = document.getElementById('change-2s10s');
    
    updateChangeElement(change2y, stats.changes_bps['2y']);
    updateChangeElement(change10y, stats.changes_bps['10y']);
    updateChangeElement(change30y, stats.changes_bps['30y']);
    
    // Calculate spread change
    // This would need to be calculated from previous day's spread
    change2s10s.textContent = 'N/A';
    change2s10s.className = 'stat-change neutral';
}

function updateChangeElement(element, value) {
    const bps = value.toFixed(1);
    if (value > 0) {
        element.textContent = `+${bps} bps`;
        element.className = 'stat-change positive';
    } else if (value < 0) {
        element.textContent = `${bps} bps`;
        element.className = 'stat-change negative';
    } else {
        element.textContent = '0.0 bps';
        element.className = 'stat-change neutral';
    }
}

function updateCurveChart(data) {
    const ctx = document.getElementById('curve-chart').getContext('2d');
    
    const tenors = ['6m', '1y', '2y', '3y', '5y', '7y', '10y', '20y', '30y'];
    const today = data.today.zeros_pct;
    const prev = data.prev_day.zeros_pct;
    
    const todayValues = tenors.map(t => today[t] || null).filter(v => v !== null);
    const prevValues = tenors.map(t => prev[t] || null).filter(v => v !== null);
    const labels = tenors.filter(t => today[t] !== undefined);
    
    if (charts.curve) {
        charts.curve.destroy();
    }
    
    charts.curve = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: data.as_of,
                data: todayValues,
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7
            }, {
                label: data.prev,
                data: prevValues,
                borderColor: 'rgb(150, 150, 150)',
                backgroundColor: 'rgba(150, 150, 150, 0.1)',
                borderDash: [5, 5],
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Yield (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Tenor'
                    }
                }
            }
        }
    });
}

function updateDeltaChart(data) {
    const ctx = document.getElementById('delta-chart').getContext('2d');
    
    const tenors = ['6m', '1y', '2y', '3y', '5y', '7y', '10y', '20y', '30y'];
    const delta = data.delta.zeros_pct;
    
    const values = tenors.map(t => delta[t] ? delta[t] * 100 : null).filter(v => v !== null);
    const labels = tenors.filter(t => delta[t] !== undefined);
    const colors = values.map(v => v >= 0 ? 'rgba(231, 76, 60, 0.8)' : 'rgba(39, 174, 96, 0.8)');
    
    if (charts.delta) {
        charts.delta.destroy();
    }
    
    charts.delta = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Change (bps)',
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Change (basis points)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Tenor'
                    }
                }
            }
        }
    });
}

function updateSpreadsChart(data) {
    const ctx = document.getElementById('spreads-chart').getContext('2d');
    
    const spreads = data.today.spreads_pct;
    const labels = Object.keys(spreads);
    const values = Object.values(spreads);
    
    if (charts.spreads) {
        charts.spreads.destroy();
    }
    
    charts.spreads = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Spread (%)',
                data: values,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgb(102, 126, 234)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Spread (%)'
                    }
                }
            }
        }
    });
}

function updatePredictionChart(predictionData) {
    const ctx = document.getElementById('prediction-chart').getContext('2d');
    
    const tenors = ['2y', '5y', '10y', '30y'];
    const actual = tenors.map(t => predictionData[t]?.actual_bps || 0);
    const predicted = tenors.map(t => predictionData[t]?.predicted_bps || 0);
    
    if (charts.prediction) {
        charts.prediction.destroy();
    }
    
    charts.prediction = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: tenors,
            datasets: [{
                label: 'Actual (bps)',
                data: actual,
                backgroundColor: 'rgba(52, 152, 219, 0.8)',
                borderColor: 'rgb(52, 152, 219)',
                borderWidth: 1
            }, {
                label: 'Predicted (bps)',
                data: predicted,
                backgroundColor: 'rgba(231, 76, 60, 0.8)',
                borderColor: 'rgb(231, 76, 60)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Change (basis points)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Tenor'
                    }
                }
            }
        }
    });
}

function updateNews(articles) {
    const container = document.getElementById('news-list');
    
    if (articles.length === 0) {
        container.innerHTML = '<div class="loading">No news articles found for this date.</div>';
        return;
    }
    
    container.innerHTML = articles.map(article => `
        <div class="news-item">
            <h3>${escapeHtml(article.title || 'No title')}</h3>
            <div class="news-meta">
                <strong>${escapeHtml(article.source || 'Unknown')}</strong> | 
                ${article.bucket ? escapeHtml(article.bucket.replace('_', ' ')) : 'Uncategorized'} |
                ${article.bucket_confidence ? (article.bucket_confidence * 100).toFixed(0) + '% confidence' : ''}
            </div>
            ${article.summary ? `<div class="news-summary">${escapeHtml(article.summary.substring(0, 200))}${article.summary.length > 200 ? '...' : ''}</div>` : ''}
            ${article.url ? `<a href="${escapeHtml(article.url)}" target="_blank">Read more →</a>` : ''}
        </div>
    `).join('');
}

function updatePredictionSummary(analysis) {
    const container = document.getElementById('prediction-summary');
    
    if (!analysis || !analysis.analysis) {
        container.innerHTML = '<div class="loading">No prediction available for this date.</div>';
        return;
    }
    
    const summary = analysis.analysis.overall_summary || 'No summary available.';
    container.innerHTML = `<div class="prediction-summary">${escapeHtml(summary)}</div>`;
}

function updateRisks(risks) {
    const container = document.getElementById('risks-list');
    
    if (risks.length === 0) {
        container.innerHTML = '<div class="loading">No risk flags detected.</div>';
        return;
    }
    
    container.innerHTML = risks.map(risk => `
        <div class="risk-item ${risk.severity}">
            <div class="risk-flag">${escapeHtml(risk.flag)}</div>
            <div class="risk-why">${escapeHtml(risk.why)}</div>
        </div>
    `).join('');
}

function updateFactorAttribution(attributionData) {
    const container = document.getElementById('factor-attribution');
    
    if (!attributionData || !attributionData.attribution) {
        container.innerHTML = '<div class="loading">No attribution data available for this date.</div>';
        return;
    }
    
    const attribution = attributionData.attribution;
    const tenors = ['2Y', '5Y', '10Y', '30Y'];
    
    let html = '<div class="attribution-tenors">';
    
    for (const tenor of tenors) {
        const factors = attribution[tenor] || {};
        if (Object.keys(factors).length === 0) {
            continue;
        }
        
        html += `<div class="tenor-attribution">
            <h3>${tenor}</h3>
            <div class="factor-list">`;
        
        // Get top 5 factors
        const topFactors = Object.entries(factors).slice(0, 5);
        for (const [factor, contribution] of topFactors) {
            const isPositive = contribution >= 0;
            const colorClass = isPositive ? 'positive' : 'negative';
            const sign = contribution >= 0 ? '+' : '';
            
            html += `
                <div class="factor-item ${colorClass}">
                    <span class="factor-name">${escapeHtml(factor)}</span>
                    <span class="factor-contribution">${sign}${contribution.toFixed(1)} bps</span>
                </div>
            `;
        }
        
        html += `</div></div>`;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function updateXGBoostPredictions(xgboostData) {
    const container = document.getElementById('xgboost-predictions');
    
    if (!xgboostData || !xgboostData.predictions) {
        container.innerHTML = '<div class="loading">No XGBoost predictions available for this date.</div>';
        return;
    }
    
    const predictions = xgboostData.predictions;
    const spreads = xgboostData.spreads || {};
    const modelDate = xgboostData.model_date || 'unknown';
    
    let html = `<div class="xgboost-info">
        <p><strong>Model Date:</strong> ${escapeHtml(modelDate)}</p>
        <p><strong>Method:</strong> ${escapeHtml(xgboostData.enhancement_method || 'xgboost')}</p>
    </div>`;
    
    html += '<div class="xgboost-predictions">';
    html += '<h4>Tenor Predictions</h4>';
    
    const tenors = ['2y', '5y', '10y', '30y'];
    for (const tenor of tenors) {
        const pred = predictions[tenor];
        if (!pred) continue;
        
        const direction = pred.direction || 'flat';
        const magnitude = pred.magnitude_bps || 0;
        const directionClass = direction === 'up' ? 'positive' : (direction === 'down' ? 'negative' : 'neutral');
        const sign = magnitude >= 0 ? '+' : '';
        
        html += `
            <div class="prediction-item ${directionClass}">
                <span class="prediction-tenor">${tenor.toUpperCase()}</span>
                <span class="prediction-direction">${direction.toUpperCase()}</span>
                <span class="prediction-magnitude">${sign}${magnitude.toFixed(1)} bps</span>
            </div>
        `;
    }
    
    html += '</div>';
    
    if (Object.keys(spreads).length > 0) {
        html += '<div class="xgboost-spreads"><h4>Spread Predictions</h4>';
        for (const [spread, pred] of Object.entries(spreads)) {
            const direction = pred.direction || 'flat';
            const magnitude = pred.magnitude_bps || 0;
            const directionClass = direction === 'steepen' ? 'positive' : (direction === 'flatten' ? 'negative' : 'neutral');
            const sign = magnitude >= 0 ? '+' : '';
            
            html += `
                <div class="prediction-item ${directionClass}">
                    <span class="prediction-tenor">${escapeHtml(spread)}</span>
                    <span class="prediction-direction">${direction.toUpperCase()}</span>
                    <span class="prediction-magnitude">${sign}${magnitude.toFixed(1)} bps</span>
                </div>
            `;
        }
        html += '</div>';
    }
    
    container.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


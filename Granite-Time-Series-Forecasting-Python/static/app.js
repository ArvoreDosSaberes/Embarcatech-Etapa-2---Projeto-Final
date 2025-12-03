/**
 * 🎨 Frontend Application - Granite Time Series Forecasting
 * 
 * Este módulo implementa a interface web interativa para visualização
 * em tempo real de séries temporais, previsões e detecção de anomalias.
 * 
 * Funcionalidades:
 * - Conexão WebSocket com backend
 * - Gráfico dinâmico usando Chart.js
 * - Alertas visuais de anomalias
 * - Controles de start/stop/reset
 * - Estatísticas em tempo real
 */

// ========== Configuração Global ==========
const MAX_CHART_POINTS = 100;  // Máximo de pontos visíveis no gráfico
const ANIMATION_DURATION = 300;  // Duração de animações em ms

// ========== Estado da Aplicação ==========
const appState = {
    socket: null,
    chart: null,
    isRunning: false,
    dataPoints: [],
    forecastPoints: [],
    anomalyPoints: [],
    rollingMeanPoints: [],
    stats: {
        totalPoints: 0,
        anomalyCount: 0,
        totalPredictions: 0
    }
};

// ========== Utilidades ==========
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function ensureChartLabel(chart, label) {
    let index = chart.data.labels.indexOf(label);

    if (index === -1) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach(dataset => dataset.data.push(null));
        index = chart.data.labels.length - 1;
    }

    return index;
}

function clearFutureForecastData(chart, fromIndex) {
    const forecastDataset = chart.data.datasets[1];
    for (let i = fromIndex; i < forecastDataset.data.length; i += 1) {
        forecastDataset.data[i] = null;
    }
}

// ========== Inicialização ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 [Init] Initializing Granite Time Series Forecasting');
    
    initializeChart();
    initializeWebSocket();
    initializeEventListeners();
    loadSystemStatus();
});

/**
 * Inicializa o gráfico Chart.js
 * 
 * Cria um gráfico de linha com três datasets:
 * - Dados reais (azul)
 * - Previsões (roxo)
 * - Anomalias (vermelho)
 */
function initializeChart() {
    console.log('📊 [Chart] Initializing chart');
    
    const ctx = document.getElementById('timeSeriesChart').getContext('2d');
    
    appState.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Dados Reais',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Previsão',
                    data: [],
                    borderColor: 'rgb(168, 85, 247)',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 4
                },
                {
                    label: 'Anomalias',
                    data: [],
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgb(239, 68, 68)',
                    borderWidth: 0,
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    pointStyle: 'triangle',
                    showLine: false
                },
                {
                    label: 'Média (30s)',
                    data: [],
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.05)',
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    spanGaps: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: ANIMATION_DURATION
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Tempo',
                        color: 'rgb(156, 163, 175)'
                    },
                    ticks: {
                        color: 'rgb(156, 163, 175)',
                        maxTicksLimit: 10
                    },
                    grid: {
                        color: 'rgba(156, 163, 175, 0.1)'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Valor',
                        color: 'rgb(156, 163, 175)'
                    },
                    ticks: {
                        color: 'rgb(156, 163, 175)'
                    },
                    grid: {
                        color: 'rgba(156, 163, 175, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'rgb(156, 163, 175)',
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(17, 24, 39, 0.9)',
                    titleColor: 'rgb(255, 255, 255)',
                    bodyColor: 'rgb(209, 213, 219)',
                    borderColor: 'rgb(75, 85, 99)',
                    borderWidth: 1
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
    
    console.log('✅ [Chart] Chart initialized successfully');
}

/**
 * Inicializa conexão WebSocket com o servidor
 */
function initializeWebSocket() {
    console.log('🔌 [WebSocket] Connecting to server...');
    
    appState.socket = io();
    
    // Evento: Conexão estabelecida
    appState.socket.on('connect', () => {
        console.log('✅ [WebSocket] Connected to server');
        updateConnectionStatus(true);
    });
    
    // Evento: Desconexão
    appState.socket.on('disconnect', () => {
        console.log('❌ [WebSocket] Disconnected from server');
        updateConnectionStatus(false);
    });
    
    // Evento: Mensagem de conexão
    appState.socket.on('connected', (data) => {
        console.log('📨 [WebSocket] Server message:', data.message);
    });
    
    // Evento: Novos dados recebidos
    appState.socket.on('new_data', (data) => {
        handleNewData(data);
    });
    
    // Evento: Status mudou
    appState.socket.on('status_changed', (data) => {
        appState.isRunning = data.running;
        updateControlButtons();
    });
    
    // Evento: Dados resetados
    appState.socket.on('data_reset', () => {
        resetChartData();
    });
}

/**
 * Inicializa event listeners dos botões
 */
function initializeEventListeners() {
    document.getElementById('startBtn').addEventListener('click', startProcessing);
    document.getElementById('stopBtn').addEventListener('click', stopProcessing);
    document.getElementById('resetBtn').addEventListener('click', resetData);
    document.getElementById('closeAlert').addEventListener('click', dismissAlert);
}

/**
 * Carrega status inicial do sistema via API REST
 */
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        console.log('📊 [Status] System status loaded:', status);
        
        // Atualizar estatísticas
        appState.stats.totalPoints = status.data_points || 0;
        appState.stats.anomalyCount = status.anomaly_count || 0;
        appState.stats.totalPredictions = status.total_predictions || 0;
        updateStatistics();
        
    } catch (error) {
        console.error('❌ [Status] Error loading system status:', error);
    }
}

/**
 * Processa novos dados recebidos via WebSocket
 * 
 * @param {Object} data - Dados recebidos do servidor
 */
function handleNewData(data) {
    console.log('📦 [Data] Received:', data);

    const { point, forecast, anomaly, stats, rolling_mean: rollingMean } = data;
    let forecastToUse = forecast;
    
    // Atualizar dados reais
    if (point) {
        appState.dataPoints.push(point);
        if (forecast && Array.isArray(forecast.predictions)) {
            const limitedPredictions = forecast.predictions.slice(0, 10);
            forecastToUse = {
                ...forecast,
                predictions: limitedPredictions
            };
            appState.forecastPoints = limitedPredictions;
            console.log(`🔮 [Forecast] Received ${limitedPredictions.length} predictions (limited to 10)`);
            updateForecastPanel(forecastToUse);
        }

        if (rollingMean) {
            appState.rollingMeanPoints.push(rollingMean);
            if (appState.rollingMeanPoints.length > MAX_CHART_POINTS * 2) {
                appState.rollingMeanPoints = appState.rollingMeanPoints.slice(-MAX_CHART_POINTS);
            }
        }

        updateChart(point, forecastToUse, anomaly.is_anomaly, rollingMean);
    }
    
    // Atualizar previsões
    if (forecastToUse && forecastToUse.predictions && forecastToUse.predictions.length > 0) {
        appState.forecastPoints = forecastToUse.predictions;
        updateForecastPanel(forecastToUse);
    }
    
    // Processar anomalia
    if (anomaly && anomaly.is_anomaly) {
        console.log('⚠️  [Anomaly] Detected:', anomaly.info);
        showAnomalyAlert(anomaly.info);
        appState.anomalyPoints.push(point);
    }
    
    // Atualizar estatísticas
    if (stats) {
        console.log('📊 [Stats] Updating:', stats);
        appState.stats = {
            totalPoints: stats.total_points || 0,
            anomalyCount: stats.anomaly_count || 0,
            totalPredictions: stats.total_predictions || 0
        };
        updateStatistics();
    }
    
    // Limitar histórico em memória
    if (appState.dataPoints.length > MAX_CHART_POINTS * 2) {
        appState.dataPoints = appState.dataPoints.slice(-MAX_CHART_POINTS);
    }

    if (appState.rollingMeanPoints.length > MAX_CHART_POINTS * 2) {
        appState.rollingMeanPoints = appState.rollingMeanPoints.slice(-MAX_CHART_POINTS);
    }
}

/**
 * Atualiza o gráfico com novos dados
 * 
 * @param {Object} point - Novo ponto de dados
 * @param {Object} forecast - Dados de previsão
 * @param {boolean} isAnomaly - Se o ponto é uma anomalia
 */
function updateChart(point, forecast, isAnomaly, rollingMean) {
    const chart = appState.chart;
    const actualLabel = formatTimestamp(point.timestamp);
    const actualIndex = ensureChartLabel(chart, actualLabel);

    chart.data.datasets[0].data[actualIndex] = point.value;
    chart.data.datasets[2].data[actualIndex] = isAnomaly ? point.value : null;
    const rollingValue = rollingMean && typeof rollingMean.value === 'number'
        ? rollingMean.value
        : point.value;
    chart.data.datasets[3].data[actualIndex] = rollingValue;

    clearFutureForecastData(chart, actualIndex + 1);

    if (forecast && Array.isArray(forecast.predictions)) {
        forecast.predictions.slice(0, 10).forEach(prediction => {
            const forecastLabel = formatTimestamp(prediction.timestamp);
            const forecastIndex = ensureChartLabel(chart, forecastLabel);
            chart.data.datasets[1].data[forecastIndex] = prediction.value;
        });
    }

    while (chart.data.labels.length > MAX_CHART_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => dataset.data.shift());
    }

    chart.update('none');
}

function updateForecastPanel(forecast) {
    const tableBody = document.getElementById('forecastTableBody');
    const generatedAtLabel = document.getElementById('forecastGeneratedAt');

    if (!tableBody || !generatedAtLabel) {
        return;
    }

    if (!forecast || !Array.isArray(forecast.predictions) || forecast.predictions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td class="px-4 py-3 text-sm text-gray-500" colspan="3">Aguardando previsões...</td>
            </tr>
        `;
        generatedAtLabel.textContent = 'Aguardando previsões...';
        return;
    }

    generatedAtLabel.textContent = `Gerado em ${formatTimestamp(forecast.forecast_timestamp || new Date().toISOString())}`;

    tableBody.innerHTML = forecast.predictions.slice(0, 10).map(prediction => `
        <tr>
            <td class="px-4 py-3 text-sm text-gray-700">${prediction.horizon_step || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700">${formatTimestamp(prediction.timestamp)}</td>
            <td class="px-4 py-3 text-sm text-gray-700 font-semibold">${prediction.value.toFixed(2)}</td>
        </tr>
    `).join('');
}

// Funções de display removidas - elementos não existem no HTML

/**
 * Mostra alerta de anomalia
 * 
 * @param {Object} info - Informações da anomalia
 */
function showAnomalyAlert(info) {
    const alertPanel = document.getElementById('alertsPanel');
    const alertContent = document.getElementById('alertContent');
    
    if (alertPanel && alertContent) {
        alertContent.innerHTML = `
            <p class="text-sm font-semibold">
                Valor ${info.value.toFixed(2)} detectado (${info.deviation.toFixed(2)}σ de desvio)
            </p>
            <p class="text-sm mt-1">
                Média: ${info.mean.toFixed(2)} | Desvio Padrão: ${info.stdev.toFixed(2)}
            </p>
            <p class="text-sm mt-1">
                Severidade: ${info.severity_emoji || '⚠️'} ${(info.severity || 'medium').toUpperCase()}
            </p>
        `;
        
        alertPanel.classList.remove('hidden');
        
        // Auto-fechar após 5 segundos
        setTimeout(() => {
            alertPanel.classList.add('hidden');
        }, 5000);
    }
    
}

/**
 * Dispensa alerta de anomalia
 */
function dismissAlert() {
    const alertPanel = document.getElementById('alertsPanel');
    if (alertPanel) {
        alertPanel.classList.add('hidden');
    }
}

/**
 * Atualiza estatísticas na interface
 */
function updateStatistics() {
    // Atualizar contadores
    document.getElementById('totalPoints').textContent = appState.stats.totalPoints || appState.stats.total_points || 0;
    document.getElementById('predictionCount').textContent = appState.stats.totalPredictions || appState.stats.total_predictions || 0;
    document.getElementById('anomalyCount').textContent = appState.stats.anomalyCount || appState.stats.anomaly_count || 0;
    
    // Atualizar status do sistema
    const statusElement = document.getElementById('systemStatus');
    if (appState.isRunning) {
        statusElement.textContent = 'Em Execução';
        statusElement.classList.remove('text-gray-600');
        statusElement.classList.add('text-green-600');
    } else {
        statusElement.textContent = 'Parado';
        statusElement.classList.remove('text-green-600');
        statusElement.classList.add('text-gray-600');
    }
}

/**
 * Atualiza status de conexão
 * 
 * @param {boolean} connected - Se está conectado
 */
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connectionStatus');
    
    if (connected) {
        statusElement.innerHTML = `
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <span class="text-sm">Conectado</span>
        `;
    } else {
        statusElement.innerHTML = `
            <div class="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
            <span class="text-sm">Desconectado</span>
        `;
    }
}

/**
 * Atualiza estado dos botões de controle
 */
function updateControlButtons() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    if (appState.isRunning) {
        startBtn.disabled = true;
        startBtn.classList.add('opacity-50', 'cursor-not-allowed');
        stopBtn.disabled = false;
        stopBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    } else {
        startBtn.disabled = false;
        startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        stopBtn.disabled = true;
        stopBtn.classList.add('opacity-50', 'cursor-not-allowed');
    }
}

/**
 * Inicia processamento em tempo real
 */
function startProcessing() {
    console.log('▶️  [Control] Starting processing');
    appState.socket.emit('start_processing');
    appState.isRunning = true;
    updateControlButtons();
    updateStatistics();
}

/**
 * Para processamento em tempo real
 */
function stopProcessing() {
    console.log('⏸️  [Control] Stopping processing');
    appState.socket.emit('stop_processing');
    appState.isRunning = false;
    updateControlButtons();
    updateStatistics();
}

/**
 * Reseta todos os dados
 */
function resetData() {
    console.log('🔄 [Control] Resetting data');
    appState.socket.emit('reset_data');
    resetChartData();
}

/**
 * Limpa dados do gráfico
 */
function resetChartData() {
    appState.dataPoints = [];
    appState.forecastPoints = [];
    appState.anomalyPoints = [];
    appState.rollingMeanPoints = [];
    appState.stats = {
        totalPoints: 0,
        anomalyCount: 0,
        totalPredictions: 0
    };
    
    const chart = appState.chart;
    chart.data.labels = [];
    chart.data.datasets.forEach(dataset => {
        dataset.data = [];
    });
    chart.update();
    
    updateStatistics();
    dismissAlert();
    
    console.log('✅ [Control] Data reset complete');
}

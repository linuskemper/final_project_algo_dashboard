/* global Chart */

// -- Chart Global Defaults for Premium Look --
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.05)';
Chart.defaults.scale.grid.borderColor = 'rgba(255, 255, 255, 0.1)';

const priceCtx = document.getElementById("priceChart").getContext("2d");
const sentimentCtx = document.getElementById("sentimentChart").getContext("2d");
const performanceCtx = document.getElementById("performanceChart").getContext("2d");

let priceChart;
let sentimentChart;
let performanceChart;

// Streaming state
let streamingInterval = null;
let fullData = null;
let currentIndex = 0;
const STREAM_SPEED = 50; // milliseconds between data points
const INITIAL_DATA_POINTS = 50; // Start with some historical data visible
const SIGNAL_DISPLAY_DURATION = 2000; // Keep Buy/Sell signal displayed for 2 seconds

// Signal display lock state
let lockedSignal = null; // { signal: 'Buy'|'Sell', explanation: string }
let signalLockExpiry = 0; // timestamp when lock expires

function buildQueryParams() {
  const form = document.getElementById("settings-form");
  const params = new URLSearchParams(new FormData(form));
  return params.toString();
}

async function fetchAllData() {
  const query = buildQueryParams();
  try {
    const [tsRes, sentRes, perfRes] = await Promise.all([
      fetch(`/api/time_series?${query}`),
      fetch(`/api/sentiment?${query}`),
      fetch(`/api/performance?${query}`),
    ]);

    if (!tsRes.ok) throw new Error(`Time Series API error: ${tsRes.statusText}`);
    if (!sentRes.ok) throw new Error(`Sentiment API error: ${sentRes.statusText}`);
    if (!perfRes.ok) throw new Error(`Performance API error: ${perfRes.statusText}`);

    const timeSeries = await tsRes.json();
    const sentiment = await sentRes.json();
    const performance = await perfRes.json();

    if (timeSeries.error) throw new Error(timeSeries.error);
    if (sentiment.error) throw new Error(sentiment.error);
    if (performance.error) throw new Error(performance.error);

    return { timeSeries, sentiment, performance };
  } catch (err) {
    console.error("Failed to fetch data:", err);
    return { error: err.message };
  }
}

function showErrorMessage(msg) {
  const signalEl = document.getElementById("latest-signal");
  const explanationEl = document.getElementById("latest-explanation");
  if (signalEl) {
    signalEl.textContent = "ERROR";
    signalEl.style.webkitTextFillColor = '#ef4444';
  }
  if (explanationEl) {
    explanationEl.textContent = msg;
    explanationEl.style.color = '#ef4444';
  }
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}

// Update live price ticker
function updateLiveTicker(price, change, changePercent) {
  const priceEl = document.getElementById("live-price");
  const changeEl = document.getElementById("live-change");

  if (priceEl) {
    priceEl.textContent = formatCurrency(price);
    priceEl.classList.add('price-flash');
    setTimeout(() => priceEl.classList.remove('price-flash'), 200);
  }

  if (changeEl && change !== null) {
    const sign = change >= 0 ? '+' : '';
    changeEl.textContent = `${sign}${formatCurrency(change)} (${sign}${changePercent.toFixed(2)}%)`;
    changeEl.className = `live-change ${change >= 0 ? 'positive' : 'negative'}`;
  }
}

// Update timestamp
function updateTimestamp(dateStr) {
  const timestampEl = document.getElementById("last-update");
  if (timestampEl) {
    timestampEl.textContent = `Last: ${dateStr}`;
  }
}

function updateKpis(performance, index, timeSeries) {
  if (!performance) return;

  const strategyRetEl = document.getElementById("kpi-strategy-return");
  const benchmarkRetEl = document.getElementById("kpi-benchmark-return");
  const maxDdEl = document.getElementById("kpi-max-dd");
  const sharpeEl = document.getElementById("kpi-sharpe");
  const hitRateEl = document.getElementById("kpi-hit-rate");
  const signalEl = document.getElementById("latest-signal");
  const explanationEl = document.getElementById("latest-explanation");

  // Calculate progressive metrics based on visible data
  const visibleEquity = performance.strategy_equity.slice(0, index + 1);
  const visibleBenchmark = performance.benchmark_equity.slice(0, index + 1);

  const currentReturn = visibleEquity.length > 0 ? visibleEquity[visibleEquity.length - 1] - 1 : 0;
  const benchmarkReturn = visibleBenchmark.length > 0 ? visibleBenchmark[visibleBenchmark.length - 1] - 1 : 0;

  // Calculate progressive max drawdown
  const maxDrawdown = calculateMaxDrawdown(visibleEquity);

  // Calculate progressive Sharpe ratio (annualized)
  const sharpeRatio = calculateSharpeRatio(visibleEquity);

  // Calculate progressive win rate based on visible buy/sell signals
  const winRate = calculateWinRate(timeSeries, index);

  // Determine current signal based on most recent buy/sell
  const { signal: currentSignal, explanation } = getCurrentSignal(timeSeries, index);

  // Animate KPI updates
  if (strategyRetEl) {
    strategyRetEl.textContent = formatPercent(currentReturn);
    strategyRetEl.classList.add('kpi-update');
    setTimeout(() => strategyRetEl.classList.remove('kpi-update'), 300);
  }
  if (benchmarkRetEl) benchmarkRetEl.textContent = `vs Benchmark: ${formatPercent(benchmarkReturn)}`;

  // Update all metrics progressively
  if (maxDdEl) maxDdEl.textContent = formatPercent(maxDrawdown);
  if (sharpeEl) sharpeEl.textContent = sharpeRatio.toFixed(2);
  if (hitRateEl) hitRateEl.textContent = formatPercent(winRate);

  if (signalEl) {
    signalEl.textContent = currentSignal.toUpperCase();
    signalEl.style.backgroundImage = 'none';
    if (currentSignal === 'Buy') {
      signalEl.style.webkitTextFillColor = '#10b981';
    } else if (currentSignal === 'Sell') {
      signalEl.style.webkitTextFillColor = '#ef4444';
    } else {
      signalEl.style.webkitTextFillColor = '#94a3b8';
    }
  }
  if (explanationEl) explanationEl.textContent = explanation;
}

// Calculate max drawdown from equity curve
function calculateMaxDrawdown(equity) {
  if (equity.length < 2) return 0;

  let maxPeak = equity[0];
  let maxDrawdown = 0;

  for (let i = 1; i < equity.length; i++) {
    if (equity[i] > maxPeak) {
      maxPeak = equity[i];
    }
    const drawdown = (maxPeak - equity[i]) / maxPeak;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }

  return maxDrawdown;
}

// Calculate annualized Sharpe ratio from equity curve
function calculateSharpeRatio(equity) {
  if (equity.length < 10) return 0;

  // Calculate daily returns
  const returns = [];
  for (let i = 1; i < equity.length; i++) {
    returns.push((equity[i] - equity[i - 1]) / equity[i - 1]);
  }

  if (returns.length === 0) return 0;

  const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
  const stdDev = Math.sqrt(variance);

  if (stdDev === 0) return 0;

  // Annualize (assuming 252 trading days)
  return (avgReturn / stdDev) * Math.sqrt(252);
}

// Calculate win rate based on completed trades up to current index
function calculateWinRate(timeSeries, index) {
  if (!timeSeries) return 0;

  const visibleBuys = timeSeries.buy_indices.filter(i => i <= index);
  const visibleSells = timeSeries.sell_indices.filter(i => i <= index);

  let wins = 0;
  let totalTrades = 0;

  // Match buy-sell pairs
  for (let i = 0; i < Math.min(visibleBuys.length, visibleSells.length); i++) {
    const buyIdx = visibleBuys[i];
    const sellIdx = visibleSells[i];

    if (sellIdx > buyIdx) {
      totalTrades++;
      if (timeSeries.close[sellIdx] > timeSeries.close[buyIdx]) {
        wins++;
      }
    }
  }

  return totalTrades > 0 ? wins / totalTrades : 0;
}

// Get current signal based on most recent buy/sell at streaming position
function getCurrentSignal(timeSeries, index) {
  if (!timeSeries) return { signal: 'Hold', explanation: 'Awaiting data...' };

  const visibleBuys = timeSeries.buy_indices.filter(i => i <= index);
  const visibleSells = timeSeries.sell_indices.filter(i => i <= index);

  const lastBuyIdx = visibleBuys.length > 0 ? visibleBuys[visibleBuys.length - 1] : -1;
  const lastSellIdx = visibleSells.length > 0 ? visibleSells[visibleSells.length - 1] : -1;

  const now = Date.now();

  // Check if a new signal just occurred at current index
  if (timeSeries.buy_indices.includes(index)) {
    // New BUY signal - lock it for 2 seconds
    lockedSignal = { signal: 'Buy', explanation: '🚀 BUY signal triggered! Market conditions favorable.' };
    signalLockExpiry = now + SIGNAL_DISPLAY_DURATION;
    return lockedSignal;
  }
  if (timeSeries.sell_indices.includes(index)) {
    // New SELL signal - lock it for 2 seconds
    lockedSignal = { signal: 'Sell', explanation: '📉 SELL signal triggered! Taking profits.' };
    signalLockExpiry = now + SIGNAL_DISPLAY_DURATION;
    return lockedSignal;
  }

  // If we have a locked signal that hasn't expired, keep displaying it
  if (lockedSignal && now < signalLockExpiry) {
    return lockedSignal;
  }

  // Lock expired, clear it
  lockedSignal = null;

  // Otherwise show current position
  if (lastBuyIdx > lastSellIdx) {
    return { signal: 'Hold', explanation: `In position since ${timeSeries.dates[lastBuyIdx]}` };
  } else if (lastSellIdx > lastBuyIdx) {
    return { signal: 'Hold', explanation: `Out of market since ${timeSeries.dates[lastSellIdx]}` };
  }

  return { signal: 'Hold', explanation: 'Waiting for entry signal...' };
}

function createGradient(ctx, colorStart, colorEnd) {
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, colorStart);
  gradient.addColorStop(1, colorEnd);
  return gradient;
}

// Slice data up to the current streaming index
function sliceTimeSeries(ts, endIndex) {
  const sliced = {
    dates: ts.dates.slice(0, endIndex + 1),
    close: ts.close.slice(0, endIndex + 1),
    bb_upper: ts.bb_upper.slice(0, endIndex + 1),
    bb_middle: ts.bb_middle.slice(0, endIndex + 1),
    bb_lower: ts.bb_lower.slice(0, endIndex + 1),
    sma_short: ts.sma_short.slice(0, endIndex + 1),
    sma_long: ts.sma_long.slice(0, endIndex + 1),
    buy_indices: ts.buy_indices.filter(i => i <= endIndex),
    sell_indices: ts.sell_indices.filter(i => i <= endIndex)
  };
  return sliced;
}

function sliceSentiment(sent, endIndex) {
  return {
    dates: sent.dates.slice(0, endIndex + 1),
    fg_value: sent.fg_value.slice(0, endIndex + 1)
  };
}

function slicePerformance(perf, endIndex) {
  return {
    dates: perf.dates.slice(0, endIndex + 1),
    strategy_equity: perf.strategy_equity.slice(0, endIndex + 1),
    benchmark_equity: perf.benchmark_equity.slice(0, endIndex + 1),
    metrics: perf.metrics,
    latest_signal: perf.latest_signal,
    latest_explanation: perf.latest_explanation
  };
}

function buildPriceChart(ts, animate = true) {
  const datasets = [
    {
      label: "Upper BB",
      data: ts.bb_upper,
      borderColor: "rgba(0, 255, 255, 0.0)",
      backgroundColor: "rgba(0, 255, 255, 0.1)",
      pointRadius: 0,
      borderWidth: 0,
      fill: "+2",
      tension: 0.1
    },
    {
      label: "Middle BB",
      data: ts.bb_middle,
      borderColor: "rgba(0, 255, 255, 0.3)",
      pointRadius: 0,
      borderWidth: 1,
      borderDash: [2, 2],
      tension: 0.1
    },
    {
      label: "Lower BB",
      data: ts.bb_lower,
      borderColor: "rgba(0, 255, 255, 0.0)",
      pointRadius: 0,
      borderWidth: 0,
      tension: 0.1
    },
    {
      label: "Price",
      data: ts.close,
      borderColor: "#3b82f6",
      borderWidth: 2,
      pointRadius: 0,
      hoverRadius: 6,
      tension: 0.1
    },
    {
      label: "SMA 5",
      data: ts.sma_short,
      borderColor: "#f59e0b",
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.1
    },
    {
      label: "SMA 50",
      data: ts.sma_long,
      borderColor: "#a855f7",
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.1
    }
  ];

  // Add Buy/Sell Markers
  const buyPoints = [];
  const sellPoints = [];

  ts.dates.forEach((date, i) => {
    if (ts.buy_indices.includes(i)) {
      buyPoints.push({ x: date, y: ts.close[i] });
    }
    if (ts.sell_indices.includes(i)) {
      sellPoints.push({ x: date, y: ts.close[i] });
    }
  });

  if (buyPoints.length > 0) {
    datasets.push({
      label: "Buy Signal",
      data: buyPoints,
      type: 'scatter',
      backgroundColor: '#10b981',
      pointRadius: 6,
      pointHoverRadius: 8
    });
  }

  if (sellPoints.length > 0) {
    datasets.push({
      label: "Sell Signal",
      data: sellPoints,
      type: 'scatter',
      backgroundColor: '#ef4444',
      pointRadius: 6,
      pointHoverRadius: 8
    });
  }

  if (priceChart) priceChart.destroy();

  priceChart = new Chart(priceCtx, {
    type: "line",
    data: {
      labels: ts.dates,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: animate ? { duration: 0 } : false, // Disable animation for streaming updates
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: function (context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null) {
                label += formatCurrency(context.parsed.y);
              }
              return label;
            }
          }
        }
      },
      scales: {
        x: { display: false },
        y: {
          position: 'right',
          grid: { display: true },
          ticks: {
            callback: function (value) {
              return '$' + value;
            }
          }
        },
      },
    },
  });
}

function buildSentimentChart(sent, animate = true) {
  if (sentimentChart) sentimentChart.destroy();

  const ctx = sentimentCtx;
  const gradientFill = ctx.createLinearGradient(0, 0, 0, 300);
  gradientFill.addColorStop(0, 'rgba(239, 68, 68, 0.2)');
  gradientFill.addColorStop(1, 'rgba(16, 185, 129, 0.2)');

  sentimentChart = new Chart(sentimentCtx, {
    type: "line",
    data: {
      labels: sent.dates,
      datasets: [
        {
          label: "Fear & Greed",
          data: sent.fg_value,
          borderColor: "#f472b6",
          borderWidth: 2,
          pointRadius: 0,
          fill: true,
          backgroundColor: gradientFill,
          tension: 0.3
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: animate ? { duration: 0 } : false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { display: false },
        y: {
          min: 0,
          max: 100,
          position: 'right',
          ticks: { stepSize: 20 }
        },
      },
    },
  });
}

function buildPerformanceChart(perf, animate = true) {
  if (performanceChart) performanceChart.destroy();

  performanceChart = new Chart(performanceCtx, {
    type: "line",
    data: {
      labels: perf.dates,
      datasets: [
        {
          label: "Strategy",
          data: perf.strategy_equity,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          fill: true,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2
        },
        {
          label: "Benchmark",
          data: perf.benchmark_equity,
          borderColor: "#94a3b8",
          borderWidth: 2,
          borderDash: [4, 4],
          pointRadius: 0,
          tension: 0.2
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: animate ? { duration: 0 } : false,
      plugins: {
        legend: {
          display: true,
          labels: { usePointStyle: true }
        }
      },
      scales: {
        x: { display: false },
        y: {
          position: 'right',
          ticks: {
            callback: (val) => (val * 100).toFixed(0) + '%'
          }
        },
      },
    },
  });
}

// Check if a new signal occurred at current index
function checkForNewSignal(ts, index) {
  if (ts.buy_indices.includes(index)) {
    flashSignal('BUY');
  } else if (ts.sell_indices.includes(index)) {
    flashSignal('SELL');
  }
}

function flashSignal(type) {
  const signalCard = document.querySelector('.signal-card');
  const body = document.body;

  // Add signal flash to signal card (2 seconds)
  if (signalCard) {
    signalCard.classList.add('signal-flash');
    signalCard.classList.add(type === 'BUY' ? 'signal-buy' : 'signal-sell');
    setTimeout(() => {
      signalCard.classList.remove('signal-flash', 'signal-buy', 'signal-sell');
    }, 2000);
  }

  // Add full-screen border glow (2 seconds)
  if (body) {
    body.classList.add('screen-flash');
    body.classList.add(type === 'BUY' ? 'flash-buy' : 'flash-sell');
    setTimeout(() => {
      body.classList.remove('screen-flash', 'flash-buy', 'flash-sell');
    }, 2000);
  }
}

// Stream the next data point
function streamNextPoint() {
  if (!fullData || currentIndex >= fullData.timeSeries.dates.length - 1) {
    // Streaming complete, show final state
    if (streamingInterval) {
      clearInterval(streamingInterval);
      streamingInterval = null;
    }
    setStreamingStatus(false);
    return;
  }

  currentIndex++;

  const ts = sliceTimeSeries(fullData.timeSeries, currentIndex);
  const sent = sliceSentiment(fullData.sentiment, Math.min(currentIndex, fullData.sentiment.dates.length - 1));
  const perf = slicePerformance(fullData.performance, currentIndex);

  // Update charts without animation for smooth streaming
  buildPriceChart(ts, false);
  buildSentimentChart(sent, false);
  buildPerformanceChart(perf, false);

  // Update live ticker
  const currentPrice = fullData.timeSeries.close[currentIndex];
  const previousPrice = fullData.timeSeries.close[currentIndex - 1] || currentPrice;
  const priceChange = currentPrice - previousPrice;
  const priceChangePercent = (priceChange / previousPrice) * 100;

  updateLiveTicker(currentPrice, priceChange, priceChangePercent);
  updateTimestamp(fullData.timeSeries.dates[currentIndex]);
  updateKpis(perf, currentIndex, fullData.timeSeries);

  // Check for signals
  checkForNewSignal(fullData.timeSeries, currentIndex);
}

function setStreamingStatus(isStreaming) {
  const statusEl = document.getElementById("stream-status");
  const indicator = document.querySelector('.live-indicator');

  if (statusEl) {
    statusEl.textContent = isStreaming ? 'LIVE' : 'PAUSED';
    statusEl.className = `stream-status ${isStreaming ? 'live' : 'paused'}`;
  }

  if (indicator) {
    indicator.classList.toggle('active', isStreaming);
  }
}

function startStreaming() {
  if (streamingInterval) {
    clearInterval(streamingInterval);
  }

  setStreamingStatus(true);
  streamingInterval = setInterval(streamNextPoint, STREAM_SPEED);
}

function pauseStreaming() {
  if (streamingInterval) {
    clearInterval(streamingInterval);
    streamingInterval = null;
  }
  setStreamingStatus(false);
}

function resetStreaming() {
  pauseStreaming();
  currentIndex = INITIAL_DATA_POINTS - 1;

  if (fullData) {
    const ts = sliceTimeSeries(fullData.timeSeries, currentIndex);
    const sent = sliceSentiment(fullData.sentiment, currentIndex);
    const perf = slicePerformance(fullData.performance, currentIndex);

    buildPriceChart(ts, true);
    buildSentimentChart(sent, true);
    buildPerformanceChart(perf, true);

    const currentPrice = fullData.timeSeries.close[currentIndex];
    updateLiveTicker(currentPrice, null, 0);
    updateTimestamp(fullData.timeSeries.dates[currentIndex]);
  }
}

async function refreshDashboard() {
  pauseStreaming();

  const data = await fetchAllData();
  if (data && data.error) {
    showErrorMessage(data.error);
    return;
  }

  if (data) {
    fullData = data;
    currentIndex = INITIAL_DATA_POINTS - 1;

    // Build initial charts with some historical data
    const ts = sliceTimeSeries(data.timeSeries, currentIndex);
    const sent = sliceSentiment(data.sentiment, currentIndex);
    const perf = slicePerformance(data.performance, currentIndex);

    buildPriceChart(ts, true);
    buildSentimentChart(sent, true);
    buildPerformanceChart(perf, true);

    // Initialize ticker
    const currentPrice = data.timeSeries.close[currentIndex];
    updateLiveTicker(currentPrice, null, 0);
    updateTimestamp(data.timeSeries.dates[currentIndex]);
    updateKpis(perf, currentIndex, data.timeSeries);

    // Auto-start streaming
    startStreaming();
  }
}

// Event listeners
document.getElementById("settings-form").addEventListener("submit", (evt) => {
  evt.preventDefault();
  refreshDashboard();
});

// Streaming controls
document.addEventListener('click', (e) => {
  if (e.target.id === 'btn-play') {
    startStreaming();
  } else if (e.target.id === 'btn-pause') {
    pauseStreaming();
  } else if (e.target.id === 'btn-reset') {
    resetStreaming();
  }
});

window.addEventListener("load", () => {
  refreshDashboard();
});

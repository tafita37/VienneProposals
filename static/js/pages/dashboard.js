// Scripts spécifiques: dashboard

document.addEventListener('DOMContentLoaded', () => {
	const INITIAL_DASHBOARD_API_URL = '/com/api/loadInitialDataDashboard/';
	const STAT_BY_COMMERCIAL_API_URL = '/com/api/statByCommercial/';
	const PROFIT_BY_MONTH_API_URL = '/com/api/profitByMonth/';
	let proposalStats = [];
	let profitStats = [];
	let loadedYear = String(new Date().getFullYear());

	const commercialYearInput = document.getElementById('dashboardYearInput');
	const profitYearInput = document.getElementById('profitYearInput');
	const commercialMeta = document.getElementById('commercialMeta');
	const commercialStatsGrid = document.getElementById('commercialStatsGrid');
	const profitMeta = document.getElementById('profitMeta');
	const profitChart = document.getElementById('profitChart');
	const profitChartCanvas = document.getElementById('profitChartCanvas');
	const yearlyProfitEl = document.getElementById('yearlyProfit');
	const bestMonthEl = document.getElementById('bestMonth');
	let profitChartInstance = null;

	if (
		!commercialYearInput ||
		!profitYearInput ||
		!commercialMeta ||
		!commercialStatsGrid ||
		!profitMeta ||
		!profitChart ||
		!profitChartCanvas ||
		!yearlyProfitEl ||
		!bestMonthEl
	) {
		return;
	}
	loadInitialDashboardData();

	commercialYearInput.addEventListener('change', handleCommercialYearInput);
	commercialYearInput.addEventListener('blur', handleCommercialYearInput);
	profitYearInput.addEventListener('change', handleProfitYearInput);
	profitYearInput.addEventListener('blur', handleProfitYearInput);

	async function loadInitialDashboardData() {
		try {
			const response = await fetch(INITIAL_DASHBOARD_API_URL, {
				method: 'GET',
				headers: {
					'X-Requested-With': 'XMLHttpRequest'
				}
			});

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}`);
			}

			const payload = await response.json();

			if (!Array.isArray(payload?.statByCommercial) || !Array.isArray(payload?.profitByMonth)) {
				return;
			}

			const apiYear = String(payload?.year || '');
			const normalizedStats = payload.statByCommercial.map((item) => ({
				name: item?.name || '-',
				proposals: Number(item?.proposals) || 0
			}));
			const normalizedProfit = payload.profitByMonth.map((item) => ({
				month: item?.month || '-',
				value: Number(item?.value) || 0
			}));

			const targetYear = apiYear || loadedYear;
			loadedYear = targetYear;
			proposalStats = normalizedStats;
			profitStats = normalizedProfit;
			commercialYearInput.value = targetYear;
			profitYearInput.value = targetYear;
			renderCommercialStats(proposalStats);
			renderMonthlyProfit(profitStats);
		} catch (error) {
			console.error('Impossible de charger les stats dashboard:', error);
		}
	}

	async function handleCommercialYearInput(event) {
		const requestedYear = String(event.target.value || '');
		const isLoaded = await loadCommercialStatsByYear(requestedYear);
		if (!isLoaded) {
			event.target.value = loadedYear;
			renderCommercialStats(proposalStats);
		}
	}

	async function handleProfitYearInput(event) {
		const requestedYear = String(event.target.value || '');
		const isLoaded = await loadProfitByMonthByYear(requestedYear);
		if (!isLoaded) {
			event.target.value = loadedYear;
			renderMonthlyProfit(profitStats);
		}
	}

	async function loadCommercialStatsByYear(year) {
		if (!/^\d{4}$/.test(year)) {
			return false;
		}

		try {
			const response = await fetch(`${STAT_BY_COMMERCIAL_API_URL}?year=${encodeURIComponent(year)}`, {
				method: 'GET',
				headers: {
					'X-Requested-With': 'XMLHttpRequest'
				}
			});

			if (!response.ok) {
				return false;
			}

			const payload = await response.json();
			if (!Array.isArray(payload?.statByCommercial)) {
				return false;
			}

			const apiYear = String(payload?.year || year);
			proposalStats = payload.statByCommercial.map((item) => ({
				name: item?.name || '-',
				proposals: Number(item?.proposals) || 0
			}));

			loadedYear = apiYear;
			commercialYearInput.value = apiYear;
			renderCommercialStats(proposalStats);
			return true;
		} catch (error) {
			console.error('Erreur chargement statByCommercial:', error);
			return false;
		}
	}

	async function loadProfitByMonthByYear(year) {
		if (!/^\d{4}$/.test(year)) {
			return false;
		}

		try {
			const response = await fetch(`${PROFIT_BY_MONTH_API_URL}?year=${encodeURIComponent(year)}`, {
				method: 'GET',
				headers: {
					'X-Requested-With': 'XMLHttpRequest'
				}
			});

			if (!response.ok) {
				return false;
			}

			const payload = await response.json();
			if (!Array.isArray(payload?.profitByMonth)) {
				return false;
			}

			const apiYear = String(payload?.year || year);
			profitStats = payload.profitByMonth.map((item) => ({
				month: item?.month || '-',
				value: Number(item?.value) || 0
			}));

			loadedYear = apiYear;
			profitYearInput.value = apiYear;
			renderMonthlyProfit(profitStats);
			return true;
		} catch (error) {
			console.error('Erreur chargement profitByMonth:', error);
			return false;
		}
	}

	function renderCommercialStats(commercialData) {
		commercialStatsGrid.innerHTML = '';

		commercialData.forEach((item) => {
			const card = document.createElement('div');
			card.className = 'commercial-stat-card';
			card.innerHTML = `
				<div class="commercial-name">${item.name}</div>
				<div class="commercial-value">${item.proposals}</div>
				<div class="commercial-label">propositions</div>
			`;
			commercialStatsGrid.appendChild(card);
		});
	}

	function renderMonthlyProfit(monthlyProfitData) {
		if (!Array.isArray(monthlyProfitData) || monthlyProfitData.length === 0) {
			yearlyProfitEl.textContent = formatCurrency(0);
			bestMonthEl.textContent = '-';
			renderProfitChart([], []);
			return;
		}

		const labels = monthlyProfitData.map((item) => item.month || '-');
		const values = monthlyProfitData.map((item) => Number(item.value) || 0);
		renderProfitChart(labels, values);

		const totalProfit = monthlyProfitData.reduce((acc, item) => acc + item.value, 0);
		yearlyProfitEl.textContent = formatCurrency(totalProfit);

		const bestMonth = monthlyProfitData.reduce((max, item) => {
			if (item.value > max.value) {
				return item;
			}
			return max;
		}, monthlyProfitData[0]);

		bestMonthEl.textContent = `${bestMonth.month} (${formatCurrencyCompact(bestMonth.value)})`;
	}

	function renderProfitChart(labels, values) {
		if (typeof Chart === 'undefined') {
			return;
		}

		if (profitChartInstance) {
			profitChartInstance.data.labels = labels;
			profitChartInstance.data.datasets[0].data = values;
			profitChartInstance.update();
			return;
		}

		profitChartInstance = new Chart(profitChartCanvas, {
			type: 'bar',
			data: {
				labels,
				datasets: [
					{
						label: 'Benefice mensuel (Ar)',
						data: values,
						backgroundColor: 'rgba(13, 115, 119, 0.65)',
						borderColor: 'rgba(13, 115, 119, 1)',
						borderWidth: 1,
						borderRadius: 6,
						maxBarThickness: 34
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						display: false
					},
					tooltip: {
						callbacks: {
							label(context) {
								return ` ${formatCurrency(context.raw || 0)}`;
							}
						}
					}
				},
				scales: {
					y: {
						beginAtZero: true,
						ticks: {
							callback(value) {
								return formatCurrencyCompact(Number(value) || 0);
							}
						}
					}
				}
			}
		});
	}
});

function formatCurrency(amount) {
	return `${new Intl.NumberFormat('fr-FR').format(amount)} €`;
}

function formatCurrencyCompact(amount) {
    if (amount >= 1_000_000) {
        return `${(amount / 1_000_000).toFixed(2).replace('.', ',')} M`;
    }
    if (amount >= 1_000) {
        return `${Math.round(amount / 1_000)} k`;
    }
    // Pour les montants < 1000, afficher la valeur réelle
    return amount.toString().replace('.', ',');
}
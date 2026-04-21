document.addEventListener('DOMContentLoaded', () => {
    const INITIAL_API_URL = '/com/api/loadInitialUserDashboardData/';
    const PROFIT_BY_MONTH_API_URL = '/com/api/userProfitByMonth/';

    const createdCountEl = document.getElementById('createdCount');
    const validatedCountEl = document.getElementById('validatedCount');
    const pendingCountEl = document.getElementById('pendingCount');
    const yearInput = document.getElementById('userProfitYearInput');
    const profitMeta = document.getElementById('userProfitMeta');
    const yearlyProfitEl = document.getElementById('userYearlyProfit');
    const bestMonthEl = document.getElementById('userBestMonth');
    const chartCanvas = document.getElementById('userProfitChartCanvas');

    let loadedYear = String(new Date().getFullYear());
    let profitStats = [];
    let chartInstance = null;

    if (
        !createdCountEl ||
        !validatedCountEl ||
        !pendingCountEl ||
        !yearInput ||
        !profitMeta ||
        !yearlyProfitEl ||
        !bestMonthEl ||
        !chartCanvas
    ) {
        return;
    }

    yearInput.addEventListener('change', handleYearInput);
    yearInput.addEventListener('blur', handleYearInput);

    loadInitialData();

    async function loadInitialData() {
        try {
            const response = await fetch(INITIAL_API_URL, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const payload = await response.json();
            const counts = payload?.counts || {};
            const year = String(payload?.year || loadedYear);
            const monthly = Array.isArray(payload?.profitByMonth) ? payload.profitByMonth : [];

            createdCountEl.textContent = Number(counts.created) || 0;
            validatedCountEl.textContent = Number(counts.validated) || 0;
            pendingCountEl.textContent = Number(counts.pending) || 0;

            loadedYear = year;
            yearInput.value = year;
            profitStats = monthly.map((item) => ({
                month: item?.month || '-',
                value: Number(item?.value) || 0,
            }));

            renderProfitSection();
        } catch (error) {
            console.error('Erreur de chargement dashboard utilisateur:', error);
        }
    }

    async function handleYearInput(event) {
        const requestedYear = String(event.target.value || '');
        const loaded = await loadProfitByMonthByYear(requestedYear);
        if (!loaded) {
            event.target.value = loadedYear;
            renderProfitSection();
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
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                return false;
            }

            const payload = await response.json();
            if (!Array.isArray(payload?.profitByMonth)) {
                return false;
            }

            loadedYear = String(payload?.year || year);
            yearInput.value = loadedYear;
            profitStats = payload.profitByMonth.map((item) => ({
                month: item?.month || '-',
                value: Number(item?.value) || 0,
            }));
            renderProfitSection();
            return true;
        } catch (error) {
            console.error('Erreur chargement marge mensuelle utilisateur:', error);
            return false;
        }
    }

    function renderProfitSection() {
        profitMeta.textContent = `Annee ${loadedYear}`;

        if (!Array.isArray(profitStats) || profitStats.length === 0) {
            yearlyProfitEl.textContent = formatCurrency(0);
            bestMonthEl.textContent = '-';
            renderProfitChart([], []);
            return;
        }

        const labels = profitStats.map((item) => item.month || '-');
        const values = profitStats.map((item) => Number(item.value) || 0);

        const total = values.reduce((sum, value) => sum + value, 0);
        yearlyProfitEl.textContent = formatCurrency(total);

        const best = profitStats.reduce((max, item) => {
            if (item.value > max.value) {
                return item;
            }
            return max;
        }, profitStats[0]);

        bestMonthEl.textContent = `${best.month} (${formatCurrencyCompact(best.value)})`;
        renderProfitChart(labels, values);
    }

    function renderProfitChart(labels, values) {
        if (typeof Chart === 'undefined') {
            return;
        }

        if (chartInstance) {
            chartInstance.data.labels = labels;
            chartInstance.data.datasets[0].data = values;
            chartInstance.update();
            return;
        }

        chartInstance = new Chart(chartCanvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Marge brute mensuelle (Ar)',
                        data: values,
                        backgroundColor: 'rgba(13, 115, 119, 0.65)',
                        borderColor: 'rgba(13, 115, 119, 1)',
                        borderWidth: 1,
                        borderRadius: 6,
                        maxBarThickness: 34,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                return ` ${formatCurrency(context.raw || 0)}`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback(value) {
                                return formatCurrencyCompact(Number(value) || 0);
                            },
                        },
                    },
                },
            },
        });
    }
});

function formatCurrency(amount) {
    return `${new Intl.NumberFormat('fr-FR').format(amount)} Ar`;
}

function formatCurrencyCompact(amount) {
    if (amount >= 1000000) {
        return `${(amount / 1000000).toFixed(2).replace('.', ',')} M`;
    }
    if (amount >= 1000) {
        return `${Math.round(amount / 1000)} k`;
    }
    return amount.toString().replace('.', ',');
}

/**
 * CodeLens — Gestion des graphiques Chart.js
 * Rendu du diagramme des langages et de l'activité des commits.
 */

// Palette de couleurs harmonieuse pour les langages et graphiques
const CHART_COLORS = [
    "#3b82f6", // Bleu
    "#f59e0b", // Ambre
    "#10b981", // Émeraude
    "#8b5cf6", // Violet
    "#ec4899", // Rose
    "#06b6d4", // Cyan
    "#f97316", // Orange
    "#64748b"  // Ardoise
];

/**
 * Initialise le graphique en anneau (Doughnut) de répartition des langages.
 * @param {string} canvasId - L'ID de l'élément canvas HTML
 * @param {Array} languages - Liste des langages analysés [{name, percentage, count, size_bytes}, ...]
 */
function initLanguagesChart(canvasId, languages) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !languages || languages.length === 0) return;

    const ctx = canvas.getContext("2d");
    const labels = languages.map(l => l.name);
    const data = languages.map(l => l.percentage);
    const backgroundColors = languages.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]);

    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: "#ffffff",
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        boxWidth: 14,
                        padding: 12,
                        font: {
                            family: "'Inter', sans-serif",
                            size: 12,
                            weight: "500"
                        },
                        generateLabels: (chart) => {
                            const original = Chart.overrides.doughnut.plugins.legend.labels.generateLabels(chart);
                            return original.map((item, idx) => {
                                const lang = languages[idx];
                                item.text = `${lang.name} (${lang.percentage}%)`;
                                return item;
                            });
                        }
                    }
                },
                tooltip: {
                    backgroundColor: "#0f172a",
                    titleFont: { family: "'Inter', sans-serif", size: 13, weight: "700" },
                    bodyFont: { family: "'Inter', sans-serif", size: 12 },
                    padding: 10,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const lang = languages[index];
                            return ` ${lang.percentage}% (${lang.count} fichier(s))`;
                        }
                    }
                }
            },
            cutout: "68%"
        }
    });
}

/**
 * Initialise le graphique en barres de l'activité temporelle des commits.
 * @param {string} canvasId - L'ID de l'élément canvas HTML
 * @param {Object} monthlyActivity - Objet contenant {labels: [...], data: [...]}
 */
function initCommitsChart(canvasId, monthlyActivity) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !monthlyActivity || !monthlyActivity.labels || monthlyActivity.labels.length === 0) return;

    const ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: monthlyActivity.labels,
            datasets: [{
                label: "Nombre de commits",
                data: monthlyActivity.data,
                backgroundColor: "rgba(79, 70, 229, 0.8)",
                hoverBackgroundColor: "#4338ca",
                borderRadius: 6,
                borderSkipped: false,
                barThickness: 24
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: "#0f172a",
                    titleFont: { family: "'Inter', sans-serif", size: 12 },
                    bodyFont: { family: "'Inter', sans-serif", size: 12, weight: "600" },
                    padding: 10,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y} commit(s)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        },
                        color: "#64748b"
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: "#f1f5f9"
                    },
                    ticks: {
                        stepSize: 1,
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        },
                        color: "#64748b"
                    }
                }
            }
        }
    });
}

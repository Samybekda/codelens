/**
 * CodeLens — Script JavaScript Principal (Vanilla JS)
 * Projet Universitaire L3 MIAGE / MIASHS - Toulouse III
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Fermeture automatique des alertes flash après 7 secondes
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";
            setTimeout(() => alert.remove(), 400);
        }, 7000);
    });

    // 2. Gestion de l'état de chargement lors de la soumission du formulaire
    const searchForm = document.getElementById("analyzeForm");
    if (searchForm) {
        searchForm.addEventListener("submit", () => {
            const submitBtn = document.getElementById("submitBtn");
            const loadingIndicator = document.getElementById("loadingIndicator");
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add("loading");
            }
            if (loadingIndicator) {
                loadingIndicator.style.display = "flex";
            }
        });
    }
});

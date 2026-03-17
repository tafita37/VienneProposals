document.addEventListener('DOMContentLoaded', () => {
    renderSummary();
    renderProposalTable();
});

window.addEventListener('storage', () => {
    renderSummary();
    renderProposalTable();
});

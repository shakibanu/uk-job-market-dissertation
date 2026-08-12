// Animates the stat card numbers counting up from 0 when they appear.
// I'm using a MutationObserver instead of just running once on page load,
// because Dash builds the Overview tab content dynamically - it doesn't
// exist in the page yet when this script first runs.

function animateStatValue(el) {
    const original = el.textContent.trim();
    // pulling out just the digits so I can animate a plain number, then
    // adding back whatever prefix/suffix was there (£, commas, etc.)
    const digitsOnly = original.replace(/[^0-9.]/g, "");
    const target = parseFloat(digitsOnly);
    if (isNaN(target)) return;

    const prefix = original.match(/^[^\d]*/)[0];
    const suffix = original.match(/[^\d]*$/)[0];
    const duration = 800; // matches the acceptance criteria, no animation over 800ms
    const startTime = performance.now();

    function frame(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const currentValue = Math.round(target * progress);
        el.textContent = prefix + currentValue.toLocaleString() + suffix;
        if (progress < 1) {
            requestAnimationFrame(frame);
        } else {
            el.textContent = original; // make sure it lands on the exact original text
        }
    }
    requestAnimationFrame(frame);
}

const statValueObserver = new MutationObserver(function (mutations) {
    document.querySelectorAll(".stat-value:not([data-animated])").forEach(function (el) {
        el.setAttribute("data-animated", "true");
        animateStatValue(el);
    });
});

statValueObserver.observe(document.body, { childList: true, subtree: true });

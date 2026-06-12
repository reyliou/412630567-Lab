async function loadFooter() {
    try {
        const response = await fetch('/assets-library/footer.html');
        const html = await response.text();
        const placeholder = document.getElementById('footer-placeholder');
        if (placeholder) {
            placeholder.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading footer:', error);
    }
}

// 頁面載入後執行
window.addEventListener('DOMContentLoaded', loadFooter);

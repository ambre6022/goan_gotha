document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from meta tag
    const token = document.querySelector('meta[name="csrf-token"]')?.content;

    if (token) {
        // Add CSRF token to all AJAX requests
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (!options.headers) {
                options.headers = {};
            }
            options.headers['X-CSRF-Token'] = token;
            return originalFetch.call(this, url, options);
        };

        // Add CSRF token to all forms
        document.querySelectorAll('form').forEach(form => {
            if (!form.querySelector('input[name="csrf_token"]')) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrf_token';
                input.value = token;
                form.appendChild(input);
            }
        });
    }
});
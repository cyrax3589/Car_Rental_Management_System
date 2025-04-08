document.addEventListener('DOMContentLoaded', function() {
    const adminLoginForm = document.getElementById('adminLoginForm');

    adminLoginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(adminLoginForm);
        
        try {
            const response = await fetch('/admin/login', {
                method: 'POST',
                body: formData
            });

            if (response.redirected) {
                window.location.href = response.url;
            } else {
                const data = await response.json();
                if (!response.ok) {
                    const errorDiv = document.querySelector('.error-message');
                    errorDiv.textContent = data.error || 'Login failed';
                    errorDiv.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Login error:', error);
            const errorDiv = document.querySelector('.error-message');
            errorDiv.textContent = 'An error occurred. Please try again.';
            errorDiv.style.display = 'block';
        }
    });
});
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const rememberMe = document.getElementById('remember');

    // Load remembered email if exists
    if (localStorage.getItem('rememberedEmail')) {
        emailInput.value = localStorage.getItem('rememberedEmail');
        rememberMe.checked = true;
    }

    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function showError(input, message) {
        const formGroup = input.parentElement;
        const errorDisplay = formGroup.querySelector('.error-message');
        formGroup.classList.add('error');
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
        formGroup.classList.add('shake');
        setTimeout(() => formGroup.classList.remove('shake'), 500);
    }

    function clearError(input) {
        const formGroup = input.parentElement;
        const errorDisplay = formGroup.querySelector('.error-message');
        formGroup.classList.remove('error');
        errorDisplay.style.display = 'none';
    }

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        let isValid = true;

        clearError(emailInput);
        clearError(passwordInput);

        if (!validateEmail(emailInput.value)) {
            showError(emailInput, 'Please enter a valid email address');
            isValid = false;
        }

        if (passwordInput.value.length < 6) {
            showError(passwordInput, 'Password must be at least 6 characters');
            isValid = false;
        }

        if (!isValid) return;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: emailInput.value,
                    password: passwordInput.value
                })
            });

            const data = await response.json();

            if (response.ok) {
                if (rememberMe.checked) {
                    localStorage.setItem('rememberedEmail', emailInput.value);
                } else {
                    localStorage.removeItem('rememberedEmail');
                }
                window.location.href = '/';
            } else {
                showError(emailInput, data.error || 'Login failed');
            }
        } catch (error) {
            showError(emailInput, 'An error occurred. Please try again.');
        }
    });

    // Clear errors on input
    [emailInput, passwordInput].forEach(input => {
        input.addEventListener('input', () => clearError(input));
    });
});
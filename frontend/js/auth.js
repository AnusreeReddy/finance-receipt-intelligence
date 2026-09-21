document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const alertBox = document.getElementById('alert-box');

    function showAlert(message, type = 'error') {
        if (!alertBox) return;
        alertBox.textContent = message;
        alertBox.className = `alert alert-${type}`;
        alertBox.style.display = 'block';
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;

            try {
                const data = await api.request('/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({ email, password })
                });

                localStorage.setItem('token', data.token);
                window.location.href = 'dashboard.html';
            } catch (err) {
                showAlert(err.message, 'error');
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;

            if (password !== confirmPassword) {
                showAlert('Passwords do not match', 'error');
                return;
            }

            try {
                await api.request('/auth/register', {
                    method: 'POST',
                    body: JSON.stringify({ email, password })
                });

                showAlert('Registration successful! Redirecting to login...', 'success');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 1500);
            } catch (err) {
                showAlert(err.message, 'error');
            }
        });
    }
});

async function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    try {
        await api.request('/auth/me', { method: 'GET' });
    } catch (err) {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    }
}

function logout() {
    const token = localStorage.getItem('token');
    if (token) {
        api.request('/auth/logout', { method: 'POST' }).finally(() => {
            localStorage.removeItem('token');
            window.location.href = 'login.html';
        });
    } else {
        window.location.href = 'login.html';
    }
}
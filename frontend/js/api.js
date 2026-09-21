const API_BASE_URL = 'http://localhost:5000/api';

const api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
            const data = await response.json();

            if (!response.ok) {
                if (response.status === 401 && endpoint !== '/auth/login') {
                    localStorage.removeItem('token');
                    window.location.href = 'login.html';
                }
                throw new Error(data.error || 'API Request failed');
            }

            return data;
        } catch (error) {
            throw error;
        }
    }
};
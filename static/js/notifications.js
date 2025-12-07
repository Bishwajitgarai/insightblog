// WebSocket client for real-time notifications

class NotificationService {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.listeners = [];
    }

    connect() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.log('No token found, skipping WebSocket connection');
            return;
        }

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/notifications?token=${token}`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.showToast('Connected to real-time notifications', 'success');
            };

            this.ws.onmessage = (event) => {
                try {
                    const notification = JSON.parse(event.data);
                    this.handleNotification(notification);
                } catch (error) {
                    console.error('Error parsing notification:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        }
    }

    handleNotification(notification) {
        // Show toast notification
        this.showToast(notification.content || 'New notification', 'info');

        // Update notification badge
        this.updateNotificationBadge();

        // Notify all listeners
        this.listeners.forEach(callback => callback(notification));
    }

    addListener(callback) {
        this.listeners.push(callback);
    }

    removeListener(callback) {
        this.listeners = this.listeners.filter(cb => cb !== callback);
    }

    updateNotificationBadge() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            const currentCount = parseInt(badge.textContent) || 0;
            badge.textContent = currentCount + 1;
            badge.classList.remove('hidden');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-fade-in`;
        toast.innerHTML = `
            <div class="flex items-center gap-md">
                <span class="text-lg">${this.getIcon(type)}</span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: '💬'
        };
        return icons[type] || icons.info;
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Global notification service instance
const notificationService = new NotificationService();

// Auto-connect when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (authService.isAuthenticated()) {
        notificationService.connect();
    }
});

/**
 * Notification utility for the application
 * Provides methods for showing loading indicators, success/error notifications
 */
const AppNotification = {
    /**
     * Show a notification message
     * @param {string} message - The message to display
     * @param {string} type - The type of notification (success, error, info)
     * @param {number} duration - Duration in ms to show the notification
     */
    show: function(message, type = 'info', duration = 3000) {
        // Remove any existing notifications
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => {
            document.body.removeChild(toast);
        });

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerText = message;
        
        // Add toast to body
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Hide and remove toast after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, duration);
    },

    /**
     * Show a loading indicator
     * @param {string} message - Optional message to display with the loading indicator
     */
    showLoading: function(message = 'Loading...') {
        // Remove any existing loading indicators
        this.hideLoading();
        
        // Create loading overlay
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        overlay.style.display = 'flex';
        overlay.style.justifyContent = 'center';
        overlay.style.alignItems = 'center';
        overlay.style.zIndex = '9999';
        
        // Create loading spinner and message
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = `
            <div style="text-align: center; color: white;">
                <div style="border: 5px solid #f3f3f3; border-top: 5px solid #d08000; border-radius: 50%; width: 50px; height: 50px; margin: 0 auto; animation: spin 1s linear infinite;"></div>
                <p style="margin-top: 15px;">${message}</p>
            </div>
        `;
        
        // Add animation style
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        // Add to DOM
        overlay.appendChild(spinner);
        document.body.appendChild(overlay);
    },

    /**
     * Hide the loading indicator
     */
    hideLoading: function() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            document.body.removeChild(overlay);
        }
    },

    /**
     * Show an error notification with a retry button
     * @param {string} message - The error message
     * @param {Function} retryCallback - Function to call when retry is clicked
     */
    showErrorWithRetry: function(message, retryCallback) {
        // Remove any existing notifications
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => {
            document.body.removeChild(toast);
        });

        // Create error notification with retry button
        const toast = document.createElement('div');
        toast.className = 'toast error';
        toast.style.width = 'auto';
        toast.style.maxWidth = '400px';
        toast.style.display = 'flex';
        toast.style.flexDirection = 'column';
        toast.style.padding = '15px';
        
        const messageElement = document.createElement('div');
        messageElement.innerText = message;
        messageElement.style.marginBottom = '10px';
        
        const retryButton = document.createElement('button');
        retryButton.innerText = 'Thử lại';
        retryButton.style.alignSelf = 'flex-end';
        retryButton.style.padding = '5px 10px';
        retryButton.style.backgroundColor = 'white';
        retryButton.style.color = '#F44336';
        retryButton.style.border = 'none';
        retryButton.style.borderRadius = '3px';
        retryButton.style.cursor = 'pointer';
        
        retryButton.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
                if (typeof retryCallback === 'function') {
                    retryCallback();
                }
            }, 300);
        });
        
        toast.appendChild(messageElement);
        toast.appendChild(retryButton);
        
        // Add toast to body
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
    }
};

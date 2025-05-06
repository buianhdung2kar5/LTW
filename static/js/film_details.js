document.addEventListener('DOMContentLoaded', function() {
    const favoriteBtn = document.getElementById('favorite-btn');
    const heartIcon = document.getElementById('heart-icon');
    const favoriteText = document.getElementById('favorite-text');
    
    function showToast(message, type = 'success') {
        if (typeof AppNotification !== 'undefined') {
            AppNotification.show(message, type);
            return;
        }
        
        const container = document.querySelector('.notification-container');
        if (!container) {
            const newContainer = document.createElement('div');
            newContainer.className = 'notification-container';
            document.body.appendChild(newContainer);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = document.createElement('span');
        icon.className = 'toast-icon';
        icon.innerHTML = type === 'success' ? '✓' : '⚠';
        
        const text = document.createElement('span');
        text.className = 'toast-message';
        text.textContent = message;
        
        toast.appendChild(icon);
        toast.appendChild(text);
        
        const toastContainer = document.querySelector('.notification-container');
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                toastContainer.removeChild(toast);
            }, 500);
        }, 3000);
    }
    
    if (favoriteBtn) {
        const filmId = favoriteBtn.getAttribute('data-film-id');
        
        fetch(`/user/favorites/check/${filmId}`)
            .then(response => response.json())
            .then(data => {
                if (data.isFavorite) {
                    favoriteBtn.classList.add('favorited');
                    heartIcon.style.color = '#fff';
                    favoriteText.textContent = 'ĐÃ YÊU THÍCH';
                }
            })
            .catch(error => console.error('Error checking favorite status:', error));
        
        favoriteBtn.addEventListener('click', function() {            
            fetch(`/user/favorites/toggle/${filmId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.action === 'added') {
                    favoriteBtn.classList.add('favorited');
                    heartIcon.style.color = '#fff';
                    favoriteText.textContent = 'ĐÃ YÊU THÍCH';
                    showToast('Đã thêm vào danh sách yêu thích');
                } else if (data.action === 'removed') {
                    favoriteBtn.classList.remove('favorited');
                    heartIcon.style.color = '';
                    favoriteText.textContent = 'THÊM VÀO YÊU THÍCH';
                    showToast('Đã xóa khỏi danh sách yêu thích');
                } else {
                    showToast('Có lỗi xảy ra', 'error');
                }
            })
            .catch(error => {
                console.error('Error toggling favorite:', error);
                showToast('Có lỗi xảy ra khi cập nhật', 'error');
            });
        });
    }
});
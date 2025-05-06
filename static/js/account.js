document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements
    const logoutBtn = document.getElementById('logout-btn');
    const changePasswordBtn = document.getElementById('change-password-btn');
    const changePasswordModal = document.getElementById('change-password-modal');
    const changePasswordForm = document.getElementById('change-password-form');
    const changePasswordError = document.getElementById('change-password-error');
    const emailDisplay = document.getElementById('email');
    
    // Load user profile data (kept for potential AJAX updates)
    async function loadUserProfile() {
        try {
            const response = await fetch('/user/profile/data');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            
            // Update UI with fresh data
            if (data.email && emailDisplay) {
                emailDisplay.textContent = data.email;
            }
            
            if (data.fullName && document.getElementById('fullname')) {
                document.getElementById('fullname').textContent = data.fullName;
            }
            
            if (data.registerDate) {
                const joinDate = new Date(data.registerDate);
                const formattedDate = joinDate.toLocaleDateString('vi-VN');
                if (document.getElementById('join-date')) {
                    document.getElementById('join-date').textContent = formattedDate;
                }
            }
        } catch (error) {
            console.error('Error loading profile data:', error);
            // Silent fail - we already have server-rendered data
        }
    }
    
    // Initialize - load profile data
    loadUserProfile();
    
    // Modal functions
    function openModal(modal) {
        if (modal) modal.style.display = 'flex';
    }
    
    function closeModal(modal) {
        if (modal) modal.style.display = 'none';
    }
    
    // Change password modal
    changePasswordBtn?.addEventListener('click', () => openModal(changePasswordModal));
    
    // Close buttons
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === changePasswordModal) closeModal(changePasswordModal);
    });
    
    // Change password
    changePasswordForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        changePasswordError.style.display = 'none';
        
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (newPassword !== confirmPassword) {
            changePasswordError.textContent = 'Mật khẩu mới không khớp!';
            changePasswordError.style.display = 'block';
            return;
        }
        
        try {
            if (typeof AppNotification !== 'undefined') {
                AppNotification.showLoading('Đang cập nhật mật khẩu...');
            }
            
            const response = await fetch('/user/password/change', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ currentPassword, newPassword })
            });
            
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            
            const data = await response.json();
            
            if (response.ok) {
                showToast('success', data.message || 'Đổi mật khẩu thành công!');
                closeModal(changePasswordModal);
                changePasswordForm.reset();
            } else {
                changePasswordError.textContent = data.message || 'Có lỗi xảy ra khi đổi mật khẩu';
                changePasswordError.style.display = 'block';
            }
        } catch (error) {
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            changePasswordError.textContent = 'Lỗi kết nối! Vui lòng thử lại sau.';
            changePasswordError.style.display = 'block';
        }
    });
    
    // Logout functionality
    logoutBtn?.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
            if (typeof AppNotification !== 'undefined') {
                AppNotification.showLoading('Đang đăng xuất...');
            }
            
            await fetch('/auth/logout', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            
            window.location.href = '/';
        } catch (error) {
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            console.error('Logout error:', error);
            showToast('error', 'Đăng xuất thất bại! Vui lòng thử lại.');
        }
    });
    
    // Show toast notification
    function showToast(type, message) {
        // Use AppNotification if available, otherwise use a simple alert
        if (typeof AppNotification !== 'undefined') {
            AppNotification.show(message, type);
        } else if (window.parent && typeof window.parent.showToast === 'function') {
            window.parent.showToast(type, message);
        } else {
            alert(message);
        }
    }
});
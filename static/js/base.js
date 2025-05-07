// Khởi tạo khi DOM load xong
document.addEventListener("DOMContentLoaded", function() {
    // Lấy các phần tử
    const loginBtn = document.querySelector('.login-btn');
    const registerBtn = document.querySelector('.register-btn');
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    const closeButtons = document.querySelectorAll('.close');
    const showRegister = document.getElementById('show-register');
    const showLogin = document.getElementById('show-login');
    const authButtons = document.getElementById('auth-buttons');
    const userInfo = document.getElementById('user-info');
    const logoutBtn = document.getElementById('logout-btn');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');
    const menuToggle = document.querySelector('.menu-toggle');
    const menuClose = document.querySelector('.menu-close');
    const navLinks = document.querySelector('.nav-links');

    // Chuyển đổi menu trên thiết bị di động
    menuToggle?.addEventListener('click', () => {
        navLinks.classList.add('active');
    });

    menuClose?.addEventListener('click', () => {
        navLinks.classList.remove('active');
    });

    // Kiểm tra trạng thái đăng nhập khi tải trang
    checkLoginStatus();

    // Mở modal đăng nhập
    loginBtn?.addEventListener('click', () => {
        loginModal.style.display = 'flex';
        registerModal.style.display = 'none';
    });

    // Mở modal đăng ký
    registerBtn?.addEventListener('click', () => {
        registerModal.style.display = 'flex';
        loginModal.style.display = 'none';
    });

    // Chuyển sang modal đăng ký
    showRegister?.addEventListener('click', (e) => {
        e.preventDefault();
        loginModal.style.display = 'none';
        registerModal.style.display = 'flex';
    });

    // Chuyển sang modal đăng nhập
    showLogin?.addEventListener('click', (e) => {
        e.preventDefault();
        registerModal.style.display = 'none';
        loginModal.style.display = 'flex';
    });

    // Đóng modal
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            loginModal.style.display = 'none';
            registerModal.style.display = 'none';
        });
    });

    // Xử lý đăng nhập
    loginForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.style.display = 'none';
        
        try {
            const formData = new FormData(loginForm);
            const response = await fetch('/auth/login', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();

            if (data.success) {
                loginModal.style.display = 'none';
                updateUIAfterLogin(data.username);
                showToast("success", data.message || "Đăng nhập thành công!");
                
                // Gọi convertLoginToFavoriteBtn nếu đang ở trang chi tiết phim
                if (typeof window.convertLoginToFavoriteBtn === 'function') {
                    window.convertLoginToFavoriteBtn();
                }
                
                // Thêm class logged-in vào body
                document.body.classList.add('logged-in');
            } else {
                showError(loginError, data.message || "Đăng nhập thất bại!");
            }
        } catch (error) {
            showError(loginError, "Lỗi kết nối! Vui lòng thử lại sau.");
            console.error('Login error:', error);
        }
    });

    // Xử lý đăng ký
    registerForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        registerError.style.display = 'none';
        
        try {
            const formData = new FormData(registerForm);
            const response = await fetch('/auth/register', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();

            if (data.success) {
                registerModal.style.display = 'none';
                updateUIAfterLogin(data.username);
                showToast("success", data.message || "Đăng ký và đăng nhập thành công!");
            } else {
                showError(registerError, data.message || "Đăng ký thất bại!");
            }
        } catch (error) {
            showError(registerError, "Lỗi kết nối! Vui lòng thử lại sau.");
            console.error('Register error:', error);
        }
    });

    // Xử lý đăng xuất
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                // Hiển thị chỉ báo tải nếu có
                if (typeof AppNotification !== 'undefined') {
                    AppNotification.showLoading('Đang đăng xuất...');
                }
                
                // Gọi endpoint đăng xuất
                const response = await fetch('/auth/logout', {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                // Ẩn chỉ báo tải nếu có
                if (typeof AppNotification !== 'undefined') {
                    AppNotification.hideLoading();
                }
                
                // Cập nhật UI - ẩn thông tin người dùng, hiển thị nút xác thực
                if (authButtons) authButtons.style.display = 'flex';
                if (userInfo) userInfo.style.display = 'none';
                
                // Nếu đang ở trang chi tiết phim, chuyển nút yêu thích thành nút đăng nhập
                if (typeof window.convertFavoriteToLoginBtn === 'function') {
                    window.convertFavoriteToLoginBtn();
                }
                
                // Hiển thị thông báo thành công
                if (typeof showToast === 'function') {
                    showToast('success', 'Đăng xuất thành công!');
                }
                
                // Chuyển hướng nếu cần dựa trên trang hiện tại
                if (window.location.pathname.includes('/account') || 
                    window.location.pathname.includes('/favorites')) {
                    window.location.href = '/';
                }
            } catch (error) {
                // Ẩn chỉ báo tải nếu có
                if (typeof AppNotification !== 'undefined') {
                    AppNotification.hideLoading();
                }
                console.error('Logout error:', error);
                if (typeof showToast === 'function') {
                    showToast('error', 'Đăng xuất thất bại! Vui lòng thử lại.');
                }
            }
        });
    }
});

// Hàm kiểm tra trạng thái đăng nhập
async function checkLoginStatus() {
    try {
        const response = await fetch('/auth/user-info');
        const data = await response.json();
        
        if (data.isLoggedIn) {
            updateUIAfterLogin(data.username);
        }
    } catch (error) {
        console.error('Error checking login status:', error);
    }
}

// Hàm cập nhật UI sau khi đăng nhập
function updateUIAfterLogin(username) {
    const authButtons = document.getElementById('auth-buttons');
    const userInfo = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');
    
    if (authButtons && userInfo && usernameDisplay) {
        authButtons.style.display = 'none';
        userInfo.style.display = 'flex';
        usernameDisplay.textContent = username;
    }
}

// Hàm hiển thị lỗi
function showError(element, message) {
    element.textContent = message;
    element.style.display = 'block';
}

// Hàm hiển thị thông báo thành công
function showToast(type, message) {
    if (typeof AppNotification !== 'undefined') {
        AppNotification.show(message, type);
    } else {
        // Fallback simple alert or console.log if AppNotification is not available
        alert(message);
    }
}

// Hàm hiển thị hộp thông báo
function showMessageBox() {
    document.getElementById('message-box-overlay').style.display = 'flex';
}

// Hàm ẩn hộp thông báo
function hideMessageBox() {
    document.getElementById('message-box-overlay').style.display = 'none';
}
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

    // Mobile menu toggle
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
    logoutBtn?.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
            await fetch('/auth/logout');
            authButtons.style.display = 'flex';
            userInfo.style.display = 'none';
            showToast("success", "Đăng xuất thành công!");
        } catch (error) {
            console.error('Logout error:', error);
        }
    });
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
    
    // Hide and remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Message box functions
function showMessageBox() {
    document.getElementById('message-box-overlay').style.display = 'flex';
}

function hideMessageBox() {
    document.getElementById('message-box-overlay').style.display = 'none';
}
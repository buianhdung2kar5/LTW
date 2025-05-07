document.addEventListener('DOMContentLoaded', function() {
    const favoriteBtn = document.getElementById('favorite-btn');
    const heartIcon = document.getElementById('heart-icon');
    const favoriteText = document.getElementById('favorite-text');
    
    // Modal elements
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    const detailsLoginBtn = document.getElementById('details-login-btn');
    const closeButtons = document.querySelectorAll('.close');
    
    // Login form elements
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    
    // Register form elements
    const registerForm = document.getElementById('register-form');
    const registerError = document.getElementById('register-error');
    
    // Show/hide login/register modals
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    
    // Check if user is logged in when page loads
    const isUserLoggedIn = document.body.classList.contains('logged-in') || 
                          (document.cookie.indexOf('user_id') !== -1) ||
                          (typeof session !== 'undefined' && session.user_id);
    
    // If user is logged in and there's a login button, convert it to favorites
    if (isUserLoggedIn && detailsLoginBtn) {
        convertLoginToFavoriteBtn();
    }
    
    function showToast(message, type = 'success') {
        // Sử dụng AppNotification nếu đã load - Kiểm tra module thông báo đã được tải chưa
        if (typeof AppNotification !== 'undefined') {
            AppNotification.show(message, type);
            return;
        }
        
        // Tạo container cho thông báo nếu chưa có - Đảm bảo có nơi để chứa thông báo
        const container = document.querySelector('.notification-container');
        if (!container) {
            const newContainer = document.createElement('div');
            newContainer.className = 'notification-container';
            document.body.appendChild(newContainer);
        }
        
        // Tạo thông báo mới - Tạo phần tử toast để hiển thị thông báo
        const toast = document.createElement('div');
        toast.className = `toast ${type}`; // Áp dụng kiểu dáng theo loại thông báo
        
        // Tạo biểu tượng cho thông báo - Thêm icon trực quan
        const icon = document.createElement('span');
        icon.className = 'toast-icon';
        icon.innerHTML = type === 'success' ? '✓' : '⚠'; // Icon khác nhau cho success/error
        
        // Tạo nội dung thông báo - Hiển thị nội dung tin nhắn
        const text = document.createElement('span');
        text.className = 'toast-message';
        text.textContent = message;
        
        // Thêm các phần tử vào toast
        toast.appendChild(icon);
        toast.appendChild(text);
        
        // Thêm toast vào container
        const toastContainer = document.querySelector('.notification-container');
        toastContainer.appendChild(toast);
        
        // Tự động ẩn toast sau 3 giây - Cơ chế tự động đóng thông báo
        setTimeout(() => {
            toast.style.opacity = '0'; // Hiệu ứng mờ dần
            setTimeout(() => {
                toastContainer.removeChild(toast); // Xóa khỏi DOM sau khi mờ dần
            }, 500);
        }, 3000);
    }
    
    // Modal functionality
    if (detailsLoginBtn) {
        detailsLoginBtn.addEventListener('click', function() {
            loginModal.style.display = 'flex';
        });
    }
    
    // Close modal when clicking the close button
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            loginModal.style.display = 'none';
            if (registerModal) registerModal.style.display = 'none';
        });
    });
    
    // Close modal when clicking outside the modal content
    window.addEventListener('click', (event) => {
        if (event.target === loginModal) {
            loginModal.style.display = 'none';
        }
        if (registerModal && event.target === registerModal) {
            registerModal.style.display = 'none';
        }
    });
    
    // Switch between login and register modals
    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', function(e) {
            e.preventDefault();
            loginModal.style.display = 'none';
            registerModal.style.display = 'flex';
        });
    }
    
    if (showLoginLink) {
        showLoginLink.addEventListener('click', function(e) {
            e.preventDefault();
            registerModal.style.display = 'none';
            loginModal.style.display = 'flex';
        });
    }
    
    // Function to convert login button to favorites button
    function convertLoginToFavoriteBtn() {
        // Get the login button - it might have been re-rendered, so query it again
        const detailsLoginBtn = document.getElementById('details-login-btn');
        if (!detailsLoginBtn) return;
        
        const filmId = detailsLoginBtn.getAttribute('data-film-id') || 
                      window.location.pathname.split('/').pop();
        
        // Create new favorite button to replace login button
        const newFavBtn = document.createElement('button');
        newFavBtn.className = 'add-to-list-btn';
        newFavBtn.id = 'favorite-btn';
        newFavBtn.setAttribute('data-film-id', filmId);
        newFavBtn.innerHTML = '<i class="fas fa-heart" id="heart-icon"></i> <span id="favorite-text">THÊM VÀO YÊU THÍCH</span>';
        
        // Replace the login button with the favorite button
        detailsLoginBtn.parentNode.replaceChild(newFavBtn, detailsLoginBtn);
        
        // Add event listener to the new favorite button
        newFavBtn.addEventListener('click', function() {
            fetch(`/user/favorites/toggle/${filmId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                const heartIcon = document.getElementById('heart-icon');
                const favoriteText = document.getElementById('favorite-text');
                
                if (data.action === 'added') {
                    newFavBtn.classList.add('favorited');
                    heartIcon.style.color = '#fff';
                    favoriteText.textContent = 'ĐÃ YÊU THÍCH';
                    showToast('Đã thêm vào danh sách yêu thích');
                } else if (data.action === 'removed') {
                    newFavBtn.classList.remove('favorited');
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
        
        // Check if this film is already in favorites
        fetch(`/user/favorites/check/${filmId}`)
            .then(response => response.json())
            .then(data => {
                if (data.isFavorite) {
                    newFavBtn.classList.add('favorited');
                    document.getElementById('heart-icon').style.color = '#fff';
                    document.getElementById('favorite-text').textContent = 'ĐÃ YÊU THÍCH';
                }
            })
            .catch(error => console.error('Error checking favorite status:', error));
    }
    
    // Expose the function to the global scope
    window.convertLoginToFavoriteBtn = convertLoginToFavoriteBtn;
    
    // Function to convert favorites button to login button
    function convertFavoriteToLoginBtn() {
        const favoriteBtn = document.getElementById('favorite-btn');
        if (!favoriteBtn) return;
        
        const filmId = favoriteBtn.getAttribute('data-film-id') || 
                      window.location.pathname.split('/').pop();
        
        // Create new login button to replace favorites button
        const newLoginBtn = document.createElement('button');
        newLoginBtn.className = 'add-to-list-btn login-btn';
        newLoginBtn.id = 'details-login-btn';
        newLoginBtn.setAttribute('data-film-id', filmId);
        newLoginBtn.innerHTML = '<i class="fas fa-heart"></i> ĐĂNG NHẬP';
        
        // Replace the favorites button with the login button
        favoriteBtn.parentNode.replaceChild(newLoginBtn, favoriteBtn);
        
        // Add event listener to the new login button
        newLoginBtn.addEventListener('click', function() {
            loginModal.style.display = 'flex';
        });
    }
    
    // Make this function globally accessible
    window.convertFavoriteToLoginBtn = convertFavoriteToLoginBtn;
    
    // Favorites functionality
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
    
    // Handle login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loginError.style.display = 'none';
            
            const formData = new FormData(loginForm);
            
            fetch('/auth/login', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Login successful
                    loginModal.style.display = 'none';
                    showToast('Đăng nhập thành công!');
                    
                    // Convert login button to favorite button
                    convertLoginToFavoriteBtn();
                    
                    // Update user info display in navbar if needed
                    if (data.username && window.updateUIAfterLogin) {
                        window.updateUIAfterLogin(data.username);
                    }
                    
                    // Add a class to the body to indicate logged in state
                    document.body.classList.add('logged-in');
                } else {
                    // Login failed
                    loginError.textContent = data.message || 'Đăng nhập thất bại!';
                    loginError.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                loginError.textContent = 'Lỗi kết nối! Vui lòng thử lại sau.';
                loginError.style.display = 'block';
            });
        });
    }
    
    // Handle register form submission
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            registerError.style.display = 'none';
            
            const formData = new FormData(registerForm);
            const password = formData.get('password');
            const confirmPassword = formData.get('confirm-password');
            
            if (password !== confirmPassword) {
                registerError.textContent = 'Mật khẩu không khớp!';
                registerError.style.display = 'block';
                return;
            }
            
            fetch('/auth/register', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Registration successful
                    registerModal.style.display = 'none';
                    showToast('Đăng ký thành công!');
                    
                    // Convert login button to favorite button
                    convertLoginToFavoriteBtn();
                    
                    // Update user info display in navbar if needed
                    if (data.username && window.updateUIAfterLogin) {
                        window.updateUIAfterLogin(data.username);
                    }
                } else {
                    // Registration failed
                    registerError.textContent = data.message || 'Đăng ký thất bại!';
                    registerError.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Registration error:', error);
                registerError.textContent = 'Lỗi kết nối! Vui lòng thử lại sau.';
                registerError.style.display = 'block';
            });
        });
    }
});
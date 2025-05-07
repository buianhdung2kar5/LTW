document.addEventListener("DOMContentLoaded", function() {
    // Lấy tham chiếu đến các phần tử DOM
    const logoutBtn = document.getElementById('logout-btn'); // Nút đăng xuất
    const changePasswordBtn = document.getElementById('change-password-btn'); // Nút đổi mật khẩu
    const changePasswordModal = document.getElementById('change-password-modal'); // Modal đổi mật khẩu
    const changePasswordForm = document.getElementById('change-password-form'); // Form đổi mật khẩu
    const changePasswordError = document.getElementById('change-password-error'); // Thông báo lỗi
    
    // Tải dữ liệu người dùng từ API
    async function loadUserProfile() {
        try {
            const response = await fetch('/user/profile/data'); // Gọi API để lấy thông tin hồ sơ
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            
            // Cập nhật giao diện với dữ liệu mới
            if (data.fullName && document.getElementById('fullname')) {
                document.getElementById('fullname').textContent = data.fullName; // Cập nhật tên đầy đủ
            }
            
            if (data.registerDate) {
                const joinDate = new Date(data.registerDate);
                const formattedDate = joinDate.toLocaleDateString('vi-VN'); // Định dạng ngày tham gia
                if (document.getElementById('join-date')) {
                    document.getElementById('join-date').textContent = formattedDate; // Cập nhật ngày tham gia
                }
            }
        } catch (error) {
            console.error('Error loading profile data:', error);
            // Fail im lặng - đã có dữ liệu được render từ server
        }
    }
    
    // Khởi tạo - tải dữ liệu hồ sơ
    loadUserProfile();
    
    // Hàm xử lý modal
    function openModal(modal) {
        if (modal) modal.style.display = 'flex'; // Hiển thị modal
    }
    
    function closeModal(modal) {
        if (modal) modal.style.display = 'none'; // Ẩn modal
    }
    
    // Mở modal đổi mật khẩu
    changePasswordBtn?.addEventListener('click', () => openModal(changePasswordModal));
    
    // Đóng modal khi click vào nút đóng
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    // Đóng modal khi click ra ngoài
    window.addEventListener('click', (e) => {
        if (e.target === changePasswordModal) closeModal(changePasswordModal);
    });
    
    // Xử lý đổi mật khẩu
    changePasswordForm?.addEventListener('submit', async (e) => {
        e.preventDefault(); // Ngăn form submit mặc định
        changePasswordError.style.display = 'none'; // Ẩn thông báo lỗi
        
        // Lấy giá trị từ form
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        // Kiểm tra mật khẩu mới khớp với xác nhận
        if (newPassword !== confirmPassword) {
            changePasswordError.textContent = 'Mật khẩu mới không khớp!';
            changePasswordError.style.display = 'block';
            return;
        }
        
        try {
            // Hiển thị loading nếu có module thông báo
            if (typeof AppNotification !== 'undefined') {
                AppNotification.showLoading('Đang cập nhật mật khẩu...');
            }
            
            // Gửi request đổi mật khẩu
            const response = await fetch('/user/password/change', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ currentPassword, newPassword })
            });
            
            // Ẩn loading sau khi nhận phản hồi
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            
            const data = await response.json();
            
            // Xử lý kết quả
            if (response.ok) {
                showToast('success', data.message || 'Đổi mật khẩu thành công!');
                closeModal(changePasswordModal);
                changePasswordForm.reset(); // Reset form
            } else {
                changePasswordError.textContent = data.message || 'Có lỗi xảy ra khi đổi mật khẩu';
                changePasswordError.style.display = 'block';
            }
        } catch (error) {
            // Xử lý lỗi kết nối
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            changePasswordError.textContent = 'Lỗi kết nối! Vui lòng thử lại sau.';
            changePasswordError.style.display = 'block';
        }
    });
    
    // Xử lý đăng xuất
    logoutBtn?.addEventListener('click', async (e) => {
        e.preventDefault(); // Ngăn chuyển hướng mặc định của thẻ a
        try {
            // Hiển thị loading
            if (typeof AppNotification !== 'undefined') {
                AppNotification.showLoading('Đang đăng xuất...');
            }
            
            // Gọi API đăng xuất
            const response = await fetch('/auth/logout', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            // Ẩn loading
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            
            // Chuyển hướng về trang chủ sau khi đăng xuất thành công
            window.location.href = '/';
        } catch (error) {
            // Xử lý lỗi đăng xuất
            if (typeof AppNotification !== 'undefined') {
                AppNotification.hideLoading();
            }
            console.error('Logout error:', error);
            showToast('error', 'Đăng xuất thất bại! Vui lòng thử lại.');
        }
    });
    
    // Hiển thị thông báo
    function showToast(type, message) {
        // Sử dụng AppNotification nếu có, ngược lại dùng alert
        if (typeof AppNotification !== 'undefined') {
            AppNotification.show(message, type);
        } else if (window.parent && typeof window.parent.showToast === 'function') {
            window.parent.showToast(type, message);
        } else {
            alert(message);
        }
    }
});
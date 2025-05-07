// Trang quản lý tài khoản người dùng
document.addEventListener('DOMContentLoaded', function() {
    // Lấy tham chiếu đến các phần tử DOM
    const accountTable = document.getElementById('accountTable'); // Bảng danh sách tài khoản
    const accountModal = document.getElementById('accountModal'); // Modal thêm/sửa tài khoản
    const deleteModal = document.getElementById('deleteModal'); // Modal xác nhận xóa
    const modalTitle = document.getElementById('modalTitle'); // Tiêu đề modal
    const accountForm = document.getElementById('accountForm'); // Form thông tin tài khoản
    const addAccountBtn = document.getElementById('addAccountBtn'); // Nút thêm tài khoản mới
    const roleFilter = document.getElementById('roleFilter'); // Bộ lọc theo vai trò
    const statusFilter = document.getElementById('statusFilter'); // Bộ lọc theo trạng thái
    const filterBtn = document.querySelector('.filter-section .btn-secondary'); // Nút áp dụng bộ lọc
    
    // Biến trạng thái
    let currentPage = 1; // Trang hiện tại
    let totalPages = 1; // Tổng số trang
    let currentAccountId = null; // ID tài khoản đang chỉnh sửa
    let deleteAccountId = null; // ID tài khoản cần xóa
    
    // Khởi tạo trang
    init();
    
    // Đăng ký các trình xử lý sự kiện
    addAccountBtn.addEventListener('click', openAddAccountModal); // Mở modal thêm tài khoản
    accountForm.addEventListener('submit', handleFormSubmit); // Xử lý submit form
    document.getElementById('saveBtn').addEventListener('click', handleFormSubmit); // Nút lưu
    document.getElementById('cancelBtn').addEventListener('click', closeAccountModal); // Nút hủy
    document.getElementById('confirmDeleteBtn').addEventListener('click', deleteAccount); // Xác nhận xóa
    document.getElementById('cancelDeleteBtn').addEventListener('click', closeDeleteModal); // Hủy xóa
    document.querySelectorAll('.modal .close').forEach(close => {
        close.addEventListener('click', function() {
            accountModal.style.display = 'none'; // Đóng modal account
            deleteModal.style.display = 'none'; // Đóng modal xóa
        });
    });
    filterBtn.addEventListener('click', applyFilters); // Áp dụng bộ lọc
    
    // Khởi tạo trang - Tải dữ liệu ban đầu
    function init() {
        AppNotification.showLoading('Đang tải dữ liệu tài khoản...'); // Hiển thị trạng thái đang tải
        loadAccounts(); // Tải danh sách tài khoản
        setupPagination(); // Thiết lập phân trang
    }
    
    // Tải danh sách tài khoản với bộ lọc tùy chọn
    function loadAccounts(page = 1, filters = {}) {
        // Xây dựng URL với tham số phân trang và bộ lọc
        let url = `/admin/accounts/api/list?page=${page}`;
        
        // Thêm các bộ lọc nếu có
        if (filters.role) url += `&role=${filters.role}`;
        if (filters.status) url += `&status=${filters.status}`;
        
        // Gọi API để lấy danh sách tài khoản
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Kiểm tra nếu data có thuộc tính error
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Cập nhật biến trạng thái
                currentPage = data.currentPage;
                totalPages = data.totalPages;
                renderAccounts(data.accounts); // Render danh sách tài khoản
                updatePagination(); // Cập nhật phân trang
                AppNotification.hideLoading(); // Ẩn trạng thái loading
            })
            .catch(error => {
                console.error('Error loading accounts:', error);
                AppNotification.hideLoading(); // Ẩn trạng thái loading
                
                // Hiển thị thông báo lỗi với nút thử lại
                AppNotification.showErrorWithRetry(
                    'Lỗi khi tải dữ liệu tài khoản: ' + error.message, 
                    () => loadAccounts(page, filters) // Hàm callback để thử lại
                );
                
                // Hiển thị trạng thái rỗng trong bảng
                const tbody = accountTable.querySelector('tbody');
                tbody.innerHTML = `<tr><td colspan="8" style="text-align: center;">
                    <div style="padding: 20px;">
                        <div style="margin-bottom: 10px;">Không thể tải dữ liệu. Vui lòng thử lại sau.</div>
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            <i class="fas fa-sync"></i> Tải lại trang
                        </button>
                    </div>
                </td></tr>`;
            });
    }
    
    // Render danh sách tài khoản vào bảng
    function renderAccounts(accounts) {
        const tbody = accountTable.querySelector('tbody');
        tbody.innerHTML = '';
        
        // Hiển thị thông báo nếu không có tài khoản
        if (accounts.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="8" style="text-align: center;">Không có tài khoản nào được tìm thấy</td>`;
            tbody.appendChild(row);
            return;
        }
        
        // Tạo từng dòng cho mỗi tài khoản
        accounts.forEach(account => {
            const row = document.createElement('tr');
            
            // Format ngày đăng ký thân thiện
            let formattedDate = 'N/A';
            if (account.registerDate) {
                const registerDate = new Date(account.registerDate);
                formattedDate = registerDate.toLocaleDateString('vi-VN');
            }
            
            // Tạo badge trạng thái (hoạt động/bị khóa)
            const statusClass = account.status === 'active' ? 'status-active' : 'status-inactive';
            const statusText = account.status === 'active' ? 'Hoạt động' : 'Bị khóa';
            
            // Ánh xạ giá trị vai trò sang văn bản hiển thị
            const roleDisplay = {
                'admin': 'Quản trị viên',
                'moderator': 'Điều hành viên',
                'user': 'Người dùng',
                'vip': 'VIP'
            };
            
            // Sử dụng ID số thay vì MongoDB _id
            row.innerHTML = `
                <td>${account.id || 'N/A'}</td>
                <td><img src="../static/images/avatar_user.png" alt="Avatar" style="width: 40px; height: 40px; border-radius: 50%;"></td>
                <td>${account.username || 'N/A'}</td>
                <td>${roleDisplay[account.role] || account.role || 'User'}</td>
                <td>${formattedDate}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td class="action-buttons">
                    <button class="action-btn edit-btn" data-id="${account._id || account.mongo_id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-btn delete-btn" data-id="${account._id || account.mongo_id}" data-name="${account.username}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        // Thêm trình xử lý sự kiện cho các nút mới
        attachActionButtonListeners();
    }
    
    // Gắn trình xử lý sự kiện cho các nút hành động
    function attachActionButtonListeners() {
        // Nút chỉnh sửa
        document.querySelectorAll('.edit-btn').forEach(button => {
            button.addEventListener('click', function() {
                const accountId = this.getAttribute('data-id');
                openEditAccountModal(accountId); // Mở modal chỉnh sửa
            });
        });
        
        // Nút xóa
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', function() {
                const accountId = this.getAttribute('data-id');
                const accountName = this.getAttribute('data-name');
                openDeleteModal(accountId, accountName); // Mở modal xác nhận xóa
            });
        });
    }

    // Setup pagination controls
    function setupPagination() {
        const pagination = document.querySelector('.pagination');
        
        // Add event listeners to pagination buttons
        pagination.addEventListener('click', function(e) {
            if (e.target.classList.contains('btn-page') || e.target.parentElement.classList.contains('btn-page')) {
                e.preventDefault();
                
                // Get the clicked button or its parent if an icon was clicked
                const button = e.target.classList.contains('btn-page') ? e.target : e.target.parentElement;
                
                // Check if it's a prev/next button or a page number
                if (button.querySelector('.fa-angle-left')) {
                    // Previous page
                    if (currentPage > 1) {
                        loadAccounts(currentPage - 1, getFilters());
                    }
                } else if (button.querySelector('.fa-angle-right')) {
                    // Next page
                    if (currentPage < totalPages) {
                        loadAccounts(currentPage + 1, getFilters());
                    }
                } else {
                    // Specific page number
                    const pageNumber = parseInt(button.textContent);
                    if (!isNaN(pageNumber)) {
                        loadAccounts(pageNumber, getFilters());
                    }
                }
            }
        });
    }
    
    // Update pagination buttons based on current page and total pages
    function updatePagination() {
        const pagination = document.querySelector('.pagination');
        pagination.innerHTML = '';
        
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn-page';
        prevBtn.innerHTML = '<i class="fas fa-angle-left"></i>';
        prevBtn.disabled = currentPage === 1;
        pagination.appendChild(prevBtn);
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, startPage + 4);
        
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `btn-page ${i === currentPage ? 'active' : ''}`;
            pageBtn.textContent = i;
            pagination.appendChild(pageBtn);
        }
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn-page';
        nextBtn.innerHTML = '<i class="fas fa-angle-right"></i>';
        nextBtn.disabled = currentPage === totalPages;
        pagination.appendChild(nextBtn);
    }
    
    // Apply filters from filter form
    function applyFilters() {
        const filters = getFilters();
        AppNotification.showLoading('Đang lọc dữ liệu...');
        loadAccounts(1, filters);
    }
    
    // Get current filter values
    function getFilters() {
        return {
            role: roleFilter.value,
            status: statusFilter.value
        };
    }
    
    // Open modal to add a new account
    function openAddAccountModal() {
        // Reset form
        accountForm.reset();
        document.getElementById('accountId').value = '';
        
        // Change modal title
        modalTitle.textContent = 'Thêm Tài Khoản Mới';
        
        // Show modal
        accountModal.style.display = 'block';
        
        // No current account being edited
        currentAccountId = null;
    }
    
    // Open modal to edit an existing account
    function openEditAccountModal(accountId) {
        // Set current account ID
        currentAccountId = accountId;
        
        // Change modal title
        modalTitle.textContent = 'Sửa Thông Tin Tài Khoản';
        
        // Fetch account details
        AppNotification.showLoading('Đang tải thông tin tài khoản...');
        fetch(`/admin/accounts/api/account/${accountId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(account => {
                // Fill form with account data
                document.getElementById('accountId').value = account.mongo_id || account.id;
                document.getElementById('username').value = account.username;

                document.getElementById('password').value = ''; // Don't show password
                document.getElementById('fullName').value = account.fullName || '';
                document.getElementById('role').value = account.role;
                document.getElementById('status').value = account.status;
                
                // Make username readonly
                document.getElementById('username').readOnly = true;
                
                // Show modal
                accountModal.style.display = 'block';
                AppNotification.hideLoading();
            })
            .catch(error => {
                console.error('Error loading account details:', error);
                showNotification('Lỗi khi tải thông tin tài khoản. Vui lòng thử lại sau.', 'error');
                AppNotification.hideLoading();
            });
    }
    
    // Open delete confirmation modal
    function openDeleteModal(accountId, accountName) {
        deleteAccountId = accountId;
        document.getElementById('deleteAccountName').textContent = accountName;
        deleteModal.style.display = 'block';
    }
    
    // Close account form modal
    function closeAccountModal() {
        accountModal.style.display = 'none';
    }
    
    // Close delete confirmation modal
    function closeDeleteModal() {
        deleteModal.style.display = 'none';
        deleteAccountId = null;
    }
    
    // Handle form submit (create or update account)
    function handleFormSubmit(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(accountForm);
        
        // Validate required fields
        const username = formData.get('username');
        const password = formData.get('password');
        
        if (!username || !username.trim()) {
            showNotification('Tên đăng nhập không được để trống', 'error');
            return;
        }
        
        if (!currentAccountId && (!password || !password.trim())) {
            showNotification('Mật khẩu không được để trống cho tài khoản mới', 'error');
            return;
        }
        
        // Determine if we're creating or updating
        const url = currentAccountId 
            ? `/admin/accounts/api/account/${currentAccountId}` 
            : '/admin/accounts/api/account';
        
        const method = currentAccountId ? 'PUT' : 'POST';
        
        // Show loading state
        const saveBtn = document.getElementById('saveBtn');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Đang xử lý...';
        saveBtn.disabled = true;
        AppNotification.showLoading('Đang lưu thông tin tài khoản...');
        
        // Submit the form
        fetch(url, {
            method: method,
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                closeAccountModal();
                loadAccounts(currentPage, getFilters());
                
                const message = currentAccountId 
                    ? 'Cập nhật tài khoản thành công!' 
                    : 'Tạo tài khoản mới thành công!';
                    
                showNotification(message, 'success');
            }
        })
        .catch(error => {
            console.error('Error saving account:', error);
            showNotification('Lỗi khi lưu tài khoản. Vui lòng thử lại sau.', 'error');
        })
        .finally(() => {
            // Restore button state
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
            AppNotification.hideLoading();
        });
    }
    
    // Delete an account
    function deleteAccount() {
        if (!deleteAccountId) return;
        
        // Show loading state
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        const originalText = deleteBtn.textContent;
        deleteBtn.textContent = 'Đang xử lý...';
        deleteBtn.disabled = true;
        AppNotification.showLoading('Đang xóa tài khoản...');
        
        fetch(`/admin/accounts/api/account/${deleteAccountId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                closeDeleteModal();
                loadAccounts(currentPage, getFilters());
                showNotification('Xóa tài khoản thành công!', 'success');
            }
        })
        .catch(error => {
            console.error('Error deleting account:', error);
            showNotification('Lỗi khi xóa tài khoản. Vui lòng thử lại sau.', 'error');
        })
        .finally(() => {
            // Restore button state
            deleteBtn.textContent = originalText;
            deleteBtn.disabled = false;
            AppNotification.hideLoading();
        });
    }
    
    // Show a notification message
    function showNotification(message, type = 'info') {
        AppNotification.show(message, type);
    }
});
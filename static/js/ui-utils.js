/**
 * Module Tiện ích UI
 * Cung cấp các chức năng UI phổ biến cho ứng dụng
 */
const UIUtils = {
    /**
     * Mở cửa sổ modal - Hiển thị cửa sổ modal bằng cách đặt display thành 'flex'
     * @param {HTMLElement} modal - Phần tử modal cần mở
     */
    openModal: function(modal) {
        if (modal) modal.style.display = 'flex';
    },

    /**
     * Đóng cửa sổ modal - Ẩn cửa sổ modal bằng cách đặt display thành 'none'
     * @param {HTMLElement} modal - Phần tử modal cần đóng
     */
    closeModal: function(modal) {
        if (modal) modal.style.display = 'none';
    },

    /**
     * Chuyển đổi chế độ toàn màn hình cho một phần tử
     * @param {HTMLElement} element - Phần tử cần chuyển đổi toàn màn hình
     * @param {Function} onStateChange - Hàm callback khi trạng thái toàn màn hình thay đổi
     */
    toggleFullscreen: function(element, onStateChange) {
        if (!document.fullscreenElement) {
            if (element.requestFullscreen) {
                element.requestFullscreen();
            } else if (element.webkitRequestFullscreen) { /* Safari */
                element.webkitRequestFullscreen();
            } else if (element.msRequestFullscreen) { /* IE11 */
                element.msRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) { /* Safari */
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) { /* IE11 */
                document.msExitFullscreen();
            }
        }
        
        if (typeof onStateChange === 'function') {
            onStateChange(!document.fullscreenElement);
        }
    },

    /**
     * Thiết lập chức năng đóng modal (nút X và click bên ngoài)
     * @param {HTMLElement} modal - Phần tử modal
     * @param {NodeList|Array} closeButtons - Bộ sưu tập các nút đóng
     */
    setupModalClosing: function(modal, closeButtons) {
        // Đóng khi click vào nút X
        if (closeButtons) {
            closeButtons.forEach(button => {
                button.addEventListener('click', () => this.closeModal(modal));
            });
        }
        
        // Đóng khi click bên ngoài
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                this.closeModal(modal);
            }
        });
    }
};

/**
 * Module Tải Tài Nguyên
 * Tải các tài nguyên JS và CSS theo yêu cầu
 */
const ResourceLoader = {
    /**
     * Tải một tập tin JavaScript - Tạo động phần tử script và thêm vào trang
     * @param {string} url - URL của tập tin JS
     * @param {boolean} async - Tải bất đồng bộ hay không
     * @returns {Promise} - Promise được giải quyết khi script đã được tải
     */
    loadScript: function(url, async = true) {
        return new Promise((resolve, reject) => {
            // Kiểm tra xem script đã tồn tại chưa - Tránh tải trùng lặp
            if (document.querySelector(`script[src="${url}"]`)) {
                resolve();
                return;
            }
            
            // Tạo phần tử script mới
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = url;
            script.async = async;
            
            // Xử lý sự kiện khi tải xong hoặc lỗi
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Lỗi tải script: ${url}`));
            
            document.head.appendChild(script);
        });
    },
    
    /**
     * Tải một tập tin CSS
     * @param {string} url - URL của tập tin CSS
     * @returns {Promise} - Promise được giải quyết khi CSS đã được tải
     */
    loadCSS: function(url) {
        return new Promise((resolve, reject) => {
            // Kiểm tra xem CSS đã tồn tại chưa
            if (document.querySelector(`link[href="${url}"]`)) {
                resolve();
                return;
            }
            
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = url;
            
            link.onload = () => resolve();
            link.onerror = () => reject(new Error(`Lỗi tải CSS: ${url}`));
            
            document.head.appendChild(link);
        });
    },
    
    /**
     * Tải nhiều tài nguyên cùng lúc
     * @param {Array} resources - Mảng các tài nguyên cần tải
     * @param {string} resources[].type - Loại tài nguyên ('js' hoặc 'css')
     * @param {string} resources[].url - URL của tài nguyên
     * @param {boolean} resources[].async - Chỉ áp dụng cho JS
     * @returns {Promise} - Promise được giải quyết khi tất cả tài nguyên đã được tải
     */
    loadResources: function(resources) {
        const promises = resources.map(resource => {
            if (resource.type === 'js') {
                return this.loadScript(resource.url, resource.async);
            } else if (resource.type === 'css') {
                return this.loadCSS(resource.url);
            }
            return Promise.reject(new Error(`Loại tài nguyên không xác định: ${resource.type}`));
        });
        
        return Promise.all(promises);
    }
};

// Tải các tài nguyên không thiết yếu sau khi trang đã tải xong
document.addEventListener('DOMContentLoaded', function() {
    const nonCriticalResources = [
        { type: 'css', url: '/static/css/homepage.css' },
        { type: 'js', url: '/static/js/lazy-loading.js', async: true },
        { type: 'js', url: '/static/js/cache-utils.js', async: true }
    ];
    
    // Chờ 200ms để ưu tiên render các phần tử quan trọng trước
    setTimeout(() => {
        ResourceLoader.loadResources(nonCriticalResources)
            .catch(error => console.error('Không thể tải tài nguyên:', error));
    }, 200);
});

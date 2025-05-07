/**
 * API Utilities Module - Enhanced with caching
 */
const ApiUtils = {
    // Cache thời gian cho các request GET
    _cache: {},
    _cacheEnabled: true,
    _defaultCacheTTL: 5 * 60 * 1000, // 5 phút
    
    /**
     * Kích hoạt/vô hiệu hóa cache
     * @param {boolean} enabled - Trạng thái cache
     */
    enableCache: function(enabled) {
        this._cacheEnabled = enabled;
    },
    
    /**
     * Làm sạch cache theo prefix url
     * @param {string} urlPrefix - Prefix của URL cần xóa cache
     */
    clearCache: function(urlPrefix = '') {
        if (!urlPrefix) {
            this._cache = {};
            return;
        }
        
        Object.keys(this._cache).forEach(key => {
            if (key.startsWith(urlPrefix)) {
                delete this._cache[key];
            }
        });
    },
    
    /**
     * Thực hiện request GET với cache
     * @param {string} url - URL để fetch
     * @param {Object} options - Options cho fetch
     * @param {number} cacheTTL - Thời gian cache (ms), 0 để bỏ qua cache
     * @returns {Promise} - Promise với kết quả
     */
    get: async function(url, options = {}, cacheTTL = this._defaultCacheTTL) {
        // Kiểm tra cache nếu được bật và không disabled với request hiện tại
        if (this._cacheEnabled && cacheTTL > 0) {
            const cacheKey = url + JSON.stringify(options);
            const cachedItem = this._cache[cacheKey];
            
            if (cachedItem && Date.now() < cachedItem.expiry) {
                return cachedItem.data;
            }
        }
        
        try {
            const defaultHeaders = {
                'X-Requested-With': 'XMLHttpRequest'
            };
            
            const response = await fetch(url, {
                method: 'GET',
                headers: { ...defaultHeaders, ...options.headers },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Lưu vào cache nếu được bật
            if (this._cacheEnabled && cacheTTL > 0) {
                const cacheKey = url + JSON.stringify(options);
                this._cache[cacheKey] = {
                    data: data,
                    expiry: Date.now() + cacheTTL
                };
            }
            
            return data;
        } catch (error) {
            console.error(`GET request failed for ${url}:`, error);
            throw error;
        }
    },
    
    /**
     * Thực hiện request POST
     * @param {string} url - URL để fetch
     * @param {Object|FormData} data - Dữ liệu để gửi
     * @param {Object} options - Options cho fetch
     * @returns {Promise} - Promise với kết quả
     */
    post: async function(url, data, options = {}) {
        try {
            // Thiết lập header cơ bản cho request
            const defaultHeaders = {
                'X-Requested-With': 'XMLHttpRequest' // Đánh dấu request là AJAX
            };
            
            // Xác định content type và format dữ liệu - Hỗ trợ cả JSON và FormData
            let body;
            if (data instanceof FormData) { // Kiểm tra dữ liệu là FormData
                body = data; // Giữ nguyên FormData
            } else {
                body = JSON.stringify(data); // Chuyển đổi object thành JSON string
                defaultHeaders['Content-Type'] = 'application/json'; // Thiết lập Content-Type cho JSON
            }
            
            // Thực hiện gọi API - Gửi request POST đến server
            const response = await fetch(url, {
                method: 'POST',
                headers: { ...defaultHeaders, ...options.headers }, // Merge headers
                body: body, // Dữ liệu gửi đi
                ...options // Các tùy chọn khác
            });
            
            // Kiểm tra kết quả trả về
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Xóa các cache liên quan đến URL này sau khi POST thành công
            this.clearCache(url.split('?')[0]); // Đảm bảo dữ liệu mới được hiển thị
            
            // Trả về kết quả dưới dạng JSON
            return await response.json();
        } catch (error) {
            console.error(`POST request failed for ${url}:`, error);
            throw error; // Ném lỗi để xử lý ở nơi gọi hàm
        }
    },
    
    /**
     * Thực hiện request PUT - Cập nhật dữ liệu hiện có
     * @param {string} url - URL để fetch
     * @param {Object} data - Dữ liệu để gửi
     * @param {Object} options - Options cho fetch
     * @returns {Promise} - Promise với kết quả
     */
    put: async function(url, data, options = {}) {
        try {
            // Thiết lập header cơ bản cho request PUT
            const defaultHeaders = {
                'Content-Type': 'application/json', // Mặc định dùng JSON cho PUT
                'X-Requested-With': 'XMLHttpRequest' // Đánh dấu request là AJAX
            };
            
            // Gửi request PUT
            const response = await fetch(url, {
                method: 'PUT',
                headers: { ...defaultHeaders, ...options.headers },
                body: JSON.stringify(data),
                ...options
            });
            
            // Kiểm tra kết quả
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Xóa các cache liên quan đến URL này sau khi PUT thành công
            this.clearCache(url.split('?')[0]);
            
            return await response.json();
        } catch (error) {
            console.error(`PUT request failed for ${url}:`, error);
            throw error;
        }
    },
    
    /**
     * Thực hiện request DELETE
     * @param {string} url - URL để fetch
     * @param {Object} options - Options cho fetch
     * @returns {Promise} - Promise với kết quả
     */
    delete: async function(url, options = {}) {
        try {
            const defaultHeaders = {
                'X-Requested-With': 'XMLHttpRequest'
            };
            
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { ...defaultHeaders, ...options.headers },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Xóa các cache liên quan đến URL này sau khi DELETE thành công
            this.clearCache(url.split('?')[0]);
            
            return await response.json();
        } catch (error) {
            console.error(`DELETE request failed for ${url}:`, error);
            throw error;
        }
    }
};

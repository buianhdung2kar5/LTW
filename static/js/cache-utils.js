/**
 * Client-side caching utility
 */
const CacheUtils = {
    // Thời gian cache mặc định: 5 phút
    DEFAULT_TTL: 5 * 60 * 1000,
    
    /**
     * Lưu dữ liệu vào cache
     * @param {string} key - Khóa cache
     * @param {*} data - Dữ liệu cần lưu
     * @param {number} ttl - Thời gian sống (ms)
     */
    set: function(key, data, ttl = this.DEFAULT_TTL) {
        const item = {
            data: data,
            expiry: Date.now() + ttl
        };
        localStorage.setItem(`cache_${key}`, JSON.stringify(item));
    },
    
    /**
     * Lấy dữ liệu từ cache
     * @param {string} key - Khóa cache
     * @returns {*|null} Dữ liệu hoặc null nếu không tìm thấy/hết hạn
     */
    get: function(key) {
        const itemStr = localStorage.getItem(`cache_${key}`);
        if (!itemStr) return null;
        
        try {
            const item = JSON.parse(itemStr);
            if (Date.now() > item.expiry) {
                localStorage.removeItem(`cache_${key}`);
                return null;
            }
            return item.data;
        } catch (error) {
            localStorage.removeItem(`cache_${key}`);
            return null;
        }
    },
    
    /**
     * Xóa một mục khỏi cache
     * @param {string} key - Khóa cache 
     */
    remove: function(key) {
        localStorage.removeItem(`cache_${key}`);
    },
    
    /**
     * Xóa tất cả cache
     */
    clear: function() {
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('cache_')) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));
    }
};

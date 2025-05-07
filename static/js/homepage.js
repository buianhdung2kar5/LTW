document.addEventListener('DOMContentLoaded', () => {
    const carousel = document.querySelector('.carousel');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    const filmItems = document.querySelectorAll('.film-item');

    // Sao chép các phần tử để tạo hiệu ứng cuộn tròn
    const originalItemsCount = filmItems.length;
    filmItems.forEach(item => {
        const clone = item.cloneNode(true);
        clone.setAttribute('data-clone', 'true');
        carousel.appendChild(clone);
    });

    // Tính chiều rộng tối đa của carousel (chỉ tính bản gốc)
    const itemWidth = 220; // Chiều rộng của mỗi .film-item
    const maxScroll = originalItemsCount * itemWidth;

    // Trạng thái để ngăn animation chồng chéo
    let isScrolling = false;

    // Hàm làm mượt chuyển đổi vị trí
    function smoothScroll(target) {
        if (isScrolling) return;
        isScrolling = true;
        
        const startPosition = carousel.scrollLeft;
        const distance = target - startPosition;
        const duration = 500; // ms
        let startTime = null;
        
        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const progress = Math.min(timeElapsed / duration, 1);
            const easeInOut = progress < 0.5 
                ? 2 * progress * progress 
                : 1 - Math.pow(-2 * progress + 2, 2) / 2;
                
            carousel.scrollLeft = startPosition + distance * easeInOut;
            
            if (timeElapsed < duration) {
                requestAnimationFrame(animation);
            } else {
                isScrolling = false;
                // Kiểm tra vòng lặp
                if (carousel.scrollLeft >= maxScroll) {
                    carousel.scrollLeft = 0;
                } else if (carousel.scrollLeft <= 0) {
                    carousel.scrollLeft = maxScroll - itemWidth;
                }
            }
        }
        
        requestAnimationFrame(animation);
    }
    
    // Sự kiện click nút prev
    prevBtn.addEventListener('click', () => {
        const target = carousel.scrollLeft - (itemWidth * 3);
        smoothScroll(target);
    });
    
    // Sự kiện click nút next
    nextBtn.addEventListener('click', () => {
        const target = carousel.scrollLeft + (itemWidth * 3);
        smoothScroll(target);
    });
    
    // Tự động chuyển slide sau mỗi 5 giây
    let autoScrollInterval = setInterval(() => {
        if (!document.hidden) {
            const target = carousel.scrollLeft + (itemWidth * 3);
            smoothScroll(target);
        }
    }, 5000);
    
    // Xử lý khi người dùng tương tác với carousel
    carousel.addEventListener('mouseenter', () => {
        clearInterval(autoScrollInterval);
    });
    
    carousel.addEventListener('mouseleave', () => {
        autoScrollInterval = setInterval(() => {
            if (!document.hidden) {
                const target = carousel.scrollLeft + (itemWidth * 3);
                smoothScroll(target);
            }
        }, 5000);
    });
});
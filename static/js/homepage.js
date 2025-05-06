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
    const smoothScrollTo = (targetScroll, duration) => {
        if (isScrolling) return;
        isScrolling = true;

        const startScroll = carousel.scrollLeft;
        const distance = targetScroll - startScroll;
        let startTime = null;

        const animation = (currentTime) => {
            if (!startTime) startTime = currentTime;
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const ease = progress * (2 - progress); // Ease-in-out
            carousel.scrollLeft = startScroll + distance * ease;

            if (progress < 1) {
                requestAnimationFrame(animation);
            } else {
                isScrolling = false;
            }
        };

        requestAnimationFrame(animation);
    };

    // Hàm cuộn tùy chỉnh
    const customScrollBy = (distance, duration) => {
        if (isScrolling) return;
        isScrolling = true;

        const startScroll = carousel.scrollLeft;
        const targetScroll = startScroll + distance;
        let startTime = null;

        const animation = (currentTime) => {
            if (!startTime) startTime = currentTime;
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const ease = progress * (2 - progress); // Ease-in-out
            carousel.scrollLeft = startScroll + distance * ease;

            if (progress < 1) {
                requestAnimationFrame(animation);
            } else {
                isScrolling = false;
            }
        };

        requestAnimationFrame(animation);
    };

    // Cuộn sang trái khi nhấn nút "prev"
    prevBtn.addEventListener('click', () => {
        const currentScroll = carousel.scrollLeft;
        if (currentScroll <= itemWidth / 2) {
            // Khi ở đầu, nhảy đến cuối và cuộn mượt
            smoothScrollTo(maxScroll, 300);
            setTimeout(() => {
                customScrollBy(-itemWidth, 600); // Cuộn ngược 1 item trong 600ms
            }, 300);
        } else {
            customScrollBy(-itemWidth, 600); // Cuộn ngược 1 item trong 600ms
        }
    });

    // Cuộn sang phải khi nhấn nút "next"
    nextBtn.addEventListener('click', () => {
        const currentScroll = carousel.scrollLeft;
        if (currentScroll >= maxScroll - itemWidth / 2) {
            // Khi gần cuối, nhảy về đầu và cuộn mượt
            smoothScrollTo(0, 300);
            setTimeout(() => {
                customScrollBy(itemWidth, 600); // Cuộn tiếp 1 item trong 600ms
            }, 300);
        } else {
            customScrollBy(itemWidth, 600); // Cuộn tiếp 1 item trong 600ms
        }
    });
});
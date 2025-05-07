document.addEventListener('DOMContentLoaded', function() {
    // Lấy tham chiếu đến các phần tử DOM cần thiết cho trình phát video
    const videoPlayer = document.getElementById('video-player');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const rewindBtn = document.getElementById('rewind-btn'); // Nút tua lùi
    const forwardBtn = document.getElementById('forward-btn'); // Nút tua tiến
    const progressBar = document.getElementById('progress-bar'); // Thanh tiến trình
    const progress = document.getElementById('progress'); // Phần đã phát
    const currentTimeEl = document.getElementById('current-time'); // Hiển thị thời gian hiện tại
    const durationEl = document.getElementById('duration'); // Hiển thị tổng thời lượng
    const muteBtn = document.getElementById('mute-btn'); // Nút tắt/bật âm thanh
    const volumeSlider = document.getElementById('volume-slider'); // Thanh điều chỉnh âm lượng 
    const settingsBtn = document.getElementById('settings-btn'); // Nút cài đặt
    const settingsMenu = document.getElementById('settings-menu'); // Menu cài đặt
    const fullscreenBtn = document.getElementById('fullscreen-btn'); // Nút toàn màn hình
    const featuredThumbnail = document.querySelector('.featured-thumbnail'); // Khung chứa video
    const videoControls = document.querySelector('.video-controls'); // Thanh điều khiển video
    
    // Kiểm tra xem phần tử video có tồn tại không trước khi thực hiện thao tác
    if (!videoPlayer) return;

    // Đặt trạng thái ban đầu cho nút phát/tạm dừng là PHÁT
    playPauseBtn.textContent = '▶';
    
    // Tạo nút mở rộng cho trình phát video
    const expandBtn = document.createElement('button');
    expandBtn.className = 'expand-video-btn'; // CSS để tạo kiểu nút mở rộng
    expandBtn.innerHTML = '↕';
    expandBtn.title = 'Expand video';
    featuredThumbnail.appendChild(expandBtn);
    
    // Helper functions
    function formatTime(timeInSeconds) {
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);
        return `${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
    }
    
    function updateVolumeUI(value) {
        const isMuted = value === 0;
        muteBtn.textContent = isMuted ? '🔇' : '🔊';
        volumeSlider.value = value * 100;
        videoPlayer.volume = value;
        videoPlayer.muted = isMuted;
    }
    
    function togglePlayPause() {
        if (videoPlayer.paused) {
            videoPlayer.play();
            playPauseBtn.textContent = '⏸';
            featuredThumbnail.classList.remove('video-paused');
        } else {
            videoPlayer.pause();
            playPauseBtn.textContent = '▶';
            featuredThumbnail.classList.add('video-paused');
        }
    }

    // Initialize player
    videoPlayer.addEventListener('loadedmetadata', function() {
        durationEl.textContent = formatTime(videoPlayer.duration);
        // Mark as paused initially to show controls
        featuredThumbnail.classList.add('video-paused');
    });
    
    // Add click event to the video element itself to toggle play/pause
    videoPlayer.addEventListener('click', function(e) {
        // Prevent the click from triggering other elements
        e.stopPropagation();
        togglePlayPause();
    });
    
    // Expand video button
    expandBtn.addEventListener('click', function() {
        featuredThumbnail.classList.toggle('video-expanded');
        this.innerHTML = featuredThumbnail.classList.contains('video-expanded') ? '↓' : '↕';
    });
    
    // Player controls
    playPauseBtn.addEventListener('click', togglePlayPause);
    
    rewindBtn.addEventListener('click', function() {
        videoPlayer.currentTime = Math.max(0, videoPlayer.currentTime - 10);
    });
    
    forwardBtn.addEventListener('click', function() {
        videoPlayer.currentTime = Math.min(videoPlayer.duration, videoPlayer.currentTime + 10);
    });
    
    videoPlayer.addEventListener('timeupdate', function() {
        const progressPercent = (videoPlayer.currentTime / videoPlayer.duration) * 100;
        progress.style.width = `${progressPercent}%`;
        currentTimeEl.textContent = `${formatTime(videoPlayer.currentTime)} / `;
    });
    
    progressBar.addEventListener('click', function(e) {
        const seekTime = (e.offsetX / this.clientWidth) * videoPlayer.duration;
        videoPlayer.currentTime = seekTime;
    });
    
    // Volume controls
    muteBtn.addEventListener('click', function() {
        const newMuteState = !videoPlayer.muted;
        updateVolumeUI(newMuteState ? 0 : videoPlayer.volume);
    });
    
    volumeSlider.addEventListener('input', function() {
        const volumeValue = this.value / 100;
        updateVolumeUI(volumeValue);
    });
    
    // Settings menu
    settingsBtn.addEventListener('click', function() {
        settingsMenu.style.display = settingsMenu.style.display === 'block' ? 'none' : 'block';
    });
    
    // Add playback speed control
    document.querySelectorAll('.settings-item').forEach(item => {
        item.addEventListener('click', function() {
            const speed = parseFloat(this.getAttribute('data-speed'));
            if (!isNaN(speed)) {
                videoPlayer.playbackRate = speed;
                // Close menu after selection
                settingsMenu.style.display = 'none';
            }
        });
    });
    
    document.addEventListener('click', function(e) {
        if (e.target !== settingsBtn && !settingsMenu.contains(e.target)) {
            settingsMenu.style.display = 'none';
        }
    });
    
    // Fullscreen toggle
    fullscreenBtn.addEventListener('click', function() {
        if (document.fullscreenElement) {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            featuredThumbnail.classList.remove('video-fullscreen');
        } else {
            if (featuredThumbnail.requestFullscreen) {
                featuredThumbnail.requestFullscreen();
            } else if (featuredThumbnail.webkitRequestFullscreen) {
                featuredThumbnail.webkitRequestFullscreen();
            } else if (featuredThumbnail.msRequestFullscreen) {
                featuredThumbnail.msRequestFullscreen();
            }
            featuredThumbnail.classList.add('video-fullscreen');
        }
    });
    
    // Handle fullscreen change events
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);
    
    function handleFullscreenChange() {
        if (!document.fullscreenElement && 
            !document.webkitFullscreenElement && 
            !document.mozFullScreenElement && 
            !document.msFullscreenElement) {
            featuredThumbnail.classList.remove('video-fullscreen');
        }
    }
    
    // Controls visibility
    if (featuredThumbnail && videoControls) {
        featuredThumbnail.addEventListener('mouseenter', () => {
            videoControls.style.opacity = '1';
        });
        
        featuredThumbnail.addEventListener('mouseleave', () => {
            if (!videoPlayer.paused) {
                videoControls.style.opacity = '0';
            }
        });
    }
});
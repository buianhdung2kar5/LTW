document.addEventListener('DOMContentLoaded', function() {
    const videoPlayer = document.getElementById('video-player');
    
    if (videoPlayer) {
        const playPauseBtn = document.getElementById('play-pause-btn');
        const rewindBtn = document.getElementById('rewind-btn');
        const forwardBtn = document.getElementById('forward-btn');
        const progressBar = document.getElementById('progress-bar');
        const progress = document.getElementById('progress');
        const currentTimeDisplay = document.getElementById('current-time');
        const durationDisplay = document.getElementById('duration');
        const muteBtn = document.getElementById('mute-btn');
        const volumeSlider = document.getElementById('volume-slider');
        const settingsBtn = document.getElementById('settings-btn');
        const settingsMenu = document.getElementById('settings-menu');
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        
        videoPlayer.removeAttribute('controls');
        document.querySelector('.video-controls').style.opacity = '1';
        
        playPauseBtn.addEventListener('click', togglePlayPause);
        rewindBtn.addEventListener('click', () => { videoPlayer.currentTime -= 10; });
        forwardBtn.addEventListener('click', () => { videoPlayer.currentTime += 10; });
        muteBtn.addEventListener('click', toggleMute);
        volumeSlider.addEventListener('input', setVolume);
        fullscreenBtn.addEventListener('click', toggleFullscreen);
        settingsBtn.addEventListener('click', toggleSettings);
        
        videoPlayer.addEventListener('timeupdate', updateProgress);
        progressBar.addEventListener('click', seek);
        
        videoPlayer.addEventListener('loadedmetadata', () => {
            durationDisplay.textContent = formatTime(videoPlayer.duration);
        });
        
        function togglePlayPause() {
            if (videoPlayer.paused) {
                videoPlayer.play();
                playPauseBtn.textContent = '⏸';
            } else {
                videoPlayer.pause();
                playPauseBtn.textContent = '▶';
            }
        }
        
        function updateProgress() {
            const percent = (videoPlayer.currentTime / videoPlayer.duration) * 100;
            progress.style.width = percent + '%';
            currentTimeDisplay.textContent = formatTime(videoPlayer.currentTime) + ' / ';
        }
        
        function formatTime(seconds) {
            const minutes = Math.floor(seconds / 60);
            seconds = Math.floor(seconds % 60);
            return minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
        }
        
        function seek(e) {
            const rect = progressBar.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / progressBar.offsetWidth;
            videoPlayer.currentTime = pos * videoPlayer.duration;
        }
        
        function toggleMute() {
            videoPlayer.muted = !videoPlayer.muted;
            muteBtn.textContent = videoPlayer.muted ? '🔇' : '🔊';
            volumeSlider.value = videoPlayer.muted ? 0 : videoPlayer.volume * 100;
        }
        
        function setVolume() {
            videoPlayer.volume = volumeSlider.value / 100;
            videoPlayer.muted = (videoPlayer.volume === 0);
            muteBtn.textContent = videoPlayer.muted ? '🔇' : '🔊';
        }
        
        function toggleSettings() {
            settingsMenu.style.display = settingsMenu.style.display === 'block' ? 'none' : 'block';
        }
        
        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                if (videoPlayer.requestFullscreen) {
                    videoPlayer.requestFullscreen();
                } else if (videoPlayer.webkitRequestFullscreen) {
                    videoPlayer.webkitRequestFullscreen();
                } else if (videoPlayer.msRequestFullscreen) {
                    videoPlayer.msRequestFullscreen();
                }
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            }
        }
        
        const featuredThumbnail = document.querySelector('.featured-thumbnail');
        featuredThumbnail.addEventListener('mouseenter', () => {
            document.querySelector('.video-controls').style.opacity = '1';
        });
        
        featuredThumbnail.addEventListener('mouseleave', () => {
            if (!videoPlayer.paused) {
                document.querySelector('.video-controls').style.opacity = '0';
            }
        });
    }
});
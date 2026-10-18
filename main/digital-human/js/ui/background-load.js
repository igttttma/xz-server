// Background image load detection
(function() {
    const backgroundContainer = document.getElementById('backgroundContainer');

    // Extract the background image URL
    let bgImageUrl = window.getComputedStyle(backgroundContainer).backgroundImage;
    const urlMatch = bgImageUrl && bgImageUrl.match(/url\(["']?(.*?)["']?\)/);
    
    if (!urlMatch || !urlMatch[1]) {
        console.warn('Could not extract a valid background image URL');
        return;
    }
    
    bgImageUrl = urlMatch[1];
    
    const bgImage = new Image();
    bgImage.onerror = function() {
        console.error('Failed to load the background image:', bgImageUrl);
    };

    // Show the model loading indicator once loading succeeds
    bgImage.onload = function() {
        modelLoading.style.display = 'flex';
    };

    bgImage.src = bgImageUrl;
})();
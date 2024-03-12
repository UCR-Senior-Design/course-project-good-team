function openNav() {
    document.getElementById("side").style.width = "250px";
    document.getElementById("openbtn").classList.add("hidden")

}

function closeNav() {
    document.getElementById("side").style.width = "0px";
    document.getElementById("openbtn").classList.remove("hidden")
}

let currentTrackIndex = -1; // Start before the first index to not display immediately
let friendQueue = [];

function loadFriendQueue() {
    fetch('/discover/friend-queue')
        .then(response => response.json())
        .then(data => {
            friendQueue = data;
            // Initialize currentTrackIndex to 0 when data is successfully fetched
            currentTrackIndex = 0;
            displayCurrentTrack();
        }).catch(error => console.error('Error loading friend queue:', error));
}

function displayCurrentTrack() {
    const queueDetailsEl = document.querySelector('.queue-details');
    if (friendQueue.length > 0 && currentTrackIndex >= 0 && currentTrackIndex < friendQueue.length) {
        const track = friendQueue[currentTrackIndex];
        queueDetailsEl.innerHTML = `
            <div class="album-cover">
                <img src="${track.image_url}" alt="Album cover">
            </div>
            <p>${track.track_name}</p>
            <p>Liked by: ${track.friends.join(', ')}</p>
        `;
    } else {
        queueDetailsEl.innerHTML = `<p>No tracks available in the friend queue.</p>`;
    }
}

function nextTrack() {
    if (currentTrackIndex < friendQueue.length - 1) {
        currentTrackIndex++;
        displayCurrentTrack();
    }
}

function previousTrack() {
    if (currentTrackIndex > 0) {
        currentTrackIndex--;
        displayCurrentTrack();
    }
}

function toggleFriendQueueDisplay() {
    const friendQueueEl = document.querySelector('.friend-queue');
    const playlistAnalyzerEl = document.querySelector('.playlist-analyzer');
    const songDetailsEl = document.querySelector('.content .song-details');

    if (friendQueueEl.style.display === "block") {
        friendQueueEl.style.display = "none";
        // Ensure that when hiding the friend queue, the song details are visible if the playlist analyzer is not open
        if (playlistAnalyzerEl.style.display !== "block") {
            songDetailsEl.style.display = "block";
        }
    } else {
        loadFriendQueue(); // Load friend queue only when showing it
        friendQueueEl.style.display = "block";
        playlistAnalyzerEl.style.display = "none"; // Ensure playlist analyzer is hidden when showing friend queue
        songDetailsEl.style.display = "none"; // Hide song details when showing friend queue
    }
}

function togglePlaylistAnalyzerDisplay() {
    const playlistAnalyzerEl = document.querySelector('.playlist-analyzer');
    const friendQueueEl = document.querySelector('.friend-queue');
    const songDetailsEl = document.querySelector('.content .song-details');

    if (playlistAnalyzerEl.style.display === "block") {
        playlistAnalyzerEl.style.display = "none";
        // Ensure that when hiding the playlist analyzer, the song details are visible if the friend queue is not open
        if (friendQueueEl.style.display !== "block") {
            songDetailsEl.style.display = "block";
        }
    } else {
        playlistAnalyzerEl.style.display = "block";
        friendQueueEl.style.display = "none"; // Ensure friend queue is hidden when showing playlist analyzer
        songDetailsEl.style.display = "none"; // Hide song details when showing playlist analyzer
    }
}


// Event listeners for next and previous buttons
document.addEventListener('DOMContentLoaded', function() {
    const nextButton = document.querySelector('.navigation-buttons button:nth-child(2)'); // Assuming next button is the second button
    const prevButton = document.querySelector('.navigation-buttons button:nth-child(1)'); // Assuming previous button is the first button

    nextButton.addEventListener('click', nextTrack);
    prevButton.addEventListener('click', previousTrack);

    const friendQueueButton = document.querySelector('.friend-queue-btn');
    friendQueueButton.addEventListener('click', toggleFriendQueueDisplay);

    const playlistAnalyzerButton = document.querySelectorAll('.sidebar-container .sidebutton')[2].querySelector('button');
    playlistAnalyzerButton.addEventListener('click', function(event) {
        event.preventDefault(); // Prevent the default button action
        togglePlaylistAnalyzerDisplay(); // Call the function to show the Playlist Analyzer section
    });

    document.getElementById('playlist-analyzer-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const playlistURL = document.getElementById('playlist-url').value;
        analyzePlaylist(playlistURL); // Implement this function to handle the analysis and display results
    });

    // Automatically analyze playlist if 'analyze_playlist' parameter exists in the URL
    const playlistId = getQueryParam('analyze_playlist');
    if (playlistId) {
        const playlistURL = `https://open.spotify.com/playlist/${playlistId}`;
        document.getElementById('playlist-url').value = playlistURL;
        analyzePlaylist(playlistURL); // Start the analysis
        
        // Show the Playlist Analyzer section
        showPlaylistAnalyzerSection(); // We'll define this function next
    }
});


// This function will handle analyzing the playlist, either from form submission or direct calling
function analyzePlaylist(playlistURL = null) {
    // If no URL is passed, try to get it from the input field
    const finalPlaylistURL = playlistURL || document.getElementById('playlist-url').value;

    // Show loading indicator
    document.getElementById('loading-indicator').style.display = 'block';

    const data = { playlist_url: finalPlaylistURL };

    fetch('/analyze_playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loading-indicator').style.display = 'none';
        displayAnalysisResults(data);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading-indicator').style.display = 'none';
    });
}


function analyzePlaylistDirectly(playlistURL) {
    // Similar logic as in the analyzePlaylist function, but directly uses the playlistURL parameter
    // Show loading indicator
    document.getElementById('loading-indicator').style.display = 'block';

    // Build the data object as needed by your back-end
    const data = { playlist_url: playlistURL };

    fetch('/analyze_playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loading-indicator').style.display = 'none';
        displayAnalysisResults(data);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading-indicator').style.display = 'none';
    });
}


function displayAnalysisResults(data) {
    const resultsEl = document.querySelector('.playlist-analysis-results');
    resultsEl.innerHTML = ''; // Clear previous results
    let content = `<h3>Analysis Results</h3>`;

    // Display average features
    content += '<div><h4>Average Features:</h4><ul>';
    Object.keys(data.average_features).forEach(feature => {
        content += `<li>${feature.charAt(0).toUpperCase() + feature.slice(1)}: ${data.average_features[feature].toFixed(2)}</li>`;
    });
    content += '</ul></div>';

    // Display top 3 most common genres
    content += '<div><h4>Genres:</h4><ul>';
    data.most_common_genres.slice(0, 3).forEach(([genre, _]) => {
        content += `<li>${genre}</li>`; // Removed the count next to each genre
    });
    content += '</ul></div>';

    resultsEl.innerHTML = content;
}



document.getElementById('playlist-analyzer-form').addEventListener('submit', function(event) {
    event.preventDefault();
    analyzePlaylist(playlistURL);
});

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function showPlaylistAnalyzerSection() {
    const playlistAnalyzerEl = document.querySelector('.playlist-analyzer');
    const otherSections = [document.querySelector('.friend-queue'), document.querySelector('.content .song-details')]; // Add any other sections that should be hidden

    // Display the Playlist Analyzer and hide other sections
    playlistAnalyzerEl.style.display = 'block';
    otherSections.forEach(section => {
        if (section) section.style.display = 'none';
    });

}
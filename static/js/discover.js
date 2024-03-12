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
});


function analyzePlaylist(playlistURL) {
    // Show loading indicator
    document.getElementById('loading-indicator').style.display = 'block';

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
        // Hide loading indicator
        document.getElementById('loading-indicator').style.display = 'none';
        displayAnalysisResults(data);
    })
    .catch((error) => {
        console.error('Error:', error);
        // Hide loading indicator
        document.getElementById('loading-indicator').style.display = 'none';
    });
}



function displayAnalysisResults(data) {
    // Assuming 'data' contains keys like 'top_songs', 'average_energy', etc.
    const resultsEl = document.querySelector('.playlist-analysis-results');
    let content = `<h3>Analysis Results</h3>`;

    // Display top 3 songs
    content += `<p>Top 3 Songs:</p><ul>`;
    data.top_songs.forEach(song => {
        content += `<li>${song.name} by ${song.artist}</li>`;
    });
    content += `</ul>`;

    // Display other metrics
    content += `<p>Average Danceability: ${data.average_danceability}</p>`;
    content += `<p>Average Energy: ${data.average_energy}</p>`;
    content += `<p>Most Prevalent Genres:</p><ul>`;
    data.most_prevalent_genres.forEach(genre => {
        content += `<li>${genre}</li>`;
    });
    content += `</ul>`;

    // Update the HTML
    resultsEl.innerHTML = content;
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
    content += '<div><h4>Most Common Genres:</h4><ul>';
    data.most_common_genres.slice(0, 3).forEach(([genre, _]) => {
        content += `<li>${genre}</li>`; // Removed the count next to each genre
    });
    content += '</ul></div>';

    resultsEl.innerHTML = content;
}



document.getElementById('playlist-analyzer-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const playlistURL = document.getElementById('playlist-url').value;
    analyzePlaylist(playlistURL);
});
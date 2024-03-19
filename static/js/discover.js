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
    const songDetailsEl = document.querySelector('.content .topsongww');

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
    const songDetailsEl = document.querySelector('.content .topsongww'); // Ensure this selector accurately targets the top song details section

    if (playlistAnalyzerEl.style.display === "flex") {
        playlistAnalyzerEl.style.display = "none";
        // If the playlist analyzer is hidden, and the friend queue is also hidden, then show the top song details
        if (friendQueueEl.style.display !== "block") {
            songDetailsEl.style.display = "block";
        }
    } else {
        playlistAnalyzerEl.style.display = "flex";
        friendQueueEl.style.display = "none"; // Hide the friend queue when showing the playlist analyzer
        songDetailsEl.style.display = "none"; // Hide the top song details when showing the playlist analyzer
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
        showPlaylistAnalyzerSection(); 
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
    // Clear the current analysis results first
    resultsEl.innerHTML = '';
    const titleEl = document.createElement('h2');
    titleEl.innerHTML = `Analysis of <em>${data.playlist_name}</em> by <em>${data.playlist_creator}</em>:`;
    resultsEl.prepend(titleEl);  // Add the title to the top of the results element

    // Display the playlist image
    const imgEl = document.createElement('img');
    imgEl.src = data.playlist_image_url;
    imgEl.alt = 'Playlist cover';
    imgEl.width = 200;  // Set the image size as required
    imgEl.height = 200;
    //resultsEl.prepend(imgEl);  // display the image but i dont think it looks that good 

    // Function to normalize loudness from -60 - 0 dB to 0 - 100
    const normalizeLoudness = (value) => ((value + 60) / 60) * 100;

    // Function to normalize tempo (assuming 200 as a typical max tempo)
    const normalizeTempo = (tempo, maxTempo = 200) => (tempo / maxTempo) * 100;

    // Function to create a bar for a feature
    const createBar = (feature, value) => {
        const percentage = feature === 'tempo' ? normalizeTempo(value) : feature === 'loudness' ? normalizeLoudness(value) : value * 100;
        const barFilledStyle = `width: ${Math.max(percentage, 0)}%;`; //minimum bar length
        const textInsideBar = percentage > 30; // Adjust this value as needed
    
        const text = `<span class="${textInsideBar ? 'inside-text' : 'outside-text'}">${feature.toUpperCase()}: ${value.toFixed(2)}</span>`;
        return `
            <div class="analysis-feature">
                <div class="progress" style="${barFilledStyle}">
                    ${textInsideBar ? text : ''}
                </div>
                ${!textInsideBar ? text : ''}
            </div>`;
    };

    // Average Features with Progress Bars
    let featuresContent = '<div><h4>Average Features:</h4>';
    Object.keys(data.average_features).forEach(feature => {
        featuresContent += createBar(feature, data.average_features[feature], ['instrumentalness', 'speechiness'].includes(feature));
    });
    featuresContent += '</div>';
    resultsEl.innerHTML += featuresContent;

    // Most Common Genres
    let genresContent = '<div><h4>Genres:</h4><ul class="genre-list">';
    data.most_common_genres.slice(0, 3).forEach(([genre, _]) => {
        genresContent += `<li>${genre}</li>`;
    });
    genresContent += '</ul></div>';
    resultsEl.innerHTML += genresContent;

    // Recommended Songs
    if (data.recommended_songs && data.recommended_songs.length > 0) {
        let recommendedSongsContent = `<div id="recommended-songs-section">
                        <h3>Recommendations for you from this playlist</h3>
                        <table id="recommended-songs-table">
                            <thead>
                                <tr>
                                    <th>Album Cover</th>
                                    <th>Title</th>
                                    <th>Artist(s)</th>
                                </tr>
                            </thead>
                            <tbody>`;

        data.recommended_songs.forEach(song => {
            recommendedSongsContent += `<tr>
                            <td><img src="${song.album_cover}" alt="Album cover" style="width: 50px; height: 50px;"></td>
                            <td>${song.title}</td>
                            <td>${song.artists}</td>
                        </tr>`;
        });

        recommendedSongsContent += `       </tbody>
                        </table>
                    </div>`; // Close the Recommended Songs section div
        resultsEl.innerHTML += recommendedSongsContent;
    }
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
    const songDetailsEl = document.querySelector('.content .topsongww'); // Selector for the top song section

    // Ensure the Playlist Analyzer is shown
    playlistAnalyzerEl.style.display = 'block';

    // Ensure the top song section is hidden
    songDetailsEl.style.display = 'none';
}

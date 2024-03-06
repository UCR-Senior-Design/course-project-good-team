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
    const songDetailsEl = document.querySelector('.content .song-details');

    // Toggle visibility based on the friendQueueEl's current display state
    if (friendQueueEl.style.display === "block") {
        friendQueueEl.style.display = "none";
        songDetailsEl.style.display = "block";
    } else {
        // Load and display the friend queue only when showing it
        loadFriendQueue();
        friendQueueEl.style.display = "block";
        songDetailsEl.style.display = "none";
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
});
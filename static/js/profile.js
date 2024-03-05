function showPlaylists() {
    var grid = document.getElementById("playlistsGrid");
    var mainContent = document.getElementById("main-profile-content"); // Get the main content container
    if (grid.style.display === "none") {
        grid.style.display = "block"; // Show the playlists grid
        mainContent.style.display = "none"; // Hide the main content
    } else {
        grid.style.display = "none"; // Hide the playlists grid
        mainContent.style.display = "block"; // Show the main content
    }
}

function openNav() {
    document.getElementById("side").style.width = "250px";
    document.getElementById("openbtn").classList.add("hidden")

}

function closeNav() {
    document.getElementById("side").style.width = "0px";
    document.getElementById("openbtn").classList.remove("hidden")
}
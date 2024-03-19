function openNav() {
    document.getElementById("side").style.width = "250px";
    document.getElementById("openbtn").classList.add("hidden")

}

function closeNav() {
    document.getElementById("side").style.width = "0px";
    document.getElementById("openbtn").classList.remove("hidden")
}


function toggleSection(sectionId) { // Function to show and hide whatever section you click on 
    var section = document.getElementById(sectionId);
    var mainContent = document.getElementById("main-profile-content"); 
    var otherSections = ["playlistsGrid", "mutualFavoritesContainer", "matchScoreContainer"]; 

    // Hide all sections except the one you are toggling
    otherSections.forEach(function(id) {
        if (id !== sectionId) {
            document.getElementById(id).style.display = "none";
        }
    });

    // toggle selected section and adjust visibility of main content
    if (section.style.display === "none" || section.style.display === "") {
        section.style.display = "block"; 
        mainContent.style.display = "none"; 
    } else {
        section.style.display = "none"; 
        mainContent.style.display = "block"; 
    }

    if (section === document.getElementById("mutualFavoritesContainer")) {
            section.style.display = "flex";
            mainContent.style.display = "none";
    }
}

function setMatchScoreMessage(score) {
    var message = "";
    score = parseInt(score); // Convert score to an integer
    if (score >= 90) message = "Wow, a perfect match!";
    else if (score >= 80) message = "You two are incredibly in tune with each other!";
    else if (score >= 70) message = "Quite a harmonious match!";
    else if (score >= 60) message = "You share some solid common ground!";
    else if (score >= 50) message = "There's potential for a musical connection.";
    else if (score >= 40) message = "You have a few hits in common.";
    else if (score >= 30) message = "A bit of a mixed tape, but it's a start.";
    else if (score >= 20) message = "Finding common ground might be a challenge.";
    else if (score >= 10) message = "Your musical worlds are quite apart.";
    else message = "You guys don't have much in common at all.";

    document.getElementById("matchScoreMessage").innerText = message;
}

function confirmAndAnalyzePlaylist(playlistId, playlistName) {
    const userConfirmation = confirm(`Do you want to analyze the playlist "${playlistName}"?`);
    if (userConfirmation) {
        // Redirect to the Playlist Analyzer with the playlist ID
        window.location.href = `/discover?analyze_playlist=${playlistId}`;
    }
}
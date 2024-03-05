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
    var otherSections = ["playlistsGrid", "mutualFavoritesContainer"]; 

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
}
function openNav() {
    document.getElementById("side").style.width = "250px";
    document.getElementById("openbtn").classList.add("hidden")

}

function closeNav() {
    document.getElementById("side").style.width = "0px";
    document.getElementById("openbtn").classList.remove("hidden")
}
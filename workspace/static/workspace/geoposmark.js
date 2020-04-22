function getLocation() {
    if (navigator.geolocation)
    { navigator.geolocation.getCurrentPosition(processPosition, showError); }
    else
    { err.innerHTML = "Geolocation is not supported by this browser."; }
}

function processPosition(position) {
    document.getElementById('id_lon').value = position.coords.longitude;
    document.getElementById('id_lat').value = position.coords.latitude;
    document.getElementById("f_err").innerHTML = "Latitude: " + position.coords.latitude + " Longitude: " + position.coords.longitude;
}

function showError(error) {
    x = document.getElementById("f_err")
    switch(error.code) {
        case error.PERMISSION_DENIED:
            x.innerHTML = "User denied the request for Geolocation."
            break;
        case error.POSITION_UNAVAILABLE:
            x.innerHTML = "Location information is unavailable."
            break;
        case error.TIMEOUT:
            x.innerHTML = "The request to get user location timed out."
            break;
        case error.UNKNOWN_ERROR:
            x.innerHTML = "An unknown error occurred."
            break;
    }
}
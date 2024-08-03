// var pathdata = document.getElementById('pathdata');

function clearSignature() {
    var svg = document.getElementsByTagName('iframe')[0].contentWindow;
    svg.clearSignature();
    document.getElementById('pathdata').value = null;
}

function showSignature() {
    getLocation();

    var svg = document.getElementsByTagName('iframe')[0].contentWindow;

    //pathdata.textContent = svg.getSignature();
    document.getElementById('pathdata').value = svg.getSignature();

    if (document.getElementById('event_category').value == ''
            || document.getElementById('event_name').value == ''
            || document.getElementById('event_date').value == ''
            || document.getElementById('hours_worked').value == ''
        ) {
        
        alert('All required fields must be filled');
        return false;
    }

    setTimeout(function(){
        document.getElementById('logForm').submit();
    }, 1000);
}

function getLocation() {
    const successCallback = (position) => {
        console.log(position);
    };

    const errorCallback = (error) => {
        console.log(error);
    };

    // Check if geolocation is supported by the browser
    if ("geolocation" in navigator) {
        // Prompt user for permission to access their location
        navigator.geolocation.getCurrentPosition(
        // Success callback function
        (position) => {
            // Get the user's latitude and longitude coordinates
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const accuracy = position.coords.accuracy;

            // Do something with the location data, e.g. display on a map
            // console.log(`Latitude: ${lat}, longitude: ${lng}`);
            document.getElementById('coords').value = lat + ',' + lng;
            document.getElementById('coords_accuracy').value = accuracy;
        },
        // Error callback function
        (error) => {
            // Handle errors, e.g. user denied location sharing permissions
            console.error("Error getting user location:", error);
        },
        { enableHighAccuracy: true }
        );
    }
}
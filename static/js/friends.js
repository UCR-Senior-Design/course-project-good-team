function acceptFriendRequest(requesterUsername) {
    fetch('/acceptfriend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({ requesterUsername: requesterUsername })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload(); // Reload the page to update the list
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function declineFriendRequest(requesterUsername) {
    fetch('/declinefriend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({ requesterUsername: requesterUsername })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload(); // Reload the page to update the list
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function askForFriend() {
    var friendName = prompt("Enter friend's name:");
    
    if (friendName !== null) {
            fetch('/addfriend', {
                method: 'POST',
                headers: {
                'Content-Type': 'application/json',
                },
            body: JSON.stringify({ friendName: friendName }),
            })
            .then(response => response.json())
        .then(data => {
            alert(data.message);
            location.reload();
        })
        .catch(error => {
                console.error('Error:', error);
        });
    }
    }

    window.onload = function() {
        const usernameElement = document.getElementById('username'); // Get the element by ID
        const username = usernameElement.dataset.username; // Access the data-username attribute
    };
    

function confirmRemoveFriend(friendUsername) {
    if (confirm(`Are you sure you want to remove ${friendUsername} as a friend?`)) {
        // Perform the fetch request to remove the friend
        fetch('/removefriend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ friendUsername: friendUsername })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            location.reload(); // Reload the page to update the friends list
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

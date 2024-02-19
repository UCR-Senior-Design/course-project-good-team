from datetime import datetime

def update_user_document(users, userid, username, profile_pic_url, top_data, playlistsnameid, date_joined=None):
    existing_user = users.find_one({'id': userid})

    if existing_user:
        # For existing users, only update if there's new data; don't overwrite date_joined
        update_data = {
            'profile_pic_url': profile_pic_url,
            **top_data  # Unpack top data dictionary
        }
        users.update_one({'id': userid}, {'$set': update_data})
    else:
        # For new users, add date_joined
        if date_joined is None:
            date_joined = datetime.now().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
        new_user = {
            'id': userid,
            'username': username,
            'profile_pic_url': profile_pic_url,
            'date_joined': date_joined,
            'friends': [],
            'friendRequests': [],
            'playlists': playlistsnameid,
            **top_data
        }
        users.insert_one(new_user)

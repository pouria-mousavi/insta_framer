import instaloader
import pickle
import os
import sys
from config import INSTAGRAM_USERNAME

def force_session_create(username, session_id):
    print(f"Creating session for {username}...")
    
    # Standard Instaloader path
    session_file_path = os.path.expanduser(f"~/.config/instaloader/session-{username}")
    os.makedirs(os.path.dirname(session_file_path), exist_ok=True)
    
    # Create loader and set cookie
    L = instaloader.Instaloader()
    L.context._session.cookies.set('sessionid', session_id, domain='.instagram.com')
    
    # Make a request to populate other cookies (csrftoken, etc.)
    print("Making request to Instagram to populate cookies...")
    try:
        L.context._session.get('https://www.instagram.com/')
        print("Request successful.")
    except Exception as e:
        print(f"Warning: Request failed: {e}")

    # Convert jar to dict for safe pickling
    import requests.utils
    session_data = requests.utils.dict_from_cookiejar(L.context._session.cookies)
    
    # Ensure sessionid is there (in case it wasn't returned/updated, tough it should be there since we set it)
    if 'sessionid' not in session_data:
        session_data['sessionid'] = session_id

    # Save manually using pickle
    try:
        with open(session_file_path, 'wb') as f:
            pickle.dump(session_data, f)
        print(f"✅ Session file (with {len(session_data)} cookies) written to: {session_file_path}")



    except Exception as e:
        print(f"❌ Failed to write session file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python force_create_session.py <session_id>")
        sys.exit(1)
        
    session_id = sys.argv[1]
    force_session_create(INSTAGRAM_USERNAME, session_id)

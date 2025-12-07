import instaloader
import os
from config import INSTAGRAM_USERNAME

def create_session_from_cookie(username, session_id):
    L = instaloader.Instaloader()
    
    # Set the sessionid cookie
    L.context._session.cookies.set('sessionid', session_id, domain='.instagram.com')
    
    # Verify it works
    try:
        print(f"Testing session for {username}...")
        # Just getting the profile of the logged in user is a good check
        profile = instaloader.Profile.from_username(L.context, username)
        print(f"Success! Logged in as {profile.username} (ID: {profile.userid})")
        
        # Save to file
        filename = f"session-{username}"
        # Instaloader usually saves to ~/.config/instaloader/
        # But we want to ensure it saves where we can find it, or let it handle standard path
        # save_session_to_file() defaults to standard path
        L.save_session_to_file(filename=filename)
        print(f"Session saved to standard path: {filename}")
        
        # Also save to local directory for easier portability if needed? 
        # Instaloader.load_session_from_file looks in standard paths. 
        # Let's simple rely on it.
        
    except Exception as e:
        print(f"Error: The session ID seems invalid or expired. Instagram response: {e}")

if __name__ == "__main__":
    if not INSTAGRAM_USERNAME:
        print("Please set INSTAGRAM_USERNAME in your .env file first.")
        exit(1)
        
    print("Instagram password login is blocked. You need to use your browser's session cookie.")
    print("1. Open Instagram.com in your browser and ensure you are logged in.")
    print("2. Open Developer Tools (F12) -> Application -> Cookies -> https://www.instagram.com")
    print("3. Find the cookie named 'sessionid' and copy its Value.")
    
    session_id = input("\nPaste your 'sessionid' here: ").strip()
    
    if session_id:
        create_session_from_cookie(INSTAGRAM_USERNAME, session_id)
    else:
        print("No session ID provided.")

#!/usr/bin/env python3
"""
Spotify Authentication Helper
Run this to authenticate your Spotify account
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to find .env
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))
load_dotenv(parent_dir / '.env')

def authenticate_spotify():
    """Authenticate Spotify and save token"""
    
    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-library-read"
    
    # Get credentials from environment
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    if not all([client_id, client_secret, redirect_uri]):
        print("❌ Missing Spotify credentials in .env file!")
        print("Make sure you have set:")
        print("  - SPOTIFY_CLIENT_ID")
        print("  - SPOTIFY_CLIENT_SECRET")
        print("  - SPOTIFY_REDIRECT_URI")
        return False
    
    print(f"Client ID: {client_id[:10]}...")
    print(f"Redirect URI: {redirect_uri}")
    
    try:
        # Create auth manager
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache",
            open_browser=True  # This will open browser automatically
        )
        
        # Get token (this will open browser for auth)
        token = auth_manager.get_access_token(as_dict=False)
        
        if token:
            print("\n✅ Successfully authenticated with Spotify!")
            
            # Test the connection
            sp = spotipy.Spotify(auth_manager=auth_manager)
            user = sp.current_user()
            print(f"👤 Logged in as: {user['display_name']}")
            
            # Check devices
            devices = sp.devices()
            if devices['devices']:
                print(f"\n📱 Available devices:")
                for device in devices['devices']:
                    status = "🟢 Active" if device['is_active'] else "⚪ Inactive"
                    print(f"  - {device['name']} ({device['type']}) {status}")
            else:
                print("\n⚠️  No active Spotify devices found!")
                print("Please open Spotify on your computer or phone.")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Authentication failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎵 Spotify Authentication Setup")
    print("="*40)
    print("\nThis will open your browser to authenticate with Spotify.")
    print("After authorizing, you'll be redirected to a URL.")
    print("Even if you see an error page, the authentication should work.\n")
    
    input("Press Enter to continue...")
    
    if authenticate_spotify():
        print("\n✨ You're all set! You can now use Spotify commands.")
    else:
        print("\n❌ Authentication failed. Please check your credentials.")
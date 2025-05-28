#!/usr/bin/env python3
"""
Spotify Authentication Helper
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables with override
load_dotenv(override=True)

def main():
    print("🎵 Spotify Authentication Setup")
    print("="*40)
    
    # Check credentials
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    print(f"\nChecking credentials:")
    print(f"Client ID: {client_id[:10] if client_id else 'NOT FOUND'}...")
    print(f"Client Secret: {'*' * 10 if client_secret else 'NOT FOUND'}")
    print(f"Redirect URI: {redirect_uri if redirect_uri else 'NOT FOUND'}")
    
    if not all([client_id, client_secret, redirect_uri]):
        print("\n❌ Missing credentials!")
        return
    
    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-library-read"
    
    print("\n📌 This will open your browser for authentication.")
    print("After authorizing, you'll be redirected to a page that may show an error.")
    print("This is normal - the authentication will still work.\n")
    
    input("Press Enter to continue...")
    
    try:
        # Create auth manager
        sp_oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        # Get auth URL
        auth_url = sp_oauth.get_authorize_url()
        print(f"\n🌐 Opening browser to: {auth_url}")
        
        import webbrowser
        webbrowser.open(auth_url)
        
        print("\n⏳ After authorizing in your browser, you'll be redirected.")
        print("Copy the ENTIRE URL from your browser's address bar and paste it here.")
        print("(Even if the page shows an error)")
        
        response = input("\nPaste the full redirect URL here: ").strip()
        
        # Extract code from response
        code = sp_oauth.parse_response_code(response)
        if code:
            # Get token
            token_info = sp_oauth.get_access_token(code)
            
            if token_info:
                print("\n✅ Successfully authenticated!")
                
                # Test connection
                sp = spotipy.Spotify(auth=token_info['access_token'])
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
                    print("\n⚠️  No active devices found! Please open Spotify.")
                
                print("\n✨ Authentication complete! You can now use Spotify commands.")
            else:
                print("\n❌ Failed to get access token")
        else:
            print("\n❌ No authorization code found in URL")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()

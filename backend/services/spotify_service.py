import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from typing import Dict, Any, Optional, List
import os
import json
from dotenv import load_dotenv

# Load environment variables with override
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class SpotifyService:
    def __init__(self):
        self.scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-library-read"
        
        # Initialize Spotify client
        self.sp = None
        self.device_id = None
        self._initialize_spotify()
    
    def _initialize_spotify(self):
        """Initialize Spotify client with OAuth"""
        try:
            # Import Config here to ensure env vars are loaded
            from backend.config import Config
            
            # Make sure we have credentials
            if not all([Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET, Config.SPOTIFY_REDIRECT_URI]):
                logger.error("Missing Spotify credentials")
                logger.error(f"Client ID: {'Set' if Config.SPOTIFY_CLIENT_ID else 'Missing'}")
                logger.error(f"Client Secret: {'Set' if Config.SPOTIFY_CLIENT_SECRET else 'Missing'}")
                logger.error(f"Redirect URI: {Config.SPOTIFY_REDIRECT_URI or 'Missing'}")
                return
            
            # Cache path for token
            cache_path = ".spotify_cache"
            
            # Check if cache file exists
            if not os.path.exists(cache_path):
                logger.error(f"No Spotify cache file found at {cache_path}. Please run auth_spotify_fixed.py first")
                return
            
            auth_manager = SpotifyOAuth(
                client_id=Config.SPOTIFY_CLIENT_ID,
                client_secret=Config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=Config.SPOTIFY_REDIRECT_URI,
                scope=self.scope,
                cache_path=cache_path,
                open_browser=False  # We'll handle this manually
            )
            
            # Check if we have a cached token
            token_info = auth_manager.get_cached_token()
            
            if not token_info:
                logger.error("No cached Spotify token found. Please run auth_spotify_fixed.py first")
                return
            
            # Check if token is expired and refresh if needed
            if auth_manager.is_token_expired(token_info):
                logger.info("Token expired, refreshing...")
                token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Spotify service initialized successfully")
            
            # Test connection
            try:
                user = self.sp.current_user()
                logger.info(f"Connected as: {user['display_name']}")
            except Exception as e:
                logger.error(f"Failed to get current user: {str(e)}")
                self.sp = None
                return
            
            # Get available devices
            self._get_device()
            
        except Exception as e:
            logger.error(f"Failed to initialize Spotify: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.sp = None
    
    def _get_device(self):
        """Get the active device or first available device"""
        try:
            devices = self.sp.devices()
            if devices['devices']:
                # Try to find active device
                active_device = next((d for d in devices['devices'] if d['is_active']), None)
                if active_device:
                    self.device_id = active_device['id']
                    logger.info(f"Using active device: {active_device['name']}")
                else:
                    # Use first available device
                    self.device_id = devices['devices'][0]['id']
                    logger.info(f"Using device: {devices['devices'][0]['name']}")
            else:
                logger.warning("No Spotify devices found. Please open Spotify on a device.")
                self.device_id = None
        except Exception as e:
            logger.error(f"Error getting devices: {str(e)}")
    
    def search_and_play(self, query: str, search_type: str = "track") -> Dict[str, Any]:
        """Search for content and play it"""
        if not self.sp:
            return {"status": "error", "message": "Spotify not initialized. Please run auth_spotify_fixed.py"}
        
        try:
            # Ensure we have a device
            if not self.device_id:
                self._get_device()
                if not self.device_id:
                    return {"status": "error", "message": "No Spotify device available. Please open Spotify."}
            
            # Map search type to Spotify types
            type_mapping = {
                "track": "track",
                "artist": "artist",
                "playlist": "playlist",
                "album": "album"
            }
            
            spotify_type = type_mapping.get(search_type, "track")
            
            # Search
            logger.info(f"Searching for {spotify_type}: {query}")
            results = self.sp.search(q=query, type=spotify_type, limit=10)
            
            if spotify_type == "track" and results['tracks']['items']:
                # Play the first track
                track = results['tracks']['items'][0]
                self.sp.start_playback(device_id=self.device_id, uris=[track['uri']])
                return {
                    "status": "success",
                    "message": f"Playing: {track['name']} by {track['artists'][0]['name']}",
                    "track": track['name'],
                    "artist": track['artists'][0]['name']
                }
                
            elif spotify_type == "artist" and results['artists']['items']:
                # Play top tracks from artist
                artist = results['artists']['items'][0]
                top_tracks = self.sp.artist_top_tracks(artist['id'])
                if top_tracks['tracks']:
                    track_uris = [track['uri'] for track in top_tracks['tracks'][:10]]
                    self.sp.start_playback(device_id=self.device_id, uris=track_uris)
                    return {
                        "status": "success",
                        "message": f"Playing top tracks by {artist['name']}",
                        "artist": artist['name']
                    }
                    
            elif spotify_type == "playlist" and results['playlists']['items']:
                # Play the first matching playlist
                playlist = results['playlists']['items'][0]
                self.sp.start_playback(device_id=self.device_id, context_uri=playlist['uri'])
                return {
                    "status": "success",
                    "message": f"Playing playlist: {playlist['name']}",
                    "playlist": playlist['name']
                }
                
            elif spotify_type == "album" and results['albums']['items']:
                # Play the album
                album = results['albums']['items'][0]
                self.sp.start_playback(device_id=self.device_id, context_uri=album['uri'])
                return {
                    "status": "success",
                    "message": f"Playing album: {album['name']} by {album['artists'][0]['name']}",
                    "album": album['name'],
                    "artist": album['artists'][0]['name']
                }
            
            return {"status": "error", "message": f"No {search_type} found for '{query}'"}
            
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 404:
                return {"status": "error", "message": "Device not found. Please open Spotify and start playing something first."}
            elif e.http_status == 403:
                return {"status": "error", "message": "Premium account required for playback control."}
            else:
                logger.error(f"Spotify API error: {str(e)}")
                return {"status": "error", "message": f"Spotify error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error in search_and_play: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def control_playback(self, action: str) -> Dict[str, Any]:
        """Control playback (play, pause, skip, previous)"""
        if not self.sp:
            return {"status": "error", "message": "Spotify not initialized. Please run auth_spotify_fixed.py"}
        
        try:
            if action == "play":
                self.sp.start_playback(device_id=self.device_id)
                return {"status": "success", "message": "Playback resumed"}
                
            elif action == "pause":
                self.sp.pause_playback(device_id=self.device_id)
                return {"status": "success", "message": "Playback paused"}
                
            elif action == "skip" or action == "next":
                self.sp.next_track(device_id=self.device_id)
                return {"status": "success", "message": "Skipped to next track"}
                
            elif action == "previous":
                self.sp.previous_track(device_id=self.device_id)
                return {"status": "success", "message": "Playing previous track"}
                
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 404:
                return {"status": "error", "message": "No active device found. Please open Spotify."}
            elif e.http_status == 403:
                return {"status": "error", "message": "Premium account required for playback control."}
            else:
                return {"status": "error", "message": f"Spotify error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error controlling playback: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_current_track(self) -> Dict[str, Any]:
        """Get currently playing track"""
        if not self.sp:
            return {"status": "error", "message": "Spotify not initialized. Please run auth_spotify_fixed.py"}
        
        try:
            current = self.sp.current_playback()
            if current and current['item']:
                track = current['item']
                return {
                    "status": "success",
                    "is_playing": current['is_playing'],
                    "track": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "progress": current['progress_ms'],
                    "duration": track['duration_ms']
                }
            else:
                return {"status": "success", "message": "No track currently playing"}
                
        except Exception as e:
            logger.error(f"Error getting current track: {str(e)}")
            return {"status": "error", "message": str(e)}

# Singleton instance
_spotify_service = None

def get_spotify_service() -> SpotifyService:
    """Get or create Spotify service instance"""
    global _spotify_service
    if _spotify_service is None:
        _spotify_service = SpotifyService()
    return _spotify_service
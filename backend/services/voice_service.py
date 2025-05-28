import speech_recognition as sr
import pyttsx3
import pygame
from gtts import gTTS
import io
import os
import tempfile
import logging
import threading
import queue
from typing import Optional, Callable
import time

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech
        self.tts_engine = None
        self.use_gtts = True  # Use Google TTS by default
        self._init_tts()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Adjust for ambient noise on startup
        self._calibrate_microphone()
        
        # For continuous listening
        self.listening = False
        self.audio_queue = queue.Queue()
        
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            # Try to use pyttsx3 for offline TTS
            self.tts_engine = pyttsx3.init()
            # Set properties
            self.tts_engine.setProperty('rate', 175)  # Speed of speech
            voices = self.tts_engine.getProperty('voices')
            # Try to use a female voice if available
            if len(voices) > 1:
                self.tts_engine.setProperty('voice', voices[1].id)
            self.use_gtts = False
            logger.info("Using offline TTS (pyttsx3)")
        except Exception as e:
            logger.warning(f"pyttsx3 initialization failed: {e}")
            logger.info("Will use Google TTS (requires internet)")
            self.use_gtts = True
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                logger.info("Microphone calibrated")
        except Exception as e:
            logger.error(f"Error calibrating microphone: {e}")
    
    def listen_once(self, timeout: Optional[int] = None) -> Optional[str]:
        """Listen for a single voice command"""
        try:
            with self.microphone as source:
                logger.info("Listening...")
                
                # Listen for audio with optional timeout
                if timeout:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                else:
                    audio = self.recognizer.listen(source, phrase_time_limit=10)
                
                logger.info("Processing speech...")
                
                # Try multiple recognition methods
                try:
                    # Try Google Speech Recognition first (requires internet)
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Recognized: {text}")
                    return text
                except sr.RequestError:
                    logger.error("Google Speech Recognition unavailable")
                    # Try offline recognition with Sphinx
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                        logger.info(f"Recognized (offline): {text}")
                        return text
                    except:
                        pass
                except sr.UnknownValueError:
                    logger.warning("Could not understand audio")
                    
        except sr.WaitTimeoutError:
            logger.debug("Listening timeout")
        except Exception as e:
            logger.error(f"Error in listen_once: {e}")
        
        return None
    
    def speak(self, text: str, wait: bool = True):
        """Convert text to speech and play it"""
        try:
            if self.use_gtts:
                # Use Google TTS
                self._speak_gtts(text, wait)
            else:
                # Use pyttsx3
                self._speak_pyttsx3(text, wait)
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            print(f"Assistant: {text}")  # Fallback to text output
    
    def _speak_gtts(self, text: str, wait: bool):
        """Speak using Google TTS"""
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file_path = tmp_file.name
                tts.save(tmp_file_path)
            
            # Play the audio file
            pygame.mixer.music.load(tmp_file_path)
            pygame.mixer.music.play()
            
            if wait:
                # Wait for the audio to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            
            # Clean up
            pygame.mixer.music.unload()
            os.unlink(tmp_file_path)
            
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            # Fallback to pyttsx3 if available
            if self.tts_engine:
                self._speak_pyttsx3(text, wait)
    
    def _speak_pyttsx3(self, text: str, wait: bool):
        """Speak using pyttsx3"""
        try:
            if wait:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                # Non-blocking speech
                def speak_async():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                thread = threading.Thread(target=speak_async)
                thread.daemon = True
                thread.start()
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
    
    def start_continuous_listening(self, callback: Callable[[str], None]):
        """Start continuous listening in background"""
        self.listening = True
        
        def listen_loop():
            while self.listening:
                text = self.listen_once(timeout=1)
                if text:
                    callback(text)
        
        thread = threading.Thread(target=listen_loop)
        thread.daemon = True
        thread.start()
        logger.info("Started continuous listening")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        self.listening = False
        logger.info("Stopped continuous listening")
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        try:
            with self.microphone as source:
                # Try to get some audio
                self.recognizer.listen(source, timeout=0.5)
            logger.info("Microphone test passed")
            return True
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False
    
    def test_speakers(self):
        """Test if speakers are working"""
        self.speak("Testing speakers. Hello, I am your AI assistant.", wait=True)

# Singleton instance
_voice_service = None

def get_voice_service() -> VoiceService:
    """Get or create voice service instance"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
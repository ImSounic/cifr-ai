import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
    
    # Model settings - Using latest Llama 3.3
    MODEL_NAME = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.3
    MAX_TOKENS = 1024
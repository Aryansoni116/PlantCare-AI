import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Folder configurations
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_AUDIO_FOLDER = os.path.join(BASE_DIR, "output_audio")
MODEL_DIR = os.path.join(BASE_DIR, "model")

# File upload restrictions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit

# API Keys — loaded from .env file
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")
GOOGLE_TTS_API_KEY = os.getenv("GOOGLE_TTS_API_KEY", "")

# Warn on startup if Grok key is missing
if not GROK_API_KEY:
    print("⚠️  WARNING: GROK_API_KEY is not set in .env file. Explanation features will use mock data.")

# App settings
DEBUG = os.getenv("DEBUG", "True") == "True"
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# Maintenance Mode
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "False").lower() in ("true", "1", "yes")
MAINTENANCE_TIME = os.getenv("MAINTENANCE_TIME", "some time")

# Model paths
MODEL_PATH = os.path.join(MODEL_DIR, "plant_disease_resnet18.pth")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "class_names.json")

# PyTorch Image Preprocessing Configuration
IMAGE_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_AUDIO_FOLDER, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

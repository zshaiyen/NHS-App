Required environment variables (can be loaded from .env in the project root folder) 

# Project root directory
PROJECT_ROOT="/my/project/root"

# List of allowed domains that can log in to the app
ALLOWED_DOMAINS=["allowed_domain1.com", "allowed_domain2.com"]

# Allowed extensions for file upload
ALLOWED_EXTENSIONS={'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif'}

# Path to temp download folder for generated Excel files
DOWNLOAD_FOLDER="${PROJECT_ROOT}/data/download"

# Path to directory where uploaded files are saved
UPLOAD_FOLDER="${PROJECT_ROOT}/data/sigs"

# Maximum file upload size in MB
MAX_CONTENT_LENGTH=10

# Path to sqlite3 database file
APP_DATABASE="${PROJECT_ROOT}/data/nhsapp.db"

# Flask secret key
SECRET_KEY="XXX"

# Google authentication
GOOGLE_AUTHORIZATION_BASE_URL="https://accounts.google.com/o/oauth2/auth"
GOOGLE_CLIENT_ID="XXXX.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="XXXX"
GOOGLE_REDIRECT_URI="http://yourdomain.com/oauth2callback"
GOOGLE_TOKEN_URL="https://accounts.google.com/o/oauth2/token"
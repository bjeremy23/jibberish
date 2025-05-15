# Import version information for easy access
from app.version import __version__, VERSION_NAME

# Core modules that should be available when importing the package
from app import chat
from app import executor
from app import api
from app import jibberish

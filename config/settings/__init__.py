from .base import *

# Use development settings by default
try:
    from .development import *
except ImportError:
    pass
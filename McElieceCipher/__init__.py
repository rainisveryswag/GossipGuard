# McElieceCipher/__init__.py
from .mceliece import McEliece  # Expose main class at package level

__version__ = "1.0.0"
__all__ = ['McEliece']  # Controls what gets imported with `from McElieceCipher import *`
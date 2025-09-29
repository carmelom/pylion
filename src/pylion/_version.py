from importlib.metadata import PackageNotFoundError, version  # py≥3.8

try:
    __version__ = version(__name__.split(".")[0])  # top-level pkg name
except PackageNotFoundError:  # not installed (e.g., running from source)
    __version__ = "0+unknown"

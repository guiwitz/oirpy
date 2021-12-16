try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from .napari_oir_reader import napari_get_reader
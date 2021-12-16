# Python reader for Olympus OIR format

This is a very basic reader for the Olympus OIR format. At the moment it is capable of reading multi-channel single-time point, single-plane images and has not been widely tested.

## Installation

Install this package directly from GitHub using:
```
pip install --upgrade git+https://github.com/guiwitz/oirpy.git@master#egg=oirpy
```

## napari reader plugin

If you have [napari](https://napari.org/) installed in your environment, you will automatically be able to load oir files into it, e.g. by drag and dropping files into the window.
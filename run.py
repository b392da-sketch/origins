"""Start the Origins observatory: python run.py  (then open http://127.0.0.1:8770)."""
import sys

if sys.version_info < (3, 10):
    sys.exit("Origins needs Python 3.10 or newer.")
try:
    import numpy  # noqa: F401
except ImportError:
    sys.exit("Origins needs NumPy. Install it with:  python -m pip install numpy")

from origins.server import main

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    main(port)

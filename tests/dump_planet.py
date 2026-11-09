"""Save planet 1's arrays (for comparing machines in the planets workflow)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from origins.worldgen import generate  # noqa: E402
from tests.test_planet_identity import FIELDS  # noqa: E402

import origins.worldgen as W  # noqa: E402
W.DEBUG = {}
p = generate(1)
out = {k: getattr(p, k) for k in FIELDS}
out.update({"dbg_" + k: v for k, v in W.DEBUG.items()})
np.savez("planet1.npz", **out)

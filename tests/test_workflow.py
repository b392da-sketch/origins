"""The gate workflow's stages hand their checkpoints on in order (G4a pilot 3, 27 November 2026: stage 6 asked for
its own checkpoint's name instead of stage 5's, so every history stopped at stage 5)."""
import re
import unittest
from pathlib import Path

WF = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "gate.yml"


class CheckpointChain(unittest.TestCase):
    def test_each_stage_starts_from_the_checkpoint_the_stage_before_saved(self):
        text = WF.read_text()
        jobs = re.split(r"\n  (?=[a-z0-9]+:\n)", text)
        chain = []
        for j in jobs:
            m = re.search(r"\n    name: (stage\d+|run|more-run|last-run)-", j) or re.search(r"\n    name: ([a-z-]+)-\$", j)
            down = re.findall(r"download-artifact@v4[^\n]*\n(?:.*\n){0,4}?\s+name: (ckpt\d*)-", j)
            up = re.findall(r"upload-artifact@v4[^\n]*\n(?:.*\n){0,6}?\s+name: (ckpt\d*)-", j)
            if up or down:
                chain.append((down[0] if down else None, up[0] if up else None))
        self.assertGreaterEqual(len(chain), 10)
        for (_, prev_up), (down, _) in zip(chain, chain[1:]):
            self.assertEqual(down, prev_up)
        names = [u for _, u in chain]
        self.assertEqual(len(set(names)), len(names))       # each stage saves under its own name


if __name__ == "__main__":
    unittest.main()

"""The compact event record changes nothing: a history with events frozen early is identical to one without."""
import unittest

from origins import engine, persist
from origins.state import EventStore, World
from origins.worldgen import generate


class EventStoreChangesNothing(unittest.TestCase):
    def test_same_history(self):
        pl = generate(1)
        digests, saved = [], []
        for hot, batch in ((10**9, 10**9), (20, 40)):
            EventStore.HOT, EventStore.BATCH = hot, batch
            try:
                w = World.new(1, 1, pl)
                engine.step(w, 4 * 1500)
                digests.append(persist.digest(w))
                saved.append([e for e in w.events])
                if hot == 20:
                    self.assertGreater(len(w.events._cold), 0)
                    w2 = persist.from_bytes(persist.to_bytes(w), pl)
                    self.assertEqual(persist.digest(w2), digests[-1])
            finally:
                EventStore.HOT, EventStore.BATCH = 20_000, 50_000
        self.assertEqual(digests[0], digests[1])
        import json
        self.assertEqual(json.dumps(saved[0]), json.dumps(saved[1]))


if __name__ == "__main__":
    unittest.main()

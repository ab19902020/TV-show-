"""Basic source-level tests for ChatGPT's White Pele insert module; no render engine needed."""
import importlib.util
from pathlib import Path
import unittest

MOD = Path(__file__).resolve().parents[1] / "film" / "upgrade.py"
spec = importlib.util.spec_from_file_location("director_upgrade_tested", MOD)
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)

def actor(who):
    return {"who": who, "feet": (800, 600), "h": 320, "draw": who + ":stand"}

def shot(t, plate, cams=(), layers=(), **kw):
    return dict(t=t, plate=plate, cams=list(cams), layers=list(layers), **kw)

class UpgradeTest(unittest.TestCase):
    def test_insert_and_resume(self):
        band = [actor(w) for w in ("maguire", "sesko", "cunha")]
        goldbridge = actor("mark")
        shots = [shot(0, "B01"), shot(13.7, "B02"), shot(15.2, "B02"),
                 shot(16.7, "B01"), shot(76.0, "B08"), shot(89.5, "B08", lights=1.35, beams=1.5),
                 shot(117.3, "B08", lights=1.35, beams=1.5), shot(120.3, "B09"),
                 shot(145.0, "B08", layers=[("actors", [goldbridge])], lights=1.55, beams=1.7),
                 shot(158.4, "B08", lights=1.55, beams=1.7), shot(163.0, "B09")]
        layer = lambda blur: [("actors", [dict(a) for a in band])]
        ns = dict(SH=shots, S_=shot, move=lambda t, z, a, b: [(t, a), (z, b)],
                  frame=lambda f, h, size, dy=0: (f[0], f[1] - h / 2, 2.0),
                  pub2=layer, st8=layer, BAND2=band, BAND8=band,
                  b=lambda n: 145.0 if n == 98 else 1.48 * n,
                  VERSE=dict(lights=1.0, beams=1.0, flash=0.8),
                  CHORUS=dict(lights=1.35, beams=1.5, flash=1.3))
        self.assertEqual(upgrade.apply(ns), 5)
        self.assertEqual(len(shots), 21)
        self.assertEqual(sum("band_insert" in s for s in shots), 5)
        self.assertEqual(len(goldbridge["keys"]), 3)
        self.assertEqual([s["t"] for s in shots], sorted(s["t"] for s in shots))

if __name__ == "__main__":
    unittest.main()

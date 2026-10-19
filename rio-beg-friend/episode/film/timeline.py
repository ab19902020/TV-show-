"""The dialogue edit: Rio's lines at his own pace, with a beat for the tray to arrive and a hold at the end."""
import json

from studio.film import ep
from studio.film.timeline import build

L = json.loads(ep.path("lines.json").read_text())
SEQ = [("gap", 0.5, "open"), ("line", "L001"), ("gap", 0.35), ("line", "L002"), ("gap", 0.4), ("line", "L003"),
       ("gap", 0.4), ("line", "L004"), ("gap", 0.6), ("line", "L005"), ("gap", 0.5), ("line", "L006"),
       ("gap", 0.45), ("line", "L007"), ("gap", 0.3), ("line", "L008"), ("gap", 0.3, "outro"), ("gap", 2.6, "end_card")]
TL = build(SEQ, L)

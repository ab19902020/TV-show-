"""The dialogue edit: a YouTube beef. Saeed live on his channel, Rio's video reply from his podcast studio, Saeed
reacting live with Rio's clip playing in the corner of his stream, then the two of them side by side for the
last line and the long awkward silence after it."""
import json

from studio.film import ep
from studio.film.timeline import build

L = json.loads(ep.path("lines.json").read_text())

SEQ = [
    ("gap", 0.70, "open"),                 # the stream goes LIVE: Saeed leans into his webcam
    ("line", "L001"),
    ("gap", 0.18),
    ("line", "L002"),                      # "...quieter than Old Trafford when we're two nil down."
    ("gap", 1.70, "cut_ot"),               # Old Trafford, 2-0 down: silence, a cough, a tumbleweed
    ("gap", 0.80, "cut_reply"),            # REPLY FROM RIO FERDINAND: his podcast studio
    ("line", "L003"),                      # "Saeed mate... have you looked in a mirror?"
    ("gap", 0.45, "cut_pip1"),             # Saeed's stream, Rio's clip in the corner: Saeed looks in a mirror
    ("line", "L004"),                      # "You're carrying a bit of timber." Saeed looks down at his belly
    ("gap", 0.20, "cut_rio2"),
    ("line", "L005"),                      # "You've got tits for God's sake."
    ("gap", 0.70, "rio_laugh"),            # Rio cracks up at his own joke
    ("gap", 0.10, "cut_tits"),
    ("line", "L006"),                      # "TITS!"
    ("gap", 0.25, "cut_smug"),
    ("line", "L007"),                      # "Brilliant Rio, at least mine are visible."
    ("gap", 0.45, "cut_ouch"),             # Rio, stung
    ("gap", 0.20, "cut_rant"),
    ("line", "L008"),
    ("gap", 0.15, "cut_police"),
    ("line", "L009"),                      # "...not the bloody fashion police." (sirens)
    ("gap", 0.40, "cut_fat"),
    ("line", "L010"),
    ("gap", 0.12),
    ("line", "L011"),                      # "...eat my feelings." The plates pile up
    ("gap", 0.90, "cut_rio3"),
    ("line", "L012"),                      # "That's not my fault."
    ("gap", 0.35, "cut_deadpan"),
    ("line", "L013"),                      # "Neither are the Glazers."
    ("gap", 0.45, "cut_split"),
    ("line", "L014"),                      # side by side: "Funny how we're both avoiding responsibility, eh, Rio?"
    ("gap", 2.40, "silence"),              # nobody says anything. For too long
    ("gap", 3.20, "cut_end"),              # end card
]

TL = build(SEQ, L)

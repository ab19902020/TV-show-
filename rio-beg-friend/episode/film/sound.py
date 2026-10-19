"""Rio's clip, a quiet office, cup and saucer foley, and a soft lovestruck string pad under the shoulder rubs."""
import json

import numpy as np

from studio.film import audio as A
from studio.film import ep
from studio.film.shots import Marks
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt


def main():
    dlg, amb, fx, mus = A.Bus(), A.Bus(), A.Bus(), A.Bus()
    A.dialogue(dlg, room_s=0.2, room_db=-28)
    A.bed(amb, "ambience/room-tone-hvac", 0.0, TL["total"], -50, lowpass=3000)
    A.steps(fx, 0.0, 1.6, -34, pace=0.42)
    A.ev(fx, "foley/cup-down", le("L002") - 0.4, -26)
    for a, b in ((ls("L003"), le("L003") + 0.5), (ls("L006"), le("L006") + 0.4), (wt("L008", "and"), TL["total"])):
        y = A.strings([262, 330, 392, 523], b - a, attack=0.6, release=0.8, bright=1800)
        mus.add(A.at_level(np.stack([y, y], 1), -30), a)
    y = A.title_sting(2.6, chord=("C3", "E3", "G3", "C4", "E4"))
    mus.add(A.at_level(y, -22), m("end_card"))
    A.master(dlg, [amb, fx], [mus])

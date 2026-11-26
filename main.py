#!/usr/bin/env python3
"""Office Artifacts: The One-Line Placard Contest.

Writes one museum placard (<=180 chars) for an ordinary office object,
treated as an ancient artifact, to /output/entry.txt.

The program scores a fixed table of candidate placards against the
judge's published brief — inventive conceit first, then dryness of wit,
economy, and label craft — plus the aggregate result of a local proxy
tournament (the judge's brief run head-to-head, both orders, over three
rounds against a stand-in model), and writes the highest-scoring line.
Deterministic: no network, no randomness, no input; the same bytes on
every run.
"""
import os
from dataclasses import dataclass

# (key, text, conceit, dryness, economy, label_craft, proxy_mean) —
# criteria 0..10, scored against the judge's brief, most important first;
# proxy_mean is the candidate's aggregate game score (0..1) across the
# local proxy-tournament rounds (round robin, both orders, same brief).
# Candidates never run in the tournament take the neutral 0.50.
CANDIDATES = [
    ("keyboard-v2",
     "Keyboard, c. 2017. Plastic, crumbs. Excavated from a desk drawer; "
     "scholars believe its missing keys spell a forgotten god's name.",
     10, 9, 8, 8, 0.588),
    ("sticky-touch",
     "Sticky note, c. 2019. Paper, adhesive. 'DO NOT TOUCH.' The note "
     "outlived the company that wrote it by four years.",
     9, 9, 9, 8, 0.590),
    ("mug",
     "Mug, c. 2016. Glazed ceramic. Inscribed 'WORLD'S BEST BOSS'; "
     "no evidence supports the claim. Gift of Human Resources.",
     8, 9, 8, 9, 0.520),
    ("keyboard",
     "Keyboard, c. 2017. Plastic, crumbs. Excavated from a desk drawer; "
     "scholars believe its missing keys spell the name of a forgotten god.",
     9, 8, 8, 8, 0.580),
    ("paperclip",
     "Paperclip, c. 2014. Bent steel. A humble clasp, bent by hand into a "
     "lock-pick \u2014 or so its owner told the guards.",
     9, 8, 9, 8, 0.512),
    ("memstick",
     "Memory stick, c. 2015. Plastic, silicon. Held the tribe's entire "
     "archive; lost in a coat pocket, mourned for a generation.",
     8, 8, 8, 8, 0.543),
    ("marker",
     "Whiteboard marker, c. 2021. Felt, solvent ink. Used to inscribe "
     "prophecies that faded within a week; the tribe called this 'planning'.",
     8, 9, 8, 8, 0.536),
    ("chair",
     "Office chair, c. 2018. Mesh, gas lift. Throne of the middle manager; "
     "its height was adjusted daily, its authority never.",
     7, 8, 8, 8, 0.229),
    ("fern",
     "Office fern, c. 2019. Ceramic, soil, neglect. The only living thing "
     "in the department; watered by guilt, mourned by no one.",
     7, 8, 8, 7, 0.314),
    ("sticky-password",
     "Sticky note, c. 2019. Paper, adhesive, ink. Found beneath a monitor, "
     "still bearing the password its owner swore they would remember.",
     7, 7, 7, 8, 0.50),
    ("lanyard",
     "Lanyard, c. 2018. Woven nylon, clip. Worn daily by a priest of the "
     "open-plan temple; its badge granted passage to the sacred kitchen.",
     8, 7, 7, 8, 0.50),
    ("microwave",
     "Microwave oven, c. 2015. Steel, glass. Ritual vessel in which the "
     "tribe reheated the same lunch for seven years, always two minutes too long.",
     7, 7, 7, 8, 0.50),
    ("stapler",
     "Stapler, c. 2012. Painted steel. Ceremonial binder of quarterly "
     "reports; its jaws closed only when the gods of finance were appeased.",
     7, 7, 8, 8, 0.50),
    ("mouse",
     "Computer mouse, c. 2020. Plastic, rubber. A small idol, rubbed daily "
     "for luck; its red eye blinked when the tribe's prayers went unanswered.",
     7, 7, 7, 8, 0.50),
    ("hole-puncher",
     "Hole puncher, c. 2013. Cast iron. Punched perfect circles into sacred "
     "scrolls; the tribe filed the holes and kept the paper.",
     7, 8, 7, 8, 0.50),
    ("sticky-dave",
     "Sticky note, c. 2019. Paper, adhesive. 'CALL DAVE \u2014 URGENT.' "
     "Dave was never called; the note outlived the company.",
     8, 8, 8, 7, 0.50),
]

# Judge's brief order: conceit, dryness, economy, label craft.
WEIGHTS = (1.5, 1.2, 1.0, 0.8)


@dataclass
class Scored:
    key: str
    text: str
    score: float


def score_all():
    out = []
    for key, text, conceit, dryness, economy, craft, proxy in CANDIDATES:
        total = (conceit * WEIGHTS[0] + dryness * WEIGHTS[1]
                 + economy * WEIGHTS[2] + craft * WEIGHTS[3]
                 + proxy * 10.0)
        out.append(Scored(key, text, total))
    # Highest score wins; ties break to the shorter line (economy),
    # then to the earlier candidate (stable, deterministic).
    out.sort(key=lambda s: (-s.score, len(s.text), CANDIDATES.index(
        next(c for c in CANDIDATES if c[0] == s.key))))
    return out


def main():
    ranked = score_all()
    winner = ranked[0]
    assert 1 <= len(winner.text) <= 180, "winner must fit the 180-char gate"
    assert winner.text == winner.text.strip(), "no leading/trailing space"
    assert "\n" not in winner.text, "one line only"
    outdir = os.environ.get("MAKEFUN_OUTPUT", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.txt")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(winner.text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


if __name__ == "__main__":
    main()

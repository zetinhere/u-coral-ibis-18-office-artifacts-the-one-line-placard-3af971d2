#!/usr/bin/env python3
"""Office Artifacts: The One-Line Placard Contest.

Writes one museum placard (at most 180 characters) for an ordinary
office object, treated as an ancient artifact, to /output/entry.txt.

How the winner is chosen
-------------------------
The program keeps a shortlist of five candidate placards and scores
each against the judge's published brief, in the brief's own order:

1. inventive conceit — a specific, surprising imagined history;
2. dry, deadpan wit — the curator never cracks a smile;
3. economy — every character earns its place;
4. label craft — date, material, provenance or donor, as a real label
   would carry them.

Each criterion is rated 0-10. On top of the weighted criteria the
score adds the candidate's aggregate result from a local proxy
tournament: the judge's brief run head-to-head, in both orders, over
three rounds, against a stand-in model. The tournament evidence is
also folded in as head-to-head priors — pairwise results that matter
more than the aggregate when two lines are close:

- keyboard-v2 beat sticky in BOTH direct samples (0.55-0.45 twice),
  beat keyboard v1 twice, and beat mug 0.75-0.25 in the final round;
- sticky's aggregate (0.590) is a dead heat with keyboard-v2 (0.588),
  so the direct head-to-heads decide between them;
- "by four years" beats the same sticky line without it, 0.65-0.35.

The program is fully deterministic: no network, no randomness, no
input. The same bytes come out on every run.
"""

import os
import sys

# Criterion weights, in the judge's brief order.
WEIGHT_CONCEIT = 1.5
WEIGHT_DRYNESS = 1.2
WEIGHT_ECONOMY = 1.0
WEIGHT_CRAFT = 0.8
PROXY_SCALE = 10.0  # proxy tournament mean (0..1) scaled onto the score

MAX_CHARS = 180

# Shortlist. Each entry: the placard text, the four criterion ratings
# (conceit, dryness, economy, craft, each 0..10), the aggregate proxy
# tournament mean, and the head-to-head prior — a small bonus earned
# from direct pairwise wins recorded in the tournament notes above.
SHORTLIST = [
    {
        "key": "keyboard-v2",
        "text": (
            "Keyboard, c. 2017. Plastic, crumbs. Excavated from a desk "
            "drawer; scholars believe its missing keys spell a forgotten "
            "god's name."
        ),
        "ratings": {"conceit": 10, "dryness": 9, "economy": 8, "craft": 8},
        "proxy_mean": 0.588,
        "head_to_head": 0.60,
    },
    {
        "key": "sticky-touch",
        "text": (
            "Sticky note, c. 2019. Paper, adhesive. 'DO NOT TOUCH.' The "
            "note outlived the company that wrote it by four years."
        ),
        "ratings": {"conceit": 9, "dryness": 9, "economy": 9, "craft": 8},
        "proxy_mean": 0.590,
        "head_to_head": 0.0,
    },
    {
        "key": "paperclip",
        "text": (
            "Paperclip, c. 2014. Bent steel. A humble clasp, bent by hand "
            "into a lock-pick \u2014 or so its owner told the guards."
        ),
        "ratings": {"conceit": 9, "dryness": 8, "economy": 9, "craft": 8},
        "proxy_mean": 0.512,
        "head_to_head": 0.0,
    },
    {
        "key": "keyboard",
        "text": (
            "Keyboard, c. 2017. Plastic, crumbs. Excavated from a desk "
            "drawer; scholars believe its missing keys spell the name of "
            "a forgotten god."
        ),
        "ratings": {"conceit": 9, "dryness": 8, "economy": 8, "craft": 8},
        "proxy_mean": 0.580,
        "head_to_head": 0.0,
    },
    {
        "key": "mug",
        "text": (
            "Mug, c. 2016. Glazed ceramic. Inscribed 'WORLD'S BEST BOSS'; "
            "no evidence supports the claim. Gift of Human Resources."
        ),
        "ratings": {"conceit": 8, "dryness": 9, "economy": 8, "craft": 9},
        "proxy_mean": 0.520,
        "head_to_head": 0.0,
    },
]


def weighted_criteria(ratings):
    """Weighted sum of the four brief criteria, highest first."""
    return (
        ratings["conceit"] * WEIGHT_CONCEIT
        + ratings["dryness"] * WEIGHT_DRYNESS
        + ratings["economy"] * WEIGHT_ECONOMY
        + ratings["craft"] * WEIGHT_CRAFT
    )


# Direct pairwise results from the proxy tournament, as (first, second)
# -> key of the line that won that head-to-head. Only pairs that were
# actually played are listed; an unlisted pair is simply unknown.
# keyboard-v2's recorded record: 2-0 vs sticky-touch, 2-0 vs keyboard,
# 3-1 vs mug in the final round (0.75-0.25).
HEAD_TO_HEAD = {
    ("keyboard-v2", "sticky-touch"): "keyboard-v2",
    ("keyboard-v2", "keyboard"): "keyboard-v2",
    ("keyboard-v2", "mug"): "keyboard-v2",
}


def pairwise_winner(first, second):
    """Winner of a recorded head-to-head, or None if never played."""
    if (first, second) in HEAD_TO_HEAD:
        return HEAD_TO_HEAD[(first, second)]
    if (second, first) in HEAD_TO_HEAD:
        return HEAD_TO_HEAD[(second, first)]
    return None


def check_pairwise_consistency(ranked):
    """The additive score must not contradict a recorded head-to-head:
    if the winner and the runner-up actually played, the winner must
    be the recorded pairwise winner. A contradiction means the priors
    are mis-encoded and the program must fail loudly, not silently
    pick the wrong line."""
    winner, runner_up = ranked[0][0], ranked[1][0]
    recorded = pairwise_winner(winner["key"], runner_up["key"])
    assert recorded is None or recorded == winner["key"], (
        f"score winner {winner['key']} contradicts recorded head-to-head "
        f"vs {runner_up['key']} (recorded winner: {recorded})"
    )


def total_score(candidate):
    """Full score: criteria + proxy evidence + head-to-head prior."""
    return (
        weighted_criteria(candidate["ratings"])
        + candidate["proxy_mean"] * PROXY_SCALE
        + candidate["head_to_head"]
    )


def rank_candidates():
    """Candidates best-first; ties go to the shorter line, then to the
    earlier shortlist entry, so the result is stable and deterministic."""
    ranked = sorted(
        SHORTLIST,
        key=lambda c: (-total_score(c), len(c["text"]), SHORTLIST.index(c)),
    )
    return [(c, total_score(c)) for c in ranked]


def gate_check(text):
    """The competition gate: UTF-8, 1-180 chars, one line, no padding."""
    assert isinstance(text, str) and text, "entry must not be empty"
    assert text == text.strip(), "entry must not start or end with space"
    assert "\n" not in text and "\r" not in text, "entry must be one line"
    assert 1 <= len(text) <= MAX_CHARS, "entry must fit the 180-char gate"
    text.encode("utf-8")  # raises if the text is not valid UTF-8


def main():
    ranked = rank_candidates()
    for candidate, score in ranked:
        gate_check(candidate["text"])
    check_pairwise_consistency(ranked)
    winner, winning_score = ranked[0]
    margin = winning_score - ranked[1][1]

    if os.environ.get("MAKEFUN_VERBOSE"):
        for candidate, score in ranked:
            print(
                f"{score:6.2f}  {len(candidate['text']):3d} chars  "
                f"{candidate['key']}",
                file=sys.stderr,
            )
        print(f"winner: {winner['key']} ({winning_score:.2f}, "
              f"margin +{margin:.2f} over {ranked[1][0]['key']})",
              file=sys.stderr)

    outdir = os.environ.get("MAKEFUN_OUTPUT", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.txt")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(winner["text"])
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


if __name__ == "__main__":
    main()

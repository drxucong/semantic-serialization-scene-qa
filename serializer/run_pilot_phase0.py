"""Extract of the authors' scripts/pilot/run_pilot_phase0.py: the two functions that the
serializer files import. The rest of that file belongs to an earlier project and is not
part of this release. The two functions are verbatim."""
import re


def forced_choices(item):
    """Strip the abstain option and re-letter deterministically."""
    opts = [t for l, t in sorted(item["choices"].items())
            if l != item["abstain_letter"]]
    letters = "ABCD"[:len(opts)]
    ch = {l: t for l, t in zip(letters, opts)}
    correct_text = item["choices"][item["answer"]]
    ans = letters[opts.index(correct_text)] if correct_text in opts else None
    return ch, ans


def parse_letter(text, valid):
    # robust: letter not adjacent to latin letters (handles CJK context, "C.", "(C)")
    m = re.search(r"(?<![A-Za-z])([A-D])(?![A-Za-z])", text.strip().upper())
    return m.group(1) if m and m.group(1) in valid else None

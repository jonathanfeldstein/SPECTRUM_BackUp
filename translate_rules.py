#!/usr/bin/env python3

import json
import re
import sys
from itertools import permutations

RULE_RE = re.compile(
    r'^\s*([0-9.]+)\s*:\s*(.*?)\s*>>\s*(.*?)\s*\^\d+\s*$'
)

ATOM_RE = re.compile(r'(\w+)\(([^)]*)\)')


def parse_atom(text):
    m = ATOM_RE.fullmatch(text.strip())
    if not m:
        raise ValueError(f"Cannot parse atom: {text}")
    pred = m.group(1)
    vars_ = tuple(v.strip() for v in m.group(2).split(","))
    return pred, vars_


def parse_rule(rule):

    m = RULE_RE.match(rule)
    if not m:
        raise ValueError(rule)

    weight = m.group(1)

    body = [x.strip() for x in m.group(2).split("&")]

    head = parse_atom(m.group(3))

    body = [parse_atom(x) for x in body]

    return float(weight), head, body


def canonical_patterns(head_vars, body_len):
    """
    Returns the expected variable pairs for each body atom.

    body_len=1:
       [(Y,X)]

    body_len=2:
       [(Z1,Y),(X,Z1)]

    body_len=3:
       [(Z2,Y),(Z1,Z2),(X,Z1)]

    etc.
    """

    X, Y = head_vars

    if body_len == 1:
        return [(Y, X)]

    z = [f"__Z{i}" for i in range(1, body_len)]

    # reverse so nearest to Y comes first
    z = list(reversed(z))

    patterns = []

    patterns.append((z[0], Y))

    for i in range(len(z)-1):
        patterns.append((z[i+1], z[i]))

    patterns.append((X, z[-1]))

    return patterns


def translate_rule(weight, head, body):

    head_pred, head_vars = head

    patterns = canonical_patterns(head_vars, len(body))

    # collect real variables
    vars_real = list(dict.fromkeys(head_vars + tuple(
        v
        for _,vs in body
        for v in vs
    )))

    X, Y = head_vars

    internal = [v for v in vars_real if v not in (X,Y)]

    if len(internal) != max(0, len(body)-1):
        raise RuntimeError(
            f"Rule is not a simple chain:\n{head}\n{body}"
        )

    znames = [f"__Z{i}" for i in range(1,len(body))]
    znames = list(reversed(znames))

    mapping = {X:X, Y:Y}

    for zn, real in zip(znames, internal):
        mapping[zn] = real

    translated = []

    remaining = list(body)

    for expected in patterns:

        exp = (mapping[expected[0]], mapping[expected[1]])

        found = False

        for i,(pred,args) in enumerate(remaining):

            if args == exp:
                translated.append(pred)
                remaining.pop(i)
                found = True
                break

            if args == (exp[1],exp[0]):
                translated.append("inv_"+pred)
                remaining.pop(i)
                found = True
                break

        if not found:
            raise RuntimeError(
                f"Could not match expected atom {exp}"
            )

    return (
        f"{weight:.3f} ({weight:.3f})\t"
        f"{head_pred} <-- "
        + ", ".join(translated)
    )


def main(inp, out):

    with open(inp) as f:
        rules = json.load(f)["rules"]

    lines = []

    for r in rules:
        w,h,b = parse_rule(r)
        lines.append(translate_rule(w,h,b))

    with open(out,"w") as f:
        for l in lines:
            f.write(l+"\n")


if __name__=="__main__":

    if len(sys.argv)!=3:
        print("usage:")
        print("python translate.py input.json output.txt")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
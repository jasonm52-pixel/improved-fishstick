"""Sensitivity of the top-5 basket to scorecard inputs.

Scores are copied from the report's 21-name table. The selection rule is the
report's, made mechanical: rank by weighted score; ties go to the name with an
in-window report (catalyst >= 3), then the lower-risk name; max 2 per sector;
max 2 AI-capex names (AI hardware plus AI-power industrials).
"""
import itertools, random
from collections import Counter

W = dict(rev=.25, cat=.20, mom=.20, risk=.15, val=.10, struct=.10)
F = list(W)
# ticker: (sector, ai_capex, rev, cat, mom, risk, val, struct)
S = {
 "NVDA": ("IT", 1, 5,3,2,4,4,5), "TRV": ("Fin", 0, 5,4,3,4,2,3),
 "DELL": ("IT", 1, 5,2,5,2,3,4), "ANET": ("IT", 1, 4,4,4,3,2,4),
 "APH":  ("IT", 1, 4,4,3,4,2,4), "JPM": ("Fin", 0, 4,4,3,3,3,4),
 "MU":   ("IT", 1, 5,4,4,1,2,3), "THC": ("HC", 0, 4,3,5,2,4,2),
 "VLO":  ("En", 0, 5,3,4,1,3,2), "P":   ("IT", 1, 5,2,4,2,1,4),
 "CVE":  ("En", 0, 4,3,3,2,4,3), "GEV": ("Ind", 1, 3,4,2,3,2,5),
 "FIX":  ("Ind", 1, 4,3,2,3,2,4), "GMED": ("HC", 0, 4,3,1,3,4,3),
 "VRT":  ("Ind", 1, 4,4,1,1,3,4), "CRWD": ("IT", 0, 4,1,4,2,1,4),
 "SNOW": ("IT", 0, 4,1,3,2,2,4), "KR":  ("Stap", 0, 2,4,1,4,4,2),
 "STRL": ("Ind", 1, 4,3,0,1,4,4), "GS":  ("Fin", 0, 1,3,1,2,3,3),
 "CCL":  ("Disc", 0, 1,4,0,1,4,3),
}
REPORT = frozenset({"NVDA", "TRV", "APH", "JPM", "THC"})

def scores(tbl, w=W):
    return {t: round(sum(w[f]*v for f, v in zip(F, r[2:])), 4) for t, r in tbl.items()}

def pick(tbl, w=W):
    sc = scores(tbl, w)
    order = sorted(tbl, key=lambda t: (-sc[t], -(tbl[t][3] >= 3), -tbl[t][5]))
    out, sec, ai = [], Counter(), 0
    for t in order:
        s, a = tbl[t][0], tbl[t][1]
        if sec[s] >= 2 or (a and ai >= 2):
            continue
        out.append(t); sec[s] += 1; ai += a
        if len(out) == 5:
            break
    return frozenset(out), sc

def tweak(tbl, t, f, v):
    new = dict(tbl); r = list(new[t]); r[2 + F.index(f)] = max(0, min(5, v)); new[t] = tuple(r)
    return new

def fmt(b):
    return ", ".join(sorted(b))

if __name__ == "__main__":
    base, sc = pick(S)
    print("Mechanical basket:", fmt(base), "| report basket:", fmt(REPORT))
    print("Differs from report by:", fmt(base - REPORT), "in /", fmt(REPORT - base), "out\n")

    print("Named scenarios")
    named = {
        "NVDA risk 4->3": tweak(S, "NVDA", "risk", 3),
        "NVDA risk 4->2": tweak(S, "NVDA", "risk", 2),
        "NVDA reports Nov 25 (catalyst 3->2)": tweak(S, "NVDA", "cat", 2),
        "NVDA Nov 25 and risk 2": tweak(tweak(S, "NVDA", "cat", 2), "NVDA", "risk", 2),
        "ANET risk 3->4 (treat like APH)": tweak(S, "ANET", "risk", 4),
    }
    for k, tbl in named.items():
        b, s = pick(tbl)
        print(f"- {k}: NVDA={s['NVDA']:.2f}; basket = {fmt(b)}")

    print("\nWeight shifts (+/-5pp on one factor, others rescaled)")
    for f, d in itertools.product(F, (+.05, -.05)):
        w = dict(W); w[f] += d
        rest = sum(v for k, v in W.items() if k != f)
        for k in W:
            if k != f:
                w[k] = W[k] * (1 - w[f]) / rest
        b, _ = pick(S, w)
        print(f"- {f} {d:+.2f}: {fmt(b)}{'' if b == base else '  <- changes'}")

    print("\nOne-at-a-time +/-1 on every sub-score (21 names x 6 factors x 2)")
    n = ch = 0; who = Counter()
    for t, f, d in itertools.product(S, F, (1, -1)):
        b, _ = pick(tweak(S, t, f, S[t][2 + F.index(f)] + d)); n += 1
        if b != base:
            ch += 1; who[f"{t}.{f}{d:+d}"] += 1
    print(f"- basket changes in {ch} of {n} single-point moves: {', '.join(who)}")

    print("\nMonte Carlo: each sub-score moves -1/0/+1 with prob 25/50/25%, 20,000 draws")
    random.seed(0); N = 20000; freq = Counter(); exact = Counter()
    for _ in range(N):
        tbl = {t: r[:2] + tuple(max(0, min(5, v + random.choice((-1, 0, 0, 1)))) for v in r[2:]) for t, r in S.items()}
        b, _ = pick(tbl); freq.update(b); exact[b] += 1
    print("| Ticker | Selected in % of draws |\n|---|---|")
    for t, c in freq.most_common(12):
        print(f"| {t} | {100*c/N:.0f}% |")
    print(f"\nMechanical basket exact: {100*exact[base]/N:.1f}% of draws; report basket exact: {100*exact[REPORT]/N:.1f}%")
    b1, c1 = exact.most_common(1)[0]
    print(f"Most common basket: {fmt(b1)} ({100*c1/N:.1f}%)")

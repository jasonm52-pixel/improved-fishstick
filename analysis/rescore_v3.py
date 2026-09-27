"""V3 re-score: one risk rule and one catalyst rule applied to all 21 names.

Risk (5 = lowest risk): start from the report's relative-volatility class
  low (~20%/yr vs index: large banks, P&C insurers, staples) = 4
  typical (~30%) = 3
  high (45-60%: semis/AI hardware, beta ~2 names, cruise) = 2
  then -1 for a known in-window binary event priced at >= +/-10%,
  -1 for an extended chart flagged in the notes (RSI ~75, or >40% above the 150-day).
Catalyst: 4 = in-window report or event announced by the company itself
  3 = in-window date from aggregators or historical pattern only
  2 = date could fall either side of Nov 20
  1 = next report expected after Nov 20
Revisions, momentum, valuation and structural scores are unchanged from V2.
"""
import sensitivity as s

# ticker: (risk_class, flags, risk_note, catalyst, cat_note)
R = {
 "NVDA": (2, 0, "semis class", 2, "Nov 17 vs Nov 25 unresolved"),
 "TRV":  (4, 0, "P&C insurer", 4, "Oct 16, company"),
 "DELL": (2, 0, "AI hardware", 1, "~Nov 24, after window"),
 "ANET": (2, 0, "AI hardware", 3, "Nov 2, aggregator"),
 "APH":  (3, 0, "diversified interconnect, typical class", 3, "Oct 28, aggregator"),
 "JPM":  (4, 0, "large bank", 4, "Oct 13, company"),
 "MU":   (2, 1, "semis; +/-10% print Sep 30", 4, "Sep 30, company"),
 "THC":  (3, 1, "RSI ~75", 3, "late Oct, pattern"),
 "VLO":  (3, 1, "refiners >40% above 150-day", 4, "Oct 22, company"),
 "P":    (2, 0, "AI hardware", 1, "early Dec"),
 "CVE":  (3, 0, "oil producer", 3, "not announced"),
 "GEV":  (3, 0, "beta ~0.8-1.0", 4, "Oct 28, company events page"),
 "FIX":  (3, 0, "typical", 3, "Oct 22, aggregator"),
 "GMED": (3, 0, "typical", 3, "~Nov 5, pattern"),
 "VRT":  (2, 0, "beta ~2.1", 3, "Oct 20/28, aggregators"),
 "CRWD": (3, 0, "software, typical", 1, "early Dec"),
 "SNOW": (3, 0, "software, typical", 1, "late Nov/Dec"),
 "KR":   (4, 0, "staples", 4, "Oct 20 investor day, company"),
 "STRL": (2, 0, "high beta, broken chart", 3, "~Nov 9, pattern"),
 "GS":   (3, 0, "trading-heavy bank, typical", 3, "Oct 13, aggregator"),
 "CCL":  (2, 1, "cruise; binary Sep 29 print", 4, "Sep 29"),
}
V3 = {}
for t, row in s.S.items():
    rc, fl, _, cat, _ = R[t]
    r = list(row); r[2 + s.F.index("risk")] = max(0, rc - fl); r[2 + s.F.index("cat")] = cat
    V3[t] = tuple(r)

v2, v3 = s.scores(s.S), s.scores(V3)
print("| Ticker | Risk V2→V3 | Catalyst V2→V3 | Score V2 | Score V3 |\n|---|---|---|---|---|")
for t in sorted(V3, key=lambda t: -v3[t]):
    i, j = 2 + s.F.index("risk"), 2 + s.F.index("cat")
    print(f"| {t} | {s.S[t][i]}→{V3[t][i]} | {s.S[t][j]}→{V3[t][j]} | {v2[t]:.2f} | {v3[t]:.2f} |")
b, sc = s.pick(V3)
print("\nV3 mechanical basket:", s.fmt(b), f"avg {sum(sc[t] for t in b)/5:.2f}")
alts = {"NVDA reports Nov 17 (catalyst 4)": s.tweak(V3, "NVDA", "cat", 4),
        "NVDA in typical risk class (risk 3)": s.tweak(V3, "NVDA", "risk", 3),
        "both": s.tweak(s.tweak(V3, "NVDA", "cat", 4), "NVDA", "risk", 3)}
for k, tbl in alts.items():
    bb, ss = s.pick(tbl); print(f"- {k}: NVDA {ss['NVDA']:.2f}; basket {s.fmt(bb)}")
import random, itertools
from collections import Counter
random.seed(0); N = 20000; freq = Counter(); exact = Counter()
for _ in range(N):
    tbl = {t: r[:2] + tuple(max(0, min(5, v + random.choice((-1, 0, 0, 1)))) for v in r[2:]) for t, r in V3.items()}
    bb, _ = s.pick(tbl); freq.update(bb); exact[bb] += 1
print("\nMonte Carlo selection frequency (V3):")
for t, c in freq.most_common(12): print(f"| {t} | {100*c/N:.0f}% |")
print(f"V3 basket exact {100*exact[b]/N:.1f}%; most common {s.fmt(exact.most_common(1)[0][0])} {100*exact.most_common(1)[0][1]/N:.1f}%")
ch = 0
for f, d in itertools.product(s.F, (.05, -.05)):
    w = dict(s.W); w[f] += d; rest = sum(v for k, v in s.W.items() if k != f)
    for k in s.W:
        if k != f: w[k] = s.W[k] * (1 - w[f]) / rest
    bb, _ = s.pick(V3, w); ch += bb != b
    if bb != b: print(f"weight {f} {d:+.2f}: {s.fmt(bb)}")
print(f"weight shifts changing the V3 basket: {ch} of 12")

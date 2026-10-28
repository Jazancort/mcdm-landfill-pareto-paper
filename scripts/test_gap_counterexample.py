"""
test_gap_counterexample.py
--------------------------
Demonstrates that gap(t)=0 does NOT imply t is Pareto-efficient.
Counterexample: T = {t=(1,1,0), u=(0,1,0), v=(2,2,1)}
F1,F2 minimise; F3 maximise. u dominates t. gap(t)=0 (no simultaneous improvement).

The check_consistency.py 'gap=0 iff Pareto' test must be ABSENT or disabled.
This file is the authoritative record of the mathematical fact.

exit 0 = PASS (counterexample confirmed), exit 1 = FAIL.
"""
import sys

def improvement(t, tp, obj_types, ranges):
    impr = []
    for k, (ot, rng) in enumerate(zip(obj_types, ranges)):
        if ot == 'min':
            impr.append((t[k] - tp[k]) / rng)
        else:
            impr.append((tp[k] - t[k]) / rng)
    return impr

def dominates(a, b, obj_types):
    at_least = all(
        (a[k] <= b[k] if ot == 'min' else a[k] >= b[k])
        for k, ot in enumerate(obj_types)
    )
    strictly = any(
        (a[k] < b[k] if ot == 'min' else a[k] > b[k])
        for k, ot in enumerate(obj_types)
    )
    return at_least and strictly

obj_types = ['min', 'min', 'max']
ranges    = [2.0, 1.0, 1.0]

t = [1.0, 1.0, 0.0]
u = [0.0, 1.0, 0.0]
v = [2.0, 2.0, 1.0]

gap_t = max(
    min(improvement(t, tp, obj_types, ranges))
    for tp in [u, v]
)

u_dom_t = dominates(u, t, obj_types)

print("=== gap=0 iff Pareto counterexample ===\n")
print(f"  T = {{t={t}, u={u}, v={v}}}")
print(f"  F1,F2 min; F3 max; ranges={ranges}")
print(f"  u dominates t: {u_dom_t}")
print(f"  gap(t) = {gap_t}")
print()

assert u_dom_t,          "FAIL: u should dominate t"
assert abs(gap_t) < 1e-12, f"FAIL: gap(t) should be 0, got {gap_t}"

print("COUNTEREXAMPLE CONFIRMED: gap(t)=0 AND t is dominated.")
print("Pareto membership requires a separate dominance test.")
print("The caption 'gap=0 iff the portfolio lies in the reference set' is INCORRECT.")
print("Correct caption: 'Pareto membership is determined by a separate dominance test.")
print("  The reported gap measures simultaneous improvement and can be zero for a dominated portfolio.'")
print()
print("TEST PASSED")
sys.exit(0)

"""Additive LMDI for positive observations at matched annual output prices."""
import math


def logarithmic_mean(before, after):
    if not all(math.isfinite(x) and x > 0 for x in (before, after)):
        raise ValueError('LMDI requires finite positive energy')
    if before == after:
        return before
    return (after - before) / math.log1p((after - before) / before)


def decompose(energy0, energy1, output0, output1):
    arrays = (energy0, energy1, output0, output1)
    if not energy0 or len({len(a) for a in arrays}) != 1:
        raise ValueError('Four nonempty arrays must have equal length')
    if any(not math.isfinite(v) or v <= 0 for a in arrays for v in a):
        raise ValueError('Missing, nonpositive or nonfinite inputs are excluded')
    total0, total1 = math.fsum(output0), math.fsum(output1)
    activity_log = math.log(total1 / total0)
    weights = [logarithmic_mean(a, b) for a, b in zip(energy0, energy1)]
    activity = math.fsum(w * activity_log for w in weights)
    structure = math.fsum(w * math.log((q1 / total1) / (q0 / total0))
                         for w, q0, q1 in zip(weights, output0, output1))
    intensity = math.fsum(w * (math.log(e1 / e0) - math.log(q1 / q0))
                         for w, e0, e1, q0, q1 in zip(weights, *arrays))
    before, after = math.fsum(energy0), math.fsum(energy1)
    change = after - before
    return {'activity_tj': activity, 'structure_tj': structure,
            'intensity_tj': intensity, 'energy_change_tj': change,
            'residual_tj': math.fsum((activity, structure, intensity)) - change,
            'energy0_tj': before, 'energy1_tj': after}

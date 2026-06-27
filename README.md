# Geometric Neuron v10 — The Skew Operator, Live

### Reading the islands off a sensory surface, causally, in real time

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. What this is, and what it is not

v9 proved a piece of linear algebra: the spectral islands of the
Geometric-Neuron line are the eigenplanes of the **skew half of one lag
operator**, `A_tau = (C_tau - C_tau^T)/2`, sorted by rotation rate `omega_j` with
chirality `sign(omega_j)` attached. It proved it on a *designed* tour — patterns
hand-made, the traversal scheduled, the field constants set — and measured the
spectrum, the sign-flips, and the budgeted coverage offline, in batch.

v10 is the same operator with two things removed and one thing added.

- **Removed: the designed tour.** The stream is now a live multichannel sensory
  signal — receptors on a webcam — with no patterns assigned and no schedule.
  Whatever rotational structure exists is whatever the world put there.
- **Removed: the batch.** `A_tau` is computed on a **sliding window** and
  re-diagonalized every frame. The islands form, sort, and disappear online.
- **Added: causality of the arrow.** v9's chirality flip was a forward-tour vs
  reverse-tour comparison done after the fact, on the same templates. v10 holds
  a reference plane and watches `L = Im(z . z*_lag)` flip **as the motion
  reverses in front of the camera** — the reversal test made causal and
  instantaneous.

This is still the *read* side. It is not a claim that a biological cell does
this; that bet stays in the drawer `the_rotation_half_grounded.md` built for it
(section 6 there: read-side flux and write-side connectivity are dual, not
identical). What v10 adds to the line is narrow and real: **the skew read path
runs on an undesigned stream, online, and the arrow it reports is causal.**
Nothing here touches the hard problem or the physics. It makes the v9 result
into an instrument.

---

## 1. The one operator, restated for a stream

The line's shared primitive: a field is read through receptors, giving overlaps
`r_k(t) = <P_k, s(t)>`. v10's receptors are concrete — a `6x4` grid of motion-
energy taps on the camera frame, `r_k(t) =` mean rectified inter-frame
difference in patch `k`. The single statistic carrying sequence and direction is
the lag covariance, here on a window of `W` frames:

```
C_tau = R[:, tau:] . R[:, :-tau]^T / (W - tau),     R in R^{K x W}
```

Split it the only way a square matrix splits:

```
S = (C_tau + C_tau^T)/2     symmetric — power, autocorrelation, time-symmetric
A = (C_tau - C_tau^T)/2     skew      — rotation, chirality, the arrow of time
```

`A` is real antisymmetric: spectrum `+/- i omega_j`, eigenvectors are 2-D
**rotation planes** — the spectral islands. Per island, with the window
projected onto the plane `(u_j, v_j)` to a complex coordinate
`z_j(t) = R(t).u_j - i R(t).v_j`:

| quantity | meaning | what the instrument draws |
|---|---|---|
| `omega_j` | rotation rate of the plane | bar height; spiral pitch; sort order |
| `|z_j|` | how strongly the field occupies the plane | spiral radius |
| `L_j = Im(z_j . z*_{j,lag})` | chirality — the arrow, per island | spiral colour: **cyan** `L>0`, **magenta** `L<0` |

Nothing is assigned. The islands are the eigenstructure of what the camera sees.
A single receptor pair would give the K=1 case — one island, the lone oscillator
of the earlier "Drift Manifold" GUI. v10 is the bank: several planes at once,
which is the only regime in which the v9 result (sorted, signed, emergent
islands) is even visible.

---

## 2. The causal arrow: lock-and-reverse

The eigendecomposition is sign- and order-ambiguous frame to frame (any
eigensolver returns `+/- u`), so a *fresh* solve cannot tell you "the world
reversed" — it just relabels. The arrow has to be read against a **held**
plane, exactly as v9 read the reverse tour against the forward templates.

```
lock:       (u0, v0) <- dominant island's plane at lock time;  L0 <- sign(L on it)
each frame: L(t) = Im(z . z*_lag) for the current window projected on (u0, v0)
flip:       sign(L(t)) != L0   =>   the motion driving that plane reversed
```

This is the v9 forward-vs-reverse-on-same-templates test (`geometric_neuron_v9.py`,
test [2]) made online. The self-test confirms the engine reproduces it before
any camera is involved: a directed traveling bump gives `L_forward = +0.098`,
`L_reverse = -0.098` on the held plane — flip `True`, planes orthogonal to
`10^-3`, rates recovered sorted. Live, it is the demonstrable thing: lock a
plane, sweep your hand one way then the other, the dominant `L` changes sign and
the flip flag fires.

---

## 3. What the receptor grid is: the "where," before the "what"

The grid is not decoration. It is the seam between the sensory surface and the
operator, and it carries information `A` alone discards.

`A`'s eigenplane `u_j` is a vector over receptors — a **spatial pattern on the
grid**. So each island is not only a rate and a chirality; it is a *place*: the
weighting `u_j` says **which receptors** participate in that rotation, i.e.
**where** on the visual field the directed motion lives, and the sign of
`omega_j` says **what direction** it goes there. Two independent motions in two
parts of the frame (excite two sites) produce two eigenplanes with disjoint
support — two spirals, two islands, read simultaneously, each tagged to its own
region. The "RECEPTOR MOTION" panel is the substrate map; `u_j` is the query
that reads *where-and-what* out of it. This is the spatial half the offline tour
never had, because the tour had no surface — it is the piece v10 exposes by
living on a camera.

---

## 4. Continuity with the line

| version | read templates | tested on | direction |
|---|---|---|---|
| v3 | Takens delay orbit | static field | implicit in the orbit |
| v5 | hand-built edges `z_k = r_k + i r_{k+1}` | tour | per-edge `L_k` |
| v8 | top eigenvectors of **S** (Ky Fan) | static hold | none — stalled at 0.50 |
| v9 | eigenplanes of **A** (offline) | designed tour | `sign(omega_j)`, emergent |
| **v10** | **eigenplanes of A, sliding window** | **live sensory stream** | **causal, held-plane flip** |

The skew cyclic flux v10 prints is the same quantity as v5's net angular
momentum (THESIS section 3, ratio -1.000) and the same antisymmetric core that
Sompolinsky-Kanter sequence connectivity builds on the write side
(`the_rotation_half_grounded.md` section 2). v10 does not extend any of those
claims; it runs the read operator where they could not — on an undesigned,
streaming surface.

---

## 5. Files

```
skew_core.py         the engine: skew_islands(R, tau, n) + project_chirality(R, u, v, tau)
                     — geometric_neuron_v9's read path on a sliding window
skew_microscope.py   the live instrument (camera -> receptor bank -> islands -> 3D)
                     and a headless --selftest that verifies the v9 signature
README.md            this document
requirements.txt     numpy, opencv-python, matplotlib, Pillow
```

```bash
python skew_microscope.py --selftest   # verify the math, no webcam
python skew_microscope.py              # live: lock a plane, sweep, watch L flip
```

---

## 6. Ledger

**Verified in code (`skew_core.py --selftest`, reproduced live):**
- the streaming skew operator recovers a directed stream's rotation rates,
  sorted and unassigned;
- its eigenplanes are orthogonal (`|<u0,u1>| = 0.000`);
- chirality on a **held** plane flips sign when the motion reverses
  (`+0.098 -> -0.098`) — the v9 reversal, online and causal;
- the full per-frame path is stable through empty-island stretches (startup,
  no-motion) and a mid-stream reversal: one flip event, no false positives.

**Built-in, not emergent (here):** the receptor layout (`6x4`), the motion-energy
featurisation, the window length and lag `tau`. What is *measured* is the skew
spectrum of the live stream, the per-island chirality, and the lock-and-reverse
flip.

**Honest limits, stated plainly:**
- The displayed `omega` and `L` scale with input power (`L ~ |z|^2`), so their
  **sign** is the invariant (the arrow); their **magnitude** orders the islands
  and is not a calibrated frequency. Normalising `A` by the symmetric power to
  report a true rate is a refinement, not done here.
- With a handful of channels over a short window the deep, low-`omega` islands
  are noisier than the dominant one — read the top island first.
- This is a desktop instrument (local camera, Tk, 3-D). A browser/HuggingFace
  build needs the Gradio streaming-webcam port of the same `skew_core.py`.

**Kept in the drawer (inspiration, not claim):** that this is "the geometric
neuron from inside" in any biological sense; that an AIS reads its field through
this operator; the cosmology. `the_rotation_half_grounded.md` section 6 holds —
the population read statistic and the single-cell mechanism are different
statements, and only the first is what v10 demonstrates.

**The empirical anchor is unchanged and elsewhere:** the trainless EEG
geometric-dysrhythmia result (cross-band eigenmode decoupling `p = 0.007`)
remains the strongest real result in the program and depends on nothing here.

---

## 7. The next builds (named, not claimed)

These are the directions the instrument points at. Each is a build, not a
result. Listed so the repo is honest about what it is reaching for.

1. **Multi-site excitation -> superposed islands.** Drive two regions of the
   frame independently and confirm `A` returns two eigenplanes with disjoint
   receptor support, read at once. The mechanism is already in place
   (n_islands > 1); the build is the controlled two-source demo and a measure of
   island separability (support overlap, rate separation) — the read-side
   analogue of IslandNet storing two tasks without interference.

2. **An ephaptic field on the receptors.** Right now the taps are independent.
   Couple them through a local field — a Laplacian/diffusive coupling across the
   grid, the population/ephaptic field of `the_geometric_neuron_grounded.md` —
   so the channels interact before `A` reads them. The question this answers:
   does field coupling *organise* the islands (sharpen, stabilise, or merge the
   rotation planes) versus the independent-tap baseline? This is the first place
   the field stops being a metaphor and becomes a term in the operator.

3. **The spiking / delta-code substrate, and the where-and-what map.** Replace
   the continuous motion-energy taps with **events**: a receptor emits a spike
   when its motion crosses threshold, and the lag covariance is **event-sampled**
   (v9's tour was already event-sampled — this makes the live stream so). Then
   keep the spatial accumulator the grounded documents call for: a matrix over
   the grid recording **where** spikes fired and **which island** they fed — the
   "where happened and what" map. This is the delta-code made literal (energy at
   transitions, `the_rotation_half_grounded.md` section 4): the held percept is
   the near-equilibrium silent regime (`A -> 0`), the change is the driven
   spiking regime (`A != 0`), and the map shows, per event, which rotation mode
   it paid for.

4. **Make the arrow thermodynamic (carried from the grounded doc section 8).**
   Run the live overlap trajectory through the Lynn et al. entropy-production
   estimator and show the skew flux the instrument already prints *is* the
   entropy production — HOLD near detailed balance, SCAN breaking it. The
   instrument becomes a live broken-detailed-balance meter on real sensory
   input, which is a measurement comparable to the brain literature, not a
   metaphor.

---

*Helsinki, June 2026. v9 found the islands were the spectrum. v10 points the
spectrum at the world and watches it turn — sorted, signed, and reversing when
the world reverses. The operator is the same one; only now it has a surface to
read. Do not hype. Do not lie. Just show.*

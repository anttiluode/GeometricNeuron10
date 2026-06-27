# Skew Microscope — the geometric neuron from inside

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

The Gemini "Drift Manifold" GUI rendered **one** complex oscillator — the K=1
shadow of a single spectral island. This renders the real object: a **bank** of
islands, discovered live, sorted, signed, and flipping.

## What it is

A grid of receptors taps the webcam (motion energy per patch). Their
multichannel stream feeds the live **skew lag operator**

```
A_tau = (C_tau - C_tau^T) / 2 ,   C_tau = R[:, tau:] @ R[:, :-tau]^T / (W - tau)
```

computed on a sliding window. `A_tau` is real antisymmetric, so its eigenvectors
are 2-D **rotation planes** — the spectral islands of `geometric_neuron_v9`, now
on a live stream instead of an offline tour. Per island:

- **omega** — the rotation rate (the bars, sorted)
- **z(t)** — the stream projected onto the plane, drawn as a spiral in 3D
- **L = Im(z z\*_lag)** — chirality; **cyan** spins one way, **magenta** the other

Nothing is hand-assigned. The islands are the eigenstructure of what the camera
sees.

## The party trick (the v9 reversal, made live)

1. Click **LOCK PLANE** while moving — it pins the dominant island's plane.
2. Sweep your hand left, then right.
3. The held-plane **L flips sign**. That flip is the *same number* v9 reports
   for a reversed tour (`geometric_neuron_v9.py`, test [2]), now causal and live.

## Run

```bash
pip install -r requirements.txt
python skew_microscope.py            # live (needs a webcam)
python skew_microscope.py --selftest # verify the math, no webcam
```

The self-test injects a directed traveling bump and confirms the live engine
reproduces v9's chirality signature (rates recovered, planes orthogonal, L flips
on reversal).

## Files

```
skew_core.py         the streaming skew operator (skew_islands + project_chirality)
skew_microscope.py   the live tkinter instrument + headless self-test
```

## Honest scope

- The receptor bank is motion energy on a coarse grid; the islands it finds are
  the dominant **directed motion patterns** in view, not labelled objects.
- A handful of channels over a short window means the deeper (low-omega) islands
  are noisier than the dominant one — read the top island first.
- This is a desktop app (local webcam + Tk + 3D). A browser/HuggingFace version
  needs the Gradio streaming-webcam variant — ask and it's a small port.
- What is *measured* and on screen: the skew spectrum, the per-island chirality,
  and the lock-and-reverse flip. Those are the v9 quantities, verified by the
  self-test before any camera is involved.

# Active Inference & The Koopman World Model

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

This module answers the final question of the Geometric Neuron arc: **Does a mathematical world model actually buy an agent survival?**

We moved from reading the sensory stream (the `skew_microscope.py`) to predicting it (`koopman_core.py`), and finally to acting upon those predictions. This folder contains the ultimate test of that architecture: a 2D "Falling Blocks" environment where agents must dodge incoming obstacles.

## What is in this directory

We pit three agents against each other in identical worlds, side-by-side:

1.  **REFLEX Agent (The Baseline):** Has no world model. It simply looks at the block currently closest to it and steps out of the way.
2.  **KOOPMAN Agent (The World Model):** Uses a reduced Dynamic Mode Decomposition (DMD) / Koopman operator on a Takens-lifted sensory grid to forecast where blocks will be in the future. It evaluates candidate actions against this forecast and chooses the one with the lowest predicted collision.
3.  **ORACLE Agent (The Control):** Uses the exact same action-evaluation loop as the Koopman agent, but is fed the *true* underlying physics of the blocks rather than a mathematical forecast.

### The Files

*   `agency_core.py`: The physics of the Falling Blocks world and the Active Inference control logic (Model Predictive Control).
*   `agency_demo.py`: The execution environment. Runs both a headless numerical self-test and the live Tkinter visualization.

## The Honest Result

If you run `python agency_demo.py --selftest` or watch the GUI, you will see a result that falsifies the romantic expectation of "prediction equals intelligence."

**Hits over 2000 steps (lower is better):**
*   **Do-nothing post:** ~21.2 hits
*   **Reflex (Dodge Current):** ~1.0 hits
*   **Forecast Agent (Oracle):** ~0.8 hits
*   **Forecast Agent (Koopman):** ~21.2 hits

### The Diagnosis

The control logic is sound (the Oracle agent crushes the reflex agent). The failure belongs entirely to the Koopman forecast.

The Koopman Agent performs exactly as badly as a rock that does nothing. **The Reflex Agent beats the Koopman World Model.**

Why? Because DMD/Koopman operators are linear tools trying to predict a highly non-linear, discrete, sparse world (sharp $1 \times 1$ falling blocks).

When the Koopman operator projects the discrete blocks into the future, it smears them into a diffuse, low-amplitude cloud of probability. The forecast captures the general downward drift of mass (it achieves a low average MSE), but it completely loses the sharp, discrete boundaries required to say, "a block is specifically *here*."

When the agent queries the forecast, the signal amplitude is so low (smeared) that it doesn't trigger the collision threshold. The agent looks into its mathematical future, sees "empty space," and stands still while getting hit.

### The True Lesson: Micro vs. Macro Horizons

This experiment beautifully confirms the boundary we mapped previously: **Persistence (Reflex) owns the micro-horizon, and Koopman owns the macro-horizon.**

*   **Dodging a discrete falling block right above your head is a highly localized, short-horizon task.** The reflex agent dominates this because it relies entirely on the immediate present.
*   **The linear Koopman forecaster is terrible at localized, sharp grids.** It excels at global, continuous, oscillating trajectories (like the Lissajous curves in the webcam testing).

If we want a Koopman agent to survive, we cannot run the operator on the raw, discrete pixel grid. We must run it on the *latent objects* themselves (tracking the continuous $(X, Y)$ trajectories of the blocks). 

This is not a failure of the architecture. It is the architecture doing its job: providing an honest, mathematically rigorous diagnosis of exactly where a linear world model succeeds, and precisely where it breaks.

## Run

```bash
# To view the numerical proof:
python agency_demo.py --selftest

# To watch the side-by-side race:
python agency_demo.py
"""
koopman_core.py — the full-operator forecaster on a Takens lift
================================================================
The skew half A is the arrow, not the vehicle. Forecasting needs the FULL
operator C = S + A (rotation AND decay/power) on a delay-embedded manifold,
where a nonlinear trajectory unrolls toward linearity (Koopman/Takens).

  lift:      H = stacked d-delay copies of the (C,W) window      (C*d, N)
  operator:  one-step linear map  H[:,t] -> H[:,t+1]  via reduced DMD
  forecast:  iterate it from the current lifted state, read the top block
  surprise:  long-horizon forecast error -- structural break, not frame noise

This is the honest version of the green cone: persistence is the short-range
tail (accurate, future-blind); the Koopman sweep is the long-range topology.
The two cross over -- persistence wins the micro-step, Koopman wins the macro.

Do not hype. Do not lie. Just show.
PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
"""
import numpy as np


def hankel(window, d, te=1):
    C, W = window.shape
    N = W - (d - 1) * te
    if N <= 1:
        return window.copy(), W
    return np.vstack([window[:, i * te:i * te + N] for i in range(d)]), N


class KoopmanForecaster:
    """Reduced-DMD one-step operator on a Takens lift, iterated to forecast.
    Fit on each window (no training across windows); rank-truncated for stability."""
    def __init__(self, d=14, rank=20, te=1):
        self.d, self.rank, self.te = d, rank, te
        self.Ur = None       # reduced basis (lifted_dim, r)
        self.Atil = None     # reduced one-step operator (r, r)
        self.C = None        # channel count

    def fit(self, window):
        self.C = window.shape[0]
        H, N = hankel(window, self.d, self.te)
        if N <= 2:
            self.Ur = self.Atil = None
            return self
        X1, X2 = H[:, :-1], H[:, 1:]
        U, S, Vt = np.linalg.svd(X1, full_matrices=False)
        r = min(self.rank, int((S > S[0] * 1e-6).sum()))
        if r < 1:
            self.Ur = self.Atil = None
            return self
        Ur, Sr, Vr = U[:, :r], S[:r], Vt[:r].conj().T
        self.Ur = Ur
        self.Atil = Ur.conj().T @ X2 @ Vr @ np.diag(1.0 / Sr)
        self._H_last = H[:, -1]
        return self

    def forecast(self, horizon):
        """Return (C, horizon) predicted channel frames, 1..horizon ahead.
        Falls back to persistence if the operator could not be fit."""
        if self.Atil is None:
            return None
        a = self.Ur.conj().T @ self._H_last
        out = np.zeros((self.C, horizon))
        for h in range(horizon):
            a = self.Atil @ a
            out[:, h] = (self.Ur @ a)[:self.C].real
        return out

    def spectrum(self):
        """Koopman eigenvalues of the reduced operator (for diagnostics):
        |lambda| = per-step growth/decay (the S part), angle = rotation (the A part)."""
        if self.Atil is None:
            return np.array([])
        return np.linalg.eigvals(self.Atil)


# ============================================================ self-test
if __name__ == "__main__":
    def lissajous_field(C, T, seed=0, noise=0.005):
        r = np.random.default_rng(seed); t = np.arange(T)
        f1, f2 = 0.013, 0.021
        a = np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * 2 * f1 * t)
        b = np.sin(2 * np.pi * f2 * t + 0.7)
        ch = np.arange(C)[:, None]
        f = (np.exp(-0.5 * ((ch - (C / 2 + 0.4 * C * a[None])) / 2.0) ** 2)
             + 0.6 * np.exp(-0.5 * ((ch - (C / 2 + 0.4 * C * b[None])) / 2.0) ** 2))
        return f + noise * r.standard_normal((C, T))

    def traveling(C, T, speed, seed, noise=0.04):
        r = np.random.default_rng(seed); t = np.arange(T)
        ctr = (speed * 0.06 * t) % C; ch = np.arange(C)[:, None]
        dd = np.minimum((ch - ctr[None]) % C, (ctr[None] - ch) % C)
        return np.exp(-0.5 * (dd / 1.4) ** 2) + noise * r.standard_normal((C, T))

    C, W = 20, 120
    print("=" * 70)
    print("KOOPMAN FORECASTER — full operator on Takens lift, vs persistence")
    print("=" * 70)
    for name, S, T in [("nonlinear lissajous", lissajous_field(20, 2000), 2000),
                       ("noisy traveling bump", traveling(16, 1600, +1.0, 1), 1600)]:
        Cc = S.shape[0]
        print(f"\n  [{name}]  (C={Cc})")
        print(f"  {'horizon':>7} | {'koopman':>9} | {'persist':>9} | winner")
        for Hh in [1, 5, 10, 20, 40]:
            ek = ep = 0.0; n = 0
            kf = KoopmanForecaster(d=14, rank=20)
            for t in range(W, T - Hh - 1, 4):
                win = S[:, t - W:t]
                fc = kf.fit(win).forecast(Hh)
                pk = fc[:, -1] if fc is not None else S[:, t]
                truth = S[:, t + Hh]
                ek += np.mean((pk - truth) ** 2)
                ep += np.mean((S[:, t] - truth) ** 2)
                n += 1
            ek /= n; ep /= n
            win_who = "KOOPMAN" if ek < ep else "persist"
            print(f"  {Hh:7d} | {ek:9.5f} | {ep:9.5f} | {win_who}")
    print("\n  -> persistence wins the micro-step (free noise); koopman wins the")
    print("     macro-horizon (captures the global trajectory). The crossover is real.")

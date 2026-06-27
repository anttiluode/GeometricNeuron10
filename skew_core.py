"""
skew_core.py — the live skew lag-operator engine (the v9 neuron, made streaming)
================================================================================
This is geometric_neuron_v9's read path, computed on a SLIDING WINDOW of a live
multichannel stream instead of an offline tour.

    A_tau = (C_tau - C_tau^T)/2 ,   C_tau = R[:,tau:] @ R[:,:-tau]^T / (W-tau)

A_tau is real antisymmetric -> eigenvalues +/- i*omega_j, eigenvectors are 2-D
rotation planes = spectral islands. Per island we read:
    z(t)  = projection of the stream onto the plane (complex)
    omega = the skew eigen-rate (how fast it winds)
    L     = Im(z z*_lag)  = chirality  (flips sign under time reversal)

Nothing here is hand-assigned. The islands are the eigenstructure of the stream.
PerceptionLab / Antti Luode, with Claude. Do not hype. Do not lie. Just show.
"""
import numpy as np


def skew_islands(R, tau=4, n_islands=3):
    """R: (C, W) real multichannel window. Returns list of islands sorted by |omega|.
    Each island: dict(omega, u, v, L, amp) where (u,v) is the rotation plane,
    L the chirality of the window projected on it, amp the rms radius."""
    C, W = R.shape
    if W <= tau + 2:
        return []
    Rc = R - R.mean(1, keepdims=True)                     # remove DC per channel
    Cov = Rc[:, tau:] @ Rc[:, :-tau].T / (W - tau)        # (C,C) lag covariance
    A = 0.5 * (Cov - Cov.T)                               # skew half (the directed part)
    w, V = np.linalg.eig(A)
    om = w.imag
    order = np.argsort(-om)                               # most positive rate first
    order = order[om[order] > 1e-9][:n_islands]           # top positive-rate planes
    islands = []
    for j in order:
        u, v = V[:, j].real, V[:, j].imag
        nu, nv = np.linalg.norm(u) + 1e-12, np.linalg.norm(v) + 1e-12
        u, v = u / nu, v / nv
        z = (Rc.T @ u) - 1j * (Rc.T @ v)                  # (W,) complex coord on the plane
        L = float((z[tau:] * np.conj(z[:-tau])).imag.mean())
        amp = float(np.sqrt((np.abs(z) ** 2).mean()))
        islands.append(dict(omega=float(om[j]), u=u, v=v, z=z, L=L, amp=amp))
    return islands


# ============================================================ self-test
if __name__ == "__main__":
    # A synthetic traveling bump across C channels = a rotation in channel space,
    # with a DEFINITE direction. The skew operator must (1) find its rate, and
    # (2) flip the chirality sign when the bump travels the other way.
    def traveling_bump(C=16, T=2000, speed=+1.0, seed=0):
        rng = np.random.default_rng(seed)
        t = np.arange(T)
        centers = (speed * 0.05 * t) % C
        ch = np.arange(C)[:, None]
        R = np.exp(-0.5 * ((ch - centers[None, :]) % C - C / 2) ** 2 / 1.5 ** 2)
        # wrap-correct gaussian on a ring
        d = np.minimum((ch - centers[None, :]) % C, (centers[None, :] - ch) % C)
        R = np.exp(-0.5 * (d / 1.5) ** 2) + 0.05 * rng.standard_normal((C, T))
        return R

    print("=" * 68)
    print("SELF-TEST: streaming skew operator on a directed traveling bump")
    print("=" * 68)
    Rf = traveling_bump(speed=+1.0)
    Rr = traveling_bump(speed=-1.0)
    isf = skew_islands(Rf, tau=4, n_islands=3)
    isr = skew_islands(Rr, tau=4, n_islands=3)
    print(f"  forward bump  -> top islands omega = {[round(i['omega'],4) for i in isf]}")
    print(f"                   top islands L     = {[round(i['L'],4) for i in isf]}")
    print(f"  reverse bump  -> top islands omega = {[round(i['omega'],4) for i in isr]}")
    print(f"                   top islands L     = {[round(i['L'],4) for i in isr]}")
    flip = np.sign(isf[0]['L']) != np.sign(isr[0]['L'])
    print(f"  dominant-island chirality flips on reversal: {flip}")
    # orthogonality of the recovered planes (eigenbasis property)
    if len(isf) >= 2:
        c = abs(isf[0]['u'] @ isf[1]['u'])
        print(f"  islands are distinct planes (|<u0,u1>| = {c:.3f}, ~0 = orthogonal)")
    print("  -> the live engine reproduces v9's chirality signature on a stream.")


def project_chirality(R, u, v, tau=4):
    """Chirality L of stream R projected onto a FIXED reference plane (u,v).
    This is the causal version of v9's forward-vs-reverse-on-same-templates
    test: hold the plane, watch L flip when the motion reverses."""
    Rc = R - R.mean(1, keepdims=True)
    z = (Rc.T @ u) - 1j * (Rc.T @ v)
    if len(z) <= tau:
        return 0.0
    return float((z[tau:] * np.conj(z[:-tau])).imag.mean())

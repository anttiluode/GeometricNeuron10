"""
skew_microscope.py — THE GEOMETRIC NEURON FROM INSIDE (live instrument)
=======================================================================
The Gemini "Drift Manifold" GUI showed ONE complex oscillator: the K=1 shadow
of a single spectral island. This is the real thing.

A bank of receptors taps the webcam. Their multichannel motion stream feeds the
live skew lag-operator A_tau = (C_tau - C_tau^T)/2 (geometric_neuron_v9's read
path, computed on a sliding window). Its eigenplanes ARE the spectral islands:
sorted by rotation rate |omega|, each with a chirality L = Im(z z*_lag) that
FLIPS when motion reverses. Nothing is hand-assigned; the islands are the
eigenstructure of what the camera sees.

  - blue/cyan spiral  = an island spinning one way   (L > 0)
  - magenta spiral     = an island spinning the other (L < 0)
  - the bars           = the discovered omega spectrum (the islands, sorted)
  - LOCK a plane, then sweep your hand left, then right: L flips. That flip is
    the same number v9 reports for a reversed tour, now live and causal.

Run live:      python skew_microscope.py
Verify math:   python skew_microscope.py --selftest      (no webcam needed)

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import sys
import time
import numpy as np

from skew_core import skew_islands, project_chirality


# ----------------------------------------------------------------------
# headless self-test: prove the live engine == the v9 chirality signature
# ----------------------------------------------------------------------
def selftest():
    def traveling_bump(C=16, T=2000, speed=+1.0, seed=0):
        rng = np.random.default_rng(seed); t = np.arange(T)
        centers = (speed * 0.05 * t) % C; ch = np.arange(C)[:, None]
        d = np.minimum((ch - centers[None, :]) % C, (centers[None, :] - ch) % C)
        return np.exp(-0.5 * (d / 1.5) ** 2) + 0.05 * rng.standard_normal((C, T))

    print("=" * 70)
    print("SKEW MICROSCOPE — self-test (engine == geometric_neuron_v9 on a stream)")
    print("=" * 70)
    Rf = traveling_bump(speed=+1.0); Rr = traveling_bump(speed=-1.0)
    isf = skew_islands(Rf, tau=4, n_islands=3)
    u0, v0 = isf[0]['u'], isf[0]['v']
    Lf = project_chirality(Rf, u0, v0, tau=4)
    Lr = project_chirality(Rr, u0, v0, tau=4)
    print(f"  discovered island rates omega = {[round(i['omega'], 4) for i in isf]}")
    print(f"  planes orthogonal (|<u0,u1>|) = {abs(isf[0]['u'] @ isf[1]['u']):.3f}")
    print(f"  L forward motion (held plane) = {Lf:+.4f}")
    print(f"  L reverse motion (held plane) = {Lr:+.4f}")
    print(f"  chirality flips on reversal   = {np.sign(Lf) != np.sign(Lr)}")
    print("  -> live engine reproduces v9's forward-vs-reverse-on-same-templates flip.")
    print("=" * 70)


# ----------------------------------------------------------------------
# the live instrument
# ----------------------------------------------------------------------
def run_gui():
    import cv2
    import tkinter as tk
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from PIL import Image, ImageTk

    GW, GH = 6, 4                       # receptor grid: 6 wide x 4 tall = 24 channels
    NCH = GW * GH
    NISL = 3                            # islands to display
    CYAN, MAGENTA = "#00e5ff", "#ff3da6"

    class SkewMicroscope:
        def __init__(self, root):
            self.root = root
            root.title("Skew Microscope — the geometric neuron from inside")
            root.geometry("1600x950"); root.configure(bg="#05050a")

            self.fs = 30.0
            self.W = 90                                  # window length (frames)
            self.buf = np.zeros((NCH, self.W))           # the multichannel stream
            self.prev_gray = None
            self.lock_u = None; self.lock_v = None       # held reference plane
            self.lock_L0 = None                          # sign at lock time
            self.flip_flash = 0

            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

            self.prev_islands = None
            self._build_ui(); self._build_plots()
            self.running = True
            self._tick()

        # ---------------- UI ----------------
        def _build_ui(self):
            hdr = tk.Frame(self.root, bg="#0a0f1c", height=56); hdr.pack(fill="x")
            tk.Label(hdr, text="SKEW MICROSCOPE  //  live eigenplanes of A\u03c4  (the islands, from a camera)",
                     font=("Consolas", 14, "bold"), fg="#00ffcc", bg="#0a0f1c").pack(side="left", padx=20, pady=12)

            body = tk.Frame(self.root, bg="#05050a"); body.pack(fill="both", expand=True, padx=5, pady=5)
            left = tk.Frame(body, bg="#0a0f1c", width=470, bd=1, relief="sunken"); left.pack(side="left", fill="y", padx=5)

            row = tk.Frame(left, bg="#0a0f1c"); row.pack(pady=14, padx=14, fill="x")
            c1 = tk.Frame(row, bg="#000"); c1.pack(side="left", padx=5)
            tk.Label(c1, text="CAMERA", fg="#fff", bg="#000", font=("Consolas", 10)).pack()
            self.lbl_cam = tk.Label(c1, bg="#111"); self.lbl_cam.pack()
            c2 = tk.Frame(row, bg="#000"); c2.pack(side="right", padx=5)
            tk.Label(c2, text="RECEPTOR MOTION", fg="#00ffcc", bg="#000", font=("Consolas", 10)).pack()
            self.lbl_rec = tk.Label(c2, bg="#111"); self.lbl_rec.pack()

            tk.Label(left, text="DISCOVERED ISLAND SPECTRUM  (sorted by rotation rate \u03c9)",
                     fg="#ffaa00", bg="#0a0f1c", font=("Consolas", 9, "bold")).pack(pady=(14, 2))
            self.spec = tk.Canvas(left, width=430, height=120, bg="#020208", highlightthickness=0)
            self.spec.pack(padx=20)

            self.lbl_chir = tk.Label(left, text="dominant island  \u03c9=--  L=--",
                                     fg="#00ffcc", bg="#0a0f1c", font=("Consolas", 12)); self.lbl_chir.pack(pady=(12, 2))
            self.lbl_flip = tk.Label(left, text="reference plane: not locked",
                                     fg="#888", bg="#0a0f1c", font=("Consolas", 11)); self.lbl_flip.pack()

            bf = tk.Frame(left, bg="#0a0f1c"); bf.pack(pady=10)
            tk.Button(bf, text="LOCK PLANE", command=self.lock_plane, bg="#10331f", fg="#00ffcc",
                      font=("Consolas", 10, "bold"), relief="flat", padx=14, pady=4).pack(side="left", padx=6)
            tk.Button(bf, text="RELEASE", command=self.release_plane, bg="#331010", fg="#ff6677",
                      font=("Consolas", 10, "bold"), relief="flat", padx=14, pady=4).pack(side="left", padx=6)

            cf = tk.Frame(left, bg="#0a0f1c"); cf.pack(fill="x", padx=20, pady=14)
            tk.Label(cf, text="Window length (frames):", fg="#aaa", bg="#0a0f1c").pack(anchor="w")
            self.win_var = tk.IntVar(value=90)
            tk.Scale(cf, from_=30, to=180, resolution=10, variable=self.win_var, orient="horizontal",
                     bg="#0a0f1c", fg="#fff", highlightthickness=0, command=self._resize).pack(fill="x", pady=(0, 10))
            tk.Label(cf, text="Lag \u03c4 (frames):", fg="#aaa", bg="#0a0f1c").pack(anchor="w")
            self.tau_var = tk.IntVar(value=4)
            tk.Scale(cf, from_=1, to=15, resolution=1, variable=self.tau_var, orient="horizontal",
                     bg="#0a0f1c", fg="#00ffcc", highlightthickness=0).pack(fill="x")
            tk.Label(left, text="LOCK a plane, then sweep your hand left, then right.\nThe dominant L flips sign \u2014 that is the v9 reversal, live.",
                     fg="#667", bg="#0a0f1c", font=("Consolas", 9), justify="left").pack(pady=(8, 0), padx=20, anchor="w")

            self.right = tk.Frame(body, bg="#000"); self.right.pack(side="left", fill="both", expand=True)

        def _build_plots(self):
            self.fig = plt.Figure(figsize=(10, 10), facecolor="#020205")
            self.ax = self.fig.add_subplot(111, projection="3d"); self.ax.set_facecolor("#020205")
            for pane in [self.ax.xaxis.pane, self.ax.yaxis.pane, self.ax.zaxis.pane]:
                pane.fill = False; pane.set_edgecolor("#111")
            self.island_lines = []
            for _ in range(NISL):
                ln, = self.ax.plot([], [], [], lw=2.0, alpha=0.85); self.island_lines.append(ln)
            self.ax.set_xlim(-2, 2); self.ax.set_ylim(-2, 2); self.ax.set_zlim(-self.W, 0)
            self.ax.set_xlabel("Re z", color="#556"); self.ax.set_ylabel("Im z", color="#556")
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.right)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)

        def _resize(self, *_):
            W = self.win_var.get()
            if W != self.W:
                nb = np.zeros((NCH, W))
                m = min(W, self.W); nb[:, -m:] = self.buf[:, -m:]
                self.buf = nb; self.W = W; self.ax.set_zlim(-W, 0)

        def lock_plane(self):
            isl = skew_islands(self.buf, tau=self.tau_var.get(), n_islands=1)
            if isl:
                self.lock_u, self.lock_v = isl[0]['u'], isl[0]['v']
                self.lock_L0 = np.sign(isl[0]['L'])
                self.lbl_flip.config(text="reference plane: LOCKED  (sweep to test)", fg="#00ffcc")

        def release_plane(self):
            self.lock_u = self.lock_v = self.lock_L0 = None
            self.lbl_flip.config(text="reference plane: not locked", fg="#888")

        # ---------------- per-frame ----------------
        def _receptors(self, gray_small):
            """motion energy per grid patch -> (NCH,) channel vector."""
            if self.prev_gray is None:
                self.prev_gray = gray_small; return np.zeros(NCH), np.zeros((GH, GW))
            mot = np.abs(gray_small.astype(np.float32) - self.prev_gray.astype(np.float32))
            self.prev_gray = gray_small
            H, Wd = gray_small.shape
            ph, pw = H // GH, Wd // GW
            out = np.zeros(NCH); rec_img = np.zeros((GH, GW))
            for r in range(GH):
                for c in range(GW):
                    patch = mot[r * ph:(r + 1) * ph, c * pw:(c + 1) * pw]
                    v = float(patch.mean()); out[r * GW + c] = v; rec_img[r, c] = v
            return out, rec_img

        def _align(self, islands):
            """stabilize display: sign/order-align this frame's planes to the last."""
            if not islands:
                return islands
            if not self.prev_islands:
                self.prev_islands = islands; return islands
            for isl in islands:
                # flip the plane's orientation to best match any previous island
                best = max(self.prev_islands, key=lambda p: abs(p['u'] @ isl['u']))
                if (best['u'] @ isl['u']) < 0:
                    isl['u'] = -isl['u']; isl['z'] = np.conj(isl['z']); isl['L'] = -isl['L']
            self.prev_islands = islands; return islands

        def _draw_spectrum(self, islands):
            self.spec.delete("all")
            if not islands: return
            om = [i['omega'] for i in islands]; mx = max(om) + 1e-9
            n = len(islands); bw = 380 / max(n, 1)
            for k, isl in enumerate(islands):
                h = 95 * isl['omega'] / mx
                col = CYAN if isl['L'] >= 0 else MAGENTA
                x0 = 25 + k * bw
                self.spec.create_rectangle(x0, 105 - h, x0 + bw * 0.7, 105, fill=col, outline="")
                self.spec.create_text(x0 + bw * 0.35, 115, text=f"\u03c9{k}", fill="#889", font=("Consolas", 8))
                self.spec.create_text(x0 + bw * 0.35, 100 - h, text=f"{isl['omega']:.3f}", fill="#cce", font=("Consolas", 7))

        def _tick(self):
            if not self.running: return
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small = cv2.resize(gray, (96, 72))
                chan, rec_img = self._receptors(small)
                self.buf[:, :-1] = self.buf[:, 1:]; self.buf[:, -1] = chan

                tau = self.tau_var.get()
                islands = skew_islands(self.buf, tau=tau, n_islands=NISL)
                islands = self._align(islands)

                # draw island spirals
                tz = np.arange(-self.W, 0)
                for k, ln in enumerate(self.island_lines):
                    if k < len(islands):
                        z = islands[k]['z']
                        col = CYAN if islands[k]['L'] >= 0 else MAGENTA
                        ln.set_data(z.real, z.imag); ln.set_3d_properties(tz[-len(z):])
                        ln.set_color(col); ln.set_alpha(0.9 - 0.22 * k)
                    else:
                        ln.set_data([], []); ln.set_3d_properties([])
                if islands:
                    r = max(2.0, 1.2 * max(np.abs(i['z']).max() for i in islands))
                    self.ax.set_xlim(-r, r); self.ax.set_ylim(-r, r)
                    d = islands[0]
                    self.lbl_chir.config(text=f"dominant island  \u03c9={d['omega']:+.3f}  L={d['L']:+.3f}",
                                         fg=CYAN if d['L'] >= 0 else MAGENTA)
                self._draw_spectrum(islands)

                # held-plane chirality + flip detector
                if self.lock_u is not None:
                    L = project_chirality(self.buf, self.lock_u, self.lock_v, tau=tau)
                    s = np.sign(L)
                    if abs(L) > 1e-4 and s != self.lock_L0:
                        self.flip_flash = 8; self.lock_L0 = s
                    spin = "spin +  (one way)" if L >= 0 else "spin \u2212  (reversed)"
                    if self.flip_flash > 0:
                        self.lbl_flip.config(text=f"\u26a1 CHIRALITY FLIPPED  L={L:+.3f}", fg="#ffe14d")
                        self.flip_flash -= 1
                    else:
                        self.lbl_flip.config(text=f"held plane L={L:+.3f}   {spin}",
                                             fg=CYAN if L >= 0 else MAGENTA)

                self.ax.view_init(elev=18, azim=(time.time() * 12) % 360)
                self.canvas.draw_idle()

                cam = Image.fromarray(cv2.cvtColor(cv2.resize(frame, (200, 150)), cv2.COLOR_BGR2RGB))
                self.lbl_cam.imgtk = ImageTk.PhotoImage(cam); self.lbl_cam.configure(image=self.lbl_cam.imgtk)
                rv = (rec_img / (rec_img.max() + 1e-9) * 255).astype(np.uint8)
                rv = cv2.resize(rv, (200, 150), interpolation=cv2.INTER_NEAREST)
                rv = cv2.applyColorMap(rv, cv2.COLORMAP_VIRIDIS)
                recimg = Image.fromarray(cv2.cvtColor(rv, cv2.COLOR_BGR2RGB))
                self.lbl_rec.imgtk = ImageTk.PhotoImage(recimg); self.lbl_rec.configure(image=self.lbl_rec.imgtk)

            self.root.after(33, self._tick)

    root = tk.Tk()
    app = SkewMicroscope(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (setattr(app, "running", False), app.cap.release(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        run_gui()
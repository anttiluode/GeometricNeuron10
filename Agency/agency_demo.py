"""
agency_demo.py — does the forecast buy survival? (the honest falling-blocks test)
=================================================================================
Three agents share identical falling-block worlds, side by side:
  REFLEX   : dodges the current nearest block. No world model.
  KOOPMAN  : active inference on the S+A forecast (the 'intelligence' candidate).
  ORACLE   : same control loop, fed the TRUE block physics (control-logic check).

Live hit counters. The point is not a pretty dodge demo -- it is to SEE which
architecture actually survives, including the chance that the fancy one does not.

Headless summary first:  python agency_demo.py --selftest
Live race:               python agency_demo.py

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import sys
import numpy as np
from agency_core import FallingBlocks, reflex_action, forecast_action
from koopman_core import KoopmanForecaster


def make_agent(kind, world):
    Wn = world.H * world.W
    state = {"koop": KoopmanForecaster(d=6, rank=16), "hist": np.zeros((Wn, 60))}
    def act():
        g = world.grid().flatten()
        state["hist"][:, :-1] = state["hist"][:, 1:]; state["hist"][:, -1] = g
        if kind == "reflex":
            return reflex_action(world)
        if kind == "oracle":
            return forecast_action(world, horizon=12, use_truth=True)
        state["koop"].fit(state["hist"])
        return forecast_action(world, horizon=12, koop=state["koop"])
    return act


def selftest():
    from agency_core import run_episode
    print("=" * 64)
    print("AGENCY — hits over 2000 steps (lower survives better), 6 seeds")
    print("=" * 64)
    def avg(fn, **kw):
        hs = [run_episode(fn, steps=2000, seed=s, **kw) for s in range(6)]
        return np.mean(hs), np.std(hs)
    for name, fn, kw in [("reflex", reflex_action, {}),
                         ("koopman forecast", forecast_action, {"use_truth": False}),
                         ("oracle forecast", forecast_action, {"use_truth": True}),
                         ("do-nothing", "nothing", {})]:
        m, s = avg(fn, **kw)
        print(f"  {name:20s}: {m:6.1f} +/- {s:4.1f} hits")
    print("\n  Read it straight: if Koopman ~ do-nothing and reflex ~ 1, the long-range")
    print("  forecast did NOT buy survival on this task -- the reflex wins. The forecast")
    print("  smears sparse blocks into a blur the agent can't localize. Honest result.")


def run_gui():
    import tkinter as tk
    CELL = 16
    KINDS = [("REFLEX", "reflex", "#88aaff"),
             ("KOOPMAN (world model)", "koopman", "#ffb020"),
             ("ORACLE (true physics)", "oracle", "#39ff88")]

    class Race:
        def __init__(self, root):
            self.root = root
            root.title("Agency — does the forecast buy survival?")
            root.configure(bg="#05050a")
            tk.Label(root, text="FALLING BLOCKS  //  reflex  vs  world-model forecast  vs  oracle",
                     font=("Consolas", 13, "bold"), fg="#00ffcc", bg="#0a0f1c").pack(fill="x", pady=8)
            self.worlds, self.agents, self.canvases, self.hits, self.labels = [], [], [], [], []
            body = tk.Frame(root, bg="#05050a"); body.pack(padx=10, pady=10)
            for i, (name, kind, col) in enumerate(KINDS):
                w = FallingBlocks(width=16, height=18, seed=7)
                self.worlds.append(w); self.agents.append(make_agent(kind, w)); self.hits.append(0)
                frame = tk.Frame(body, bg="#0a0f1c", bd=1, relief="sunken"); frame.pack(side="left", padx=8)
                tk.Label(frame, text=name, fg=col, bg="#0a0f1c", font=("Consolas", 10, "bold")).pack(pady=4)
                cv = tk.Canvas(frame, width=w.W * CELL, height=w.H * CELL, bg="#020208", highlightthickness=0)
                cv.pack(padx=6); self.canvases.append(cv)
                lb = tk.Label(frame, text="hits: 0", fg=col, bg="#0a0f1c", font=("Consolas", 12, "bold"))
                lb.pack(pady=4); self.labels.append(lb)
            self.col = [c for _, _, c in KINDS]
            self.running = True; self.tick()

        def tick(self):
            if not self.running: return
            for i, w in enumerate(self.worlds):
                a = self.agents[i]()
                _, hit = w.step(a)
                if hit: self.hits[i] += 1
                cv = self.canvases[i]; cv.delete("all")
                for col, row, _ in w.blocks:
                    r = int(round(row))
                    cv.create_rectangle(col * CELL, r * CELL, (col + 1) * CELL, (r + 1) * CELL,
                                        fill="#cc3344", outline="")
                cv.create_rectangle(w.agent * CELL, (w.H - 1) * CELL,
                                    (w.agent + 1) * CELL, w.H * CELL, fill=self.col[i], outline="")
                self.labels[i].config(text=f"hits: {self.hits[i]}")
            self.root.after(60, self.tick)

    root = tk.Tk()
    app = Race(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (setattr(app, "running", False), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        run_gui()

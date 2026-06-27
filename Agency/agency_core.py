"""
agency_core.py — active inference on the Koopman forecast (the observer gets a hand)
====================================================================================
The observer predicts the world (Koopman amber cone) and measures surprise. Agency
is closing that loop: simulate candidate ACTIONS, project each into the forecasted
future, and pick the action that minimizes PREDICTED collision (predicted surprise).

This is Model Predictive Control / active inference, stated minimally:
  world model:   where will the falling blocks be in 1..H steps?  (Koopman or truth)
  self model:    where will I be in 1..H steps under action a?    (left / stay / right)
  cost:          predicted collisions over the horizon
  act:           argmin_a cost(a)

The honest question this file answers with numbers, NOT assertion:
  Does the world-model agent survive longer than (1) a reflex that only dodges the
  CURRENT nearest block, (2) a random walker, (3) a do-nothing post? If it does not
  beat the reflex, the forecast bought nothing and the 'intelligence' claim fails.

Do not hype. Do not lie. Just show.
PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
"""
import numpy as np


class FallingBlocks:
    """A 1-D world: agent on a row of `width` cells at the bottom; blocks fall from
    the top at integer columns with per-block speeds. Hit = block reaches the agent
    row in the agent's column. The agent sees the whole grid (its 'webcam')."""
    def __init__(self, width=16, height=18, rate=0.18, seed=0):
        self.W, self.H, self.rate = width, height, rate
        self.rng = np.random.default_rng(seed)
        self.agent = width // 2
        self.blocks = []                  # list of [col, row, speed]
        self.t = 0

    def grid(self):
        g = np.zeros((self.H, self.W))
        for col, row, _ in self.blocks:
            r = int(round(row))
            if 0 <= r < self.H:
                g[r, int(col)] = 1.0
        return g

    def step(self, action):
        """action in {-1,0,+1}. Returns (grid, hit:bool)."""
        self.agent = int(np.clip(self.agent + action, 0, self.W - 1))
        for b in self.blocks:
            b[1] += b[2]
        # spawn
        if self.rng.random() < self.rate:
            col = int(self.rng.integers(0, self.W))
            speed = float(self.rng.uniform(0.5, 1.1))
            self.blocks.append([col, 0.0, speed])
        # collisions at the agent row (bottom)
        hit = False
        survivors = []
        for col, row, sp in self.blocks:
            if row >= self.H - 1:
                if int(col) == self.agent:
                    hit = True
                # block leaves the field
            else:
                survivors.append([col, row, sp])
        self.blocks = survivors
        self.t += 1
        return self.grid(), hit


# ---------------- agents ----------------
def reflex_action(world):
    """Dodge only the CURRENT lowest block if it's in/adjacent to the agent column.
    A pure reactive reflex -- no forecast."""
    if not world.blocks:
        return 0
    # nearest-to-bottom block
    col, row, sp = max(world.blocks, key=lambda b: b[1])
    dx = int(col) - world.agent
    if abs(dx) <= 1 and row > world.H * 0.5:
        # step away from it
        if dx == 0:
            return 1 if world.agent < world.W - 1 else -1
        return -1 if dx > 0 else 1
    return 0


def forecast_action(world, horizon=12, use_truth=False, koop=None, buf=None):
    """Active inference: for each candidate action, project the agent forward and
    project the WORLD forward; pick the action with the fewest predicted collisions.
    use_truth=True uses the real block physics (oracle forecast) to isolate the
    control logic from forecast quality. Otherwise uses the Koopman forecast `koop`
    fit on the grid history `buf`."""
    # predict world occupancy over the horizon: P[h] = set of (row,col) likely filled
    future_cols = []   # for each horizon step, list of columns at the bottom row
    if use_truth:
        for h in range(1, horizon + 1):
            cols_at_bottom = []
            for col, row, sp in world.blocks:
                fr = row + sp * h
                if world.H - 1.5 <= fr <= world.H - 0.5:
                    cols_at_bottom.append(int(col))
            future_cols.append(cols_at_bottom)
    else:
        # Koopman forecast of the grid; threshold to occupancy, read bottom row
        fc = koop.forecast(horizon) if koop is not None else None
        for h in range(horizon):
            if fc is None:
                future_cols.append([]); continue
            frame = fc[:, h]
            # frame is flattened grid (H*W,) -> reshape, read near-bottom rows
            g = frame.reshape(world.H, world.W)
            bottom = g[world.H - 2:, :].max(0)
            cols = list(np.where(bottom > 0.4)[0])
            future_cols.append(cols)

    best_a, best_cost = 0, np.inf
    for a in (-1, 0, 1):
        pos = int(np.clip(world.agent + a, 0, world.W - 1))
        cost = 0.0
        # agent moves toward target then holds; approximate its column over horizon
        for h, cols in enumerate(future_cols):
            # the agent can keep adjusting, but cost the immediate committed step most
            if pos in cols:
                cost += 1.0 / (1 + h)          # nearer collisions hurt more
        # tiny preference to not drift to walls / not move needlessly
        cost += 0.01 * abs(a)
        if cost < best_cost:
            best_cost, best_a = cost, a
    return best_a


def run_episode(agent_fn, steps=2000, seed=0, **kw):
    world = FallingBlocks(seed=seed)
    hits = 0
    from koopman_core import KoopmanForecaster
    koop = KoopmanForecaster(d=6, rank=16)
    Wn = world.H * world.W
    hist = np.zeros((Wn, 60))
    for t in range(steps):
        g = world.grid().flatten()
        hist[:, :-1] = hist[:, 1:]; hist[:, -1] = g
        if agent_fn is forecast_action and not kw.get("use_truth", False):
            koop.fit(hist)
            a = forecast_action(world, horizon=kw.get("horizon", 12), koop=koop)
        elif agent_fn is forecast_action:
            a = forecast_action(world, horizon=kw.get("horizon", 12), use_truth=True)
        elif agent_fn is reflex_action:
            a = reflex_action(world)
        elif agent_fn == "random":
            a = world.rng.integers(-1, 2)
        else:  # do nothing
            a = 0
        _, hit = world.step(a)
        if hit:
            hits += 1
    return hits


if __name__ == "__main__":
    N = 6; STEPS = 2000
    print("=" * 72)
    print("AGENCY HEAD-TO-HEAD — hits taken over 2000 steps (lower = survives better)")
    print("=" * 72)
    def avg(fn, **kw):
        hs = [run_episode(fn, steps=STEPS, seed=s, **kw) for s in range(N)]
        return np.mean(hs), np.std(hs)

    m_none, s_none = avg("nothing")
    m_rand, s_rand = avg("random")
    m_reflex, s_reflex = avg(reflex_action)
    m_oracle, s_oracle = avg(forecast_action, use_truth=True, horizon=12)
    m_koop, s_koop = avg(forecast_action, use_truth=False, horizon=12)

    print(f"  do-nothing post          : {m_none:6.1f} +/- {s_none:4.1f} hits")
    print(f"  random walker            : {m_rand:6.1f} +/- {s_rand:4.1f} hits")
    print(f"  reflex (dodge current)   : {m_reflex:6.1f} +/- {s_reflex:4.1f} hits")
    print(f"  forecast agent (Koopman) : {m_koop:6.1f} +/- {s_koop:4.1f} hits")
    print(f"  forecast agent (oracle)  : {m_oracle:6.1f} +/- {s_oracle:4.1f} hits")
    print("-" * 72)
    print(f"  reflex beats do-nothing  : {m_reflex < m_none}")
    print(f"  Koopman beats reflex     : {m_koop < m_reflex}  <-- did the FORECAST buy survival?")
    print(f"  oracle beats reflex      : {m_oracle < m_reflex}  <-- is the CONTROL logic sound?")

import collections
import math
import numpy as np


class FirstCrackPredictor:
    """Estimador IA ligero para pronosticar el primer crack.

    Usa un modelo de regresión lineal multivariable entrenado con datos
    sintéticos de tostiones y se recalibra con las observaciones reales que
    captura el usuario al marcar 1C. Los cálculos se realizan solo con NumPy
    para evitar dependencias pesadas."""

    def __init__(self, target_bt=196.0):
        self.target_bt = float(target_bt)
        self._weights = self._bootstrap_weights()
        self._observations = collections.deque(maxlen=240)
        self._last_prediction = None

    def _bootstrap_weights(self, roasts=420, samples_per_roast=22):
        rng = np.random.default_rng(42)
        feats = []
        targets = []
        for _ in range(roasts):
            fc_time = rng.uniform(390.0, 630.0)
            charge_bt = rng.uniform(150.0, 175.0)
            fc_bt = rng.uniform(self.target_bt - 2.0, self.target_bt + 4.0)
            tau = rng.uniform(70.0, 140.0)
            noise = rng.normal(0.0, 0.6, size=samples_per_roast)
            times = np.sort(rng.uniform(30.0, fc_time * 0.96, size=samples_per_roast))
            for idx, t in enumerate(times):
                bt = fc_bt - (fc_bt - charge_bt) * math.exp(-t / tau) + noise[idx]
                ror = (fc_bt - bt) / max(1e-3, fc_time - t) * 60.0
                ror = max(2.0, min(24.0, ror))
                feats.append([1.0, t, bt, ror, bt * ror])
                targets.append(fc_time - t)
        X = np.array(feats, dtype=float)
        y = np.array(targets, dtype=float)
        w, *_ = np.linalg.lstsq(X, y, rcond=None)
        return w

    def observe(self, t, bt, ror, capture=True):
        if not (math.isfinite(bt) and math.isfinite(ror)):
            return self._last_prediction
        feats = np.array([1.0, t, bt, ror, bt * ror], dtype=float)
        remaining = float(np.dot(self._weights, feats))
        remaining = max(0.0, min(900.0, remaining))
        prediction = (t + remaining, remaining)
        self._last_prediction = prediction
        if capture:
            self._observations.append((t, feats))
        return prediction

    def commit_first_crack(self, t_fc):
        if not self._observations:
            self._last_prediction = (t_fc, 0.0)
            return
        X = np.array([obs[1] for obs in self._observations], dtype=float)
        y = np.array([max(0.0, t_fc - obs[0]) for obs in self._observations], dtype=float)
        try:
            new_w, *_ = np.linalg.lstsq(X, y, rcond=None)
            self._weights = 0.7 * self._weights + 0.3 * new_w
        except Exception:
            pass
        self._observations.clear()
        self._last_prediction = (t_fc, 0.0)

    def reset(self):
        self._observations.clear()
        self._last_prediction = None

    @property
    def last_prediction(self):
        return self._last_prediction

    def set_target_bt(self, value):
        value = float(value)
        if math.isclose(value, self.target_bt, rel_tol=0.0, abs_tol=1e-3):
            self.target_bt = value
            return
        self.target_bt = value
        self._weights = self._bootstrap_weights()
        self.reset()


class RoastModel:
    def __init__(self, alpha=0.12, ror_window=9, first_crack_bt=196.0):
        self.alpha = float(alpha)
        self.bt_est = None
        self.t_hist = []
        self.et_hist = []
        self.bt_hist = []
        self.ror_hist = []
        self._w = max(5, (int(ror_window) // 2) * 2 + 1)
        self.fc_predictor = FirstCrackPredictor(target_bt=first_crack_bt)

    def _update_bt(self, et):
        if not math.isfinite(et):
            return float('nan') if self.bt_est is None else self.bt_est
        if self.bt_est is None or not math.isfinite(self.bt_est):
            self.bt_est = et * 0.85
        else:
            self.bt_est = self.bt_est + self.alpha * (et - self.bt_est)
        return self.bt_est

    def step(self, t, et):
        bt = self._update_bt(et)
        self.t_hist.append(t)
        self.et_hist.append(et)
        self.bt_hist.append(bt)
        ror = math.nan
        if len(self.bt_hist) >= 3:
            ror = (self.bt_hist[-1] - self.bt_hist[-3]) / (self.t_hist[-1] - self.t_hist[-3] + 1e-6) * 60.0
        self.ror_hist.append(ror)
        if len(self.ror_hist) >= self._w:
            self.ror_hist[-1] = float(np.nanmean(self.ror_hist[-self._w:]))
        self.fc_predictor.observe(t, bt, self.ror_hist[-1])
        return bt, self.ror_hist[-1], self.fc_predictor.last_prediction

    def update_idle(self, et, t=None):
        bt = self._update_bt(et)
        if t is not None and self.ror_hist:
            self.fc_predictor.observe(t, bt, self.ror_hist[-1], capture=False)
        return bt

    def reset(self):
        self.bt_est = None
        self.t_hist.clear()
        self.et_hist.clear()
        self.bt_hist.clear()
        self.ror_hist.clear()
        self.fc_predictor.reset()

    def eta_seconds(self, target_bt):
        """Tiempo estimado (s) para alcanzar target_bt por extrapolación lineal."""
        N = min(20, len(self.bt_hist))
        if N < 4:
            return None
        y = np.array(self.bt_hist[-N:])
        x = np.array(self.t_hist[-N:])
        A = np.vstack([x, np.ones_like(x)]).T
        try:
            a, b = np.linalg.lstsq(A, y, rcond=None)[0]
        except Exception:
            return None
        if abs(a) < 1e-6:
            return None
        t_hit = (target_bt - b) / a
        t_now = self.t_hist[-1]
        eta = t_hit - t_now
        if eta < 0 or eta > 3600:
            return None
        return float(eta)


def gas_air_suggestion(ror_now, ror_target, tol=0.4):
    import math as _math

    if ror_now is None or (_math.isnan(ror_now) if isinstance(ror_now, float) else False):
        return "—"
    if ror_now > ror_target + tol:
        return "Bajar GAS 1; revisar AIRE +1"
    if ror_now < ror_target - tol:
        return "Subir GAS 1; revisar AIRE -1"
    return "Mantener"

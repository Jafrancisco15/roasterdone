import numpy as np
import math

def et_to_bt_target(et_c: float) -> float:
    """Map ET->BT target using a simple two-point calibration.
    Passes through (ET=25°C -> BT=25°C) to keep ambient aligned,
    and (ET=125°C -> BT=195°C) per user's data.
    Result is clipped to a sane range [0, 300] °C.
    """
    try:
        et = float(et_c)
    except Exception:
        return float('nan')
    m = (195.0 - 25.0) / (125.0 - 25.0)  # 1.7
    b = 25.0 - m*25.0                     # -17.5
    bt = m*et + b
    # Clip to reasonable roasting temps
    if bt < 0.0: bt = 0.0
    if bt > 300.0: bt = 300.0
    return bt

class RoastModel:

    def __init__(self, alpha=0.12, ror_window=9):
        self.alpha=float(alpha); self.bt_est=None
        self.t_hist=[]; self.et_hist=[]; self.bt_hist=[]; self.ror_hist=[]
        self._w = max(5, (int(ror_window)//2)*2+1)

    def step(self, t, et):
        target_bt = et_to_bt_target(et)
        if self.bt_est is None:
            self.bt_est = target_bt
        else:
            self.bt_est = self.bt_est + self.alpha*(target_bt - self.bt_est)
        self.t_hist.append(t); self.et_hist.append(et); self.bt_hist.append(self.bt_est)
        ror = math.nan
        if len(self.bt_hist)>=3:
            ror = (self.bt_hist[-1]-self.bt_hist[-3])/(self.t_hist[-1]-self.t_hist[-3]+1e-6)*60.0
        self.ror_hist.append(ror)
        if len(self.ror_hist)>=self._w:
            self.ror_hist[-1] = float(np.nanmean(self.ror_hist[-self._w:]))
        return self.bt_est, self.ror_hist[-1]

    def reset(self):
        self.bt_est=None; self.t_hist.clear(); self.et_hist.clear(); self.bt_hist.clear(); self.ror_hist.clear()

    def eta_seconds(self, target_bt):
        """Tiempo estimado (s) para alcanzar target_bt por extrapolación lineal
        usando las últimas N muestras. Retorna None si no hay base."""
        N = min(20, len(self.bt_hist))
        if N < 4: 
            return None
        y = np.array(self.bt_hist[-N:])
        x = np.array(self.t_hist[-N:])
        # Ajuste lineal: y = a*x + b
        A = np.vstack([x, np.ones_like(x)]).T
        try:
            a,b = np.linalg.lstsq(A, y, rcond=None)[0]
        except Exception:
            return None
        if abs(a) < 1e-6:
            return None
        t_hit = (target_bt - b) / a
        t_now = self.t_hist[-1]
        eta = t_hit - t_now
        if eta < 0 or eta > 3600:  # 1h cap
            return None
        return float(eta)

def gas_air_suggestion(ror_now, ror_target, tol=0.4):
    import math
    if ror_now is None or (isinstance(ror_now,float) and math.isnan(ror_now)): return "—"
    if ror_now>ror_target+tol: return "Bajar GAS 1; revisar AIRE +1"
    if ror_now<ror_target-tol: return "Subir GAS 1; revisar AIRE -1"
    return "Mantener"

    def predict_first_crack_info(self, target_bt=196.0):
        """
        Lightweight 'ML' prediction using a rolling linear regression on BT vs time
        to estimate when BT will hit target_bt. Returns a dict with:
        {"eta_sec": seconds_until, "pred_time_sec": absolute_time_at_hit, "target_bt": target_bt}
        """
        if len(self.t_hist) < 6 or len(self.bt_hist) < 6:
            return {"eta_sec": None, "pred_time_sec": None, "target_bt": float(target_bt)}
        # Use last ~30s of data (assuming ~2Hz -> 60 samples)
        n = min(60, len(self.t_hist))
        t = np.array(self.t_hist[-n:], dtype=float)
        y = np.array(self.bt_hist[-n:], dtype=float)
        # Linear regression y = a*t + b
        try:
            a, b = np.polyfit(t, y, 1)
            if abs(a) < 1e-6:
                return {"eta_sec": None, "pred_time_sec": None, "target_bt": float(target_bt)}
            t_hit = (target_bt - b) / a
            t_now = self.t_hist[-1]
            eta = t_hit - t_now
            if eta < 0 or eta > 3600:
                return {"eta_sec": None, "pred_time_sec": None, "target_bt": float(target_bt)}
            return {"eta_sec": float(eta), "pred_time_sec": float(t_hit), "target_bt": float(target_bt)}
        except Exception:
            return {"eta_sec": None, "pred_time_sec": None, "target_bt": float(target_bt)}

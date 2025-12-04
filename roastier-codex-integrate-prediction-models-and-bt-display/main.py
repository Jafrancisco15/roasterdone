\
import math
import os, time, json, tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import traceback

from phidget_reader import ETReader
from model import RoastModel, gas_air_suggestion
from storage import export_session_csv, timestamp_slug

APPNAME="RoastLab"
BG="#0c1118"; FG="#e6edf3"; GLASS="#111827"; GRID="#1f2a37"; ACC="#38bdf8"

def load_cfg():
    cfg={"offset_c":0.0,"scale_pct":100.0,"sample_hz":2.0,"phidget_serial":""}
    if os.path.exists("config.json"):
        try:
            data=json.load(open("config.json","r",encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update(data)
        except Exception:
            pass
    return cfg

CFG = load_cfg()

class S:
    running=False; t0=None
    samples=[]; events=[]; gas=5; air=5; set_temp=0
    meta={"origin":"","density":"","moisture":"","charge_mass_g":"","process":"lavado","brewTarget":"espresso"}
    reader=None; model=None
    ch=0; tc="K"; force_sim=False; force_phidget=False
    input_is_f=False
    show_f=False

def apply_cal(et_c):
    et = (et_c * (CFG["scale_pct"]/100.0)) + CFG["offset_c"]
    return et

serial_cfg = CFG.get("phidget_serial") or os.environ.get("PHIDGET_1048_SERIAL")
S.reader = ETReader(sample_hz=CFG["sample_hz"], channel=S.ch, thermocouple_type=S.tc,
                    force_sim=S.force_sim, force_phidget=S.force_phidget,
                    device_serial=serial_cfg)
S.model = RoastModel(alpha=0.12)

def style_root(root):
    root.title(APPNAME)
    root.configure(bg=BG)
    st=ttk.Style(root); st.theme_use("clam")
    st.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
    st.configure("TFrame", background=BG)
    st.configure("TButton", background=GLASS, foreground=FG, borderwidth=0, padding=8, font=("Segoe UI Semibold", 10))
    st.map("TButton", background=[('active','#1b2430')])
    st.configure("TEntry", fieldbackground="#0f1621", foreground=FG, insertcolor=FG)
    st.configure("TSpinbox", fieldbackground="#0f1621", foreground=FG, arrowsize=14)
    st.configure("TCombobox", fieldbackground="#0f1621", foreground=FG)
root=tk.Tk(); style_root(root)

# ======= TOP BAR =======
top=ttk.Frame(root); top.pack(fill="x", padx=12, pady=8)
status=tk.Canvas(top,width=14,height=14,highlightthickness=0,bg=BG); status.pack(side="left")
DOT=status.create_oval(1,1,13,13,fill="#ef4444",outline="")
RUNVAR=tk.StringVar(value="RUN: False"); ttk.Label(top,textvariable=RUNVAR).pack(side="left", padx=(4,10))

BTVAR=tk.StringVar(value="BT —.— °C")
ETVAR=tk.StringVar(value="ET —.— °C")
ttk.Label(top,textvariable=ETVAR,font=("Segoe UI",20,"bold")).pack(side="left",padx=10)
ttk.Label(top,textvariable=BTVAR,font=("Segoe UI",20,"bold")).pack(side="left",padx=10)
src_var=tk.StringVar(value="Fuente: —")
ttk.Label(top,textvariable=src_var).pack(side="left", padx=(10,0))
raw_var=tk.StringVar(value="RAW: —  |  FILT: —"); ttk.Label(top,textvariable=raw_var).pack(side="left", padx=(10,0))
count_var=tk.StringVar(value="Muestras: 0"); ttk.Label(top,textvariable=count_var).pack(side="left", padx=(10,0))

# Device config minimal
ttk.Label(top,text="Canal").pack(side="left",padx=(12,4))
spin_ch=ttk.Spinbox(top,from_=0,to=3,width=4); spin_ch.set(S.ch); spin_ch.pack(side="left")
ttk.Label(top,text="TC").pack(side="left",padx=(8,4))
tc=ttk.Combobox(top, values=["K","J","E","T","N","S","R","B"], width=4); tc.set(S.tc); tc.pack(side="left")
serial_var=tk.StringVar(value=str(CFG.get("phidget_serial","")))
ttk.Label(top,text="Serial").pack(side="left",padx=(8,4))
serial_entry=ttk.Entry(top,textvariable=serial_var,width=12)
serial_entry.pack(side="left")

# Simulator + Units + Force Phidget
sim_var=tk.BooleanVar(value=S.force_sim)
chk_sim=ttk.Checkbutton(top, text="Simulador", variable=sim_var)
chk_sim.pack(side="left", padx=(12,4))
inputf_var=tk.BooleanVar(value=S.input_is_f)
chk_f=ttk.Checkbutton(top, text="Entrada °F→°C (manual)", variable=inputf_var)
chk_f.pack(side="left", padx=(6,4))
force_ph=tk.BooleanVar(value=S.force_phidget)
chk_force=ttk.Checkbutton(top, text="Forzar Phidget", variable=force_ph)
chk_force.pack(side="left", padx=(6,4))
showf=tk.BooleanVar(value=S.show_f)
chk_showf=ttk.Checkbutton(top, text="Mostrar °F (display)", variable=showf)
chk_showf.pack(side="left", padx=(6,4))

# Sample rate
ttk.Label(top,text="Hz").pack(side="left",padx=(12,4))
rate=ttk.Spinbox(top, from_=0.5, to=10.0, increment=0.5, width=6)
rate.set(CFG["sample_hz"]); rate.pack(side="left")

proc=ttk.Combobox(top, values=["natural","honey","anaerobico","levadura","lavado"], width=12); proc.set(S.meta["process"]); proc.pack(side="left", padx=(12,0))
brew=ttk.Combobox(top, values=["espresso","filter","both"], width=10); brew.set(S.meta["brewTarget"]); brew.pack(side="left")
ttk.Label(top,text="Gas").pack(side="left",padx=(12,4)); gas=ttk.Spinbox(top,from_=1,to=10,width=4); gas.set(S.gas); gas.pack(side="left")
ttk.Label(top,text="Aire").pack(side="left",padx=(8,4)); air=ttk.Spinbox(top,from_=1,to=10,width=4); air.set(S.air); air.pack(side="left")
ttk.Label(top,text="Set°").pack(side="left",padx=(8,4)); setv=ttk.Spinbox(top,from_=0,to=300,width=6); setv.set(S.set_temp); setv.pack(side="left")
ttk.Label(top,text="Origen").pack(side="left",padx=(12,4)); origin=ttk.Entry(top,width=18); origin.pack(side="left")
ttk.Label(top,text="Densidad").pack(side="left",padx=(8,4)); density=ttk.Entry(top,width=10); density.pack(side="left")
ttk.Label(top,text="Humedad").pack(side="left",padx=(8,4)); moist=ttk.Entry(top,width=8); moist.pack(side="left")

# ======= BUTTONS =======
btns=ttk.Frame(root); btns.pack(fill="x", padx=12, pady=8)
def annotate_event(name, t, temp_c):
    v=ax1.axvline(t, color="#f87171", linestyle="--", linewidth=1.2, alpha=0.9)
    marker=ax1.plot(t, temp_c, marker="o", color="#f87171", markersize=5)[0]
    text=ax1.text(t, temp_c+3, f"{name}\\n{t:.0f}s @ {temp_c:.1f}°C", color=FG,
                  bbox=dict(boxstyle="round,pad=0.3", fc=GLASS, ec=GRID, alpha=0.9),
                  ha="left", va="bottom", fontsize=9)
    event_artists.append((v,marker,text))
def log_event(n):
    t=0.0 if not S.t0 else time.time()-S.t0
    bt=S.model.bt_hist[-1] if S.model.bt_hist else None
    et=current_et_c()
    temp = bt if (bt is not None and bt==bt) else et
    S.events.append({"event":n,"t_sec":round(t,2),"temp_c":round(temp,1)})
    annotate_event(n, t, temp)
    if n == "1C":
        try:
            S.model.fc_predictor.commit_first_crack(t)
        except Exception as e:
            log("AI 1C feedback error: "+str(e))
for name in ["CHARGE","TP","DRY_END","1C","2C","DROP"]:
    ttk.Button(btns, text=name, command=lambda n=name: log_event(n)).pack(side="left", padx=4)

def export_all():
    if not S.samples: messagebox.showwarning("Export","No hay muestras"); return
    base=filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"roast-{timestamp_slug()}")
    if not base: return
    meta=S.meta|{"events_count":len(S.events), "offset_c":CFG["offset_c"], "scale_pct":CFG["scale_pct"]}
    fig.savefig(base.replace(".csv","")+".plot.png", dpi=160, facecolor=BG)
    export_session_csv(base, S.samples, S.events, meta)
    messagebox.showinfo("Export","CSV/PNG exportados.")
ttk.Button(btns, text="Export CSV/PNG", command=export_all).pack(side="right", padx=4)

# Calibration row
cal=ttk.Frame(root); cal.pack(fill="x", padx=12, pady=6)
off_var=tk.StringVar(value=str(CFG["offset_c"])); sca_var=tk.StringVar(value=str(CFG["scale_pct"]))
ttk.Label(cal,text="Offset (°C)").pack(side="left"); off_e=ttk.Entry(cal,textvariable=off_var,width=8); off_e.pack(side="left",padx=4)
ttk.Label(cal,text="Scale (%)").pack(side="left"); sca_e=ttk.Entry(cal,textvariable=sca_var,width=8); sca_e.pack(side="left",padx=4)

def apply_calibration():
    try:
        CFG["offset_c"]=float(off_var.get())
        CFG["scale_pct"]=float(sca_var.get())
        json.dump(CFG, open("config.json","w",encoding="utf-8"), indent=2)
        messagebox.showinfo("Calibración","Guardado en config.json")
    except Exception as e:
        messagebox.showerror("Calibración", f"Error: {e}")
ttk.Button(cal,text="Aplicar calib", command=apply_calibration).pack(side="left", padx=8)

def wizard_one_point():
    val = simpledialog.askfloat("1 punto (offset)","Ingresa temperatura real (°C) ahora (por ej. ambiente medida con termómetro)")
    if val is None: return
    raw = S.reader.raw_c
    try:
        raw = float(raw)
    except:
        messagebox.showerror("1 punto","Lectura RAW inválida"); return
    CFG["scale_pct"]=100.0
    CFG["offset_c"]=val - raw
    off_var.set(str(round(CFG["offset_c"],2))); sca_var.set(str(CFG["scale_pct"]))
    json.dump(CFG, open("config.json","w",encoding="utf-8"), indent=2)
    messagebox.showinfo("1 punto","Aplicado: offset={:.2f}°C".format(CFG["offset_c"]))
def wizard_two_points():
    messagebox.showinfo("2 puntos","Necesitas dos baños: 0°C (hielo/agua) y ~100°C (ebullición).")
    r1 = simpledialog.askfloat("2 puntos","Temp real P1 (°C): ej. 0")
    if r1 is None: return
    messagebox.showinfo("2 puntos","Coloca la punta en P1 y espera 10s, luego OK...")
    raw1 = S.reader.raw_c
    r2 = simpledialog.askfloat("2 puntos","Temp real P2 (°C): ej. 100")
    if r2 is None: return
    messagebox.showinfo("2 puntos","Coloca la punta en P2 y espera 10s, luego OK...")
    raw2 = S.reader.raw_c
    try:
        raw1=float(raw1); raw2=float(raw2)
    except:
        messagebox.showerror("2 puntos","Lecturas inválidas"); return
    if raw2-raw1 == 0:
        messagebox.showerror("2 puntos","Lecturas idénticas, no se puede escalar."); return
    scale = (r2 - r1) / (raw2 - raw1)
    offset = r1 - scale*raw1
    CFG["scale_pct"]=scale*100.0; CFG["offset_c"]=offset
    off_var.set(str(round(CFG["offset_c"],2))); sca_var.set(str(round(CFG["scale_pct"],2)))
    json.dump(CFG, open("config.json","w",encoding="utf-8"), indent=2)
    messagebox.showinfo("2 puntos","Aplicado: scale={:.2f}%, offset={:.2f}°C".format(CFG["scale_pct"], CFG["offset_c"]))

ttk.Button(cal,text="Calib 1 punto", command=wizard_one_point).pack(side="left", padx=8)
ttk.Button(cal,text="Calib 2 puntos", command=wizard_two_points).pack(side="left", padx=4)

# Control buttons
ctrl=ttk.Frame(root); ctrl.pack(fill="x", padx=12, pady=6)
def start_run():
    try:
        S.running=True; RUNVAR.set("RUN: True")
        if S.t0 is None: S.t0=time.time()
        log("Start OK")
    except Exception as e:
        log("Start ERROR: "+str(e))
def stop_run():
    S.running=False; RUNVAR.set("RUN: False"); log("Stop")
def reset_session():
    S.running=False; RUNVAR.set("RUN: False")
    S.samples.clear(); S.events.clear()
    S.model.reset(); redraw_empty()
    S.t0=None; eta1.config(text="ETA 1C: —"); etad.config(text="ETA Drop: —"); sugg.config(text="Sugerencia: —"); fc_var.set("Pred 1C IA: —"); BTVAR.set("BT —.— °C")
    log("Reset")
def reconnect_reader():
    try: S.reader.stop()
    except: pass
    try:
        hz=float(rate.get()); CFG["sample_hz"]=hz
    except: pass
    serial=serial_var.get().strip()
    CFG["phidget_serial"]=serial
    json.dump(CFG, open("config.json","w",encoding="utf-8"), indent=2)
    serial_cfg = serial or os.environ.get("PHIDGET_1048_SERIAL")
    S.reader = ETReader(sample_hz=CFG["sample_hz"], channel=int(spin_ch.get()), thermocouple_type=tc.get(),
                        force_sim=sim_var.get(), force_phidget=force_ph.get(),
                        device_serial=serial_cfg)
    S.reader.start()
    log(f"Phidget reiniciado (canal={spin_ch.get()}, TC={tc.get()}, sim={sim_var.get()}, forzar={force_ph.get()}, {CFG['sample_hz']} Hz)")
def test_read():
    try:
        raw = S.reader.raw_c
        filt = S.reader.et_c
        messagebox.showinfo("Test lectura", f"Fuente={S.reader.source}\\nRAW={raw:.2f}°C\\nFiltrado={filt:.2f}°C\\nOK={S.reader.ok}\\nAviso={S.reader.warn or '—'}")
    except Exception as e:
        messagebox.showerror("Test lectura", f"Error: {e}")

ttk.Button(ctrl,text="Start", command=start_run).pack(side="left", padx=4)
ttk.Button(ctrl,text="Stop (Pausa)", command=stop_run).pack(side="left", padx=4)
ttk.Button(ctrl,text="Reset", command=reset_session).pack(side="left", padx=4)
ttk.Button(ctrl,text="Reconectar lector", command=reconnect_reader).pack(side="right", padx=8)
ttk.Button(ctrl,text="Test lectura", command=test_read).pack(side="right", padx=8)

footer=ttk.Frame(root); footer.pack(fill="x", padx=12, pady=4)
eta1=ttk.Label(footer,text="ETA 1C: —"); eta1.pack(side="left",padx=8)
etad=ttk.Label(footer,text="ETA Drop: —"); etad.pack(side="left",padx=8)
sugg=ttk.Label(footer,text="Sugerencia: —"); sugg.pack(side="left",padx=8)
fc_var=tk.StringVar(value="Pred 1C IA: —")
ttk.Label(footer,textvariable=fc_var).pack(side="left",padx=8)

# ======= PLOTS =======
import matplotlib as mpl
plt.rcParams.update({
    "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "font.family": "Segoe UI",
})
fig,(ax1,ax2)=plt.subplots(2,1,figsize=(10.5,7.0),dpi=110)
fig.patch.set_facecolor(BG)
for ax in (ax1,ax2):
    ax.set_facecolor(BG); ax.tick_params(colors=FG,labelsize=10)
    for sp in ax.spines.values(): sp.set_color(GRID)
    ax.grid(True,color=GRID,alpha=0.35,linewidth=0.7)
ax1.set_title("Temperaturas"); ax2.set_title("Rate of Rise (RoR)")
ln_et,=ax1.plot([],[],label="ET",linewidth=2.2,color="#60a5fa")
ln_bt,=ax1.plot([],[],label="BT_est",linewidth=2.2,color="#f59e0b")
ln_set,=ax1.plot([],[],label="Set",linewidth=1.6,color="#94a3b8",linestyle="--")
ax1.legend(facecolor=BG, labelcolor=FG, edgecolor=GRID, loc="upper left")
ln_ror,=ax2.plot([],[],label="RoR",linewidth=2.0,color="#a3e635")
ln_ror_t,=ax2.plot([],[],label="RoR target",linewidth=1.6,color="#ef4444",linestyle="--")
ax2.legend(facecolor=BG, labelcolor=FG, edgecolor=GRID, loc="upper left")
canvas=FigureCanvasTkAgg(fig, master=root); canvas.get_tk_widget().pack(fill="both",expand=True,padx=12,pady=8)
event_artists=[]

# ======= CONSOLA DEBUG =======
dbg=ttk.Frame(root); dbg.pack(fill="both", expand=False, padx=12, pady=(0,8))
ttk.Label(dbg, text="Consola").pack(anchor="w")
txt=tk.Text(dbg, height=6, bg="#0f1621", fg="#d1d5db")
txt.pack(fill="both", expand=True)
def log(msg):
    try:
        txt.insert("end", time.strftime("[%H:%M:%S] ") + msg + "\\n")
        txt.see("end")
    except:
        pass

def redraw_empty():
    for arts in event_artists:
        for a in arts: 
            try: a.remove()
            except Exception: pass
    event_artists.clear()
    for ln in (ln_et, ln_bt, ln_set, ln_ror, ln_ror_t):
        ln.set_data([],[])
    canvas.draw_idle()

def current_et_c():
    et=S.reader.et_c
    if et==et and inputf_var.get():
        et = (et - 32.0) * (5.0/9.0)
    et = apply_cal(et)
    if showf.get():
        ETVAR.set(f"ET {et*9/5+32:.1f} °F")
    else:
        ETVAR.set(f"ET {et:.1f} °C")
    return et

def update_bt_display(bt):
    if bt==bt:
        if showf.get():
            BTVAR.set(f"BT {bt*9/5+32:.1f} °F")
        else:
            BTVAR.set(f"BT {bt:.1f} °C")
    else:
        BTVAR.set("BT —.— °C")

def push_meta(*_):
    S.meta["process"]=proc.get(); S.meta["brewTarget"]=brew.get()
    try: S.gas=int(gas.get()); S.air=int(air.get()); S.set_temp=int(setv.get())
    except: pass
    S.meta["origin"]=origin.get(); S.meta["density"]=density.get(); S.meta["moisture"]=moist.get()
for w in [proc,brew,gas,air,setv,origin,density,moist]:
    if hasattr(w,"bind"): w.bind("<<ComboboxSelected>>", push_meta)

S.reader.start()
log("Lector iniciado")

def animate(_):
    try:
        et_raw = S.reader.raw_c; et_filt = S.reader.et_c
        src_var.set(f"Fuente: {S.reader.source}")
        try:
            raw_var.set(f"RAW: {et_raw:.2f} | FILT: {et_filt:.2f}")
        except Exception:
            pass

        ok=S.reader.ok
        status.itemconfig(DOT, fill=("#22c55e" if ok else "#ef4444"))

        now=time.time()
        if S.t0 is None: S.t0=now
        t=now-S.t0

        et=current_et_c()

        bt_input = et if math.isfinite(et) else (S.model.bt_hist[-1] if S.model.bt_hist else float('nan'))
        if S.running:
            bt, ror, _ = S.model.step(t, bt_input)
        else:
            bt = S.model.update_idle(bt_input, t)
            ror = S.model.ror_hist[-1] if S.model.ror_hist else float('nan')

        update_bt_display(bt)

        if not S.samples:
            S.samples.append({
                "t_sec":0.0,
                "et_c":et if math.isfinite(et) else np.nan,
                "bt_est_c":round(bt,2) if math.isfinite(bt) else np.nan,
                "ror":np.nan,
                "gas":S.gas,
                "air":S.air,
                "set_temp":S.set_temp,
            })
        else:
            if S.running:
                ror_target = 7.0
                firstC = 196.0
                dropBT = 205.0
                try:
                    prof=json.load(open("profiles.json","r",encoding="utf-8"))[S.meta["process"]][S.meta["brewTarget"]]
                    S.model.alpha=float(prof["alpha"])
                    ror_target=float(prof["rorTarget"])
                    firstC=float(prof["firstCrackBT"])
                    dropBT=float(prof["dropBT"])
                    S.model.fc_predictor.set_target_bt(firstC)
                except Exception:
                    pass
                S.samples.append({
                    "t_sec":round(t,2),
                    "et_c":round(et,2) if math.isfinite(et) else np.nan,
                    "bt_est_c":round(bt,2) if math.isfinite(bt) else np.nan,
                    "ror":round(ror if isinstance(ror,float) else 0.0,3),
                    "gas":S.gas,
                    "air":S.air,
                    "set_temp":S.set_temp,
                })
                try:
                    def eta_str(s):
                        if s is None: return "—"
                        return f"{int(s//60)}m{int(s%60)}s"
                    eta1.config(text="ETA 1C (lin): "+eta_str(S.model.eta_seconds(firstC)))
                    etad.config(text="ETA Drop: "+eta_str(S.model.eta_seconds(dropBT)))
                except Exception as e:
                    log("ETA error: "+str(e))
                try:
                    sugg.config(text="Sugerencia: "+gas_air_suggestion(ror if isinstance(ror,float) else None, ror_target))
                except Exception as e:
                    log("Sugerencia error: "+str(e))
            else:
                last=S.samples[-1]
                last["et_c"]=round(et,2) if math.isfinite(et) else np.nan
                last["bt_est_c"]=round(bt,2) if math.isfinite(bt) else np.nan

        pred = S.model.fc_predictor.last_prediction
        if pred is not None:
            abs_fc, rem_fc = pred
            def fmt(sec):
                return f"{int(sec//60)}m{int(sec%60)}s"
            if rem_fc <= 1.0:
                fc_var.set("Pred 1C IA: alcanzado")
            else:
                fc_var.set(f"Pred 1C IA: {fmt(abs_fc)} (faltan {fmt(rem_fc)})")
        else:
            fc_var.set("Pred 1C IA: —")

        t_arr=[s["t_sec"] for s in S.samples]
        et_arr=[s["et_c"] for s in S.samples]
        bt_arr=[s.get("bt_est_c",np.nan) for s in S.samples]
        ror_arr=[s.get("ror",np.nan) for s in S.samples]

        ror_target = 7.0
        try:
            prof=json.load(open("profiles.json","r",encoding="utf-8"))[S.meta["process"]][S.meta["brewTarget"]]
            ror_target=float(prof["rorTarget"])
        except Exception:
            pass

        ln_et.set_data(t_arr, et_arr); ln_bt.set_data(t_arr, bt_arr); ln_set.set_data(t_arr, [S.set_temp]*len(t_arr))
        ln_ror.set_data(t_arr, ror_arr); ln_ror_t.set_data(t_arr, [ror_target]*len(t_arr))
        for ax in (ax1,ax2):
            ax.relim(); ax.autoscale_view()

        count_var.set(f"Muestras: {len(S.samples)}")
    except Exception as e:
        log("Loop error: "+str(e)+"\\n"+traceback.format_exc())

ani=FuncAnimation(fig, animate, interval=int(1000/CFG["sample_hz"]))
root.protocol("WM_DELETE_WINDOW", lambda: (S.reader.stop(), root.destroy()))
root.mainloop()

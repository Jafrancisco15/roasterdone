\
import os, time, json, math, tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import numpy as np
import pandas as pd
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
    if os.path.exists("config.json"):
        try:
            return json.load(open("config.json","r",encoding="utf-8"))
        except Exception:
            pass
    return {"offset_c":0.0,"scale_pct":100.0,"sample_hz":2.0}

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

S.reader = ETReader(sample_hz=CFG["sample_hz"], channel=S.ch, thermocouple_type=S.tc, force_sim=S.force_sim, force_phidget=S.force_phidget)
S.model = RoastModel(alpha=0.12)

DESIGN={
    "mode": False,
    "active": "BT",
    "bt_points": [],
    "et_points": [],
    "drag_point": None,
    "dragging": False,
    "last_path": None,
}

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
    st.configure("TCheckbutton", background=GLASS, foreground=FG)
    st.map("TCheckbutton", background=[('active', '#1b2430')])

    st.configure("Content.TFrame", background=BG)
    st.configure("Header.TFrame", background=GLASS)
    st.configure("Metric.TFrame", background=BG)
    st.configure("MetricCard.TFrame", background=GLASS, relief="ridge", borderwidth=1)
    st.configure("Card.TFrame", background=GLASS)
    st.configure("Card.TLabelframe", background=GLASS, borderwidth=1, relief="ridge", foreground=FG)
    st.configure("Card.TLabelframe.Label", background=GLASS, foreground=FG, font=("Segoe UI Semibold", 11))
    st.configure("CardText.TLabel", background=GLASS, foreground=FG, font=("Segoe UI", 10))

    st.configure("HeaderTitle.TLabel", background=GLASS, foreground=FG, font=("Segoe UI Semibold", 24))
    st.configure("HeaderSubtitle.TLabel", background=GLASS, foreground="#94a3b8", font=("Segoe UI", 11))
    st.configure("HeaderStatus.TLabel", background=GLASS, foreground="#e5e7eb", font=("Segoe UI", 10, "bold"))
    st.configure("RunBadge.TLabel", background=ACC, foreground=BG, padding=(12,6), font=("Segoe UI Semibold", 11))
    st.configure("MetricTitle.TLabel", background=GLASS, foreground="#94a3b8", font=("Segoe UI", 10))
    st.configure("MetricValue.TLabel", background=GLASS, foreground=FG, font=("Segoe UI", 16, "bold"))
root=tk.Tk(); style_root(root)
root.geometry("1300x900")
root.minsize(1100, 780)

content=ttk.Frame(root, style="Content.TFrame")
content.pack(fill="both", expand=True)
content.grid_rowconfigure(0, weight=1)
content.grid_columnconfigure(0, weight=1)

main_area=ttk.Frame(content, style="Content.TFrame")
main_area.grid(row=0, column=0, sticky="nsew")

drawer_container=tk.Frame(content, bg=BG, width=300)
drawer_container.grid(row=0, column=1, sticky="ns", padx=(0,16), pady=16)
drawer_container.grid_propagate(False)

drawer_canvas=tk.Canvas(drawer_container, bg=GLASS, highlightthickness=0, width=300)
drawer_scroll=ttk.Scrollbar(drawer_container, orient="vertical", command=drawer_canvas.yview)
drawer_canvas.configure(yscrollcommand=drawer_scroll.set)
drawer_canvas.pack(side="left", fill="both", expand=True)
drawer_scroll.pack(side="right", fill="y")

advanced_panel=ttk.Frame(drawer_canvas, style="Content.TFrame")
drawer_window=drawer_canvas.create_window((0,0), window=advanced_panel, anchor="nw")

def _update_drawer_scroll(_event=None):
    drawer_canvas.configure(scrollregion=drawer_canvas.bbox("all"))
    cont_w = drawer_container.winfo_width()
    drawer_canvas.itemconfigure(drawer_window, width=cont_w)

advanced_panel.bind("<Configure>", _update_drawer_scroll)
drawer_container.bind("<Configure>", _update_drawer_scroll)

def _on_mousewheel(event):
    if event.delta:
        drawer_canvas.yview_scroll(int(-event.delta/120), "units")
    elif event.num in (4,5):
        drawer_canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
    return "break"

def _activate_scroll(_event=None):
    drawer_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    drawer_canvas.bind_all("<Button-4>", _on_mousewheel)
    drawer_canvas.bind_all("<Button-5>", _on_mousewheel)

def _deactivate_scroll(_event=None):
    drawer_canvas.unbind_all("<MouseWheel>")
    drawer_canvas.unbind_all("<Button-4>")
    drawer_canvas.unbind_all("<Button-5>")

drawer_canvas.bind("<Enter>", _activate_scroll)
drawer_canvas.bind("<Leave>", _deactivate_scroll)

toggle_text=tk.StringVar(value="Mostrar panel lateral")

drawer_container.grid_remove()

def toggle_advanced():
    if drawer_container.winfo_ismapped():
        drawer_container.grid_remove()
        toggle_text.set("Mostrar panel lateral")
        _deactivate_scroll()
    else:
        drawer_container.grid()
        toggle_text.set("Ocultar panel lateral")
        drawer_container.after(10, _update_drawer_scroll)

# ======= TOP BAR =======
topbar=ttk.Frame(main_area, style="Header.TFrame", padding=(16, 10))
topbar.pack(fill="x", padx=16, pady=(16, 8))

title_wrap=ttk.Frame(topbar, style="Header.TFrame")
title_wrap.pack(side="left", anchor="w")
ttk.Label(title_wrap, text="☕ RoastLab Studio", style="HeaderTitle.TLabel").pack(anchor="w")
ttk.Label(title_wrap, text="Seguimiento del tueste en vivo", style="HeaderSubtitle.TLabel").pack(anchor="w", pady=(2,0))

status_wrap=ttk.Frame(topbar, style="Header.TFrame")
status_wrap.pack(side="left", padx=(24,0))
RUNVAR=tk.StringVar(value="RUN: False")
run_lbl=ttk.Label(status_wrap, textvariable=RUNVAR, style="RunBadge.TLabel")
run_lbl.pack(side="left", padx=(0,12))

status_block=ttk.Frame(status_wrap, style="Header.TFrame")
status_block.pack(side="left", padx=(0,12))
status=tk.Canvas(status_block,width=16,height=16,highlightthickness=0,bg=GLASS)
status.pack(side="left")
DOT=status.create_oval(1,1,15,15,fill="#ef4444",outline="")
ttk.Label(status_block, text="Phidget", style="HeaderStatus.TLabel").pack(side="left", padx=(6,0))

sensor_block=ttk.Frame(status_wrap, style="Header.TFrame")
sensor_block.pack(side="left")
sensor_status=tk.Canvas(sensor_block,width=16,height=16,highlightthickness=0,bg=GLASS)
sensor_status.pack(side="left")
SENSOR_DOT=sensor_status.create_oval(1,1,15,15,fill="#ef4444",outline="")
ttk.Label(sensor_block, text="Sensor", style="HeaderStatus.TLabel").pack(side="left", padx=(6,0))

control_buttons=ttk.Frame(topbar, style="Header.TFrame")
control_buttons.pack(side="right", anchor="e")
btn_start=ttk.Button(control_buttons, text="▶️ Iniciar", command=lambda: start_run())
btn_start.pack(side="left", padx=4)
btn_stop=ttk.Button(control_buttons, text="⏸️ Pausa", command=lambda: stop_run())
btn_stop.pack(side="left", padx=4)
btn_reset=ttk.Button(control_buttons, text="⏹️ Reset", command=lambda: reset_session())
btn_reset.pack(side="left", padx=4)

toggle_row=ttk.Frame(main_area, style="Content.TFrame", padding=(16, 0))
toggle_row.pack(fill="x")
ttk.Button(toggle_row, textvariable=toggle_text, command=toggle_advanced).pack(side="left")

# ======= METRICS & CONTROLS (ADVANCED) =======
for col in range(3):
    advanced_panel.columnconfigure(col, weight=1)

metrics=ttk.Frame(advanced_panel, style="Metric.TFrame")
metrics.pack(fill="x", pady=(0, 12))
metrics.columnconfigure(0, weight=1)

ETVAR=tk.StringVar(value="ET —.— °C")
BTVAR=tk.StringVar(value="BT —.— °C")
src_var=tk.StringVar(value="Fuente: —")
sensor_var=tk.StringVar(value="Sensor: —")
raw_var=tk.StringVar(value="RAW: —  |  FILT: —")
count_var=tk.StringVar(value="Muestras: 0")

metric_data=[
    ("🌡️ ET", ETVAR),
    ("🔥 BT", BTVAR),
    ("📡 Fuente", src_var),
    ("🧪 Sensor", sensor_var),
    ("🧬 Lecturas", raw_var),
    ("🧮 Muestras", count_var),
]

for idx, (label_text, var) in enumerate(metric_data):
    card=ttk.Frame(metrics, style="MetricCard.TFrame", padding=(14, 12))
    card.grid(row=idx, column=0, padx=6, pady=6, sticky="ew")
    ttk.Label(card, text=label_text, style="MetricTitle.TLabel").pack(anchor="w")
    ttk.Label(card, textvariable=var, style="MetricValue.TLabel").pack(anchor="w", pady=(6,0))

control_area=ttk.Frame(advanced_panel, style="Content.TFrame")
control_area.pack(fill="both", expand=True, pady=(0, 12))

device_frame=ttk.LabelFrame(control_area, text="⚙️ Hardware", style="Card.TLabelframe", padding=(14, 12))
device_frame.pack(fill="x", padx=6, pady=6)
device_frame.columnconfigure(1, weight=1)

ttk.Label(device_frame, text="Canal", style="CardText.TLabel").grid(row=0, column=0, sticky="w")
spin_ch=ttk.Spinbox(device_frame,from_=0,to=3,width=6)
spin_ch.set(S.ch)
spin_ch.grid(row=0, column=1, sticky="ew", pady=2)

ttk.Label(device_frame, text="Termopar", style="CardText.TLabel").grid(row=1, column=0, sticky="w", pady=(4,0))
tc=ttk.Combobox(device_frame, values=["K","J","E","T","N","S","R","B"], width=6)
tc.set(S.tc)
tc.grid(row=1, column=1, sticky="ew", pady=(4,0))

ttk.Label(device_frame, text="Frecuencia (Hz)", style="CardText.TLabel").grid(row=2, column=0, sticky="w", pady=(6,0))
rate=ttk.Spinbox(device_frame, from_=0.5, to=10.0, increment=0.5, width=6)
rate.set(CFG["sample_hz"])
rate.grid(row=2, column=1, sticky="ew", pady=(6,0))

sim_var=tk.BooleanVar(value=S.force_sim)
chk_sim=ttk.Checkbutton(device_frame, text="Simulador", variable=sim_var)
chk_sim.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10,0))

force_ph=tk.BooleanVar(value=S.force_phidget)
chk_force=ttk.Checkbutton(device_frame, text="Forzar Phidget", variable=force_ph)
chk_force.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

inputf_var=tk.BooleanVar(value=S.input_is_f)
chk_f=ttk.Checkbutton(device_frame, text="Entrada °F→°C\nmanual", variable=inputf_var)
chk_f.grid(row=5, column=0, columnspan=2, sticky="w", pady=2)

showf=tk.BooleanVar(value=S.show_f)
chk_showf=ttk.Checkbutton(device_frame, text="Mostrar °F", variable=showf)
chk_showf.grid(row=6, column=0, columnspan=2, sticky="w", pady=2)

session_frame=ttk.LabelFrame(control_area, text="🧾 Datos del lote", style="Card.TLabelframe", padding=(14, 12))
session_frame.pack(fill="x", padx=6, pady=6)
session_frame.columnconfigure(1, weight=1)

ttk.Label(session_frame, text="Proceso", style="CardText.TLabel").grid(row=0, column=0, sticky="w")
proc=ttk.Combobox(session_frame, values=["natural","honey","anaerobico","levadura","lavado"], width=14)
proc.set(S.meta["process"])
proc.grid(row=0, column=1, sticky="ew", pady=2)

ttk.Label(session_frame, text="Método", style="CardText.TLabel").grid(row=1, column=0, sticky="w", pady=(4,0))
brew=ttk.Combobox(session_frame, values=["espresso","filter","both"], width=12)
brew.set(S.meta["brewTarget"])
brew.grid(row=1, column=1, sticky="ew", pady=(4,0))

ttk.Label(session_frame, text="Gas", style="CardText.TLabel").grid(row=2, column=0, sticky="w", pady=(6,0))
gas=ttk.Spinbox(session_frame,from_=1,to=10,width=6)
gas.set(S.gas)
gas.grid(row=2, column=1, sticky="ew", pady=(6,0))

ttk.Label(session_frame, text="Aire", style="CardText.TLabel").grid(row=3, column=0, sticky="w", pady=(4,0))
air=ttk.Spinbox(session_frame,from_=1,to=10,width=6)
air.set(S.air)
air.grid(row=3, column=1, sticky="ew", pady=(4,0))

ttk.Label(session_frame, text="Setpoint (°C)", style="CardText.TLabel").grid(row=4, column=0, sticky="w", pady=(6,0))
setv=ttk.Spinbox(session_frame,from_=0,to=300,width=8)
setv.set(S.set_temp)
setv.grid(row=4, column=1, sticky="ew", pady=(6,0))

ttk.Label(session_frame, text="Origen", style="CardText.TLabel").grid(row=5, column=0, sticky="w", pady=(8,0))
origin=ttk.Entry(session_frame)
origin.grid(row=5, column=1, sticky="ew", pady=(8,0))
origin.insert(0, S.meta.get("origin",""))

ttk.Label(session_frame, text="Densidad", style="CardText.TLabel").grid(row=6, column=0, sticky="w", pady=(4,0))
density=ttk.Entry(session_frame)
density.grid(row=6, column=1, sticky="ew", pady=(4,0))
density.insert(0, S.meta.get("density",""))

ttk.Label(session_frame, text="Humedad", style="CardText.TLabel").grid(row=7, column=0, sticky="w", pady=(4,0))
moist=ttk.Entry(session_frame)
moist.grid(row=7, column=1, sticky="ew", pady=(4,0))
moist.insert(0, S.meta.get("moisture",""))

control_frame=ttk.LabelFrame(control_area, text="🎛️ Control de tueste", style="Card.TLabelframe", padding=(14, 12))
control_frame.pack(fill="x", padx=6, pady=6)
control_frame.columnconfigure(0, weight=1)

btn_reconnect=ttk.Button(control_frame, text="🔄 Reconectar", command=lambda: reconnect_reader())
btn_reconnect.grid(row=0, column=0, sticky="ew", pady=(0,4))
btn_test=ttk.Button(control_frame, text="🧪 Test lectura", command=lambda: test_read())
btn_test.grid(row=1, column=0, sticky="ew", pady=2)

ttk.Separator(control_frame).grid(row=2, column=0, sticky="ew", pady=8)

eta1=ttk.Label(control_frame,text="ETA 1C: —", style="MetricTitle.TLabel")
eta1.grid(row=3, column=0, sticky="w", pady=(0,2))
etad=ttk.Label(control_frame,text="ETA Drop: —", style="MetricTitle.TLabel")
etad.grid(row=4, column=0, sticky="w", pady=2)
sugg=ttk.Label(control_frame,text="Sugerencia: —", style="MetricTitle.TLabel", wraplength=220, justify="left")
sugg.grid(row=5, column=0, sticky="w", pady=(4,0))

cal_frame=ttk.LabelFrame(control_area, text="🧭 Calibración", style="Card.TLabelframe", padding=(14, 12))
cal_frame.pack(fill="x", padx=6, pady=6)
cal_frame.columnconfigure(3, weight=1)

off_var=tk.StringVar(value=str(CFG["offset_c"]))
sca_var=tk.StringVar(value=str(CFG["scale_pct"]))
ttk.Label(cal_frame,text="Offset (°C)", style="CardText.TLabel").grid(row=0, column=0, sticky="w")
off_e=ttk.Entry(cal_frame,textvariable=off_var,width=10)
off_e.grid(row=0, column=1, sticky="w", padx=(6,12))
ttk.Label(cal_frame,text="Scale (%)", style="CardText.TLabel").grid(row=0, column=2, sticky="w")
sca_e=ttk.Entry(cal_frame,textvariable=sca_var,width=10)
sca_e.grid(row=0, column=3, sticky="w", padx=(6,0))

btn_apply_cal=ttk.Button(cal_frame,text="💾 Guardar", command=lambda: apply_calibration())
btn_apply_cal.grid(row=0, column=4, sticky="w", padx=(12,0))

btn_cal1=ttk.Button(cal_frame,text="📍 Calib 1 punto", command=lambda: wizard_one_point())
btn_cal1.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10,0))
btn_cal2=ttk.Button(cal_frame,text="📍 Calib 2 puntos", command=lambda: wizard_two_points())
btn_cal2.grid(row=1, column=2, columnspan=2, sticky="w", pady=(10,0))

# ======= CONSOLA DEBUG (ADVANCED) =======
dbg=ttk.LabelFrame(advanced_panel, text="📜 Bitácora", style="Card.TLabelframe", padding=(12, 10))
dbg.pack(fill="both", expand=False, pady=(0, 6))
txt=tk.Text(dbg, height=6, bg="#0f1621", fg="#d1d5db", insertbackground="#f9fafb", relief="flat")
txt.pack(fill="both", expand=True)


def apply_calibration():
    try:
        CFG["offset_c"]=float(off_var.get())
        CFG["scale_pct"]=float(sca_var.get())
        json.dump(CFG, open("config.json","w",encoding="utf-8"), indent=2)
        messagebox.showinfo("Calibración","Guardado en config.json")
    except Exception as e:
        messagebox.showerror("Calibración", f"Error: {e}")
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
    S.t0=None; eta1.config(text="ETA 1C: —"); etad.config(text="ETA Drop: —"); sugg.config(text="Sugerencia: —")
    log("Reset")
def reconnect_reader():
    try: S.reader.stop()
    except: pass
    try:
        hz=float(rate.get()); CFG["sample_hz"]=hz; json.dump(CFG, open("config.json","w",encoding="utf-8"), indent=2)
    except: pass
    S.reader = ETReader(sample_hz=CFG["sample_hz"], channel=int(spin_ch.get()), thermocouple_type=tc.get(),
                        force_sim=sim_var.get(), force_phidget=force_ph.get())
    S.reader.start()
    log(f"Phidget reiniciado (canal={spin_ch.get()}, TC={tc.get()}, sim={sim_var.get()}, forzar={force_ph.get()}, {CFG['sample_hz']} Hz)")
def test_read():
    try:
        raw = S.reader.raw_c
        filt = S.reader.et_c
        messagebox.showinfo("Test lectura", f"Fuente={S.reader.source}\\nRAW={raw:.2f}°C\\nFiltrado={filt:.2f}°C\\nOK={S.reader.ok}\\nAviso={S.reader.warn or '—'}")
    except Exception as e:
        messagebox.showerror("Test lectura", f"Error: {e}")

def show_about():
    messagebox.showinfo(APPNAME, "RoastLab Studio\nInterfaz rediseñada para un monitoreo más claro y amigable.")


def export_all():
    if not S.samples:
        messagebox.showwarning("Export", "No hay muestras")
        return
    base=filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"roast-{timestamp_slug()}")
    if not base:
        return
    meta=S.meta|{"events_count":len(S.events), "offset_c":CFG["offset_c"], "scale_pct":CFG["scale_pct"]}
    fig.savefig(base.replace(".csv", "")+".plot.png", dpi=160, facecolor=BG)
    export_session_csv(base, S.samples, S.events, meta)
    messagebox.showinfo("Export", "CSV/PNG exportados.")


menubar=tk.Menu(root)
file_menu=tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Exportar CSV/PNG", command=export_all)
file_menu.add_separator()
file_menu.add_command(label="Salir", command=root.destroy)
menubar.add_cascade(label="Archivo", menu=file_menu)

session_menu=tk.Menu(menubar, tearoff=0)
session_menu.add_command(label="Iniciar", command=start_run)
session_menu.add_command(label="Pausa", command=stop_run)
session_menu.add_command(label="Reset", command=reset_session)
menubar.add_cascade(label="Sesión", menu=session_menu)

hardware_menu=tk.Menu(menubar, tearoff=0)
hardware_menu.add_command(label="Reconectar lector", command=reconnect_reader)
hardware_menu.add_command(label="Test lectura", command=test_read)
menubar.add_cascade(label="Hardware", menu=hardware_menu)

tools_menu=tk.Menu(menubar, tearoff=0)
tools_menu.add_command(label="Guardar calibración", command=apply_calibration)
tools_menu.add_command(label="Calibración 1 punto", command=wizard_one_point)
tools_menu.add_command(label="Calibración 2 puntos", command=wizard_two_points)
menubar.add_cascade(label="Herramientas", menu=tools_menu)

help_menu=tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="Acerca de", command=show_about)
menubar.add_cascade(label="Ayuda", menu=help_menu)

root.config(menu=menubar)

# ======= PLOTS =======
import matplotlib as mpl
plt.rcParams.update({
    "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "font.family": "Segoe UI",
})
plot_card=ttk.LabelFrame(main_area, text="📈 Seguimiento en vivo", style="Card.TLabelframe", padding=(12, 10))
plot_card.pack(fill="both", expand=True, padx=16, pady=(0,12))

design_panel=ttk.LabelFrame(plot_card, text="🎯 Modo diseño de perfil", style="Card.TLabelframe", padding=(12, 10))
design_panel.pack(fill="x", padx=8, pady=(0, 12))

design_mode_var=tk.BooleanVar(value=False)
design_curve_var=tk.StringVar(value="BT")
design_status_var=tk.StringVar(value="BT: 0 pts | ET: 0 pts")
design_collapse_text=tk.StringVar(value="Ocultar opciones")

design_header=ttk.Frame(design_panel, style="Card.TFrame")
design_header.pack(fill="x")

design_toggle=ttk.Checkbutton(design_header, text="Activar modo diseño", variable=design_mode_var)
design_toggle.pack(side="left")

design_curve_box=ttk.Frame(design_header, style="Card.TFrame")
design_curve_box.pack(side="left", padx=(16,0))
design_bt_radio=ttk.Radiobutton(design_curve_box, text="Editar BT", value="BT", variable=design_curve_var)
design_bt_radio.pack(side="left", padx=(0,8))
design_et_radio=ttk.Radiobutton(design_curve_box, text="Editar ET", value="ET", variable=design_curve_var)
design_et_radio.pack(side="left")

design_body=ttk.Frame(design_panel, style="Card.TFrame")
design_body.pack(fill="x", pady=(8,0))

design_btns=ttk.Frame(design_body, style="Card.TFrame")
design_btns.pack(fill="x")

btn_design_load=ttk.Button(design_btns, text="📂 Cargar", width=12)
btn_design_load.pack(side="left", padx=4, pady=2)
btn_design_save=ttk.Button(design_btns, text="💾 Guardar", width=12)
btn_design_save.pack(side="left", padx=4, pady=2)
btn_design_clear=ttk.Button(design_btns, text="🧹 Limpiar curva", width=14)
btn_design_clear.pack(side="left", padx=4, pady=2)

design_help=ttk.Label(
    design_body,
    text="Haz clic en la gráfica para agregar puntos. Arrastra para moverlos y usa clic derecho para eliminar."
         " Puedes diseñar BT o ET y guardar el perfil para reutilizarlo antes de cada tueste.",
    style="CardText.TLabel",
    wraplength=460,
    justify="left",
)
design_help.pack(fill="x", pady=(6,6))

ttk.Label(design_body, textvariable=design_status_var, style="CardText.TLabel").pack(anchor="w")

def toggle_design_panel():
    if design_body.winfo_ismapped():
        design_body.pack_forget()
        design_collapse_text.set("Mostrar opciones")
    else:
        design_body.pack(fill="x", pady=(8,0))
        design_collapse_text.set("Ocultar opciones")

ttk.Button(design_header, textvariable=design_collapse_text, command=toggle_design_panel).pack(side="right")

events_panel=ttk.LabelFrame(plot_card, text="🗓️ Eventos del tueste", style="Card.TLabelframe", padding=(12, 10))
events_panel.pack(fill="x", padx=8, pady=(0, 12))
event_buttons=ttk.Frame(events_panel, style="Card.TFrame")
event_buttons.pack(fill="x")
for name in ["CHARGE","TP","DRY_END","1C","2C","DROP"]:
    ttk.Button(event_buttons, text=f"📌 {name}", command=lambda n=name: log_event(n)).pack(side="left", padx=4, pady=2)
ttk.Button(event_buttons, text="💾 Exportar CSV/PNG", command=export_all).pack(side="left", padx=4, pady=2)

plot_container=ttk.Frame(plot_card, style="Card.TFrame")
plot_container.pack(fill="both", expand=True)
fig,ax1=plt.subplots(1,1,figsize=(11.2,6.6),dpi=110)
fig.subplots_adjust(right=0.83)
fig.patch.set_facecolor(BG)
ax1.set_facecolor(BG); ax1.tick_params(colors=FG,labelsize=10)
for sp in ax1.spines.values(): sp.set_color(GRID)
ax1.grid(True,color=GRID,alpha=0.35,linewidth=0.7)
ax1.set_title("Roaster Scope — BT/ET + RoR")
ax1.set_ylabel("Temperatura (°C)")
ax_ror=ax1.twinx()
ax_ror.set_facecolor('none')
ax_ror.tick_params(colors="#a3e635",labelsize=10)
ax_ror.spines['right'].set_color('#a3e635')
ax_ror.set_ylabel("RoR (°C/min)", color="#a3e635")
ln_et,=ax1.plot([],[],label="ET",linewidth=2.2,color="#60a5fa")
ln_bt,=ax1.plot([],[],label="BT_est",linewidth=2.2,color="#f59e0b")
ln_set,=ax1.plot([],[],label="Set",linewidth=1.6,color="#94a3b8",linestyle="--")
ln_bt_proj,=ax1.plot([],[],label="BT forecast",linewidth=1.2,linestyle=":",color="#f59e0b")
ln_et_proj,=ax1.plot([],[],label="ET forecast",linewidth=1.2,linestyle=":",color="#60a5fa")
design_bt_line,=ax1.plot([],[],label="BT diseño",linewidth=1.6,linestyle="-.",color="#fb923c",alpha=0.85)
design_et_line,=ax1.plot([],[],label="ET diseño",linewidth=1.6,linestyle="-.",color="#60a5fa",alpha=0.55)
design_bt_points,=ax1.plot([],[],marker="s",markersize=5,color="#f97316",linestyle="None",alpha=0.9,label="_nolegend_")
design_et_points,=ax1.plot([],[],marker="s",markersize=5,color="#3b82f6",linestyle="None",alpha=0.9,label="_nolegend_")
eta1_line=ax1.axvline(np.nan,color="#f472b6",linestyle="--",linewidth=1.2,alpha=0.85,label="ETA 1C")
eta1_line.set_visible(False)
bt_now_marker,=ax1.plot([],[],marker="o",markersize=5,color="#f59e0b",linestyle="None",alpha=0.9,label="_nolegend_")
bt_future_marker,=ax1.plot([],[],marker="D",markersize=6,color="#f59e0b",linestyle="None",fillstyle="none",alpha=0.9,label="_nolegend_")
et_now_marker,=ax1.plot([],[],marker="o",markersize=5,color="#60a5fa",linestyle="None",alpha=0.9,label="_nolegend_")
et_future_marker,=ax1.plot([],[],marker="D",markersize=6,color="#60a5fa",linestyle="None",fillstyle="none",alpha=0.9,label="_nolegend_")
bt_info_text=ax1.text(0.02,0.96,"",transform=ax1.transAxes,color="#fbbf24",fontsize=10,va="top")
et_info_text=ax1.text(0.02,0.88,"",transform=ax1.transAxes,color="#93c5fd",fontsize=10,va="top")
eta1_plot_text=ax1.text(0.98,0.96,"",transform=ax1.transAxes,color="#f472b6",fontsize=10,va="top",ha="right")
ax1.set_ylim(90.0, 240.0)
ln_ror,=ax_ror.plot([],[],label="RoR",linewidth=2.0,color="#a3e635")
ln_ror_t,=ax_ror.plot([],[],label="RoR target",linewidth=1.6,color="#ef4444",linestyle="--")
def refresh_legend():
    handles, labels = ax1.get_legend_handles_labels()
    ror_handles, ror_labels = ax_ror.get_legend_handles_labels()
    ax1.legend(handles+ror_handles, labels+ror_labels, facecolor=BG, labelcolor=FG, edgecolor=GRID,
               loc="upper left", bbox_to_anchor=(1.02,1.0), borderaxespad=0.0)
refresh_legend()
ax1.set_xlabel("Tiempo (min)")
canvas=FigureCanvasTkAgg(fig, master=plot_container)
canvas_widget=canvas.get_tk_widget()
canvas_widget.pack(fill="both",expand=True)

view_panel=ttk.LabelFrame(plot_card, text="🧭 Navegación de gráfica", style="Card.TLabelframe", padding=(12, 10))
view_panel.pack(fill="x", padx=8, pady=(6, 10))
view_panel.columnconfigure(1, weight=1)
view_panel.columnconfigure(3, weight=1)
view_panel.columnconfigure(5, weight=1)

x_window_var=tk.DoubleVar(value=8.0)
x_offset_var=tk.DoubleVar(value=0.0)
ror_scale_var=tk.DoubleVar(value=12.0)

def apply_view_range():
    try:
        width=max(1.0,float(x_window_var.get()))
    except Exception:
        width=8.0
    try:
        offset=max(0.0,float(x_offset_var.get()))
    except Exception:
        offset=0.0
    start=offset
    end=start+width
    ax1.set_xlim(start,end)
    try:
        rmax=max(1.0,float(ror_scale_var.get()))
    except Exception:
        rmax=12.0
    ax_ror.set_ylim(-rmax*0.25, rmax)
    canvas.draw_idle()

def update_pan_limit(xmax_min):
    try:
        width=max(1.0,float(x_window_var.get()))
    except Exception:
        width=8.0
    x_offset_var.set(min(x_offset_var.get(), max(0.0, xmax_min-width)))
    pan_slider.configure(to=max(0.0, xmax_min-width))

ttk.Label(view_panel, text="Zoom (min)", style="CardText.TLabel").grid(row=0, column=0, sticky="w")
zoom_slider=ttk.Scale(view_panel, from_=2, to=18, variable=x_window_var, command=lambda *_: apply_view_range())
zoom_slider.grid(row=0, column=1, sticky="ew", padx=(6,12))
ttk.Label(view_panel, text="Pan (min)", style="CardText.TLabel").grid(row=0, column=2, sticky="w")
pan_slider=ttk.Scale(view_panel, from_=0, to=20, variable=x_offset_var, command=lambda *_: apply_view_range())
pan_slider.grid(row=0, column=3, sticky="ew", padx=(6,12))
ttk.Label(view_panel, text="RoR escala", style="CardText.TLabel").grid(row=0, column=4, sticky="w")
ror_slider=ttk.Scale(view_panel, from_=6, to=30, variable=ror_scale_var, command=lambda *_: apply_view_range())
ror_slider.grid(row=0, column=5, sticky="ew")
apply_view_range()

history_panel=ttk.LabelFrame(plot_card, text="📂 Historial y comparación", style="Card.TLabelframe", padding=(12, 10))
history_panel.pack(fill="x", padx=8, pady=(0, 12))
history_panel.columnconfigure(1, weight=1)

history_path_var=tk.StringVar(value="Ninguna sesión cargada")
comparison_status=tk.StringVar(value="0 tuestes cargados para comparar")

def _parse_session_csv(path):
    try:
        df=pd.read_csv(path)
    except Exception as e:
        messagebox.showerror("Cargar sesión", f"No se pudo leer el archivo: {e}")
        return None
    if 'row_type' in df.columns:
        samples=df[df['row_type']=='sample']
        events=df[df['row_type']=='event']
    elif path.endswith('.samples.csv'):
        samples=df
        events_path=path.replace('.samples.csv','.events.csv')
        if os.path.exists(events_path):
            events=pd.read_csv(events_path)
        else:
            events=pd.DataFrame()
    else:
        samples=df
        events=pd.DataFrame()
    return {
        "t": list(samples.get('t_sec', [])),
        "et": list(samples.get('et_c', [])),
        "bt": list(samples.get('bt_est_c', [])),
        "ror": list(samples.get('ror', [])),
        "events": events.to_dict(orient='records'),
        "name": os.path.basename(path),
    }

overlay_colors=["#f87171", "#34d399", "#c084fc", "#22d3ee", "#facc15"]
history_overlay={"lines":None, "data":None}
comparison_traces=[]

def redraw_overlays():
    if history_overlay["lines"] and history_overlay["data"]:
        d=history_overlay["data"]
        history_overlay["lines"]["bt"].set_data([t/60.0 for t in d['t']], d['bt'])
        history_overlay["lines"]["et"].set_data([t/60.0 for t in d['t']], d['et'])
        history_overlay["lines"]["ror"].set_data([t/60.0 for t in d['t']], d['ror'])
    for trace in comparison_traces:
        data=trace["data"]
        color=trace["color"]
        trace["line"].set_data([t/60.0 for t in data['t']], data['bt'])
        trace["ror_line"].set_data([t/60.0 for t in data['t']], data['ror'])
        trace["line"].set_color(color)
        trace["ror_line"].set_color(color)
    refresh_legend()
    canvas.draw_idle()

def load_previous_session():
    path=filedialog.askopenfilename(filetypes=(("Datos de tueste","*.csv"),("Todos","*.*")))
    if not path:
        return
    data=_parse_session_csv(path)
    if not data:
        return
    history_path_var.set(f"Sesión: {data['name']}")
    if not history_overlay["lines"]:
        history_overlay["lines"]={
            "bt": ax1.plot([],[], linestyle='--', linewidth=1.2, color="#f472b6", label="BT sesión previa")[0],
            "et": ax1.plot([],[], linestyle='--', linewidth=1.2, color="#22d3ee", label="ET sesión previa")[0],
            "ror": ax_ror.plot([],[], linestyle=':', linewidth=1.4, color="#a855f7", label="RoR sesión previa")[0],
        }
    history_overlay["data"]=data
    redraw_overlays()

def add_comparison_trace():
    path=filedialog.askopenfilename(filetypes=(("Samples","*.csv"),("Todos","*.*")))
    if not path:
        return
    data=_parse_session_csv(path)
    if not data:
        return
    color=overlay_colors[len(comparison_traces)%len(overlay_colors)]
    line=ax1.plot([],[], linestyle='-', linewidth=1.1, color=color, alpha=0.65, label=f"BT: {data['name']}")[0]
    ror_line=ax_ror.plot([],[], linestyle=':', linewidth=1.0, color=color, alpha=0.9, label=f"RoR: {data['name']}")[0]
    comparison_traces.append({"line":line,"ror_line":ror_line,"data":data,"color":color})
    comparison_status.set(f"{len(comparison_traces)} tuestes cargados para comparar")
    redraw_overlays()

def clear_comparisons():
    for trace in comparison_traces:
        trace["line"].set_data([],[])
        trace["ror_line"].set_data([],[])
    comparison_traces.clear()
    comparison_status.set("0 tuestes cargados para comparar")
    redraw_overlays()

ttk.Button(history_panel, text="📂 Cargar sesión previa", command=load_previous_session).grid(row=0, column=0, sticky="w", padx=(0,8))
ttk.Label(history_panel, textvariable=history_path_var, style="CardText.TLabel").grid(row=0, column=1, sticky="w")
btn_compare=ttk.Button(history_panel, text="➕ Añadir a comparación", command=add_comparison_trace)
btn_compare.grid(row=1, column=0, sticky="w", padx=(0,8), pady=(8,0))
ttk.Label(history_panel, textvariable=comparison_status, style="CardText.TLabel").grid(row=1, column=1, sticky="w", pady=(8,0))
ttk.Button(history_panel, text="🧹 Limpiar comparación", command=clear_comparisons).grid(row=1, column=2, sticky="e", padx=(8,0), pady=(8,0))

design_edit_controls=[design_bt_radio, design_et_radio, btn_design_clear]

def update_design_summary():
    summary=f"BT: {len(DESIGN['bt_points'])} pts | ET: {len(DESIGN['et_points'])} pts"
    if DESIGN.get("last_path"):
        summary+=f" | Archivo: {os.path.basename(DESIGN['last_path'])}"
    design_status_var.set(summary)

def refresh_design_plot():
    bt_x=[p["x"] for p in DESIGN["bt_points"]]
    bt_y=[p["y"] for p in DESIGN["bt_points"]]
    et_x=[p["x"] for p in DESIGN["et_points"]]
    et_y=[p["y"] for p in DESIGN["et_points"]]
    design_bt_line.set_data(bt_x, bt_y)
    design_bt_points.set_data(bt_x, bt_y)
    design_et_line.set_data(et_x, et_y)
    design_et_points.set_data(et_x, et_y)
    update_design_summary()
    canvas.draw_idle()

def _current_design_points():
    return DESIGN["bt_points"] if DESIGN["active"] == "BT" else DESIGN["et_points"]

def update_design_ui_state(*_):
    active=bool(design_mode_var.get())
    DESIGN["mode"]=active
    DESIGN["drag_point"]=None
    DESIGN["dragging"]=False
    try:
        canvas_widget.configure(cursor="tcross" if active else "")
    except Exception:
        pass
    for w in design_edit_controls:
        if active:
            w.state(["!disabled"])
        else:
            w.state(["disabled"])

def on_design_curve_change(*_):
    DESIGN["active"]=design_curve_var.get()
    DESIGN["drag_point"]=None
    DESIGN["dragging"]=False

def clear_current_design(confirm=True):
    pts=_current_design_points()
    if not pts:
        return
    if confirm:
        if not messagebox.askyesno("Limpiar curva", "¿Deseas borrar los puntos de la curva seleccionada?"):
            return
    pts.clear()
    DESIGN["drag_point"]=None
    DESIGN["dragging"]=False
    refresh_design_plot()

def save_design_profile():
    data={
        "bt": [{"time_min": float(p["x"]), "temp_c": float(p["y"])} for p in DESIGN["bt_points"]],
        "et": [{"time_min": float(p["x"]), "temp_c": float(p["y"])} for p in DESIGN["et_points"]],
    }
    path=filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=(("Perfil de diseño","*.json"),("Todos","*.*")),
        initialfile=f"perfil-diseno-{timestamp_slug()}.json",
    )
    if not path:
        return
    try:
        with open(path,"w",encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        DESIGN["last_path"]=path
        update_design_summary()
        log(f"Perfil de diseño guardado en {path}")
    except Exception as e:
        messagebox.showerror("Guardar perfil", f"No se pudo guardar el perfil: {e}")

def _load_point_list(raw_list):
    pts=[]
    if not isinstance(raw_list, (list, tuple)):
        return pts
    for item in raw_list:
        try:
            if isinstance(item, dict):
                x=float(item.get("time_min", item.get("t", item.get("x", 0.0))))
                y=float(item.get("temp_c", item.get("temp", item.get("y", 0.0))))
            elif isinstance(item, (list, tuple)) and len(item)>=2:
                x=float(item[0]); y=float(item[1])
            else:
                continue
        except Exception:
            continue
        if not (math.isfinite(x) and math.isfinite(y)):
            continue
        pts.append({"x": x, "y": y})
    pts.sort(key=lambda p:p["x"])
    return pts

def load_design_profile():
    path=filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=(("Perfil de diseño","*.json"),("Todos","*.*")),
    )
    if not path:
        return
    try:
        with open(path,"r",encoding="utf-8") as fh:
            data=json.load(fh)
    except Exception as e:
        messagebox.showerror("Cargar perfil", f"No se pudo abrir el archivo: {e}")
        return
    DESIGN["bt_points"]=_load_point_list(data.get("bt") or data.get("BT"))
    DESIGN["et_points"]=_load_point_list(data.get("et") or data.get("ET"))
    DESIGN["last_path"]=path
    refresh_design_plot()
    log(f"Perfil de diseño cargado desde {path}")

def _nearest_point(points, x, y):
    if not points:
        return None, float("inf")
    best=None; best_dist=float("inf")
    for pt in points:
        dx=x-pt["x"]
        dy=(y-pt["y"])/6.0
        dist=math.hypot(dx, dy)
        if dist<best_dist:
            best=pt; best_dist=dist
    return best, best_dist

def on_design_press(event):
    if not DESIGN["mode"] or event.inaxes!=ax1:
        return
    if event.xdata is None or event.ydata is None:
        return
    points=_current_design_points()
    target, dist=_nearest_point(points, float(event.xdata), float(event.ydata))
    if event.button==3:
        if target and dist<0.6:
            points.remove(target)
            refresh_design_plot()
        return
    if event.button!=1:
        return
    if target and dist<0.6:
        DESIGN["drag_point"]=target
        DESIGN["dragging"]=True
    else:
        new_pt={"x": max(0.0, float(event.xdata)), "y": max(0.0, min(350.0, float(event.ydata)))}
        points.append(new_pt)
        points.sort(key=lambda p:p["x"])
        DESIGN["drag_point"]=new_pt
        DESIGN["dragging"]=True
        refresh_design_plot()

def on_design_motion(event):
    if not DESIGN["mode"] or not DESIGN["dragging"]:
        return
    if event.inaxes!=ax1 or event.xdata is None or event.ydata is None:
        return
    pt=DESIGN["drag_point"]
    if not pt:
        return
    pt["x"]=max(0.0, float(event.xdata))
    pt["y"]=max(0.0, min(350.0, float(event.ydata)))
    pts=_current_design_points()
    pts.sort(key=lambda p:p["x"])
    refresh_design_plot()

def on_design_release(_event):
    if DESIGN["dragging"]:
        DESIGN["dragging"]=False
        DESIGN["drag_point"]=None
        refresh_design_plot()

design_mode_var.trace_add("write", update_design_ui_state)
design_curve_var.trace_add("write", on_design_curve_change)
btn_design_load.config(command=load_design_profile)
btn_design_save.config(command=save_design_profile)
btn_design_clear.config(command=lambda: clear_current_design(confirm=True))

update_design_ui_state()
refresh_design_plot()

canvas.mpl_connect('button_press_event', on_design_press)
canvas.mpl_connect('motion_notify_event', on_design_motion)
canvas.mpl_connect('button_release_event', on_design_release)

event_artists=[]

def annotate_event(name, t, temp_c):
    tmin = (t/60.0) if t is not None else 0.0
    v=ax1.axvline(tmin, color="#f87171", linestyle="--", linewidth=1.2, alpha=0.9)
    marker=ax1.plot(tmin, temp_c, marker="o", color="#f87171", markersize=5)[0]
    text=ax1.text(
        tmin,
        temp_c+3,
        f"{name}\n{(t/60):.2f} min @ {temp_c:.1f}°C",
        color=FG,
        bbox=dict(boxstyle="round,pad=0.3", fc=GLASS, ec=GRID, alpha=0.9),
        ha="left",
        va="bottom",
        fontsize=9,
    )
    event_artists.append((v,marker,text))

def log_event(n):
    t=0.0 if not S.t0 else time.time()-S.t0
    bt=S.model.bt_hist[-1] if S.model.bt_hist else None
    et=current_et_c()
    temp = bt if (bt is not None and bt==bt) else et
    S.events.append({"event":n,"t_sec":round(t,2),"temp_c":round(temp,1)})
    annotate_event(n, t, temp)

# ======= CONSOLA DEBUG =======
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
    for ln in (ln_et, ln_bt, ln_set, ln_ror, ln_ror_t, ln_bt_proj, ln_et_proj,
               eta1_line,
               bt_now_marker, bt_future_marker, et_now_marker, et_future_marker):
        ln.set_data([],[])
    eta1_line.set_visible(False)
    bt_info_text.set_text(""); et_info_text.set_text(""); eta1_plot_text.set_text("")
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

        now=time.time()
        try:
            latency = now - float(getattr(S.reader, "last_update", 0.0))
        except Exception:
            latency = float("inf")
        sample_dt = float(getattr(S.reader, "sample_dt", 0.5))
        fresh_threshold = max(3.0 * sample_dt, 1.5)
        has_value = False
        try:
            has_value = math.isfinite(float(et_raw))
        except Exception:
            has_value = False
        sensor_ok = has_value and latency < fresh_threshold and bool(getattr(S.reader, "ok", False))
        sensor_status.itemconfig(SENSOR_DOT, fill=("#22c55e" if sensor_ok else "#ef4444"))
        if sensor_ok:
            sensor_var.set("Sensor: datos OK")
        elif has_value and getattr(S.reader, "ok", False):
            sensor_var.set("Sensor: lectura atrasada")
        else:
            sensor_var.set("Sensor: sin datos")

        ok=S.reader.ok
        status.itemconfig(DOT, fill=("#22c55e" if ok else "#ef4444"))
        if S.t0 is None: S.t0=now
        t=now-S.t0

        et=current_et_c()

        ror_nominal = 7.0
        eta_fc = None
        eta_drop = None

        if not S.samples:
            S.samples.append({"t_sec":0.0,"et_c":et if et==et else np.nan,"bt_est_c":np.nan,"ror":np.nan,"gas":S.gas,"air":S.air,"set_temp":S.set_temp})
        else:
            if S.running:
                bt, ror = S.model.step(t, et if et==et else (S.model.bt_hist[-1] if S.model.bt_hist else np.nan))
                # Update BT display
                try:
                    bt_disp = S.model.bt_hist[-1] if S.model.bt_hist else float('nan')
                    if showf.get():
                        BTVAR.set(f"BT {bt_disp*9/5+32:.1f} °F")
                    else:
                        BTVAR.set(f"BT {bt_disp:.1f} °C")
                except Exception:
                    pass
                try:
                    prof=json.load(open("profiles.json","r",encoding="utf-8"))[S.meta["process"]][S.meta["brewTarget"]]
                    S.model.alpha=float(prof["alpha"]); ror_nominal=float(prof["rorTarget"])
                    firstC=float(prof["firstCrackBT"]); dropBT=float(prof["dropBT"])
                except Exception:
                    firstC=196.0; dropBT=205.0
                S.samples.append({"t_sec":round(t,2),"et_c":round(et,2) if et==et else np.nan,"bt_est_c":round(bt,2),
                                  "ror":round(ror if isinstance(ror,float) else 0.0,3),"gas":S.gas,"air":S.air,"set_temp":S.set_temp})
                try:
                    def eta_str(s): 
                        if s is None: return "—"
                        return f"{int(s//60)}m{int(s%60)}s"
                    eta_fc = S.model.eta_seconds(firstC)
                    eta_drop = S.model.eta_seconds(dropBT)
                    eta1.config(text="ETA 1C: "+eta_str(eta_fc))
                    etad.config(text="ETA Drop: "+eta_str(eta_drop))
                except Exception as e:
                    log("ETA error: "+str(e))
            else:
                last=S.samples[-1]; last["et_c"]=round(et,2) if et==et else np.nan
                try:
                    prof=json.load(open("profiles.json","r",encoding="utf-8"))[S.meta["process"]][S.meta["brewTarget"]]
                    firstC=float(prof["firstCrackBT"]); dropBT=float(prof["dropBT"])
                except Exception:
                    firstC=196.0; dropBT=205.0
                eta_fc = S.model.eta_seconds(firstC)
                eta_drop = S.model.eta_seconds(dropBT)
                try:
                    def eta_str(s):
                        if s is None: return "—"
                        return f"{int(s//60)}m{int(s%60)}s"
                    eta1.config(text="ETA 1C: "+eta_str(eta_fc))
                    etad.config(text="ETA Drop: "+eta_str(eta_drop))
                except Exception:
                    pass

        t_arr=[s["t_sec"] for s in S.samples]
        t_min_arr=[t/60.0 for t in t_arr]
        et_arr=[s["et_c"] for s in S.samples]
        bt_arr=[s.get("bt_est_c",np.nan) for s in S.samples]
        # Projection: linear regression on last ~60 samples (~30s at 2Hz) to project 5 minutes ahead
        bt_proj_arr=[]; bt_proj_t=[]; et_proj_arr=[]; et_proj_t=[]
        try:
            import numpy as _np
            recent = min(60, len(t_arr))

            def _project(series):
                if recent < 6:
                    return None
                _t = _np.array(t_arr[-recent:], dtype=float)
                _y = _np.array([v for v in series[-recent:]], dtype=float)
                mask = _np.isfinite(_t) & _np.isfinite(_y)
                _t = _t[mask]; _y = _y[mask]
                if _t.size < 6:
                    return None
                a,b = _np.polyfit(_t, _y, 1)
                last_sample_t = t_arr[-1] if t_arr else 0.0
                t_end = last_sample_t + 900.0
                steps = max(90, int(max(1.0, t_end - _t[-1]) / 5.0))
                ts = list(_np.linspace(_t[-1], t_end, steps))
                return ts, list(a*_np.array(ts) + b)

            if len(t_arr) >= 2:
                bt_res = _project(bt_arr)
                if bt_res:
                    bt_proj_t, bt_proj_arr = bt_res
                et_res = _project(et_arr)
                if et_res:
                    et_proj_t, et_proj_arr = et_res
        except Exception:
            bt_proj_arr=[]; bt_proj_t=[]; et_proj_arr=[]; et_proj_t=[]

        ror_arr=[s.get("ror",np.nan) for s in S.samples]

        # Build RoR target as a curve if available
        ror_target_arr = [7.0]*len(t_arr)
        try:
            prof=json.load(open("profiles.json","r",encoding="utf-8"))[S.meta["process"]][S.meta["brewTarget"]]
            if "rorCurve" in prof:
                # rorCurve: [{"t":0, "v":9.0}, {"t":180, "v":6.0}, {"t":360, "v":4.0}]
                pts = prof["rorCurve"]
                pts = sorted([(float(p.get("t",0)), float(p.get("v",0))) for p in pts], key=lambda x:x[0])
                import bisect
                ts = [pt[0] for pt in pts]
                vs = [pt[1] for pt in pts]
                ror_target_arr = []
                for tt in t_arr:
                    i = bisect.bisect_right(ts, tt)
                    if i <= 0:
                        ror_target_arr.append(vs[0])
                    elif i >= len(ts):
                        ror_target_arr.append(vs[-1])
                    else:
                        # linear interp
                        t0,t1 = ts[i-1], ts[i]
                        v0,v1 = vs[i-1], vs[i]
                        frac = 0 if t1==t0 else (tt-t0)/(t1-t0)
                        ror_target_arr.append(v0 + frac*(v1-v0))
            else:
                r_start = float(prof.get("rorTargetStart", prof.get("rorTarget", 7.0)))
                r_mid = float(prof.get("rorTargetFirstCrack", max(4.5, r_start*0.7)))
                r_end = float(prof.get("rorTargetEnd", max(3.5, r_start*0.55)))
                first_bt = float(prof.get("firstCrackBT", 196.0))
                drop_bt = float(prof.get("dropBT", 205.0))
                if eta_fc is None:
                    eta_fc = S.model.eta_seconds(first_bt)
                if eta_drop is None:
                    eta_drop = S.model.eta_seconds(drop_bt)
                now_t = t_arr[-1] if t_arr else 0.0
                fc_time = (now_t + eta_fc) if eta_fc is not None else now_t + 240.0
                drop_time = (now_t + eta_drop) if eta_drop is not None else fc_time + 180.0
                if drop_time <= fc_time:
                    drop_time = fc_time + 120.0
                shape_points = [
                    (0.0, r_start),
                    (max(0.0, fc_time - 180.0), (r_start + r_mid) / 2.0),
                    (fc_time, r_mid),
                    (drop_time, r_end),
                ]
                shape_points = [(t, max(0.5, v)) for t, v in shape_points]
                import bisect
                base_ts = [pt[0] for pt in shape_points]
                base_vs = [pt[1] for pt in shape_points]
                ror_target_arr = []
                for tt in t_arr:
                    i = bisect.bisect_right(base_ts, tt)
                    if i <= 0:
                        ror_target_arr.append(base_vs[0])
                    elif i >= len(base_ts):
                        ror_target_arr.append(base_vs[-1])
                    else:
                        t0,t1 = base_ts[i-1], base_ts[i]
                        v0,v1 = base_vs[i-1], base_vs[i]
                        frac = 0.0 if t1==t0 else (tt - t0)/(t1 - t0)
                        ror_target_arr.append(v0 + frac*(v1 - v0))
        except Exception:
            # fallback constant
            ror_target_arr = [7.0]*len(t_arr)

        ln_et.set_data(t_min_arr, et_arr); ln_bt.set_data(t_min_arr, bt_arr); ln_set.set_data(t_min_arr, [S.set_temp]*len(t_arr))
        ln_ror.set_data(t_min_arr, ror_arr); ln_ror_t.set_data(t_min_arr, ror_target_arr)
        ln_bt_proj.set_data([tp/60.0 for tp in bt_proj_t], bt_proj_arr)
        ln_et_proj.set_data([tp/60.0 for tp in et_proj_t], et_proj_arr)

        def _set_marker(marker, tx, ty):
            try:
                fx = float(tx)
                fy = float(ty)
            except Exception:
                marker.set_data([], [])
                return
            if not (math.isfinite(fx) and math.isfinite(fy)):
                marker.set_data([], [])
                return
            marker.set_data([fx], [fy])

        current_t_min = t_min_arr[-1] if t_min_arr else float('nan')
        bt_current = bt_arr[-1] if bt_arr else float('nan')
        et_current = et_arr[-1] if et_arr else float('nan')
        bt_future_val = bt_proj_arr[-1] if bt_proj_arr else bt_current
        et_future_val = et_proj_arr[-1] if et_proj_arr else et_current
        bt_future_t = bt_proj_t[-1]/60.0 if bt_proj_t else float('nan')
        et_future_t = et_proj_t[-1]/60.0 if et_proj_t else float('nan')

        _set_marker(bt_now_marker, current_t_min, bt_current)
        _set_marker(et_now_marker, current_t_min, et_current)
        _set_marker(bt_future_marker, bt_future_t, bt_future_val)
        _set_marker(et_future_marker, et_future_t, et_future_val)

        def _fmt_temp(val):
            unit = "°F" if showf.get() else "°C"
            try:
                disp_c = float(val)
            except Exception:
                return f"—.— {unit}"
            if not math.isfinite(disp_c):
                return f"—.— {unit}"
            disp = disp_c
            if showf.get():
                disp = disp_c*9/5+32
            return f"{disp:.1f} {unit}"

        bt_info_text.set_text(f"BT {_fmt_temp(bt_current)} → {_fmt_temp(bt_future_val)}")
        et_info_text.set_text(f"ET {_fmt_temp(et_current)} → {_fmt_temp(et_future_val)}")

        def _fmt_eta(mins):
            if mins is None or not math.isfinite(mins):
                return ""
            total_sec = max(0.0, mins*60.0)
            mm = int(total_sec//60)
            ss = int(total_sec%60)
            return f"ETA 1C: {mm:02d}:{ss:02d}"

        if eta_fc is not None and t_arr:
            fc_time_min = (t_arr[-1] + eta_fc) / 60.0
            if math.isfinite(fc_time_min):
                y0, y1 = ax1.get_ylim()
                if not (math.isfinite(y0) and math.isfinite(y1)):
                    y0, y1 = 0.0, 1.0
                if y0 == y1:
                    y1 = y0 + 1.0
                eta1_line.set_data([fc_time_min, fc_time_min], [y0, y1])
                eta1_line.set_visible(True)
                eta1_plot_text.set_text(_fmt_eta(eta_fc/60.0))
            else:
                eta1_line.set_data([], [])
                eta1_line.set_visible(False)
                eta1_plot_text.set_text("")
        else:
            eta1_line.set_data([], [])
            eta1_line.set_visible(False)
            eta1_plot_text.set_text("")
        try:
            ror_target_current = ror_target_arr[-1] if ror_target_arr else ror_nominal
            current_ror = ror_arr[-1] if ror_arr else None
            sugg.config(text="Sugerencia: "+gas_air_suggestion(current_ror, ror_target_current))
        except Exception as e:
            log("Sugerencia error: "+str(e))

        ax1.relim(); ax1.autoscale_view()
        ax_ror.relim(); ax_ror.autoscale_view()
        # dynamic autoscale with margins so ET doesn't look flat
        try:
            import numpy as _np
            # AX1 limits
            yvals_source=[v for v in et_arr+bt_arr if v==v]
            for pts in (DESIGN["bt_points"], DESIGN["et_points"]):
                yvals_source.extend([float(p["y"]) for p in pts if p["y"]==p["y"]])
            if history_overlay["data"]:
                yvals_source.extend([float(v) for v in history_overlay["data"].get("bt",[]) if v==v])
                yvals_source.extend([float(v) for v in history_overlay["data"].get("et",[]) if v==v])
            for trace in comparison_traces:
                yvals_source.extend([float(v) for v in trace["data"].get("bt",[]) if v==v])
            yvals = _np.array(yvals_source, dtype=float)
            if yvals.size>3:
                ymin=float(_np.nanmin(yvals)); ymax=float(_np.nanmax(yvals))
                pad=max(3.0,(ymax-ymin)*0.15)
                lower = min(0.0, ymin-pad)
                upper = max(250.0, ymax+pad)
                if upper - lower < 25.0:
                    upper = lower + 25.0
                ax1.set_ylim(lower, upper)
            else:
                ax1.set_ylim(90.0, 240.0)

            x_candidates=[]
            def _extend_max(source_list):
                try:
                    if source_list:
                        x_candidates.append(max(float(v) for v in source_list))
                except Exception:
                    pass
            if t_min_arr:
                x_candidates.append(float(t_min_arr[-1]))
            if bt_proj_t:
                x_candidates.append(float(bt_proj_t[-1]/60.0))
            if et_proj_t:
                x_candidates.append(float(et_proj_t[-1]/60.0))
            for pts in (DESIGN["bt_points"], DESIGN["et_points"]):
                _extend_max([p.get("x") for p in pts])
            if history_overlay["data"]:
                _extend_max([t/60.0 for t in history_overlay["data"].get("t",[])])
            for trace in comparison_traces:
                _extend_max([t/60.0 for t in trace["data"].get("t",[])])
            xmax=max(x_candidates+[20.0])
            try:
                width=max(1.0,float(x_window_var.get()))
            except Exception:
                width=8.0
            update_pan_limit(xmax)
            start=min(max(0.0,float(x_offset_var.get())), max(0.0, xmax - width))
            end=start+width
            ax1.set_xlim(start, end)
            ax_ror.set_xlim(start, end)

            try:
                rmax_slider=max(1.0,float(ror_scale_var.get()))
            except Exception:
                rmax_slider=12.0
            ax_ror.set_ylim(-rmax_slider*0.25, rmax_slider)
        except Exception:
            pass

        count_var.set(f"Muestras: {len(S.samples)}")
    except Exception as e:
        log("Loop error: "+str(e)+"\\n"+traceback.format_exc())

ani=FuncAnimation(fig, animate, interval=int(1000/CFG["sample_hz"]))
root.protocol("WM_DELETE_WINDOW", lambda: (S.reader.stop(), root.destroy()))
root.mainloop()

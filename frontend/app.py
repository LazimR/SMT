import tkinter as tk
from tkinter import ttk, font as tkfont
import threading
import requests
import uuid
import random
import time
from datetime import datetime
from collections import deque


SERVER_URL   = "http://localhost:5000/leitura"   
SENSOR_ID    = "sensor-01"
INTERVAL_MS  = 3000          
HISTORY_MAX  = 50            

TEMP_MIN     = -10.0
TEMP_MAX     =  40.0


TEMP_ALERTA  = 10.0
TEMP_CRITICO = 15.0


BG_DARK   = "#0d0f14"
BG_PANEL  = "#13161e"
BG_CARD   = "#1a1e2a"
BG_ROW_A  = "#1d2132"
BG_ROW_B  = "#161926"

ACC_BLUE  = "#3a8fff"
ACC_CYAN  = "#00d4ff"

COL_NORM  = "#00e676"   # Normal
COL_ALRT  = "#ffc107"   # Alerta
COL_CRIT  = "#ff3d3d"   # Crítico
COL_PEND  = "#7a8099"   # Aguardando

FG_MAIN   = "#e8ecf4"
FG_DIM    = "#5a6180"
FG_MID    = "#9aa3be"

BORDER    = "#252a3a"


def status_color(status: str) -> str:
    s = (status or "").strip().lower()
    if "crít" in s or "critico" in s:
        return COL_CRIT
    if "alerta" in s:
        return COL_ALRT
    if "normal" in s:
        return COL_NORM
    return COL_PEND


def classify_locally(temp: float) -> str:
    if temp > TEMP_CRITICO:
        return "Crítico"
    if temp > TEMP_ALERTA:
        return "Alerta"
    return "Normal"



class SensorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de Temperatura · Sensor")
        self.geometry("860x680")
        self.minsize(760, 580)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

    
        self._auto_job   = None
        self._sending    = False
        self._history    = deque(maxlen=HISTORY_MAX)
        self._total_sent = 0
        self._total_err  = 0

        self._build_fonts()
        self._build_ui()


    def _build_fonts(self):
        self.f_title  = tkfont.Font(family="Courier", size=13, weight="bold")
        self.f_label  = tkfont.Font(family="Courier", size=9)
        self.f_value  = tkfont.Font(family="Courier", size=28, weight="bold")
        self.f_status = tkfont.Font(family="Courier", size=14, weight="bold")
        self.f_small  = tkfont.Font(family="Courier", size=8)
        self.f_mono   = tkfont.Font(family="Courier", size=9)
        self.f_btn    = tkfont.Font(family="Courier", size=10, weight="bold")
        self.f_head   = tkfont.Font(family="Courier", size=8, weight="bold")

   
    def _build_ui(self):
     
        hdr = tk.Frame(self, bg=BG_DARK)
        hdr.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(hdr, text="◈  SENSOR MONITOR", font=self.f_title,
                 bg=BG_DARK, fg=ACC_CYAN).pack(side="left")

        self._lbl_clock = tk.Label(hdr, text="", font=self.f_small,
                                   bg=BG_DARK, fg=FG_DIM)
        self._lbl_clock.pack(side="right")
        self._tick_clock()

     
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=20, pady=0)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

       
        self._build_footer()

   
    def _build_left(self, parent):
        left = tk.Frame(parent, bg=BG_DARK, width=290)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        left.pack_propagate(False)

        
        self._build_section(left, "SERVIDOR")
        card_srv = self._card(left)

        self._build_field(card_srv, "URL do Servidor")
        self._entry_url = self._entry(card_srv, SERVER_URL)

        self._build_field(card_srv, "ID do Sensor")
        self._entry_sid = self._entry(card_srv, SENSOR_ID)

       
        self._build_section(left, "LEITURA MANUAL")
        card_man = self._card(left)

        self._build_field(card_man, "Temperatura (°C)  [manual]")
        f_temp = tk.Frame(card_man, bg=BG_CARD)
        f_temp.pack(fill="x")
        self._var_temp = tk.StringVar(value="")
        tk.Entry(f_temp, textvariable=self._var_temp,
                 bg=BG_DARK, fg=FG_MAIN, insertbackground=ACC_CYAN,
                 relief="flat", font=self.f_mono,
                 bd=0, highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=ACC_BLUE, width=10).pack(side="left", ipady=5)
        tk.Label(f_temp, text="  (vazio = aleatório)", font=self.f_small,
                 bg=BG_CARD, fg=FG_DIM).pack(side="left")

        self._btn_send = self._btn(card_man, "▶  ENVIAR AGORA", self._send_once,
                                   ACC_BLUE, "#0a1f44")
        self._btn_send.pack(fill="x", pady=(10, 0))

     
        self._build_section(left, "ENVIO AUTOMÁTICO")
        card_auto = self._card(left)

        self._build_field(card_auto, "Intervalo (ms)")
        self._var_interval = tk.StringVar(value=str(INTERVAL_MS))
        self._entry(card_auto, "", var=self._var_interval)

        f_auto = tk.Frame(card_auto, bg=BG_CARD)
        f_auto.pack(fill="x", pady=(8, 0))
        f_auto.columnconfigure(0, weight=1)
        f_auto.columnconfigure(1, weight=1)

        self._btn_start = self._btn(f_auto, "⏵  INICIAR", self._start_auto,
                                    COL_NORM, "#002211")
        self._btn_start.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self._btn_stop = self._btn(f_auto, "⏹  PARAR", self._stop_auto,
                                   COL_CRIT, "#2a0000", state="disabled")
        self._btn_stop.grid(row=0, column=1, sticky="ew")

        
        self._build_section(left, "ESTATÍSTICAS")
        card_stat = self._card(left)

        row_s = tk.Frame(card_stat, bg=BG_CARD)
        row_s.pack(fill="x")
        self._lbl_sent = self._stat_item(row_s, "ENVIADAS", "0", COL_NORM)
        self._lbl_err  = self._stat_item(row_s, "ERROS",    "0", COL_CRIT)

   
    def _build_right(self, parent):
        right = tk.Frame(parent, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

     
        disp = tk.Frame(right, bg=BG_PANEL,
                        highlightthickness=1, highlightbackground=BORDER)
        disp.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        tk.Label(disp, text="TEMPERATURA ATUAL", font=self.f_head,
                 bg=BG_PANEL, fg=FG_DIM).pack(pady=(14, 0))

        self._lbl_temp_big = tk.Label(disp, text="--.- °C",
                                      font=self.f_value,
                                      bg=BG_PANEL, fg=ACC_CYAN)
        self._lbl_temp_big.pack()

        self._lbl_status = tk.Label(disp, text="● AGUARDANDO",
                                    font=self.f_status,
                                    bg=BG_PANEL, fg=COL_PEND)
        self._lbl_status.pack(pady=(2, 0))

        self._lbl_uuid = tk.Label(disp, text="UUID: —",
                                  font=self.f_small,
                                  bg=BG_PANEL, fg=FG_DIM)
        self._lbl_uuid.pack(pady=(4, 14))

        
        self._build_section_raw(right, "HISTÓRICO LOCAL", row=1)

        hist_frame = tk.Frame(right, bg=BG_CARD,
                              highlightthickness=1,
                              highlightbackground=BORDER)
        hist_frame.grid(row=2, column=0, sticky="nsew")
        right.rowconfigure(2, weight=1)

       
        cols = [("HORA",       80, "center"),
                ("TEMP (°C)",  90, "center"),
                ("STATUS",    100, "center"),
                ("UUID",      200, "w"),
                ("RESP HTTP",  80, "center")]

        hdr_f = tk.Frame(hist_frame, bg=BG_DARK)
        hdr_f.pack(fill="x")
        for txt, w, anc in cols:
            tk.Label(hdr_f, text=txt, font=self.f_head,
                     bg=BG_DARK, fg=FG_DIM, width=w//8,
                     anchor=anc).pack(side="left", padx=4, pady=4)

        tk.Frame(hist_frame, bg=BORDER, height=1).pack(fill="x")

       
        self._canvas = tk.Canvas(hist_frame, bg=BG_CARD,
                                 highlightthickness=0)
        sb = ttk.Scrollbar(hist_frame, orient="vertical",
                           command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._hist_inner = tk.Frame(self._canvas, bg=BG_CARD)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._hist_inner, anchor="nw")

        self._hist_inner.bind("<Configure>", self._on_inner_conf)
        self._canvas.bind("<Configure>", self._on_canvas_conf)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._col_widths = [w for _, w, _ in cols]
        self._col_anchors = [a for _, _, a in cols]

  
    def _build_footer(self):
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(8, 0))
        foot = tk.Frame(self, bg=BG_DARK)
        foot.pack(fill="x", padx=20, pady=6)
        self._lbl_last = tk.Label(foot, text="Nenhuma leitura enviada ainda.",
                                  font=self.f_small, bg=BG_DARK, fg=FG_DIM)
        self._lbl_last.pack(side="left")
        tk.Label(foot, text="Atividade 3 · SD",
                 font=self.f_small, bg=BG_DARK, fg=FG_DIM).pack(side="right")

    
    def _card(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=BG_CARD, padx=12, pady=10,
                     highlightthickness=1, highlightbackground=BORDER)
        f.pack(fill="x", pady=(0, 8))
        return f

    def _build_section(self, parent, text):
        tk.Label(parent, text=text, font=self.f_head,
                 bg=BG_DARK, fg=FG_DIM).pack(anchor="w", pady=(10, 2))

    def _build_section_raw(self, parent, text, row=0):
        f = tk.Frame(parent, bg=BG_DARK)
        f.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        f.columnconfigure(0, weight=1)

        tk.Label(f, text=text, font=self.f_head,
                 bg=BG_DARK, fg=FG_DIM).pack(side="left")

        tk.Button(f, text="✕  LIMPAR", font=self.f_small,
                  command=self._clear_history,
                  fg=COL_CRIT, bg=BG_DARK,
                  activeforeground=COL_CRIT, activebackground=BG_PANEL,
                  relief="flat", bd=0, cursor="hand2",
                  pady=0).pack(side="right")

    def _build_field(self, parent, text):
        tk.Label(parent, text=text, font=self.f_small,
                 bg=BG_CARD, fg=FG_DIM).pack(anchor="w")

    def _entry(self, parent, default="", var=None) -> tk.Entry:
        if var is None:
            var = tk.StringVar(value=default)
        e = tk.Entry(parent, textvariable=var,
                     bg=BG_DARK, fg=FG_MAIN, insertbackground=ACC_CYAN,
                     relief="flat", font=self.f_mono,
                     bd=0, highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=ACC_BLUE)
        e.pack(fill="x", ipady=5, pady=(0, 6))
        return e

    def _btn(self, parent, text, cmd, fg, bg_col,
             state="normal") -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         font=self.f_btn, fg=fg, bg=bg_col,
                         activeforeground=fg, activebackground=BG_DARK,
                         relief="flat", bd=0, cursor="hand2",
                         state=state, pady=6)

    def _stat_item(self, parent, label, val, color) -> tk.Label:
        f = tk.Frame(parent, bg=BG_CARD)
        f.pack(side="left", expand=True, fill="x", padx=(0, 8))
        tk.Label(f, text=label, font=self.f_small,
                 bg=BG_CARD, fg=FG_DIM).pack(anchor="w")
        lbl = tk.Label(f, text=val, font=self.f_status,
                       bg=BG_CARD, fg=color)
        lbl.pack(anchor="w")
        return lbl

   
    def _tick_clock(self):
        self._lbl_clock.configure(
            text=datetime.now().strftime("  %Y-%m-%d  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    def _send_once(self):
        if self._sending:
            return
        self._sending = True
        self._btn_send.configure(state="disabled")
        threading.Thread(target=self._do_send, daemon=True).start()

    def _do_send(self):
        url       = self._entry_url.get().strip() or SERVER_URL
        sensor_id = self._entry_sid.get().strip() or SENSOR_ID

        
        manual = self._var_temp.get().strip()
        try:
            temp = float(manual) if manual else round(
                random.uniform(TEMP_MIN, TEMP_MAX), 2)
        except ValueError:
            temp = round(random.uniform(TEMP_MIN, TEMP_MAX), 2)

        req_uuid  = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        status_local = classify_locally(temp)

        payload = {
            "id":          req_uuid,
            "sensor_id":   sensor_id,
            "temperatura": temp,
            "timestamp":   timestamp,
        }


        http_code = "—"
        status_srv = None
        try:
            resp      = requests.post(url, json=payload, timeout=5)
            http_code = str(resp.status_code)
            data      = resp.json()
            status_srv = data.get("status_logico", status_local)
        except requests.exceptions.ConnectionError:
            http_code = "CONN ERR"
        except requests.exceptions.Timeout:
            http_code = "TIMEOUT"
        except Exception:
            http_code = "ERRO"

        status_final = status_srv or status_local

        record = {
            "hora":     datetime.now().strftime("%H:%M:%S"),
            "temp":     temp,
            "status":   status_final,
            "uuid":     req_uuid[:8] + "…",
            "http":     http_code,
        }
        if "ERR" in http_code or "ERRO" in http_code or "TIME" in http_code:
            self._total_err += 1
        else:
            self._total_sent += 1

        self._history.appendleft(record)
        self.after(0, self._refresh_ui, temp, status_final,
                   req_uuid, record)

    def _refresh_ui(self, temp, status, req_uuid, record):
        
        self._lbl_temp_big.configure(
            text=f"{temp:+.2f} °C",
            fg=status_color(status))
        self._lbl_status.configure(
            text=f"● {status.upper()}",
            fg=status_color(status))
        self._lbl_uuid.configure(
            text=f"UUID: {req_uuid}")

       
        self._lbl_sent.configure(text=str(self._total_sent))
        self._lbl_err.configure(text=str(self._total_err))

       
        self._lbl_last.configure(
            text=f"Última: {record['hora']}  |  "
                 f"{temp:+.2f}°C  |  {status}  |  HTTP {record['http']}")

        
        self._rebuild_history()

        self._sending = False
        self._btn_send.configure(state="normal")

   
    def _rebuild_history(self):
        for w in self._hist_inner.winfo_children():
            w.destroy()

        for i, rec in enumerate(self._history):
            bg = BG_ROW_A if i % 2 == 0 else BG_ROW_B
            row = tk.Frame(self._hist_inner, bg=bg)
            row.pack(fill="x")

            vals = [rec["hora"], f"{rec['temp']:+.2f}",
                    rec["status"], rec["uuid"], rec["http"]]
            sc   = status_color(rec["status"])

            for j, (val, w, anc) in enumerate(
                    zip(vals, self._col_widths, self._col_anchors)):
                fg = sc if j == 2 else (FG_MID if j != 3 else FG_DIM)
                tk.Label(row, text=val, font=self.f_mono,
                         bg=bg, fg=fg, width=w // 8,
                         anchor=anc).pack(side="left", padx=4, pady=2)

    def _clear_history(self):
        self._history.clear()
        self._rebuild_history()
        self._lbl_last.configure(text="Histórico limpo.")


    def _start_auto(self):
        try:
            ms = int(self._var_interval.get())
        except ValueError:
            ms = INTERVAL_MS
        self._btn_start.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        self._schedule_auto(ms)

    def _schedule_auto(self, ms):
        self._send_once()
        self._auto_job = self.after(ms, lambda: self._schedule_auto(ms))

    def _stop_auto(self):
        if self._auto_job:
            self.after_cancel(self._auto_job)
            self._auto_job = None
        self._btn_start.configure(state="normal")
        self._btn_stop.configure(state="disabled")

    
    def _on_inner_conf(self, _):
        self._canvas.configure(
            scrollregion=self._canvas.bbox("all"))

    def _on_canvas_conf(self, e):
        self._canvas.itemconfig(self._canvas_win, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")


if __name__ == "__main__":
    app = SensorApp()
    app.mainloop()

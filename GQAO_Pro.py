#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GQAO Pro v2.0 — PROMACAB S.A. | tkinter pur, zéro dépendance externe"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, os, sys, csv
from datetime import datetime, date

# ── CHEMINS ──────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gqao_pro.db")

# ── PALETTE SOMBRE ───────────────────────────────────────────
C = dict(
    bg="#0e1117", bg2="#161b27", bgc="#1c2333", bgh="#212d40",
    acc="#f5a623", acc2="#fbbf24",
    t1="#e2e8f0", t2="#8892a4", t3="#4a5568",
    red="#ef4444", redb="#2d1515",
    yel="#eab308", yelb="#2a2410",
    grn="#22c55e", grnb="#0d2315",
    blu="#3b82f6", blub="#0d1e3d",
    bdr="#2a3448",
)

ILUO_COLORS = {
    0: ("#2d1515", "#854040", "—"),
    1: ("#2a2410", "#a07d10", "I"),
    2: ("#0d2316", "#1d7048", "L"),
    3: ("#0d2315", "#22c55e", "U"),
    4: ("#0d1e3d", "#3b82f6", "O"),
}
ILUO_LABELS = {0:"— Non habilité",1:"I  Initié",2:"L  Libre",3:"U  Autonome",4:"O  Formateur"}

# ── STYLE GLOBAL ttk ─────────────────────────────────────────
def apply_style(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=C["bg2"], foreground=C["t1"],
                 fieldbackground=C["bgc"], borderwidth=0, relief="flat",
                 font=("Segoe UI", 9))
    s.configure("TFrame", background=C["bg2"])
    s.configure("TLabel", background=C["bg2"], foreground=C["t1"])
    s.configure("TButton", background=C["bgc"], foreground=C["t1"],
                 padding=(10,5), relief="flat", borderwidth=1)
    s.map("TButton", background=[("active", C["bgh"])])
    s.configure("Accent.TButton", background=C["acc"], foreground="#000",
                 font=("Segoe UI", 9, "bold"))
    s.map("Accent.TButton", background=[("active", C["acc2"])])
    s.configure("Danger.TButton", background=C["redb"], foreground=C["red"])
    s.map("Danger.TButton", background=[("active", "#3d1a1a")])
    s.configure("Treeview", background=C["bgc"], foreground=C["t1"],
                 fieldbackground=C["bgc"], rowheight=26, borderwidth=0,
                 font=("Segoe UI", 9))
    s.configure("Treeview.Heading", background=C["bg2"], foreground=C["t2"],
                 relief="flat", font=("Courier New", 9, "bold"), borderwidth=0)
    s.map("Treeview", background=[("selected", C["bgh"])],
          foreground=[("selected", C["acc"])])
    s.configure("TCombobox", fieldbackground=C["bgc"], background=C["bgc"],
                 foreground=C["t1"], selectbackground=C["bgh"],
                 arrowcolor=C["t2"], borderwidth=1)
    s.map("TCombobox", fieldbackground=[("readonly", C["bgc"])],
          selectbackground=[("readonly", C["bgh"])])
    s.configure("TEntry", fieldbackground=C["bgc"], foreground=C["t1"],
                 insertcolor=C["t1"], borderwidth=1)
    s.configure("Scrollbar.TScrollbar", background=C["bg2"],
                 troughcolor=C["bg"], arrowcolor=C["t3"])
    s.configure("TNotebook", background=C["bg"])
    s.configure("TNotebook.Tab", background=C["bgc"], foreground=C["t2"],
                 padding=(14,6))
    s.map("TNotebook.Tab", background=[("selected", C["bgh"])],
          foreground=[("selected", C["acc"])])
    s.configure("TSeparator", background=C["bdr"])
    # Tag colors for treeview
    return s

# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════
class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._create()
        self._seed()

    def _create(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS operators (
            id TEXT PRIMARY KEY, name TEXT, initials TEXT,
            team TEXT, poste TEXT, hire_date TEXT, active INTEGER DEFAULT 1, notes TEXT);
        CREATE TABLE IF NOT EXISTS operations (
            id TEXT PRIMARY KEY, name TEXT, required_level INTEGER DEFAULT 2,
            critical INTEGER DEFAULT 0, description TEXT, project TEXT);
        CREATE TABLE IF NOT EXISTS iluo_matrix (
            operator_id TEXT, operation_id TEXT, level INTEGER DEFAULT 0,
            validated_by TEXT, validation_date TEXT,
            PRIMARY KEY(operator_id, operation_id));
        CREATE TABLE IF NOT EXISTS non_conformites (
            id TEXT PRIMARY KEY, date TEXT, type TEXT, gravity TEXT,
            description TEXT, operator_id TEXT, operation_id TEXT,
            status TEXT DEFAULT 'Ouvert', cause TEXT, created_at TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS capa (
            id TEXT PRIMARY KEY, nc_id TEXT, title TEXT, responsible TEXT,
            method TEXT, date_open TEXT, date_target TEXT, date_close TEXT,
            status TEXT DEFAULT 'Ouvert', description TEXT, result TEXT);
        CREATE TABLE IF NOT EXISTS trainings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_id TEXT, module TEXT, trainer_id TEXT,
            planned_date TEXT, actual_date TEXT, duration TEXT,
            status TEXT DEFAULT 'Planifiée', result TEXT, score INTEGER, notes TEXT);
        CREATE TABLE IF NOT EXISTS production_of (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            of_number TEXT, reference TEXT, quantity INTEGER,
            operator_id TEXT, operation_id TEXT, machine TEXT,
            status TEXT DEFAULT 'En attente', conformity TEXT, alert TEXT, date TEXT);
        CREATE TABLE IF NOT EXISTS fournisseurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, country TEXT, category TEXT, score INTEGER DEFAULT 80,
            ppm INTEGER DEFAULT 200, nc_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Qualifié', notes TEXT);
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, type TEXT, auditor TEXT,
            planned_date TEXT, actual_date TEXT, status TEXT DEFAULT 'Planifié',
            scope TEXT, nb_findings INTEGER DEFAULT 0, notes TEXT);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        """)
        self.conn.commit()

    def _seed(self):
        if self.conn.execute("SELECT COUNT(*) FROM operators").fetchone()[0] > 0:
            return
        c = self.conn.cursor()
        ops = [
            ("OP001","Hassan Benmoussa","HB","Équipe A","Coupe / Dénudage","2019-03-15"),
            ("OP002","Fatima Zahra Idrissi","FI","Équipe A","Sertissage","2020-06-01"),
            ("OP003","Mohamed Alami","MA","Équipe B","Assemblage","2018-09-10"),
            ("OP004","Aicha Kettani","AK","Équipe B","Test / Inspection","2021-01-20"),
            ("OP005","Youssef Mansouri","YM","Équipe A","Polyvalent","2017-05-03"),
            ("OP006","Sara Lahlou","SL","Équipe C","Inspection / Étanch.","2022-03-14"),
            ("OP007","Omar Naciri","ON","Équipe C","Soudure","2019-11-08"),
            ("OP008","Nadia Rachidi","NR","Équipe B","Conditionnement","2020-02-25"),
            ("OP009","Karim Tahiri","KT","Équipe A","Manchonnage","2018-07-17"),
            ("OP010","Layla Squalli","LS","Équipe C","Assemblage","2023-01-09"),
            ("OP011","Ahmed Doukkali","AD","Équipe B","Polyvalent","2021-08-30"),
            ("OP012","Meriem Fassi","MF","Équipe A","Sertissage / Montage","2020-10-12"),
            ("OP013","Rachid Guessous","RG","Équipe C","Coupe / Soudure","2019-04-22"),
            ("OP014","Houda El Haj","HE","Équipe B","Test électrique","2022-07-05"),
            ("OP015","Jalal Pacha","JP","Équipe A","Assemblage / Cond.","2021-03-18"),
        ]
        c.executemany("INSERT INTO operators(id,name,initials,team,poste,hire_date) VALUES(?,?,?,?,?,?)", ops)
        opns = [
            ("COU","Coupe câble",2,1,"Coupe fils selon gamme","BJT/SCENIC"),
            ("DEN","Dénudage",2,0,"Dénudage extrémités","BJT/SCENIC"),
            ("SER","Sertissage Manuel",2,1,"Sertissage pinces manuelles","BJT"),
            ("SEA","Sertissage Auto",3,1,"Machine Komax / Schleuniger","BJT"),
            ("MON","Montage Connecteur",2,1,"Clipsage terminaux","BJT/SCENIC"),
            ("ASS","Assemblage Faisceau",2,0,"Montage tableau de câblage","BJT"),
            ("TES","Test Électrique",3,1,"Banco de test électrique","BJT"),
            ("INS","Inspection Visuelle",2,0,"Contrôle visuel final","ALL"),
            ("SOU","Soudure",3,1,"Soudure ultrasonique / TIG","SCENIC"),
            ("MAN","Manchonnage",2,0,"Pose manchons et rubans","BJT"),
            ("ETA","Test Étanchéité",3,1,"Test pression connecteurs","SCENIC"),
            ("CON","Conditionnement",1,0,"Emballage et étiquetage","ALL"),
        ]
        c.executemany("INSERT INTO operations(id,name,required_level,critical,description,project) VALUES(?,?,?,?,?,?)", opns)
        raw = [
            ("OP001",[4,4,3,2,3,2,2,3,1,2,0,2]),
            ("OP002",[3,3,4,4,3,3,2,3,0,1,2,3]),
            ("OP003",[2,2,2,1,4,4,3,3,2,3,1,2]),
            ("OP004",[1,2,3,3,2,2,4,4,0,0,3,2]),
            ("OP005",[4,4,4,3,2,1,1,2,3,4,2,1]),
            ("OP006",[2,1,2,2,3,3,2,4,0,2,4,3]),
            ("OP007",[3,3,1,0,2,3,3,2,4,3,0,2]),
            ("OP008",[2,2,3,3,3,2,2,3,1,2,2,4]),
            ("OP009",[4,3,2,2,1,2,2,1,3,4,1,2]),
            ("OP010",[1,1,2,2,3,4,3,3,0,1,2,3]),
            ("OP011",[3,3,3,4,2,2,1,2,2,2,3,2]),
            ("OP012",[2,2,4,4,4,3,2,3,0,1,2,1]),
            ("OP013",[4,4,2,1,2,2,2,2,4,3,1,2]),
            ("OP014",[1,2,2,2,3,3,4,4,1,2,3,3]),
            ("OP015",[3,2,1,0,2,4,3,2,2,3,2,4]),
        ]
        op_ids = ["COU","DEN","SER","SEA","MON","ASS","TES","INS","SOU","MAN","ETA","CON"]
        for oid, levels in raw:
            for i, lvl in enumerate(levels):
                c.execute("INSERT INTO iluo_matrix(operator_id,operation_id,level,validation_date) VALUES(?,?,?,?)",
                          (oid, op_ids[i], lvl, "2024-10-01"))
        ncs = [
            ("NC-2024-089","2024-11-28","Interne","Majeur","Court-circuit connecteur C045","OP002","SEA","Ouvert","Sertissage hors tolérance"),
            ("NC-2024-088","2024-11-27","Client","Critique","Faisceau P3 longueur hors tolérance","OP003","ASS","En cours","Coupe câble +3mm"),
            ("NC-2024-087","2024-11-27","Interne","Mineur","Manchon mal positionné lot 220","OP009","MAN","Clôturé","Non-respect gamme"),
            ("NC-2024-086","2024-11-26","Fournisseur","Majeur","Terminaux C045 déformés","","","En cours","Conditionnement fournisseur"),
            ("NC-2024-085","2024-11-25","Client","Critique","Test électrique KO — court-circuit","OP014","TES","Ouvert","Inversion fils B-C"),
            ("NC-2024-084","2024-11-25","Interne","Mineur","Étiquetage incorrect lot 221","OP008","CON","Clôturé","Erreur picking"),
            ("NC-2024-083","2024-11-24","Interne","Majeur","Sertissage insuffisant pin 14","OP011","SER","En cours","Pince non étalonnée"),
            ("NC-2024-082","2024-11-23","Client","Majeur","Longueur câble rouge hors spec","OP001","COU","Ouvert","Dérive machine coupe"),
        ]
        c.executemany("INSERT INTO non_conformites(id,date,type,gravity,description,operator_id,operation_id,status,cause) VALUES(?,?,?,?,?,?,?,?,?)", ncs)
        capas = [
            ("CAPA-2024-038","NC-2024-089","Maîtrise sertissage C045","OP002","8D","2024-11-28","2024-12-15","","Ouvert","",""),
            ("CAPA-2024-037","NC-2024-088","Conformité longueur faisceau P3","OP003","8D","2024-11-27","2024-12-10","","En cours","",""),
            ("CAPA-2024-036","NC-2024-085","Court-circuit test électrique","OP014","5 Pourquoi","2024-11-25","2024-12-08","","En cours","",""),
            ("CAPA-2024-035","NC-2024-083","Étalonnage pince sertissage","OP009","Ishikawa","2024-11-24","2024-12-05","","En cours","",""),
            ("CAPA-2024-031","NC-2024-079","Manchonnage gamme rev.3","OP009","5 Pourquoi","2024-11-18","2024-11-30","2024-11-28","Clôturé","","Efficace"),
        ]
        c.executemany("INSERT INTO capa(id,nc_id,title,responsible,method,date_open,date_target,date_close,status,description,result) VALUES(?,?,?,?,?,?,?,?,?,?,?)", capas)
        trainings = [
            ("OP001","Test étanchéité","OP006","2024-12-02","","4h","Planifiée","",None,""),
            ("OP004","Soudure TIG","OP007","2024-12-03","","8h","Planifiée","",None,""),
            ("OP005","Test électrique avancé","OP014","2024-12-04","","6h","Planifiée","",None,""),
            ("OP010","Sertissage automatique","OP002","2024-12-05","","8h","Planifiée","",None,""),
        ]
        c.executemany("INSERT INTO trainings(operator_id,module,trainer_id,planned_date,actual_date,duration,status,result,score,notes) VALUES(?,?,?,?,?,?,?,?,?,?)", trainings)
        fours = [
            ("SUMITOMO WIRING","JP","Connecteurs",72,340,8,"Sous surveillance",""),
            ("LEONI WIRE","DE","Fils & Câbles",91,89,2,"Qualifié",""),
            ("TE CONNECTIVITY","US","Terminaux",85,156,4,"Qualifié",""),
            ("DELPHI TECHNOLOGIES","UK","Connecteurs",78,220,6,"Sous surveillance",""),
            ("COFICAB MAROC","MA","Fils & Câbles",95,45,1,"Certifié",""),
            ("APTIV","IE","Systèmes câblage",88,112,3,"Qualifié",""),
        ]
        c.executemany("INSERT INTO fournisseurs(name,country,category,score,ppm,nc_count,status,notes) VALUES(?,?,?,?,?,?,?,?)", fours)
        audits_data = [
            ("Audit interne Production","Interne","Resp. Qualité","2024-12-12","","Planifié","Processus 7.5",0,""),
            ("Audit ILUO — Ligne P3","Interne","Dir. Production","2024-12-19","","Planifié","Compétences",0,""),
            ("Surveillance IATF 16949","Externe","BSI Group","2025-01-08","","Confirmé","Système complet",0,""),
            ("Audit qualité Renault","Client","Renault SQE","2025-01-15","","Confirmé","Qualité produit",0,""),
        ]
        c.executemany("INSERT INTO audits(title,type,auditor,planned_date,actual_date,status,scope,nb_findings,notes) VALUES(?,?,?,?,?,?,?,?,?)", audits_data)
        c.executemany("INSERT OR IGNORE INTO settings VALUES(?,?)", [
            ("company_name","PROMACAB S.A."),("company_city","Casablanca, Maroc"),
            ("standard","IATF 16949 : 2016"),
        ])
        self.conn.commit()

    def q(self, sql, p=()):
        return self.conn.execute(sql, p).fetchall()
    def run(self, sql, p=()):
        self.conn.execute(sql, p); self.conn.commit()
    def get_setting(self, k, d=""):
        r = self.conn.execute("SELECT value FROM settings WHERE key=?", (k,)).fetchone()
        return r[0] if r else d
    def set_setting(self, k, v):
        self.run("INSERT OR REPLACE INTO settings VALUES(?,?)", (k,v))
    def get_operators(self):
        return self.q("SELECT * FROM operators ORDER BY team,name")
    def get_operations(self):
        return self.q("SELECT * FROM operations ORDER BY name")
    def get_iluo_dict(self):
        return {(r["operator_id"],r["operation_id"]):r["level"] for r in self.q("SELECT * FROM iluo_matrix")}
    def set_iluo(self, op_id, opn_id, lvl):
        self.run("INSERT OR REPLACE INTO iluo_matrix(operator_id,operation_id,level,validation_date) VALUES(?,?,?,?)",
                 (op_id,opn_id,lvl,date.today().isoformat()))
    def get_ncs(self, sf="", gf="", tf=""):
        sql = "SELECT n.*,o.name as op_name,op2.name as opn_name FROM non_conformites n LEFT JOIN operators o ON n.operator_id=o.id LEFT JOIN operations op2 ON n.operation_id=op2.id WHERE 1=1"
        p=[]
        if sf: sql+=" AND n.status=?"; p.append(sf)
        if gf: sql+=" AND n.gravity=?"; p.append(gf)
        if tf: sql+=" AND n.type=?"; p.append(tf)
        return self.q(sql+" ORDER BY n.date DESC", p)
    def get_capas(self, sf=""):
        sql = "SELECT c.*,o.name as resp_name FROM capa c LEFT JOIN operators o ON c.responsible=o.id WHERE 1=1"
        p=[]
        if sf: sql+=" AND c.status=?"; p.append(sf)
        return self.q(sql+" ORDER BY c.date_open DESC", p)
    def get_trainings(self):
        return self.q("SELECT t.*,o.name as op_name,tr.name as trainer_name FROM trainings t LEFT JOIN operators o ON t.operator_id=o.id LEFT JOIN operators tr ON t.trainer_id=tr.id ORDER BY t.planned_date")
    def get_production(self):
        return self.q("SELECT p.*,o.name as op_name,op2.name as opn_name FROM production_of p LEFT JOIN operators o ON p.operator_id=o.id LEFT JOIN operations op2 ON p.operation_id=op2.id ORDER BY p.id DESC")
    def get_fournisseurs(self):
        return self.q("SELECT * FROM fournisseurs ORDER BY score DESC")
    def get_audits(self):
        return self.q("SELECT * FROM audits ORDER BY planned_date")
    def get_kpis(self):
        nc_open = self.conn.execute("SELECT COUNT(*) FROM non_conformites WHERE status='Ouvert'").fetchone()[0]
        nc_crit = self.conn.execute("SELECT COUNT(*) FROM non_conformites WHERE gravity='Critique' AND status!='Clôturé'").fetchone()[0]
        capa_open = self.conn.execute("SELECT COUNT(*) FROM capa WHERE status!='Clôturé'").fetchone()[0]
        total = self.conn.execute("SELECT COUNT(*) FROM iluo_matrix").fetchone()[0]
        qual = self.conn.execute("SELECT COUNT(*) FROM iluo_matrix im JOIN operations o ON im.operation_id=o.id WHERE im.level>=o.required_level AND im.level>0").fetchone()[0]
        hab = round(qual/total*100) if total else 0
        tr_plan = self.conn.execute("SELECT COUNT(*) FROM trainings WHERE status='Planifiée'").fetchone()[0]
        return dict(nc_open=nc_open, nc_crit=nc_crit, capa_open=capa_open, hab=hab, tr_plan=tr_plan)

# ═══════════════════════════════════════════════════════════════
# WIDGETS HELPERS
# ═══════════════════════════════════════════════════════════════
def make_tv(parent, cols, height=18):
    frm = tk.Frame(parent, bg=C["bgc"])
    tv = ttk.Treeview(frm, columns=[c[0] for c in cols], show="headings", height=height)
    for cid,lbl,w in cols:
        tv.heading(cid,text=lbl,anchor="w"); tv.column(cid,width=w,minwidth=30,anchor="w")
    vsb = ttk.Scrollbar(frm,orient="vertical",command=tv.yview)
    hsb = ttk.Scrollbar(frm,orient="horizontal",command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tv.grid(row=0,column=0,sticky="nsew"); vsb.grid(row=0,column=1,sticky="ns")
    hsb.grid(row=1,column=0,sticky="ew")
    frm.rowconfigure(0,weight=1); frm.columnconfigure(0,weight=1)
    tv.tag_configure("rouge", foreground="#fca5a5")
    tv.tag_configure("jaune", foreground="#fde68a")
    tv.tag_configure("vert",  foreground="#86efac")
    tv.tag_configure("bleu",  foreground="#93c5fd")
    return frm, tv

def lbl_val(parent, text, row, col=0, span=1, bold=False, color=None):
    f = ("Segoe UI", 9, "bold") if bold else ("Segoe UI", 9)
    fg = color or C["t1"]
    ttk.Label(parent, text=text, font=f, foreground=fg, background=C["bg2"]).grid(
        row=row, column=col, columnspan=span, sticky="w", padx=8, pady=3)

def field(parent, label, row, val="", choices=None, width=26):
    ttk.Label(parent, text=label, foreground=C["t2"],
              background=C["bg2"], font=("Courier New",9)).grid(
        row=row, column=0, sticky="w", padx=(12,8), pady=4)
    var = tk.StringVar(value=val)
    if choices:
        cb = ttk.Combobox(parent, textvariable=var, values=choices,
                          state="readonly", width=width)
        cb.grid(row=row, column=1, sticky="ew", padx=(0,12), pady=4)
    else:
        e = ttk.Entry(parent, textvariable=var, width=width+2)
        e.grid(row=row, column=1, sticky="ew", padx=(0,12), pady=4)
    return var

def section_bar(parent, text, fg=None):
    f = tk.Frame(parent, bg=C["bgh"], height=32)
    f.pack(fill="x"); f.pack_propagate(False)
    tk.Label(f, text=f"  {text}", bg=C["bgh"], fg=fg or C["acc"],
             font=("Courier New",10,"bold")).pack(side="left",pady=6)
    return f

def kpi_card(parent, col, label, value, unit, color, row=0):
    f = tk.Frame(parent, bg=C["bgc"], bd=0, highlightthickness=1,
                 highlightbackground=C["bdr"])
    f.grid(row=row, column=col, padx=5, pady=4, sticky="nsew")
    tk.Frame(f, bg=color, height=3).pack(fill="x")
    tk.Label(f, text=label, bg=C["bgc"], fg=C["t3"],
             font=("Courier New",8)).pack(pady=(8,2))
    tk.Label(f, text=value, bg=C["bgc"], fg=color,
             font=("Courier New",20,"bold")).pack()
    tk.Label(f, text=unit, bg=C["bgc"], fg=C["t2"],
             font=("Segoe UI",8)).pack(pady=(0,8))
    return f

def status_tag(status):
    m = {"Ouvert":"rouge","En cours":"jaune","Clôturé":"vert",
         "Planifiée":"bleu","À planifier":"jaune","Validée":"vert",
         "Critique":"rouge","Majeur":"jaune","Mineur":"vert",
         "Conforme":"vert","Non conforme":"rouge","Confirmé":"bleu"}
    return m.get(status,"")

# ═══════════════════════════════════════════════════════════════
# FORMULAIRE GÉNÉRIQUE (Toplevel)
# ═══════════════════════════════════════════════════════════════
class FormDialog(tk.Toplevel):
    def __init__(self, parent, title, fields_def, initial=None, width=480, height=500):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(bg=C["bgc"])
        self.resizable(True, True)
        self.grab_set()
        self.result = None
        self.vars = {}
        # Content
        canvas = tk.Canvas(self, bg=C["bgc"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        inner = tk.Frame(canvas, bg=C["bgc"])
        win_id = canvas.create_window((0,0), window=inner, anchor="nw")
        inner.columnconfigure(1, weight=1)
        def _on_frame_config(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_config(e):
            canvas.itemconfig(win_id, width=e.width)
        inner.bind("<Configure>", _on_frame_config)
        canvas.bind("<Configure>", _on_canvas_config)
        for i, fd in enumerate(fields_def):
            key, label, ftype, default, opts = fd
            init_val = initial[key] if (initial and key in initial and initial[key] is not None) else default
            if ftype == "combo":
                v = field(inner, label, i, str(init_val), opts, 32)
            elif ftype == "text":
                ttk.Label(inner, text=label, foreground=C["t2"],
                          background=C["bgc"], font=("Courier New",9)).grid(
                    row=i, column=0, sticky="nw", padx=(12,8), pady=4)
                v = tk.StringVar(value=str(init_val))
                txt = tk.Text(inner, width=35, height=3, bg=C["bg2"], fg=C["t1"],
                              insertbackground=C["t1"], relief="flat", bd=1,
                              font=("Segoe UI",9))
                txt.insert("1.0", str(init_val))
                txt.grid(row=i, column=1, sticky="ew", padx=(0,12), pady=4)
                txt._var_ref = v
                txt._is_text = True
                v._text_widget = txt
            else:
                v = field(inner, label, i, str(init_val), None, 32)
            self.vars[key] = v
        # Buttons
        bf = tk.Frame(self, bg=C["bgc"])
        bf.pack(fill="x", padx=12, pady=10, side="bottom")
        tk.Button(bf, text="  ✓  Enregistrer  ", bg=C["acc"], fg="#000",
                  font=("Segoe UI",10,"bold"), relief="flat", bd=0,
                  cursor="hand2", command=self._save).pack(side="right", padx=(6,0))
        tk.Button(bf, text="  Annuler  ", bg=C["bgc"], fg=C["t2"],
                  font=("Segoe UI",9), relief="flat", bd=1,
                  cursor="hand2", command=self.destroy).pack(side="right")
        self.wait_window()

    def _save(self):
        data = {}
        for k, v in self.vars.items():
            if hasattr(v, '_text_widget'):
                data[k] = v._text_widget.get("1.0", "end-1c").strip()
            else:
                data[k] = v.get().strip()
        self.result = data
        self.destroy()

# ═══════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════
class GQAOApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = DB()
        apply_style(self)
        self.title(f"GQAO Pro v2.0 — {self.db.get_setting('company_name','PROMACAB S.A.')}")
        self.geometry("1300x780")
        self.minsize(1000,650)
        self.configure(bg=C["bg"])
        self._build()
        self._nav("dashboard")

    # ─── STRUCTURE ──────────────────────────────────────────
    def _build(self):
        self._build_header()
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self.content = tk.Frame(body, bg=C["bg"])
        self.content.pack(side="left", fill="both", expand=True)
        self.pages = {}
        for name, builder in [
            ("dashboard", self._page_dashboard),
            ("nc",        self._page_nc),
            ("capa",      self._page_capa),
            ("iluo",      self._page_iluo),
            ("trainings", self._page_trainings),
            ("operators", self._page_operators),
            ("operations",self._page_operations),
            ("production",self._page_production),
            ("fournisseurs",self._page_fournisseurs),
            ("audits",    self._page_audits),
            ("settings",  self._page_settings),
        ]:
            f = tk.Frame(self.content, bg=C["bg"])
            self.pages[name] = f
            builder(f)

    def _build_header(self):
        h = tk.Frame(self, bg=C["bg2"], height=50)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text=" GQAO", bg=C["bg2"], fg=C["acc"],
                 font=("Courier New",14,"bold")).pack(side="left")
        tk.Label(h, text="Pro  ", bg=C["bg2"], fg=C["t2"],
                 font=("Courier New",14)).pack(side="left")
        tk.Frame(h, bg=C["bdr"], width=1).pack(side="left", fill="y", padx=8, pady=12)
        self.company_lbl = tk.Label(h, text=self.db.get_setting("company_name","PROMACAB S.A."),
                                    bg=C["bg2"], fg=C["t2"], font=("Segoe UI",10))
        self.company_lbl.pack(side="left", padx=4)
        tk.Label(h, text="IATF 16949 | ISO 9001", bg=C["bg2"], fg=C["t3"],
                 font=("Courier New",9)).pack(side="left", padx=12)
        self.clock_lbl = tk.Label(h, text="", bg=C["bg2"], fg=C["t3"],
                                  font=("Courier New",9))
        self.clock_lbl.pack(side="right", padx=16)
        tk.Label(h, text="Resp. Qualité ▣", bg=C["bg2"], fg=C["t2"],
                 font=("Segoe UI",9)).pack(side="right", padx=8)
        self._tick()

    def _tick(self):
        self.clock_lbl.configure(text=datetime.now().strftime("%d/%m/%Y  %H:%M"))
        self.after(30000, self._tick)

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["bg2"], width=200)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)
        self._nav_btns = {}
        def sec(t): tk.Label(sb,text=t,bg=C["bg2"],fg=C["t3"],
                             font=("Courier New",8)).pack(fill="x",padx=12,pady=(10,2))
        def btn(k,t,m,hl=False):
            b = tk.Button(sb, text=t, bg=C["bg2"], fg=C["t2"],
                          font=("Segoe UI",10), relief="flat", anchor="w",
                          padx=14, pady=6, cursor="hand2",
                          activebackground=C["bgh"], activeforeground=C["acc"],
                          command=lambda m=m: self._nav(m))
            b.pack(fill="x", padx=4, pady=1)
            self._nav_btns[k] = b
        sec("APERÇU")
        btn("dashboard","  📊  Dashboard KPI","dashboard")
        sec("QUALITÉ PRODUIT")
        btn("nc","  📌  Non-Conformités","nc")
        btn("capa","  🛠   CAPA — 8D","capa")
        btn("audits","  📑  Audits","audits")
        sec("PRODUCTION")
        btn("production","  🏭  Traçabilité OF","production")
        btn("fournisseurs","  📦  Fournisseurs","fournisseurs")
        sec("COMPÉTENCES ★")
        btn("iluo","  🎓  Matrice ILUO","iluo",True)
        btn("trainings","  📅  Formations","trainings")
        sec("RÉFÉRENTIELS")
        btn("operators","  👤  Opérateurs","operators")
        btn("operations","  ⚙   Opérations","operations")
        btn("settings","  ⚙   Paramètres","settings")
        tk.Label(sb,text="v2.0 © PROMACAB 2024",bg=C["bg2"],fg=C["t3"],
                 font=("Courier New",7)).pack(side="bottom",pady=8)

    def _nav(self, name):
        for f in self.pages.values(): f.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        for k,b in self._nav_btns.items():
            if k == name:
                b.configure(bg=C["bgh"], fg=C["acc"],
                            font=("Segoe UI",10,"bold"))
            else:
                b.configure(bg=C["bg2"], fg=C["t2"],
                            font=("Segoe UI",10))
        rf = {
            "dashboard":self._r_dashboard, "nc":self._r_nc,
            "capa":self._r_capa, "iluo":self._r_iluo,
            "trainings":self._r_trainings, "operators":self._r_operators,
            "operations":self._r_operations, "production":self._r_production,
            "fournisseurs":self._r_fournisseurs, "audits":self._r_audits,
        }
        if name in rf: rf[name]()

    def _mod_hdr(self, parent, title, sub=""):
        f = tk.Frame(parent, bg=C["bg"])
        f.pack(fill="x", padx=16, pady=(14,8))
        tk.Label(f, text=title, bg=C["bg"], fg=C["t1"],
                 font=("Segoe UI",15,"bold")).pack(side="left")
        if sub:
            tk.Label(f, text=f"  {sub}", bg=C["bg"], fg=C["t3"],
                     font=("Courier New",9)).pack(side="left", pady=(4,0))
        return f

    def _btn_row(self, parent):
        f = tk.Frame(parent, bg=C["bg"])
        f.pack(fill="x", padx=16, pady=(0,8))
        return f

    def _acc_btn(self, parent, text, cmd, color=None, side="left"):
        bg = color or C["acc"]; fg = "#000" if (color is None or color==C["acc"]) else C["t1"]
        b = tk.Button(parent, text=text, bg=bg, fg=fg,
                      font=("Segoe UI",9,"bold"), relief="flat", bd=0,
                      padx=12, pady=5, cursor="hand2",
                      activebackground=C["acc2"],
                      command=cmd)
        b.pack(side=side, padx=(0,6))
        return b

    def _sec_btn(self, parent, text, cmd, side="left", danger=False):
        bg = C["redb"] if danger else C["bgc"]
        fg = C["red"] if danger else C["t1"]
        b = tk.Button(parent, text=text, bg=bg, fg=fg,
                      font=("Segoe UI",9), relief="flat", bd=1,
                      padx=10, pady=5, cursor="hand2",
                      command=cmd)
        b.pack(side=side, padx=(0,6))
        return b

    # ══════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════
    def _page_dashboard(self, f):
        self._mod_hdr(f, "Dashboard Qualité", "Indicateurs temps réel — PROMACAB S.A.")
        # KPI frame
        self._dash_kpi_f = tk.Frame(f, bg=C["bg"])
        self._dash_kpi_f.pack(fill="x", padx=16, pady=(0,12))
        for i in range(6): self._dash_kpi_f.columnconfigure(i, weight=1)
        # Alert
        self._dash_alert_v = tk.StringVar()
        self._dash_alert_lbl = tk.Label(f, textvariable=self._dash_alert_v,
                                        bg=C["redb"], fg="#fca5a5",
                                        font=("Segoe UI",9), anchor="w", padx=12)
        self._dash_alert_lbl.pack(fill="x", padx=16, pady=(0,10))
        # Two columns
        mid = tk.Frame(f, bg=C["bg"])
        mid.pack(fill="both", expand=True, padx=16)
        mid.columnconfigure(0, weight=1); mid.columnconfigure(1, weight=1)
        # Pareto
        lf = tk.Frame(mid, bg=C["bgc"], bd=1, relief="flat",
                      highlightthickness=1, highlightbackground=C["bdr"])
        lf.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=4)
        tk.Label(lf, text="Pareto NC par gravité", bg=C["bgc"], fg=C["t2"],
                 font=("Courier New",9)).pack(anchor="w", padx=12, pady=(10,6))
        self._dash_pareto_f = tk.Frame(lf, bg=C["bgc"])
        self._dash_pareto_f.pack(fill="both", expand=True, padx=12, pady=(0,10))
        # ILUO Coverage
        rf = tk.Frame(mid, bg=C["bgc"], bd=1, relief="flat",
                      highlightthickness=1, highlightbackground=C["bdr"])
        rf.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=4)
        tk.Label(rf, text="Couverture ILUO par équipe", bg=C["bgc"], fg=C["t2"],
                 font=("Courier New",9)).pack(anchor="w", padx=12, pady=(10,6))
        self._dash_cov_f = tk.Frame(rf, bg=C["bgc"])
        self._dash_cov_f.pack(fill="both", expand=True, padx=12, pady=(0,10))
        # Recent NCs
        bot = tk.Frame(f, bg=C["bg"])
        bot.pack(fill="both", expand=True, padx=16, pady=(8,16))
        bot.columnconfigure(0, weight=3); bot.columnconfigure(1, weight=2)
        lf2 = tk.Frame(bot, bg=C["bgc"], highlightthickness=1, highlightbackground=C["bdr"])
        lf2.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        tk.Label(lf2, text="Dernières NC ouvertes", bg=C["bgc"], fg=C["t2"],
                 font=("Courier New",9)).pack(anchor="w", padx=12, pady=(10,4))
        tv_f, self._dash_nc_tv = make_tv(lf2, [
            ("id","ID NC",110),("date","Date",80),("grav","Gravité",75),
            ("desc","Description",260),("stat","Statut",75)], height=7)
        tv_f.pack(fill="both", expand=True, padx=6, pady=(0,6))
        rf2 = tk.Frame(bot, bg=C["bgc"], highlightthickness=1, highlightbackground=C["bdr"])
        rf2.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        tk.Label(rf2, text="Accès rapide", bg=C["bgc"], fg=C["t2"],
                 font=("Courier New",9)).pack(anchor="w", padx=12, pady=(10,6))
        for lbl, cmd in [("+ Créer NC",lambda:self._nav("nc")),
                         ("+ Planifier formation",lambda:self._nav("trainings")),
                         ("Matrice ILUO",lambda:self._nav("iluo")),
                         ("Export données CSV",self._export_csv)]:
            tk.Button(rf2, text=f"  {lbl}", bg=C["bgh"], fg=C["t1"],
                      font=("Segoe UI",9), relief="flat", anchor="w",
                      padx=8, pady=6, cursor="hand2", command=cmd).pack(
                fill="x", padx=10, pady=3)

    def _r_dashboard(self):
        kpis = self.db.get_kpis()
        for w in self._dash_kpi_f.winfo_children(): w.destroy()
        data = [
            ("NC OUVERTES",str(kpis["nc_open"]),"NC",C["red"] if kpis["nc_open"]>5 else C["yel"],0),
            ("NC CRITIQUES",str(kpis["nc_crit"]),"NC crit.",C["red"],1),
            ("CAPA EN COURS",str(kpis["capa_open"]),"actions",C["acc"],2),
            ("HABILITATION",f"{kpis['hab']}","%",C["red"] if kpis["hab"]<70 else C["grn"],3),
            ("FORMATIONS",str(kpis["tr_plan"]),"planifiées",C["blu"],4),
            ("PPM QUALITÉ","1247","ppm",C["yel"],5),
        ]
        for lbl,val,unit,col,ci in data:
            kpi_card(self._dash_kpi_f, ci, lbl, val, unit, col)
        # Alert
        self._dash_alert_v.set("  ⚠  3 habilitations expirées — Hassan B. / Sertissage Auto | Youssef M. / Test électrique | Ahmed D. / Sertissage Auto")
        # Pareto
        for w in self._dash_pareto_f.winfo_children(): w.destroy()
        ncs = self.db.get_ncs()
        from collections import Counter
        cnt = Counter(n["gravity"] for n in ncs if n["status"]!="Clôturé")
        colors = {"Critique":C["red"],"Majeur":C["yel"],"Mineur":C["grn"]}
        total = sum(cnt.values()) or 1
        for grav, c in sorted(cnt.items(), key=lambda x:-x[1]):
            pct = c/total
            col = colors.get(grav, C["t2"])
            rf = tk.Frame(self._dash_pareto_f, bg=C["bgc"])
            rf.pack(fill="x", pady=3)
            tk.Label(rf, text=f"{grav:<10}", bg=C["bgc"], fg=C["t2"],
                     font=("Courier New",9), width=12, anchor="w").pack(side="left")
            canvas = tk.Canvas(rf, bg=C["bg2"], height=16, highlightthickness=0)
            canvas.pack(side="left", fill="x", expand=True, padx=6)
            canvas.update_idletasks()
            w_ = canvas.winfo_width() or 200
            canvas.create_rectangle(0,2,max(4,int(w_*pct)),14,fill=col,outline="")
            tk.Label(rf, text=str(c), bg=C["bgc"], fg=col,
                     font=("Courier New",9), width=3).pack(side="right")
        # Coverage
        for w in self._dash_cov_f.winfo_children(): w.destroy()
        ops_all = self.db.get_operators()
        opns_all = self.db.get_operations()
        iluo_d = self.db.get_iluo_dict()
        teams = {}
        for op in ops_all: teams.setdefault(op["team"],[]).append(op["id"])
        for team, ids in sorted(teams.items()):
            tot = len(ids)*len(opns_all)
            q = sum(1 for oid in ids for opn in opns_all
                    if iluo_d.get((oid,opn["id"]),0)>=opn["required_level"] and iluo_d.get((oid,opn["id"]),0)>0)
            pct = round(q/tot*100) if tot else 0
            col = C["grn"] if pct>=80 else C["acc"] if pct>=60 else C["red"]
            rf = tk.Frame(self._dash_cov_f, bg=C["bgc"])
            rf.pack(fill="x", pady=4)
            tk.Label(rf, text=team, bg=C["bgc"], fg=C["t2"],
                     font=("Segoe UI",9), width=12, anchor="w").pack(side="left")
            canvas = tk.Canvas(rf, bg=C["bg2"], height=14, highlightthickness=0)
            canvas.pack(side="left", fill="x", expand=True, padx=4)
            canvas.update_idletasks()
            w_ = canvas.winfo_width() or 200
            canvas.create_rectangle(0,2,max(4,int(w_*pct/100)),12,fill=col,outline="")
            tk.Label(rf, text=f"{pct}%", bg=C["bgc"], fg=col,
                     font=("Courier New",9,"bold"), width=5).pack(side="right")
        # NC table
        self._dash_nc_tv.delete(*self._dash_nc_tv.get_children())
        for n in self.db.get_ncs()[:8]:
            tag = status_tag(n["gravity"])
            self._dash_nc_tv.insert("","end", values=(
                n["id"],n["date"],n["gravity"],(n["description"] or "")[:55],n["status"]),
                tags=(tag,))

    # ══════════════════════════════════════════════════════════
    # NON-CONFORMITÉS
    # ══════════════════════════════════════════════════════════
    def _page_nc(self, f):
        self._mod_hdr(f, "Non-Conformités", "Gestion complète NC — CRUD")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Créer NC", self._add_nc)
        self._sec_btn(br, "✏  Modifier", self._edit_nc)
        self._sec_btn(br, "🗑  Supprimer", self._del_nc, danger=True)
        tk.Label(br, text="  Statut:", bg=C["bg"], fg=C["t2"], font=("Segoe UI",9)).pack(side="left",padx=(8,2))
        self._nc_sf = tk.StringVar(value="Tous")
        cb1 = ttk.Combobox(br, textvariable=self._nc_sf, values=["Tous","Ouvert","En cours","Clôturé"],
                           state="readonly", width=10)
        cb1.pack(side="left", padx=2)
        cb1.bind("<<ComboboxSelected>>", lambda e: self._r_nc())
        tk.Label(br, text="  Gravité:", bg=C["bg"], fg=C["t2"], font=("Segoe UI",9)).pack(side="left",padx=(8,2))
        self._nc_gf = tk.StringVar(value="Toutes")
        cb2 = ttk.Combobox(br, textvariable=self._nc_gf, values=["Toutes","Critique","Majeur","Mineur"],
                           state="readonly", width=10)
        cb2.pack(side="left", padx=2)
        cb2.bind("<<ComboboxSelected>>", lambda e: self._r_nc())
        self._sec_btn(br, "⟳", self._r_nc, side="right")
        tv_f, self._nc_tv = make_tv(f, [
            ("id","ID NC",110),("date","Date",82),("type","Type",80),
            ("grav","Gravité",78),("desc","Description",240),
            ("op","Opérateur",150),("opn","Opération",120),
            ("stat","Statut",78),("cause","Cause",200)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._nc_tv.bind("<Double-1>", lambda e: self._edit_nc())

    def _r_nc(self):
        self._nc_tv.delete(*self._nc_tv.get_children())
        sf = self._nc_sf.get() if self._nc_sf.get()!="Tous" else ""
        gf = self._nc_gf.get() if self._nc_gf.get()!="Toutes" else ""
        for n in self.db.get_ncs(sf, gf):
            tag = status_tag(n["gravity"])
            self._nc_tv.insert("","end", iid=n["id"], values=(
                n["id"],n["date"],n["type"],n["gravity"],
                (n["description"] or "")[:60],n["op_name"] or "—",
                n["opn_name"] or "—",n["status"],n["cause"] or ""), tags=(tag,))

    def _nc_fields(self, existing=None):
        ops = [""] + [r["id"]+" — "+r["name"] for r in self.db.get_operators()]
        opns = [""] + [r["id"]+" — "+r["name"] for r in self.db.get_operations()]
        e = dict(existing) if existing else {}
        op_val = next((x for x in ops if x.startswith(e.get("operator_id",""))), "")
        opn_val = next((x for x in opns if x.startswith(e.get("operation_id",""))), "")
        return [
            ("id","ID NC *","entry",e.get("id",f"NC-{date.today().year}-"),None),
            ("date","Date *","entry",e.get("date",date.today().isoformat()),None),
            ("type","Type","combo",e.get("type","Interne"),["Interne","Client","Fournisseur","Process"]),
            ("gravity","Gravité","combo",e.get("gravity","Mineur"),["Mineur","Majeur","Critique"]),
            ("description","Description *","entry",e.get("description",""),None),
            ("operator_id","Opérateur","combo",op_val,ops),
            ("operation_id","Opération","combo",opn_val,opns),
            ("status","Statut","combo",e.get("status","Ouvert"),["Ouvert","En cours","Clôturé"]),
            ("cause","Cause racine","entry",e.get("cause",""),None),
            ("notes","Notes","entry",e.get("notes","") or "",None),
        ]

    def _add_nc(self):
        d = FormDialog(self, "Créer Non-Conformité", self._nc_fields(), height=540)
        if not d.result: return
        r = d.result
        ncid = r["id"]
        if not ncid or not r["description"]:
            messagebox.showerror("Erreur","ID et Description obligatoires"); return
        op = r["operator_id"].split(" — ")[0].strip()
        opn = r["operation_id"].split(" — ")[0].strip()
        try:
            self.db.run("INSERT INTO non_conformites VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (ncid,r["date"],r["type"],r["gravity"],r["description"],op,opn,r["status"],r["cause"],date.today().isoformat(),r["notes"]))
            self._r_nc()
        except Exception as ex:
            messagebox.showerror("Erreur DB", str(ex))

    def _edit_nc(self):
        sel = self._nc_tv.selection()
        if not sel: messagebox.showwarning("Sélection","Sélectionner une NC"); return
        row = self.db.conn.execute("SELECT * FROM non_conformites WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, f"Modifier {sel[0]}", self._nc_fields(row), height=540)
        if not d.result: return
        r = d.result
        op = r["operator_id"].split(" — ")[0].strip()
        opn = r["operation_id"].split(" — ")[0].strip()
        self.db.run("UPDATE non_conformites SET date=?,type=?,gravity=?,description=?,operator_id=?,operation_id=?,status=?,cause=?,notes=? WHERE id=?",
            (r["date"],r["type"],r["gravity"],r["description"],op,opn,r["status"],r["cause"],r["notes"],sel[0]))
        self._r_nc()

    def _del_nc(self):
        sel = self._nc_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer",f"Supprimer {sel[0]} ?"):
            self.db.run("DELETE FROM non_conformites WHERE id=?", (sel[0],))
            self._r_nc()

    # ══════════════════════════════════════════════════════════
    # CAPA
    # ══════════════════════════════════════════════════════════
    def _page_capa(self, f):
        self._mod_hdr(f, "CAPA", "Actions Correctives & Préventives — 8D | 5 Pourquoi | Ishikawa")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Ouvrir CAPA", self._add_capa)
        self._sec_btn(br, "✏  Modifier", self._edit_capa)
        self._sec_btn(br, "🗑  Supprimer", self._del_capa, danger=True)
        tk.Label(br,text="  Statut:",bg=C["bg"],fg=C["t2"],font=("Segoe UI",9)).pack(side="left",padx=(8,2))
        self._capa_sf = tk.StringVar(value="Tous")
        cb = ttk.Combobox(br, textvariable=self._capa_sf,
                          values=["Tous","Ouvert","En cours","Clôturé","Annulé"],
                          state="readonly", width=10)
        cb.pack(side="left",padx=2)
        cb.bind("<<ComboboxSelected>>", lambda e: self._r_capa())
        self._sec_btn(br, "⟳", self._r_capa, side="right")
        tv_f, self._capa_tv = make_tv(f, [
            ("id","ID CAPA",120),("nc","NC associée",108),("title","Titre",220),
            ("resp","Responsable",140),("meth","Méthode",80),
            ("d_open","Ouverture",88),("d_tgt","Cible",88),
            ("stat","Statut",78),("result","Résultat",120)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._capa_tv.bind("<Double-1>", lambda e: self._edit_capa())

    def _r_capa(self):
        self._capa_tv.delete(*self._capa_tv.get_children())
        sf = self._capa_sf.get() if self._capa_sf.get()!="Tous" else ""
        for c in self.db.get_capas(sf):
            tag = status_tag(c["status"])
            self._capa_tv.insert("","end", iid=c["id"], values=(
                c["id"],c["nc_id"] or "—",c["title"],
                c["resp_name"] or c["responsible"] or "—",c["method"] or "",
                c["date_open"] or "",c["date_target"] or "—",
                c["status"],c["result"] or ""), tags=(tag,))

    def _capa_fields(self, existing=None):
        ops = [""] + [r["id"]+" — "+r["name"] for r in self.db.get_operators()]
        e = dict(existing) if existing else {}
        resp_val = next((x for x in ops if x.startswith(e.get("responsible",""))), "")
        return [
            ("id","ID CAPA *","entry",e.get("id","CAPA-2024-"),None),
            ("nc_id","NC associée","entry",e.get("nc_id",""),None),
            ("title","Titre *","entry",e.get("title",""),None),
            ("responsible","Responsable","combo",resp_val,ops),
            ("method","Méthode","combo",e.get("method","8D"),["8D","5 Pourquoi","Ishikawa","A3","PDCA","Autre"]),
            ("date_open","Date ouverture","entry",e.get("date_open",date.today().isoformat()),None),
            ("date_target","Date cible","entry",e.get("date_target",""),None),
            ("date_close","Date clôture","entry",e.get("date_close",""),None),
            ("status","Statut","combo",e.get("status","Ouvert"),["Ouvert","En cours","Clôturé","Annulé"]),
            ("description","Description","entry",e.get("description",""),None),
            ("result","Résultat","entry",e.get("result",""),None),
        ]

    def _add_capa(self):
        d = FormDialog(self, "Ouvrir CAPA", self._capa_fields(), height=580)
        if not d.result: return
        r = d.result
        if not r["id"] or not r["title"]: messagebox.showerror("Erreur","ID et Titre requis"); return
        resp = r["responsible"].split(" — ")[0].strip()
        try:
            self.db.run("INSERT INTO capa VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (r["id"],r["nc_id"],r["title"],resp,r["method"],r["date_open"],r["date_target"],r["date_close"],r["status"],r["description"],r["result"]))
            self._r_capa()
        except Exception as ex:
            messagebox.showerror("Erreur DB", str(ex))

    def _edit_capa(self):
        sel = self._capa_tv.selection()
        if not sel: messagebox.showwarning("Sélection","Sélectionner une CAPA"); return
        row = self.db.conn.execute("SELECT * FROM capa WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, f"Modifier {sel[0]}", self._capa_fields(row), height=580)
        if not d.result: return
        r = d.result
        resp = r["responsible"].split(" — ")[0].strip()
        self.db.run("UPDATE capa SET nc_id=?,title=?,responsible=?,method=?,date_open=?,date_target=?,date_close=?,status=?,description=?,result=? WHERE id=?",
            (r["nc_id"],r["title"],resp,r["method"],r["date_open"],r["date_target"],r["date_close"],r["status"],r["description"],r["result"],sel[0]))
        self._r_capa()

    def _del_capa(self):
        sel = self._capa_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer",f"Supprimer {sel[0]} ?"):
            self.db.run("DELETE FROM capa WHERE id=?", (sel[0],))
            self._r_capa()

    # ══════════════════════════════════════════════════════════
    # MATRICE ILUO
    # ══════════════════════════════════════════════════════════
    def _page_iluo(self, f):
        self._mod_hdr(f, "Matrice ILUO — Habilitations Opérateurs",
                      "Clic gauche = niveau suivant  |  Clic droit = remettre à zéro")
        # Controls
        ctrl = tk.Frame(f, bg=C["bgc"])
        ctrl.pack(fill="x", padx=16, pady=(0,8))
        tk.Label(ctrl,text="  Équipe:",bg=C["bgc"],fg=C["t2"],font=("Segoe UI",9)).pack(side="left",padx=(4,2))
        self._iluo_team = tk.StringVar(value="Toutes")
        cb = ttk.Combobox(ctrl, textvariable=self._iluo_team,
                          values=["Toutes","Équipe A","Équipe B","Équipe C"],
                          state="readonly", width=10)
        cb.pack(side="left",padx=4,pady=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._r_iluo())
        tk.Label(ctrl,text="Recherche:",bg=C["bgc"],fg=C["t2"],font=("Segoe UI",9)).pack(side="left",padx=(12,2))
        self._iluo_search = tk.StringVar()
        self._iluo_search.trace("w", lambda *a: self._r_iluo())
        ttk.Entry(ctrl, textvariable=self._iluo_search, width=18).pack(side="left",padx=4)
        # Legend
        for lvl in range(5):
            bg,fg,lbl = ILUO_COLORS[lvl]
            fr = tk.Frame(ctrl, bg=bg, width=22, height=20)
            fr.pack(side="right",padx=2,pady=4); fr.pack_propagate(False)
            tk.Label(fr,text=lbl,bg=bg,fg=fg,font=("Courier New",9,"bold")).pack(expand=True)
            desc = ILUO_LABELS[lvl].split()[1] if lvl > 0 else "Non hab."
            tk.Label(ctrl,text=desc,bg=C["bgc"],fg=C["t3"],font=("Courier New",8)).pack(side="right",padx=(0,2))
        # Stats
        self._iluo_stats_v = tk.StringVar()
        tk.Label(f, textvariable=self._iluo_stats_v, bg=C["bg"], fg=C["t2"],
                 font=("Courier New",9)).pack(anchor="w", padx=16)
        # Scrollable matrix area
        self._iluo_outer = tk.Frame(f, bg=C["bgc"])
        self._iluo_outer.pack(fill="both", expand=True, padx=16, pady=(4,4))
        canvas = tk.Canvas(self._iluo_outer, bg=C["bgc"], highlightthickness=0)
        vsb = ttk.Scrollbar(self._iluo_outer, orient="vertical", command=canvas.yview)
        hsb = ttk.Scrollbar(self._iluo_outer, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=0,column=1,sticky="ns"); hsb.grid(row=1,column=0,sticky="ew")
        canvas.grid(row=0,column=0,sticky="nsew")
        self._iluo_outer.rowconfigure(0,weight=1); self._iluo_outer.columnconfigure(0,weight=1)
        self._iluo_canvas = canvas
        self._iluo_inner = tk.Frame(canvas, bg=C["bgc"])
        self._iluo_canvas_win = canvas.create_window((0,0), window=self._iluo_inner, anchor="nw")
        self._iluo_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # Validator
        val_f = tk.Frame(f, bg=C["bgh"])
        val_f.pack(fill="x", padx=16, pady=(4,12))
        tk.Label(val_f,text="  VALIDATEUR AFFECTATION :",bg=C["bgh"],fg=C["acc"],
                 font=("Courier New",9,"bold")).pack(side="left",padx=4,pady=8)
        tk.Label(val_f,text="Opérateur:",bg=C["bgh"],fg=C["t2"],font=("Segoe UI",9)).pack(side="left",padx=(8,2))
        self._val_op = tk.StringVar()
        self._val_op_cb = ttk.Combobox(val_f, textvariable=self._val_op, width=22, state="readonly")
        self._val_op_cb.pack(side="left",padx=4)
        tk.Label(val_f,text="Poste:",bg=C["bgh"],fg=C["t2"],font=("Segoe UI",9)).pack(side="left",padx=(12,2))
        self._val_opn = tk.StringVar()
        self._val_opn_cb = ttk.Combobox(val_f, textvariable=self._val_opn, width=22, state="readonly")
        self._val_opn_cb.pack(side="left",padx=4)
        tk.Button(val_f,text="  ▶ Vérifier  ",bg=C["acc"],fg="#000",
                  font=("Segoe UI",9,"bold"),relief="flat",cursor="hand2",
                  command=self._validate_aff,pady=4).pack(side="left",padx=10)
        self._val_res_v = tk.StringVar()
        self._val_res_lbl = tk.Label(val_f, textvariable=self._val_res_v,
                                     bg=C["bgh"], fg=C["t2"], font=("Segoe UI",9))
        self._val_res_lbl.pack(side="left",padx=8)

    def _r_iluo(self):
        for w in self._iluo_inner.winfo_children(): w.destroy()
        ops_all = self.db.get_operators()
        opns = self.db.get_operations()
        iluo_d = self.db.get_iluo_dict()
        tf = self._iluo_team.get(); sf = self._iluo_search.get().lower()
        ops = [o for o in ops_all
               if (tf=="Toutes" or o["team"]==tf)
               and (not sf or sf in o["name"].lower())]
        LVLS = ["—","I","L","U","O"]
        # Header row
        tk.Label(self._iluo_inner, text="Opérateur / Équipe", bg=C["bg2"], fg=C["t2"],
                 font=("Courier New",9,"bold"), width=24, anchor="w",
                 relief="flat", bd=0).grid(row=0,column=0,padx=2,pady=2,sticky="w")
        for j, opn in enumerate(opns):
            col = C["acc"] if opn["critical"] else C["t2"]
            text = opn["name"][:10]+("★" if opn["critical"] else "")
            tk.Label(self._iluo_inner, text=text, bg=C["bg2"], fg=col,
                     font=("Courier New",8), width=9, anchor="center",
                     wraplength=65).grid(row=0,column=j+1,padx=1,pady=2)
        tk.Label(self._iluo_inner,text="Score",bg=C["bg2"],fg=C["t2"],
                 font=("Courier New",9,"bold"),width=6).grid(row=0,column=len(opns)+1,padx=4)
        # Data rows
        total_q=0; total_c=0
        for i, op in enumerate(ops):
            row_bg = C["bgc"] if i%2==0 else C["bgh"]
            tk.Label(self._iluo_inner, text=f"  {op['initials']}  {op['name'][:19]}",
                     bg=row_bg, fg=C["t1"], font=("Segoe UI",9),
                     width=24, anchor="w").grid(row=i+1,column=0,padx=2,pady=1,sticky="w")
            op_q = 0
            for j, opn in enumerate(opns):
                total_c += 1
                lvl = iluo_d.get((op["id"],opn["id"]),0)
                ok = lvl >= opn["required_level"] and lvl > 0
                if ok: total_q+=1; op_q+=1
                bg_c, fg_c, lbl_c = ILUO_COLORS[lvl]
                btn = tk.Button(
                    self._iluo_inner, text=lbl_c, bg=bg_c, fg=fg_c,
                    font=("Courier New",10,"bold"), width=5, relief="flat",
                    bd=1, highlightthickness=0, cursor="hand2",
                    command=lambda oi=op["id"],oj=opn["id"],l=lvl: self._cycle_iluo(oi,oj,l))
                btn.grid(row=i+1, column=j+1, padx=1, pady=1)
                btn.bind("<Button-3>", lambda e,oi=op["id"],oj=opn["id"]: self._reset_iluo(oi,oj))
            score = round(op_q/len(opns)*100) if opns else 0
            sc = C["grn"] if score>=70 else C["acc"] if score>=50 else C["red"]
            tk.Label(self._iluo_inner,text=f"{score}%",bg=row_bg,fg=sc,
                     font=("Courier New",9,"bold"),width=6).grid(row=i+1,column=len(opns)+1,padx=4)
        pct = round(total_q/total_c*100) if total_c else 0
        self._iluo_stats_v.set(
            f"Couverture globale: {pct}%  ({total_q}/{total_c} habilitations conformes)  |  {len(ops)} opérateurs affichés")
        # Update validator
        op_vals = [o["id"]+" — "+o["name"] for o in ops_all]
        opn_vals = [o["id"]+" — "+o["name"] for o in opns]
        self._val_op_cb.configure(values=op_vals)
        self._val_opn_cb.configure(values=opn_vals)
        if op_vals: self._val_op_cb.set(op_vals[0])
        if opn_vals: self._val_opn_cb.set(opn_vals[0])

    def _cycle_iluo(self, op_id, opn_id, current):
        self.db.set_iluo(op_id, opn_id, (current+1)%5)
        self._r_iluo()

    def _reset_iluo(self, op_id, opn_id):
        self.db.set_iluo(op_id, opn_id, 0)
        self._r_iluo()

    def _validate_aff(self):
        op_raw = self._val_op.get().split(" — ")[0].strip()
        opn_raw = self._val_opn.get().split(" — ")[0].strip()
        if not op_raw or not opn_raw:
            self._val_res_v.set("⚠ Sélectionner opérateur et poste")
            self._val_res_lbl.configure(fg=C["yel"]); return
        iluo_d = self.db.get_iluo_dict()
        lvl = iluo_d.get((op_raw,opn_raw),0)
        opn = self.db.conn.execute("SELECT * FROM operations WHERE id=?", (opn_raw,)).fetchone()
        op = self.db.conn.execute("SELECT name FROM operators WHERE id=?", (op_raw,)).fetchone()
        if not opn or not op:
            self._val_res_v.set("ID introuvable"); return
        LVLS=["—","I","L","U","O"]; req=opn["required_level"]
        if lvl>=req and lvl>0:
            self._val_res_v.set(f"✓  {op['name']} est HABILITÉ sur {opn['name']}  (Niveau: {LVLS[lvl]} ≥ requis: {LVLS[req]})")
            self._val_res_lbl.configure(fg=C["grn"])
        else:
            self._val_res_v.set(f"✗  {op['name']} NON HABILITÉ sur {opn['name']}  (Niveau: {LVLS[lvl]} < requis: {LVLS[req]})")
            self._val_res_lbl.configure(fg=C["red"])

    # ══════════════════════════════════════════════════════════
    # FORMATIONS
    # ══════════════════════════════════════════════════════════
    def _page_trainings(self, f):
        self._mod_hdr(f, "Plan de Formation", "Planification | Suivi | Évaluation opérateurs")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Planifier session", self._add_tr)
        self._sec_btn(br, "✏  Modifier", self._edit_tr)
        self._sec_btn(br, "🗑  Supprimer", self._del_tr, danger=True)
        self._sec_btn(br, "⟳", self._r_trainings, side="right")
        tv_f, self._tr_tv = make_tv(f, [
            ("id","ID",50),("op","Opérateur",155),("mod","Module",180),
            ("trainer","Formateur",155),("pd","Date planifiée",108),
            ("dur","Durée",65),("stat","Statut",90),
            ("res","Résultat",95),("sc","Score",60)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._tr_tv.bind("<Double-1>", lambda e: self._edit_tr())

    def _r_trainings(self):
        self._tr_tv.delete(*self._tr_tv.get_children())
        for t in self.db.get_trainings():
            tag = status_tag(t["status"])
            self._tr_tv.insert("","end", iid=t["id"], values=(
                t["id"], t["op_name"] or t["operator_id"],
                t["module"] or "", t["trainer_name"] or t["trainer_id"] or "—",
                t["planned_date"] or "", t["duration"] or "",
                t["status"], t["result"] or "", t["score"] or ""), tags=(tag,))

    def _tr_fields(self, existing=None):
        ops = [""] + [r["id"]+" — "+r["name"] for r in self.db.get_operators()]
        opn_names = [r["name"] for r in self.db.get_operations()]
        e = dict(existing) if existing else {}
        op_val = next((x for x in ops if x.startswith(e.get("operator_id",""))), "")
        tr_val = next((x for x in ops if x.startswith(e.get("trainer_id",""))), "")
        return [
            ("operator_id","Opérateur *","combo",op_val,ops),
            ("module","Module *","combo",e.get("module",""),opn_names),
            ("trainer_id","Formateur","combo",tr_val,ops),
            ("planned_date","Date planifiée","entry",e.get("planned_date",""),None),
            ("actual_date","Date réelle","entry",e.get("actual_date",""),None),
            ("duration","Durée","entry",e.get("duration","4h"),None),
            ("status","Statut","combo",e.get("status","Planifiée"),["Planifiée","En cours","Validée","Annulée","À planifier"]),
            ("result","Résultat","combo",e.get("result",""),["","Réussi","Échoué","En attente"]),
            ("score","Score (/100)","entry",str(e.get("score","") or ""),None),
            ("notes","Notes","entry",e.get("notes","") or "",None),
        ]

    def _add_tr(self):
        d = FormDialog(self, "Planifier Session de Formation", self._tr_fields(), height=540)
        if not d.result: return
        r = d.result
        op = r["operator_id"].split(" — ")[0].strip()
        tr = r["trainer_id"].split(" — ")[0].strip()
        if not op or not r["module"]: messagebox.showerror("Erreur","Opérateur et Module requis"); return
        sc = int(r["score"]) if r["score"].isdigit() else None
        self.db.run("INSERT INTO trainings(operator_id,module,trainer_id,planned_date,actual_date,duration,status,result,score,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (op,r["module"],tr,r["planned_date"],r["actual_date"],r["duration"],r["status"],r["result"],sc,r["notes"]))
        self._r_trainings()

    def _edit_tr(self):
        sel = self._tr_tv.selection()
        if not sel: return
        row = self.db.conn.execute("SELECT * FROM trainings WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, "Modifier Session", self._tr_fields(row), height=540)
        if not d.result: return
        r = d.result
        op = r["operator_id"].split(" — ")[0].strip()
        tr = r["trainer_id"].split(" — ")[0].strip()
        sc = int(r["score"]) if r["score"].isdigit() else None
        self.db.run("UPDATE trainings SET operator_id=?,module=?,trainer_id=?,planned_date=?,actual_date=?,duration=?,status=?,result=?,score=?,notes=? WHERE id=?",
            (op,r["module"],tr,r["planned_date"],r["actual_date"],r["duration"],r["status"],r["result"],sc,r["notes"],sel[0]))
        self._r_trainings()

    def _del_tr(self):
        sel = self._tr_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer","Supprimer cette session ?"):
            self.db.run("DELETE FROM trainings WHERE id=?", (sel[0],))
            self._r_trainings()

    # ══════════════════════════════════════════════════════════
    # OPÉRATEURS
    # ══════════════════════════════════════════════════════════
    def _page_operators(self, f):
        self._mod_hdr(f, "Gestion des Opérateurs", "Fiches individuelles — CRUD complet")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Ajouter opérateur", self._add_op)
        self._sec_btn(br, "✏  Modifier", self._edit_op)
        self._sec_btn(br, "🗑  Supprimer", self._del_op, danger=True)
        self._sec_btn(br, "⟳", self._r_operators, side="right")
        tv_f, self._op_tv = make_tv(f, [
            ("id","ID",68),("name","Nom complet",180),("init","Init.",52),
            ("team","Équipe",80),("poste","Poste actuel",165),
            ("hire","Embauche",90),("active","Actif",50),("notes","Notes",200)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._op_tv.bind("<Double-1>", lambda e: self._edit_op())

    def _r_operators(self):
        self._op_tv.delete(*self._op_tv.get_children())
        for o in self.db.get_operators():
            self._op_tv.insert("","end", iid=o["id"], values=(
                o["id"],o["name"],o["initials"] or "",o["team"] or "",
                o["poste"] or "",o["hire_date"] or "",
                "Oui" if o["active"] else "Non",o["notes"] or ""))

    def _op_fields(self, existing=None):
        e = dict(existing) if existing else {}
        return [
            ("id","ID Opérateur *","entry",e.get("id","OP0??"),None),
            ("name","Nom complet *","entry",e.get("name",""),None),
            ("initials","Initiales","entry",e.get("initials",""),None),
            ("team","Équipe","combo",e.get("team","Équipe A"),["Équipe A","Équipe B","Équipe C","Équipe D"]),
            ("poste","Poste actuel","entry",e.get("poste",""),None),
            ("hire_date","Date embauche","entry",e.get("hire_date",date.today().isoformat()),None),
            ("active","Actif","combo",str(e.get("active","1")),["1","0"]),
            ("notes","Notes","entry",e.get("notes","") or "",None),
        ]

    def _add_op(self):
        d = FormDialog(self, "Nouvel Opérateur", self._op_fields(), height=460)
        if not d.result: return
        r = d.result
        if not r["id"] or not r["name"]: messagebox.showerror("Erreur","ID et Nom requis"); return
        try:
            self.db.run("INSERT INTO operators VALUES(?,?,?,?,?,?,?,?)",
                (r["id"],r["name"],r["initials"],r["team"],r["poste"],r["hire_date"],int(r["active"]),r["notes"]))
            self._r_operators()
        except Exception as ex:
            messagebox.showerror("Erreur DB", str(ex))

    def _edit_op(self):
        sel = self._op_tv.selection()
        if not sel: messagebox.showwarning("Sélection","Sélectionner un opérateur"); return
        row = self.db.conn.execute("SELECT * FROM operators WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, f"Modifier {sel[0]}", self._op_fields(row), height=460)
        if not d.result: return
        r = d.result
        self.db.run("UPDATE operators SET name=?,initials=?,team=?,poste=?,hire_date=?,active=?,notes=? WHERE id=?",
            (r["name"],r["initials"],r["team"],r["poste"],r["hire_date"],int(r["active"]),r["notes"],sel[0]))
        self._r_operators()

    def _del_op(self):
        sel = self._op_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer",f"Supprimer l'opérateur {sel[0]} ?"):
            self.db.run("DELETE FROM operators WHERE id=?", (sel[0],))
            self._r_operators()

    # ══════════════════════════════════════════════════════════
    # OPÉRATIONS
    # ══════════════════════════════════════════════════════════
    def _page_operations(self, f):
        self._mod_hdr(f, "Opérations / Postes de travail", "Niveaux ILUO requis par poste")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Ajouter opération", self._add_opn)
        self._sec_btn(br, "✏  Modifier", self._edit_opn)
        self._sec_btn(br, "🗑  Supprimer", self._del_opn, danger=True)
        self._sec_btn(br, "⟳", self._r_operations, side="right")
        tv_f, self._opn_tv = make_tv(f, [
            ("id","ID",60),("name","Nom",180),("req","Niveau requis",100),
            ("crit","Critique",70),("proj","Projet(s)",120),("desc","Description",300)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._opn_tv.bind("<Double-1>", lambda e: self._edit_opn())

    def _r_operations(self):
        self._opn_tv.delete(*self._opn_tv.get_children())
        LVLS=["—","I","L","U","O"]
        for o in self.db.get_operations():
            self._opn_tv.insert("","end", iid=o["id"], values=(
                o["id"],o["name"],LVLS[o["required_level"]],
                "Oui ★" if o["critical"] else "Non",o["project"] or "",o["description"] or ""))

    def _opn_fields(self, existing=None):
        e = dict(existing) if existing else {}
        return [
            ("id","ID Opération *","entry",e.get("id",""),None),
            ("name","Nom opération *","entry",e.get("name",""),None),
            ("required_level","Niveau ILUO requis","combo",str(e.get("required_level","2")),["1","2","3","4"]),
            ("critical","Poste critique","combo",str(e.get("critical","0")),["0","1"]),
            ("project","Projet(s)","entry",e.get("project","ALL"),None),
            ("description","Description","entry",e.get("description",""),None),
        ]

    def _add_opn(self):
        d = FormDialog(self, "Nouvelle Opération", self._opn_fields(), height=380)
        if not d.result: return
        r = d.result
        if not r["id"] or not r["name"]: messagebox.showerror("Erreur","ID et Nom requis"); return
        try:
            self.db.run("INSERT INTO operations VALUES(?,?,?,?,?,?)",
                (r["id"],r["name"],int(r["required_level"]),int(r["critical"]),r["description"],r["project"]))
            self._r_operations()
        except Exception as ex:
            messagebox.showerror("Erreur DB", str(ex))

    def _edit_opn(self):
        sel = self._opn_tv.selection()
        if not sel: messagebox.showwarning("Sélection","Sélectionner une opération"); return
        row = self.db.conn.execute("SELECT * FROM operations WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, f"Modifier {sel[0]}", self._opn_fields(row), height=380)
        if not d.result: return
        r = d.result
        self.db.run("UPDATE operations SET name=?,required_level=?,critical=?,description=?,project=? WHERE id=?",
            (r["name"],int(r["required_level"]),int(r["critical"]),r["description"],r["project"],sel[0]))
        self._r_operations()

    def _del_opn(self):
        sel = self._opn_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer",f"Supprimer {sel[0]} ?"):
            self.db.run("DELETE FROM operations WHERE id=?", (sel[0],))
            self._r_operations()

    # ══════════════════════════════════════════════════════════
    # PRODUCTION
    # ══════════════════════════════════════════════════════════
    def _page_production(self, f):
        self._mod_hdr(f, "Traçabilité Production", "Ordres de Fabrication | Vérification ILUO automatique")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Créer OF", self._add_prod)
        self._sec_btn(br, "✏  Modifier", self._edit_prod)
        self._sec_btn(br, "🗑  Supprimer", self._del_prod, danger=True)
        self._sec_btn(br, "⟳", self._r_production, side="right")
        tv_f, self._prod_tv = make_tv(f, [
            ("id","ID",50),("of","N° OF",100),("ref","Référence",130),
            ("qty","Qté",58),("op","Opérateur",155),("opn","Opération",120),
            ("mach","Machine",108),("stat","Statut",88),("conf","Conformité ILUO",130)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))

    def _r_production(self):
        self._prod_tv.delete(*self._prod_tv.get_children())
        iluo_d = self.db.get_iluo_dict()
        for p in self.db.get_production():
            conf = p["conformity"] or "—"
            tag = ""
            if p["operator_id"] and p["operation_id"]:
                lvl = iluo_d.get((p["operator_id"],p["operation_id"]),0)
                opn = self.db.conn.execute("SELECT required_level FROM operations WHERE id=?", (p["operation_id"],)).fetchone()
                if opn:
                    if lvl >= opn["required_level"] and lvl > 0:
                        conf = "✓ Habilité"; tag = "vert"
                    else:
                        conf = "✗ Non habilité ⚠"; tag = "rouge"
            self._prod_tv.insert("","end", iid=p["id"], values=(
                p["id"],p["of_number"] or "",p["reference"] or "",p["quantity"] or 0,
                p["op_name"] or p["operator_id"] or "—",
                p["opn_name"] or p["operation_id"] or "—",
                p["machine"] or "—",p["status"],conf), tags=(tag,))

    def _prod_fields(self, existing=None):
        ops = [""] + [r["id"]+" — "+r["name"] for r in self.db.get_operators()]
        opns = [""] + [r["id"]+" — "+r["name"] for r in self.db.get_operations()]
        e = dict(existing) if existing else {}
        op_val = next((x for x in ops if x.startswith(e.get("operator_id",""))), "")
        opn_val = next((x for x in opns if x.startswith(e.get("operation_id",""))), "")
        return [
            ("of_number","N° OF *","entry",e.get("of_number","OF-2024-"),None),
            ("reference","Référence","entry",e.get("reference",""),None),
            ("quantity","Quantité","entry",str(e.get("quantity","100")),None),
            ("operator_id","Opérateur","combo",op_val,ops),
            ("operation_id","Opération","combo",opn_val,opns),
            ("machine","Machine","entry",e.get("machine",""),None),
            ("status","Statut","combo",e.get("status","En attente"),["En attente","En cours","Terminé","Arrêté"]),
            ("date","Date","entry",e.get("date",date.today().isoformat()),None),
        ]

    def _add_prod(self):
        d = FormDialog(self, "Créer Ordre de Fabrication", self._prod_fields(), height=460)
        if not d.result: return
        r = d.result
        if not r["of_number"]: messagebox.showerror("Erreur","N° OF requis"); return
        op = r["operator_id"].split(" — ")[0].strip()
        opn = r["operation_id"].split(" — ")[0].strip()
        self.db.run("INSERT INTO production_of(of_number,reference,quantity,operator_id,operation_id,machine,status,conformity,alert,date) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (r["of_number"],r["reference"],int(r["quantity"] or 0),op,opn,r["machine"],r["status"],"En cours","",r["date"]))
        self._r_production()

    def _edit_prod(self):
        sel = self._prod_tv.selection()
        if not sel: return
        row = self.db.conn.execute("SELECT * FROM production_of WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, f"Modifier OF {sel[0]}", self._prod_fields(row), height=460)
        if not d.result: return
        r = d.result
        op = r["operator_id"].split(" — ")[0].strip()
        opn = r["operation_id"].split(" — ")[0].strip()
        self.db.run("UPDATE production_of SET of_number=?,reference=?,quantity=?,operator_id=?,operation_id=?,machine=?,status=?,date=? WHERE id=?",
            (r["of_number"],r["reference"],int(r["quantity"] or 0),op,opn,r["machine"],r["status"],r["date"],sel[0]))
        self._r_production()

    def _del_prod(self):
        sel = self._prod_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer","Supprimer cet OF ?"):
            self.db.run("DELETE FROM production_of WHERE id=?", (sel[0],))
            self._r_production()

    # ══════════════════════════════════════════════════════════
    # FOURNISSEURS
    # ══════════════════════════════════════════════════════════
    def _page_fournisseurs(self, f):
        self._mod_hdr(f, "Gestion Fournisseurs", "Scorecard | NC fournisseur | Qualification")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Ajouter", self._add_four)
        self._sec_btn(br, "✏  Modifier", self._edit_four)
        self._sec_btn(br, "🗑  Supprimer", self._del_four, danger=True)
        self._sec_btn(br, "⟳", self._r_fournisseurs, side="right")
        tv_f, self._four_tv = make_tv(f, [
            ("id","ID",50),("name","Fournisseur",175),("country","Pays",55),
            ("cat","Catégorie",135),("score","Score",65),("ppm","PPM",65),
            ("nc","NC",55),("stat","Statut",110),("notes","Notes",200)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._four_tv.bind("<Double-1>", lambda e: self._edit_four())

    def _r_fournisseurs(self):
        self._four_tv.delete(*self._four_tv.get_children())
        for f in self.db.get_fournisseurs():
            score = f["score"]
            tag = "vert" if score>=85 else "jaune" if score>=70 else "rouge"
            self._four_tv.insert("","end", iid=f["id"], values=(
                f["id"],f["name"],f["country"] or "",f["category"] or "",
                f"{score}/100",f["ppm"],f["nc_count"],f["status"],f["notes"] or ""), tags=(tag,))

    def _four_fields(self, existing=None):
        e = dict(existing) if existing else {}
        return [
            ("name","Nom fournisseur *","entry",e.get("name",""),None),
            ("country","Pays (code)","entry",e.get("country","MA"),None),
            ("category","Catégorie","combo",e.get("category","Connecteurs"),["Connecteurs","Fils & Câbles","Terminaux","Systèmes câblage","Fournitures","Autre"]),
            ("score","Score qualité (0-100)","entry",str(e.get("score","80")),None),
            ("ppm","PPM","entry",str(e.get("ppm","200")),None),
            ("nc_count","Nb NC ouvertes","entry",str(e.get("nc_count","0")),None),
            ("status","Statut","combo",e.get("status","Qualifié"),["Qualifié","Certifié","Sous surveillance","Disqualifié","Nouveau"]),
            ("notes","Notes","entry",e.get("notes","") or "",None),
        ]

    def _add_four(self):
        d = FormDialog(self, "Nouveau Fournisseur", self._four_fields(), height=460)
        if not d.result: return
        r = d.result
        if not r["name"]: messagebox.showerror("Erreur","Nom requis"); return
        self.db.run("INSERT INTO fournisseurs(name,country,category,score,ppm,nc_count,status,notes) VALUES(?,?,?,?,?,?,?,?)",
            (r["name"],r["country"],r["category"],int(r["score"] or 80),int(r["ppm"] or 0),int(r["nc_count"] or 0),r["status"],r["notes"]))
        self._r_fournisseurs()

    def _edit_four(self):
        sel = self._four_tv.selection()
        if not sel: return
        row = self.db.conn.execute("SELECT * FROM fournisseurs WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, f"Modifier Fournisseur", self._four_fields(row), height=460)
        if not d.result: return
        r = d.result
        self.db.run("UPDATE fournisseurs SET name=?,country=?,category=?,score=?,ppm=?,nc_count=?,status=?,notes=? WHERE id=?",
            (r["name"],r["country"],r["category"],int(r["score"] or 80),int(r["ppm"] or 0),int(r["nc_count"] or 0),r["status"],r["notes"],sel[0]))
        self._r_fournisseurs()

    def _del_four(self):
        sel = self._four_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer","Supprimer ce fournisseur ?"):
            self.db.run("DELETE FROM fournisseurs WHERE id=?", (sel[0],))
            self._r_fournisseurs()

    # ══════════════════════════════════════════════════════════
    # AUDITS
    # ══════════════════════════════════════════════════════════
    def _page_audits(self, f):
        self._mod_hdr(f, "Gestion des Audits", "Internes | Clients | IATF 16949")
        br = self._btn_row(f)
        self._acc_btn(br, "+ Planifier audit", self._add_aud)
        self._sec_btn(br, "✏  Modifier", self._edit_aud)
        self._sec_btn(br, "🗑  Supprimer", self._del_aud, danger=True)
        self._sec_btn(br, "⟳", self._r_audits, side="right")
        tv_f, self._aud_tv = make_tv(f, [
            ("id","ID",50),("title","Titre",250),("type","Type",85),
            ("auditor","Auditeur",145),("planned","Date planifiée",108),
            ("actual","Date réelle",98),("stat","Statut",88),
            ("scope","Périmètre",155),("nf","Nb écarts",80)], height=22)
        tv_f.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._aud_tv.bind("<Double-1>", lambda e: self._edit_aud())

    def _r_audits(self):
        self._aud_tv.delete(*self._aud_tv.get_children())
        for a in self.db.get_audits():
            tag = status_tag(a["status"])
            self._aud_tv.insert("","end", iid=a["id"], values=(
                a["id"],a["title"],a["type"],a["auditor"] or "",
                a["planned_date"] or "",a["actual_date"] or "",
                a["status"],a["scope"] or "",a["nb_findings"]), tags=(tag,))

    def _aud_fields(self, existing=None):
        e = dict(existing) if existing else {}
        return [
            ("title","Titre *","entry",e.get("title",""),None),
            ("type","Type","combo",e.get("type","Interne"),["Interne","Client","IATF","ISO","Fournisseur","Processus"]),
            ("auditor","Auditeur","entry",e.get("auditor",""),None),
            ("planned_date","Date planifiée","entry",e.get("planned_date",""),None),
            ("actual_date","Date réelle","entry",e.get("actual_date",""),None),
            ("scope","Périmètre","entry",e.get("scope",""),None),
            ("nb_findings","Nb écarts","entry",str(e.get("nb_findings","0")),None),
            ("status","Statut","combo",e.get("status","Planifié"),["Planifié","Confirmé","En cours","Terminé","Annulé"]),
            ("notes","Notes","entry",e.get("notes","") or "",None),
        ]

    def _add_aud(self):
        d = FormDialog(self, "Planifier Audit", self._aud_fields(), height=500)
        if not d.result: return
        r = d.result
        if not r["title"]: messagebox.showerror("Erreur","Titre requis"); return
        self.db.run("INSERT INTO audits(title,type,auditor,planned_date,actual_date,status,scope,nb_findings,notes) VALUES(?,?,?,?,?,?,?,?,?)",
            (r["title"],r["type"],r["auditor"],r["planned_date"],r["actual_date"],r["status"],r["scope"],int(r["nb_findings"] or 0),r["notes"]))
        self._r_audits()

    def _edit_aud(self):
        sel = self._aud_tv.selection()
        if not sel: return
        row = self.db.conn.execute("SELECT * FROM audits WHERE id=?", (sel[0],)).fetchone()
        d = FormDialog(self, f"Modifier Audit", self._aud_fields(row), height=500)
        if not d.result: return
        r = d.result
        self.db.run("UPDATE audits SET title=?,type=?,auditor=?,planned_date=?,actual_date=?,status=?,scope=?,nb_findings=?,notes=? WHERE id=?",
            (r["title"],r["type"],r["auditor"],r["planned_date"],r["actual_date"],r["status"],r["scope"],int(r["nb_findings"] or 0),r["notes"],sel[0]))
        self._r_audits()

    def _del_aud(self):
        sel = self._aud_tv.selection()
        if not sel: return
        if messagebox.askyesno("Supprimer","Supprimer cet audit ?"):
            self.db.run("DELETE FROM audits WHERE id=?", (sel[0],))
            self._r_audits()

    # ══════════════════════════════════════════════════════════
    # PARAMÈTRES
    # ══════════════════════════════════════════════════════════
    def _page_settings(self, f):
        self._mod_hdr(f, "Paramètres Système", "Configuration entreprise")
        frm = tk.Frame(f, bg=C["bgc"])
        frm.pack(fill="x", padx=16, pady=16)
        frm.columnconfigure(1, weight=1)
        self._s_vars = {}
        fields = [("company_name","Nom entreprise"),("company_city","Ville / Pays"),("standard","Norme qualité")]
        for i,(k,lbl) in enumerate(fields):
            tk.Label(frm, text=lbl, bg=C["bgc"], fg=C["t2"],
                     font=("Segoe UI",9)).grid(row=i,column=0,padx=20,pady=10,sticky="w")
            v = tk.StringVar(value=self.db.get_setting(k,""))
            ttk.Entry(frm, textvariable=v, width=50).grid(row=i,column=1,padx=20,pady=10,sticky="ew")
            self._s_vars[k] = v
        tk.Button(frm, text="  ✓  Enregistrer  ", bg=C["acc"], fg="#000",
                  font=("Segoe UI",10,"bold"), relief="flat", bd=0,
                  padx=14, pady=6, cursor="hand2",
                  command=self._save_settings).grid(row=len(fields),column=0,columnspan=2,padx=20,pady=16,sticky="w")
        tk.Label(f, text=f"Base de données: {DB_PATH}", bg=C["bg"], fg=C["t3"],
                 font=("Courier New",8)).pack(anchor="w", padx=16, pady=8)
        tk.Button(f, text="  📤  Exporter toutes les données (CSV)  ", bg=C["bgc"],
                  fg=C["t1"], font=("Segoe UI",9), relief="flat", bd=1,
                  padx=10, pady=5, cursor="hand2",
                  command=self._export_csv).pack(anchor="w", padx=16)

    def _save_settings(self):
        for k,v in self._s_vars.items():
            self.db.set_setting(k, v.get())
        self.title(f"GQAO Pro v2.0 — {self.db.get_setting('company_name','PROMACAB S.A.')}")
        self.company_lbl.configure(text=self.db.get_setting("company_name",""))
        messagebox.showinfo("Paramètres","Enregistré avec succès.")

    # ══════════════════════════════════════════════════════════
    # EXPORT CSV
    # ══════════════════════════════════════════════════════════
    def _export_csv(self):
        path = filedialog.askdirectory(title="Choisir le dossier d'export")
        if not path: return
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        count = 0
        exports = {
            "NC": self.db.get_ncs,
            "CAPA": self.db.get_capas,
            "Formations": self.db.get_trainings,
            "Fournisseurs": self.db.get_fournisseurs,
            "Audits": self.db.get_audits,
            "Operateurs": self.db.get_operators,
            "Operations": self.db.get_operations,
        }
        for name, fn in exports.items():
            rows = fn()
            if not rows: continue
            fp = os.path.join(path, f"GQAO_{name}_{ts}.csv")
            with open(fp, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(rows[0].keys())
                for r in rows: w.writerow(list(r))
            count += 1
        # ILUO matrix export
        ops = self.db.get_operators(); opns = self.db.get_operations()
        iluo_d = self.db.get_iluo_dict()
        fp = os.path.join(path, f"GQAO_Matrice_ILUO_{ts}.csv")
        LVLS=["—","I","L","U","O"]
        with open(fp, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["ID","Operateur","Equipe"] + [o["name"] for o in opns] + ["Score%"])
            for op in ops:
                q = 0
                row = [op["id"],op["name"],op["team"]]
                for opn in opns:
                    lvl = iluo_d.get((op["id"],opn["id"]),0)
                    row.append(LVLS[lvl])
                    if lvl >= opn["required_level"] and lvl > 0: q+=1
                row.append(f"{round(q/len(opns)*100)}%" if opns else "0%")
                w.writerow(row)
        count += 1
        messagebox.showinfo("Export terminé", f"{count} fichier(s) CSV exporté(s) dans:\n{path}")

# ─── MAIN ───────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        app = GQAOApp()
        app.mainloop()
    except Exception as e:
        import traceback
        messagebox.showerror("Erreur critique", f"{e}\n\n{traceback.format_exc()}")

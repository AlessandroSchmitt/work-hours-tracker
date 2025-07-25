import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime, timedelta, date
import json
import os
import calendar
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import holidays

# --- COSTANTI ---
ORARIO_STANDARD = timedelta(hours=7, minutes=42)
FILE_DATI = "registro_orari.json"
FESTIVITA_ITA = holidays.Italy(years=date.today().year)

# --- CONFIG CUSTOMTKINTER ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- FUNZIONI UTILI ---
def str_timedelta(td):
    total_minutes = int(td.total_seconds() // 60)
    segno = "-" if total_minutes < 0 else ""
    total_minutes = abs(total_minutes)
    ore = total_minutes // 60
    minuti = total_minutes % 60
    return f"{segno}{ore}h {minuti}m"

def salva_dati(data):
    if os.path.exists(FILE_DATI):
        with open(FILE_DATI, "r") as f:
            dati = json.load(f)
    else:
        dati = {}
    dati.update(data)
    with open(FILE_DATI, "w") as f:
        json.dump(dati, f, indent=2)

def carica_dati():
    if os.path.exists(FILE_DATI):
        with open(FILE_DATI, "r") as f:
            return json.load(f)
    return {}

def is_feriale(giorno):
    # Esclude sabati, domeniche e festività italiane
    return giorno.weekday() < 5 and giorno not in FESTIVITA_ITA

# --- FUNZIONI PRINCIPALI ---

def calcola_per_data():
    ingresso = entry_ingresso.get().strip()
    uscita = entry_uscita.get().strip()
    giorno_selezionato = calendar_picker.get_date()

    try:
        t_ingresso = datetime.strptime(ingresso, "%H:%M")
        t_uscita = datetime.strptime(uscita, "%H:%M")

        if t_uscita <= t_ingresso:
            raise ValueError("L'orario di uscita non può essere prima dell'ingresso.")

        if not is_feriale(giorno_selezionato):
            messagebox.showinfo("Info", "Il giorno selezionato è un sabato, domenica o festa. I dati non verranno conteggiati.")
        
        lavorato = t_uscita - t_ingresso
        residuo = lavorato - ORARIO_STANDARD
        giorno_settimana = calendar.day_name[giorno_selezionato.weekday()]
        str_data = giorno_selezionato.isoformat()

        dati_giorno = {
            str_data: {
                "giorno": giorno_settimana,
                "ingresso": ingresso,
                "uscita": uscita,
                "lavorato": str_timedelta(lavorato),
                "residuo": str_timedelta(residuo)
            }
        }

        salva_dati(dati_giorno)
        label_risultato.configure(
            text=f"Hai lavorato: {str_timedelta(lavorato)}\nResiduo: {str_timedelta(residuo)}",
            text_color="green"
        )

    except ValueError as ve:
        messagebox.showerror("Errore", str(ve))
    except Exception:
        messagebox.showerror("Errore", "Formato orario non valido. Usa HH:MM.")

def mostra_riepilogo():
    dati = carica_dati()
    oggi = date.today()

    totale_settimana = timedelta()
    totale_mese = timedelta()
    totale_anno = timedelta()

    for giorno_str, info in dati.items():
        giorno = datetime.strptime(giorno_str, "%Y-%m-%d").date()
        if not is_feriale(giorno):
            continue
        residuo = info.get("residuo", "0h 0m")
        ore, minuti = map(int, residuo.replace("-", "").replace("h", "").replace("m", "").split())
        td = timedelta(hours=ore, minutes=minuti)
        if "-" in residuo:
            td = -td

        if giorno.isocalendar()[1] == oggi.isocalendar()[1] and giorno.year == oggi.year:
            totale_settimana += td
        if giorno.month == oggi.month and giorno.year == oggi.year:
            totale_mese += td
        if giorno.year == oggi.year:
            totale_anno += td

    messagebox.showinfo("Riepilogo", f"Settimana: {str_timedelta(totale_settimana)}\n"
                                     f"Mese: {str_timedelta(totale_mese)}\n"
                                     f"Anno: {str_timedelta(totale_anno)}")

# --- FUNZIONE PER ESPORTARE CSV ---
def esporta_csv():
    dati = carica_dati()
    if not dati:
        messagebox.showinfo("Esporta CSV", "Nessun dato da esportare.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Data", "Giorno", "Ingresso", "Uscita", "Ore Lavorate", "Residuo"])
        for data_str, info in sorted(dati.items()):
            writer.writerow([data_str,
                             info.get("giorno", ""),
                             info.get("ingresso", ""),
                             info.get("uscita", ""),
                             info.get("lavorato", ""),
                             info.get("residuo", "")])
    messagebox.showinfo("Esporta CSV", f"Dati esportati correttamente in {file_path}")

# --- FUNZIONI PER LA FINESTRA STORICO (modifica e cancella) ---
def apri_storico():
    finestra = ctk.CTkToplevel(app)
    finestra.title("Storico Orari")
    finestra.geometry("700x400")
    
    dati = carica_dati()
    righe = sorted(dati.items())

    def aggiorna_storico():
        for widget in frame_lista.winfo_children():
            widget.destroy()
        for i, (data_str, info) in enumerate(righe):
            ingresso = info["ingresso"]
            uscita = info["uscita"]
            lavorato = info["lavorato"]
            residuo = info["residuo"]

            ctk.CTkLabel(frame_lista, text=data_str, width=100).grid(row=i, column=0, padx=5)
            entry_in = ctk.CTkEntry(frame_lista, width=60)
            entry_in.insert(0, ingresso)
            entry_in.grid(row=i, column=1)

            entry_out = ctk.CTkEntry(frame_lista, width=60)
            entry_out.insert(0, uscita)
            entry_out.grid(row=i, column=2)

            ctk.CTkLabel(frame_lista, text=lavorato, width=80).grid(row=i, column=3)
            ctk.CTkLabel(frame_lista, text=residuo, width=80).grid(row=i, column=4)

            def salva_modifica(data_key=data_str, en_in=entry_in, en_out=entry_out):
                try:
                    in_t = datetime.strptime(en_in.get(), "%H:%M")
                    out_t = datetime.strptime(en_out.get(), "%H:%M")
                    if out_t <= in_t:
                        raise ValueError
                    lav = out_t - in_t
                    res = lav - ORARIO_STANDARD
                    dati[data_key]["ingresso"] = en_in.get()
                    dati[data_key]["uscita"] = en_out.get()
                    dati[data_key]["lavorato"] = str_timedelta(lav)
                    dati[data_key]["residuo"] = str_timedelta(res)
                    with open(FILE_DATI, "w") as f:
                        json.dump(dati, f, indent=2)
                    aggiorna_storico()
                except:
                    messagebox.showerror("Errore", "Formato orario non valido.")

            def elimina(data_key=data_str):
                if messagebox.askyesno("Conferma", f"Eliminare la data {data_key}?"):
                    dati.pop(data_key)
                    with open(FILE_DATI, "w") as f:
                        json.dump(dati, f, indent=2)
                    righe[:] = sorted(dati.items())
                    aggiorna_storico()

            ctk.CTkButton(frame_lista, text="✏️", width=30, command=salva_modifica).grid(row=i, column=5)
            ctk.CTkButton(frame_lista, text="❌", width=30, fg_color="red", command=elimina).grid(row=i, column=6)

    frame_lista = ctk.CTkScrollableFrame(finestra, width=680, height=350)
    frame_lista.pack(pady=10)
    aggiorna_storico()

# --- FUNZIONE PER MOSTRARE GRAFICI ---
def apri_grafici():
    dati = carica_dati()
    if not dati:
        messagebox.showinfo("Grafici", "Nessun dato disponibile per i grafici.")
        return

    dates = []
    ore_lavorate = []
    residui_minuti = []

    for data_str, info in sorted(dati.items()):
        giorno = datetime.strptime(data_str, "%Y-%m-%d").date()
        if not is_feriale(giorno):
            continue
        dates.append(giorno)
        lavorato = info.get("lavorato", "0h 0m")
        residuo = info.get("residuo", "0h 0m")

        # Converti lavorato in minuti
        ore_lav, min_lav = map(int, lavorato.replace("h", "").replace("m", "").split())
        minuti_lav = ore_lav * 60 + min_lav
        ore_lavorate.append(minuti_lav)

        # Converti residuo in minuti con segno
        segno = -1 if residuo.startswith("-") else 1
        ore_res, min_res = map(int, residuo.replace("-", "").replace("h", "").replace("m", "").split())
        residui_minuti.append(segno * (ore_res * 60 + min_res))

    finestra = ctk.CTkToplevel(app)
    finestra.title("Grafici Ore e Residui")
    finestra.geometry("800x500")

    fig, ax = plt.subplots(2, 1, figsize=(8, 6), constrained_layout=True)

    # Grafico ore lavorate
    ax[0].plot(dates, [m/60 for m in ore_lavorate], marker='o', color='blue')
    ax[0].set_title("Ore Lavorate")
    ax[0].set_ylabel("Ore")
    ax[0].grid(True)

    # Grafico residui
    ax[1].bar(dates, [m/60 for m in residui_minuti], color=['green' if x >= 0 else 'red' for x in residui_minuti])
    ax[1].set_title("Residui Giornalieri")
    ax[1].set_ylabel("Ore")
    ax[1].grid(True)

    canvas = FigureCanvasTkAgg(fig, master=finestra)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# --- INTERFACCIA GRAFICA PRINCIPALE ---

app = ctk.CTk()
app.title("Calcolo Ore Lavorate con Residui")
app.geometry("400x400")

ctk.CTkLabel(app, text="Seleziona giorno:").pack(pady=(10, 0))
calendar_picker = DateEntry(app, width=12, background='darkblue',
                foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
calendar_picker.pack(pady=5)

ctk.CTkLabel(app, text="Orario Ingresso (HH:MM):").pack()
entry_ingresso = ctk.CTkEntry(app)
entry_ingresso.pack(pady=5)

ctk.CTkLabel(app, text="Orario Uscita (HH:MM):").pack()
entry_uscita = ctk.CTkEntry(app)
entry_uscita.pack(pady=5)

btn_calcola = ctk.CTkButton(app, text="Calcola", command=calcola_per_data)
btn_calcola.pack(pady=10)

label_risultato = ctk.CTkLabel(app, text="", font=ctk.CTkFont(size=14))
label_risultato.pack(pady=5)

btn_riepilogo = ctk.CTkButton(app, text="Mostra Riepilogo", command=mostra_riepilogo)
btn_riepilogo.pack(pady=5)

btn_storico = ctk.CTkButton(app, text="Apri Storico", command=apri_storico)
btn_storico.pack(pady=5)

btn_export = ctk.CTkButton(app, text="Esporta CSV", command=esporta_csv)
btn_export.pack(pady=5)

btn_grafici = ctk.CTkButton(app, text="Mostra Grafici", command=apri_grafici)
btn_grafici.pack(pady=5)

app.mainloop()

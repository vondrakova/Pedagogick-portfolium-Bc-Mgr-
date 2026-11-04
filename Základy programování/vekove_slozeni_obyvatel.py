import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random  # pro náhodné generování barev
import chardet  # pro kontrolu kódování CSV
import os  # práce s cestami
from PIL import Image, ImageTk  # práce s obrázky
from matplotlib.ticker import MaxNLocator # pro přehlednost osy y

bars = []
data = None
original_title = ""  # proměnná pro původní název grafu

# pro zjištění kódování - pro kontrolu
def zjistit_kodovani(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        return result['encoding']

# nahrání souboru CSV
def nahrat_csv():
    global data
    file_path = filedialog.askopenfilename(
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not file_path:
        status_label.config(text="Nahrávání bylo zrušeno." , fg="red")
        return
    
    try:
        encoding = zjistit_kodovani(file_path)
        data = pd.read_csv(file_path, delimiter=";", encoding=encoding)
        print(f"Zjištěné kódování: {encoding}")  # pouze pro kontrolu - výpis se objeví v konzole

        status_label.config(text="Soubor byl úspěšně nahrán!", fg="green")
  
    except Exception as e:
        status_label.config(text=f"Chyba při načítání souboru: {e}", fg="red")

# vykreslení grafu
def vykreslit_graf():
    global data, vybrana_kategorie, bars, original_title
    if data is None:
        messagebox.showerror("Chyba!", "Nejprve nahrajte CSV soubor!")
        return

    try:
        # definování všech věkových skupin
        kategorie = ["muži 0-14let", "muži 15-64let", "muži 65 a více let", "ženy 0-14let", "ženy 15-64let", "ženy 65 a více let"]

        if vybrana_kategorie.get() == "Výběr kategorie" or vybrana_kategorie.get() not in kategorie:
            messagebox.showerror("Chyba", "Neplatná kategorie! Vyberte jednu z možností.")
            return

        # výběr dat pro vybranou kategorii
        data_pro_kategorii = data.loc[:, ["kraj", vybrana_kategorie.get()]]
        
        print(f"Data pro kategorii {vybrana_kategorie.get()}:")
        print(data_pro_kategorii.to_string())  # zobrazí konkrétní hodnoty pro vybranou kategorii - pro kontrolu, v konzoli

        # vykreslení grafu
        plt.figure(figsize=(12, 6)) # velikost grafu
        x = np.arange(len(data_pro_kategorii))  

        # generování náhodných barev pro každý sloupec
        colors = [plt.cm.tab20c(i / len(data_pro_kategorii)) for i in range(len(data_pro_kategorii))]

        bars = plt.bar(x, data_pro_kategorii[vybrana_kategorie.get()], color=colors)  # každý sloupec má jinou barvu

        # přidání čísel nad každý sloupec - pro přehlednost
        for i, value in enumerate(data_pro_kategorii[vybrana_kategorie.get()]):  
            plt.text(i, value + 0.01 * value, str(value), ha='center', va='bottom', fontsize=8)

        plt.xticks(x, data_pro_kategorii["kraj"], rotation=45, ha="right")
        plt.ylabel("počet obyvatel") # popis osy y
        plt.xlabel("kraje") # popis osy x
        original_title = f"Věková skupina: {vybrana_kategorie.get()}" # originální název grafu
        plt.title(original_title)

        # zobrazení celkového počtu obyvatel po kliknutí na sloupec
        def on_click(event):
            clicked = False  
            for i, bar in enumerate(bars):
                if bar.contains(event)[0]:
                    kraj = data_pro_kategorii["kraj"].iloc[i]
                    celkovy_pocet = data[data["kraj"] == kraj][kategorie].sum(axis=1).iloc[0]
                    plt.gca().set_title(f"Počet obyvatel celkem: {celkovy_pocet}", fontsize=12)
                    plt.draw()  
                    clicked = True  
                    break  

            if not clicked:
                plt.gca().set_title(original_title, fontsize=12)
                plt.draw()

        plt.gcf().canvas.mpl_connect('button_press_event', on_click)
        plt.tight_layout()
        plt.show()

        # po vykreslení grafu se automaticky uloží CSV soubor pro danou kategorii
        ulozit_csv_automaticky()

        # celkový počet obyvatel se zobrazí v názvu grafu
        nadpis_label.config(text=f"Věkové složení obyvatel: {vybrana_kategorie.get()}")

    except Exception as e:
        messagebox.showerror("Chyba", f"Nepodařilo se vykreslit graf: {e}")


def get_save_path():
    # aktuální adresář 
    save_folder = os.getcwd()
    save_file = os.path.join(save_folder, f'vystupni_data_{vybrana_kategorie.get()}.csv') 
    return save_file

def ulozit_csv_automaticky():
    global data
    if data is not None and vybrana_kategorie.get() != "Výběr kategorie":
        save_path = get_save_path()  # cesta pro uložení souboru
        try:

            # uložení pouze vybraných dat pro kategorii
            data_pro_kategorii = data.loc[:, ["kraj", vybrana_kategorie.get()]]
            data_pro_kategorii.to_csv(save_path, index=False, sep=';')
            messagebox.showinfo("Úspěch", f"Soubor pro kategorii '{vybrana_kategorie.get()}' byl automaticky uložen do: {save_path}")
       
        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba při ukládání souboru: {e}")
    else:
        messagebox.showerror("Chyba", "Nejprve nahrajte CSV soubor a vyberte kategorii!")


root = tk.Tk()
root.title("Vykreslení grafu")

try:
    image = Image.open("mapa.jpg")  
    image = image.resize((400, 250), Image.Resampling.LANCZOS)  
    photo = ImageTk.PhotoImage(image)

except Exception as e:
    print(f"Chyba při načítání obrázku: {e}")
    photo = None

# nadpis
nadpis_label = tk.Label(root, text="Věkové složení obyvatel", font=("Arial", 14), fg="blue")
nadpis_label.pack(pady=10)  # Zobrazí nadpis pod obrázkem

if photo:
    obrazek_label = tk.Label(root, image=photo)
    obrazek_label.pack(pady=10)  

# tlačítko pro nahrání CSV
btn_nahrat = tk.Button(root, text="Nahrát CSV", command=nahrat_csv, width=20, height=2, bg="lightblue")
btn_nahrat.pack(pady=10)

status_label = tk.Label(root, text="", font=("Arial", 10), fg="black")
status_label.pack(pady=10)

# seznam kategorií pro výběr
kategorie = ["Výběr kategorie", "muži 0-14let", "muži 15-64let", "muži 65 a více let", "ženy 0-14let", "ženy 15-64let", "ženy 65 a více let"]

# výběr kategorie 
vybrana_kategorie = tk.StringVar(root)
vybrana_kategorie.set(kategorie[0])  # nastavení výchozí hodnoty na "Výběr kategorií"

option_menu = tk.OptionMenu(root, vybrana_kategorie, *kategorie)
option_menu.config(width=18, height=2, bg="lightblue")
option_menu.pack(pady=10)

# tlačítko pro vykreslení grafu
btn_graf = tk.Button(root, text="Vykreslit graf", command=vykreslit_graf, width=20, height=2, bg="blue")
btn_graf.pack(pady=10)

# spuštění
root.mainloop()

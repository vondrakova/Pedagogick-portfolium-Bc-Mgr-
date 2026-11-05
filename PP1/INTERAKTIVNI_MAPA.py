import geopandas as gpd
import tkinter as tk
from tkinter import filedialog, messagebox
import folium
from folium.features import GeoJsonTooltip
from folium.plugins import Search
import json
import webbrowser
import os

# skryti hlavniho okna tkinter
root = tk.Tk()
root.withdraw()

messagebox.showinfo(
    "Informace",
    "Vytvoření interaktivní mapy s počty obyvatel pro okresy i kraje.\n\n"
    "Pokračujte stisknutím OK."
)

messagebox.showinfo("Krok 1", "Vložte soubor s daty pro kraje ČR.")

# vyber souboru s kraji
kraje_file = filedialog.askopenfilename(
    title="Vyberte GeoJSON soubor s kraji",
    filetypes=[("GeoJSON files", "*.geojson"), ("JSON files", "*.json")]
)
if not kraje_file:
    print("Soubor s kraji nebyl vybrán.")
    exit()

messagebox.showinfo("Krok 2", "Vložte soubor s daty pro okresy ČR.")

# vyber souboru s okresy
okresy_file = filedialog.askopenfilename(
    title="Vyberte GeoJSON soubor s okresy",
    filetypes=[("GeoJSON files", "*.geojson"), ("JSON files", "*.json")]
)
if not okresy_file:
    print("Soubor s okresy nebyl vybrán.")
    exit()

# cesta k souboru s mesty
messagebox.showinfo("Krok 3", "Vložte soubor s daty pro města ČR.")
mesta_file = filedialog.askopenfilename(
    title="Vyberte JSON soubor s městy",
    filetypes=[("JSON files", "*.json"), ("GeoJSON files", "*.geojson")]
)
if not mesta_file:
    print("Soubor s městy nebyl vybrán.")
    exit()

# nacteni
try:
    with open(mesta_file, "r", encoding="utf-8") as f:
        mesta_raw = json.load(f)
except Exception as e:
    messagebox.showerror("Chyba", f"Nepodařilo se načíst soubor měst:\n{mesta_file}\n\n{e}")
    raise

# pretvoreni na seznam s name, lat, lon, admin_name
mesta = []
for m in mesta_raw:
    try:
        name = m.get("city") or m.get("name") or m.get("town")
        lat = float(m.get("lat") or m.get("latitude"))
        lon = float(m.get("lng") or m.get("lon") or m.get("longitude"))
        admin = m.get("admin_name") or m.get("region") or ""
        mesta.append({"name": name, "lat": lat, "lon": lon, "admin_name": admin})
    except Exception:
        continue

# nacteni dat
gdf_kraje = gpd.read_file(kraje_file)
gdf_okresy = gpd.read_file(okresy_file)

# prepocet plochy na km² 
gdf_kraje['plocha_km2'] = gdf_kraje['shape_Area'] / 1_000_000
gdf_okresy['plocha_km2'] = gdf_okresy['shape_Area'] / 1_000_000

# vyber ulozeni vysledne mapy
save_path = filedialog.asksaveasfilename(
    title="Kam uložit HTML mapu",
    initialfile="Mapa_Pocet_obyvatel.html",
    defaultextension=".html",
    filetypes=[("HTML files", "*.html")]
)
if not save_path:
    print("Cesta pro uložení nebyla vybrána.")
    exit()

# vytvoreni mapy
mapa = folium.Map(location=[49.8, 15.5], zoom_start=7)


# barvení podle populace
def style_dynamic(feature):
    pop = feature['properties'].get('gis724060001', 0)
    try:
        pop = float(pop)
    except:
        pop = 0
    if pop < 50000:
        color = "#fff7bc"
    elif pop < 100000:
        color = "#fec44f"
    elif pop < 200000:
        color = "#fe9929"
    elif pop < 500000:
        color = "#ec7014"
    elif pop < 1000000:
        color = "#cc4c02"
    else:
        color = "#8c2d04" # (největší populace)

    return {
        'fillColor': color,
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.3
    }

def highlight_kraje(feature):
    return {
        'fillColor': "#3AA5C0D2",
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.4
    }

def highlight_okresy(feature):
    return {
        'fillColor': "#3AA5C0D2",
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.4
    }

# HTML legenda
legend_html = '''
<div style="
    position: fixed;
    top: 10px;
    right: 140px;
    width: 200px;
    padding: 0px 5px;
    z-index: 9999;
    font-size: 11px;
">
    <div style="text-align: center; margin-bottom: 2px; font-weight: bold; color: black;">
        Počet obyvatel kraje
    </div>
    <div style="
    width: 100%;
    height: 10px;
    background: linear-gradient(to right, 
        #fff7bc 0%,
        #fec44f 20%,
        #fe9929 40%,
        #ec7014 60%,
        #cc4c02 80%,
        #8c2d04 100%
    );
    border: 1px solid #ccc;
"></div>
</div>
'''
# pridani do mapy
mapa.get_root().html.add_child(folium.Element(legend_html))

# tooltipy
tooltip_kraje_fields = ['nazev', 'gis724060001', 'gis724060002', 'gis724060003', 'plocha_km2']
tooltip_kraje_aliases = ['Název kraje:', 'Celková populace:', 'Muži:', 'Ženy:', 'Plocha (km²):']

tooltip_okresy_fields = ['nazev', 'gis724060001', 'plocha_km2']
tooltip_okresy_aliases = ['Název okresu:', 'Počet obyvatel:', 'Plocha (km²):']


# Vrstvy
kraje_layer = folium.GeoJson(
    gdf_kraje,
    style_function=style_dynamic,
    highlight_function=highlight_kraje,
    tooltip=GeoJsonTooltip(fields=tooltip_kraje_fields, aliases=tooltip_kraje_aliases, localize=True),
    name="Kraje"
).add_to(mapa)
kraje_layer._name = "kraje_layer"

okresy_layer = folium.GeoJson(
    gdf_okresy,
    style_function=style_dynamic,
    highlight_function=highlight_okresy,
    tooltip=GeoJsonTooltip(fields=tooltip_okresy_fields, aliases=tooltip_okresy_aliases, localize=True),
    show=False,
    name="Okresy"
).add_to(mapa)


# mesta
mesta_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": m["name"]},
            "geometry": {"type": "Point", "coordinates": [m["lon"], m["lat"]]}
        }
        for m in mesta
    ]
}
mesta_layer = folium.FeatureGroup(name="Města", show=True)

for feature in mesta_geojson['features']:
    coords = feature['geometry']['coordinates']
    folium.CircleMarker(
        location=[coords[1], coords[0]],
        radius=5,
        color="#FFD700",
        fill=True,
        fill_color="#FFD700",
        fill_opacity=1,
        weight=1,
        popup=feature['properties']['name']
    ).add_to(mesta_layer)

mesta_layer.add_to(mapa)


# pridani ovladani vrstev
folium.LayerControl().add_to(mapa)

# uloteni mapy
mapa.save(save_path)

# okno po ulozeni
messagebox.showinfo(
    "Mapa uložena",
    f"Mapa byla úspěšně uložena do:\n{save_path}\n\n"
    "Po stisknutí OK se otevře v prohlížeči."
)

# otevreni mapy v prohlizeci
webbrowser.open(f"file://{os.path.abspath(save_path)}")
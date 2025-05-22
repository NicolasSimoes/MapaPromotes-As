import pandas as pd
import folium
from folium import DivIcon


df = pd.read_csv('promotesativmob.csv', encoding="ISO-8859-1", sep=';')
for col in ['LATITUDE CASA','LONGITUDE CASA','LATITUDE','LONGITUDE']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna(subset=['PROMOTOR'])


cores = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#393b79", "#637939", "#8c6d31", "#843c39", "#7b4173",
    "#3182bd", "#31a354", "#756bb1", "#636363", "#e6550d",
    "#969696", "#fec44f", "#bdbdbd"
]
promotores = df['PROMOTOR'].unique()
cores_prom = {p: cores[i % len(cores)] for i, p in enumerate(promotores)}


mapa = folium.Map(location=[-3.7424091, -38.4867581], zoom_start=13)

css = """
<style>
@keyframes blink { 0%{opacity:1;} 50%{opacity:0;} 100%{opacity:1;} }
.blinking-home { animation: blink 1s infinite; font-size:24px; }
</style>
"""
mapa.get_root().html.add_child(folium.Element(css))


for prom in promotores:
    dfp = df[df['PROMOTOR'] == prom].dropna(subset=['LATITUDE CASA','LONGITUDE CASA','LATITUDE','LONGITUDE'])
    if dfp.empty:
        continue

    cor = cores_prom[prom]
    fg = folium.FeatureGroup(name=f"Promotor: {prom}", show=True)

    
    casa = [dfp.iloc[0]['LATITUDE CASA'], dfp.iloc[0]['LONGITUDE CASA']]
    folium.Marker(
        location=casa,
        popup=f"Casa do Promotor {prom}",
        icon=DivIcon(
            icon_size=(60, 60), icon_anchor=(15, 15),
            html=(
                '<div class="blinking-home" '
                f'style="color:{cor};"><i class="fa fa-home"></i></div>'
            )
        )
    ).add_to(fg)

    
    rota = [casa]
    for _, row in dfp.iterrows():
        coords = [row['LATITUDE'], row['LONGITUDE']]
        popup_html = (
            f"<b>{row['LOJA']}</b><br>"
            f"Mix de Produtos: {row['Mix de Produtos quantidade']}"
        )
        folium.Marker(
            location=coords,
            popup=popup_html,
            icon=DivIcon(
                icon_size=(24, 24), icon_anchor=(12, 12),
                html=(
                    f'<div style="font-size:20px; color:{cor};">'
                    '<i class="fa fa-shopping-cart"></i>'
                    '</div>'
                )
            )
        ).add_to(fg)
        rota.append(coords)

    
    if len(rota) > 1:
        folium.PolyLine(rota, color=cor, weight=3, opacity=0.8).add_to(fg)

    mapa.add_child(fg)


legend_html = '''
<div style="position: fixed;
     bottom: 50px; left: 50px;
     width: 200px; height: 250px;
     background-color: white; opacity: 0.9; z-index:9999;
     font-size:14px; padding:10px;
     border:2px solid grey; border-radius:5px;
     overflow-y: auto;">
  <b style="display:block; margin-bottom:8px;">Legenda dos Promotores</b>
'''
for prom, cor in cores_prom.items():
    legend_html += (
        '<div style="display:flex; align-items:center; margin-bottom:6px;">'
        f'<i style="background:{cor}; width:12px; height:12px; margin-right:6px;"></i>'
        f'{prom}</div>'
    )
legend_html += '</div>'
mapa.get_root().html.add_child(folium.Element(legend_html))


folium.LayerControl(collapsed=True).add_to(mapa)
mapa.save("mapaRotasPromotores As.html")
print("Mapa salvo em mapa_casas_promotores.html")

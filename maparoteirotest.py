import pandas as pd
import folium
from folium import DivIcon

# 1) Ler e preparar o DataFrame
df = pd.read_csv('dbmaparoteironovo.csv', encoding="ISO-8859-1", sep=';')
for col in ['LATITUDE CASA','LONGITUDE CASA','LATITUDE','LONGITUDE']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna(subset=['PROMOTOR'])

# 2) Cores para cada promotor (hex)
cores = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#393b79", "#637939", "#8c6d31", "#843c39", "#7b4173",
    "#3182bd", "#31a354", "#756bb1", "#636363", "#e6550d",
    "#969696", "#fec44f", "#bdbdbd"
]
promotores = df['PROMOTOR'].unique()
cores_prom = {p: cores[i % len(cores)] for i, p in enumerate(promotores)}

# 3) Criar o mapa base
mapa = folium.Map(location=[-3.7424091, -38.4867581], zoom_start=13)

# CSS para ícone da casa piscante
css = """
<style>
@keyframes blink { 0%{opacity:1;} 50%{opacity:0;} 100%{opacity:1;} }
.blinking-home { animation: blink 1s infinite; font-size:24px; }
</style>
"""
mapa.get_root().html.add_child(folium.Element(css))

# 4) Construir overlays de cada promotor
for prom in promotores:
    dfp = df[df['PROMOTOR'] == prom].dropna(subset=['LATITUDE CASA','LONGITUDE CASA','LATITUDE','LONGITUDE'])
    if dfp.empty:
        continue

    cor = cores_prom[prom]
    fg = folium.FeatureGroup(name=f"Promotor: {prom}", show=True)

    # 4.1 Casa do promotor (DivIcon piscante)
    casa = [dfp.iloc[0]['LATITUDE CASA'], dfp.iloc[0]['LONGITUDE CASA']]
    folium.Marker(
        location=casa,
        popup=f"Casa do Promotor {prom}",
        icon=DivIcon(
            icon_size=(60, 60), icon_anchor=(15, 15),
            html=(
                '<div class=\"blinking-home\" '
                f'style=\"color:{cor};\"><i class=\"fa fa-home\"></i></div>'
            )
        )
    ).add_to(fg)

    # 4.2 Montar rota e marcar lojas com popup estendido
    rota = [casa]
    for _, row in dfp.iterrows():
        coords = [row['LATITUDE'], row['LONGITUDE']]
        popup_html = (
            f"<b>{row['LOJA']}</b><br>"
        )
        folium.Marker(
            location=coords,
            popup=popup_html,
            icon=DivIcon(
                icon_size=(24, 24), icon_anchor=(12, 12),
                html=(
                    f'<div style=\"font-size:20px; color:{cor};\">'
                    '<i class=\"fa fa-shopping-cart\"></i>'
                    '</div>'
                )
            )
        ).add_to(fg)
        rota.append(coords)

    # 4.3 Linha ligando casa → cada loja
    if len(rota) > 1:
        folium.PolyLine(rota, color=cor, weight=3, opacity=0.8).add_to(fg)

    mapa.add_child(fg)

# 5) Legenda vertical com rolagem interna
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
        '<div style=\"display:flex; align-items:center; margin-bottom:6px;\">'
        f'<i style=\"background:{cor}; width:12px; height:12px; margin-right:6px;\"></i>'
        f'{prom}</div>'
    )
legend_html += '</div>'
mapa.get_root().html.add_child(folium.Element(legend_html))

# 6) Controle de camadas
folium.LayerControl(collapsed=True).add_to(mapa)

# 7) Botão para desmarcar todas as camadas (posicionado ao lado do filtro de camadas)
deselect_js = """
<script>
function deselectAll() {
    var overlays = document.getElementsByClassName('leaflet-control-layers-overlays')[0];
    var inputs = overlays.getElementsByTagName('input');
    for (var i = 0; i < inputs.length; i++) {
        if (inputs[i].checked) { inputs[i].click(); }
    }
}
</script>
"""
# posiciona o botão no topo, à esquerda do botão de filtros
button_html = """
<button onclick=\"deselectAll()\"
 style=\"position: fixed; top: 10px; right: 70px; z-index:9999;
 background-color: white; padding:5px 8px; border:2px solid grey;
 border-radius:4px; cursor: pointer; font-size:14px;\">
 Desmarcar Todos
</button>
"""
mapa.get_root().html.add_child(folium.Element(deselect_js + button_html))

# 8) Salvar mapa
mapa.save("mapaNovoRoteiroJun.html")
print("Mapa salvo em mapaNovoRoteiroJun.html.html")
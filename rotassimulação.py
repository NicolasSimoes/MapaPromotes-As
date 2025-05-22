import pandas as pd
import math
import folium
from math import radians, sin, cos, atan2, sqrt
from branca.element import Template, MacroElement

# Parâmetros
MIN_PER_ROUTE = 6
MAX_PER_ROUTE = 12

# 1) Carrega e padroniza colunas
df = pd.read_csv("rotas.csv", sep=";", encoding="utf-8-sig")
df = df.rename(columns={"LOJA": "LOJA", "LOGITUDE": "LONGITUDE"})
df = df.dropna(subset=["LOJA", "LATITUDE", "LONGITUDE"]).reset_index(drop=True)
df["LATITUDE"] = df["LATITUDE"].astype(str).str.replace(",", ".").astype(float)
df["LONGITUDE"] = df["LONGITUDE"].astype(str).str.replace(",", ".").astype(float)

coords = list(zip(df["LATITUDE"], df["LONGITUDE"]))
N = len(coords)
if N < MIN_PER_ROUTE:
    raise ValueError(f"São apenas {N} LOJA; mínimo por rota é {MIN_PER_ROUTE}.")

def haversine(a, b):
    R = 6371
    lat1, lon1 = radians(a[0]), radians(a[1])
    lat2, lon2 = radians(b[0]), radians(b[1])
    dlat, dlon = lat2-lat1, lon2-lon1
    h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(h), sqrt(1-h))

# 2) Define quantas rotas (k) e quantos pontos em cada
k = math.ceil(N / MAX_PER_ROUTE)
if not (k*MIN_PER_ROUTE <= N <= k*MAX_PER_ROUTE):
    raise ValueError("Não é possível particionar dentro dos limites dados.")

sizes = [MIN_PER_ROUTE]*k
resto = N - MIN_PER_ROUTE*k
for i in range(k):
    extra = min(resto, MAX_PER_ROUTE - MIN_PER_ROUTE)
    sizes[i] += extra
    resto -= extra

# 3) Sweep clustering
centroid = (df["LATITUDE"].mean(), df["LONGITUDE"].mean())
angles = [atan2(lat-centroid[0], lon-centroid[1]) for lat,lon in coords]
idx_sorted = [i for i,_ in sorted(enumerate(coords), key=lambda x: angles[x[0]])]

clusters = []
pos = 0
for sz in sizes:
    clusters.append(idx_sorted[pos:pos+sz])
    pos += sz

# 4) Rota interna por vizinho mais próximo
def nearest_neighbor(cluster):
    unvisited = set(cluster)
    route = [cluster[0]]
    unvisited.remove(cluster[0])
    while unvisited:
        last = route[-1]
        nxt = min(unvisited, key=lambda j: haversine(coords[last], coords[j]))
        route.append(nxt)
        unvisited.remove(nxt)
    return route

routes = [nearest_neighbor(c) for c in clusters]

# 5) Desenha no Folium com FeatureGroups e LayerControl
m = folium.Map(location=centroid, zoom_start=12)
colors = [
    "red","blue","green","purple","orange","darkred",
    "lightred","beige","darkblue","darkgreen","cadetblue","darkpurple"
]

for i, route in enumerate(routes):
    cor = colors[i % len(colors)]
    fg = folium.FeatureGroup(name=f"Rota {i+1}")
    for idx in route:
        folium.Marker(
            location=coords[idx],
            popup=df.loc[idx, "LOJA"],
            icon=folium.Icon(prefix="fa", icon="shopping-cart", color=cor)
        ).add_to(fg)
    folium.PolyLine(
        locations=[coords[idx] for idx in route],
        color=cor, weight=3, opacity=0.8
    ).add_to(fg)
    m.add_child(fg)

# LayerControl padrão
m.add_child(folium.LayerControl(collapsed=False))

# 6) Botão “Desmarcar Todas”
template = """
{% macro html(this,kwargs) %}
  <div style="position: fixed; top: 10px; right: 130px; z-index:9999;">
    <button onclick="uncheckAll()" style="padding:5px 10px;">
      Desmarcar Todas
    </button>
  </div>
  <script>
    function uncheckAll(){
      var inputs = document.getElementsByClassName('leaflet-control-layers-selector');
      for(var i=0; i<inputs.length; i++){
        if(inputs[i].checked){
          inputs[i].click();
        }
      }
    }
  </script>
{% endmacro %}
"""
macro = MacroElement()
macro._template = Template(template)
m.get_root().add_child(macro)

# Salva
m.save("rotas.html")
print("Mapa salvo em rotas_com_botao.html")

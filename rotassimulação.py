import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from scipy.spatial.distance import cdist
import folium
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from tqdm import tqdm

# ↓↓↓ Ajuste aqui seus parâmetros ↓↓↓
MIN_SIZE       = 8        # mínimo de lojas por cluster
MAX_SIZE       = 12       # máximo de lojas por cluster
BATCH_SIZE     = 100      # para MiniBatchKMeans
MAX_ITER_KMEAN = 100      # iterações do MiniBatchKMeans
MAX_REBALANCE  = 50       # iterações máximas de rebalanceamento
RANDOM_SEED    = 42
# ↑↑↑ fim dos parâmetros ↑↑↑

# 1) Lê dados
df = pd.read_csv('rotas.csv', sep=';')
df.columns = df.columns.str.strip()
coords = df[['LATITUDE','LONGITUDE']].to_numpy()
N = coords.shape[0]

# 2) Define número de clusters inicial
avg_size   = (MIN_SIZE + MAX_SIZE) / 2
n_clusters = int(round(N / avg_size))

# 3) Roda MiniBatchKMeans
mbk = MiniBatchKMeans(
    n_clusters=n_clusters,
    batch_size=BATCH_SIZE,
    max_iter=MAX_ITER_KMEAN,
    n_init=1,
    random_state=RANDOM_SEED
)
labels    = mbk.fit_predict(coords)
centroids = mbk.cluster_centers_.copy()

# 4) Rebalanceamento (com barra de progresso)
for it in tqdm(range(1, MAX_REBALANCE+1), desc='Rebalanceando clusters'):
    sizes = np.bincount(labels, minlength=n_clusters)
    small = np.where((sizes>0)&(sizes<MIN_SIZE))[0]
    large = np.where(sizes>MAX_SIZE)[0]

    if not small.size and not large.size:
        break

    # 4a) reatribui pequenos
    if small.size:
        idxs = np.nonzero(np.isin(labels, small))[0]
        D = cdist(coords[idxs], centroids, metric='euclidean')
        D[:, small] = np.inf
        labels[idxs] = np.argmin(D, axis=1)

    # 4b) retira excedentes
    if large.size:
        for cl in large:
            idxs_cl = np.where(labels==cl)[0]
            excess  = sizes[cl] - MAX_SIZE
            if excess>0:
                pts      = coords[idxs_cl]
                dist_own = np.linalg.norm(pts-centroids[cl], axis=1)
                far     = np.argsort(-dist_own)[:excess]
                idxs_mv = idxs_cl[far]
                Dm      = cdist(coords[idxs_mv], centroids, metric='euclidean')
                Dm[:, cl] = np.inf
                labels[idxs_mv] = np.argmin(Dm, axis=1)

    # 4c) recalcula centróides
    for cl in range(n_clusters):
        mem = coords[labels==cl]
        if mem.size:
            centroids[cl] = mem.mean(axis=0)

# 5) Anexa ao DataFrame e exporta CSV
df['cluster'] = labels.astype(int)
df[['LOJA','cluster']].to_csv('lojas_clusters.csv', index=False)
print("CSV de clusters salvo em → lojas_clusters.csv")

# 6) Prepara cores e FeatureGroups
unique = sorted(df['cluster'].unique())
cmap   = plt.get_cmap('tab20', len(unique))
colors = {u: mcolors.to_hex(cmap(i)) for i,u in enumerate(unique)}

# 7) Cria mapa e grupos
m = folium.Map(
    location=[df['LATITUDE'].mean(), df['LONGITUDE'].mean()],
    zoom_start=12
)

feature_groups = {
    u: folium.FeatureGroup(name=f"Cluster {u}", show=(u!=-1))
    for u in unique
}
for fg in feature_groups.values():
    m.add_child(fg)

for _, row in df.iterrows():
    cl = row['cluster']
    folium.CircleMarker(
        location=(row['LATITUDE'], row['LONGITUDE']),
        radius=6,
        color=colors[cl],
        fill=True,
        fill_color=colors[cl],
        fill_opacity=0.7,
        popup=f"{row['LOJA']} (cluster {cl})"
    ).add_to(feature_groups[cl])

# 8) Adiciona controle de camadas e salva
folium.LayerControl(collapsed=False).add_to(m)
m.save('mapa_clusters.html')
print(f"{len(unique)} camadas (clusters) disponíveis em → mapa_clusters.html")

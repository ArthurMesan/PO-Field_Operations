import csv
import time

import folium
import googlemaps
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import polyline

API_KEY = "xx"
gmaps = googlemaps.Client(key=API_KEY)

# Lista expandida de regiões
regionais = [
    "Barreiro, Belo Horizonte, MG",
    "Centro-Sul, Belo Horizonte, MG",
    "Leste, Belo Horizonte, MG",
    "Nordeste, Belo Horizonte, MG",
    "Pampulha, Belo Horizonte, MG",
    "Venda Nova, Belo Horizonte, MG",
    "Padre Eustáquio, Belo Horizonte, MG",
    "Castelo, Belo Horizonte, MG",
    "Bairro Ouro Preto, Belo Horizonte, MG",
    "Balneário da Ressaca, Contagem, MG",
    "Nacional, Contagem, MG",
    "Santa Luzia, MG",
    "Planalto, Belo Horizonte, MG",
    "União, Belo Horizonte, MG",
]

destino_ufmg = "UFMG Campus Pampulha, Antônio Carlos 6627, Belo Horizonte, MG"

# Configurando o Mapa
mapa = folium.Map(location=[-19.869, -43.966], zoom_start=12)
folium.Marker(
    location=[-19.869, -43.966],
    popup="UFMG - Campus Pampulha",
    icon=folium.Icon(color="red", icon="info-sign"),
).add_to(mapa)

# GERAÇÃO DINÂMICA DE CORES
cmap = plt.get_cmap("tab20")  # Paleta com 20 cores distintas
cores = [cmap(i) for i in range(len(regionais))]

# Configurando o CSV
nome_arquivo_csv = "distancias_ufmg.csv"
nome_arquivo_mapa = "mapa_rotas_ufmg.html"


print(f"Iniciando busca de rotas para {len(regionais)} regiões...\n")

with open(nome_arquivo_csv, mode="w", newline="", encoding="utf-8") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)
    escritor.writerow(["Regional", "Distancia_km", "Tempo_minutos"])

    for idx, origem in enumerate(regionais):
        nome_curto = origem.split(",")[0]

        # Converte a tupla de cor do matplotlib para formato Hexadecimal para o Folium
        cor_hex = mcolors.to_hex(cores[idx])

        try:
            resultado = gmaps.directions(origem, destino_ufmg, mode="driving")

            if resultado:
                rota = resultado[0]
                linha_codificada = rota["overview_polyline"]["points"]
                distancia_km = rota["legs"][0]["distance"]["value"] / 1000.0
                tempo_min = rota["legs"][0]["duration"]["value"] / 60.0

                # Salvando no CSV
                escritor.writerow(
                    [nome_curto, round(distancia_km, 2), round(tempo_min, 2)]
                )

                # Desenhando no Mapa
                coordenadas = polyline.decode(linha_codificada)
                folium.PolyLine(
                    coordenadas,
                    color=cor_hex,
                    weight=5,
                    opacity=0.8,
                    tooltip=f"{nome_curto}: {distancia_km:.1f}km",
                ).add_to(mapa)

                print(f"Sucesso: {nome_curto} ({distancia_km:.2f} km)")
            else:
                print(f"Nenhuma rota encontrada para {nome_curto}.")

        except Exception as e:
            print(f"Erro ao processar {nome_curto}: {e}")

        time.sleep(1)

mapa.save(nome_arquivo_mapa)
print(f"\nMapa gerado com sucesso em '{nome_arquivo_mapa}'.")

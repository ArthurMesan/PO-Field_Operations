import csv

# Custos do Veículo
preco_diesel = 6.94  # Preço do litro do diesel em Reais
eficiencia_onibus = 2.6  # Consumo médio de um ônibus de 40 lugares (km/L)

# Custos de Mão de Obra (Motorista)
salario_motorista = 3500.00  # Salário base estimado em Reais
horas_mensais = 220  # Jornada padrão CLT
custo_por_minuto = salario_motorista / (horas_mensais * 60)


distancias = []
tempos = []
regionais = []

try:
    with open("distancias_ufmg.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            regionais.append(row["Regional"])
            distancias.append(float(row["Distancia_km"]))
            # Agora também pegamos a coluna de tempo que a API gerou
            tempos.append(float(row["Tempo_minutos"]))
except FileNotFoundError:
    print("ERRO: O arquivo 'distancias_ufmg.csv' não foi encontrado!")
    exit()


h = []
for idx in range(len(distancias)):
    dist_ida = distancias[idx]
    tempo_ida = tempos[idx]

    # Custo de Combustível (Ida e Volta)
    litros_gastos = (dist_ida * 2) / eficiencia_onibus
    custo_diesel = litros_gastos * preco_diesel

    # Custo da Mão de Obra (Tempo total da viagem de Ida e Volta)
    tempo_total_viagem = tempo_ida * 2
    custo_salario = tempo_total_viagem * custo_por_minuto

    # Custo Operacional Total da Viagem
    custo_total = custo_diesel + custo_salario
    h.append(round(custo_total, 2))


nome_arquivo_saida = "custos_operacionais.txt"

texto_saida = "# Custos de operação dinâmicos (h_i) extraídos da API do Google\n"
texto_saida += f"h = {h}\n\n"

texto_saida += "# Referência de Regiões (apenas para conferência):\n"
for idx, regiao in enumerate(regionais):
    texto_saida += f"# {regiao}: R$ {h[idx]:.2f}\n"

# Escrevendo no arquivo TXT
with open(nome_arquivo_saida, mode="w", encoding="utf-8") as file:
    file.write(texto_saida)

print(f"Sucesso! Os custos foram calculados e salvos em '{nome_arquivo_saida}'.")

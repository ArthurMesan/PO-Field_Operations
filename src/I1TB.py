import gurobipy as gp
import matplotlib.pyplot as plt
import numpy as np
from gurobipy import GRB

# PARÂMETROS E DADOS DE ENTRADA
# Instância Expandida: 14 regionais
regionais = [
    "Barreiro",
    "Centro-Sul",
    "Leste",
    "Nordeste",
    "Pampulha",
    "Venda Nova",
    "Padre Eustáquio",
    "Castelo",
    "Ouro Preto",
    "Balneário da Ressaca",
    "Nacional",
    "Santa Luzia",
    "Planalto",
    "União",
]
horarios = ["07:00", "11:00", "18:00"]

I = range(len(regionais))
T = range(len(horarios))

# Capacidade de um ônibus único padrão (B)
B = 40

# Frota total disponível por horário (F_t)
F = [180, 120, 80]

# Matriz de demanda d_it (Alunos por regional em cada horário)
d = [
    [850, 300, 150],  # Barreiro
    [250, 100, 50],  # Centro-Sul
    [500, 200, 100],  # Leste
    [600, 250, 150],  # Nordeste
    [200, 100, 50],  # Pampulha
    [950, 400, 200],  # Venda Nova
    [400, 180, 80],  # Padre Eustáquio
    [350, 150, 60],  # Castelo
    [300, 120, 50],  # Ouro Preto
    [450, 200, 90],  # Balneário da Ressaca
    [500, 220, 100],  # Nacional
    [700, 300, 130],  # Santa Luzia
    [400, 160, 70],  # Planalto
    [380, 150, 60],  # União
]

# Custos de ativação (c_i) - Taxa de Uso do Viário
c = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]

# Custos de operação estáticos (h_i) estimados pela distância + tempo
h = [
    108.48,
    47.99,
    71.43,
    41.0,
    15.05,
    39.45,
    42.87,
    30.96,
    19.7,
    54.99,
    52.0,
    62.67,
    36.3,
    37.0,
]

# Penalidade-base (rho_padrao) e Prioridade territorial (q_i)
rho_padrao = 12.6
q = [
    1.30,
    0.70,
    1.10,
    1.15,
    0.65,
    1.40,
    1.00,
    0.80,
    0.85,
    1.35,
    1.30,
    1.25,
    0.95,
    1.05,
]


# INICIALIZAÇÃO DO MODELO
m = gp.Model("Linhas_Diretas_UFMG")
m.setParam("OutputFlag", 0)  # Esconde os logs do solver para não poluir o terminal


# VARIÁVEIS DE DECISÃO
x = m.addVars(I, T, vtype=GRB.INTEGER, name="x")  # alunos atendidos
u = m.addVars(I, T, vtype=GRB.INTEGER, name="u")  # alunos não atendidos
z = m.addVars(I, T, vtype=GRB.INTEGER, name="z")  # ônibus alocados
y = m.addVars(I, T, vtype=GRB.BINARY, name="y")  # se a linha opera no horário
w = m.addVars(I, vtype=GRB.BINARY, name="w")  # se a regional foi coberta

# RESTRIÇÕES PADRÃO (Serão mantidas/alteradas dinamicamente depois)
for i in I:
    for t in T:
        m.addConstr(x[i, t] + u[i, t] == d[i][t], name=f"Atendimento_{i}_{t}")
        m.addConstr(x[i, t] <= B * z[i, t], name=f"Capacidade_{i}_{t}")
        m.addConstr(y[i, t] <= z[i, t], name=f"AtivacaoMin_{i}_{t}")
        m.addConstr(z[i, t] <= F[t] * y[i, t], name=f"AtivacaoMax_{i}_{t}")
        m.addConstr(x[i, t] >= y[i, t], name=f"GarantiaOp_{i}_{t}")
        m.addConstr(y[i, t] <= w[i], name=f"Consistencia1_{i}_{t}")
    m.addConstr(w[i] <= gp.quicksum(y[i, t] for t in T), name=f"Consistencia2_{i}")

# Restrição de Frota Original (salvamos a referência para removê-la depois)
frota_constrs = []
for t in T:
    frota_constrs.append(
        m.addConstr(gp.quicksum(z[i, t] for i in I) <= F[t], name=f"FrotaTotal_{t}")
    )


# RESOLUÇÃO PADRÃO (Cenário Base)
m.setObjective(
    gp.quicksum(c[i] * y[i, t] for i in I for t in T)
    + gp.quicksum(h[i] * z[i, t] for i in I for t in T)
    + gp.quicksum(rho_padrao * q[i] * u[i, t] for i in I for t in T)
    + gp.quicksum(rho_padrao * q[i] * (1 - w[i]) for i in I),
    GRB.MINIMIZE,
)
m.optimize()

alocacao_onibus = np.zeros((len(regionais), len(horarios)))
demanda_atendida = np.zeros(len(regionais))
demanda_nao_atendida = np.zeros(len(regionais))

if m.Status == GRB.OPTIMAL:
    print("\n--- Solução Ótima (Cenário Base) Encontrada ---")
    print(f"Custo Total (Z): R$ {m.ObjVal:.2f}")

    for i in I:
        for t in T:
            alocacao_onibus[i, t] = z[i, t].X
            demanda_atendida[i] += x[i, t].X
            demanda_nao_atendida[i] += u[i, t].X


# ANÁLISE DE SENSIBILIDADE (Variação do Rho)
print("Rodando análise de sensibilidade do Rho...")
valores_rho = np.linspace(0, 50, 26)
historico_nao_atendidos_rho = []
historico_atendidos_rho = []
historico_custo_real_rho = []

for r in valores_rho:
    m.setObjective(
        gp.quicksum(c[i] * y[i, t] for i in I for t in T)
        + gp.quicksum(h[i] * z[i, t] for i in I for t in T)
        + gp.quicksum(r * q[i] * u[i, t] for i in I for t in T)
        + gp.quicksum(r * q[i] * (1 - w[i]) for i in I),
        GRB.MINIMIZE,
    )
    m.optimize()

    if m.Status == GRB.OPTIMAL:
        total_nao_atendidos = sum(u[i, t].X for i in I for t in T)
        total_atendidos = sum(x[i, t].X for i in I for t in T)

        custo_real = sum(c[i] * y[i, t].X for i in I for t in T) + sum(
            h[i] * z[i, t].X for i in I for t in T
        )

        historico_nao_atendidos_rho.append(total_nao_atendidos)
        historico_atendidos_rho.append(total_atendidos)
        historico_custo_real_rho.append(custo_real)
    else:
        historico_nao_atendidos_rho.append(None)
        historico_atendidos_rho.append(None)
        historico_custo_real_rho.append(None)


# ANÁLISE DE SENSIBILIDADE DA FROTA (Nova Etapa)
print("Rodando análise de sensibilidade da frota...")

# Restaurar o Rho padrão no objetivo antes de iterar a frota
m.setObjective(
    gp.quicksum(c[i] * y[i, t] for i in I for t in T)
    + gp.quicksum(h[i] * z[i, t] for i in I for t in T)
    + gp.quicksum(rho_padrao * q[i] * u[i, t] for i in I for t in T)
    + gp.quicksum(rho_padrao * q[i] * (1 - w[i]) for i in I),
    GRB.MINIMIZE,
)

# Remover a restrição de frota original estática
for constr in frota_constrs:
    m.remove(constr)

# Range da frota total (ex: de 1 até 300, iterando de 5 em 5 para velocidade)
limite_frota_range = range(1, 301, 5)
historico_custo_real_frota = []
historico_nao_atendidos_frota = []
historico_atendidos_frota = []

# Criamos uma variável de restrição que será atualizada dinamicamente
restricoes_frota_dinamica = []

for f_total in limite_frota_range:
    # Remove as restrições da iteração anterior, se existirem
    for constr in restricoes_frota_dinamica:
        m.remove(constr)
    restricoes_frota_dinamica = []

    # Adiciona a nova restrição de frota máxima global para a iteração atual (soma de todos os horários)
    for t in T:
        c_frota = m.addConstr(
            gp.quicksum(z[i, t] for i in I) <= f_total, name=f"FrotaDinamica_{t}"
        )
        restricoes_frota_dinamica.append(c_frota)

    m.optimize()

    if m.Status == GRB.OPTIMAL:
        historico_nao_atendidos_frota.append(sum(u[i, t].X for i in I for t in T))
        historico_atendidos_frota.append(sum(x[i, t].X for i in I for t in T))
        custo_real = sum(c[i] * y[i, t].X for i in I for t in T) + sum(
            h[i] * z[i, t].X for i in I for t in T
        )
        historico_custo_real_frota.append(custo_real)
    else:
        historico_nao_atendidos_frota.append(None)
        historico_atendidos_frota.append(None)
        historico_custo_real_frota.append(None)


# GERAÇÃO DOS GRÁFICOS EM JANELAS SEPARADAS

# JANELA 1: CENÁRIO BASE
fig1, axes1 = plt.subplots(1, 2, figsize=(16, 7))
fig1.canvas.manager.set_window_title("Cenário Base: Operação Diária")

x_pos = np.arange(len(regionais))
total_width = 0.8
width = total_width / len(horarios)

for t_idx, t_label in enumerate(horarios):
    offset = (t_idx - len(horarios) / 2) * width + width / 2
    axes1[0].bar(
        x_pos + offset, alocacao_onibus[:, t_idx], width, label=f"Horário: {t_label}"
    )

axes1[0].set_ylabel("Quantidade de Ônibus ($z_{it}$)")
axes1[0].set_title(f"Alocação de Ônibus (Cenário Base: Rho = {rho_padrao})")
axes1[0].set_xticks(x_pos)
axes1[0].set_xticklabels(regionais, rotation=45, ha="right")
axes1[0].legend()
axes1[0].grid(axis="y", linestyle="--", alpha=0.7)

axes1[1].bar(regionais, demanda_atendida, label="Atendida ($x_{it}$)", color="green")
axes1[1].bar(
    regionais,
    demanda_nao_atendida,
    bottom=demanda_atendida,
    label="Não Atendida ($u_{it}$)",
    color="red",
)
axes1[1].set_ylabel("Número de Alunos")
axes1[1].set_title(f"Situação da Demanda Diária (Cenário Base: Rho = {rho_padrao})")
axes1[1].tick_params(axis="x", rotation=45)
axes1[1].set_xticks(x_pos)
axes1[1].set_xticklabels(regionais, rotation=45, ha="right")
axes1[1].legend()
axes1[1].grid(axis="y", linestyle="--", alpha=0.7)

fig1.tight_layout()

# JANELA 2: ANÁLISE DE SENSIBILIDADE DO RHO
fig2, axes2 = plt.subplots(1, 2, figsize=(16, 7))
fig2.canvas.manager.set_window_title("Análise de Sensibilidade: Variação da Penalidade")

axes2[0].plot(
    valores_rho,
    historico_nao_atendidos_rho,
    marker="o",
    color="red",
    linewidth=2,
    label="Não Atendidos",
)
axes2[0].plot(
    valores_rho,
    historico_atendidos_rho,
    marker="^",
    color="green",
    linewidth=2,
    label="Atendidos",
)
axes2[0].set_ylabel("Total de Alunos (Soma de Todas Regionais)")
axes2[0].set_xlabel("Valor da Penalidade Base ($Rho$)")
axes2[0].set_title("Efeito do Rho na Cobertura da Demanda")
axes2[0].legend()
axes2[0].grid(True, linestyle="--", alpha=0.7)

axes2[1].plot(
    valores_rho, historico_custo_real_rho, marker="s", color="blue", linewidth=2
)
axes2[1].set_ylabel("Custo Financeiro Real Diário (R$)")
axes2[1].set_xlabel("Valor da Penalidade Base ($Rho$)")
axes2[1].set_title("Efeito do Rho no Orçamento Operacional (Sem Multas)")
axes2[1].grid(True, linestyle="--", alpha=0.7)

fig2.tight_layout()

# JANELA 3: ANÁLISE DE SENSIBILIDADE DA FROTA
fig3, axes3 = plt.subplots(1, 2, figsize=(16, 7))
fig3.canvas.manager.set_window_title(
    "Análise de Sensibilidade: Variação da Frota Máxima"
)

axes3[0].plot(
    limite_frota_range,
    historico_nao_atendidos_frota,
    marker="o",
    color="red",
    label="Não Atendidos",
)
axes3[0].plot(
    limite_frota_range,
    historico_atendidos_frota,
    marker="^",
    color="green",
    label="Atendidos",
)
axes3[0].set_ylabel("Total de Alunos")
axes3[0].set_xlabel("Capacidade Máxima de Ônibus ($F_{total}$)")
axes3[0].set_title("Impacto da Frota na Cobertura da Demanda")
axes3[0].legend()
axes3[0].grid(True, linestyle="--", alpha=0.6)

axes3[1].plot(
    limite_frota_range,
    historico_custo_real_frota,
    marker="s",
    color="blue",
    linewidth=2,
)
axes3[1].set_ylabel("Custo Operacional Total (R$)")
axes3[1].set_xlabel("Capacidade Máxima de Ônibus ($F_{total}$)")
axes3[1].set_title("Custo Operacional vs. Aumento da Frota")
axes3[1].grid(True, linestyle="--", alpha=0.6)

fig3.tight_layout()

# Exibe todas as três janelas
plt.show()

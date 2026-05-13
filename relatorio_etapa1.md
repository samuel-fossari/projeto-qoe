# Programabilidade de Infraestruturas de Rede
## Melhoria da QoE em Streaming de Vídeo com Mininet, SDN e P4

**Relatório de Progresso — Etapa 1**
Maio de 2025

---

## 1. Objetivo Geral

Este projeto tem como objetivo projetar, implementar e avaliar um mecanismo de rede programável para detectar e mitigar a degradação da Qualidade de Experiência (QoE) em fluxos de streaming de vídeo. O ambiente utiliza Mininet para emulação de redes, o controlador SDN POX para programação do plano de controle, e possui extensão opcional em P4.

---

## 2. Ambiente Experimental

### 2.1 Versões de Software

| Software | Versão | Status |
|---|---|---|
| Python | 3.12.3 | ✅ OK |
| Mininet | 2.3.0 | ✅ OK |
| POX Controller | 0.7.0 (gar) | ✅ OK |
| Open vSwitch | 3.3.4 | ✅ OK |
| iproute2 / tc | 6.1.0 | ✅ OK |
| iperf3 | 3.16 | ✅ OK |
| nginx | 1.24.0 (Ubuntu) | ✅ OK |
| git | 2.54.0 | ✅ OK |

### 2.2 Topologia da Rede

A topologia implementada consiste em 1 servidor de vídeo, 2 clientes e 2 switches OpenFlow:

```
                    [Controlador POX]
                    OpenFlow 1.0 — porta 6633
                      /            \
                     /              \
              [Switch s1]  ←→  [Switch s2]
              OpenFlow       10 Mbps / 5ms     OpenFlow
                  |                      |            |
              100 Mbps               100 Mbps    100 Mbps
                  |                      |            |
            [Servidor]             [Cliente 1]  [Cliente 2]
           nginx + DASH             10.0.0.2     10.0.0.3
            10.0.0.1
```

**Características dos links:**
- Servidor → s1: 100 Mbps, sem degradação
- s1 → s2: 10 Mbps, 5ms de latência (link de gargalo — onde a degradação será aplicada na Etapa 2)
- s2 → clientes: 100 Mbps, sem degradação

**Endereços IP:**
- Servidor: 10.0.0.1/24
- Cliente 1: 10.0.0.2/24
- Cliente 2: 10.0.0.3/24

### 2.3 Organização do Repositório

| Diretório / Arquivo | Descrição |
|---|---|
| `topology/topologia.py` | Script Mininet com a topologia da rede |
| `controller/qoe_controller.py` | Lógica de controle SDN (POX) |
| `streaming/nginx.conf` | Configuração do servidor DASH |
| `traffic/degradacao.sh` | Scripts de indução de degradação (tc netem) |
| `metrics/coletar.py` | Coleta automatizada de métricas |
| `metrics/plotar.py` | Geração de gráficos |
| `results/` | Dados e gráficos gerados nos experimentos |
| `p4/` | Extensão P4 (Etapa 4) |
| `Makefile` | Automação de execução |
| `README.md` | Instruções de reprodução |

---

## 3. Resultados da Etapa 1

### 3.1 Conectividade

Após a inicialização da topologia com o controlador POX ativo, o teste de conectividade `pingAll` retornou **0% de perda de pacotes (6/6 recebidos)**, confirmando o funcionamento correto do encaminhamento L2 via OpenFlow 1.0.

| Origem | Destino | Resultado |
|---|---|---|
| servidor (10.0.0.1) | cliente1 (10.0.0.2) | ✅ 0% perda |
| servidor (10.0.0.1) | cliente2 (10.0.0.3) | ✅ 0% perda |
| cliente1 (10.0.0.2) | cliente2 (10.0.0.3) | ✅ 0% perda |

### 3.2 Observações

Durante a execução foram observados os seguintes avisos, todos sem impacto funcional:

- **`sch_htb: quantum of class 50001 is big`** — aviso do kernel sobre configuração de QoS; não afeta os experimentos
- **POX com Python 3.12** — versão fora da lista oficialmente suportada; o encaminhamento L2 funciona corretamente; erros de parsing de DNS são consequência desta incompatibilidade e não afetam o plano de dados

---

## 4. Próximas Etapas

| Etapa | Prazo | Descrição |
|---|---|---|
| Etapa 2 | 20 de maio | Indução de degradação com `tc netem` e caracterização da QoE sob carga adversa |
| Etapa 3 | 10 de junho | Implementação da lógica de controle SDN para mitigação de degradação |
| Etapa 4 | 24 de junho | Avaliação experimental completa e extensão P4 |

---

## 5. Instruções de Reprodução

**Pré-requisitos:**
- Ubuntu 24.04 (ou compatível)
- Mininet 2.3.0, POX 0.7.0, Open vSwitch 3.3.4
- iperf3 e nginx instalados via apt

**Execução:**

```bash
# Terminal 1 — Controlador POX
cd ~/pox
python3 pox.py forwarding.l2_learning

# Terminal 2 — Topologia Mininet
cd ~/projeto-qoe
sudo python3 topology/topologia.py
```

**Verificação:** o `pingAll` deve reportar `0% dropped (6/6 received)`.

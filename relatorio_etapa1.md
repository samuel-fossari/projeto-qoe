# Programabilidade de Infraestruturas de Rede
## Melhoria da QoE em Streaming de Vídeo com Mininet, SDN e P4

**Relatório de Progresso — Etapa 1**
Maio de 2026

---

## 1. Objetivo Geral

Este projeto tem como objetivo projetar, implementar e avaliar um mecanismo de rede programável para detectar e mitigar a degradação da Qualidade de Experiência (QoE) em fluxos de streaming de vídeo. O ambiente utiliza Mininet para emulação de redes, o controlador SDN POX para programação do plano de controle, e possui extensão opcional em P4.

---

## 2. Ambiente Experimental

### 2.1 Versões de Software

| Software | Versão | Status |
|---|---|---|
| Python | 3.12.3 | OK |
| Mininet | 2.3.0 | OK |
| POX Controller | 0.7.0 (gar) | OK |
| Open vSwitch | 3.3.4 | OK |
| iproute2 / tc | 6.1.0 | OK |
| iperf3 | 3.16 | OK |
| nginx | 1.24.0 (Ubuntu) | OK |
| ffmpeg | 6.1.1 | OK |
| VLC | 3.0.20 | OK |
| git | 2.54.0 | OK |

### 2.2 Topologia da Rede

A topologia implementada consiste em 1 servidor de vídeo, 2 clientes e 2 switches OpenFlow:

```
                    [Controlador POX]
                    OpenFlow 1.0 — porta 6633
                      /            \
                     /              \
              [Switch s1]  <->  [Switch s2]
              OpenFlow       10 Mbps / 5ms       OpenFlow
                  |                      |              |
              100 Mbps               100 Mbps      100 Mbps
                  |                      |              |
            [Servidor]             [Cliente 1]    [Cliente 2]
           nginx + DASH             10.0.0.2       10.0.0.3
            10.0.0.1
```

**Características dos links:**

- Servidor para s1: 100 Mbps, sem degradação
- s1 para s2: 10 Mbps, 5ms de latência (link de gargalo — onde a degradação será aplicada na Etapa 2)
- s2 para clientes: 100 Mbps, sem degradação

**Endereços IP:**

- Servidor: 10.0.0.1/24
- Cliente 1: 10.0.0.2/24
- Cliente 2: 10.0.0.3/24

### 2.3 Organização do Repositório

| Diretório / Arquivo | Descrição |
|---|---|
| topology/topologia.py | Script Mininet com a topologia da rede |
| controller/qoe_controller.py | Lógica de controle SDN (POX) |
| streaming/nginx.conf | Configuração do servidor DASH |
| traffic/degradacao.sh | Scripts de indução de degradação (tc netem) |
| metrics/coletar.py | Coleta automatizada de métricas |
| metrics/plotar.py | Geração de gráficos |
| results/ | Dados e gráficos gerados nos experimentos |
| p4/ | Extensão P4 (Etapa 4) |
| Makefile | Automação de execução |
| README.md | Instruções de reprodução |

---

## 3. Resultados da Etapa 1

### 3.1 Conectividade

Após a inicialização da topologia com o controlador POX ativo, o teste de conectividade pingAll retornou **0% de perda de pacotes (6/6 recebidos)**, confirmando o funcionamento correto do encaminhamento L2 via OpenFlow 1.0.

| Origem | Destino | Resultado |
|---|---|---|
| servidor (10.0.0.1) | cliente1 (10.0.0.2) | 0% perda |
| servidor (10.0.0.1) | cliente2 (10.0.0.3) | 0% perda |
| cliente1 (10.0.0.2) | cliente2 (10.0.0.3) | 0% perda |

### 3.2 Servidor de Vídeo DASH

O servidor de vídeo foi configurado utilizando nginx com conteúdo DASH gerado via ffmpeg.

**Geração do conteúdo:**

Um vídeo sintético de 2 minutos (1280x720, H.264 + AAC, yuv420p) foi gerado com ffmpeg e segmentado em três qualidades para simular a adaptação de bitrate do DASH:

| Stream | Resolução | Bitrate de vídeo | Bitrate de áudio |
|---|---|---|---|
| Baixa qualidade | 640x360 | 250 kbps | 64 kbps |
| Média qualidade | 854x480 | 500 kbps | 96 kbps |
| Alta qualidade | 1280x720 | 1000 kbps | 128 kbps |

O segmentador gerou 6 streams (3 de vídeo + 3 de áudio), cada um com 15 a 24 segmentos .m4s e um manifesto principal stream.mpd.

**Configuração do nginx:**

O nginx foi configurado para servir os segmentos DASH com os cabeçalhos HTTP corretos: Content-Type application/dash+xml, Access-Control-Allow-Origin *, Cache-Control no-cache.

**Verificação externa (fora do Mininet):**

```
curl -I http://localhost/stream.mpd
HTTP/1.1 200 OK
Content-Type: application/dash+xml
```

**Verificação interna (dentro do Mininet):**

O nginx foi iniciado dentro do namespace de rede do host servidor e o cliente1 consumiu o stream via rede emulada, confirmando a cadeia completa: servidor -> s1 -> s2 -> cliente1.

Erros de saída de áudio são esperados — o namespace de rede do Mininet não tem acesso ao dispositivo de áudio da máquina real e não afetam o experimento.

### 3.3 Medições Iniciais (Baseline)

As medições foram coletadas com o script metrics/coletar.py, que executa ping (20 pacotes) e iperf3 (10 segundos) do cliente1 para o servidor, sem nenhuma degradação aplicada.

| Métrica | Valor | Interpretação |
|---|---|---|
| Throughput | 9.52 Mbps | Coerente com o limite de 10 Mbps do link s1-s2 |
| Latência mínima | 10.46 ms | Ida e volta pelo link com 5ms de delay configurado |
| Latência média | 10.97 ms | Estável, sem jitter significativo |
| Latência máxima | 17.15 ms | Pico pontual, dentro do esperado |
| Perda de pacotes | 0% | Rede estável sem degradação |

Esses resultados confirmam que o ambiente está funcional e estável, servindo como referência para comparação com os cenários adversos da Etapa 2.

### 3.4 Automação com Makefile

O arquivo Makefile centraliza os principais comandos do projeto:

- make pox — sobe o controlador POX
- make topologia — sobe a topologia Mininet
- make baseline — coleta métricas sem degradação
- make limpar — remove arquivos de resultados gerados

### 3.5 Observações

Durante a execução foram observados os seguintes avisos, todos sem impacto funcional:

- **sch_htb: quantum of class 50001 is big** — aviso do kernel sobre configuração de QoS; não afeta os experimentos
- **POX com Python 3.12** — versão fora da lista oficialmente suportada; o encaminhamento L2 funciona corretamente; erros de parsing de DNS são consequência desta incompatibilidade e não afetam o plano de dados
- **VLC não executa como root** — contornado com su -c dentro do Mininet
- **decode_slice_header error** — warnings menores do decodificador H.264 nos primeiros frames; resolvido ao regenerar o vídeo com yuv420p

---

## 4. Próximas Etapas

| Etapa | Prazo | Descrição |
|---|---|---|
| Etapa 2 | 20 de maio | Indução de degradação com tc netem e caracterização da QoE sob carga adversa |
| Etapa 3 | 10 de junho | Implementação da lógica de controle SDN para mitigação de degradação |
| Etapa 4 | 24 de junho | Avaliação experimental completa e extensão P4 |

---

## 5. Instruções de Reprodução

**Pré-requisitos:**

- Ubuntu 24.04 (ou compatível)
- Mininet 2.3.0, POX 0.7.0, Open vSwitch 3.3.4
- iperf3, nginx, ffmpeg e VLC instalados via apt

**Geração do conteúdo DASH (executar uma vez):**

```bash
ffmpeg -f lavfi -i testsrc=duration=120:size=1280x720:rate=30 \
       -f lavfi -i sine=frequency=1000:duration=120 \
       -c:v libx264 -b:v 1000k -pix_fmt yuv420p \
       -c:a aac -b:a 128k -y ~/video_teste.mp4

ffmpeg -i ~/video_teste.mp4 \
  -map 0:v -map 0:a -map 0:v -map 0:a -map 0:v -map 0:a \
  -b:v:0 250k  -s:v:0 640x360  -pix_fmt yuv420p \
  -b:v:1 500k  -s:v:1 854x480  -pix_fmt yuv420p \
  -b:v:2 1000k -s:v:2 1280x720 -pix_fmt yuv420p \
  -b:a:0 64k -b:a:1 96k -b:a:2 128k \
  -use_timeline 1 -use_template 1 \
  -adaptation_sets "id=0,streams=v id=1,streams=a" \
  -f dash ~/projeto-qoe/streaming/dash/stream.mpd
```

**Execução:**

```bash
# Terminal 1 — Controlador POX
make pox

# Terminal 2 — Topologia Mininet
make topologia
```

**Dentro do Mininet:**

```
servidor nginx -c /etc/nginx/nginx.conf -g "daemon off;" &
servidor iperf3 -s -D
cliente1 python3 /home/sam/projeto-qoe/metrics/coletar.py baseline 10.0.0.2 10.0.0.1 metricas_baseline.csv
```

**Verificação:** o pingAll deve reportar 0% dropped (6/6 received), o VLC deve reproduzir o stream sem erros de rede, e o CSV de métricas deve ser gerado em results/metricas_baseline.csv.

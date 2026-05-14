# Programabilidade de Infraestruturas de Rede
## Melhoria da QoE em Streaming de Vídeo com Mininet, SDN e P4

**Universidade Federal do Pampa — UNIPAMPA**
Campus Alegrete — Engenharia de Software

**Aluno:** Samuel Anthonny Fossari Monteiro
**Matrícula:** 2410100276
**Relatório de Progresso — Etapa 1**
Maio de 2026

---

## 1. Objetivo Geral

Este projeto tem como objetivo projetar, implementar e avaliar um mecanismo de rede programável para detectar e mitigar a degradação da Qualidade de Experiência (QoE) em fluxos de streaming de vídeo. Para isso, utiliza-se o Mininet como plataforma de emulação de redes, o controlador SDN POX para programação do plano de controle via protocolo OpenFlow, e conteúdo de vídeo segmentado no formato DASH (Dynamic Adaptive Streaming over HTTP), servido por um servidor nginx e consumido por clientes VLC.

O sistema deve ser capaz de observar métricas de rede como throughput, latência e perda de pacotes, e futuramente aplicar ações de controle capazes de melhorar o desempenho percebido pela aplicação. Este relatório descreve a construção do ambiente experimental realizada na Etapa 1 do projeto.

---

## 2. Ambiente Experimental

Todo o ambiente foi construído sobre uma máquina com sistema operacional Ubuntu 24.04 (Zorin OS, baseado em Ubuntu Noble).

### 2.1 Softwares Utilizados

| Software | Versão | Função no Projeto |
|---|---|---|
| Python | 3.12.3 | Linguagem base para scripts e controlador |
| Mininet | 2.3.0 | Emulação da topologia de rede |
| POX Controller | 0.7.0 (gar) | Controlador SDN via OpenFlow 1.0 |
| Open vSwitch | 3.3.4 | Switch OpenFlow virtual |
| iproute2 / tc | 6.1.0 | Indução de degradação de rede (Etapa 2) |
| iperf3 | 3.16 | Medição de throughput |
| nginx | 1.24.0 (Ubuntu) | Servidor HTTP para streaming DASH |
| ffmpeg | 6.1.1 | Geração e segmentação do conteúdo de vídeo |
| VLC | 3.0.20 | Cliente de streaming de vídeo |
| git | 2.54.0 | Controle de versão do projeto |

### 2.2 Escolha do Controlador SDN

O enunciado do projeto sugere o uso do controlador Ryu. No entanto, durante a fase de configuração do ambiente, o Ryu não pôde ser instalado com sucesso devido a incompatibilidades com a versão do Python disponível no sistema (3.12). Como alternativa, optou-se pelo controlador POX, que é igualmente baseado em Python, suporta OpenFlow 1.0 — o mesmo protocolo utilizado pelo Mininet e pelo Open vSwitch — e é amplamente utilizado em contextos acadêmicos.

O POX foi clonado diretamente do repositório oficial e executado sem necessidade de instalação adicional. O módulo `forwarding.l2_learning` foi utilizado para encaminhamento baseado em aprendizado de endereços MAC, funcionalmente equivalente ao que seria utilizado com o Ryu. O controlador é iniciado com:

```bash
cd ~/pox
python3 pox.py forwarding.l2_learning
```

Ao iniciar, o POX escuta conexões OpenFlow na porta 6633. Quando a topologia Mininet é iniciada, os switches se conectam automaticamente ao controlador, conforme confirmado pelas mensagens de log:

```
INFO:core:POX 0.7.0 (gar) is up.
INFO:openflow.of_01:[00-00-00-00-00-01 2] connected
INFO:openflow.of_01:[00-00-00-00-00-02 3] connected
```

### 2.3 Topologia da Rede

A topologia foi definida e implementada no arquivo `topology/topologia.py`, utilizando a API Python do Mininet. A topologia consiste em 1 servidor de vídeo, 2 clientes e 2 switches OpenFlow:

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
- Servidor para s1: 100 Mbps, sem restrição adicional
- s1 para s2: 10 Mbps com 5ms de latência — link de gargalo onde a degradação será induzida na Etapa 2
- s2 para cliente1 e cliente2: 100 Mbps, sem restrição adicional

**Endereços IP:**
- servidor: 10.0.0.1/24
- cliente1: 10.0.0.2/24
- cliente2: 10.0.0.3/24

A topologia é iniciada com:

```bash
sudo python3 topology/topologia.py
```

O resultado do pingAll automático foi `0% dropped (6/6 received)`, confirmando que todos os hosts se comunicam corretamente através dos switches OpenFlow gerenciados pelo POX.

### 2.4 Organização do Repositório

O repositório foi criado no GitHub (github.com/samuel-fossari/projeto-qoe) com a seguinte estrutura:

| Diretório / Arquivo | Descrição |
|---|---|
| `topology/topologia.py` | Script Mininet com a definição da topologia de rede |
| `controller/qoe_controller.py` | Lógica de controle SDN a ser implementada no POX |
| `streaming/nginx.conf` | Configuração do servidor nginx para streaming DASH |
| `streaming/dash/` | Segmentos de vídeo gerados pelo ffmpeg |
| `traffic/degradacao.sh` | Scripts de indução de degradação com tc netem |
| `metrics/coletar.py` | Script Python para coleta automatizada de métricas |
| `metrics/plotar.py` | Script para geração de gráficos a partir dos CSVs |
| `results/` | Dados CSV e gráficos gerados nos experimentos |
| `p4/` | Extensão P4 a ser implementada na Etapa 4 |
| `Makefile` | Automação dos principais comandos do projeto |
| `README.md` | Instruções de reprodução do ambiente |

---

## 3. Implementação do Streaming DASH

Para implementar o streaming de vídeo real conforme exigido pelo enunciado, foram necessárias três etapas: geração do conteúdo de vídeo, segmentação no formato DASH e configuração do servidor nginx.

### 3.1 Geração do Conteúdo de Vídeo

Como não havia um arquivo de vídeo pré-existente disponível, optou-se por gerar um vídeo sintético utilizando o ffmpeg com fontes artificiais. Essa abordagem é completamente reproduzível e sem dependências externas. O vídeo tem duração de 2 minutos, resolução 1280x720, codec H.264 com perfil yuv420p e áudio AAC mono a 128 kbps:

```bash
ffmpeg -f lavfi -i testsrc=duration=120:size=1280x720:rate=30 \
       -f lavfi -i sine=frequency=1000:duration=120 \
       -c:v libx264 -b:v 1000k -pix_fmt yuv420p \
       -c:a aac -b:a 128k -y ~/video_teste.mp4
```

> **Nota:** uma primeira versão foi gerada com o perfil `yuv444p`, causando erros de decodificação no VLC. O problema foi resolvido ao regenerar o vídeo com `yuv420p`.

### 3.2 Segmentação no Formato DASH

O DASH é um protocolo de streaming adaptativo em que o vídeo é dividido em pequenos segmentos e oferecido em múltiplas qualidades. O cliente escolhe automaticamente a qualidade mais adequada com base na largura de banda disponível. O vídeo foi segmentado em três qualidades:

| Qualidade | Resolução | Bitrate de Vídeo | Bitrate de Áudio |
|---|---|---|---|
| Baixa | 640x360 | 250 kbps | 64 kbps |
| Média | 854x480 | 500 kbps | 96 kbps |
| Alta | 1280x720 | 1000 kbps | 128 kbps |

```bash
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

O resultado foi 6 streams (3 de vídeo + 3 de áudio), cada um com 15 a 24 segmentos `.m4s`, além do manifesto `stream.mpd`.

### 3.3 Configuração do Servidor nginx

O nginx foi configurado para servir os segmentos DASH via HTTP na porta 80:

```nginx
server {
    listen 80;
    server_name localhost;
    root /home/sam/projeto-qoe/streaming/dash;
    index stream.mpd;
    location / {
        add_header Access-Control-Allow-Origin *;
        add_header Cache-Control no-cache;
        types {
            application/dash+xml mpd;
            video/mp4 m4s mp4;
        }
    }
}
```

A verificação com `curl -I http://localhost/stream.mpd` retornou `HTTP/1.1 200 OK` com `Content-Type: application/dash+xml`, confirmando o servidor operacional.

### 3.4 Verificação do Streaming dentro do Mininet

Para validar a cadeia completa, o nginx foi iniciado dentro do namespace de rede do host servidor e o VLC foi executado no cliente1:

```
mininet> servidor nginx -c /etc/nginx/nginx.conf -g "daemon off;" &
mininet> cliente1 su -c "vlc http://10.0.0.1/stream.mpd --play-and-exit" sam
```

O VLC reproduziu o stream com sucesso, confirmando a cadeia completa: servidor -> s1 -> s2 -> cliente1.

---

## 4. Coleta de Métricas e Medições Iniciais

### 4.1 Script de Coleta

Foi desenvolvido o script `metrics/coletar.py`, que automatiza a execução de ping (20 pacotes, para latência e perda) e iperf3 (10 segundos, para throughput), salvando os resultados em CSV. O script é invocado da seguinte forma:

```
servidor iperf3 -s -D
cliente1 python3 /home/sam/projeto-qoe/metrics/coletar.py baseline 10.0.0.2 10.0.0.1 metricas_baseline.csv
```

### 4.2 Resultados do Baseline

| Métrica | Valor Obtido | Interpretação |
|---|---|---|
| Throughput | 9.52 Mbps | Coerente com o limite de 10 Mbps do link s1-s2 |
| Latência mínima | 10.46 ms | RTT com 5ms de delay (ida e volta = ~10ms) |
| Latência média | 10.97 ms | Estável, sem jitter significativo |
| Latência máxima | 17.15 ms | Pico pontual dentro do esperado |
| Perda de pacotes | 0% | Rede estável, sem degradação |

Os dados foram salvos em `results/metricas_baseline.csv`:

```
timestamp,cenario,origem,destino,throughput_mbps,latencia_min_ms,latencia_media_ms,latencia_max_ms,perda_pct
2026-05-13T22:48:18,baseline,10.0.0.2,10.0.0.1,9.52,10.456,10.973,17.15,0.0
```

---

## 5. Automação com Makefile

Para facilitar a reprodução do ambiente, foi criado um Makefile com os principais comandos do projeto:

```makefile
.PHONY: all topologia pox baseline limpar

pox:
	cd ~/pox && python3 pox.py forwarding.l2_learning

topologia:
	sudo python3 topology/topologia.py

baseline:
	python3 metrics/coletar.py baseline 10.0.0.2 10.0.0.1 metricas_baseline.csv

limpar:
	rm -f results/*.csv results/*.png

help:
	@echo "Comandos disponíveis:"
	@echo "  make pox        — sobe o controlador POX"
	@echo "  make topologia  — sobe a topologia Mininet"
	@echo "  make baseline   — coleta métricas sem degradação"
	@echo "  make limpar     — remove arquivos de resultados gerados"
```

---

## 6. Observações Técnicas

- **sch_htb: quantum of class 50001 is big** — aviso do kernel ao configurar TCLink no Mininet. Não afeta os experimentos.
- **POX com Python 3.12** — versão fora da lista suportada oficialmente. Erros de parsing de DNS aparecem no log, mas o encaminhamento L2 funciona corretamente para tráfego HTTP e ICMP.
- **VLC não executa como root** — contornado com `su -c "vlc ..." sam` dentro do Mininet.
- **Formato yuv444p** — primeira versão do vídeo causou erros no VLC. Corrigido ao regenerar com `yuv420p`.

---

## 7. Próximas Etapas

| Etapa | Prazo | Descrição |
|---|---|---|
| Etapa 2 | 20 de maio de 2026 | Indução de degradação com tc netem e caracterização da QoE sob carga adversa |
| Etapa 3 | 10 de junho de 2026 | Implementação da lógica de detecção e mitigação no controlador POX |
| Etapa 4 | 24 de junho de 2026 | Avaliação experimental completa e extensão com P4 |

---

## 8. Instruções de Reprodução

**Pré-requisitos:**
- Ubuntu 24.04 (ou compatível)
- Mininet 2.3.0, POX clonado em `~/pox`
- `sudo apt install -y iperf3 nginx ffmpeg vlc`

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
# Terminal 1
make pox

# Terminal 2
make topologia
```

**Dentro do Mininet:**

```
servidor nginx -c /etc/nginx/nginx.conf -g "daemon off;" &
servidor iperf3 -s -D
cliente1 python3 /home/sam/projeto-qoe/metrics/coletar.py baseline 10.0.0.2 10.0.0.1 metricas_baseline.csv
```

**Verificação esperada:** pingAll com 0% dropped, VLC reproduzindo o stream sem erros de rede, e CSV gerado em `results/metricas_baseline.csv` com throughput próximo de 9-10 Mbps, latência média em torno de 11ms e 0% de perda.

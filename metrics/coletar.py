#!/usr/bin/env python3
"""
Coleta de métricas de rede no ambiente Mininet.
Mede throughput (iperf3), latência e perda (ping).
Salva resultados em results/metricas_baseline.csv
"""

import subprocess
import csv
import os
import sys
import json
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)


def coletar_ping(origem, destino, count=20):
    """Executa ping e retorna latência média e perda."""
    cmd = f'ping -c {count} -i 0.2 {destino}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout

    perda = 100.0
    latencia_media = 0.0
    latencia_min = 0.0
    latencia_max = 0.0

    for line in output.splitlines():
        if 'packet loss' in line:
            parts = line.split(',')
            for p in parts:
                if 'packet loss' in p:
                    perda = float(p.strip().split('%')[0])
        if 'rtt min/avg/max' in line or 'round-trip min/avg/max' in line:
            stats = line.split('=')[1].strip().split('/')
            latencia_min = float(stats[0])
            latencia_media = float(stats[1])
            latencia_max = float(stats[2].split()[0])

    return {
        'latencia_min_ms': latencia_min,
        'latencia_media_ms': latencia_media,
        'latencia_max_ms': latencia_max,
        'perda_pct': perda
    }


def coletar_iperf3(origem, destino, duracao=10):
    """Executa iperf3 e retorna throughput em Mbps."""
    cmd = f'iperf3 -c {destino} -t {duracao} -J'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    throughput_mbps = 0.0
    try:
        data = json.loads(result.stdout)
        bits = data['end']['sum_received']['bits_per_second']
        throughput_mbps = bits / 1_000_000
    except Exception as e:
        print(f'Erro ao parsear iperf3: {e}')

    return {'throughput_mbps': round(throughput_mbps, 2)}


def salvar_csv(metricas, nome_arquivo):
    caminho = os.path.join(RESULTS_DIR, nome_arquivo)
    campos = ['timestamp', 'cenario', 'origem', 'destino',
              'throughput_mbps', 'latencia_min_ms', 'latencia_media_ms',
              'latencia_max_ms', 'perda_pct']

    escrever_header = not os.path.exists(caminho)
    with open(caminho, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        if escrever_header:
            writer.writeheader()
        writer.writerow(metricas)

    print(f'Métricas salvas em {caminho}')


def coletar(cenario, origem, destino, arquivo_csv):
    print(f'\n=== Coletando métricas: {cenario} ===')
    print(f'Origem: {origem} -> Destino: {destino}')

    print('Executando ping...')
    ping = coletar_ping(origem, destino)
    print(f'  Latência média: {ping["latencia_media_ms"]} ms')
    print(f'  Perda: {ping["perda_pct"]}%')

    print('Executando iperf3...')
    iperf = coletar_iperf3(origem, destino)
    print(f'  Throughput: {iperf["throughput_mbps"]} Mbps')

    metricas = {
        'timestamp': datetime.now().isoformat(),
        'cenario': cenario,
        'origem': origem,
        'destino': destino,
        **ping,
        **iperf
    }

    salvar_csv(metricas, arquivo_csv)
    return metricas


if __name__ == '__main__':
    cenario = sys.argv[1] if len(sys.argv) > 1 else 'baseline'
    origem = sys.argv[2] if len(sys.argv) > 2 else '10.0.0.2'
    destino = sys.argv[3] if len(sys.argv) > 3 else '10.0.0.1'
    arquivo = sys.argv[4] if len(sys.argv) > 4 else 'metricas_baseline.csv'

    coletar(cenario, origem, destino, arquivo)
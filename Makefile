.PHONY: all topologia pox baseline limpar

# Sobe o controlador POX (rodar em terminal separado)
pox:
	cd ~/pox && python3 pox.py forwarding.l2_learning

# Sobe a topologia Mininet
topologia:
	sudo python3 topology/topologia.py

# Coleta métricas baseline (rodar de dentro do Mininet no host cliente1)
baseline:
	python3 metrics/coletar.py baseline 10.0.0.2 10.0.0.1 metricas_baseline.csv

# Limpa resultados gerados
limpar:
	rm -f results/*.csv results/*.png

# Mostra ajuda
help:
	@echo "Comandos disponíveis:"
	@echo "  make pox        — sobe o controlador POX"
	@echo "  make topologia  — sobe a topologia Mininet"
	@echo "  make baseline   — coleta métricas sem degradação"
	@echo "  make limpar     — remove arquivos de resultados gerados"
#!/usr/bin/env python3
"""
Topologia para o projeto QoE — Programabilidade de Redes
1 servidor de vídeo, 2 clientes, 2 switches OpenFlow
Controlador: POX (OpenFlow 1.0)
"""

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI


def criar_topologia():
    net = Mininet(
        switch=OVSSwitch,
        controller=RemoteController,
        link=TCLink,
        autoSetMacs=True
    )

    info("*** Criando controlador remoto (POX)\n")
    c0 = net.addController(
        "c0",
        controller=RemoteController,
        ip="127.0.0.1",
        port=6633
    )

    info("*** Criando switches\n")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")

    info("*** Criando hosts\n")
    servidor = net.addHost("servidor", ip="10.0.0.1/24")
    cliente1 = net.addHost("cliente1", ip="10.0.0.2/24")
    cliente2 = net.addHost("cliente2", ip="10.0.0.3/24")

    info("*** Criando links\n")
    net.addLink(servidor, s1, bw=100)
    net.addLink(s1, s2, bw=10, delay="5ms")
    net.addLink(s2, cliente1, bw=100)
    net.addLink(s2, cliente2, bw=100)

    info("*** Iniciando rede\n")
    net.start()

    info("*** Testando conectividade básica\n")
    net.pingAll()

    info("*** Abrindo CLI (digite 'exit' para encerrar)\n")
    CLI(net)

    info("*** Encerrando rede\n")
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    criar_topologia()
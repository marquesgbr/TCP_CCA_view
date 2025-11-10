#!/usr/bin/python3
# -*- coding: utf-8 -*-

from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def create_dumbbell_topology():
    """Cria uma topologia roteada (sem switches) com um gargalo central."""
    
    net = Mininet(topo=None, link=TCLink)

    info('*** Adicionando roteadores (como Nodes)\n')
    r1 = net.addHost('r1', cls=Node, ip=None) 
    r2 = net.addHost('r2', cls=Node, ip=None)

    info('*** Adicionando hosts\n')
    # Cada host está em sua própria sub-rede, com o roteador como gateway
    # Hosts Transmissores
    h1 = net.addHost('h1', ip='10.0.1.1/24', defaultRoute='via 10.0.1.254')
    h2 = net.addHost('h2', ip='10.0.2.1/24', defaultRoute='via 10.0.2.254')

    # Hosts Receptores
    h3 = net.addHost('h3', ip='10.0.3.1/24', defaultRoute='via 10.0.3.254')
    h4 = net.addHost('h4', ip='10.0.4.1/24', defaultRoute='via 10.0.4.254')

    info('*** Adicionando links\n')
    # Links dos hosts para os roteadores (10Mbps)
    net.addLink(h1, r1, intfName2='r1-eth1', bw=10)
    net.addLink(h2, r1, intfName2='r1-eth2', bw=10)
    net.addLink(h3, r2, intfName2='r2-eth1', bw=10)
    net.addLink(h4, r2, intfName2='r2-eth2', bw=10)
    
    # Link do GARGALO R1-R2 (10 Mbps)
    net.addLink(r1, r2, intfName1='r1-eth3', intfName2='r2-eth3', bw=10)

    info('*** Iniciando a rede\n')
    net.build()

    info('*** Configurando IPs dos roteadores\n')
    # Lado R1
    r1.cmd('ifconfig r1-eth1 10.0.1.254/24') # Definindo Gateway para h1
    r1.cmd('ifconfig r1-eth2 10.0.2.254/24') # Definindo Gateway para h2
    r1.cmd('ifconfig r1-eth3 10.10.10.1/24') # Link gargalo
    
    # Lado R2
    r2.cmd('ifconfig r2-eth1 10.0.3.254/24') # Definindo Gateway para h3
    r2.cmd('ifconfig r2-eth2 10.0.4.254/24') # Definindo Gateway para h4
    r2.cmd('ifconfig r2-eth3 10.10.10.2/24') # Link gargalo

    info('*** Configurando roteamento e IP forward\n')
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')
    
    # R1 precisa saber como chegar nas redes de h3 e h4
    r1.cmd('route add -net 10.0.3.0/24 gw 10.10.10.2')
    r1.cmd('route add -net 10.0.4.0/24 gw 10.10.10.2')
    
    # R2 precisa saber como chegar nas redes de h1 e h2
    r2.cmd('route add -net 10.0.1.0/24 gw 10.10.10.1')
    r2.cmd('route add -net 10.0.2.0/24 gw 10.10.10.1')
    
    info('*** Rede pronta. Iniciando CLI...\n')
    CLI(net)

    info('*** Parando a rede\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_dumbbell_topology()
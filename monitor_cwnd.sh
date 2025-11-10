#!/bin/bash
# Script para monitorar a CWND de um host Mininet

# --- Configs ---
CCA_NOME="bbr"    # Nome do Congestion Control Algorithm usado no host
HOST_NS="h1"       # Host que vamos monitorar
PORTA=5001         # Porta de destino que o h1 vai usar
OUTPUT_FILE="cwnd_h1_${CCA_NOME}.txt"
# ---------------------

echo "Iniciando monitoramento de CWND para $HOST_NS ($CCA_NOME) na porta $PORTA..."
echo "time_ms,cwnd" > $OUTPUT_FILE

START_TIME=$(date +%s%N)

# O Mininet cria 'namespaces' de rede. Este comando executa o 'ss'
# dentro do namespace (rede isolada) do host h1.
while true; do
    # O comando 'ss' (socket statistics) nos dá informações sobre as conexões
    # -i: info interna do socket, -t: TCP
    CWND_DATA=$(sudo ip netns exec $HOST_NS ss -i -t 'dport = :'$PORTA | grep -o "cwnd:[0-9]*")
    
    if [ ! -z "$CWND_DATA" ]; then
        NOW=$(date +%s%N)
        # Calcula o tempo decorrido em milissegundos
        ELAPSED_MS=$((($NOW - $START_TIME) / 1000000))
        # Extrai apenas o número do "cwnd:10"
        CWND=$(echo $CWND_DATA | cut -d':' -f2)
        
        echo "$ELAPSED_MS,$CWND" >> $OUTPUT_FILE
    fi
    # Coleta dados a cada 100ms
    sleep 0.1
done

import matplotlib.pyplot as plt
import csv
import os

def plotar_vazao(cca_name):
    """Lê arquivos de vazão do iperf (formato -y C) e plota."""
    
    # Nomes dos arquivos de throughput para h1 e h2
    arquivos = [f'throughput_h1_{cca_name}.txt', f'throughput_h2_{cca_name}.txt']
    
    plt.figure(figsize=(12, 7))
    
    for i, arquivo in enumerate(arquivos):
        host_name = f'h{i+1}'
        tempos = []
        vazoes = [] # em Mbits/s
        
        try:
            with open(arquivo, 'r') as f:
                for line in f:
                    # Formato iperf -y C (CSV): 
                    # timestamp,ip1,port1,ip2,port2,id,interval,bytes,bits_per_second
                    parts = line.strip().split(',')
                    
                    if len(parts) == 9:
                        try:
                            intervalo_str = parts[6]
                            vazao_bits_s = float(parts[8])
                            
                            intervalo_parts = intervalo_str.split('-')
                            tempo_inicio = float(intervalo_parts[0])
                            tempo_fim = float(intervalo_parts[1])

                            # Regra para pular linhas de sumário (ex: "0.0-88.1" ou "60.0-88.1")
                            # Queremos somente os relatórios de ~1 segundo de intervalo.
                            if (tempo_fim - tempo_inicio) > 2.0:
                                continue
                                
                            tempos.append(tempo_fim)
                            vazoes.append(vazao_bits_s / 1_000_000) # Converter para Mbits/s
                        
                        except (ValueError, IndexError):
                            # Pula linhas mal formatadas ou que não são de dados
                            continue
                            
        except FileNotFoundError:
            print(f"Arquivo não encontrado, pulando: {arquivo}")
            continue

        plt.plot(tempos, vazoes, label=f'Vazão {host_name} ({cca_name})', alpha=0.8)

    plt.title(f'Vazão (Throughput) vs. Tempo - CCA: {cca_name.upper()}', fontsize=16)
    plt.xlabel('Tempo (segundos)', fontsize=12)
    plt.ylabel('Vazão (Mbits/s)', fontsize=12)
    # Define o limite do eixo Y para ser um pouco acima de 10 Mbps
    plt.ylim(0, 12) 
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'vazao_{cca_name}.png')
    plt.close() # Fecha a figura para economizar memória

def plotar_cwnd(cca_name):
    """Lê o arquivo de CWND e plota."""
    arquivo = f'cwnd_h1_{cca_name}.txt'
    
    tempos_ms = []
    cwnds = []
    
    try:
        with open(arquivo, 'r') as f:
            reader = csv.reader(f)
            next(reader) # Pula o cabeçalho "time_ms,cwnd"
            for row in reader:
                if len(row) == 2:
                    try:
                        tempos_ms.append(float(row[0]))
                        cwnds.append(int(row[1]))
                    except ValueError:
                        continue # Pula linhas mal formatadas
                        
    except FileNotFoundError:
        print(f"Arquivo não encontrado, pulando: {arquivo}")
        return
    except StopIteration:
        print(f"Arquivo vazio ou sem cabeçalho: {arquivo}")
        return

    if not tempos_ms:
        print(f"Nenhum dado de CWND encontrado para {cca_name}")
        return

    # Converter tempo de ms para segundos
    tempos_s = [t / 1000.0 for t in tempos_ms]

    plt.figure(figsize=(12, 7))
    plt.plot(tempos_s, cwnds, label=f'CWND h1 ({cca_name})')
    plt.title(f'Janela de Congestionamento (CWND) vs. Tempo - CCA: {cca_name.upper()}', fontsize=16)
    plt.xlabel('Tempo (segundos)', fontsize=12)
    plt.ylabel('Janela de Congestionamento (segmentos/MSS)', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'cwnd_{cca_name}.png')
    plt.close() # Fecha a figura

# --- Execução Principal ---

algoritmos = ['reno', 'cubic', 'bbr']
print("Iniciando geração de gráficos...")

for cca in algoritmos:
    print(f"Processando {cca}...")
    plotar_vazao(cca)
    plotar_cwnd(cca)

print("\nGráficos gerados com sucesso!")
print("Arquivos criados na sua pasta:")
for cca in algoritmos:
    print(f" - vazao_{cca}.png")
    print(f" - cwnd_{cca}.png")
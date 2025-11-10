# Visualizador de Controle de Congestionamento TCP

Este projeto utiliza o Mininet para simular uma topologia de rede "dumbbell" (haltere) roteada e comparar o comportamento de três algoritmos de controle de congestionamento (CCAs) do TCP: **Reno**, **CUBIC** e **BBR**.

O objetivo é coletar e plotar dados de **Vazão (Throughput)** e **Janela de Congestionamento (CWND)** de dois fluxos de dados competindo por um único link de gargalo de 10 Mbits/sec.

## 🚀 Configuração do Ambiente (Windows 11 + WSL2)

Este guia foi testado no **Windows 11** com **WSL2 (Ubuntu 24.04)**. A configuração não é tão simples e envolve algumas pecurialidades do WSL.

### 1. Instalação do WSL2 + Ubuntu

1.  Abra o **PowerShell como Administrador** no Windows.
2.  Execute `wsl --install` para instalar o WSL2.
3.  Instale o **Ubuntu 24.04 LTS** (ou a versão de sua preferência). No meu caso foi instalado pela Microsoft Store
4.  Abra o Ubuntu e crie seu usuário e senha.

### 2. (OBS.:) Problema de Instalação pela Microsoft Store - Corrigindo o Local de Instalação
Aqui tem uma descrição de um problema chave enfrentado durante a configuração do ambiente com uma solução simples mas que pode passar despercebido. Pode pular se o seu ubuntu não foi instalado pela Microsoft Store
* **Problema:** Se o Windows estiver configurado para instalar novos aplicativos em um drive que não seja o `C:` (ex: `D:`), o WSL falhará ao iniciar com erros de "arquivo criptografado" (`0x80071772`).
* **Solução:**
    1.  Vá em "Configurações" > "Sistema" > "Armazenamento".
    2.  Vá em "Configurações avançadas de armazenamento" > "Alterar onde o novo conteúdo é salvo".
    3.  Mude a opção **"Novos aplicativos serão salvos em:"** de volta para o seu drive **`Windows (C:)`**.
    4.  Desinstale e reinstale o Ubuntu.

### 3. Instalação das Dependências (Ubuntu)

Dentro do seu terminal do Ubuntu, instale todas as ferramentas necessárias:

```bash
# Atualiza os repositórios
sudo apt-get update

# Instala o Mininet, iperf (para tráfego) e o pip (para pacotes Python)
sudo apt-get install mininet iperf python3-pip

# Instala o matplotlib (para gerar os gráficos)
sudo pip3 install matplotlib

# Instala o módulo de teste gráfico (para verificar o WSLg)
sudo apt-get install x11-apps
```

### 4\. Verificando o WSLg (Gráficos)

O Windows 11 usa o **WSLg** nativamente. Para testar:

1.  Feche e reabra seu terminal do Ubuntu.
2.  Digite `xeyes`.
3.  Uma janela com "olhos" deve aparecer. Se sim, está funcionando.

### 5\. Corrigindo o Gargalo do Mininet no WSL2 (Kernel)

Este é o passo mais crítico. Por padrão, o Mininet não conseguirá limitar a banda (o `bw=10`) porque o kernel do WSL não vem com os módulos de tráfego.

1.  **No PowerShell (Admin):** Force uma atualização do kernel do WSL.

    ```powershell
    wsl --update
    wsl --shutdown 
    ```
    
2.  **No terminal do Ubuntu:** Reabra o Ubuntu e carregue manualmente os módulos `htb` (para banda) e `bbr` (para o CCA).
    
    ```bash
    # Carrega o módulo para controle de banda (TCLink)
    sudo modprobe sch_htb

    # Carrega o módulo para o CCA BBR
    sudo modprobe tcp_bbr
    ```
    (Estes comandos devem rodar em silêncio, sem erros).

### 6\. (Opcional) Permissão do VS Code

Se você usa o VS Code para editar os arquivos de dentro do WSL (via `\\wsl$\...`), ele pode bloquear o salvamento.

  * **Correção:** Em `Configurações` (`Ctrl + ,`), procure por `security.allowedUNCHosts` e adicione um item com o valor `wsl$`.

-----

## 🏁 Executando o Experimento (Passo a Passo)

Para coletar os dados, você precisará de **dois terminais do Ubuntu** abertos lado a lado.

### Rodada 1: Coletando Dados do "Reno"

**Terminal 1 (Principal):**

1.  Limpe qualquer sessão anterior do Mininet:
    ```bash
    sudo mn -c
    ```
2.  Inicie a topologia (V9) que você criou:
    ```bash
    sudo python3 dumbbell_topo.py
    ```
3.  Você estará no prompt `mininet>`. Configure o CCA para **Reno** e inicie os servidores `iperf`:
    ```bash
    mininet> h1 sysctl -w net.ipv4.tcp_congestion_control=reno
    mininet> h2 sysctl -w net.ipv4.tcp_congestion_control=reno
    mininet> h3 iperf -s -p 5001 &
    mininet> h4 iperf -s -p 5002 &
    ```

**Terminal 2 (Monitor):**

1.  **(Apenas na primeira vez)** Edite o `monitor_cwnd.sh` e garanta que a variável esteja correta:
    `CCA_NOME="reno"`
2.  **(Toda vez que o Mininet reiniciar)** O `h1` é um novo processo. Precisamos "linkar" seu namespace para o script de monitoramento funcionar:
    ```bash
    # Encontra o ID do processo do h1
    PID_H1=$(ps aux | grep 'mininet:h1' | grep -v 'grep' | awk '{print $2}')

    # Cria o "atalho" que o comando 'ip netns' precisa
    sudo mkdir -p /var/run/netns
    sudo ln -sf /proc/$PID_H1/ns/net /var/run/netns/h1
    ```
3.  Inicie o monitor. Ele ficará parado, esperando:
    ```bash
    ./monitor_cwnd.sh
    ```

**Terminal 1 (Principal):**

1.  Inicie os dois fluxos de tráfego por 60 segundos (os IPs `10.0.3.1` e `10.0.4.1` são de `h3` e `h4`):
    ```bash
    mininet> h1 iperf -c 10.0.3.1 -p 5001 -t 60 -i 1 -y C > throughput_h1_reno.txt &
    mininet> h2 iperf -c 10.0.4.1 -p 5002 -t 60 -i 1 -y C > throughput_h2_reno.txt &
    ```
2.  Aguarde cerca de 65 segundos (para garantir que ambos os fluxos de 60s terminaram).

**Terminal 2 (Monitor):**

1.  Pare o script de monitoramento pressionando `Ctrl + C`.

### Rodada 2 e 3: Coletando para `cubic` e `bbr`

Repita *exatamente* o processo acima, mas com estas mudanças:

1.  **Saia** do Mininet no Terminal 1 (`exit`) e limpe (`sudo mn -c`) antes de reiniciar.
2.  **No Terminal 2**, edite o `monitor_cwnd.sh` para `CCA_NOME="cubic"` (ou `"bbr"`).
3.  **No Terminal 1**, use os comandos `sysctl` para `cubic` (ou `bbr`).
4.  **No Terminal 1**, salve os arquivos de saída com o nome correto (ex: `..._cubic.txt` ou `..._bbr.txt`).
5.  **No Terminal 2**, lembre-se de **refazer o link do PID** (Passo 2 do Monitor) toda vez que o Mininet reiniciar\!

-----

## 📊 Gerando os Gráficos

Após coletar todos os 9 arquivos de dados (`.txt`), você pode gerar os 6 gráficos (`.png`):

1.  No seu terminal do Ubuntu, execute o script de plotagem:
    ```bash
    python3 plotar.py
    ```
2.  Para ver os arquivos `.png` gerados, abra o Explorador de Arquivos do Windows na sua pasta atual:
    ```bash
    explorer.exe .
    ```

## 📁 Estrutura dos Arquivos

  * `dumbbell_topo.py`: O script Python (V9) que cria a topologia de rede roteada no Mininet.
  * `monitor_cwnd.sh`: O script Bash usado para monitorar a janela de congestionamento (CWND) do `h1`.
  * `plotar.py`: O script Python (usando Matplotlib) que lê todos os arquivos `.txt` e gera os 6 gráficos `.png`.
  * `out/txt/*.txt`: Arquivos de dados brutos coletados dos experimentos (`throughput_...` e `cwnd_...`).
  * `out/png/*.png`: Os gráficos de resultados finais.

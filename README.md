# gRPC e Serviço de Nomes (ASR11)

Implementação em Python com gRPC, baseada no exemplo
([gRPC-SimpleNamingService](https://github.com/professorfabio/gRPC-SimpleNamingService)), de:

- **Serviço de Nomes** (`servidor_nomes.py`) com `Bind`, `Lookup`, `Unbind` e `Rebind`.
- **Dois serviços de aplicação**, cada um em seu próprio processo/máquina:
  - `servidor_biblioteca.py` — `CadastrarLivro`, `ListarLivros`, `Emprestar`, `Devolver`
  - `servidor_dicionario.py` — `Buscar`, `Adicionar`, `ListarPalavras` (termos de Sistemas Distribuídos)
- **Cliente** (`cliente.py`) que descobre o endereço dos serviços via `Lookup` e faz requisições a eles.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `protos/nomes.proto` | Interface do Serviço de Nomes (mesmas mensagens do exemplo do professor) |
| `protos/biblioteca.proto` | Interface do serviço Biblioteca |
| `protos/dicionario.proto` | Interface do serviço Dicionário |
| `const.py` | Endereço do Serviço de Nomes (o único endereço fixo do sistema) |
| `servidor_nomes.py` | Servidor do Serviço de Nomes (tabela nome → ip/porta em memória) |
| `registro.py` | Funções usadas pelos servidores para fazer bind/rebind/unbind |
| `servidor_biblioteca.py`, `servidor_dicionario.py` | Servidores de aplicação |
| `cliente.py` | Cliente: faz lookup e usa os dois serviços |
| `testNS.py` | Testa as 4 operações do Serviço de Nomes |
| `gerar_codigo.sh` | Gera os stubs Python a partir dos `.proto` |

## Como funciona

1. O Serviço de Nomes sobe numa porta conhecida (`const.NS_PORT`, padrão `5678`).
2. Cada servidor de aplicação sobe numa **porta dinâmica**: ele pede a porta `0`, o sistema operacional escolhe uma
   porta livre e o gRPC devolve qual foi (`porta = server.add_insecure_port('[::]:0')`).
   Em seguida faz **Bind** do seu nome (`Biblioteca` ou `Dicionario`) com seu IP e essa porta.
   Se o nome já existir (ex.: o servidor foi reiniciado em outra máquina/porta), faz **Rebind** para atualizar o endereço.
3. O cliente só conhece o endereço do Serviço de Nomes. Ele faz **Lookup** de cada nome, recebe IP e porta e se conecta ao servidor.
   Ninguém precisa saber de antemão em que porta os servidores estão: essa é a função do Serviço de Nomes.
4. Ao ser desligado (Ctrl+C ou `kill`), o servidor faz **Unbind** do seu nome
   (só se o nome ainda apontar para ele, para não apagar o registro de um servidor que fez rebind depois).

Diferenças em relação ao exemplo do professor:
- `Bind` de um nome já registrado retorna `NOK` (no exemplo, criava um registro duplicado).
- `Rebind` de um nome inexistente cria o registro (no exemplo, gerava erro).
- A tabela de nomes é protegida por um lock, pois o servidor atende requisições em várias threads.

### Armazenamento dos registros

O Serviço de Nomes **não salva nada em disco**: a tabela nome → ip/porta fica só na memória do processo
(um dicionário Python), como no exemplo do professor. Isso significa que:
- se o Serviço de Nomes for reiniciado, todos os registros são perdidos;
- os servidores de aplicação que já estavam rodando precisam ser reiniciados para fazer `Bind` de novo.

Para esta tarefa isso é suficiente, porque os servidores sempre se registram ao iniciar.
Persistir em disco (arquivo ou banco) teria um efeito colateral: se um servidor caísse sem fazer `Unbind`,
o registro dele continuaria apontando para um endereço que não responde mais.

## Instalação

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./gerar_codigo.sh
```

## Execução na mesma máquina

Em terminais separados (com o venv ativado):

```sh
python servidor_nomes.py
python servidor_biblioteca.py
python servidor_dicionario.py
python cliente.py
```

Para testar só o Serviço de Nomes: `python testNS.py`.

## Execução em máquinas diferentes (mesma rede Wi-Fi / LAN)

Use dois ou mais computadores conectados **na mesma rede Wi-Fi** (ou cabo).

**1. Prepare cada máquina:** copie o projeto (ex.: `git clone`) e rode os passos de [Instalação](#instalação).

**2. Descubra o IP de cada máquina na rede local:**

| Sistema | Comando |
|---|---|
| macOS | `ipconfig getifaddr en0` |
| Linux | `hostname -I` |
| Windows | `ipconfig` (campo "Endereço IPv4") |

O IP costuma ser algo como `192.168.x.x` ou `10.x.x.x`. Não use `127.0.0.1` nem `localhost`.

**3. Teste se uma máquina enxerga a outra:** `ping <IP da outra máquina>`.

**4. Rode os processos.** Exemplo com duas máquinas, A = `192.168.0.10` e B = `192.168.0.11`:

```sh
# Máquina A
python servidor_nomes.py
python servidor_dicionario.py --ip 192.168.0.10

# Máquina B
python servidor_biblioteca.py --ip 192.168.0.11 --ns 192.168.0.10:5678
python cliente.py --ns 192.168.0.10:5678
```

No `lookup`, o cliente deve mostrar `Biblioteca -> 192.168.0.11:...` e `Dicionario -> 192.168.0.10:...`,
ou seja, cada serviço em uma máquina diferente.

**Problemas comuns:**
- **Esquecer o `--ip`:** o servidor se registra como `localhost` e o cliente da outra máquina tenta conectar em si mesmo.
- **Firewall:** no macOS, aceite "Permitir conexões de entrada" para o Python quando aparecer o aviso;
  no Windows, permita o Python no Firewall do Windows (rede privada).
- **Wi-Fi da faculdade / redes públicas:** costumam bloquear conexões entre dispositivos (isolamento de clientes).
  Se o `ping` não responder, use o roteador de casa ou o hotspot do celular.

Com 4 máquinas, cada processo pode ficar em uma. O IP do Serviço de Nomes também pode ser colocado em
`NS_IPADDR` no `const.py`, dispensando o `--ns`:

```sh
# Máquina A (192.168.0.10)
python servidor_nomes.py

# Máquina B (192.168.0.11)
python servidor_biblioteca.py --ip 192.168.0.11 --ns 192.168.0.10:5678

# Máquina C (192.168.0.12)
python servidor_dicionario.py --ip 192.168.0.12 --ns 192.168.0.10:5678

# Máquina D (cliente)
python cliente.py --ns 192.168.0.10:5678
```

`--ip` é o IP da própria máquina do servidor: é o endereço registrado no Serviço de Nomes e usado pelo cliente.

Se houver firewall entre as máquinas (ex.: security group da AWS), uma porta escolhida pelo sistema pode estar bloqueada.
Nesse caso, fixe a porta com `--porta` e libere-a junto com a 5678 do Serviço de Nomes:

```sh
python servidor_biblioteca.py --ip 192.168.0.11 --porta 6000 --ns 192.168.0.10:5678
```

## Exemplo de saída

`python testNS.py`:
```
  Bind 10.0.0.1:6000          -> OK
  Lookup  -> ip='10.0.0.1' porta='6000'
  Bind repetido               -> NOK
  Rebind 10.0.0.2:7000        -> OK
  Lookup  -> ip='10.0.0.2' porta='7000'
  Unbind                      -> OK
  Lookup  -> ip='' porta=''
  Unbind de nome inexistente  -> NOK
```

`python cliente.py`:
```
== Biblioteca ==
lookup('Biblioteca') -> localhost:49666
  CadastrarLivro -> #4 O Hobbit
  Emprestar #1   -> 'Sistemas Distribuídos: Princípios e Paradigmas' emprestado
  Emprestar #1   -> 'Sistemas Distribuídos: Princípios e Paradigmas' já está emprestado
  Emprestar #99  -> livro não existe
  ListarLivros:
    #1 Sistemas Distribuídos: Princípios e Paradigmas (Tanenbaum e Van Steen) - emprestado
    #2 Sistemas Distribuídos: Conceitos e Projeto (Coulouris et al.) - disponível
    #3 Dom Casmurro (Machado de Assis) - disponível
    #4 O Hobbit (J. R. R. Tolkien) - disponível
  Devolver #1    -> 'Sistemas Distribuídos: Princípios e Paradigmas' devolvido
== Dicionário ==
lookup('Dicionario') -> localhost:49664
  Buscar 'gRPC' -> Framework de RPC do Google que usa HTTP/2 e Protocol Buffers.
  Buscar 'lookup' -> (não encontrada)
  Adicionar 'lookup' -> 'lookup' adicionada
  Buscar 'lookup' -> Operação do serviço de nomes que devolve o endereço de um nome.
  ListarPalavras -> grpc, lookup, middleware, rpc, stub
```

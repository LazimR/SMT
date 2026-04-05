# Atividade 3 - Sistema Cliente/Servidor em Camadas

## Estrutura

- `frontend/app.py`: Cliente Tkinter (simulador de sensor).
- `backend/app.py`: Servidor Flask com regras de negócio e idempotência.
- `backend/database.py`: Inicialização e acesso ao SQLite.
- `backend/rules.py`: Processamento lógico de status.
- `backend/storage.py`: Salvamento em disco de JSON e PNG com OpenCV.
- `backend/data/leituras.db`: Banco SQLite (criado automaticamente).
- `backend/storage/leituras/`: Arquivos de cada leitura (JSON e PNG).

## Requisitos

- Python 3
- Dependências em `requirements.txt`

## Instalação

No diretório `SMT`:

```bash
pip install -r requirements.txt
```

## Execução

1. Inicie o servidor em modo de produção:

```bash
python backend/run_server.py
```

2. Inicie o cliente (em outro terminal):

```bash
python frontend/app.py
```

3. No cliente Tkinter, ajuste o campo URL para o IP/host do servidor no formato:

```text
http://IP_DO_SERVIDOR:5000/leitura
```

## Regras de negócio implementadas

- Temperatura `> 10`: `Alerta`
- Temperatura `> 15`: `Crítico`
- Caso contrário: `Normal`

## Idempotência

- Cada envio usa `id` (UUID) como chave primária da tabela `leituras`.
- Se o mesmo UUID for reenviado, o servidor retorna os dados já processados e não duplica no banco.

## Banco SQLite

Tabela `leituras`:

- `id` (TEXT, chave primária)
- `sensor_id` (TEXT)
- `temperatura` (REAL)
- `status_logico` (TEXT)
- `timestamp` (TEXT)

## Fluxo implementado

1. Cliente gera leitura e envia JSON com UUID.
2. Servidor valida UUID e payload.
3. Servidor aplica regra de negócio de status.
4. Servidor salva arquivo JSON e imagem PNG da leitura em disco.
5. Metadados são persistidos no SQLite.
6. Servidor retorna status lógico para atualização da GUI.

## Demonstração

- O backend gera automaticamente um JSON e uma imagem PNG para cada leitura processada.
- As imagens ficam em `backend/storage/leituras/` e podem ser usadas como evidência visual da execução.
- Para a entrega final no GitHub, você ainda pode adicionar prints da interface ou um vídeo demonstrativo do fluxo cliente/servidor.

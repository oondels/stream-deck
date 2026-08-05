# Desenvolvimento e operação

## Estrutura esperada

```text
platformio.ini            configuração do firmware
include/                  headers de domínio, aplicação e portas
src/                      implementação e adaptadores ESP32
test/                     testes nativos do firmware
host_app/                 pacote e testes Python
docs/                     contratos e decisões
projeto_exemplo.c         referência, fora do build
```

## Firmware

Pré-requisito: PlatformIO Core 6 ou extensão PlatformIO IDE.

```bash
pio run
pio run -t upload
pio device monitor -b 115200
pio test -e native
```

Na primeira gravação, selecione explicitamente a porta se necessário:

```bash
pio run -t upload --upload-port COM4
```

Não mantenha o monitor serial aberto ao executar o aplicativo Python; somente um
processo pode possuir a porta COM.

## Aplicativo Windows

No PowerShell, a partir da raiz:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e host_app
python -m streamdeck_monitor --config host_app\config.example.json
```

Para fixar uma porta:

```powershell
python -m streamdeck_monitor --config host_app\config.example.json --port COM4
```

O diretório `host_app` será incluído no caminho pelo comando de desenvolvimento
documentado no próprio pacote. O monitor cria o diretório de log quando necessário.

## Configuração

O JSON de configuração contém:

- `serial.port`: `auto` ou nome de porta.
- `serial.baud_rate`: deve permanecer `115200` no protocolo v1.
- `serial.scan_interval_seconds`: intervalo entre varreduras.
- `logging.level`: `DEBUG`, `INFO`, `WARNING` ou `ERROR`.
- `logging.file`: caminho do JSONL.
- `logging.max_bytes`: tamanho de cada arquivo.
- `logging.backup_count`: quantidade de backups.

Argumentos da CLI prevalecem sobre o arquivo.

## Diagnóstico

- Nenhuma porta encontrada: confira cabo de dados e driver CH340/CP210x da DevKit.
- Porta ocupada: feche PlatformIO Serial Monitor e outros terminais.
- Porta abre, mas não identifica: confirme firmware e baud rate.
- Eventos repetidos: confira GND, montagem e teste de debounce.
- Encoder invertido: troque A/B no perfil de placa.
- Log indisponível: o console deve continuar e informar a falha.

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

O exemplo configura mídia nas teclas 1 a 4, `Win+D`, Calculadora, YouTube e
volume/mudo no encoder. Edite `actions.bindings` para alterar o mapa.

No Linux, valide todo o fluxo sem executar ações Windows:

```bash
host_app/.venv/bin/python -m streamdeck_monitor \
  --config host_app/config.example.json \
  --port /dev/ttyUSB0 \
  --dry-run-actions
```

Com bindings configurados, executar fora do Windows sem `--dry-run-actions`
termina com erro de configuração operacional.

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
- `actions.queue_size`: limite da fila FIFO, padrão 64.
- `actions.bindings`: relação entre `control`/`event` e uma ação.

Tipos de ação:

- `media`: reprodução, faixa, volume e mudo.
- `hotkey`: combinação de teclas normalizadas em minúsculas.
- `launch`: executável e argumentos, sem interpretação por shell.
- `open_url`: URL HTTP ou HTTPS.

Argumentos da CLI prevalecem sobre o arquivo.

## Diagnóstico

- Nenhuma porta encontrada: confira cabo de dados e driver CH340/CP210x da DevKit.
- Porta ocupada: feche PlatformIO Serial Monitor e outros terminais.
- Porta abre, mas não identifica: confirme firmware e baud rate.
- Eventos repetidos: confira GND, montagem e teste de debounce.
- Encoder invertido: troque A/B no perfil de placa.
- Log indisponível: o console deve continuar e informar a falha.
- `action_failed`: a ação falhou, mas a leitura serial continua.
- `action_suppressed`: evento regressivo não executado para evitar duplicação.
- `action_dropped`: fila cheia ou encerramento com ações pendentes.
- Não abra `pio device monitor` junto com o app. No POSIX, o app solicita
  exclusividade da TTY; apenas um consumidor deve usar a serial.

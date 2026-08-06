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

## Firmware e perfis de placa

Pré-requisito: PlatformIO Core 6 ou extensão PlatformIO IDE.

Ambientes disponíveis:

| Ambiente | Placa | Comunicação USB | Identificação no `hello` |
|---|---|---|---|
| `esp32dev` | ESP32-WROOM-32U/ESP32 Dev Module | ponte USB-UART | `esp32` |
| `esp32c3` | ESP32-C3 compacta | USB CDC/JTAG nativa | `esp32-c3` |
| `native` | computador de desenvolvimento | não se aplica | testes somente |

`esp32dev` é o ambiente padrão. Por isso, comandos sem `-e` continuam
compilando e gravando o ESP32-WROOM-32U.

### Descobrir a porta

Conecte somente a placa que será gravada e execute:

```bash
pio device list
```

No Linux, a porta normalmente será `/dev/ttyUSB0` ou `/dev/ttyACM0`. No Windows,
será algo como `COM4`.

### ESP32-WROOM-32U

```bash
pio run -e esp32dev
pio run -e esp32dev -t upload --upload-port /dev/ttyUSB0
pio device monitor -e esp32dev -p /dev/ttyUSB0
```

No Windows, substitua `/dev/ttyUSB0` por `COM4`.

### ESP32-C3 compacta

Este perfil atende à placa que expõe GPIO0–10, GPIO20 e GPIO21. A comunicação e
a gravação usam USB CDC/JTAG nativa nos GPIO18/19 internos; o encoder usa
GPIO20/21.

```bash
pio run -e esp32c3
pio run -e esp32c3 -t upload --upload-port /dev/ttyACM0
pio device monitor -e esp32c3 -p /dev/ttyACM0
```

Essa placa normalmente aparece como `/dev/ttyACM0` no Linux. Use a porta exibida
por `pio device list`; no Windows, ela aparecerá como uma porta `COM`.

No primeiro upload, se a placa não entrar automaticamente no bootloader:

1. mantenha `BOOT` pressionado;
2. pressione e solte `RESET`;
3. solte `BOOT`;
4. repita o comando de upload com a nova porta detectada.

### Compilar todos e executar testes

```bash
pio run -e esp32dev -e esp32c3
pio test -e native
```

Ao trocar de placa, sempre informe o ambiente correto com `-e`. O perfil escolhe
a pinagem em tempo de compilação; não é necessário alterar o código-fonte.

Antes de iniciar o aplicativo Python, encerre `pio device monitor` com `Ctrl+C`.
Somente um processo pode consumir a porta serial sem corromper ou perder dados.

## Aplicativo Windows

A interface gráfica é o host recomendado. Consulte o [guia completo da
GUI](GUI.md). No PowerShell, a partir da raiz:

```powershell
py -3.12 -m venv host_app\.venv
host_app\.venv\Scripts\Activate.ps1
python -m pip install -e "host_app[gui]"
streamdeck-gui
```

O monitor CLI abaixo permanece disponível para diagnóstico e automação.

No PowerShell:

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

O host identifica automaticamente os dois perfis pelo handshake; não existe uma
configuração Python diferente para cada placa.

O exemplo configura mídia nas teclas 1 a 4, `Win+D`, Calculadora, YouTube e
volume/mudo no encoder. Edite `actions.bindings` para alterar o mapa.

No Linux, valide todo o fluxo sem executar ações Windows:

```bash
host_app/.venv/bin/python -m streamdeck_monitor \
  --config host_app/config.example.json \
  --port /dev/ttyUSB0 \
  --dry-run-actions
```

Se a placa aparecer como `/dev/ttyACM0`, use esse caminho no lugar de
`/dev/ttyUSB0`.

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

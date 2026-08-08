# Stream Deck Mini

Stream Deck físico com sete teclas e um encoder rotativo, baseado em ESP32. O
firmware envia os eventos por USB serial e o aplicativo desktop permite
configurar visualmente ações de mídia, atalhos, aplicativos, URLs e perfis.

O host principal é uma interface gráfica em Python/PySide6 para Windows 10/11.
O Linux pode ser usado para desenvolvimento, leitura do dispositivo e testes em
modo simulado. O monitor CLI continua disponível para diagnóstico.

## Recursos

- Sete teclas com eventos independentes de pressionar e soltar.
- Encoder com giro horário, giro anti-horário, pressionar e soltar.
- Perfis criados e ativados manualmente.
- Nome, ícone e cor configuráveis para cada controle.
- Ordem visual das teclas ajustável para acompanhar a soldagem física.
- Ações de mídia/volume, hotkeys, abertura de aplicativos e URLs.
- Aplicação imediata das alterações, sem desconectar o dispositivo.
- Descoberta automática, reconexão e escolha manual da porta serial.
- Visualização e filtro dos eventos recentes.
- Destaque visual do controle físico acionado.
- Teste manual das ações pela interface.
- Pausa global de ações, bandeja do sistema e autostart opcional.
- Importação/exportação de perfis e backup completo.
- Configuração com escrita atômica e backup automático.
- Suporte a ESP32-WROOM-32U e ESP32-C3 compacta.
- Executável Windows `onedir` gerado com PyInstaller, sem janela de console.

Não estão implementados: macros com várias etapas, shell arbitrário, HID USB,
Wi-Fi, Bluetooth, LEDs e instalador Windows.

## Sumário

- [Requisitos](#requisitos)
- [Hardware e pinagem](#hardware-e-pinagem)
- [Instalação completa no Windows](#instalação-completa-no-windows)
- [Gravar o firmware](#gravar-o-firmware)
- [Executar a interface](#executar-a-interface)
- [Tutoriais de uso](#tutoriais-de-uso)
- [Gerar o executável Windows](#gerar-o-executável-windows)
- [Executar no Linux](#executar-no-linux)
- [Monitor CLI](#monitor-cli)
- [Configuração, dados e logs](#configuração-dados-e-logs)
- [Testes](#testes)
- [Troubleshooting](#troubleshooting)
- [Estrutura e documentação](#estrutura-e-documentação)

## Requisitos

### Hardware

- Uma placa ESP32 suportada:
  - ESP32-WROOM-32U/ESP32 Dev Module com ponte USB-serial; ou
  - ESP32-C3 compacta que exponha GPIO0–10, GPIO20 e GPIO21.
- Sete botões momentâneos normalmente abertos.
- Um encoder incremental de quadratura com botão integrado.
- Fios, protoboard ou placa soldada e um cabo USB de dados.

### Software para Windows

- Windows 10 ou 11, 64-bit.
- Python 3.11 ou superior; Python 3.12 é recomendado.
- Git para clonar o projeto.
- PlatformIO Core para compilar e gravar o firmware.
- Driver USB da placa, quando necessário, normalmente CH340, CP210x ou o driver
  USB/JTAG nativo do ESP32-C3.

O Visual Studio Code e a extensão PlatformIO IDE são opcionais. Todos os
procedimentos abaixo funcionam pelo PowerShell.

## Hardware e pinagem

Todas as entradas usam o pull-up interno do ESP32. Cada botão deve ser ligado
entre seu GPIO e `GND`; não aplique 5 V aos GPIOs.

### ESP32-WROOM-32U / ESP32 Dev Module

| Controle | GPIO | Ligação |
|---|---:|---|
| Tecla 1 | 13 | botão entre GPIO e GND |
| Tecla 2 | 14 | botão entre GPIO e GND |
| Tecla 3 | 16 | botão entre GPIO e GND |
| Tecla 4 | 17 | botão entre GPIO e GND |
| Tecla 5 | 18 | botão entre GPIO e GND |
| Tecla 6 | 19 | botão entre GPIO e GND |
| Tecla 7 | 21 | botão entre GPIO e GND |
| Encoder A | 22 | terminal A; comum no GND |
| Encoder B | 23 | terminal B; comum no GND |
| Clique do encoder | 25 | botão entre GPIO e GND |

### ESP32-C3 compacta

Este perfil atende à placa com as portas `0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
20, 21`. GPIO18 e GPIO19 são usados internamente pelo USB e não precisam estar
expostos.

| Controle | GPIO | Ligação |
|---|---:|---|
| Tecla 1 | 0 | botão entre GPIO e GND |
| Tecla 2 | 1 | botão entre GPIO e GND |
| Tecla 3 | 3 | botão entre GPIO e GND |
| Tecla 4 | 4 | botão entre GPIO e GND |
| Tecla 5 | 5 | botão entre GPIO e GND |
| Tecla 6 | 6 | botão entre GPIO e GND |
| Tecla 7 | 7 | botão entre GPIO e GND |
| Clique do encoder | 10 | botão entre GPIO e GND |
| Encoder A | 20 | terminal A; comum no GND |
| Encoder B | 21 | terminal B; comum no GND |

GPIO2, GPIO8 e GPIO9 são pinos de strapping e não são usados como controles.
GPIO8 fica reservado para um possível LED futuro. Consulte
[docs/HARDWARE.md](docs/HARDWARE.md) antes de montar a placa definitiva.

## Instalação completa no Windows

### 1. Clonar o projeto

Abra o PowerShell:

```powershell
git clone https://github.com/oondels/stream-deck.git
cd stream-deck
```

Se você já possui o repositório:

```powershell
cd stream-deck
git pull
```

Todos os comandos deste README consideram que o terminal está na raiz
`stream-deck`.

### 2. Verificar o Python

```powershell
py -3.12 --version
```

Se esse comando não funcionar, instale o Python 3.12 64-bit e habilite o Python
Launcher durante a instalação. Python 3.11 ou mais recente também é aceito;
nesse caso, substitua `py -3.12` pelo comando disponível.

### 3. Criar o ambiente virtual

```powershell
py -3.12 -m venv host_app\.venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
host_app\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

O prompt deve passar a mostrar `(.venv)`. Sempre ative esse ambiente antes de
executar comandos Python do projeto.

### 4. Instalar a GUI e o PlatformIO

```powershell
python -m pip install -e "host_app[gui]"
python -m pip install platformio
```

Verifique a instalação:

```powershell
streamdeck-gui --help
pio --version
```

## Gravar o firmware

### 1. Descobrir a porta

Conecte apenas a placa que será gravada:

```powershell
pio device list
```

Procure uma porta como `COM4`. Feche Arduino IDE, PlatformIO Serial Monitor e
qualquer outro programa que possa estar usando essa porta.

### 2. ESP32-WROOM-32U / ESP32 Dev Module

Compile:

```powershell
pio run -e esp32dev
```

Grave, substituindo `COM4` pela porta encontrada:

```powershell
pio run -e esp32dev -t upload --upload-port COM4
```

### 3. ESP32-C3 compacta

Compile:

```powershell
pio run -e esp32c3
```

Grave:

```powershell
pio run -e esp32c3 -t upload --upload-port COM4
```

Se o primeiro upload não entrar automaticamente no bootloader:

1. Mantenha `BOOT` pressionado.
2. Pressione e solte `RESET`.
3. Solte `BOOT`.
4. Execute novamente `pio device list`.
5. Repita o upload usando a porta exibida.

### 4. Conferir o firmware pela serial

```powershell
pio device monitor -e esp32c3 -p COM4
```

Use `esp32dev` no lugar de `esp32c3` para a outra placa. O baud rate é 115200.
Ao iniciar, o firmware deve emitir uma mensagem `hello`; botões e encoder devem
emitir mensagens `input` em JSON.

Encerre o monitor com `Ctrl+C` antes de abrir a GUI. Apenas um processo pode
consumir a porta serial ao mesmo tempo.

## Executar a interface

Com o ambiente virtual ativo:

```powershell
streamdeck-gui
```

Alternativa equivalente:

```powershell
python -m streamdeck_monitor.gui.bootstrap
```

Na primeira execução, a aplicação cria o perfil multimídia padrão. Deixe a
porta serial como `auto`: a GUI examina as portas e aceita apenas o dispositivo
que responder ao handshake do Stream Deck Mini.

O arquivo de configuração fica em:

```text
%APPDATA%\StreamDeckMini\config.json
```

Quando habilitado, o autostart é salvo no registro do usuário em
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`; não exige privilégios de
administrador.

## Tutoriais de uso

### Primeiro teste integrado

1. Grave o firmware correspondente à sua placa.
2. Feche o monitor serial do PlatformIO.
3. Conecte o ESP32 e execute `streamdeck-gui`.
4. Aguarde `Conectado — COMx` no topo da janela.
5. Pressione cada uma das sete teclas.
6. Gire o encoder nos dois sentidos e pressione seu botão.
7. Confira o destaque do controle e as linhas na aba `Eventos`.

### Configurar uma tecla

1. Selecione a tecla no desenho do dispositivo.
2. Altere seu nome, ícone e cor.
3. Escolha `Pressionar` ou `Soltar`.
4. Escolha o tipo de ação.
5. Preencha os campos da ação.
6. Saia do campo ou confirme a seleção; alterações válidas são salvas e
   aplicadas imediatamente.
7. Clique em `Testar ação`.

Selecionar `Nenhuma` remove a ação daquele evento.

### Reorganizar as teclas conforme a soldagem

A ordem visual é global porque representa a ligação física do dispositivo; ela
continua igual ao trocar de perfil.

1. Clique em `Reordenar teclas` na área do dispositivo.
2. Arraste uma tecla sobre outra para trocar suas posições.
3. Repita até o desenho corresponder à posição real de cada botão.
4. Clique em `Concluir organização`.

A alteração é salva a cada troca. O encoder permanece fixo no canto superior
direito. Aparência, bindings, seleção e destaque acompanham o controle físico:
se `key_4` for movida para a primeira posição, uma entrada `key_4` destacará e
editará essa posição.

### Configurar mídia e volume

Escolha `Mídia / volume` e selecione uma operação:

- reproduzir/pausar;
- faixa anterior ou próxima;
- parar;
- aumentar ou diminuir volume;
- silenciar volume.

### Configurar um atalho

Escolha `Atalho de teclado` e informe as teclas separadas por `+`:

```text
Ctrl+Shift+S
```

São aceitos modificadores, letras, números, `F1`–`F24`, setas e teclas comuns
como Enter, Escape, Tab, espaço, Home, End, Delete e Page Up/Page Down.

### Abrir um aplicativo

Escolha `Abrir aplicativo` e informe o executável, por exemplo:

```text
C:\Windows\System32\calc.exe
```

Argumentos são opcionais. O aplicativo é aberto diretamente, sem interpretação
por shell.

### Abrir uma URL

Escolha `Abrir URL` e informe um endereço completo HTTP ou HTTPS:

```text
https://www.youtube.com
```

### Configurar o encoder

Selecione o encoder e configure separadamente:

- girar no sentido horário;
- girar no sentido anti-horário;
- pressionar;
- soltar.

Se os sentidos estiverem invertidos fisicamente, troque os terminais A e B do
encoder.

### Criar e trocar perfis

- `Novo` cria um perfil com o mapeamento padrão.
- `Duplicar` copia o perfil atual para servir como ponto de partida.
- `Renomear` altera o nome.
- `Excluir` remove o perfil atual; pelo menos um perfil sempre é mantido.
- Um clique na lista ativa o perfil imediatamente.

Os perfis também podem ser selecionados pelo menu da bandeja.

### Importar, exportar e recuperar configurações

No menu `Arquivo`:

- `Importar perfil` adiciona um perfil vindo de outro computador.
- `Exportar perfil` salva apenas o perfil ativo.
- `Exportar backup completo` salva todas as preferências e perfis.
- `Restaurar backup completo` substitui a configuração em uso pelo arquivo
  escolhido.

Antes de cada gravação, a configuração anterior também é preservada como
`config.json.bak`.

### Pausa, bandeja e autostart

- `Pausar ações` mantém a leitura e os logs, mas bloqueia ações disparadas pelo
  hardware.
- `Testar ação` continua disponível durante a pausa.
- Fechar a janela minimiza para a bandeja quando essa opção estiver ativa.
- Use `Sair` no menu da bandeja para encerrar o monitor e liberar a porta.
- `Arquivo > Configurações` permite ativar o início automático com o Windows.

### Investigar eventos

A aba `Eventos` pode ser filtrada por texto ou nível. Eventos mais importantes:

| Evento | Significado |
|---|---|
| `device_searching` | procurando o dispositivo |
| `device_connected` | handshake concluído |
| `device_disconnected` | porta removida ou falha de leitura |
| `input` | evento físico válido recebido |
| `action_succeeded` | ação executada no Windows |
| `action_dry_run` | ação apenas simulada |
| `action_failed` | falha ao executar uma ação |
| `action_suppressed` | ação bloqueada por pausa ou sequência regressiva |
| `sequence_gap` | uma ou mais mensagens não chegaram ao host |
| `invalid_message` | linha serial não contém uma mensagem válida |

## Gerar o executável Windows

O projeto gera uma distribuição `onedir`: o executável e suas dependências ficam
em uma pasta que deve ser distribuída inteira. Não há instalador nesta etapa.

No PowerShell, a partir da raiz:

```powershell
powershell -ExecutionPolicy Bypass -File host_app\scripts\build_gui.ps1
```

O script:

1. cria `host_app\.venv` se necessário;
2. instala as dependências de GUI e build;
3. executa o PyInstaller com `streamdeck_gui.spec`;
4. gera a aplicação sem console.

Resultado:

```text
host_app\dist\StreamDeckMini\StreamDeckMini.exe
```

Para distribuir, compacte ou copie toda a pasta `StreamDeckMini`. Executar
somente o `.exe` fora dessa pasta não funciona. O build Windows deve ser gerado
no próprio Windows; o PyInstaller não faz compilação cruzada de Linux para
Windows.

Antes de publicar uma versão, execute os testes e o checklist manual de
[docs/GUI.md](docs/GUI.md).

## Executar no Linux

No Linux, a interface lê o ESP32, permite editar perfis e mostra os eventos, mas
as ações externas são automaticamente simuladas como `action_dry_run`. A
execução real das ações atuais usa APIs do Windows.

### Ubuntu 24.04 e derivados

```bash
sudo apt update
sudo apt install python3-venv libxcb-cursor0
python3 -m venv host_app/.venv
source host_app/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'host_app[gui]'
python -m pip install platformio
streamdeck-gui
```

Se a porta serial retornar `Permission denied`:

```bash
sudo usermod -aG dialout "$USER"
```

Encerre a sessão e entre novamente para aplicar o novo grupo. A placa geralmente
aparece como `/dev/ttyUSB0` no ESP32 Dev Module ou `/dev/ttyACM0` no ESP32-C3.

Para descobrir a porta:

```bash
pio device list
```

## Monitor CLI

O CLI é útil para diagnosticar a comunicação sem abrir a interface.

### Windows

```powershell
python -m streamdeck_monitor `
  --config host_app\config.example.json `
  --port COM4
```

O argumento `--port` é opcional. Sem ele, a configuração `auto` examina todas
as portas.

### Linux em dry-run

```bash
python -m streamdeck_monitor \
  --config host_app/config.example.json \
  --port /dev/ttyUSB0 \
  --dry-run-actions
```

No dry-run, cada binding encontrado gera `action_dry_run`, mas não abre URLs,
programas nem envia teclas.

## Configuração, dados e logs

### GUI

| Sistema | Diretório padrão |
|---|---|
| Windows | `%APPDATA%\StreamDeckMini` |
| Linux | `~/.streamdeck-mini` |

Arquivos principais:

- `config.json`: configuração v2, perfis, aparência e bindings.
- `config.json.bak`: versão anterior criada automaticamente.
- `logs/events.jsonl`: log estruturado com rotação.

Não edite o JSON enquanto a GUI estiver aberta. Prefira os formulários e os
comandos de importação/exportação.

O campo global `key_order` guarda a ordem visual de `key_1` a `key_7`.
Configurações anteriores que não possuem o campo usam automaticamente a ordem
padrão.

### CLI legado

O exemplo [host_app/config.example.json](host_app/config.example.json) continua
compatível. Ele configura:

- teclas 1–4 para controles de mídia;
- tecla 5 para `Win+D`;
- tecla 6 para a Calculadora;
- tecla 7 para o YouTube;
- encoder para volume e mudo.

O baud rate deve permanecer em `115200` no protocolo v1.

## Testes

### Aplicativo Python

Com o ambiente virtual ativo:

```bash
cd host_app
python -m pip install -e '.[gui,gui-test]'
python -m pip install ruff
pytest
ruff check streamdeck_monitor tests
cd ..
```

### Firmware

```bash
pio test -e native
pio run -e esp32dev
pio run -e esp32c3
```

Os testes Qt usam o backend `offscreen`, portanto não precisam abrir janelas.

## Troubleshooting

### `streamdeck-gui` não é reconhecido

Ative o ambiente virtual e reinstale o pacote:

```powershell
host_app\.venv\Scripts\Activate.ps1
python -m pip install -e "host_app[gui]"
python -m streamdeck_monitor.gui.bootstrap
```

No Linux, use `source host_app/.venv/bin/activate`.

### PowerShell bloqueia `Activate.ps1`

Libere scripts somente para o terminal atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
host_app\.venv\Scripts\Activate.ps1
```

### Qt encontra `xcb`, mas não consegue carregá-lo no Linux

Erro típico:

```text
xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin
```

No Ubuntu/Debian:

```bash
sudo apt install libxcb-cursor0
```

Se persistir:

```bash
QT_DEBUG_PLUGINS=1 streamdeck-gui
```

### A GUI fica em `Procurando dispositivo`

- Confira se o cabo USB transmite dados.
- Execute `pio device list` e confirme que a porta existe.
- Feche o Serial Monitor, Arduino IDE e outra instância do host.
- Confira se o firmware correto foi gravado.
- Mantenha baud rate em 115200.
- Em `Arquivo > Configurações`, tente fixar a porta `COM` detectada.
- Teste outra porta USB e outro cabo.
- Instale o driver CH340/CP210x correspondente à sua placa.

### A porta está ocupada ou retorna acesso negado

Somente um programa pode abrir a serial. Encerre:

- `pio device monitor`;
- Arduino Serial Monitor;
- PuTTY, screen ou minicom;
- outra instância antiga do aplicativo.

No Linux, adicione seu usuário ao grupo `dialout` conforme a seção de instalação.

### ESP32-C3 não entra no modo de gravação

Use a sequência `BOOT` + `RESET` descrita na seção de firmware. A porta pode
mudar quando o bootloader é ativado; execute novamente `pio device list`.

### Upload falha com timeout

- Confira o ambiente: `esp32dev` ou `esp32c3`.
- Informe explicitamente `--upload-port COMx`.
- Feche qualquer consumidor da serial.
- Reduza extensões USB e teste um cabo curto de dados.
- No ESP32-C3, entre manualmente no bootloader.

### Eventos chegam, mas ações não acontecem

- No Linux isso é esperado: procure `action_dry_run` nos eventos.
- No CLI, remova `--dry-run-actions` somente no Windows.
- Na GUI, confirme que `Pausar ações` não está ativo.
- Confira se o evento configurado é `Pressionar`, `Soltar` ou o movimento correto
  do encoder.
- Use `Testar ação`; se falhar, procure `action_failed`.
- Para aplicativos, use um caminho de executável válido.
- Para URLs, informe `http://` ou `https://`.

### Aparecem `invalid_message` e `sequence_gap`

Uma linha JSON foi corrompida ou um número de sequência não chegou. Ocorrências
isoladas não derrubam o aplicativo e a leitura continua. Se forem frequentes:

- troque o cabo USB;
- evite hubs sem alimentação;
- confira GND e alimentação da montagem;
- certifique-se de que apenas um processo lê a serial;
- confira se botões e encoder não usam pinos reservados.

### Botão dispara mais de uma vez

- Confira a ligação entre GPIO e GND.
- Não use resistores externos que conflitem com o pull-up interno.
- Verifique ruído, mau contato e comprimento dos fios.
- Confirme que o firmware atual está gravado; ele aplica debounce de 30 ms.

### Encoder gira ao contrário ou perde passos

- Troque os terminais A e B para inverter o sentido.
- Confira o terminal comum no GND.
- Evite fios longos e mau contato.
- Um passo físico inválido é descartado deliberadamente pelo firmware.

### Configuração inválida impede a abertura

A configuração e seu backup ficam no diretório de dados descrito anteriormente.
Com a aplicação encerrada:

1. preserve uma cópia dos dois arquivos;
2. substitua `config.json` por `config.json.bak`; ou
3. renomeie `config.json` para que a aplicação crie o padrão novamente.

### A janela desapareceu ao fechar

Ela provavelmente está na bandeja. Dê duplo clique no ícone ou use `Abrir`.
Para encerrar completamente, escolha `Sair`. Esse comportamento pode ser
desativado em `Arquivo > Configurações`.

### O executável funciona no computador de build, mas não em outro

- Distribua a pasta `dist\StreamDeckMini` inteira.
- Não mova apenas `StreamDeckMini.exe`.
- Gere o build no Windows de mesma arquitetura do destino.
- Confira se o antivírus colocou algum arquivo em quarentena.
- Instale o driver USB necessário para a placa.

## Estrutura e documentação

```text
platformio.ini                 perfis de firmware
include/ e src/                firmware e regras compartilhadas
test/                          testes nativos do firmware
host_app/                      pacote Python, GUI, CLI e testes
host_app/scripts/build_gui.ps1 build Windows
host_app/streamdeck_gui.spec   configuração PyInstaller
docs/                          arquitetura, protocolo e guias especializados
```

Documentação complementar:

- [Visão e escopo](docs/VISION.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Hardware](docs/HARDWARE.md)
- [Protocolo serial](docs/PROTOCOL.md)
- [Desenvolvimento e operação](docs/DEVELOPMENT.md)
- [Interface gráfica e checklist Windows](docs/GUI.md)
- [Estratégia de testes](docs/TESTING.md)
- [Portabilidade para Raspberry Pi Pico](docs/PORTABILITY.md)
- [Decisão de plataforma e transporte](docs/adr/0001-esp32-serial-first.md)

O arquivo `projeto_exemplo.c` é apenas uma referência histórica e não participa
da compilação.

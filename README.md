# Stream Deck Mini

Controlador multimídia experimental baseado em ESP32-WROOM-32U, sete botões e
um encoder rotativo com clique. O firmware envia eventos por uma porta serial
USB e o aplicativo Windows transforma bindings configuráveis em ações locais.

O projeto foi estruturado para que regras de entrada e protocolo não dependam do
ESP32. A futura migração para Raspberry Pi Pico deve exigir principalmente novos
adaptadores de hardware e configuração do PlatformIO.

## Estado do MVP

- Alvo atual: ESP32-WROOM-32U em uma DevKit com ponte USB-serial.
- Perfil alternativo: ESP32-C3 compacta com USB CDC nativa.
- Controles: sete botões e encoder com giro horário, anti-horário e clique.
- Transporte: JSON Lines pela serial a 115200 baud.
- Host: aplicativo Python com interface gráfica, bandeja, perfis e log JSONL.
- Ações: mídia/volume, hotkeys, aplicativos e URLs configurados visualmente.
- CLI: monitor de terminal preservado para desenvolvimento e diagnóstico.
- Fora da etapa atual: HID, macros, instalador, Wi-Fi, Bluetooth e LEDs.

## Documentação

- [Visão e escopo](docs/VISION.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Hardware](docs/HARDWARE.md)
- [Protocolo serial](docs/PROTOCOL.md)
- [Desenvolvimento e operação](docs/DEVELOPMENT.md)
- [Interface gráfica Windows](docs/GUI.md)
- [Estratégia de testes](docs/TESTING.md)
- [Portabilidade para Pico](docs/PORTABILITY.md)
- [Decisão de plataforma e transporte](docs/adr/0001-esp32-serial-first.md)

## Fluxo de uso

1. Escolha `esp32dev` ou `esp32c3` e monte os controles conforme a tabela do
   perfil em `docs/HARDWARE.md`.
2. Instale o PlatformIO e compile/grave com `pio run -e <perfil>` conforme
   `docs/DEVELOPMENT.md`.
3. Crie o ambiente virtual Python e instale as dependências da interface.
4. Execute `streamdeck-gui` conforme o guia da interface gráfica.
5. Configure os controles visualmente; pressione os botões e gire o encoder.

O arquivo `projeto_exemplo.c` é somente uma referência histórica e não participa
da compilação.

# Stream Deck Mini

Controlador multimídia experimental baseado em ESP32-WROOM-32U, sete botões e
um encoder rotativo com clique. O firmware envia eventos por uma porta serial
USB e o aplicativo Windows transforma bindings configuráveis em ações locais.

O projeto foi estruturado para que regras de entrada e protocolo não dependam do
ESP32. A futura migração para Raspberry Pi Pico deve exigir principalmente novos
adaptadores de hardware e configuração do PlatformIO.

## Estado do MVP

- Alvo atual: ESP32-WROOM-32U em uma DevKit com ponte USB-serial.
- Controles: sete botões e encoder com giro horário, anti-horário e clique.
- Transporte: JSON Lines pela serial a 115200 baud.
- Host: monitor Python para Windows, com console, JSONL e fila de ações.
- Ações: mídia/volume, hotkeys, aplicativos e URLs configurados por JSON.
- Fora da etapa atual: HID, GUI, perfis, autostart, Wi-Fi, Bluetooth e LEDs.

## Documentação

- [Visão e escopo](docs/VISION.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Hardware](docs/HARDWARE.md)
- [Protocolo serial](docs/PROTOCOL.md)
- [Desenvolvimento e operação](docs/DEVELOPMENT.md)
- [Estratégia de testes](docs/TESTING.md)
- [Portabilidade para Pico](docs/PORTABILITY.md)
- [Decisão de plataforma e transporte](docs/adr/0001-esp32-serial-first.md)

## Fluxo de uso

1. Monte os controles conforme `docs/HARDWARE.md`.
2. Instale o PlatformIO e compile/grave o firmware conforme
   `docs/DEVELOPMENT.md`.
3. Crie o ambiente virtual Python e instale as dependências.
4. Execute `python -m streamdeck_monitor` a partir da raiz conforme o guia de
   desenvolvimento.
5. Pressione os botões e gire o encoder; confira eventos e ações no log.

O arquivo `projeto_exemplo.c` é somente uma referência histórica e não participa
da compilação.

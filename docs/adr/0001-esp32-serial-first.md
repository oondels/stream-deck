# ADR 0001: ESP32 atual com transporte serial

- Estado: aceito
- Data: 2026-08-04

## Contexto

O hardware disponível é uma DevKit com ESP32-WROOM-32U e USB-C. O sufixo `U`
indica antena externa; o ESP32 clássico não expõe HID USB nativo por esse
conector. A USB-C da DevKit usa uma ponte para a UART.

O produto deverá migrar futuramente para Raspberry Pi Pico, que possui USB nativo.
Antes de executar ações Windows, é necessário validar controles e transporte.

## Decisão

Usar o ESP32-WROOM-32U no MVP e transportar eventos por JSON Lines sobre serial.
O aplicativo Windows apenas registra eventos. Hardware e transporte serão
adaptadores externos às regras.

## Consequências

- O aplicativo precisa permanecer ativo para observar o deck.
- A ponte USB pode exigir driver e aparece como COM variável.
- Handshake é necessário para identificar a porta correta.
- Domínio, protocolo e host podem ser preservados na migração.
- HID e ações Windows ficam explicitamente adiados.

# Portabilidade para Raspberry Pi Pico

## Objetivo

Migrar futuramente o firmware para Pico RP2040 sem alterar comportamento externo
nem aplicativo Windows.

## Artefatos reutilizados

- Tipos e regras do domínio.
- Casos de uso de varredura e publicação.
- Contrato JSON Lines v1.
- Testes nativos e fakes.
- Aplicativo Python e arquivos de log.

## Artefatos substituídos

- Ambiente PlatformIO e perfil de pinagem.
- Adaptadores de GPIO e relógio quando a API diferir.
- UART com ponte USB-serial por USB CDC nativo.
- Rotina de upload e diagnóstico.

## Regras para preservar a migração

- Não usar tipos Arduino nas assinaturas internas.
- Não consultar pinos diretamente em casos de uso.
- Não serializar JSON dentro do domínio.
- Não condicionar regras com `#ifdef ESP32`.
- Adicionar Pico como perfil e adaptador separado quando a migração ocorrer.
- Manter o handshake baseado em `device`; `board` é apenas diagnóstico.

## Critério de prontidão

A arquitetura está pronta para o port quando os testes de domínio/aplicação
compilam no ambiente nativo sem pacotes Espressif e o monitor aceita um `hello`
com qualquer `board` suportada.

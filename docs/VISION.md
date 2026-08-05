# Visão e escopo

## Problema

Criar uma base confiável para um deck físico programável no Windows. Antes de
executar ações externas, o primeiro incremento precisa comprovar leitura dos
controles, transporte USB serial, descoberta do dispositivo e observabilidade.

## Resultado do MVP

Ao conectar o ESP32 ao Windows, um monitor Python encontra o dispositivo pelo
handshake. Cada mudança de estado dos sete botões, cada passo do encoder e o
clique são mostrados no console e persistidos em um log estruturado. Remover e
recolocar o cabo não exige reiniciar o monitor.

## Critérios de sucesso

- Um acionamento físico produz um único evento sem repetição causada por bounce.
- O sentido do encoder é identificado corretamente.
- O protocolo permite detectar eventos perdidos por meio de sequência crescente.
- Mensagens inválidas não derrubam firmware nem aplicativo.
- O monitor redescobre o deck depois de uma desconexão.
- Domínio e aplicação podem ser testados sem placa ou porta COM.
- A montagem e a operação podem ser reproduzidas somente com a documentação.

## Fora do escopo

- Execução de atalhos, mídia, programas, URLs ou comandos.
- HID USB, GUI, instalador ou executável empacotado.
- Wi-Fi, Bluetooth, atualização remota e persistência no microcontrolador.
- LEDs externos. O GPIO futuro fica apenas reservado e documentado.
- Perfis, macros, clique longo, duplo clique e aceleração do encoder.

## Evolução prevista

1. Validar o hardware e a telemetria serial. **Concluído.**
2. Adicionar bindings seguros e ações Windows como casos de uso do host.
   **Implementado nesta etapa.**
3. Adicionar configuração visual e perfis.
4. Adicionar feedback luminoso por adaptador de saída.
5. Portar a infraestrutura do firmware para Raspberry Pi Pico e avaliar HID USB.

## Resultado da etapa 2

- Bindings são validados e carregados de JSON na inicialização.
- Eventos podem controlar mídia/volume, hotkeys, aplicativos e URLs no Windows.
- Ações usam fila dedicada e não bloqueiam a leitura serial.
- Linux oferece dry-run explícito para validar a integração sem efeitos externos.
- Shell arbitrário, macros, gestos adicionais, GUI e perfis continuam fora do
  escopo.

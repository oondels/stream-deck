# Hardware

## Componentes

- Uma placa suportada: ESP32-WROOM-32U/ESP32 Dev Module com ponte USB-serial ou
  ESP32-C3 compacta com USB nativa.
- Antena externa compatível com o conector U.FL se Wi-Fi/Bluetooth forem usados
  futuramente; rádio não é necessário neste MVP.
- Sete botões momentâneos normalmente abertos.
- Um encoder incremental de quadratura com botão integrado.
- Protoboard ou placa, fios e cabo USB de dados.

## Pinagem

### ESP32-WROOM-32U

| Controle | GPIO | Ligação |
|---|---:|---|
| Tecla 1 | 13 | botão entre GPIO e GND |
| Tecla 2 | 14 | botão entre GPIO e GND |
| Tecla 3 | 16 | botão entre GPIO e GND |
| Tecla 4 | 17 | botão entre GPIO e GND |
| Tecla 5 | 18 | botão entre GPIO e GND |
| Tecla 6 | 19 | botão entre GPIO e GND |
| Tecla 7 | 21 | botão entre GPIO e GND |
| Encoder A | 22 | terminal A entre GPIO e comum/GND |
| Encoder B | 23 | terminal B entre GPIO e comum/GND |
| Encoder clique | 25 | botão entre GPIO e GND |
| LED futuro | 26 | reservado; deixar desconectado |

### ESP32-C3 compacta

Este perfil corresponde à placa que expõe os GPIO0–10, GPIO20 e GPIO21. Os
GPIO18/19 são ligados internamente ao conector USB e não aparecem nos headers.

| Controle | GPIO | Ligação |
|---|---:|---|
| Tecla 1 | 0 | botão entre GPIO e GND |
| Tecla 2 | 1 | botão entre GPIO e GND |
| Tecla 3 | 3 | botão entre GPIO e GND |
| Tecla 4 | 4 | botão entre GPIO e GND |
| Tecla 5 | 5 | botão entre GPIO e GND |
| Tecla 6 | 6 | botão entre GPIO e GND |
| Tecla 7 | 7 | botão entre GPIO e GND |
| Encoder clique | 10 | botão entre GPIO e GND |
| Encoder A | 20 | terminal A entre GPIO e comum/GND |
| Encoder B | 21 | terminal B entre GPIO e comum/GND |
| LED futuro | 8 | reservado; não utilizado atualmente |

A USB CDC nativa permanece habilitada: GPIO18 é USB D- e GPIO19 é USB D+.
GPIO2, GPIO8 e GPIO9 são pinos de strapping e não são usados como controles.

Todas as entradas usam pull-up interno e ficam em nível alto quando abertas.
O evento ativo ocorre em nível baixo.

## Restrições

- Regras comuns:
  - confirmar no silk da DevKit que todos os GPIOs da tabela estão expostos;
  - nunca aplicar 5 V a um GPIO; a lógica opera em 3,3 V;
  - compartilhar o mesmo GND entre placa, botões e encoder;
  - usar um cabo USB que transporte dados, não apenas energia.
- No ESP32-WROOM-32U:
  - GPIO1 e GPIO3 ficam reservados à UART0/ponte USB-serial;
  - GPIO6 a GPIO11 ficam conectados à flash e não devem ser usados.
- No ESP32-C3 compacto:
  - GPIO18 e GPIO19 ficam reservados internamente para USB CDC/JTAG;
  - GPIO20 e GPIO21 são usados pelo encoder e não pela UART0;
  - GPIO2, GPIO8 e GPIO9 são pinos de strapping; não conecte botões a eles.

## Montagem

1. Escolha a tabela correspondente à placa e, com ela desligada, conecte um
   terminal de cada botão ao GPIO indicado.
2. Una os outros terminais ao GND.
3. Conecte o comum do encoder ao GND e os terminais A/B aos GPIOs da tabela.
4. Conecte o clique do encoder entre o GPIO indicado e GND.
5. Revise continuidade e ausência de curto antes de conectar a USB.

Se o sentido do encoder ficar invertido, corrija a ordem A/B no perfil de placa;
não altere a regra de domínio.

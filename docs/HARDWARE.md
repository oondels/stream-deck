# Hardware

## Componentes

- Uma DevKit com ESP32-WROOM-32U, conector USB-C e ponte USB-serial.
- Antena externa compatível com o conector U.FL se Wi-Fi/Bluetooth forem usados
  futuramente; rádio não é necessário neste MVP.
- Sete botões momentâneos normalmente abertos.
- Um encoder incremental de quadratura com botão integrado.
- Protoboard ou placa, fios e cabo USB de dados.

## Pinagem

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

Todas as entradas usam pull-up interno e ficam em nível alto quando abertas.
O evento ativo ocorre em nível baixo.

## Restrições

- Confirmar no silk da DevKit que todos os GPIOs da tabela estão expostos.
- Nunca aplicar 5 V a um GPIO; a lógica do ESP32 opera em 3,3 V.
- Não usar GPIO 1 e 3, reservados à UART0/ponte USB-serial.
- Não usar GPIO 6 a 11, conectados à flash do módulo.
- O encoder deve compartilhar o mesmo GND da placa.
- O cabo USB precisa transportar dados, não apenas energia.

## Montagem

1. Com a placa desligada, conecte um terminal de cada botão ao GPIO indicado.
2. Una os outros terminais ao GND.
3. Conecte o comum do encoder ao GND, A ao GPIO 22 e B ao GPIO 23.
4. Conecte o clique do encoder entre GPIO 25 e GND.
5. Revise continuidade e ausência de curto antes de conectar a USB.

Se o sentido do encoder ficar invertido, corrija a ordem A/B no perfil de placa;
não altere a regra de domínio.

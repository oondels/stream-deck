# Protocolo serial v1

## Transporte

- UART0 exposta ao Windows por uma ponte USB-serial.
- 115200 baud, 8 bits, sem paridade, um stop bit.
- UTF-8, uma mensagem JSON por linha, terminada por `\n`.
- Linha máxima: 256 bytes, incluindo terminador.
- Chaves adicionais devem ser ignoradas para compatibilidade futura.

## Mensagens do host

### Probe

```json
{"v":1,"type":"probe"}
```

Pode ser enviado a qualquer momento. O firmware responde com `hello`.

## Mensagens do dispositivo

### Hello

```json
{"v":1,"type":"hello","device":"stream-deck-mini","board":"esp32","firmware":"0.1.0"}
```

Enviado no boot e em resposta a `probe`.

### Evento de entrada

```json
{"v":1,"type":"input","control":"key_1","event":"press","seq":1,"uptime_ms":1234}
```

Campos obrigatórios:

| Campo | Tipo | Regra |
|---|---|---|
| `v` | inteiro | exatamente `1` |
| `type` | string | `input` |
| `control` | string | identificador da tabela abaixo |
| `event` | string | evento permitido para o controle |
| `seq` | inteiro sem sinal | crescente por boot, iniciando em 1 |
| `uptime_ms` | inteiro sem sinal | relógio monotônico desde o boot |

Controles e eventos:

| Controle | Eventos |
|---|---|
| `key_1` a `key_7` | `press`, `release` |
| `encoder_press` | `press`, `release` |
| `encoder_cw`, `encoder_ccw` | `rotate` |

Cada passo lógico completo do encoder gera um `rotate`. `seq` avança apenas
para eventos de entrada, não para `hello`.

## Validação e compatibilidade

- JSON inválido, versão incompatível ou mensagem desconhecida não derruba a
  conexão.
- O firmware ignora mensagens desconhecidas do host.
- O host registra e ignora mensagens desconhecidas do dispositivo.
- Um salto crescente de `seq` indica perda; regressão indica reinício ou nova
  sessão e deve ser registrada.
- O campo `board` não altera comportamento. Uma futura porta usará `pico`.
- Mudança incompatível exige incrementar `v`.

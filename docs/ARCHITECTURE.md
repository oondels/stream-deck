# Arquitetura

## Contexto

```text
[Botões + encoder]
        |
        v
[Firmware ESP32] -- JSON Lines / UART / ponte USB --> [Monitor Python]
                                                          |       |
                                                          v       v
                                                      [console] [JSONL]
                                                          |
                                                          v
                                                    [bindings + fila]
                                                          |
                                                          v
                                                    [ações Windows]
```

O handshake, e não VID/PID ou nome de porta, identifica o deck. Isso evita
acoplamento a diferentes pontes USB-serial e preserva o contrato na futura troca
de microcontrolador.

## Regras de dependência

As dependências apontam para dentro. Domínio não conhece framework, sistema
operacional, transporte ou representação JSON.

```text
bootstrap -> infraestrutura -> aplicação -> domínio
                  |                  |
                  +------ portas <---+
```

### Firmware

- **Domínio:** identificadores de controles, tipos de evento, debounce e
  decodificação determinística do encoder.
- **Aplicação:** varre controles, transforma transições em `InputEvent`, atribui
  sequência e publica.
- **Portas:** contratos de entrada digital, relógio e publicador de eventos.
- **Infraestrutura:** GPIO/millis do Arduino e transporte JSON pela serial.
- **Bootstrap:** instancia e conecta implementações no `setup()`/`loop()`.

O JSON é uma representação de saída; portanto, sua serialização permanece no
adaptador serial e não no evento de domínio.

### Monitor Windows

- **Domínio:** mensagens aceitas, validação e erros de protocolo.
- **Aplicação:** descoberta, conexão, sequência, resolução de bindings e emissão
  de registros.
- **Portas:** fonte serial, relógio, destino de registros, dispatcher e executor
  de ações.
- **Infraestrutura:** pyserial, console, arquivo rotativo, fila e APIs Windows.
- **Bootstrap:** CLI, configuração e composição.

## Fluxos principais

### Descoberta

1. O monitor enumera portas candidatas.
2. Abre uma por vez e envia `probe`.
3. Aceita somente uma resposta `hello` compatível com protocolo v1 e o nome do
   dispositivo.
4. Mantém a conexão até erro ou remoção.
5. Retorna à descoberta com backoff quando desconectado.

### Entrada

1. O adaptador GPIO fornece o nível atual e o relógio monotônico.
2. A regra de controle elimina bounce e transições inválidas.
3. A aplicação cria um evento e incrementa `seq`.
4. O adaptador serial converte o evento em uma linha JSON.
5. O host valida a linha, verifica a sequência e envia o registro aos dois sinks.
6. Um binding correspondente é enfileirado sem bloquear a leitura.
7. O worker executa a ação e registra sucesso ou falha.

## Falhas e recuperação

- Porta ocupada ou sem resposta: fechar e continuar a varredura.
- Cabo removido: registrar, fechar recursos e tentar novamente.
- Linha inválida: registrar aviso e continuar.
- Falha no arquivo: manter console ativo e informar o erro.
- Reinício do firmware: um novo `hello` e/ou redução de `seq` inicia nova sessão.
- Fila/buffer saturado: nunca bloquear indefinidamente o loop de controles.
- Ação externa falha: registrar e continuar processando a serial.
- Sequência duplicada ou regressiva: registrar e suprimir a ação correspondente.

## Limites arquiteturais

- Nenhum include Arduino em domínio ou aplicação.
- Nenhum import de `serial`, `logging` ou `pathlib` no domínio Python.
- A aplicação conhece intenções de ação, mas não APIs concretas do Windows.
- Suporte futuro ao Pico será outro adaptador/perfil, não condicionais espalhadas.

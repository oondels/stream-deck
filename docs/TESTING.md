# Estratégia de testes

## Pirâmide

1. Testes unitários determinísticos de domínio.
2. Testes de aplicação com fakes das portas.
3. Testes de adaptadores com serial e arquivos simulados.
4. Validação manual integrada no hardware e Windows.

## Firmware

- Debounce aceita uma transição somente depois de 30 ms estáveis.
- Press/release não se repetem enquanto o estado permanece igual.
- Encoder reconhece sequência completa horária e anti-horária.
- Transição inválida do encoder não gera evento.
- Publicação atribui `seq` crescente e `uptime_ms` recebido do relógio.
- Probe v1 produz hello; entrada inválida não bloqueia a próxima mensagem.

As regras puras serão compiladas pelo ambiente `native`; testes dependentes do
Arduino ficam restritos à integração no alvo.

## Aplicativo

- Valida hello e todos os controles/eventos permitidos.
- Rejeita tipos incorretos, campos ausentes e versão incompatível.
- Reconstrói linhas recebidas em fragmentos.
- Descobre por handshake, respeita override e fecha portas rejeitadas.
- Detecta salto e regressão de sequência.
- Retorna à descoberta depois de erro de leitura.
- Emite o mesmo evento para console e arquivo estruturado.
- Rotaciona o arquivo nos limites configurados.

## Validação manual

1. Conectar o deck e iniciar o monitor em modo automático.
2. Acionar individualmente as sete teclas.
3. Girar o encoder lentamente nos dois sentidos e clicar.
4. Confirmar um par press/release por botão e um rotate por passo.
5. Remover e recolocar a USB; confirmar reconexão sem reiniciar o monitor.
6. Comparar console e JSONL.
7. Deixar eventos suficientes para provocar rotação em configuração de teste.

## Gate de conclusão

- Documentação internamente consistente.
- `pio run` e `pio test -e native` aprovados.
- `pytest` aprovado.
- Validação manual documentada; se não houver hardware disponível, marcar
  explicitamente como pendente, sem declarar o MVP fisicamente validado.

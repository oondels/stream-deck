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
- Valida bindings e rejeita ações inseguras ou incompatíveis.
- Resolve eventos e mantém ações em fila FIFO sem bloquear a serial.
- Simula `SendInput`, abertura de processos e URLs sem depender de Windows.
- Suprime ações para sequências duplicadas ou regressivas.
- Valida migração, persistência atômica, perfis e importação/exportação.
- Testa widgets Qt em modo offscreen, troca de perfil e fluxo de eventos.

## Validação manual

1. Conectar o deck e iniciar o monitor em modo automático.
2. Acionar individualmente as sete teclas.
3. Girar o encoder lentamente nos dois sentidos e clicar.
4. Confirmar um par press/release por botão e um rotate por passo.
5. Remover e recolocar a USB; confirmar reconexão sem reiniciar o monitor.
6. Comparar console e JSONL.
7. Deixar eventos suficientes para provocar rotação em configuração de teste.

## Validação manual das ações

### Linux

1. Fechar o monitor serial do PlatformIO.
2. Iniciar o app com `--dry-run-actions`.
3. Acionar todos os controles e confirmar `input` seguido de `action_dry_run`.
4. Confirmar que eventos `release` sem binding não geram ação.

### Windows

1. Confirmar faixa anterior, play/pause, próxima faixa e parar nas teclas 1–4.
2. Confirmar `Win+D`, Calculadora e YouTube nas teclas 5–7.
3. Confirmar volume e mudo pelo encoder, uma ação por evento.
4. Remover e recolocar a USB e repetir uma ação sem reiniciar o host.
5. Provocar uma ação inválida e confirmar que eventos posteriores continuam.

## Gate de conclusão

- Documentação internamente consistente.
- `pio run -e esp32dev`, `pio run -e esp32c3` e `pio test -e native` aprovados.
- `pytest` aprovado.
- Dry-run físico no Linux aprovado.
- Validação real das APIs de ação no Windows documentada; se não houver Windows
  disponível, marcar explicitamente como pendente.
- Checklist manual da GUI em `docs/GUI.md` aprovado no Windows antes da release.

# Implementação da GUI

Este arquivo é o ponto de retomada da etapa 3. Uma tarefa só deve ser marcada
como concluída depois que seus testes associados passarem.

## Estado

- Branch: `agent/gui-management`
- Plataforma de produto: Windows 10/11 64-bit
- Framework: PySide6/Qt
- Idioma/tema: PT-BR, escuro
- Configuração: `%APPDATA%\StreamDeckMini\config.json`

## Etapas

- [x] 1. Fundações do pacote GUI
  - [x] dependências opcionais `gui` e `build`
  - [x] entrypoint `streamdeck-gui`
  - [x] estrutura de módulos sem acoplar domínio ao Qt
- [x] 2. Configuração v2 e perfis
  - [x] modelos de perfil e aparência dos controles
  - [x] repositório AppData com escrita atômica e backup
  - [x] migração/importação do JSON legado
  - [x] importação/exportação de perfil e backup completo
  - [x] testes de validação, migração e persistência
- [x] 3. Runtime atualizável
  - [x] cancelamento cooperativo do monitor
  - [x] troca thread-safe de bindings e perfil
  - [x] pausa de ações e teste manual
  - [x] estados de conexão e stream de eventos para a GUI
  - [x] testes de concorrência, reconexão e encerramento
- [x] 4. Interface principal
  - [x] janela, navegação e tema escuro
  - [x] deck 3 teclas + encoder / 4 teclas
  - [x] metadados de nome, ícone e cor
  - [x] editores de press/release e encoder
  - [x] formulários de mídia, hotkey, aplicativo e URL
  - [x] gestão manual de perfis
- [x] 5. Operação Windows
  - [x] status do dispositivo e eventos recentes
  - [x] configurações básicas e avançadas
  - [x] bandeja e pausa/troca de perfil
  - [x] instância única
  - [x] autostart opcional por HKCU
- [ ] 6. Distribuição e aceite
  - [ ] assets e ícone do aplicativo
  - [ ] PyInstaller `onedir` sem console
  - [ ] testes Qt com `pytest-qt`
  - [ ] build/testes existentes sem regressão
  - [ ] documentação de uso e checklist manual Windows

## Decisões fixadas

- A GUI controla um único deck e substitui o monitor de terminal no uso normal.
- Perfis são manuais e aplicados imediatamente, sem desconectar o dispositivo.
- O catálogo de ações permanece mídia/volume, hotkey, aplicativo e URL.
- Firmware, GPIO e debounce são apenas informativos.
- Fechar a janela envia o aplicativo para a bandeja; sair pelo menu encerra.
- A primeira execução cria o perfil multimídia padrão.
- O CLI atual e configurações legadas continuam compatíveis.

## Como retomar

1. Conferir `git status -sb` e preservar mudanças não relacionadas.
2. Ler este arquivo e localizar a primeira caixa não marcada.
3. Executar os testes da última etapa concluída antes de continuar.
4. Atualizar este checklist no mesmo commit da etapa implementada.

## Última validação

- 2026-08-06: etapas 1 a 5 concluídas; `71 passed` no host e `ruff check`
  aprovado.

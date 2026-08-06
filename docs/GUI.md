# Interface gráfica

A interface gráfica é o modo normal de operação do Stream Deck Mini no Windows
10/11 64-bit. Ela é o único processo que deve abrir a porta serial: feche o
monitor do PlatformIO e qualquer instância do monitor CLI antes de iniciá-la.

## Executar em desenvolvimento

No PowerShell, a partir da raiz do repositório:

```powershell
py -3.12 -m venv host_app\.venv
host_app\.venv\Scripts\Activate.ps1
python -m pip install -e "host_app[gui]"
streamdeck-gui
```

Também é possível executar:

```powershell
python -m streamdeck_monitor.gui.bootstrap
```

Na primeira abertura, o arquivo
`%APPDATA%\StreamDeckMini\config.json` é criado com o perfil multimídia padrão.
O backup automático da versão anterior fica em `config.json.bak`.

## Uso

1. Conecte o ESP32 com o firmware gravado e aguarde o status `Conectado`.
2. Selecione um perfil na coluna esquerda.
3. Clique em uma tecla ou no encoder representado no centro.
4. Defina nome, ícone e cor do controle.
5. Escolha o evento e sua ação. Alterações válidas são salvas e aplicadas
   imediatamente, sem reconectar o deck.
6. Use `Testar ação` para executar a ação selecionada sem pressionar o hardware.

Teclas oferecem `Pressionar` e `Soltar`. O encoder oferece giro horário, giro
anti-horário, pressionar e soltar. Uma ação pode controlar mídia/volume, enviar
um atalho, abrir um aplicativo, abrir uma URL ou ficar desativada.

Os perfis são ativados manualmente e podem ser criados, duplicados, renomeados,
excluídos, importados ou exportados. O menu `Arquivo` também exporta e restaura
um backup completo.

## Eventos e configurações

A aba `Eventos` mostra conexão, entradas, execução de ações e erros. O filtro
aceita texto e nível de log. Uma entrada física destaca temporariamente seu
controle no desenho do deck.

Em `Arquivo > Configurações` é possível fixar uma porta `COM`, ajustar tempos de
reconexão, nível de log, limite de eventos, comportamento da bandeja e início
automático. Deixe a porta como `auto` para descoberta por handshake.

Fechar a janela envia o aplicativo para a bandeja quando essa opção está ativa.
O menu da bandeja permite abrir a janela, pausar ações, trocar o perfil e sair.
Uma segunda execução apenas traz a instância existente para frente.

## Gerar a distribuição Windows

No PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File host_app\scripts\build_gui.ps1
```

O resultado `onedir`, sem console, fica em
`host_app\dist\StreamDeckMini\StreamDeckMini.exe`. Copie a pasta inteira para
outra máquina; esta etapa não cria instalador.

## Checklist manual de aceite no Windows

- [ ] O aplicativo abre sem console e uma segunda execução ativa a primeira.
- [ ] O ESP32-C3 e o ESP32 DevKit são encontrados no modo automático.
- [ ] As sete teclas destacam o controle correto e executam press/release.
- [ ] Os dois sentidos e o clique do encoder executam a ação correta.
- [ ] Pausar bloqueia ações físicas; `Testar ação` continua funcionando.
- [ ] Trocar de perfil muda os bindings sem desconectar a serial.
- [ ] Remover e recolocar o USB atualiza o status e reconecta.
- [ ] Fechar envia para a bandeja e `Sair` encerra a porta serial.
- [ ] Autostart cria/remove a entrada do usuário e inicia minimizado.
- [ ] Importar/exportar perfil e backup preserva todas as configurações.

## Diagnóstico rápido

- `Procurando dispositivo`: confira cabo de dados, driver e se a porta está
  ocupada por outro processo.
- `invalid_message` ou `sequence_gap`: confira alimentação/cabo; esses eventos
  indicam linha JSON corrompida ou perda de uma mensagem.
- `action_failed`: confira o caminho do executável, a URL ou o atalho; a leitura
  do deck continua ativa.
- Ação não ocorre no terminal com `--dry-run-actions`: esse modo apenas registra
  `action_dry_run`. Use a GUI no Windows para executar a ação real.

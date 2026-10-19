"""Player-facing words in the player's language: English, Spanish or Portuguese.

The language comes from PADMINT_LANG (en, es, pt), then the system: the Windows
display language, or LC_ALL / LC_MESSAGES / LANG on Mac, Linux and in Termux.
A missing translation falls back to English. Technical lines (file paths, build
logs, error details) stay as they are: they are what someone helping the player
needs to read.
"""
import ctypes
import os
import sys

LANGUAGES = ("en", "es", "pt")
# Windows primary language IDs (the low 10 bits of a LANGID).
WINDOWS_LANGUAGES = {0x0A: "es", 0x16: "pt"}

MESSAGES = {
    "intro": {
        "en": "PadMint {version}: make your own copy of a game from your own game file.",
        "es": "PadMint {version}: crea tu propia copia de un juego a partir de tu propio archivo del juego.",
        "pt": "PadMint {version}: crie sua própria cópia de um jogo a partir do seu próprio arquivo do jogo.",
    },
    "drag_or_choose": {
        "en": "Drag your game file into this window, then press Enter (no file? just press Enter to choose a game): ",
        "es": "Arrastra tu archivo del juego a esta ventana y pulsa Enter (¿sin archivo? pulsa Enter para elegir un juego): ",
        "pt": "Arraste o arquivo do jogo para esta janela e pressione Enter (sem arquivo? pressione Enter para escolher um jogo): ",
    },
    "drag_again": {
        "en": "Drag the file again, or press Enter to choose a game: ",
        "es": "Arrastra el archivo de nuevo, o pulsa Enter para elegir un juego: ",
        "pt": "Arraste o arquivo de novo, ou pressione Enter para escolher um jogo: ",
    },
    "game": {"en": "Game", "es": "Juego", "pt": "Jogo"},
    "make_it_for": {"en": "Make it for", "es": "Crear para", "pt": "Criar para"},
    "number": {"en": "Number: ", "es": "Número: ", "pt": "Número: "},
    "menu_range": {
        "en": "Enter a menu number from 1 to {count}.",
        "es": "Escribe un número del menú, del 1 al {count}.",
        "pt": "Digite um número do menu, de 1 a {count}.",
    },
    "android": {"en": "Android phone or tablet", "es": "Teléfono o tableta Android",
                "pt": "Celular ou tablet Android"},
    "ios_mac": {"en": "iPhone or iPad", "es": "iPhone o iPad", "pt": "iPhone ou iPad"},
    "ios_off_mac": {"en": "iPhone or iPad (experimental)", "es": "iPhone o iPad (experimental)",
                    "pt": "iPhone ou iPad (experimental)"},
    "windows_here": {"en": "This Windows PC (experimental)", "es": "Este PC con Windows (experimental)",
                     "pt": "Este PC com Windows (experimental)"},
    "mac_here": {"en": "This Mac", "es": "Este Mac", "pt": "Este Mac"},
    "drag_game_file": {
        "en": "Drag your own {name} game file into this window, then press Enter: ",
        "es": "Arrastra tu propio archivo del juego {name} a esta ventana y pulsa Enter: ",
        "pt": "Arraste o seu próprio arquivo do jogo {name} para esta janela e pressione Enter: ",
    },
    "type_game_file": {
        "en": "Type the path of your own {name} game file, then press Enter: ",
        "es": "Escribe la ruta de tu propio archivo del juego {name} y pulsa Enter: ",
        "pt": "Digite o caminho do seu próprio arquivo do jogo {name} e pressione Enter: ",
    },
    "no_file": {"en": "No file at {path}", "es": "No hay ningún archivo en {path}",
                "pt": "Nenhum arquivo em {path}"},
    "reading_file": {"en": "Reading your file…", "es": "Leyendo tu archivo…", "pt": "Lendo seu arquivo…"},
    "game_from_file": {
        "en": "Game: {name} (from your file, {game_id})",
        "es": "Juego: {name} (según tu archivo, {game_id})",
        "pt": "Jogo: {name} (pelo seu arquivo, {game_id})",
    },
    "saved_in": {
        "en": "Your copy will be saved in {folder}",
        "es": "Tu copia se guardará en {folder}",
        "pt": "Sua cópia será salva em {folder}",
    },
    "plan": {
        "en": ("\nWhat happens now. Keep this window open; you can use your computer meanwhile.\n"
               "  1. PadMint downloads the free build tools it needs. First time only.\n"
               "  2. It builds your copy on this computer. The first time usually takes\n"
               "     a few minutes to a few hours, depending on the computer.\n"
               "  3. When it finishes, this window tells you exactly what to do next.\n"
               "Lots of text will scroll by. That is normal.\n"),
        "es": ("\nQué pasa ahora. Deja esta ventana abierta; puedes usar tu computadora mientras tanto.\n"
               "  1. PadMint descarga las herramientas gratuitas que necesita. Solo la primera vez.\n"
               "  2. Crea tu copia en esta computadora. La primera vez suele tardar\n"
               "     de unos minutos a unas horas, según la computadora.\n"
               "  3. Al terminar, esta ventana te dice exactamente qué hacer.\n"
               "Verás pasar mucho texto. Es normal.\n"),
        "pt": ("\nO que acontece agora. Deixe esta janela aberta; você pode usar o computador enquanto isso.\n"
               "  1. O PadMint baixa as ferramentas gratuitas de que precisa. Só na primeira vez.\n"
               "  2. Ele cria sua cópia neste computador. Na primeira vez costuma levar\n"
               "     de alguns minutos a algumas horas, dependendo do computador.\n"
               "  3. Ao terminar, esta janela mostra exatamente o que fazer.\n"
               "Muito texto vai passar na tela. Isso é normal.\n"),
    },
    "step_tools": {
        "en": "\nStep 1 of 3: build tools (downloaded the first time only).",
        "es": "\nPaso 1 de 3: herramientas de compilación (se descargan solo la primera vez).",
        "pt": "\nEtapa 1 de 3: ferramentas de compilação (baixadas só na primeira vez).",
    },
    "downloading": {
        "en": "  downloading {name} {version} from {host}",
        "es": "  descargando {name} {version} desde {host}",
        "pt": "  baixando {name} {version} de {host}",
    },
    "percent": {"en": "    {percent}% of {size} GB", "es": "    {percent}% de {size} GB",
                "pt": "    {percent}% de {size} GB"},
    "unpacking": {
        "en": "  unpacking {name}. This can take several minutes, especially on Windows; it is not stuck.",
        "es": "  descomprimiendo {name}. Puede tardar varios minutos, sobre todo en Windows; no está bloqueado.",
        "pt": "  descompactando {name}. Pode levar vários minutos, principalmente no Windows; não travou.",
    },
    "tool_ready": {"en": "ok   {name} {version}", "es": "listo {name} {version}",
                   "pt": "pronto {name} {version}"},
    "tool_got": {"en": "got  {name} {version}", "es": "listo {name} {version}",
                 "pt": "pronto {name} {version}"},
    "published_app": {
        "en": "Downloading the published {name}",
        "es": "Descargando la app publicada {name}",
        "pt": "Baixando o app publicado {name}",
    },
    "step_build": {
        "en": ("\nStep 2 of 3: building your copy with {jobs} parallel jobs. The first build usually\n"
               "takes a few minutes to a few hours; later builds reuse finished work. Keep this window open."),
        "es": ("\nPaso 2 de 3: creando tu copia con {jobs} tareas en paralelo. La primera vez suele\n"
               "tardar de unos minutos a unas horas; las siguientes reutilizan lo ya hecho. Deja esta ventana abierta."),
        "pt": ("\nEtapa 2 de 3: criando sua cópia com {jobs} tarefas em paralelo. A primeira vez costuma\n"
               "levar de alguns minutos a algumas horas; as seguintes reaproveitam o que já foi feito. Deixe esta janela aberta."),
    },
    "step_next": {
        "en": "\nStep 3 of 3: done! What to do next:",
        "es": "\nPaso 3 de 3: ¡listo! Qué hacer ahora:",
        "pt": "\nEtapa 3 de 3: pronto! O que fazer agora:",
    },
    "next_link": {"en": "Next: {guide}", "es": "Siguiente paso: {guide}", "pt": "Próximo passo: {guide}"},
    "platform_android": {"en": "Android", "es": "Android", "pt": "Android"},
    "platform_ios": {"en": "iPhone and iPad", "es": "iPhone y iPad", "pt": "iPhone e iPad"},
    "platform_macos": {"en": "Mac", "es": "Mac", "pt": "Mac"},
    "platform_windows": {"en": "Windows", "es": "Windows", "pt": "Windows"},
    "your_copy": {"en": "Your {name} for {platform}: {path}", "es": "Tu {name} para {platform}: {path}",
                  "pt": "Seu {name} para {platform}: {path}"},
    "keep_private": {
        "en": "It contains game code made from your own copy: keep it to yourself.",
        "es": "Contiene código del juego hecho a partir de tu propia copia: no lo compartas.",
        "pt": "Contém código do jogo feito a partir da sua própria cópia: não compartilhe.",
    },
    "keep_private_compiled": {
        "en": "It contains game code: keep it to yourself.",
        "es": "Contiene código del juego: no lo compartas.",
        "pt": "Contém código do jogo: não compartilhe.",
    },
    "data_exists": {
        "en": "Your {name} game data folder is already at {path}",
        "es": "Tu carpeta de datos del juego de {name} ya está en {path}",
        "pt": "Sua pasta de dados do jogo de {name} já está em {path}",
    },
    "tidied_older": {
        "en": "Freed {size} GB: removed build files left by older versions of {name}.",
        "es": "Se liberaron {size} GB: se quitaron archivos de compilación de versiones anteriores de {name}.",
        "pt": "{size} GB liberados: foram removidos arquivos de compilação de versões anteriores de {name}.",
    },
    "data_saving": {
        "en": "Saving your {name} game data folder (about {size} GB)…",
        "es": "Guardando tu carpeta de datos del juego de {name} (unos {size} GB)…",
        "pt": "Salvando sua pasta de dados do jogo de {name} (cerca de {size} GB)…",
    },
    "data_saved_computer": {
        "en": ("Your {name} game data folder: {path}\n  New to {name}? Copy it to your device and choose it "
               "with {label}. It needs no key."),
        "es": ("Tu carpeta de datos del juego de {name}: {path}\n  ¿Primera vez con {name}? Cópiala a tu "
               "dispositivo y elígela con {label}. No necesita ninguna clave."),
        "pt": ("Sua pasta de dados do jogo de {name}: {path}\n  Primeira vez com {name}? Copie-a para o seu "
               "aparelho e escolha-a com {label}. Não precisa de chave."),
    },
    "data_saved_phone": {
        "en": ("Your {name} game data folder: {path}\n  New to {name}? It is already on this phone; choose it "
               "with {label}. It needs no key."),
        "es": ("Tu carpeta de datos del juego de {name}: {path}\n  ¿Primera vez con {name}? Ya está en este "
               "teléfono; elígela con {label}. No necesita ninguna clave."),
        "pt": ("Sua pasta de dados do jogo de {name}: {path}\n  Primeira vez com {name}? Ela já está neste "
               "celular; escolha-a com {label}. Não precisa de chave."),
    },
    "full_guide": {"en": "Full guide: {guide}", "es": "Guía completa (en inglés): {guide}",
                   "pt": "Guia completo (em inglês): {guide}"},
    "no_build": {"en": "no build needed", "es": "no hace falta crearlo", "pt": "não precisa criar"},
    "download_intro": {
        "en": "\n{name} needs no build: its app contains no game files, and you add your own. To get it:",
        "es": "\nNo hace falta crear {name}: su app no trae archivos del juego y tú añades los tuyos. Para conseguirlo:",
        "pt": "\nNão é preciso criar {name}: o app não traz arquivos do jogo e você adiciona os seus. Para obtê-lo:",
    },
    "build_stopped": {
        "en": ("\nThe build stopped; the lines above say why. For help, post them with your computer "
               "type (Windows, Mac or Linux) at {url}"),
        "es": ("\nLa compilación se detuvo; las líneas de arriba dicen por qué. Para pedir ayuda, "
               "publícalas junto con tu tipo de computadora (Windows, Mac o Linux) en {url}"),
        "pt": ("\nA compilação parou; as linhas acima dizem o motivo. Para pedir ajuda, publique-as "
               "com o tipo do seu computador (Windows, Mac ou Linux) em {url}"),
    },
    # The PadMint window (padmint ui).
    "w_open": {
        "en": ("PadMint {version} is open in your web browser.\nKeep this window open while PadMint works; "
               "close it when you are done.\nIf no browser opened, go to: {url}"),
        "es": ("PadMint {version} está abierto en tu navegador.\nDeja esta ventana abierta mientras PadMint "
               "trabaja; ciérrala cuando termines.\nSi no se abrió el navegador, ve a: {url}"),
        "pt": ("O PadMint {version} está aberto no seu navegador.\nDeixe esta janela aberta enquanto o "
               "PadMint trabalha; feche-a quando terminar.\nSe o navegador não abriu, acesse: {url}"),
    },
    "w_intro": {
        "en": "Make your own copy of a game from your own game file. Everything stays on this device.",
        "es": "Crea tu propia copia de un juego a partir de tu propio archivo del juego. Todo se queda en este dispositivo.",
        "pt": "Crie sua própria cópia de um jogo a partir do seu próprio arquivo do jogo. Tudo fica neste dispositivo.",
    },
    "w_language": {"en": "Language", "es": "Idioma", "pt": "Idioma"},
    "w_game": {"en": "Game", "es": "Juego", "pt": "Jogo"},
    "w_pick_game": {"en": "Choose your game", "es": "Elige tu juego", "pt": "Escolha o seu jogo"},
    "w_no_build": {"en": "No build needed: download the app, add your own files",
                   "es": "No hace falta crearlos: descarga la app y añade tus archivos",
                   "pt": "Não precisam ser criados: baixe o app e adicione seus arquivos"},
    "w_later_head": {"en": "Not available yet", "es": "Todavía no disponibles", "pt": "Ainda não disponíveis"},
    "w_later_note": {"en": "Listed so you can find them. There is nothing to build or download through PadMint yet: choose one to see where it stands.",
                     "es": "Aparecen para que puedas encontrarlos. Todavía no hay nada que crear ni descargar con PadMint: elige uno para ver en qué punto está.",
                     "pt": "Aparecem para que você possa encontrá-los. Ainda não há nada para criar ou baixar pelo PadMint: escolha um para ver em que pé está."},
    "w_tab_build": {"en": "Build with PadMint", "es": "Crear con PadMint", "pt": "Criar com o PadMint"},
    "w_tab_download": {"en": "Download", "es": "Descargar", "pt": "Baixar"},
    "w_flow_1": {"en": "Choose your game", "es": "Elige tu juego", "pt": "Escolha o seu jogo"},
    "w_flow_1s": {"en": "and your own game file", "es": "y tu propio archivo del juego", "pt": "e o seu próprio arquivo do jogo"},
    "w_flow_2": {"en": "PadMint builds it", "es": "PadMint lo crea", "pt": "O PadMint cria"},
    "w_flow_2s": {"en": "on this computer, with free tools", "es": "en esta computadora, con herramientas gratuitas", "pt": "neste computador, com ferramentas gratuitas"},
    "w_flow_3": {"en": "Install and play", "es": "Instala y juega", "pt": "Instale e jogue"},
    "w_flow_3s": {"en": "the page tells you how", "es": "la página te dice cómo", "pt": "a página diz como"},
    "w_later_link": {"en": "Read about {name}", "es": "Más sobre {name}", "pt": "Saiba mais sobre {name}"},
    "w_file": {"en": "Your own game file", "es": "Tu propio archivo del juego", "pt": "O seu próprio arquivo do jogo"},
    "w_file_in_app": {
        "en": "{name} asks for your game file inside the app, after you install it. Nothing to choose here.",
        "es": "{name} te pide tu archivo del juego dentro de la app, después de instalarla. Aquí no hay que elegir nada.",
        "pt": "{name} pede o seu arquivo do jogo dentro do app, depois de instalá-lo. Nada para escolher aqui.",
    },
    "w_choose": {"en": "Choose file…", "es": "Elegir archivo…", "pt": "Escolher arquivo…"},
    "w_found": {"en": "Game files in {folder}:", "es": "Archivos de juegos en {folder}:",
                "pt": "Arquivos de jogos em {folder}:"},
    "w_type": {"en": "Or type or paste the file's full path:", "es": "O escribe o pega la ruta completa del archivo:",
               "pt": "Ou digite ou cole o caminho completo do arquivo:"},
    "w_use": {"en": "Use", "es": "Usar", "pt": "Usar"},
    "w_file_ok": {"en": "Selected: {file}", "es": "Seleccionado: {file}", "pt": "Selecionado: {file}"},
    "w_wrong_game": {"en": "This file is not a {name} game file.", "es": "Este archivo no es del juego {name}.",
                     "pt": "Este arquivo não é do jogo {name}."},
    "w_not_game_file": {
        "en": "{file} is not a game file. {name} needs your own game file ({formats}), not the app.",
        "es": "{file} no es un archivo del juego. {name} necesita tu propio archivo del juego ({formats}), no la app.",
        "pt": "{file} não é um arquivo do jogo. {name} precisa do seu próprio arquivo do jogo ({formats}), não do app.",
    },
    "w_device": {"en": "Make it for", "es": "Crear para", "pt": "Criar para"},
    "w_make": {"en": "Make my copy", "es": "Crear mi copia", "pt": "Criar minha cópia"},
    "w_time": {
        "en": ("The first build usually takes a few minutes to a few hours. Keep this page and PadMint open "
               "(its window, or Termux on a phone); you can do other things meanwhile."),
        "es": ("La primera vez suele tardar de unos minutos a unas horas. Deja abiertos esta página y PadMint "
               "(su ventana, o Termux en un teléfono); mientras tanto puedes hacer otras cosas."),
        "pt": ("A primeira vez costuma levar de alguns minutos a algumas horas. Deixe esta página e o PadMint "
               "abertos (a janela dele, ou o Termux no celular); enquanto isso, você pode fazer outras coisas."),
    },
    "w_step_tools": {"en": "Step 1 of 3: getting the free build tools (first time only)",
                     "es": "Paso 1 de 3: descargando las herramientas gratuitas (solo la primera vez)",
                     "pt": "Etapa 1 de 3: baixando as ferramentas gratuitas (só na primeira vez)"},
    "w_step_build": {"en": "Step 2 of 3: building your copy", "es": "Paso 2 de 3: creando tu copia",
                     "pt": "Etapa 2 de 3: criando sua cópia"},
    "w_step_done": {"en": "Step 3 of 3: done!", "es": "Paso 3 de 3: ¡listo!", "pt": "Etapa 3 de 3: pronto!"},
    "w_starting": {"en": "Starting…", "es": "Empezando…", "pt": "Começando…"},
    "w_elapsed": {"en": "Time so far", "es": "Tiempo transcurrido", "pt": "Tempo até agora"},
    "w_now": {"en": "Now", "es": "Ahora", "pt": "Agora"},
    "w_cancel": {"en": "Cancel", "es": "Cancelar", "pt": "Cancelar"},
    "w_cancelled": {
        "en": "Cancelled. Finished work is kept, so the next try is faster.",
        "es": "Cancelado. Lo ya hecho se conserva, así que el siguiente intento será más rápido.",
        "pt": "Cancelado. O que já foi feito fica guardado, então a próxima tentativa é mais rápida.",
    },
    "w_details": {"en": "Details", "es": "Detalles", "pt": "Detalhes"},
    "w_copy": {"en": "Copy details", "es": "Copiar detalles", "pt": "Copiar detalhes"},
    "w_copied": {"en": "Copied", "es": "Copiado", "pt": "Copiado"},
    "w_failed": {
        "en": ("The build stopped. The details below say why. For help, copy them and post them with "
               "your computer type (Windows, Mac or Linux) at"),
        "es": ("La compilación se detuvo. Los detalles de abajo dicen por qué. Para pedir ayuda, cópialos "
               "y publícalos junto con tu tipo de computadora (Windows, Mac o Linux) en"),
        "pt": ("A compilação parou. Os detalhes abaixo dizem o motivo. Para pedir ajuda, copie-os e "
               "publique-os com o tipo do seu computador (Windows, Mac ou Linux) em"),
    },
    "w_show": {"en": "Show in folder", "es": "Mostrar en la carpeta", "pt": "Mostrar na pasta"},
    "w_next": {"en": "What to do next:", "es": "Qué hacer ahora:", "pt": "O que fazer agora:"},
    "w_guide": {"en": "Full guide", "es": "Guía completa (en inglés)", "pt": "Guia completo (em inglês)"},
    "w_again": {"en": "Make another copy", "es": "Crear otra copia", "pt": "Criar outra cópia"},
    "w_none": {"en": "No game can be made on this computer yet.",
               "es": "Todavía no se puede crear ningún juego en esta computadora.",
               "pt": "Ainda não é possível criar nenhum jogo neste computador."},

    "w_trust_local": {"en": "Runs only on this computer", "es": "Funciona solo en esta computadora",
                      "pt": "Funciona só neste computador"},
    "w_trust_upload": {"en": "Nothing is uploaded", "es": "No se sube nada", "pt": "Nada é enviado"},
    "w_trust_open": {"en": "Free, open-source tools", "es": "Herramientas libres y gratuitas",
                     "pt": "Ferramentas livres e gratuitas"},
    "w_how_title": {"en": "How PadMint works", "es": "Cómo funciona PadMint", "pt": "Como o PadMint funciona"},
    "w_how_1": {"en": "You choose a game, your own game file and the device you'll play on.",
                "es": "Eliges un juego, tu propio archivo del juego y el dispositivo en el que vas a jugar.",
                "pt": "Você escolhe um jogo, o seu próprio arquivo do jogo e o aparelho em que vai jogar."},
    "w_how_2": {"en": "PadMint downloads that game's source code and the free build tools it needs, once. Each download is checked against a known checksum.",
                "es": "PadMint descarga el código fuente de ese juego y las herramientas gratuitas que necesita, una sola vez. Cada descarga se comprueba con una suma de verificación conocida.",
                "pt": "O PadMint baixa o código-fonte desse jogo e as ferramentas gratuitas de que ele precisa, uma vez só. Cada download é conferido com uma soma de verificação conhecida."},
    "w_how_3": {"en": "It downloads the game's published app, which has no game code in it.",
                "es": "Descarga la app publicada del juego, que no trae código del juego.",
                "pt": "Baixa o app publicado do jogo, que não traz código do jogo."},
    "w_how_4": {"en": "It makes the game part from your file, on this computer, and adds it to the app. Your file is never uploaded.",
                "es": "Crea la parte del juego a partir de tu archivo, en esta computadora, y la añade a la app. Tu archivo nunca se sube.",
                "pt": "Cria a parte do jogo a partir do seu arquivo, neste computador, e a adiciona ao app. O seu arquivo nunca é enviado."},
    "w_how_5": {"en": "It saves your copy in your Downloads folder and tells you how to install it.",
                "es": "Guarda tu copia en tu carpeta Descargas y te dice cómo instalarla.",
                "pt": "Salva a sua cópia na pasta Downloads e diz como instalá-la."},
    "w_why_title": {"en": "Why do I need this?", "es": "¿Por qué hace falta esto?", "pt": "Por que preciso disto?"},
    "w_why_1": {"en": "Most of these apps are published without the game, because the game belongs to its publisher. PadMint makes the game part from the copy you own, on your own computer, so nobody has to share the game itself.",
                "es": "La mayoría de estas apps se publican sin el juego, porque el juego pertenece a su editor. PadMint crea la parte del juego a partir de la copia que tienes, en tu propia computadora, para que nadie tenga que compartir el juego en sí.",
                "pt": "A maioria destes apps é publicada sem o jogo, porque o jogo pertence à sua editora. O PadMint cria a parte do jogo a partir da cópia que você tem, no seu próprio computador, para que ninguém precise compartilhar o jogo em si."},
    "w_why_2": {"en": "The copy PadMint makes is yours alone: keep it to yourself. Some games, such as KartPad, also offer ready-to-play downloads; the game's card says so when it does.",
                "es": "La copia que crea PadMint es solo tuya: no la compartas. Algunos juegos, como KartPad, también tienen descargas listas para jugar; la tarjeta del juego lo indica cuando es así.",
                "pt": "A cópia que o PadMint cria é só sua: não a compartilhe. Alguns jogos, como o KartPad, também têm downloads prontos para jogar; o cartão do jogo avisa quando é o caso."},
    "w_step1": {"en": "1. Choose a game", "es": "1. Elige un juego", "pt": "1. Escolha um jogo"},
    "w_step2": {"en": "Your own game file", "es": "Tu propio archivo del juego",
                "pt": "O seu próprio arquivo do jogo"},
    "w_step3": {"en": "Where will you play?", "es": "¿Dónde vas a jugar?", "pt": "Onde você vai jogar?"},
    "w_dl_tag": {"en": "Download the app", "es": "Descarga la app", "pt": "Baixe o app"},
    "w_home": {"en": "PadMint: all games", "es": "PadMint: todos los juegos", "pt": "PadMint: todos os jogos"},
    "w_search": {"en": "Search games", "es": "Buscar juegos", "pt": "Buscar jogos"},
    "w_builds": {"en": "Made on this computer from your game file", "es": "Se crean en esta computadora con tu archivo del juego",
                 "pt": "Criados neste computador com o seu arquivo do jogo"},
    "w_ready_tag": {"en": "{devices}: ready-to-play app", "es": "{devices}: app lista para jugar", "pt": "{devices}: app pronto para jogar"},
    "w_ready_title": {"en": "There's a ready-to-play download", "es": "Hay una descarga lista para jugar",
                      "pt": "Há um download pronto para jogar"},
    "w_ready_link": {"en": "Download the {devices} app", "es": "Descargar la app para {devices}", "pt": "Baixar o app para {devices}"},
    "w_ready_or": {"en": "Then keep going below: PadMint makes what the app needs from your game file.",
                   "es": "Luego sigue abajo: PadMint crea lo que la app necesita a partir de tu archivo del juego.",
                   "pt": "Depois continue abaixo: o PadMint cria o que o app precisa a partir do seu arquivo do jogo."},
    "w_file_hint": {"en": "Your own copy of {game}.", "es": "Tu propia copia de {game}.", "pt": "A sua própria cópia de {game}."},
    "w_file_formats": {"en": "File types: {formats}", "es": "Tipos de archivo: {formats}", "pt": "Tipos de arquivo: {formats}"},
    "w_file_region": {"en": "Only the {region} version works.", "es": "Solo funciona la versión {region}.",
                      "pt": "Só funciona a versão {region}."},
    "w_region_us": {"en": "US (North American)", "es": "de EE. UU. (Norteamérica)", "pt": "dos EUA (América do Norte)"},
    "w_region_eu": {"en": "European (PAL)", "es": "europea (PAL)", "pt": "europeia (PAL)"},
    "w_region_jp": {"en": "Japanese", "es": "japonesa", "pt": "japonesa"},
    "w_which_file": {"en": "Which file? Any one of these:", "es": "¿Qué archivo? Cualquiera de estos:",
                     "pt": "Qual arquivo? Qualquer um destes:"},
    "w_more_file": {"en": "More about this file", "es": "Más sobre este archivo", "pt": "Mais sobre este arquivo"},
    "w_picker_open": {"en": "A window to choose your file has opened. If you don't see it, it may be behind this browser window.",
                      "es": "Se abrió una ventana para elegir tu archivo. Si no la ves, puede estar detrás de esta ventana del navegador.",
                      "pt": "Abriu uma janela para escolher o seu arquivo. Se não a vir, ela pode estar atrás desta janela do navegador."},
    "w_setup_easy": {"en": "Easiest", "es": "Lo más fácil", "pt": "O mais fácil"},
    "w_setup_xcode": {"en": "Needs Xcode", "es": "Necesita Xcode", "pt": "Precisa do Xcode"},
    "w_setup_brew": {"en": "Needs Xcode + Homebrew", "es": "Necesita Xcode + Homebrew", "pt": "Precisa do Xcode + Homebrew"},
    "w_start_note": {"en": "New here? Games you can download are quickest; next easiest are games that only need Xcode.",
                     "es": "¿Es tu primera vez? Lo más rápido son los juegos que se descargan; después, los que solo necesitan Xcode.",
                     "pt": "Primeira vez? O mais rápido são os jogos para baixar; depois, os que só precisam do Xcode."},
    "w_check_again": {"en": "Check again", "es": "Comprobar de nuevo", "pt": "Verificar de novo"},
    "w_only_for": {"en": "(only for {formats} files)", "es": "(solo para archivos {formats})", "pt": "(só para arquivos {formats})"},
    "w_why_device": {"en": "Choose where you'll play (step 3).", "es": "Elige dónde vas a jugar (paso 3).",
                     "pt": "Escolha onde vai jogar (etapa 3)."},
    "w_why_file": {"en": "Choose your game file (step 2).", "es": "Elige tu archivo del juego (paso 2).",
                   "pt": "Escolha o seu arquivo do jogo (etapa 2)."},
    "w_why_reading": {"en": "Checking your game file…", "es": "Comprobando tu archivo del juego…",
                      "pt": "Verificando o seu arquivo do jogo…"},
    "w_why_loading": {"en": "Reading what this game needs…", "es": "Leyendo lo que necesita este juego…",
                      "pt": "Lendo o que este jogo precisa…"},
    "w_why_blocked": {"en": "Install what's marked not found above, then click Check again.",
                      "es": "Instala lo marcado como no encontrado arriba y luego pulsa Comprobar de nuevo.",
                      "pt": "Instale o que está marcado como não encontrado acima e depois clique em Verificar de novo."},
    "w_install_preview": {"en": "After the build: how to install and play", "es": "Después de crear: cómo instalar y jugar",
                          "pt": "Depois de criar: como instalar e jogar"},
    "w_your_copy": {"en": "your copy", "es": "tu copia", "pt": "a sua cópia"},
    "w_the_ipa": {"en": "the .ipa file PadMint saves", "es": "el archivo .ipa que guarda PadMint",
                  "pt": "o arquivo .ipa que o PadMint salva"},
    "w_tools_folder": {"en": "Kept in {folder}", "es": "Se guardan en {folder}", "pt": "Ficam em {folder}"},
    "xcode_install": {
        "en": "Get Xcode, Apple's free app for making iPhone apps, from the App Store: https://apps.apple.com/app/xcode/id497799835 It is a large download. Open Xcode once and, when it asks which platforms to add, include iOS.",
        "es": "Descarga Xcode, la app gratuita de Apple para crear apps de iPhone, desde la App Store: https://apps.apple.com/app/xcode/id497799835 Es una descarga grande. Abre Xcode una vez y, cuando pregunte qué plataformas añadir, incluye iOS.",
        "pt": "Baixe o Xcode, o app gratuito da Apple para criar apps de iPhone, na App Store: https://apps.apple.com/app/xcode/id497799835 É um download grande. Abra o Xcode uma vez e, quando ele perguntar quais plataformas adicionar, inclua o iOS.",
    },
    "xcode_select": {
        "en": "Xcode is installed, but this Mac isn't using it yet. Copy the line below into Terminal (Applications → Utilities), press Return and type your Mac password. Then open Xcode once.",
        "es": "Xcode está instalado, pero este Mac todavía no lo usa. Copia la línea de abajo en Terminal (Aplicaciones → Utilidades), pulsa Retorno y escribe la contraseña de tu Mac. Luego abre Xcode una vez.",
        "pt": "O Xcode está instalado, mas este Mac ainda não o usa. Copie a linha abaixo no Terminal (Aplicativos → Utilitários), pressione Return e digite a senha do seu Mac. Depois abra o Xcode uma vez.",
    },
    "w_file_ids": {"en": "Disc ID {ids}", "es": "ID del disco {ids}", "pt": "ID do disco {ids}"},
    "w_file_code": {"en": "Game code {ids}", "es": "Código del juego {ids}", "pt": "Código do jogo {ids}"},
    "w_stage": {"en": "Current step: {stage}", "es": "Paso actual: {stage}", "pt": "Etapa atual: {stage}"},
    "w_what_you_got": {"en": "What you got", "es": "Lo que obtuviste", "pt": "O que você recebeu"},
    "w_short_android": {"en": "Android", "es": "Android", "pt": "Android"},
    "w_short_ios": {"en": "iPhone/iPad", "es": "iPhone/iPad", "pt": "iPhone/iPad"},
    "w_short_macos": {"en": "Mac", "es": "Mac", "pt": "Mac"},
    "w_short_windows": {"en": "Windows", "es": "Windows", "pt": "Windows"},
    # A device the game's recipe can make but PadMint doesn't offer yet (catalog unoffered_targets).
    "w_held_tag": {"en": "Not yet", "es": "Todavía no", "pt": "Ainda não"},
    "w_needs_apple_silicon": {"en": "Requires Apple Silicon", "es": "Requiere Apple Silicon",
                              "pt": "Requer Apple Silicon"},
    "mac_requires_apple_silicon": {
        "en": "{name} for Mac requires Apple Silicon (M1 or newer). It cannot run on an Intel Mac. You can build a copy for another device listed here.",
        "es": "{name} para Mac requiere Apple Silicon (M1 o posterior). No funciona en un Mac Intel. Puedes crear una copia para otro dispositivo de esta lista.",
        "pt": "O {name} para Mac requer Apple Silicon (M1 ou mais recente). Ele não funciona em um Mac Intel. Você pode criar uma cópia para outro dispositivo desta lista."},
    "held_text": {"en": "PadMint doesn't make {name} for {device} yet. To play it now, choose {others}.",
                  "es": "PadMint todavía no crea {name} para {device}. Para jugar ahora, elige {others}.",
                  "pt": "O PadMint ainda não cria o {name} para {device}. Para jogar agora, escolha {others}."},
    "held_or": {"en": " or ", "es": " o ", "pt": " ou "},
    "w_all": {"en": "All", "es": "Todos", "pt": "Todos"},
    "w_count": {"en": "{count} games", "es": "{count} juegos", "pt": "{count} jogos"},
    "w_no_match": {"en": "No game matches. Try another name.", "es": "Ningún juego coincide. Prueba otro nombre.",
                   "pt": "Nenhum jogo encontrado. Tente outro nome."},
    "w_change": {"en": "← All games", "es": "← Todos los juegos", "pt": "← Todos os jogos"},
    "w_tab_all": {"en": "All games", "es": "Todos los juegos", "pt": "Todos os jogos"},
    "w_your_games": {"en": "Your games", "es": "Tus juegos", "pt": "Seus jogos"},
    "w_library": {"en": "Game library", "es": "Biblioteca de juegos", "pt": "Biblioteca de jogos"},
    "w_built_for": {"en": "Built for {device}", "es": "Creado para {device}", "pt": "Criado para {device}"},
    "w_up_to_date": {"en": "Up to date", "es": "Al día", "pt": "Atualizado"},
    "w_update_to": {"en": "Update to {version}", "es": "Actualizar a {version}", "pt": "Atualizar para {version}"},
    "w_new_version": {"en": "{version} is out", "es": "Ya salió {version}", "pt": "Saiu a {version}"},
    "w_build_again": {"en": "Build again", "es": "Crear de nuevo", "pt": "Criar de novo"},
    "w_checking": {"en": "Checking for updates…", "es": "Buscando actualizaciones…", "pt": "Procurando atualizações…"},
    "w_pm_update": {"en": "PadMint {version} is available", "es": "PadMint {version} está disponible",
                    "pt": "PadMint {version} está disponível"},
    "w_welcome_title": {"en": "Make your first copy", "es": "Crea tu primera copia", "pt": "Crie sua primeira cópia"},
    "w_welcome_text": {"en": "Pick a game below. PadMint builds it on this computer from your own game file, then keeps it here so you can see when an update is ready.",
                       "es": "Elige un juego abajo. PadMint lo crea en este ordenador a partir de tu propio archivo del juego y luego lo guarda aquí para que veas cuándo hay una actualización.",
                       "pt": "Escolha um jogo abaixo. O PadMint o cria neste computador a partir do seu próprio arquivo do jogo e o mantém aqui para você ver quando houver uma atualização."},
    "w_act_build": {"en": "Build", "es": "Crear", "pt": "Criar"},
    "w_act_update": {"en": "Update", "es": "Actualizar", "pt": "Atualizar"},
    "w_act_download": {"en": "Get the app", "es": "Obtener la app", "pt": "Baixar o app"},
    "w_act_later": {"en": "Coming soon", "es": "Próximamente", "pt": "Em breve"},
    "w_in_library": {"en": "In your games", "es": "En tus juegos", "pt": "Nos seus jogos"},
    "w_about_padmint": {"en": "About PadMint", "es": "Acerca de PadMint", "pt": "Sobre o PadMint"},
    "w_latest": {"en": "Latest {version}", "es": "Última: {version}", "pt": "Mais recente: {version}"},
    "w_update_ready": {"en": "1 update ready", "es": "1 actualización lista", "pt": "1 atualização pronta"},
    "w_updates_ready": {"en": "{count} updates ready", "es": "{count} actualizaciones listas", "pt": "{count} atualizações prontas"},
    "w_all_current": {"en": "Everything is up to date", "es": "Todo está al día", "pt": "Tudo está atualizado"},
    "w_show_all": {"en": "Show all {count}", "es": "Mostrar los {count}", "pt": "Mostrar todos os {count}"},
    "w_show_less": {"en": "Show fewer", "es": "Mostrar menos", "pt": "Mostrar menos"},
    "w_change_short": {"en": "Change", "es": "Cambiar", "pt": "Alterar"},
    "w_see_progress": {"en": "See progress", "es": "Ver el progreso", "pt": "Ver o progresso"},
    "w_update_ready_short": {"en": "Update ready", "es": "Actualización lista", "pt": "Atualização pronta"},
    "w_nav_games": {"en": "Games", "es": "Juegos", "pt": "Jogos"},
    "w_nav_storage": {"en": "Storage", "es": "Almacenamiento", "pt": "Armazenamento"},
    "w_sn_library": {"en": "Library", "es": "Biblioteca", "pt": "Biblioteca"},
    "w_sn_mine": {"en": "My games", "es": "Mis juegos", "pt": "Meus jogos"},
    "w_sn_updates": {"en": "Updates", "es": "Actualizaciones", "pt": "Atualizações"},
    "w_sn_browse": {"en": "All games", "es": "Todos los juegos", "pt": "Todos os jogos"},
    "w_sn_devices": {"en": "Devices", "es": "Dispositivos", "pt": "Aparelhos"},
    "w_this_mac": {"en": "This Mac", "es": "Este Mac", "pt": "Este Mac"},
    "w_mine_note": {"en": "Every game PadMint can find on your iPhone, iPad and this Mac, plus the copies it built here.",
                    "es": "Cada juego que PadMint encuentra en tu iPhone, iPad y este Mac, más las copias que creó aquí.",
                    "pt": "Cada jogo que o PadMint encontra no seu iPhone, iPad e neste Mac, mais as cópias que ele criou aqui."},
    "w_updates_note": {"en": "A newer version is out. Updating makes a fresh copy from the latest release; install it the same way as before. Your saves stay on the device.",
                       "es": "Hay una versión más nueva. Actualizar crea una copia nueva a partir de la última versión; instálala igual que antes. Tus partidas se quedan en el dispositivo.",
                       "pt": "Saiu uma versão mais nova. Atualizar cria uma cópia nova a partir da versão mais recente; instale do mesmo jeito que antes. Seus saves ficam no aparelho."},
    "w_mac_note": {"en": "PadMint games in your Applications folder, and Mac copies PadMint built.",
                   "es": "Juegos de PadMint en tu carpeta Aplicaciones y copias para Mac que creó PadMint.",
                   "pt": "Jogos do PadMint na sua pasta Aplicativos e cópias para Mac que o PadMint criou."},
    "w_android_note": {"en": "PadMint can't see what's on an Android phone. These are the Android copies it built on this computer.",
                       "es": "PadMint no puede ver lo que hay en un teléfono Android. Estas son las copias para Android que creó en este ordenador.",
                       "pt": "O PadMint não consegue ver o que há num celular Android. Estas são as cópias para Android que ele criou neste computador."},
    "w_android_unseen": {"en": "PadMint can't check Android phones", "es": "PadMint no puede revisar teléfonos Android", "pt": "O PadMint não consegue verificar celulares Android"},
    "w_device_live": {"en": "Connected", "es": "Conectado", "pt": "Conectado"},
    "w_device_away": {"en": "Not reachable right now", "es": "No disponible ahora", "pt": "Indisponível agora"},
    "w_seen": {"en": "last seen {when}", "es": "visto por última vez {when}", "pt": "visto pela última vez {when}"},
    "w_checked": {"en": "Checked {when}", "es": "Revisado {when}", "pt": "Verificado {when}"},
    "w_checking_devices": {"en": "Looking at your devices…", "es": "Revisando tus dispositivos…", "pt": "Verificando seus aparelhos…"},
    "w_look_again": {"en": "Check again", "es": "Revisar de nuevo", "pt": "Verificar de novo"},
    "w_no_xcode_note": {"en": "To see which games are on your iPhone or iPad, install Xcode and connect the device to this Mac once.",
                        "es": "Para ver qué juegos tienes en tu iPhone o iPad, instala Xcode y conecta el dispositivo a este Mac una vez.",
                        "pt": "Para ver quais jogos estão no seu iPhone ou iPad, instale o Xcode e conecte o aparelho a este Mac uma vez."},
    "w_sec_updates": {"en": "Updates available", "es": "Actualizaciones disponibles", "pt": "Atualizações disponíveis"},
    "w_sec_current": {"en": "On the latest version", "es": "En la última versión", "pt": "Na versão mais recente"},
    "w_sec_all": {"en": "All on the latest version", "es": "Todos en la última versión", "pt": "Todos na versão mais recente"},
    "w_latest_short": {"en": "Latest", "es": "Al día", "pt": "Atualizado"},
    "w_no_updates": {"en": "Everything is on the latest version.", "es": "Todo está en la última versión.", "pt": "Tudo está na versão mais recente."},
    "w_empty_mine": {"en": "No games yet. Open All games to make your first copy.", "es": "Aún no hay juegos. Abre Todos los juegos para crear tu primera copia.", "pt": "Ainda não há jogos. Abra Todos os jogos para criar sua primeira cópia."},
    "w_empty_device": {"en": "No PadMint games here yet.", "es": "Aún no hay juegos de PadMint aquí.", "pt": "Ainda não há jogos do PadMint aqui."},
    "w_your_copies": {"en": "Your copies", "es": "Tus copias", "pt": "Suas cópias"},
    "w_built_copy": {"en": "Built for {device}, not installed", "es": "Creada para {device}, sin instalar", "pt": "Criada para {device}, não instalada"},
    "w_built_when": {"en": "built {when}", "es": "creada {when}", "pt": "criada {when}"},
    "w_not_on_devices": {"en": "not found on your devices", "es": "no está en tus dispositivos", "pt": "não está nos seus aparelhos"},
    "w_version_unknown": {"en": "version not shown", "es": "versión no indicada", "pt": "versão não informada"},
    "w_in_apps": {"en": "in Applications", "es": "en Aplicaciones", "pt": "em Aplicativos"},
    "w_installed": {"en": "Installed", "es": "Instalado", "pt": "Instalado"},
    "w_built_short": {"en": "Built", "es": "Creado", "pt": "Criado"},

    "w_hero_title": {"en": "Classic games, rebuilt as native apps for your devices", "es": "Juegos clásicos, convertidos en apps nativas para tus dispositivos", "pt": "Jogos clássicos, refeitos como apps nativos para os seus aparelhos"},
    "w_hero_text": {"en": "PadMint builds free, open-source game ports made by Kahris for iPhone, iPad, Mac and Android. You bring a game you own; PadMint makes your copy on this computer.",
                    "es": "PadMint crea los ports de juegos gratuitos y de código abierto hechos por Kahris para iPhone, iPad, Mac y Android. Tú pones un juego que tienes; PadMint crea tu copia en este ordenador.",
                    "pt": "O PadMint cria os ports de jogos gratuitos e de código aberto feitos por Kahris para iPhone, iPad, Mac e Android. Você traz um jogo que tem; o PadMint faz a sua cópia neste computador."},
    "w_intro_1": {"en": "Pick a game", "es": "Elige un juego", "pt": "Escolha um jogo"},
    "w_intro_2": {"en": "Choose your own game file", "es": "Elige tu propio archivo del juego", "pt": "Escolha o seu próprio arquivo do jogo"},
    "w_intro_3": {"en": "PadMint builds it and shows how to install it", "es": "PadMint lo crea y te dice cómo instalarlo", "pt": "O PadMint cria e mostra como instalar"},
    "w_learn_more": {"en": "How it works and why", "es": "Cómo funciona y por qué", "pt": "Como funciona e por quê"},
    "w_who_title": {"en": "Made by", "es": "Hecho por", "pt": "Feito por"},
    "w_who_text": {"en": "PadMint and every port in it are free and open source. Each port is its own app for touch screens and controllers. None of them include the original game: that part always comes from your own copy.",
                   "es": "PadMint y todos sus ports son gratuitos y de código abierto. Cada port es su propia app para pantallas táctiles y mandos. Ninguno incluye el juego original: esa parte siempre sale de tu propia copia.",
                   "pt": "O PadMint e todos os seus ports são gratuitos e de código aberto. Cada port é seu próprio app para telas de toque e controles. Nenhum inclui o jogo original: essa parte sempre vem da sua própria cópia."},
    "w_up_title": {"en": "PadMint {version} is ready", "es": "PadMint {version} está listo", "pt": "PadMint {version} está pronto"},
    "w_up_text": {"en": "PadMint downloads it from GitHub, checks it against the release's checksums and restarts. Your games, tools and builds stay where they are.",
                  "es": "PadMint lo descarga de GitHub, lo comprueba con las sumas de verificación de la versión y se reinicia. Tus juegos, herramientas y compilaciones se quedan donde están.",
                  "pt": "O PadMint baixa do GitHub, confere com as somas de verificação da versão e reinicia. Seus jogos, ferramentas e compilações ficam onde estão."},
    "w_up_now": {"en": "Update now", "es": "Actualizar ahora", "pt": "Atualizar agora"},
    "w_up_short": {"en": "Update", "es": "Actualizar", "pt": "Atualizar"},
    "w_up_downloading": {"en": "Downloading… {percent}%", "es": "Descargando… {percent}%", "pt": "Baixando… {percent}%"},
    "w_up_installing": {"en": "Installing…", "es": "Instalando…", "pt": "Instalando…"},
    "w_up_installed": {"en": "PadMint {version} is installed", "es": "PadMint {version} está instalado", "pt": "PadMint {version} está instalado"},
    "w_up_restart": {"en": "Restart PadMint", "es": "Reiniciar PadMint", "pt": "Reiniciar o PadMint"},
    "w_up_restarting": {"en": "Restarting PadMint…", "es": "Reiniciando PadMint…", "pt": "Reiniciando o PadMint…"},
    "w_up_failed": {"en": "The update didn't finish: {error}", "es": "La actualización no terminó: {error}", "pt": "A atualização não terminou: {error}"},
    "w_up_manual": {"en": "Download it from GitHub", "es": "Descárgalo de GitHub", "pt": "Baixe do GitHub"},
    "w_st_intro": {"en": "PadMint keeps each game's source code, its build tools and a few downloads in one folder on this computer. Anything marked safe to remove can go: PadMint downloads it again if a build needs it. Your installed games, game files and saves aren't in this folder.", "es": "PadMint guarda el código de cada juego, sus herramientas y algunas descargas en una carpeta de este ordenador. Lo que esté marcado como que se puede quitar puede irse: PadMint lo vuelve a descargar si una compilación lo necesita. Tus juegos instalados, archivos de juego y partidas no están en esta carpeta.", "pt": "O PadMint guarda o código de cada jogo, as ferramentas e alguns downloads numa pasta deste computador. O que estiver marcado como pode remover pode sair: o PadMint baixa de novo se uma compilação precisar. Seus jogos instalados, arquivos de jogo e saves não ficam nesta pasta."},
    "w_st_calc": {"en": "Measuring PadMint's folder…", "es": "Midiendo la carpeta de PadMint…", "pt": "Medindo a pasta do PadMint…"},
    "w_st_used": {"en": "used in {folder}", "es": "usados en {folder}", "pt": "usados em {folder}"},
    "w_st_free": {"en": "{size} free on this disk", "es": "{size} libres en este disco", "pt": "{size} livres neste disco"},
    "w_st_free_up": {"en": "Free up {size}", "es": "Liberar {size}", "pt": "Liberar {size}"},
    "w_st_nothing": {"en": "Nothing to clean up", "es": "Nada que limpiar", "pt": "Nada para limpar"},
    "w_st_kept_short": {"en": "Kept", "es": "Se conserva", "pt": "Mantido"},
    "w_st_can_go": {"en": "{size} can go", "es": "{size} se pueden quitar", "pt": "{size} podem sair"},
    "w_st_old": {"en": "Older versions of your games", "es": "Versiones anteriores de tus juegos", "pt": "Versões anteriores dos seus jogos"},
    "w_st_old_note": {"en": "When a game updates, PadMint downloads the new version and leaves the old one here. Only the newest is needed. Removing these doesn't affect games installed on your devices.", "es": "Cuando un juego se actualiza, PadMint descarga la versión nueva y deja la anterior aquí. Solo hace falta la más reciente. Quitarlas no afecta a los juegos instalados en tus dispositivos.", "pt": "Quando um jogo atualiza, o PadMint baixa a versão nova e deixa a antiga aqui. Só a mais recente é necessária. Removê-las não afeta os jogos instalados nos seus aparelhos."},
    "w_st_tools": {"en": "Build tools no longer needed", "es": "Herramientas que ya no hacen falta", "pt": "Ferramentas que não são mais necessárias"},
    "w_st_cache": {"en": "App and extra downloads", "es": "Descargas de apps y extras", "pt": "Downloads de apps e extras"},
    "w_st_cache_note": {"en": "Copies of each port's published app (with no game inside) and extras such as mods. If you remove them, PadMint downloads them again the next time you build that game.", "es": "Copias de la app publicada de cada port (sin el juego dentro) y extras como mods. Si las quitas, PadMint las vuelve a descargar la próxima vez que crees ese juego.", "pt": "Cópias do app publicado de cada port (sem o jogo dentro) e extras como mods. Se você remover, o PadMint baixa de novo na próxima vez que criar esse jogo."},
    "w_st_kept": {"en": "Kept: {count} items · {size}", "es": "Se conservan: {count} elementos · {size}", "pt": "Mantidos: {count} itens · {size}"},
    "w_st_kept_note": {"en": "PadMint keeps the newest version of each game and the tools your builds use, so your next build is faster.", "es": "PadMint conserva la versión más reciente de cada juego y las herramientas que usan tus compilaciones, para que la próxima sea más rápida.", "pt": "O PadMint mantém a versão mais recente de cada jogo e as ferramentas que suas compilações usam, para a próxima ser mais rápida."},
    "w_st_remove": {"en": "Remove", "es": "Quitar", "pt": "Remover"},
    "w_st_remove_size": {"en": "Remove {size}", "es": "Quitar {size}", "pt": "Remover {size}"},
    "w_st_removing": {"en": "Removing…", "es": "Quitando…", "pt": "Removendo…"},
    "w_st_cancel": {"en": "Cancel", "es": "Cancelar", "pt": "Cancelar"},
    "w_st_confirm_title": {"en": "Remove {size}?", "es": "¿Quitar {size}?", "pt": "Remover {size}?"},
    "w_st_confirm_text": {"en": "PadMint deletes these folders from {folder}. Installed games, game files and saves are not touched, and anything needed later is downloaded again.", "es": "PadMint borra estas carpetas de {folder}. No toca los juegos instalados, los archivos de juego ni las partidas, y lo que haga falta se vuelve a descargar.", "pt": "O PadMint apaga estas pastas de {folder}. Jogos instalados, arquivos de jogo e saves não são tocados, e o que for preciso depois é baixado de novo."},
    "w_st_freed": {"en": "Freed {size}", "es": "Se liberaron {size}", "pt": "{size} liberados"},
    "w_st_busy": {"en": "Wait for the current build to finish first.", "es": "Espera a que termine la compilación actual.", "pt": "Espere a compilação atual terminar."},
    "w_st_r_old": {"en": "Older version", "es": "Versión anterior", "pt": "Versão anterior"},
    "w_st_r_partial": {"en": "Unfinished download", "es": "Descarga sin terminar", "pt": "Download incompleto"},
    "w_st_r_unused": {"en": "No longer needed", "es": "Ya no hace falta", "pt": "Não é mais necessária"},
    "w_st_r_cache": {"en": "Downloaded again when needed", "es": "Se vuelve a descargar cuando haga falta", "pt": "Baixado de novo quando precisar"},
    "w_st_r_current": {"en": "Kept", "es": "Se conserva", "pt": "Mantido"},

    "w_status_paused": {"en": "Paused", "es": "En pausa", "pt": "Em pausa"},
    "w_status_rebuilding": {"en": "New version in progress", "es": "Nueva versión en camino", "pt": "Nova versão a caminho"},
    "w_status_in_development": {"en": "In development", "es": "En desarrollo", "pt": "Em desenvolvimento"},
    "w_status_alpha": {"en": "Early alpha", "es": "Alfa temprana", "pt": "Alfa inicial"},
    "w_st_in_use": {"en": "In use", "es": "En uso", "pt": "Em uso"},
    "w_st_uninstall": {"en": "Removing PadMint", "es": "Quitar PadMint", "pt": "Remover o PadMint"},
    "w_st_uninstall_text": {"en": "PadMint has no installer. It is the folder you unzipped (or PadMint.app on a Mac) plus {folder}, where it keeps everything it downloads. To remove it, close PadMint, move the PadMint folder to the Trash and delete {folder}. Games on your devices, the copies in your Downloads folder and your saves stay.",
                            "es": "PadMint no tiene instalador. Es la carpeta que descomprimiste (o PadMint.app en un Mac) más {folder}, donde guarda todo lo que descarga. Para quitarlo, cierra PadMint, mueve la carpeta de PadMint a la papelera y borra {folder}. Los juegos de tus dispositivos, las copias de tu carpeta Descargas y tus partidas se quedan.",
                            "pt": "O PadMint não tem instalador. Ele é a pasta que você descompactou (ou o PadMint.app no Mac) mais {folder}, onde guarda tudo o que baixa. Para removê-lo, feche o PadMint, mova a pasta do PadMint para o lixo e apague {folder}. Os jogos dos seus dispositivos, as cópias na pasta Downloads e seus saves continuam."},
    "w_st_safe": {"en": "Safe to remove", "es": "Se puede quitar", "pt": "Pode remover"},
    "w_st_folder_line": {"en": "PadMint's folder ({folder}) · {free} free on this disk", "es": "Carpeta de PadMint ({folder}) · {free} libres en este disco", "pt": "Pasta do PadMint ({folder}) · {free} livres neste disco"},
    "w_st_kind_app": {"en": "{name} app download", "es": "Descarga de la app {name}", "pt": "Download do app {name}"},
    "w_st_kind_extra": {"en": "{name} extra downloads", "es": "Descargas extra de {name}", "pt": "Downloads extras do {name}"},
    "w_st_app_note": {"en": "The published app, with no game inside", "es": "La app publicada, sin el juego dentro", "pt": "O app publicado, sem o jogo dentro"},
    "w_st_extra_note": {"en": "Mods and packs the build adds", "es": "Mods y paquetes que añade la compilación", "pt": "Mods e pacotes que a compilação adiciona"},
    "w_st_kept_sum": {"en": "In use: newest version of {games} games · {tools} build tools · {size}", "es": "En uso: la versión más reciente de {games} juegos · {tools} herramientas · {size}", "pt": "Em uso: a versão mais recente de {games} jogos · {tools} ferramentas · {size}"},
    "w_st_r_newest": {"en": "Newest version · kept", "es": "Versión más reciente · se conserva", "pt": "Versão mais recente · mantida"},
    "w_st_r_tool": {"en": "Build tool · used by your builds", "es": "Herramienta · la usan tus compilaciones", "pt": "Ferramenta · usada pelas suas compilações"},

    "w_st_r_behind": {"en": "Newest you've downloaded · kept · {version} is out", "es": "La más reciente que descargaste · se conserva · ya salió {version}", "pt": "A mais recente que você baixou · mantida · saiu a {version}"},
    "w_get_padmint": {"en": "Download", "es": "Descargar", "pt": "Baixar"},
    "w_plan_loading": {"en": "Reading {name}'s latest release…", "es": "Leyendo la última versión de {name}…", "pt": "Lendo a versão mais recente de {name}…"},
    "w_game_page": {"en": "About {name}: install guide and updates", "es": "Sobre {name}: guía de instalación y novedades", "pt": "Sobre {name}: guia de instalação e novidades"},
    "w_about_title": {"en": "How it works", "es": "Cómo funciona", "pt": "Como funciona"},
    "w_needs_mac_head": {"en": "Needs a Mac", "es": "Necesitan un Mac", "pt": "Precisam de um Mac"},
    "w_needs_mac_note": {"en": "These are built on a Mac with Apple Silicon (M1 or newer). They're listed so you know they exist: choose one to see its options.",
                         "es": "Estos se crean en un Mac con Apple Silicon (M1 o posterior). Aparecen para que sepas que existen: elige uno para ver sus opciones.",
                         "pt": "Estes são criados em um Mac com Apple Silicon (M1 ou mais novo). Aparecem para você saber que existem: escolha um para ver as opções."},
    "w_all_note_off_mac": {"en": "Every game, by name. Dimmed ones are built on a Mac with Apple Silicon: choose one to see why.",
                           "es": "Todos los juegos, por nombre. Los atenuados se crean en un Mac con Apple Silicon: elige uno para ver por qué.",
                           "pt": "Todos os jogos, por nome. Os esmaecidos são criados em um Mac com Apple Silicon: escolha um para ver por quê."},
    "w_tab_missing": {"en": "Not installed", "es": "Sin instalar", "pt": "Não instalados"},
    "w_missing_note": {"en": "Games you don't have on any of your devices yet.", "es": "Juegos que aún no tienes en ninguno de tus dispositivos.", "pt": "Jogos que você ainda não tem em nenhum dos seus dispositivos."},
    "w_lib_not_installed": {"en": "Not installed", "es": "Sin instalar", "pt": "Não instalado"},
    "w_lib_on": {"en": "On {where}", "es": "En {where}", "pt": "Em {where}"},
    "w_here_mac": {"en": "This Mac can build {build} games for your iPhone, iPad or Mac, and get {apps} ready-made apps.",
                   "es": "Este Mac puede crear {build} juegos para tu iPhone, iPad o Mac, y obtener {apps} apps ya hechas.",
                   "pt": "Este Mac pode criar {build} jogos para seu iPhone, iPad ou Mac, e obter {apps} apps prontos."},
    "w_here_devices": {"en": "PadMint sees {devices}.", "es": "PadMint ve {devices}.", "pt": "O PadMint vê {devices}."},
    "w_here_no_devices": {"en": "Connect your iPhone or iPad to this Mac with a cable once, and PadMint shows what's on it.",
                          "es": "Conecta tu iPhone o iPad a este Mac con un cable una vez y PadMint te muestra lo que tiene.",
                          "pt": "Conecte seu iPhone ou iPad a este Mac com um cabo uma vez e o PadMint mostra o que há nele."},
    "w_here_no_xcode": {"en": "With Xcode installed, PadMint also shows which games are on your iPhone and iPad.",
                        "es": "Con Xcode instalado, PadMint también muestra qué juegos hay en tu iPhone y iPad.",
                        "pt": "Com o Xcode instalado, o PadMint também mostra quais jogos estão no seu iPhone e iPad."},
    "w_here_other": {"en": "On this computer you can build {names} and get {apps} ready-made apps for iPhone and iPad. The other {mac} games are built on a Mac with Apple Silicon (M1 or newer).",
                     "es": "En esta computadora puedes crear {names} y obtener {apps} apps ya hechas para iPhone y iPad. Los otros {mac} juegos se crean en un Mac con Apple Silicon (M1 o posterior).",
                     "pt": "Neste computador você pode criar {names} e obter {apps} apps prontos para iPhone e iPad. Os outros {mac} jogos são criados em um Mac com Apple Silicon (M1 ou mais novo)."},
    "w_here_other_none": {"en": "On this computer you can get {apps} ready-made apps for iPhone and iPad. The other {mac} games are built on a Mac with Apple Silicon (M1 or newer).",
                          "es": "En esta computadora puedes obtener {apps} apps ya hechas para iPhone y iPad. Los otros {mac} juegos se crean en un Mac con Apple Silicon (M1 o posterior).",
                          "pt": "Neste computador você pode obter {apps} apps prontos para iPhone e iPad. Os outros {mac} jogos são criados em um Mac com Apple Silicon (M1 ou mais novo)."},
    "w_all_note_plain": {"en": "Every game, by name.", "es": "Todos los juegos, por nombre.", "pt": "Todos os jogos, por nome."},
    "w_all_note": {"en": "Every game, by name. Dimmed ones aren't available yet: choose one to see why.",
                   "es": "Todos los juegos, por nombre. Los atenuados todavía no están disponibles: elige uno para ver por qué.",
                   "pt": "Todos os jogos, por nome. Os esmaecidos ainda não estão disponíveis: escolha um para ver por quê."},
    "w_original": {"en": "Original: {system}", "es": "Original: {system}", "pt": "Original: {system}"},
    "w_plays_on": {"en": "Plays on {devices}", "es": "Se juega en {devices}", "pt": "Roda em {devices}"},
    "w_needs_mac_tag": {"en": "Needs an M1+ Mac", "es": "Necesita un Mac M1+", "pt": "Precisa de um Mac M1+"},
    "w_before_title": {"en": "Install with Homebrew, once:", "es": "Instala con Homebrew, una vez:",
                       "pt": "Instale com o Homebrew, uma vez:"},
    "w_before_hint": {
        "en": "Open Terminal (Applications → Utilities), click Copy, paste the line into Terminal and press Return. Wait until it finishes, then click Check again. Packages already on this Mac show ✓.",
        "es": "Abre Terminal (Aplicaciones → Utilidades), pulsa Copiar, pega la línea en Terminal y pulsa Retorno. Espera a que termine y luego pulsa Comprobar de nuevo. Los paquetes que ya están en este Mac muestran ✓.",
        "pt": "Abra o Terminal (Aplicativos → Utilitários), clique em Copiar, cole a linha no Terminal e pressione Return. Espere terminar e depois clique em Verificar de novo. Os pacotes que já estão neste Mac mostram ✓.",
    },
    "w_before_brew": {
        "en": "First install Homebrew, a free installer for programs like these: open https://brew.sh, copy the line under Install Homebrew, paste it into Terminal (Applications → Utilities) and press Return. When it finishes, paste the line below the same way.",
        "es": "Primero instala Homebrew, un instalador gratuito para programas como estos: abre https://brew.sh, copia la línea bajo Install Homebrew, pégala en Terminal (Aplicaciones → Utilidades) y pulsa Retorno. Cuando termine, pega la línea de abajo de la misma forma.",
        "pt": "Primeiro instale o Homebrew, um instalador gratuito para programas como estes: abra https://brew.sh, copie a linha em Install Homebrew, cole no Terminal (Aplicativos → Utilitários) e pressione Return. Quando terminar, cole a linha abaixo da mesma forma.",
    },
    "w_copy": {"en": "Copy", "es": "Copiar", "pt": "Copiar"},
    "w_ios27": {
        "en": "Heads-up: this app was built with Apple's iOS 27 tools, and PadMint couldn't confirm it uses the app startup Apple requires with them. It may not open on iOS or iPadOS 27 until {name} is updated; iOS 26 and earlier aren't affected. If it doesn't open, please say so at {issues}",
        "es": "Aviso: esta app se creó con las herramientas de iOS 27 de Apple y PadMint no pudo confirmar que use el inicio de app que Apple exige con ellas. Puede que no abra en iOS o iPadOS 27 hasta que {name} se actualice; iOS 26 y anteriores no se ven afectados. Si no abre, avísanos en {issues}",
        "pt": "Atenção: este app foi criado com as ferramentas do iOS 27 da Apple e o PadMint não conseguiu confirmar que ele usa a inicialização de app que a Apple exige com elas. Ele pode não abrir no iOS ou iPadOS 27 até que {name} seja atualizado; o iOS 26 e anteriores não são afetados. Se não abrir, avise em {issues}",
    },
    "w_needs_mac": {
        "en": "PadMint makes {name} for iPhone and iPad on a Mac with Apple Silicon (M1 or newer) and Xcode, so it can't make it on this computer yet. If you have such a Mac, open PadMint there and choose {name}. The game's page has the latest on other computers.",
        "es": "PadMint crea {name} para iPhone y iPad en un Mac con Apple Silicon (M1 o posterior) y Xcode, así que todavía no puede crearlo en esta computadora. Si tienes uno de esos Mac, abre PadMint allí y elige {name}. La página del juego tiene las novedades para otras computadoras.",
        "pt": "O PadMint cria {name} para iPhone e iPad num Mac com Apple Silicon (M1 ou mais novo) e Xcode, então ainda não consegue criá-lo neste computador. Se você tem um Mac assim, abra o PadMint nele e escolha {name}. A página do jogo tem as novidades para outros computadores.",
    },
    "w_needs_windows": {
        "en": "{name}'s Windows copy is made on the Windows PC it will run on: open PadMint on that PC and choose {name}.",
        "es": "La copia de {name} para Windows se crea en el PC con Windows donde vas a jugar: abre PadMint en ese PC y elige {name}.",
        "pt": "A cópia de {name} para Windows é criada no PC com Windows onde você vai jogar: abra o PadMint nesse PC e escolha {name}.",
    },
    "elsewhere": {
        "en": "Not on this computer: {names}. PadMint makes them on a Mac with Apple Silicon (M1 or newer); each game's page has the latest.",
        "es": "No disponibles en esta computadora: {names}. PadMint los crea en un Mac con Apple Silicon (M1 o posterior); la página de cada juego tiene las novedades.",
        "pt": "Não disponíveis neste computador: {names}. O PadMint os cria num Mac com Apple Silicon (M1 ou mais novo); a página de cada jogo tem as novidades.",
    },
    "w_type_toggle": {"en": "Type a path instead", "es": "Escribir una ruta", "pt": "Digitar um caminho"},
    "w_plan_title": {"en": "What PadMint will do on this computer", "es": "Qué hará PadMint en esta computadora",
                     "pt": "O que o PadMint vai fazer neste computador"},
    "w_plan_source": {"en": "Download {name}'s source code (latest release) from {repo}",
                      "es": "Descargar el código fuente de {name} (última versión) desde {repo}",
                      "pt": "Baixar o código-fonte de {name} (última versão) de {repo}"},
    "w_plan_tools": {"en": "Download the free build tools it needs, once",
                     "es": "Descargar una sola vez las herramientas gratuitas que necesita",
                     "pt": "Baixar uma única vez as ferramentas gratuitas necessárias"},
    "w_tool_here": {"en": "already on this computer", "es": "ya está en esta computadora", "pt": "já está neste computador"},
    "w_plan_app": {"en": "Download {name}'s published app, which has no game code in it",
                   "es": "Descargar la app publicada de {name}, que no contiene código del juego",
                   "pt": "Baixar o app publicado de {name}, que não contém código do jogo"},
    "w_plan_build": {"en": "Build your copy here from your game file: the first time takes a few minutes to a few hours, later builds reuse finished work",
                     "es": "Crear tu copia aquí con tu archivo del juego: la primera vez tarda de unos minutos a unas horas; después se reutiliza lo hecho",
                     "pt": "Criar sua cópia aqui com o seu arquivo do jogo: a primeira vez leva de alguns minutos a algumas horas; depois o que foi feito é reaproveitado"},
    "w_plan_save": {"en": "Save your copy in {folder}", "es": "Guardar tu copia en {folder}", "pt": "Salvar sua cópia em {folder}"},
    "w_plan_build_app": {"en": "Build the app here (you add your game file inside the app afterwards): the first time takes a few minutes to a few hours, later builds reuse finished work",
                         "es": "Crear la app aquí (añades tu archivo del juego dentro de la app después): la primera vez tarda de unos minutos a unas horas; después se reutiliza lo hecho",
                         "pt": "Criar o app aqui (você adiciona o seu arquivo do jogo dentro do app depois): a primeira vez leva de alguns minutos a algumas horas; depois o que foi feito é reaproveitado"},
    "w_plan_space": {"en": "Free space needed: about {gb} GB", "es": "Espacio libre necesario: unos {gb} GB",
                     "pt": "Espaço livre necessário: cerca de {gb} GB"},
    "w_plan_needs": {"en": "Before you start (one time only):", "es": "Antes de empezar (solo una vez):",
                     "pt": "Antes de começar (só uma vez):"},
    "w_needs_ok": {"en": "found", "es": "encontrado", "pt": "encontrado"},
    "w_needs_missing": {"en": "not found", "es": "no encontrado", "pt": "não encontrado"},
    "w_output_android": {"en": "You get a game data folder to add in the {name} app on your Android phone or tablet.",
                         "es": "Recibes una carpeta de datos del juego para añadir en la app {name} de tu teléfono o tableta Android.",
                         "pt": "Você recebe uma pasta de dados do jogo para adicionar no app {name} do seu celular ou tablet Android."},
    "w_output_ios": {"en": "You get an .ipa app file. You put it on your iPhone or iPad with Sideloadly (free) and your Apple ID: the steps are below.",
                     "es": "Recibes un archivo de app .ipa. Lo pones en tu iPhone o iPad con Sideloadly (gratis) y tu Apple ID: los pasos están abajo.",
                     "pt": "Você recebe um arquivo de app .ipa. Você o coloca no seu iPhone ou iPad com o Sideloadly (grátis) e o seu Apple ID: os passos estão abaixo."},
    "w_output_macos": {"en": "You get a Mac app to open on this Mac.", "es": "Recibes una app para abrir en este Mac.",
                       "pt": "Você recebe um app para abrir neste Mac."},
    "w_output_windows": {"en": "You get a folder with {name}.exe to play on this PC.",
                         "es": "Recibes una carpeta con {name}.exe para jugar en este PC.",
                         "pt": "Você recebe uma pasta com {name}.exe para jogar neste PC."},
    "w_making": {"en": "Making {name} for {device}", "es": "Creando {name} para {device}", "pt": "Criando {name} para {device}"},
    "w_ph_release": {"en": "Find the latest {name} release", "es": "Buscar la última versión de {name}",
                     "pt": "Encontrar a última versão de {name}"},
    "w_ph_source": {"en": "Download {name}'s source code", "es": "Descargar el código fuente de {name}",
                    "pt": "Baixar o código-fonte de {name}"},
    "w_ph_tools": {"en": "Get the free build tools", "es": "Obtener las herramientas gratuitas",
                   "pt": "Obter as ferramentas gratuitas"},
    "w_ph_app": {"en": "Download {name}'s app (no game code inside)", "es": "Descargar la app de {name} (sin código del juego)",
                 "pt": "Baixar o app de {name} (sem código do jogo)"},
    "w_ph_build": {"en": "Build your copy on this computer", "es": "Crear tu copia en esta computadora",
                   "pt": "Criar sua cópia neste computador"},
    "w_ph_save": {"en": "Save your copy", "es": "Guardar tu copia", "pt": "Salvar sua cópia"},
    "w_from": {"en": "from {host}", "es": "desde {host}", "pt": "de {host}"},
    "w_version_from": {"en": "{version}, from {repo}", "es": "{version}, desde {repo}", "pt": "{version}, de {repo}"},
    "w_unpacking": {"en": "unpacking", "es": "descomprimiendo", "pt": "descompactando"},
    "w_log": {"en": "Technical log", "es": "Registro técnico", "pt": "Registro técnico"},
    "w_log_empty": {"en": "Nothing written yet.", "es": "Todavía no hay nada escrito.", "pt": "Nada escrito ainda."},
    "w_copy_log": {"en": "Copy log for a bug report", "es": "Copiar registro para un informe", "pt": "Copiar registro para um relato"},
    "w_done_title": {"en": "Your copy is ready", "es": "Tu copia está lista", "pt": "Sua cópia está pronta"},
    "w_took": {"en": "Took", "es": "Tardó", "pt": "Levou"},
    "next_ios_sideloadly": {"en": "On this computer, install Sideloadly (free) from https://sideloadly.io and open it.",
                            "es": "En esta computadora, instala Sideloadly (gratis) desde https://sideloadly.io y ábrelo.",
                            "pt": "Neste computador, instale o Sideloadly (grátis) em https://sideloadly.io e abra-o."},
    "next_ios_connect": {"en": "Connect your iPhone or iPad to this computer with a cable. Unlock it and tap Trust if it asks.",
                         "es": "Conecta tu iPhone o iPad a esta computadora con un cable. Desbloquéalo y toca Confiar si te lo pregunta.",
                         "pt": "Conecte o seu iPhone ou iPad a este computador com um cabo. Desbloqueie-o e toque em Confiar se ele perguntar."},
    "next_ios_sign": {"en": "Drag {file} into Sideloadly, type your Apple ID email and click Start. Sideloadly asks for your Apple ID password to sign the app with Apple.",
                      "es": "Arrastra {file} a Sideloadly, escribe el correo de tu Apple ID y pulsa Start. Sideloadly te pide la contraseña de tu Apple ID para firmar la app con Apple.",
                      "pt": "Arraste {file} para o Sideloadly, digite o e-mail do seu Apple ID e clique em Start. O Sideloadly pede a senha do seu Apple ID para assinar o app com a Apple."},
    "next_ios_trust": {"en": "On the iPhone or iPad, open Settings → General → VPN & Device Management, tap your Apple ID, then tap Trust.",
                       "es": "En el iPhone o iPad, abre Ajustes → General → VPN y gestión de dispositivos, toca tu Apple ID y luego Confiar.",
                       "pt": "No iPhone ou iPad, abra Ajustes → Geral → VPN e Gerenciamento de Dispositivos, toque no seu Apple ID e depois em Confiar."},
    "next_ios_devmode": {"en": "If it says Developer Mode is required: Settings → Privacy & Security → Developer Mode → On, then restart when asked.",
                         "es": "Si dice que se necesita el Modo de desarrollador: Ajustes → Privacidad y seguridad → Modo de desarrollador → Activado, y reinicia cuando te lo pida.",
                         "pt": "Se disser que o Modo de Desenvolvedor é necessário: Ajustes → Privacidade e Segurança → Modo de Desenvolvedor → Ativado, e reinicie quando pedir."},
    "next_ios_note": {"en": "With a free Apple ID the app opens for 7 days; to keep playing, drag the same file into Sideloadly again. To update {name}, do the same with the new file and the same Apple ID: your saves stay. AltStore and SideStore work too.",
                      "es": "Con un Apple ID gratuito la app abre durante 7 días; para seguir jugando, arrastra el mismo archivo a Sideloadly otra vez. Para actualizar {name}, haz lo mismo con el archivo nuevo y el mismo Apple ID: tus partidas se conservan. AltStore y SideStore también funcionan.",
                      "pt": "Com um Apple ID gratuito o app abre por 7 dias; para continuar jogando, arraste o mesmo arquivo para o Sideloadly de novo. Para atualizar o {name}, faça o mesmo com o arquivo novo e o mesmo Apple ID: seus saves continuam. AltStore e SideStore também funcionam."},
    "next_ios_in_app": {"en": "Open {name} and add your own game file when it asks; the full guide below shows how.",
                        "es": "Abre {name} y añade tu propio archivo del juego cuando te lo pida; la guía completa de abajo explica cómo.",
                        "pt": "Abra o {name} e adicione o seu próprio arquivo do jogo quando ele pedir; o guia completo abaixo mostra como."},
    "next_ios_open": {"en": "Open {name} and play. If it asks for anything else, the full guide below shows how.",
                      "es": "Abre {name} y juega. Si pide algo más, la guía completa de abajo explica cómo.",
                      "pt": "Abra o {name} e jogue. Se ele pedir mais alguma coisa, o guia completo abaixo mostra como."},
    "w_failed_title": {"en": "The build stopped", "es": "La compilación se detuvo", "pt": "A compilação parou"},
    "w_cancel_note": {"en": "Cancel keeps finished work, so the next try is faster.",
                      "es": "Cancelar conserva lo ya hecho, así que el siguiente intento será más rápido.",
                      "pt": "Cancelar guarda o que já foi feito, então a próxima tentativa é mais rápida."},
    "w_source": {"en": "PadMint source code", "es": "Código fuente de PadMint", "pt": "Código-fonte do PadMint"},
    "w_report": {"en": "Report a problem", "es": "Informar un problema", "pt": "Relatar um problema"},
    "w_update": {"en": "Update PadMint", "es": "Actualizar PadMint", "pt": "Atualizar o PadMint"},
    "w_device_help": {"en": "Missing a device?", "es": "¿Falta un dispositivo?", "pt": "Falta um dispositivo?"},
    "w_update_help": {
        "en": "The device list comes with this PadMint download. To update it, close PadMint, download the latest ZIP and open PadMint from the newly extracted folder. Your existing builds and downloads stay where they are.",
        "es": "La lista de dispositivos viene con esta descarga de PadMint. Para actualizarla, cierra PadMint, descarga el ZIP más reciente y abre PadMint desde la carpeta recién extraída. Tus compilaciones y descargas existentes permanecen donde están.",
        "pt": "A lista de dispositivos vem com este download do PadMint. Para atualizá-la, feche o PadMint, baixe o ZIP mais recente e abra o PadMint na pasta recém-extraída. Suas compilações e downloads existentes continuam onde estão."},
    "w_local_note": {"en": "This page is served by PadMint on this computer (127.0.0.1).",
                     "es": "Esta página la sirve PadMint en esta computadora (127.0.0.1).",
                     "pt": "Esta página é servida pelo PadMint neste computador (127.0.0.1)."},
}


def _from_tag(tag):
    tag = (tag or "").strip().lower().replace("-", "_")
    if not tag or tag in ("c", "posix"):
        return None
    code = tag.split("_")[0].split(".")[0]
    return code if code in LANGUAGES else "en"


def _windows_language():
    try:
        primary = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
    except (AttributeError, OSError):
        return None
    return WINDOWS_LANGUAGES.get(primary, "en")


def language(environ=None, windows=None):
    """The player's language code: en, es or pt."""
    environ = os.environ if environ is None else environ
    chosen = _from_tag(environ.get("PADMINT_LANG"))
    if chosen:
        return chosen
    if windows is None:
        windows = os.name == "nt"
    if windows:
        found = _windows_language()
        if found:
            return found
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        found = _from_tag(environ.get(name))
        if found:
            return found
    return "en"


def t(key, **fields):
    """The message for key in the player's language, with fields filled in. A console that
    cannot show accented letters gets English instead of an error."""
    chosen = language()
    if chosen != "en" and not stream_supports():
        chosen = "en"
    return phrase(key, chosen, **fields)


def phrase(key, lang, **fields):
    """The message for key in the given language (the PadMint window chooses its own)."""
    texts = MESSAGES[key]
    return texts.get(lang, texts["en"]).format(**fields)


def localized(value, field, lang=None):
    """A catalog value's translation (value["translations"][lang][field]) or the English original."""
    chosen = lang or (language() if stream_supports() else "en")
    return ((value.get("translations") or {}).get(chosen) or {}).get(field, value.get(field))


def stream_supports(stream=None):
    """True when stream can print this language's characters (always, on modern terminals)."""
    encoding = getattr(stream or sys.stdout, "encoding", None) or "utf-8"
    try:
        "áéíóúãçñ¿¡…".encode(encoding)
        return True
    except (LookupError, UnicodeEncodeError):
        return False

from pathlib import Path
p=Path('game/game.html');s=p.read_text(encoding='utf8');assert '<script src="host-adapter.js"></script>' in s
s=s.replace('<script src="host-adapter.js"></script>','<script src="host-adapter.js"></script>\n\t<script src="event-hooks.js"></script>');s=s.replace('cr_createRuntime("c2canvas");','oneConnectInstrumentation.install();\n\t            cr_createRuntime("c2canvas");');p.write_text(s,encoding='utf8')

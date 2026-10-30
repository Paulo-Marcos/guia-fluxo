"""D-204: no pilot, `queue add` e `next` sobem o executor da fila destacado.

Nos testes isso seria um processo solto integrando no sandbox enquanto o
teste roda (e segurando a pasta temporaria no Windows). Desligado aqui para
todos; o teste da D-204 religa onde quer o spawn de verdade.
"""

import os

os.environ.setdefault("GUIA_AUTO_EXECUTOR", "off")

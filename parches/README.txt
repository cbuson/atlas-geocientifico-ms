ITA ARANDU MS · CORRELAÇÃO ESTRATIGRÁFICA MULTIPONTO · R1

Nova ferramenta da Bancada Digital em Estratigrafia e tempo.

Inclui
- duas ou mais colunas
- coluna atual do construtor
- importação de JSON
- seleção interativa de níveis
- correlação litológica, bioestratigráfica, cronoestratigráfica, por superfície ou outro marcador
- critério obrigatório
- confiança alta, moderada ou possível
- linha contínua ou tracejada
- nível marcador
- alinhamento por base, topo ou marcador
- mapa com pontos GPS
- distâncias entre seções
- ordem espacial do perfil
- exportação JSON, CSV e SVG
- interface responsiva para celular vertical
- Ajuda e Ciência
- metodologia e referências APA 7

O patch não substitui index.html inteiro.

Instalação

Set-ExecutionPolicy -Scope Process Bypass
.\APLICAR_CORRELACAO_ESTRATIGRAFICA_R1.ps1

Depois use Ctrl + F5.


R1.1
Corrige a falha de instalação quando referencias/index.html não possui a tag </main>.
O instalador agora aceita </main>, </body> ou </html> e continua sendo idempotente.
Pode ser executado mesmo depois da tentativa R1 parcialmente aplicada.

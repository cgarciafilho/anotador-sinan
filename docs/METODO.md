# METODO — anotador SINAN

Cópia pública do METODO do repositório de desenvolvimento: as decisões estão como foram escritas (append-only, datadas);
foram retirados caminhos locais, nomes de máquinas e detalhes operacionais que não dizem respeito ao método. As pastas
`herdado/` do repositório de desenvolvimento chamam-se `tabelas/` aqui.

## Fontes

- Dicionários: `.def` e `.cnv` do TabWin (`TAB_SINANNET.zip`, FTP do DATASUS), em `tabelas/tab_sinannet/` (58 `.def`, 134 `.cnv`).
- Entrada da ferramenta: DBF exportado do Sinan NET (`C:\SinanNet\BaseDBF\`), latin-1 (cp850/cp1252 a confirmar na base real).

- Manuais do Sinan sobre duplicidade (levantados em 2026-10-25): `Docs_TAB_SINAN.zip` do FTP do DATASUS (65.650.628 bytes,
  sha256 `037e5d59…`), Caderno geral do Sinan NET (2008, espelho da SES-GO), Caderno de hanseníase 2026 (MS, jan/2026), manual do
  Sinan Online 2011 (SES-GO), NT 10/2020 da SES-DF e, do acervo da SESA-CE, a NT Sinan de 2017, o manual de saúde do trabalhador
  (2017/2023) e a NT Conjunta 01/2025 de sífilis. Os PDFs não são redistribuídos neste repositório; páginas citadas em
  `docs/duplicidades_definicoes_manuais.md`.
- Regionalização da SESA-CE (município → ADS → SR): `tabelas/regionalizacao_sesa_sr_ads.csv` (184 municípios, 22 ADS, 5 SR), extraído
  da planilha "SR / ADS" da SESA-CE de 02/03/2022. A REGIONET do TabWin (2021) traz as 22 regionais do CE com o nome antigo
  ("3 CRES MARACANAU"); serve só de reserva quando o município não está na tabela.

## Ambiente

- Entrega A: Python 3.13.5 "embeddable" para Windows x64 (python.org, sha256 `7d2650fd…`) com `python313._pth` apontando para
  `Lib\site-packages` e wheels win_amd64 de pandas 3.0.6, numpy 2.5.4, openpyxl 3.1.5, dbfread 2.0.7 instalados por
  `pip install --target --platform win_amd64`. Construção reproduzível: `build/build_windows_zip.sh`; a partir da v0.2.0 o zip é
  montado pelo GitHub Actions a cada tag `vX.Y.Z` (`.github/workflows/release.yml`), com sha256 publicado no release.
- O embeddable não traz tkinter: interface por arrastar o arquivo sobre o `.bat` (v1) ou página local no navegador.
- Desenvolvimento: `.venv` com Python 3.13 e as mesmas versões do pacote Windows, mais pytest. Testes: `python -m pytest tests/ -q`
  (153 testes em 2026-10-26, ~3 min). O zip do produto tem ~103 MB; o embeddable e as wheels baixadas ficam em `build/`, fora do git.
- Manual em PDF (`build/build_manual_pdf.py`): precisa de `weasyprint` e `markdown` no venv; instalados no legba em 2026-10-29
  (weasyprint 70.0). O zip local de 2026-10-29 (fb7a1c7 + correção do script) tem 67,6 MB: as tabelas comprimem bem.

## Decisões

### 2026-10-20 — Projeto separado do projeto de análise anterior
Contexto: produto para equipes (anotar, duplicidades, modelos), natureza diferente da análise. Decisão: pasta e repositório
próprios, reaproveitando parsers e critérios por cópia. Alternativa descartada: crescer dentro do projeto de análise.
Consequência: precisa de repositório no GitHub para as sessões na nuvem.

### 2026-10-20 — Forma de entrega: A (Python embutido em zip), com C (página no navegador) como reserva
Contexto: as equipes não podem instalar Python. Opções: A zip com Python embeddable; B `.exe` PyInstaller (GitHub Actions
Windows); C HTML que lê DBF no navegador. Decisão: A primeiro, por não exigir instalação nem compilação e ser menos barrado
que um `.exe` desconhecido; B só se A passar na política e a equipe pedir "um programa"; C se a política barrar executáveis
(limite: bases grandes como dengue 11 anos). Teste decisivo: `anotador_teste_2026-10-20.zip` numa máquina da SESA.

### 2026-10-20 — Alternativa simples declarada
Sinan NET e TabWin não exportam microdados com rótulo (usuário, 2026-10-20). A alternativa a vencer é TabWin + Excel à mão;
o piloto da semana 3 mede tempo e erros contra ela, com critério escrito antes.

## Bugs corrigidos

- 2026-10-22 — parser `.cnv`: divisão rótulo/códigos por "2+ espaços" quebrava `Municbr.cnv` ("Ignorado ou exterior" com
  códigos no rótulo) e `AB.cnv`; trocado por colunas fixas (10–59 / 60+) com a divisão por espaços como reserva. Achado por
  inspeção do xlsx de fumaça.
- 2026-10-22 — vírgula final na lista de códigos (`nudosePB.cnv`) era lida como categoria de branco; o branco de DOSE_RECEB
  saía "6 doses". Achado pelo teste sintético de hanseníase (critério 2).
- 2026-10-22 — gerador sintético: sorteava códigos mais largos que o campo (`00-99` em campo de 1 caractere) e `0001` em
  campo numérico (o DBF devolve 1). Corrigido no gerador, não no programa.
- 2026-10-22 — `anotar.bat` usava `PYTHONPATH` + `-I`; o Python embeddable com `._pth` ignora `PYTHONPATH`. O caminho `..\app`
  foi para o `python313._pth`. Não testado no Windows.
- 2026-10-26 — sífilis em gestante: o `tipo_sugerido` mostrava o código cru de `CS_GESTANT` ("trimestres 4/1"), e o código 4
  (idade gestacional ignorada, `gestante.cnv`) era lido como "4º trimestre". Passa a mostrar o rótulo ("gestação: 1º trimestre /
  idade gestacional ignorada"); as colunas `CS_GESTANT_rotulo_A/B` já estavam certas. Achado pelo usuário na base real. Teste novo
  com o código 4 e conferência na planilha sintética (`tests/test_duplicates.py`).
- 2026-10-29 — `build/build_windows_zip.sh` copiava as tabelas com `*.def` e `*.cnv` (só minúsculas): o zip montado hoje saiu
  com 668 dos 703 arquivos de `tabelas/tab_sinannet/`, sem `Unid_Prisionais.CNV`, `AnimaispNET.DEF`, `PlanSurtoNet.DEF` e 32
  `*.CNV` do pacote completo. Achado ao conferir o conteúdo do zip antes de entregar. Trocado por `find -iname`; zip remontado
  com 703 (597+33 cnv, 58+2 def, 13 dbf/csv), sha256 `fbb2d70c…`, 67,6 MB. O release do GitHub Actions (tag) usa o mesmo script.

### 2026-10-22 — Critério de aceite da sessão 01
Registrado antes de escrever código, copiado do brief da sessão 01. Ajustes depois dos resultados serão marcados pós-hoc.
1. Para cada `.def` de `tabelas/tab_sinannet/` escolhido para o teste (TuberculNET, SifilisNET, GestSifNET, HansNET, LeishvisNET,
   LeishtegNET, DengueNET), 100% dos campos do DBF sintético que têm `.cnv` no `.def` recebem a coluna `<campo>_rotulo`.
2. Num DBF sintético com verdade conhecida (valores sorteados dentro das categorias do `.cnv`, mais alguns códigos fora da tabela
   e alguns vazios), a contagem por rótulo no xlsx é igual à contagem da verdade, campo a campo, em 100% dos campos.
3. Código fora da tabela vira `[codigo] sem rótulo`; vazio vira `Ign/Branco`; nenhum registro é perdido (linhas do xlsx = registros do DBF).
4. `NU_IDADE_N` vira idade em anos (4xxx = anos; 3xxx = meses; 2xxx = dias; 1xxx = horas; conferir no `.cnv` de faixa etária e
   nas instruções do Sinan), com teste próprio. Datas `D` saem como data do Excel.
5. Município (`ID_MN_RESI`, `ID_MUNICIP`, 6 dígitos IBGE) recebe nome a partir do `.cnv` de municípios de `tabelas/tab_sinannet/`
   (há um por UF; usar o do CE e deixar os outros disponíveis).
6. Só pandas, numpy, openpyxl e dbfread; Python 3.13. Qualquer outra dependência exige decisão no METODO.
7. Acima de 1.048.576 linhas, a saída é dividida por ano de notificação com aviso; teste com DBF sintético pequeno e limite
   artificialmente baixo.

### 2026-10-22 — Interpretações do critério de aceite fixadas antes de rodar os testes
Registradas depois de ler os `.def`/`.cnv` e antes do primeiro teste; não alteram o critério, dizem como ele é lido.
- Critério 1: "campos que têm `.cnv` no `.def`" = campos cujo `.cnv` existe em `tabelas/tab_sinannet/`. Faltam vários (dengue 12
  campos, hanseníase 2, TB `penitenciario.cnv`); cada um vai para o log como `AVISO ... não está disponível` e para o backlog.
  Tabelas de agrupamento (ANOS/MESES/TRIME em datas; UF/região metropolitana/capital/fronteira/prioritário sobre código de
  município; NHE sobre unidade; faixas etárias) não são categorias do campo e não geram `_rotulo`; campos de data saem como data
  (critério 4). A tabela de UF (`UFCODIGO.CNV`) é agrupamento sobre `ID_MUNICIP`, mas é a tabela de categorias de `SG_UF`,
  `SG_UF_NOT`, `UF_TRANSF`: nesses campos gera `_rotulo`.
- Critério 3: vazio vira o rótulo de branco da própria tabela quando ela tem (Sexo.cnv: `Em Branco`), senão `Ign/Branco`.
  Tabelas de complemento (MUNICBR) não são consultadas para o vazio.
- Critério 4: `NU_IDADE_N` gera `NU_IDADE_N_anos` (4xxx → xxx; 1xxx/2xxx/3xxx → 0; outros → vazio) e `NU_IDADE_N_rotulo` com a
  faixa etária `FXIDAD10NET.CNV` ("Fx Etaria SINAN", 10 faixas), para manter o nome `_rotulo` uniforme.
- Critério 5: cadeia `MUNICCE.CNV` → `MUNICBR.CNV` → `[codigo] sem rótulo`. O BR tem linha-pega-tudo (`000001-009999,999999` →
  "Ignorado ou exterior"); códigos de 6 dígitos inexistentes nela viram `sem rótulo`.

### 2026-10-22 — Semântica do `.cnv`: última linha vence; vírgula final não é branco
Contexto: `Anos.cnv` tem `IGN 0000-9999` antes das linhas por ano; `Sim_nao.cnv` tem `Ign/Branco ,0-9` antes de `Sim 1`.
TabWin preenche um vetor código → categoria linha a linha, então a última linha que contém o código vence. Decisão: mesma
regra. Token vazio (vírgula inicial `,0-9`, ou no meio, como em `Municbr.cnv`) = valor em branco; vírgula no fim da lista
(`6 doses  06, 6,6 ,` em `nudosePB.cnv`) é descuido de edição e não vira branco (achado pelo teste sintético: o branco de
DOSE_RECEB virava "6 doses"). Layout: rótulo nas colunas 10–59, códigos a partir da 60, exceto os `NHE*.cnv` (outro layout,
só agrupamento), onde se divide pela última sequência de 2+ espaços. Terceiro campo do `.def` = posição inicial no campo (5 =
mês em AAAAMMDD); o código é cortado à largura do cabeçalho do `.cnv`. Confiança: alta para a regra "última vence" (coerente
com todas as tabelas lidas), média para o tratamento de códigos de largura maior que o campo (não ocorre em dados reais).

### 2026-10-22 — TB usa `TuberculNET5_0.def`, não `TuberculNET.def`
Contexto: o brief dizia `TUBENET*.DBF → TuberculNET.def`. O `TuberculNET5_0.def` é a versão 5.0 da ficha (TEST_MOLEC,
ANT_RETRO, populações especiais, 17 campos a mais), é o que o projeto de análise anterior usou com a base real
e cita 1 `.cnv` faltante contra 9 do antigo (SITUA_ENCE sem tabela no antigo).
Decisão: reconhecimento por nome (`TUBENET` → candidatos 5_0 e antigo), desempate pela maior interseção de campos com o DBF
e, depois, pelo menor número de `.cnv` faltantes; padrão do `A` do `.def` e conjunto de campos como reserva. Pré-teste.

### 2026-10-22 — Codificação do DBF: cp850 × cp1252 por pontuação, empate → cp850
O projeto anterior leu a base real com cp850 (padrão de `d01`), cp1252 como alternativa. Decisão: ler tudo como latin-1
(sem perda), contar letras do português nas duas decodificações, escolher a maior; `--codificacao` força. Registrado no log.

### 2026-10-22 — Saída em openpyxl write-only; limite por ano
`pandas.to_excel` carrega a planilha inteira em memória; o modo write-only grava linha a linha. Datas com formato
`DD/MM/YYYY`. Acima de `max_linhas` (padrão 1.048.575) divide por `NU_ANO` ou ano de `DT_NOTIFIC`; ano acima do limite vira
`_parteN`. Medida (nuvem, base sintética TB 100 mil × 81 campos): 138 s, 382 MB RSS, xlsx 70 MB — ver backlog P1.

### 2026-10-22 — Ambiente da nuvem barra python.org
`build/build_windows_zip.sh` baixa wheels do PyPI (passa) e o Python embeddable de python.org (403 no proxy). O script
aceita o arquivo pré-baixado em `build/` ou `SEM_PYTHON=1` para montar o resto e conferir. Zip completo e teste no Windows
ficam com o usuário (PLANO P0).

### 2026-10-22 — Resultado dos testes da sessão 01 (critérios 1–7)
92 testes `pytest` passando (`tests/`): parse à mão de 12 `.cnv`/`.def` lidos no editor; regras de idade, branco, município,
UF, posição inicial; detecção de agravo; e os 7 DBFs sintéticos (300 registros cada, 80% códigos válidos, 10% vazios, 10% fora
da tabela, nomes com acentos em cp850) para TUBENET, SIFCNET, SIFGENET, HANSNET, LEIVNET, LTANET, DENGNET: critério 1 (todo
campo com tabela disponível tem `_rotulo`, coluna ao lado), 2 (contagem por rótulo igual à verdade em 100% dos campos), 3
(linhas = registros; `sem rótulo` e `Ign/Branco` presentes), 4 (idade e faixa iguais à verdade; `DT_NOTIFIC` como data), 5
(municípios CE), 6 (só pandas/numpy/openpyxl/dbfread), 7 (25 registros com limite 8 → arquivos por ano e `_parteN`, soma 25).
Campos rotulados por agravo (campos do `.def` presentes no DBF sintético → com `_rotulo`): TB 79 → 63; sífilis adquirida 54 → 33;
sífilis gestante 28 → 17; hanseníase 46 → 23 (2 sem `.cnv`); LV 53 → 34; LTA 57 → 31; dengue 62 → 27 (12 sem `.cnv`). O
restante são datas, tabelas externas `.dbf`, somas e agrupamentos. Limite do teste: verdade e programa compartilham o parser
do `.cnv` (a independência vem dos testes à mão) e a escolha da tabela por campo (`build_plan`); o DBF real não foi testado.

### 2026-10-22 — Base real (SIFGENET, Windows do usuário): codificação é cp1252, não cp850
Primeiro DBF real pelo pacote Windows: SIFGENET.DBF, 16.274 registros, 70 campos. A detecção escolheu cp1252 com margem
larga (cp1252: 4.951 letras do português e 6 estranhas; cp850: 667 e 4.290). Contradiz o padrão cp850 do `d01` do projeto
anterior (que avisava para tentar cp1252 "se os nomes saírem trocados"). Decisão: manter a detecção automática como padrão;
não fixar cp1252, porque outras exportações ou versões do Sinan NET podem diferir. 17 de 70 campos rotulados: o `.def` da
sífilis em gestante descreve só 28 campos; os outros 42 do DBF (identificação, endereço, datas de controle) são copiados sem
rótulo, e agora o log os lista. Tempo: 86 s no Windows (contra ~14 s estimados pela taxa da nuvem para 1,4 milhão de células),
sem saber ainda em que fase; o log passou a cronometrar leitura, anotação e gravação. Linhas = registros: OK.

### 2026-10-22 — Nomes por extenso no cabeçalho: "Nome (CAMPO)", quatro fontes em ordem
Pedido do usuário depois do primeiro xlsx real. Cabeçalho da aba `dados` vira `Nome por extenso (CAMPO)`, `Nome — rótulo
(CAMPO_rotulo)`, `Idade em anos (NU_IDADE_N_anos)`, `Faixa etária (NU_IDADE_N_rotulo)`; `--sem-nome-extenso` mantém o nome
curto. Nova aba `campos` (coluna, nome, campo DBF, tipo, fonte do nome, rótulo TabWin, tabela de rótulos). Fontes, em ordem:
(1) CSVs em `dicionarios/` ao lado das tabelas (formato do `dicionario_tuberculose.csv` do projeto de análise anterior: `variavel`
ou `variavel_dbf_observado` + `nome_campo`; ou `campo,nome`) — ainda não copiados para este repositório; (2) tabela interna
com os nomes dos campos 1–30 e de controle da ficha de notificação individual do Sinan NET (digitada em `names.py`, única
exceção à regra "não digite dicionário à mão", porque nenhum `.def` dá esses nomes e os rótulos do TabWin para eles são
siglas: "Mun US Noti", "Escolar SinanNET"); (3) rótulo da linha do `.def` do agravo usada para o campo, limpo da palavra de
tabulação ("Ano da Notific" → "Data Notific", "Mun Resid CE" → "Mun Resid", descartando "Mes/Trim/Fx Etária/Reg Metr/UF sobre
código de município"); (4) rótulo do mesmo campo em outro `.def` (NotIndiviNet primeiro). Limite conhecido da fonte 4: o mesmo
nome de campo pode ter outro sentido em outro agravo (TRATAMENTO é data na leptospirose, tipo de entrada na TB); a aba
`campos` registra a fonte de cada nome para que isso seja auditável. Limite da fonte 3: os rótulos do TabWin são
abreviados; o remédio é a fonte 1 (backlog). 105 testes passando.

### 2026-10-22 — Dicionários CSV do projeto anterior: o do próprio agravo vence; ficha vence CSV alheio
Copiados `dicionario_{tuberculose,hans,lta,lv}.csv` para `tabelas/dicionarios/` (251 variáveis; 19 com nome diferente entre
agravos, ex.: TRATAMENTO = "Tipo de Entrada" na TB e "Data do início do tratamento" na LV). Regras: (1) o CSV do agravo
reconhecido (`DEF_TO_CSV` em `names.py`) é lido antes dos outros; (2) linhas `match_dbf = def_tabwin` (completadas pelo s04b a
partir do `.def`, com o rótulo do TabWin — "Ano Diagnóstico" para DT_DIAG) são ignoradas; (3) nomes que são só "(campo interno)"
são ignorados; (4) para os campos da ficha de notificação, a tabela interna vence um CSV de outro agravo (que traz ruído de
extração, "Semana epidemiológic a"), mas perde para o CSV do próprio agravo. Cobertura dos nomes em DBF sintético (campos do
`.def` + NU_NOTIFIC/NM_PACIENT): TB 81 campos → 52 CSV, 26 `.def`, 3 ficha; hanseníase 48 → 41/4/3; LV 55 → 53/0/2;
LTA 59 → 42/14/3; sífilis gestante 30 → 17 CSV alheio (campos comuns), 10 `.def`, 3 ficha; sífilis adquirida 56 → 16/36/3,
1 sem nome; dengue 64 → 31/30/3 (medido antes da regra 4; depois dela parte dos "CSV alheio" passa para "ficha"). 107 testes.

### 2026-10-22 — Base real TB (Windows do usuário): a gravação do xlsx é 89% do tempo
TUBENET.DBF, 17.201 registros × 130 campos, cp1252 (223 letras do português × 49), `TuberculNET5_0.def`, 63 campos rotulados,
125/130 nomes por extenso (83 do CSV de TB). Fases: leitura 3,2 s, anotação 0,8 s, gravação 33,8 s (xlsx de 15,3 MB); total
37,9 s. Taxa de gravação ≈ 100 mil células/s, igual à da nuvem; os 86 s do SIFGENET de manhã (1,4 milhão de células) devem ter
sido primeira execução (antivírus sobre o python.exe recém-extraído) e não foram repetidos. Consequência para bases grandes:
o gargalo é o openpyxl, não o pandas; para 1 milhão de registros × 100 colunas estimam-se ~17 min só de gravação, mais a
memória. Opções no backlog (PLANO P1). Ajustes desta rodada: UFCODIGO/UFCCODIG na mesma UF deixam de gerar aviso; FONETICA_N e
SOUNDEX ganham nome na tabela da ficha. Sem nome ainda: OUTRAS_DES, ID_DISTR_2, NU_PRONT_A (específicos da TB 5.0, fora do CSV).

### 2026-10-22 — Unidades (CNES), ocupação e outras tabelas externas do TabWin
Pedido do usuário: rotular `ID_UNIDADE`/`ID_UNID_AT`/`PRE_UNIPRE` (código CNES de 7 dígitos). As linhas do `.def` para esses
campos apontam para tabelas DBF externas do TabWin (`unidanet.dbf`, `UNIDINVEST.DBF`, `ocupanet.dbf`, `regionet.dbf`,
`paisnet.dbf`, `distrnet.dbf`, `bairrnet.dbf`, `agravnet.dbf`), que não vieram na cópia de `tabelas/tab_sinannet/`. Decisão:
`src/sinan_anotador/lookup.py` lê essas tabelas quando existem na pasta das tabelas, em DBF ou em CSV de mesmo nome
(`unidanet.csv`, colunas `ID_UNIDADE,NM_UNIDADE` ou `codigo,nome`), e gera `<campo>_rotulo` como com os `.cnv`: código sem
correspondência → `[codigo] sem rótulo`, vazio → `Ign/Branco`. Comparação exata e numérica (zeros à esquerda). Arquivo
referido ausente mas outro com a mesma coluna de nome presente (UNIDINVEST → unidanet, ambos `NM_UNIDADE`) → usa o
presente, com aviso. Na aba `dicionario` entram só os códigos presentes na base (a tabela de unidades do Brasil tem centenas
de milhares de linhas). Teste com `unidanet.dbf` e `ocupanet.csv` sintéticos (`tests/test_lookup.py`); 110 testes. Fontes
do arquivo real, por ordem: TabWin instalado na SESA; `TAB_SINANNET.zip` no FTP do DATASUS; como melhoria, CSV
reduzido do CNES público (`BASE_DE_DADOS_CNES_AAAAMM.zip`, `tbEstabelecimento`), que traz também município e tipo da
unidade e cobre unidades extintas. Critério para trocar unidanet por CNES: fração de códigos `sem rótulo` em `ID_UNIDADE`
na base real, medida antes.

### 2026-10-23 — Tabelas externas do TabWin em `tabelas/tab_sinannet/` (TAB_SINANNET.zip, DATASUS, março de 2021)
Os 13 `.dbf` do `TAB_SINANNET.zip` (FTP do DATASUS) entraram no repositório; `UNIDTOTAL.DBF`
(272 MB) ficou fora do git (limite do GitHub de 100 MB; `.gitignore`). Conteúdo conferido:
- `UNIDANET.DBF` 37.693 unidades notificadoras e `UNIDINVEST.DBF` 55.658 unidades (ambas com `ID_UNIDADE`, `NM_UNIDADE`,
  município, UF, esfera, natureza jurídica), cp850. Elas se complementam: 11.665 códigos de UNIDANET não estão em UNIDINVEST e
  o HU Walter Cantídio (2561492) só está em UNIDINVEST. Decisão: cadeia por coluna de nome comum (`NM_UNIDADE`): o arquivo que
  o `.def` cita é o principal e os outros do mesmo `.def` com a mesma coluna são complemento, com os códigos presentes na base
  listados na aba `dicionario`. Ceará: 1.712 e 2.878 unidades. Carga: 2,3 s + 3,2 s, uma vez por processo (cache).
- `OCUPANET.DBF` 2.671 CBO; `PAISNET.DBF` 266; `REGIONET.DBF` 373; `DISTRNET.dbf` 555 (cp1252); `MUNICNET.DBF` 5.717 e `UF.DBF`
  não são citados pelos `.def` (município já vem do `.cnv`); `CNAENET.DBF` e `USDISNET.DBF` idem.
- `BAIRRNET.DBF` vem vazio (0 registros): tabela recusada com aviso, ID_BAIRRO segue sem rótulo.
- `AGRAVNET.DBF` não é tabela de nomes: são 14.200 linhas só com o código CID em `ID_AGRAVO`, sem `NM_AGRAVO` (estrutura de
  registro de notificação, todos os outros campos vazios; confirmado que não há dado de caso). O leitor passou a recusar
  tabela sem a coluna de nome esperada (só adivinha quando a tabela tem exatamente duas colunas).
Limite: retrato de 2021; unidades criadas depois saem `[codigo] sem rótulo`. Medida pendente na base real: fração de
`ID_UNIDADE_rotulo` sem rótulo; se alta, gerar `unidanet.csv` do CNES público. 111 testes (`tests/test_lookup.py` cobre as
tabelas reais: HU Walter Cantídio via complemento, CBO 223505 → ENFERMEIRO, país 1 → BRASIL).

### 2026-10-24 — `unidanet.csv` a partir do CNES público (pedido do usuário, antes da medida na base real)
Contexto: a regra de 2026-10-22 era trocar as tabelas do TabWin (retrato de 2021) pelo CNES só depois de medir a fração de
`ID_UNIDADE` sem rótulo no TUBENET real. O usuário pediu gerar o CSV já (24/10), sem essa medida; ela continua pendente e
passa a servir para medir o ganho do CSV. Fonte: `ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_202609.ZIP` (745 MB, publicado
em 15/10/2026), arquivo `tbEstabelecimento202609.csv` (todos os estabelecimentos já cadastrados, ativos e inativos).
Critérios de aceite, escritos antes de baixar:
1. Cobertura: pelo menos 99% dos códigos de `UNIDANET.DBF` ∪ `UNIDINVEST.DBF` (2021) estão em tbEstabelecimento 202609.
   Abaixo disso o CSV não substitui as tabelas do TabWin: fica como principal e as DBF como complemento (cadeia já existente).
2. Nomes: em 200 códigos comuns sorteados (semente 20261024), pelo menos 90% têm o mesmo nome depois de normalizar (maiúsculas,
   sem acento, espaços colapsados), comparando `NM_UNIDADE` com `NO_FANTASIA`; o restante é relatado como renomeação/divergência.
3. Controles: 2561492 (HU Walter Cantídio) e 2.000 códigos presentes só em UNIDINVEST continuam rotulados.
4. Os 111 testes continuam passando, mais testes novos: CSV vence o DBF de mesmo radical quando os dois existem, e o DBF
   complementa o CSV na cadeia.
5. Tamanho: o CSV (código, nome) entra no git se tiver menos de 50 MB (aviso do GitHub); acima disso o `lookup.py` passa a ler
   `.csv.gz` e o arquivo entra comprimido.
Decisão de desenho: em `find_lookup_file`, o CSV passa a vencer o DBF de mesmo radical (hoje é o contrário), e `lookup_chain`
acrescenta o DBF do mesmo radical como complemento. Nome usado: `NO_FANTASIA`, com `NO_RAZAO_SOCIAL` quando o fantasia está vazio.
Alternativa descartada: apagar as DBF do TabWin do repositório (perderia os nomes de 2021 para códigos que o CNES não tenha).
Resultados (medidos em 2026-10-24, `scripts/make_unidanet_csv.py tmp/cnes/tbEstabelecimento202609.csv.gz --medir`):
- `BASE_DE_DADOS_CNES_202609.ZIP` sha256
  cd74a6be…99208, 109 membros; só `tbEstabelecimento202609.csv` (303 MB, 640.122 estabelecimentos) foi trazido, comprimido em
  `tmp/cnes/tbEstabelecimento202609.csv.gz` (92 MB, sha256 8bac9169…bec5d, fora do git). O zip não tem tabela de estabelecimentos
  excluídos (só `tbMotivoDesativacao`): o CNES público retira do `tbEstabelecimento` os códigos desativados.
- Critério 1 (cobertura ≥ 99%): **reprovado**, 94,76% (63.794 de 67.323 códigos de 2021 estão no CNES 2026; 3.529 ausentes,
  unidades desativadas). Consequência pré-registrada aplicada: o CSV é a tabela principal e as DBF de 2021 ficam como
  complemento na cadeia; nenhum código que tinha rótulo perdeu rótulo.
- Critério 2 (mesmo nome em ≥ 90% de 200 sorteados): **reprovado**, 73% (146/200). As 54 diferenças vistas são renomeações
  (CSF→USF, UBS↔USF, "HOSPITAL SANTO ANTONIO"→"HOSPITAL MUNICIPAL DR ANTONIO CARLOS DA SILVA MONNERAT"): o CNES traz o nome
  atual e o TabWin o de 2021. Lido como: o CSV muda o rótulo de cerca de um quarto das unidades em relação à versão anterior,
  para o nome vigente; não invalida o CSV.
- Critério 3: aprovado (2561492 → HOSPITAL UNIVERSITARIO WALTER CANTIDIO; 1.886 dos 2.000 códigos só de UNIDINVEST rotulados
  pelo CSV, os 114 restantes pelo DBF na cadeia).
- Critério 4: 113 testes passando (111 + 2 novos: CSV vence o DBF e o DBF complementa; `.csv.gz` lido). 122 s.
- Critério 5: `unidanet.csv` com 23,2 MB (ID_UNIDADE,NM_UNIDADE; nome = NO_FANTASIA, ou NO_RAZAO_SOCIAL quando vazio; nenhum
  nome com vírgula ou aspas): entra no git como `.csv`. Carga 1,7 s por processo (as DBF: 2,2 s + 3,2 s).
- 576.328 códigos do CNES não estavam nas tabelas de 2021 (unidades novas ou que nunca notificaram): é o ganho esperado na
  base real, ainda não medido (pendência: fração de `ID_UNIDADE_rotulo` sem rótulo no TUBENET real, antes e depois do CSV).
Atualização: refazer com o `BASE_DE_DADOS_CNES_AAAAMM.ZIP` mais recente do FTP (mensal) e commitar o CSV novo.

### 2026-10-25 — Cobertura das tabelas externas no log
Contexto: o TUBENET real rodado pelo usuário em 24/10 (17.201 registros, 63,6 s, `unidanet.csv` carregado) não trazia no log a
fração de `ID_UNIDADE` sem rótulo, que era a medida pendente; eu tinha dito que trazia. Decisão: o log ganha uma linha por campo
com tabela externa: registros preenchidos, quantos cada tabela da cadeia rotulou (CSV do CNES, DBF de 2021) e quantos ficaram
sem rótulo, com % e códigos distintos (`annotate.lookup_coverage`, teste em `tests/test_lookup.py`). Medida a ler no próximo
TUBENET: a linha `Cobertura ID_UNIDADE`.

### 2026-10-25 — Rótulo de município e UF sem o código na frente
Pedido do usuário, ao inspecionar o TUBENET anotado: "em vez do nome do município sair como '230650 Itapiúna', pode ser só
'Itapiúna'". Levantamento nos 134 `.cnv`: o rótulo começa pelo próprio código em todas as 28 tabelas `Munic??.cnv`, em
`UFcodigo.cnv` ("23 Ceará"), em outras listas de municípios (Capital, ClusterBR, Munfront, NHEMUNBR, TBmunTRM, TBpri181,
Mun_indig) e em `TipoUnidade.cnv` ("01 Posto de Saúde"); e também, por coincidência, em `nudoseMB.cnv` ("12 doses") e
`nudosePB.cnv` ("6 doses"), onde tirar o prefixo estragaria o rótulo. Decisão: tirar o prefixo (≥ 2 dígitos + espaço) só nos
rótulos vindos das tabelas de município (`Munic??.cnv`) e de UF (`UFcodigo`/`UFCCODIG`), na aba `dados` e na aba `dicionario`
(`annotate.strip_code_prefix`); o código continua na coluna da esquerda. As demais tabelas (Capital, TipoUnidade…) são
agrupamentos, não rotulam campo, e ficam como estão. Alternativa descartada: regra geral "rótulo que começa pelo próprio
código" (erraria nas doses). Oráculo dos testes (`tests/synthetic.py`) e teste do critério 5 reescritos com a mesma regra, este
último lendo os nomes direto do `Municce.cnv`. 113 testes.

### 2026-10-25 — Medida pendente do CNES: unidades sem rótulo no TUBENET real = 0 (informado pelo usuário)
Usuário inspecionou o `TUBENET_anotado.xlsx` de 24/10 (17.201 registros, `unidanet.csv` do CNES + DBF de 2021 na cadeia) e
informou "ID_UNIDADE_rotulo vazia = 0": nenhuma unidade notificadora ficou sem rótulo. Fecha a medida pendente de 2026-10-22 e
2026-10-24. Não há o valor "antes" (só DBF de 2021) para a mesma base; a linha `Cobertura ID_UNIDADE` do log, a partir do próximo
zip, mostra quantos registros cada tabela da cadeia rotulou, o que dá o ganho do CSV sem rodar duas vezes.

### 2026-10-25 — Duplicidades: ponto de partida são as definições dos manuais do Sinan, não as chaves herdadas
Contexto: início da sessão 02 (aba `duplicidades`). O usuário pediu que antes de qualquer critério se levantassem as definições dos
manuais do Sinan, gerais e por agravo.
Decisão: o documento `docs/duplicidades_definicoes_manuais.md` é a referência de definições (com fonte e página). O que ele fixa:
(a) a chave padrão do Sinan NET (primeiro + último nome, data de nascimento, sexo; filtros: nome completo, idade, nome da mãe,
fonética 1–15) é a alternativa simples que a aba tem de vencer; (b) os tipos a distinguir são duplicidade verdadeira, duplo
registro (transferência; recidiva/reingresso), homônimo e, por agravo, "evento diferente" (novo acidente, nova violência, nova
gestação); (c) regras por agravo: agudos = mesmo evento pelo período prodrômico (sem número nos manuais); TB/hanseníase = mesma
unidade + mesmo tratamento (duplicidade) ou unidades diferentes no mesmo tratamento (transferência, vincular); Aids = qualquer
período; sífilis em gestante = 12 meses entre diagnósticos (SES-DF), ou 280 dias (script d02 do projeto de análise anterior) — a escolher; (d) o DBF traz
`NDUPLIC_N` (1 = já marcado "não listar"), `IN_VINCULA`, `FONETICA_N` e `SOUNDEX`, a aproveitar. Divergência registrada: o MS
(2007) mantém a primeira notificação; a SESA (sífilis, 2025) mantém a mais completa com diagnóstico mais antigo.
Alternativas descartadas: partir direto das chaves do `x01`–`x04`/`d02`–`d04` (foram feitas para outra pergunta: excesso
estadual × federal) sem antes saber o que o Sinan e a área técnica chamam de duplicidade.
Consequência: o critério de aceite da aba (a escrever antes de medir) compara a chave padrão do Sinan com as chaves adicionais na
base sintética e, depois, na base real do usuário; a janela dos agudos e a regra de sífilis entram como "Depende do usuário".

### 2026-10-25 — Duplicidades: três escolhas do usuário sobre o §5 do levantamento
Contexto: perguntas deixadas em `docs/duplicidades_definicoes_manuais.md` §5 depois do levantamento dos manuais.
Decisão (usuário, 2026-10-25): (1) agravos agudos: a aba **mostra a distância em dias** entre as datas de primeiros sintomas (ou do
acidente/ocorrência/diagnóstico, conforme o agravo) e não aplica corte; quem revisa decide. (2) Sífilis em gestante: **12 meses**
entre as datas de diagnóstico separam gestações (regra da NT SES-DF 10/2020), não os 280 dias do script d02 do projeto de análise anterior. (3) Ficha sugerida
para manter: **a do MS** (Normas e Rotinas 2007, p. 24: a notificada primeiro; em empate, a do município de residência); a saída
mostra também completude e data de diagnóstico de cada ficha, para a equipe poder aplicar a regra da SESA se quiser.
Consequência: a janela temporal deixa de ser parâmetro oculto; o único corte em dias embutido é o de sífilis em gestante (365 dias).

### 2026-10-25 — Critério de aceite da aba `duplicidades` (pré-registrado, antes de escrever código e testes)
Contexto: decisões do usuário de 2026-10-25 (distância em dias sem corte nos agudos; 12 meses na sífilis em gestante; ficha sugerida
pela regra do MS) e concordância com os números abaixo ("Concordo, escreva o critério e comece pela sintética").
**Chaves** (nomes sem acento nem pontuação, maiúsculas): `padrao` = primeiro + último nome + data de nascimento + sexo (a do
relatório do Sinan NET; é a alternativa simples a vencer); adicionais: `nome_mae` = nome completo + nome da mãe (ambos
preenchidos), nascimento livre; `nome_nasc1` = nome completo + sexo, nascimento diferente em um só componente (dia, mês ou ano) ou
com dia e mês trocados; `nasc_nome_sim` = mesma data de nascimento + sexo + nome parecido (similaridade ≥ 0,85, `difflib`).
Fora, salvo medida que mostre ganho: `SOUNDEX`/fonética do Sinan. Um par sai uma vez, com todas as chaves que o acharam.
**Etiquetas sugeridas** (nunca decisão): TB e hanseníase pela regra dos cadernos (mesma unidade + mesmo tipo/modo de entrada +
tratamentos sobrepostos → "duplicidade verdadeira?"; unidade ≠ + tratamentos sobrepostos + saída/entrada "transferência" → "duplo
registro por transferência"; tratamentos não sobrepostos ou entrada recidiva/reingresso → "recidiva/reingresso"); sífilis em
gestante: > 365 dias entre diagnósticos → "gestação diferente", ≤ 365 → "mesma gestação?" com os trimestres; aids: "possível
duplicidade (qualquer período)"; agudos: "mesma pessoa, N dias entre eventos" sem corte; nome da mãe preenchido e diferente nos
dois → "homônimo?" em qualquer agravo. Ficha sugerida para manter: a de notificação mais antiga; empate → a do município de
residência (MNR 2007, p. 24). Par com `NDUPLIC_N` = 1 ou `IN_VINCULA` = 1 em algum dos registros vai para a seção "já julgado pela equipe".
**Base sintética** (gerador em `tests/`, verdade conhecida; por agravo: TB, hanseníase, sífilis em gestante, dengue): fundo de
registros únicos; pares plantados com rótulo: (a) duplicata exata, (b) erro de uma letra no nome, (c) nascimento com um componente
errado ou dia/mês trocados, (d) mãe em branco num dos dois, (e) homônimos (1º e último nome, nascimento e sexo iguais; mãe e
município diferentes), (f) TB/hans: transferência e recidiva, (g) gestante: dois diagnósticos > 365 dias e ≤ 365 dias.
**Critérios** (todos têm de passar; falha vira entrada no METODO, não ajuste do critério):
C1 — `padrao` acha 100% dos pares plantados com identidade igual (a, d, e, f, g); homônimos plantados aparecem (é o que o Sinan faz).
C2 — cada chave adicional: revocação ≥ 90% no tipo que ela mira (b → `nasc_nome_sim`; c → `nome_nasc1`; b e c → `nome_mae`) e
precisão ≥ 95% (pares entre pessoas plantadas diferentes, fora os homônimos, ≤ 5% dos pares da chave). Chave reprovada sai da saída
padrão (fica como opção).
C3 — etiquetas: transferência ≥ 90% dos pares (f-transferência); recidiva/reingresso ≥ 90% (f-recidiva); duplicata exata em TB/hans
→ "duplicidade verdadeira?" ≥ 90%; homônimos (e) → "homônimo?" 100%; gestante > 365 → "gestação diferente" 100%, ≤ 365 → "mesma
gestação?" 100%.
C4 — ficha sugerida = notificação mais antiga em 100% dos pares com datas distintas; empate → residência.
C5 — pares com `NDUPLIC_N` = 1 plantado vão 100% para "já julgado"; nenhum registro é removido da aba `dados`.
**Base real** (máquina do usuário, depois): chave adicional fica se ≥ 50% de 30 pares sorteados dela (misturados com pares `padrao` como
controle, julgamento às cegas pelo usuário) forem a mesma pessoa; a concordância da etiqueta com o julgamento é só descritiva na 1ª
rodada. Ganho a reportar: pares confirmados além do relatório do Sinan e tempo de revisão.
**Saída** (forma a discutir com o usuário, 2026-10-25): aba `duplicidades` completa (todas as colunas de identificação, datas,
unidade, município, chaves, dias, etiqueta, regra, ficha sugerida, completude) e aba `duplicidades_resumo` com poucas colunas, para
a equipe acompanhar e mandar às regionais, com coluna em branco para a decisão da equipe.
Correção (2026-10-25, antes de olhar qualquer resultado além do erro de lógica): o texto acima dizia "b e c → `nome_mae`"; a chave
`nome_mae` usa o nome completo, logo não pode achar o par com erro de letra no nome (b). Alvo de `nome_mae` em C2 é só (c). Não é
ajuste de limiar; é correção de um alvo impossível.

### 2026-10-25 — Resultado do critério da aba `duplicidades` na base sintética: C1–C5 aprovados
Implementação: `src/sinan_anotador/duplicates.py` (chaves, etiquetas, ficha sugerida, duas abas), ligado ao `cli.py` (opção
`--sem-duplicidades`) e ao `excel.py` (abas `duplicidades` e `duplicidades_resumo` entre `dados` e `campos`). Gerador com pares
plantados: `tests/synthetic_dups.py` (fundo de 200 pessoas únicas + 8 ou 9 tipos × 10 pares); testes: `tests/test_duplicates.py`,
para TUBENET, HANSNET, SIFGENET e DENGNET. Resultado (147 testes no total, 185 s): C1 100% (60 pares `padrao` por agravo, inclusive
os 10 homônimos, como o Sinan faria); C2 revocação 10/10 em `nasc_nome_sim` (erro de letra), `nome_nasc1` e `nome_mae` (nascimento
errado), 0 pares entre pessoas diferentes em qualquer chave adicional; C3 etiquetas 10/10 em homônimo, transferência, recidiva,
duplicata exata (TB e hans), gestação diferente e mesma gestação; C4 e C5 100%. Um ajuste de implementação feito antes de rodar
os testes de etiqueta, não depois: tratamentos "sobrepostos" admitem intervalo de até 60 dias entre a saída por transferência e o
início na unidade de destino (`TRANSFER_GAP_DAYS`), porque a unidade que recebe registra o início dias depois da saída da origem.
Limites conhecidos: base sintética não tem erro de digitação no nome da mãe nem nome com partícula faltando ("DA"); a chave
`nasc_nome_sim` só compara nomes que partilham o primeiro ou o último token (custo); grupos com mais de 50 registros na mesma
chave só pareiam vizinhos por data. Tempo em base grande (dengue, 1 milhão) não medido.

### 2026-10-25 — ADS no resumo das duplicidades; "etiqueta" vira "tipo sugerido"
Contexto: o usuário disse que a ADS é coluna importante na versão resumida (é a unidade que recebe e cobra a correção) e perguntou o
que era "etiqueta". Decisão: (1) a ADS vem do município pela tabela de regionalização da SESA (ver Fontes), não do campo
`ID_REGIONA` do Sinan, que depende da tabela carregada em cada instalação e tem nome antigo (CRES); `ID_REGIONA`/`ID_RG_RESI` ficam
como reserva. O resumo abre com `ADS_notificacao_A`, `ADS_notificacao_B` e `ADS_residencia` (uma só quando as duas fichas concordam,
"X / Y" quando não), e as duas abas saem ordenadas por ADS da primeira notificação e data, a ordem em que uma regional lê. A
completa traz também `ADS_residencia_A/B`. (2) A coluna `etiqueta_sugerida` passa a `tipo_sugerido`: é o tipo de duplicidade na
linguagem dos cadernos (duplicidade verdadeira, duplo registro por transferência, recidiva/reingresso, homônimo, gestação diferente),
com "?" onde falta confirmação humana. Testes: 35 em `test_duplicates.py` (ADS preenchida em todos os pares; tabela com 184/22/5).

### 2026-10-25 — Log das duplicidades conta os registros que nenhuma chave alcança
Pedido do usuário antes de testar no SIFGENET real. O log passa a trazer "Registros que nenhuma chave alcança" (sem nome, ou sem data
de nascimento e sem nome da mãe) e o alcance parcial: sem nascimento (só nome+mãe), sem sexo (chave padrão com sexo em branco), sem
mãe (sem nome+mãe), nome de uma palavra (sem chave padrão). Nenhum registro sai da aba `dados`. 36 testes de duplicidade.

### 2026-10-26 — Sífilis em gestante: janela de 45 semanas entre diagnósticos (substitui os 12 meses de 2026-10-25)
Contexto: a entrada "Duplicidades: três escolhas do usuário" (2026-10-25, item 2) fixou 12 meses (365 dias), da NT SES-DF 10/2020.
Decisão (usuário, 2026-10-26): diagnósticos com mais de **45 semanas (315 dias)** entre si são gestações diferentes; até 315 dias,
"mesma gestação?". `GESTATION_WINDOW_DAYS = 45 * 7`; a coluna `regra` diz "SES-DF, NT 10/2020, p. 6 (janela de 45 semanas)", porque
o corte já não é o da nota. Alternativas descartadas: 12 meses (SES-DF) e 280 dias (script d02 do projeto de análise anterior). Consequência: pares com 316 a 365
dias entre diagnósticos passam de "mesma gestação?" a "gestação diferente". No critério C3 (2026-10-25) o corte de gestante passa a
315 dias; não é ajuste pós-hoc de limiar de aceite: os pares sintéticos plantados (10–200 e 400–800 dias) ficam do mesmo lado nas
duas janelas, e foi acrescentado teste da fronteira (315 → mesma gestação, 316 → gestação diferente). 153 testes passando.

### 2026-10-28 — Manual do usuário em `docs/MANUAL.md`, no repositório e no zip; não em wiki
Contexto: projeto publicado com DOI (Zenodo, v0.2.0). O usuário pediu um manual entendível por terceiros, sobretudo das regras de
duplicidade, e perguntou se seria melhor nos `.md` existentes, numa wiki do GitHub ou outra forma.
Decisão: documento novo, `docs/MANUAL.md`, dentro do repositório, copiado para o zip como `MANUAL.md` (CRLF) e ligado do README,
do `LEIA-ME.txt`, do template de issue e das notas do release. Os dois documentos anteriores ficam como estão e passam a ser
referência citada pelo manual: `METODO.md` é diário de decisões (append-only) e `duplicidades_definicoes_manuais.md` é
levantamento de fontes; nenhum dos dois é instrução de uso, e o §5 do levantamento é anterior às decisões (está superado por
elas). Alternativas descartadas: (a) wiki do GitHub: é um repositório git separado, fora do tarball que o Zenodo arquiva em cada
release, fora da tag, fora do zip e sem CI; rompe o acoplamento versão–documentação que o DOI promete; (b) reescrever os `.md`
existentes: mudaria a natureza do diário e da revisão de fontes. O manual descreve o que `duplicates.py` faz nesta versão, não o
que foi planejado: ordem das condições de `classify()`, códigos de entrada/saída por agravo, tolerância de 60 dias, janela de 315
dias, similaridade 0,85, bloco de 50, regra da ficha a manter e critério de "já julgado". Anti-descolamento: `tests/test_manual.py`
extrai por `ast` cada rótulo que `classify()` retorna e cada motivo de `_keep()`, e exige que apareçam no manual, junto com as
chaves, as constantes, os campos e códigos de cada perfil e as colunas das duas abas (geradas por `build_tables` numa base
mínima). Não verifica semântica; acusa mudança de regra sem mudança de texto. Pendente: o usuário vai testar o manual com o zip
(seguir o manual usando o pacote). Fora do escopo por ora: GitHub Pages servindo `docs/` e PDF do manual anexado ao release;
ficam como opções se a leitura no GitHub ou no `.md` dentro do zip se mostrar insuficiente para as equipes.

### 2026-10-28 — Manual em PDF gerado do `MANUAL.md` (WeasyPrint), no zip e no release
Contexto: o usuário informou que há colegas que trabalham com o manual impresso; o `.md` dentro do zip e a página do GitHub não
servem para isso.
Decisão: um só texto-fonte (`docs/MANUAL.md`) e um conversor, `build/build_manual_pdf.py`: markdown → HTML (`markdown` 3.11.2, com
ids de título iguais aos do GitHub, para o sumário do `.md` continuar válido) → PDF A4 (`weasyprint` 70.0, CSS de mídia paginada:
capa com versão, data, DOI de conceito e endereço dos documentos citados; sumário com número de página; rodapé "página N de M";
quebra de página só antes das seções 1 e 4; `thead` repetido nas tabelas que atravessam página). Links para outros arquivos do
repositório viram nome do arquivo (o endereço da árvore da versão está na capa); links externos imprimem o endereço. O PDF é
gerado no CI (artefato, 30 dias) e no release (anexado, com sha256, e copiado para o zip como `MANUAL.pdf`); não é versionado no
git. Alternativas descartadas: pandoc + LaTeX (pesado no runner, fontes e acentuação a gerir); Chrome headless (não suporta as
caixas de margem do CSS paginado, logo sem "página N de M" sem script extra); committar o PDF (binário que muda a cada edição do
texto e que o Zenodo arquivaria duplicado; o release e o zip já o distribuem). Verificação feita: 14 páginas, metadados
(título, autor) corretos, tabelas dentro da margem nas páginas 7 e 11 (as mais largas), inspeção visual de todas as páginas em
baixa resolução. Limite: o CI não compara o PDF com uma referência; só garante que ele é gerado e que os links do sumário
resolvem.

### 2026-10-28 — Base de outro estado: ADS vazia quando a regional do Sinan está em branco (era "Ign/Branco")
Contexto: o usuário perguntou o que acontece com as colunas de ADS numa base que não é do Ceará (sem base real para testar).
Medida em base sintética de TB (280 registros, 80 pares plantados, municípios de São Paulo), três cenários: `ID_REGIONA` com
código da REGIONET, em branco, e mistura CE + SP. Nenhum trava; chaves, tipos e ficha sugerida saem iguais aos da base cearense.
Defeito achado: com município fora da tabela da SESA e `ID_REGIONA` em branco, `_ads()` aceitava o rótulo "Ign/Branco" do campo
como nome de regional: coluna de ADS com "Ign/Branco", par ordenado sob a letra I e não no fim, log sem contar o lado como sem ADS.
Decisão: `_ads()` devolve vazio quando o código de `ID_REGIONA`/`ID_RG_RESI` está em branco ou sem nome na REGIONET; com código
conhecido continua devolvendo o nome da regional do Sinan (por exemplo "GVE XXVI SAO JOAO DA BOA VISTA"). Teste de regressão
`test_ads_outside_ceara_falls_back_to_sinan_regional_or_blank` (falhava antes da correção, passa depois); manual §4.8 descreve o
comportamento. Limite: os códigos de GVE da base sintética são inventados (um colidiu com regional do Paraná, porque a REGIONET é
nacional e a busca é só por código); em DBF real os códigos são os do próprio Sinan e não há motivo para colisão, mas isso não foi
verificado em base real.

### 2026-10-28 — Base real de sífilis congênita (SIFICNET.DBF): nome não reconhecido e falha na gravação do xlsx
Contexto: log do usuário com a base real (7.743 registros, 103 campos, cp1252): "o nome do arquivo (SIFICNET.DBF) não foi
reconhecido; agravo escolhido pelo conjunto de campos: NotnegatNET.def (5 de 5 campos presentes)", 3 de 103 campos rotulados, e
`RESULTADO: FALHA` com `IllegalCharacterError` do openpyxl numa célula de `DS_OBS`.
Causas, verificadas no código: (1) a tabela de nomes conhecidos tinha `SIFCNET`, copiada do padrão `A` do `SifilisNET.def`
(`Sifc*.DB?`), e não o nome que o Sinan NET grava (`SIFICNET`); os testes sintéticos usavam o mesmo nome errado e por isso nunca
acusaram. (2) A escolha por conjunto de campos ordenava pela proporção de campos do `.def` presentes no DBF; recomputado com os
103 campos do log: NotnegatNET 5/5 = 1,00, SifilisNET 47/54 = 0,87, NotIndiviNet 23/34 = 0,68 — um `.def` pequeno e genérico, só
com campos da ficha de notificação, ganha de qualquer `.def` de agravo. Os 7 campos do SifilisNET ausentes são os `CRI_*`
(critérios de definição), inferência: retirados em versão posterior da ficha. (3) O openpyxl recusa caracteres de controle
(0–31, exceto tabulação, LF e CR); o caractere não aparece na mensagem porque é invisível (inferência: `\x00` de preenchimento
ou `\x1a` de campo memo). A gravação é o último passo, então a falha perdia a anotação e as 632 duplicidades já calculadas.
Decisão: `SIFICNET` entra nos nomes conhecidos (`SIFCNET` fica, por compatibilidade com o padrão do TabWin); a escolha por campos
passa a exigir metade dos campos do `.def` (mínimo 5) e, entre os elegíveis, prefere o maior número absoluto de campos presentes,
depois a proporção; o log lista até três outros candidatos com a contagem. Com a base do log: SifilisNET (47 de 54), outros
GestSifNET (15 de 28), HivGestNET (15 de 29). Um DBF que é de fato a notificação individual genérica continua escolhendo
`NotIndiviNet` (teste). Na gravação, `_cell_value` remove os caracteres que o openpyxl recusa e conta as células por aba e coluna;
`write_xlsx` acrescenta ao log "AVISO: N células continham caracteres de controle … dados.DS_OBS (n)". A limpeza é só na
gravação: o valor lido do DBF segue íntegro para as chaves de duplicidade e para o dicionário. Alternativa descartada: limpar na
leitura (`read_dbf`), que mudaria o dado antes das chaves e esconderia do log a origem.
Verificação: testes novos `test_detect_sifilis_congenita_real_name`, `test_detect_by_fields_prefers_specific_def_over_generic`
e `tests/test_excel.py` (célula com `\x00`, `\x1a` e `\x07`; tabulação e quebra de linha preservadas; aviso com contagem por
coluna; sem aviso quando não há nada a limpar); suíte completa 166 passados, 4 pulados. Ponta a ponta com SIFICNET sintético
(49 campos, `\x00\x1a` injetado em `NM_PACIENT`): nome reconhecido, 34 de 49 campos rotulados, aviso de 1 célula, `RESULTADO: OK`;
renomeado para `EXPORT.DBF`, a escolha por campos acerta SifilisNET. Limite: não foi rodado na base real do usuário; os 7 campos
`CRI_*` do `.def` que o DBF não tem continuam só sem rótulo, como antes.

### 2026-10-28 — Cinco bases reais (HANSNET, LEISHNET, LTANET, MENINNET, SIFGENET): o que os logs mostraram e o que mudou
Contexto: logs da 0.3.0 no Windows do usuário, todos `RESULTADO: OK`, cp1252 em todos, linhas gravadas iguais às lidas.
Achados, por ordem de importância, e decisões:
1. MENINNET: `NM_PACIENT` existe e está em branco nos 5.902 registros; 0 pares e só a linha "sem nome 5902" no fim do bloco.
   Inferência: export sem identificação. Decisão: `AVISO` explícito quando o nome falta em metade ou mais dos registros.
   O DBF não foi aberto aqui; cabe ao usuário confirmar a causa.
2. LEISHNET e LTANET: pares com 17.399 a 23.443 dias entre `DT_SIN_PRI` (47 a 64 anos), impossíveis numa base que começa com
   os migrados do Sinan Windows. Decisão: limite = amplitude de `DT_NOTIFIC` da própria base + 366 dias
   (`IMPLAUSIBLE_MARGIN_DAYS`); acima dele o tipo é `data implausível? … conferir as datas`. Alternativa descartada: corte
   fixo (1993, início do Sinan), porque depende de saber a história de cada base; a amplitude observada vale para qualquer
   arquivo. Limite: erro de data dentro da amplitude (2015 por 2025) continua invisível.
3. LEISHNET: 425 linhas "mesma pessoa, N dias" no log, uma por valor. Decisão: faixas 0 / 1–7 / 8–30 / 31–90 / 91–365 /
   >365 no rótulo e na contagem do log; os dias exatos ficam entre parênteses e na coluna `dias_entre_eventos`. As faixas
   são de leitura, não de regra: os manuais não dão corte para os agudos (MANUAL §4.5).
4. `.cnv` ausentes no `TAB_SINANNET.zip`: hanseníase `ESQUETER.CNV`/`ESQUETERatu.CNV`; meningite 9 tabelas (critério,
   etiologia, evolução, aspecto do líquor…). O FTP do DATASUS não é alcançável do ambiente de desenvolvimento. Decisão: usar
   `categorias_cnv` do dicionário do agravo (copiada do `.cnv` real na extração, coluna `fonte_categorias` = "pdf + cnv:…")
   para reconstruir a tabela em memória; resolve hanseníase. Meningite fica sem rótulo nesses campos até alguém copiar as
   tabelas do TabWin ou extrair o dicionário de meningite; o log passa a listar as tabelas numa linha. Alternativa descartada:
   escrever as `.cnv` de meningite de memória (sem fonte verificável; rótulo errado é pior que nenhum).
5. HANSNET `DOSE_RECEB`: três tabelas no `.def` (PB, MB, detalhada); a 0.3.0 usava a primeira (PB) para todos, e "6 doses"
   só é esquema completo em paucibacilar. Levantamento em todos os 58 `.def`: só dois campos têm mais de uma tabela de
   categorias (`DOSE_RECEB` e `EVOLUCAO` do NotIndiviNet). Decisão: regra explícita por campo (`TABLE_SWITCH`): tabela
   escolhida por `CLASSOPERA` em cada registro; `EVOLUCAO` genérico continua na primeira. Alternativa descartada: "a tabela
   com mais categorias", que escolheria a tabela de LTA para a evolução da notificação genérica.
6. Nomes divergentes DBF × `.def`: `BACILOSCO`/`BACILOSCOP` (hanseníase), `DT_DESC3`/`DT_DES3` (LTA). Decisão: tabela de
   aliases em `cnv.py`, aplicada no plano, na lista "não descreve" do log e nos nomes por extenso.
7. Avisos enganosos: `UNIDINVEST.dbf` "sem a coluna ATE_HOSP_1/PRE_UNIPRE" (a tabela é boa, o código está em `ID_UNIDADE`) e
   `BAIRRNET.DBF` "tabela vazia" (194 bytes, só cabeçalho, em todo arquivo). Decisão: coluna de código cai para a primeira
   `ID_`/`CO_`/`CD_` com nota; tabela vazia vira nota por campo citando `NM_BAIRRO`.
8. Nomes por extenso de dicionário alheio: 15 campos têm nome diferente entre os quatro CSVs; 13 são paráfrases, dois são
   homônimos de sentido diferente (`TRATAMENTO`, `HIV`). Decisão: para agravo sem dicionário próprio, o nome de outro CSV só
   vale se todos os CSVs que o definem concordam na primeira palavra; senão fica o rótulo do `.def`.
9. `LEISHNET` e `MENINNET` reconhecidos pelo padrão `A` do `.def`, não pelo nome; entram na tabela de nomes conhecidos.
Verificação: testes novos em `test_annotate.py` (aliases, tabela reconstruída do CSV com e sem CSV, `DOSE_RECEB` por
`CLASSOPERA` com rótulos por registro), `test_lookup.py` (coluna de código alternativa), `test_names.py` (concordância entre
dicionários, alias), `test_duplicates.py` (faixas nos dez limites, data implausível com `DT_SIN_PRI` de 1960 numa base
2020–2024, aviso de nome em branco); `test_manual.py` obriga os rótulos novos a constar do manual. Ponta a ponta com
HANSNET, LEISHNET e MENINNET sintéticos: reconhecidos pelo nome; log com as notas de ESQ_INI_N/ESQ_ATU_N, DOSE_RECEB e a
linha das tabelas ausentes; UNIDINVEST lida para ATE_HOSP_1. Não rodado nas bases reais.

### 2026-10-28 — Varredura das tabelas ausentes e primeiro pacote do TabWin da SESA (TAB_SINANONLINE.zip)
Contexto: depois dos achados de meningite e hanseníase, o usuário pediu a lista completa do que falta para trazer de uma vez.
`scripts/tabelas_ausentes.py` (mesma lógica do `build_plan`: só linhas de categoria, sem agrupamentos nem tabelas de
município) achou 254 `.cnv` distintas ausentes, em 53 dos 58 `.def`, e 2 `.dbf` externos (`localidade.dbf`, `unidtotal.dbf`).
As mais citadas: `CURAOBIT.CNV` (17 `.def`), `sim_naoap.cnv` (13), `CONFDESCA.CNV` e `Reagente.cnv` (10). O pacote
`TAB_SINANNET.zip` de março de 2021 que originou `tabelas/tab_sinannet/` tinha 134 `.cnv`, menos da metade do que seus
próprios `.def` citam.
Primeiro pacote recebido (via Google Drive, pasta Claude_Temporarios): `TAB_SINANONLINE.zip`, 244 KB, 72 `.cnv` e 3 `.def`
(dengue, dengue online 3.0, chikungunya), do TabWin instalado na SESA-CE. Cruzamento: 9 das 254 ausentes estão nele, todas
de dengue/chik; copiadas com o nome do zip. Dos 75 arquivos, 25 são idênticos aos do repositório e 31 diferem: os 3 `.def`
por 1 a 4 bytes de espaço; 21 `Munic*.cnv` em que o repositório tem o mesmo número de categorias ou mais (BA 420 vs 418,
CE 187 vs 185, BR 5657 vs 5658 com os mesmos códigos): o repositório é igual ou mais novo; `NHE.cnv`/`NHEUNIDADE.cnv` com o
repositório maior (409 vs 326, 233 vs 190); `Escolarnet.cnv` igual em categorias, o zip só acrescenta códigos sem zero à
esquerda (` 9`, ` 0`), que o parser já trata; `Confdesc.cnv` com linha de branco `,9` no zip e `,0-9` no repositório.
Decisão: nenhum arquivo existente foi substituído; só os 9 novos entraram. Alternativa descartada: adotar o pacote da SESA
inteiro, porque é mais antigo nas tabelas de município.
Achado derivado: `DengueNET.def` lista para `CRITERIO` duas tabelas, "Conf.Desc ate2010" (`CONFDESC.CNV`: 1 Laboratorial,
2 Clínico-epidemiológico) e "Conf.Desc pos2010" (`CONFDESCDENG2011.CNV`: acrescenta 3 Em investigação); a regra "primeira
tabela" escolhia a antiga para a base inteira. Decisão: `TABLE_SWITCH` por `NU_ANO` (1990–2010 → antiga; demais → 2011),
mesmo mecanismo do `DOSE_RECEB`. Com a antiga, código 3 cai na linha de branco `0-9` e sai "Ign/Branco"; é o que a tabela
oficial diz para aquele ano, e o teste fixa esse comportamento. Dengue continua sem `Evideng.cnv` e `graufhd.cnv` (campos da
ficha antiga de FHD).
O segundo pacote (`TAB_SINANNET.zip` da SESA, 9,4 MB, sem os `.dbf` grandes) não pôde ser lido: o conector do Drive não
entrega arquivo desse tamanho e o proxy do ambiente bloqueia `drive.google.com`; o upload direto no chat e o Remote Control
para o computador do usuário também não funcionaram nesta sessão. Pendente.

### 2026-10-29 — Pacote completo do TabWin em `tabelas/tab_sinannet/`: cobertura de dicionário de 75% para 100% dos campos
Contexto: ao rodar a 0.3.0 em bases reais, vários campos saíram sem rótulo e a varredura de 28/10 achou 254 `.cnv` ausentes.
O usuário temia que o dicionário tivesse se perdido na passagem do repositório privado para este. Conferido por checksum:
`tabelas/` aqui é cópia byte a byte do dicionário do repositório de origem (só `UNIDTOTAL.DBF`, 272 MB, ficou fora, pelo
limite do GitHub, como já registrado) mais as 9 tabelas de dengue/chik de 28/10. Nada se perdeu na publicação. A falta é
anterior aos dois repositórios: a pasta herdada do projeto de origem era uma extração parcial do `TAB_SINANNET.zip`
(138 `.cnv` dos 627 que o zip traz). Correção ao registro de 28/10: o zip nunca "tinha 134 `.cnv`"; a extração é que tinha.
Fonte: `TAB_SINANNET.zip` do FTP do DATASUS (`SINAN/AUXILIAR/`), baixado em 22/10/2026, 44.001.396 bytes, sha256 `24ac0c62…`,
700 entradas (627 `.cnv`, 60 `.def`, 13 `.dbf`), arquivos datados de 24/04/2024. Difere do zip baixado em 07/10/2026 só por
`DIAGNOSCOPIA.cnv`. Dois pacotes do TabWin instalado na SESA-CE, recebidos em 28/10 (`TAB_SINANNET.zip` 9,4 MB, sha256
`f29646e0…`, 627 `.cnv`, 59 `.def`, 12 `.dbf`; `TAB_SINANONLINE.zip` 244 KB, sha256 `5fdda9d1…`), comparados arquivo a arquivo.
Medida, por campo de categoria nos `.def` (`scripts/cobertura_campos.py`, mesma regra do `build_plan`: fora agrupamentos de
ano/mês, município e faixa etária): antes, 1.801 de 2.397 campos com tabela (75,1%) em 58 `.def`, 7 `.def` completos, 245
`.cnv` ausentes em 51 `.def`; com o pacote do DATASUS, 2.452 de 2.453 (100,0%) em 60 `.def`, 59 completos, 1 `.cnv` ausente.
Decisões:
1. Copiados do pacote do DATASUS só os arquivos que faltavam: 486 `.cnv`, 2 `.def` (`AnimaispNET.DEF`, animais peçonhentos;
   `PlanSurtoNet.DEF`, planilha de surto) e `Diagnos.cnv`, com os nomes do pacote. Nenhum arquivo existente foi substituído,
   exceto `PfapolioNET.def`, que na versão de 2024 cita `DIAGNOSCOPIA.CNV` (existe) em vez de `DIAGNOS.CNV` e corrige o padrão
   do DBF. As 6 tabelas de dengue de 28/10 (`Classdeng`, `ConfdescDeng2011`, `evodeng`, `Resultado`, `Sorodeng`, `TipoSistema`)
   ficam na versão do TabWin da SESA, mais nova (`Classdeng` com a classificação de 2014: 10 categorias contra 6).
   `dt_notific.cnv` (0 bytes, citado por nenhum `.def`) não entrou. Alternativa descartada: adotar o pacote inteiro
   substituindo os existentes, porque as tabelas de município e as de dengue do repositório são iguais ou mais novas.
2. `.def` com extensão em maiúsculas (`.DEF`) passam a ser lidos: `def_files()` em `cnv.py`, usado pelo programa, pelos
   scripts e pelos testes no lugar de `glob("*.def")`. Sem isso os dois `.def` novos eram invisíveis.
3. Cabeçalho de `.cnv` com um token a mais (`10  6   33X001`, nas sete `*_regsaudn.cnv` de região de saúde) é aceito;
   antes o parser dizia "sem cabeçalho". Teste unitário com o formato.
4. O teste da tabela reconstruída do dicionário (ESQUETER) passa a tirar os dois arquivos de uma cópia da pasta, porque o
   caso real deixou de existir; confere também que, com a pasta real, a tabela real dá os mesmos rótulos que o CSV.
O que fica sem tabela: `br_uf_nu_sg_dhx.cnv` (UF de infecção, `-LeptoNET`, não está em pacote nenhum), `localidade.dbf`
(bairro em dengue/chik, idem) e `unidtotal.dbf` para um campo de coqueluche (está no repositório de origem, fora do git).
Comparação com os pacotes da SESA (decisão pendente, do usuário): os 627 `.cnv` são iguais aos do DATASUS, salvo
`Municro.cnv` (SESA acrescenta Guaraí/TO) e `Unid_Prisionais.CNV`, tabela local do Ceará (22 unidades prisionais com código
CNES) citada só pelo `NotIndiviNet.def` da SESA. Os 59 `.def` da SESA diferem dos do DATASUS em todos os casos na linha
`A` (padrão do nome do DBF): a SESA traz os nomes reais do export do Sinan NET (`TUBEN*.DBF`, `SifiCN*.DBF`, `LeishN*.DBF`,
`MENINN*.DBF`), que o DATASUS escreve com prefixo curto (`Sifc*.DB?`), e foi isso que obrigou a tabela manual
`KNOWN_DBF_PREFIXES`. Medido: com os padrões da SESA, `SIFICNET.DBF`, `NINDINET.DBF`, `EPIZONET.DBF` e `TETANNET.DBF` passam
a casar o `.def` certo (hoje não casam ou casam o errado) e `LEPTONET.DBF`/`DENGONET.DBF` deixam de ser ambíguos; 53 de 59
nomes casam um só `.def`, contra 47. Fora da linha `A`, cinco `.def` da SESA mudam conteúdo: `AntirabNET` (UF de residência por
`SG_UF`, não `ID_MN_RESI`), `EsquisNET` (acrescenta distrito e bairro), `LeptoNET` (tira mês/trimestre de `DT_SIN_PRI`),
`NotIndiviNet` (acrescenta `Unid_Prisionais`), `ViolenciaNet` (`CICL_VID_AUTOR`, 14 caracteres, impossível em nome de campo
DBF: edição local errada). Proposta: adotar só as linhas `A` da SESA nos 60 `.def` (mantendo o corpo do DATASUS) e
`Unid_Prisionais.CNV`; decidir os cinco conteúdos com as bases reais, campo a campo. Nada disso foi aplicado.
Verificação: `scripts/tabelas_ausentes.py` e `scripts/cobertura_campos.py` depois da cópia (números acima); suíte completa,
186 testes passando e 4 pulados (174 s). Não rodado em base real: o teste com as bases de todos os agravos está marcado para 29/10.

### 2026-10-29 — Linhas `A` dos `.def` da SESA e `Unid_Prisionais.CNV` adotadas (decisão do usuário)
Contexto: ver a entrada anterior. O usuário decidiu adotar, nos `.def` do repositório, só a linha `A` (padrão do nome do DBF) da
versão da SESA-CE, mantendo o corpo do DATASUS, e incluir a tabela local `Unid_Prisionais.CNV`. Os cinco `.def` com outras
diferenças de conteúdo continuam pendentes, salvo a linha que cita a tabela prisional em `NotIndiviNet.def`, que entra com ela.
Critério de aceite, escrito antes de aplicar:
- C1. Os 60 `.def` continuam a ser lidos e, comparados com a versão anterior, diferem só na linha `A` (`NotIndiviNet.def` também
  na linha `XUnid_Prisionais`). `-LeptoNET.def` não existe na SESA e fica como está.
- C2. Nome de export inferido do padrão de cada `.def` (prefixo + `ET.DBF`) casa um só `.def` em pelo menos 53 dos 59, e
  `SIFICNET.DBF`, `NINDINET.DBF`, `EPIZONET.DBF` e `TETANNET.DBF` casam, respectivamente, `SifilisNET`, `NotIndiviNet`, `EpizotNet`
  e `TetneoNET` (hoje: nenhum, nenhum, nenhum e `TetacidNET`).
- C3. `detect_def` com os oito nomes reais já vistos (`TUBENET`, `SIFGENET`, `SIFICNET`, `HANSNET`, `LEISHNET`, `MENINNET`, `LTANET`,
  `DENGNET`) escolhe o mesmo `.def` que antes, com `KNOWN_DBF_PREFIXES` esvaziado no teste (a lista manual continua no código como
  reserva, mas não pode ser o que faz o reconhecimento funcionar).
- C4. Suíte completa passando.
Consequência pré-registrada: se C1–C4 não forem todos atendidos, as linhas voltam à versão do DATASUS (`git checkout`), a tabela
prisional fica e o achado permanece registrado aqui como pendente.
Resultado (2026-10-29, antes da decisão final):
- C1 atendido: 58 linhas `A` trocadas (as de `PfapolioNET.def` e `-LeptoNET.def` já eram iguais ou não existem na SESA); o diff
  contra a versão anterior tem só linhas `A` mais a linha `XUnid_Prisionais` e uma linha em branco em `NotIndiviNet.def`.
- C2 **não atendido por um**: 52 de 59 nomes casam um só `.def` (antes, 50). Os quatro nomes citados casam o `.def` certo. Os sete
  ambíguos são pares legítimos do pacote (`TuberculNET`/`TuberculNET5_0`, `ChagasNET`/`ChagasNET2`, `CoqueNET`/`CoqueNETeste`) e
  `LeptoNET`/`-LeptoNET`. O limiar 53 foi escrito a partir da simulação com o conjunto da SESA, que não tem `-LeptoNET.def`; o
  critério mandava manter esse arquivo, logo o próprio critério contava com 53 num conjunto e media em outro. Erro meu de denominador,
  anotado como tal; a consequência pré-registrada (reverter) fica para o usuário aplicar ou dispensar, e a dispensa é pós-hoc.
- C3 atendido: os oito nomes reais escolhem o mesmo `.def` com a lista manual vazia, agora "pelo padrão de arquivo do .def".
- C4 atendido: 188 testes passando, 4 pulados (181 s).
Achado ao incluir a tabela prisional: no `build_plan`, quando um campo tinha busca em `.dbf` externo e tabela de categorias, a
tabela de categorias vencia. Com a linha `XUnid_Prisionais` em `NotIndiviNet.def`, `ID_UNIDADE` passou a ter só as 22 prisões e o
HU Walter Cantídio saiu "sem rótulo". O mesmo mecanismo já fazia `ID_OCUPA_N` da notificação individual sair pelo `GRUPO1a.CNV`
("Categoria de ocupação classificada na CBO") em vez do nome da CBO em `OCUPANET`. Decisão: busca externa primeiro, tabelas de
categorias do mesmo campo como reserva para códigos que ela não tem, com nota no log. Afeta só `ID_UNIDADE` e `ID_OCUPA_N` de
`NotIndiviNet.def` (levantamento nos 60 `.def`: os únicos campos com as duas coisas, além de `ID_AGRAVO`, cujo `AGRAVNET.DBF`
não tem nomes e por isso continua pelas listas `.cnv`). Os 23 códigos da tabela prisional já estão no `unidanet.csv` do CNES:
a tabela só responderia para unidade que o CNES não tivesse. Testes: `test_real_export_names_recognised_by_def_pattern` (C3 e os
três nomes novos) e `test_prison_units_table_does_not_displace_cnes_lookup` (unidade e ocupação).
Decisão final (usuário, 2026-10-29): manter as linhas `A` da SESA apesar do C2, com esta nota pós-hoc: o limiar 53 estava errado
pelo denominador (conjunto sem `-LeptoNET.def`); medido no conjunto certo, o mesmo critério daria 52, e a diferença é toda a variante
`-LeptoNET.def`, que também existe no DATASUS. A lista `KNOWN_DBF_PREFIXES` continua no código como reserva.

### 2026-10-29 — Teste nas 35 bases reais da SESA: quatro ajustes decididos pelo usuário (CNAE, coluna truncada, CID-10, nomes do empregador)
Contexto: o zip v0.3.0 (79116e8) rodou numa máquina da SESA em 35 bases do Sinan NET (notificações de 01/01 a 01/03/2026); os 35
logs terminaram em `RESULTADO: OK`. A leitura dos logs (tabela por base no projeto privado, `docs/teste_bases_reais_2026-10-29.md`)
achou: (1) CNAE 100% sem rótulo nas 7 bases de saúde do trabalhador (2.805 registros): `CNAENET.DBF` tem as colunas `CLASS_CNAE`,
`DS_CNAE`, `CO_SEQ`, e `_pick_columns` caía em `CO_SEQ` (um sequencial) porque só aceitava o nome exato `CNAE` ou a primeira
coluna `ID_/CO_/CD_`; (2) `DISTRNET.dbf` falhava na esquistossomose porque o `.def` pede `NM_DISTRITO` (11 letras) e o DBF só
guarda 10 (`NM_DISTRIT`); (3) `AGRAVNET.DBF` do TabWin não é tabela de CID (14.200 linhas, código em `ID_AGRAVO`, nenhuma coluna
de nome), e por isso `CID_ACID`, `DIAG_ESP`, `DIAG_CONF` e `CID_LESAO` saem sem rótulo em 6 bases; (4) 415 de 3.959 campos sem
nome por extenso, dos quais o bloco do empregador (10 campos) se repete em 8 bases. O usuário mandou fazer os quatro, com a CID-10
"tirada do TabWin". Fonte da CID-10: os 22 `.cnv` por capítulo (`CID10_01.CNV` … `CID10_22.cnv`, largura 4, categorias de 3 e
subcategorias de 4 caracteres) do pacote `OBITOS_CID10_TAB.zip` do TabWin do SIM (DATASUS), já em disco no projeto do atlas de
mortalidade; 14.465 linhas declaradas nos cabeçalhos. Gravados como `tabelas/tab_sinannet/agravnet.csv` (colunas `CODIGO,NOME`),
que a cadeia de busca já prefere ao `.dbf` de mesmo nome (`lookup.find_lookup_files`), por `scripts/make_agravnet_csv.py`.
Fora deste bloco (não pedido): apelidos `.def`→export (8 campos), perfil de duplicidade para antirrábico e violência.
Critério de aceite, escrito antes de mexer no código:
- C1. `_pick_columns` escolhe `CLASS_CNAE` para (`cnae`, `ds_cnae`) numa tabela com `CLASS_CNAE, DS_CNAE, CO_SEQ`, e `NM_DISTRIT`
  para `NM_DISTRITO`; a nota do log diz qual coluna foi usada quando o nome não é exato. A regra: nome exato; depois os 10 primeiros
  caracteres iguais (limite do DBF); depois coluna que contém o nome pedido. A heurística antiga (`ID_/CO_/CD_`) fica por último.
- C2. `agravnet.csv` tem 14.465 linhas e devolve, por amostra conferida no texto dos `.cnv`: `A000`, `X450`, `M545`, `D170`, `Z999`
  e as categorias de 3 letras (`X45`). Código de 4 caracteres que não existe na tabela cai na categoria de 3 (`lookup`, só para
  código que começa por letra). Base sintética de acidente grave com `CID_ACID` recebe `CID_ACID_rotulo` com esses nomes.
- C3. Com o `agravnet.csv` presente, a falha do `AGRAVNET.DBF` deixa de ser AVISO e vira nota (a tabela foi substituída, não perdida).
- C4. Os 10 campos do bloco do empregador (`NUCNPJ_CPF`, `NOEMPRESA`, `DIS_EMP`, `COBAIEMP`, `NOBAIEMP`, `END_EMP`, `NU_EMP`,
  `REF_EMP`, `DDD_EMP`, `FONE_EMP`) e mais `COMP_EMP`, `CEP_EMP`, `UF_EMP`/`SG_UF_EMP` quando existirem ganham nome por extenso de uma
  tabela interna própria ("ficha de saúde do trabalhador (tabela interna)"), depois do dicionário CSV e dos `.def`, sem tirar nome de
  campo que já tinha.
- C5. Suíte completa passando (188 antes) e os testes sintéticos de ponta a ponta sem campo rotulado a menos.
Consequência pré-registrada: ajuste que não atender ao seu critério é revertido e o achado volta ao PLANO como pendente; nenhum
limiar é ajustado depois do resultado. A medida que vale (fração de registros com rótulo em CNAE e nos campos CID) só sai na
próxima rodada nas bases reais, na SESA.
Ressalva anotada antes: `CNAENET.DBF` tem 580 códigos de 5 dígitos, o que bate com as 581 classes da CNAE 1.0 (de memória). Se o
export trouxer CNAE 2.0 (7 dígitos de subclasse), a tabela certa não casa e não se deve cortar o código para 5 dígitos, porque as
classes mudaram de significado entre as versões; o log da próxima rodada diz quantos casam.
Resultado (2026-10-29, mesma sessão):
- C1 atendido. Regra em `lookup._match_column`: nome exato; 10 primeiros caracteres iguais; coluna única que contém o nome. A coluna
  de nome é escolhida antes da de código, e excluída da busca do código, porque `cnae` está contido em `CLASS_CNAE` e em `DS_CNAE`
  (a primeira versão da regra devolvia "ambíguo" e caía de novo em `CO_SEQ`; corrigido antes de medir). Nota no log quando o nome
  não é exato (`coluna cnae lida de CLASS_CNAE`; `coluna NM_DISTRITO lida de NM_DISTRIT (nome cortado em 10 caracteres no DBF)`).
- C2 atendido. `agravnet.csv` com 14.465 códigos (2.065 categorias de 3 e 12.400 subcategorias de 4), igual à soma dos cabeçalhos
  dos 22 `.cnv`; nenhuma linha rejeitada, nenhum código repetido. Amostra conferida no texto dos `.cnv`: `A000`, `X45`, `X450`, `M545`,
  `D170`, `Z999` (o nome que eu esperava para `Z999` estava errado; vale o do arquivo). `A002`, que não existe, cai em `A00` ("Cólera").
  O parser do SIM não é o `cnv.parse_cnv` (cabeçalho `N 3693 4 L` e marcas `@`, `&`, `#` e `-` junto ao código, que o Sinan não usa);
  o script tira o código repetido no fim da linha pelo valor, não pela coluna, porque rótulo longo deixa um só espaço antes dele.
  Limite da fonte: o `.cnv` do TabWin corta o nome em cerca de 100 caracteres ("...resultando em doenças infecciosas e parasitá").
- C3 atendido: com `agravnet.csv` presente, `AGRAVNET.DBF` sai como nota ("não pôde ser lida: sem a coluna …; substituída por
  agravnet.csv"), não como AVISO. Sem a CSV o comportamento é o antigo.
- C4 atendido: tabela `names.WORK_FORM` (17 campos: os 10 do bloco mais `COMP_EMP`, `CEP_EMP`, `UF_EMP`/`SG_UF_EMP`, `MUN_EMP`,
  `CNPJ_PRIN`, `NOME_PRIN`), fonte "ficha de saúde do trabalhador (tabela interna)", consultada depois do CSV, da ficha de
  notificação e dos `.def`. Os nomes seguem as fichas impressas de memória, não conferidos linha a linha; corrigir se a equipe apontar.
- C5 atendido: 193 testes passando, 3 pulados, 183 s. Coletados: 192 antes, 196 agora, os 4 novos
  `test_pick_columns_contains_and_truncated_names`, `test_cnae_table_labels_by_class_code`, `test_cid10_csv_answers_for_agravnet` e
  `test_employer_block_gets_names_from_work_form_table` (os pulados são casos parametrizados de duplicidade que só valem para sífilis
  em gestante; a contagem "188 e 4" da entrada anterior era de outra parametrização).
Pendentes do mesmo teste, não pedidos: apelidos `.def`→export (8 campos em AIDSCNET, ANIMPNET, AIDSANET); perfil de duplicidade para
antirrábico (806 pares em 10.595) e violência (278 em 5.285), hoje `agudo`; CNAE 2.0 se o export trouxer 7 dígitos.

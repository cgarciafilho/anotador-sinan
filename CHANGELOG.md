# Registro de mudanças

Formato de [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); numeração [SemVer](https://semver.org/lang/pt-BR/):
`MAIOR.MENOR.CORREÇÃO`. Enquanto a versão for `0.x`, a forma das abas e das colunas ainda pode mudar entre versões menores.
Cada versão tem uma tag `vX.Y.Z` no git e um release no GitHub com o zip para Windows e sua soma sha256.

## [Não lançado]

### Adicionado
- CNAE 2.3 na cadeia de busca dos campos `CNAE` e `CNAE_PRIN` das oito fichas de saúde do trabalhador:
  `tabelas/tab_sinannet/cnaenet_cnae23.csv` (673 classes de 5 dígitos e 1.332 subclasses de 7, colunas `CODIGO,NOME,NIVEL`),
  gerado por `scripts/make_cnae23_csv.py` a partir de cópias públicas da tabela do IBGE (o IBGE não era alcançável da sessão;
  as cópias foram comparadas entre si, ver `docs/METODO.md`, 2026-11-04). A CNAE 1.0 do TabWin (`CNAENET.DBF`, 580 classes)
  continua na cadeia: as duas versões não têm nenhum código de 5 dígitos em comum, então não há desempate nem risco de nome
  da versão errada, e a linha `Cobertura` do log diz quantos registros cada versão rotulou. Subclasse de 7 dígitos que a tabela
  não tem (retirada numa revisão da 2.x, como `4713-0/01`) recebe o nome da sua classe (os 5 primeiros dígitos); isso vale só
  para tabelas de CNAE, não para o CNES. Fecha o item "Em revisão" da 0.4.0 quanto à colisão; a cobertura em base real ainda
  não foi medida.
- Complementos de tabela externa: além de `<tabela>.csv` e `<tabela>.dbf`, a cadeia carrega `<tabela>_*.csv` (e `.csv.gz`),
  entre os dois, em ordem de nome.
- O log lista os códigos sem rótulo de cada campo com tabela externa (CNES, CBO, CNAE…): os 30 mais frequentes, com a contagem
  e a distribuição por tamanho do código; a aba `dicionario` traz a lista completa, com `rotulo` "[sem rótulo]" e `tabela` vazia.

### Corrigido
Revisão de código do pacote inteiro (2026-11-04; critério e resultado em `docs/METODO.md`), seis correções, cada uma com teste:
- Duplicidades: base sem `DT_NOTIFIC` com ao menos um par derrubava a rodada inteira (`KeyError` ao ordenar a aba); agora
  a aba sai sem a coluna de data.
- Duplicidades: grupo com mais de 50 registros de mesmo nome e sexo (ou mesma data de nascimento e sexo) era descartado em
  silêncio nas chaves `nome_nasc1` e `nasc_nome_sim`, e reduzido sem aviso em `nome_mae`; agora todas as chaves pareiam
  registros consecutivos por data de notificação nesses grupos, como `padrao` já fazia, e o log diz quantos grupos por chave.
- Duplicidades: no desempate da ficha a manter (mesma data), a ficha com município de notificação em branco ganhava como
  "notificada pelo município de residência"; a comparação misturava texto vazio com falso.
- Aba `dicionario`: um código rotulado pela primeira tabela complementar da cadeia (UNIDANET) aparecia de novo sob as seguintes
  (UNIDINVEST), com o nome que não foi usado; agora cada tabela lista só os códigos que chegaram até ela.
- Tabela externa em DBF com código numérico em branco: a linha virava o código "<NA>" (inteiro) ou derrubava a tabela inteira
  (decimal, `int(nan)`); a linha é ignorada.
- `--saida` que não pode ser criada: a falha estourava fora do `try`, abortava o lote todo e não deixava log; agora é uma
  falha registrada, com o log gravado ao lado do DBF.
- Gravação do xlsx: as colunas de data passam a ser reconhecidas pelo tipo ou pelo primeiro valor preenchido, em vez de uma
  função Python por célula de toda a tabela. Medido num quadro de 17.201 × 200: a varredura caiu de 0,41 s para 0,01 s e a
  gravação de 26,8 s para 25,8 s (mediana de 3); o resto do tempo é o próprio openpyxl, célula a célula.

## [0.4.0] - 2026-10-30

### Em revisão
- CNAE nas oito fichas de saúde do trabalhador (`CNAE`, `CNAE_PRIN`): a tabela do TabWin é a CNAE 1.0 (580 classes de 5 dígitos).
  Em 35 bases reais de 2026, 45% dos códigos preenchidos ficaram sem nome (1.258 de 2.805), e um código da CNAE 2.0 que coincida com
  um da 1.0 recebe o nome errado sem aviso. Os rótulos de CNAE desta versão são provisórios; estamos levantando os códigos reais
  para decidir a tabela. Os outros campos dessas fichas, inclusive os CID, não são afetados.

### Adicionado
- Dicionários de sífilis congênita (`tabelas/dicionarios/dicionario_sifc.csv`, 85 campos, 37 com categorias) e de sífilis em
  gestante (`dicionario_sifg.csv`, 53 campos, 17 com categorias), extraídos dos dicionários de dados oficiais do Sinan NET 5.0
  (`DIC_DADOS_Sifilis_Congenita_v5.pdf`, `DIC_DADOS_Gestante_Sifilis_v5.pdf`) pela mesma cadeia que gerou os de TB, hanseníase, LTA
  e LV, sem linha escrita à mão. Os sinais clínicos da criança saem com o nome que o export usa (`CLI_ANEMIA`, `HEPATO`,
  `LESOES`…), que o próprio PDF manda manter ("nome da variável no SINAN-W").
- Campo do DBF que o `.def` não descreve, mas que o dicionário CSV do agravo traz com categorias, passa a ser rotulado por elas,
  com nota no log ("campo que o .def não descreve; categorias tomadas de dicionario_sifc.csv"). Na sífilis congênita isso dá rótulo
  a 12 variáveis que o TabWin nunca tabulou: 10 sinais clínicos, `CS_GESTANT` e `CS_ESCOL_N`. O log lista esses campos em linha
  própria, separados dos "copiados sem rótulo". Nos outros agravos com dicionário o mesmo mecanismo rotula campos de sistema e
  de investigação que o TabWin não tabula (`TP_NOT`, `NDUPLIC_N`, `IN_VINCULA`, `CS_FLXRET`, `MIGRADO_W`; na tuberculose, também
  populações especiais, teste molecular, sensibilidade, agravos associados e transferência; na LTA, `CON_CLASS` e `TRA_DROGA`).
  Texto com mais de 100 caracteres na coluna de categorias do CSV é descartado (é frase do PDF, não categoria).
- `tabelas/tab_sinannet/agravnet.csv`: CID-10 completa (14.465 códigos, categorias de 3 e subcategorias de 4 caracteres) tirada dos
  22 `.cnv` por capítulo do TabWin do SIM (`OBITOS_CID10_TAB.zip`, DATASUS), por `scripts/make_agravnet_csv.py`. Dá nome aos campos
  CID das fichas de saúde do trabalhador (`CID_ACID`, `DIAG_ESP`, `DIAG_CONF`, `CID_LESAO`), que saíam sem rótulo porque o
  `AGRAVNET.DBF` do TabWin não tem coluna de nome. Subcategoria ausente cai na categoria (`A002` → "Cólera").
- Nome por extenso para o bloco do empregador das fichas de saúde do trabalhador (`NOEMPRESA`, `NUCNPJ_CPF`, `END_EMP`, `FONE_EMP`…,
  17 campos), que nenhum `.def` nomeia; fonte "ficha de saúde do trabalhador (tabela interna)" na aba `campos`.
- Pacote completo do TabWin em `tabelas/tab_sinannet/`: 486 `.cnv`, 2 `.def` (animais peçonhentos e planilha de surto) e
  `Diagnos.cnv` copiados do `TAB_SINANNET.zip` do DATASUS (arquivos de 04/2024). Cobertura de dicionário, medida por campo de
  categoria nos `.def`: de 1.801 de 2.397 campos (75%) em 58 `.def` para 2.452 de 2.453 (100%) em 60 `.def`; só
  `br_uf_nu_sg_dhx.cnv` (UF de infecção da leptospirose) segue ausente. A pasta de origem era uma extração parcial do zip
  (138 dos 627 `.cnv`); nada se perdeu na publicação. `PfapolioNET.def` na versão de 2024 (cita `DIAGNOSCOPIA.CNV`).
- `scripts/cobertura_campos.py`: por `.def`, quantos campos de categoria têm tabela, com o total e os campos sem tabela.
- `.def` com extensão em maiúsculas (`AnimaispNET.DEF`, `PlanSurtoNet.DEF`) passam a ser lidos.
- Linha `A` (padrão do nome do DBF) dos 58 `.def` trocada pela do TabWin da SESA-CE, que traz os nomes reais do export do
  Sinan NET (`TUBEN*.DBF`, `SifiCN*.DBF`, `NindiN*.DBF`): a base é reconhecida pelo próprio `.def`, e a lista manual de nomes
  vira reserva. Passam a ser reconhecidos pelo padrão `SIFICNET`, `NINDINET`, `EPIZONET` e `TETANNET` (este casava o `.def` de
  tétano acidental). O corpo dos `.def` continua o do DATASUS.
- `Unid_Prisionais.CNV` (22 unidades prisionais do Ceará, código CNES) do TabWin da SESA, citada por `NotIndiviNet.def`.

### Corrigido
- CNAE saía 100% sem rótulo nas bases de saúde do trabalhador (35 bases reais da SESA, 2026-10-29): em `CNAENET.DBF` o código está em
  `CLASS_CNAE`, e a escolha de coluna caía em `CO_SEQ` (sequencial). A coluna de uma tabela externa agora é achada pelo nome exato,
  pelos 10 primeiros caracteres (limite do DBF: o `.def` da esquistossomose pede `NM_DISTRITO`, o `DISTRNET.dbf` guarda `NM_DISTRIT`)
  ou por ser a única que contém o nome pedido; o log anota a coluna usada.
- Tabela externa que falha mas tem substituta (`agravnet.csv` ao lado de `AGRAVNET.DBF`) vira nota no log, não AVISO.
- Campo com busca em tabela externa (CNES, CBO) e tabela de categorias no mesmo `.def`: a tabela de categorias vencia. Na
  notificação individual, a ocupação saía como "Categoria de ocupação classificada na CBO" (`GRUPO1a.CNV`) em vez do nome da CBO,
  e, com a tabela prisional, a unidade perderia o nome do CNES. Agora a busca externa vem primeiro e a tabela de categorias só
  responde para códigos que ela não tem; o log anota.
- `.cnv` cujo cabeçalho traz um token a mais (`10  6   33X001`, tabelas de região de saúde) era rejeitado como "sem cabeçalho".
- `build/build_windows_zip.sh` copiava só `*.def` e `*.cnv` em minúsculas: `Unid_Prisionais.CNV`, `AnimaispNET.DEF`,
  `PlanSurtoNet.DEF` e 32 `*.CNV` ficavam fora do zip (668 de 703 arquivos). Agora copia sem distinguir maiúsculas.
- Nomes reais de export do Sinan NET reconhecidos pelo nome: `SIFICNET` (sífilis congênita), `LEISHNET` (leishmaniose
  visceral) e `MENINNET` (meningite), além dos já conhecidos.
- Tabela `.cnv` que o `.def` cita e o pacote do TabWin não tem: quando o dicionário de dados do agravo em `tabelas/dicionarios/`
  traz as categorias copiadas dela (`categorias_cnv`), o programa reconstrói a tabela e rotula o campo; a aba `dicionario`
  marca "reconstruída de dicionario_hans.csv". Vale hoje para `ESQ_INI_N` e `ESQ_ATU_N` de hanseníase (`ESQUETER.CNV`,
  `ESQUETERatu.CNV`). O log passa a listar numa linha só as tabelas ausentes, para copiar do TabWin.
- Hanseníase, `DOSE_RECEB`: a tabela de rótulos é escolhida registro a registro por `CLASSOPERA` (1 → `nudosePB.cnv`,
  2 → `nudoseMB.cnv`, demais → `nudoses.cnv`), em vez de usar a de paucibacilar para todos.
- Duplicidades no perfil agudo: o tipo sugerido traz o intervalo em faixas (`mesmo dia`, `1 a 7 dias`, `8 a 30 dias`,
  `31 a 90 dias`, `91 a 365 dias`, `mais de 365 dias`) com os dias exatos entre parênteses; o log conta por faixa, não por
  valor (eram 425 linhas no LEISHNET real). Intervalo maior do que o período coberto pela própria base (mais um ano) vira
  `data implausível? … conferir as datas`: erro de digitação numa das datas, não "mesma pessoa".
- Nove tabelas de dengue e chikungunya do `TAB_SINANONLINE.zip` (TabWin da SESA-CE) em `tabelas/tab_sinannet/`:
  `Classdeng`, `Classchik`, `Clinic_chi`, `ConfdescDeng2011`, `evodeng`, `Resultado`, `Resultado3`, `Sorodeng`, `TipoSistema`.
  Classificação final, critério, evolução, sorotipo e resultados de exame de dengue passam a sair rotulados.
- Dengue e chikungunya, `CRITERIO`: o `.def` traz uma tabela até 2010 e outra pós 2010; a tabela segue `NU_ANO` em cada
  registro (até 2010 → `Confdesc.cnv`; depois → `ConfdescDeng2011.cnv`), em vez de usar a antiga para todos.
- `scripts/tabelas_ausentes.py`: lista as `.cnv` e `.dbf` que os `.def` citam e `tabelas/tab_sinannet/` não tem (lista
  única com quantos `.def` citam cada uma, e por `.def` com os campos afetados). Em 28/10/2026: 254 tabelas, 53 de 58 `.def`.
- `AVISO` no log quando `NM_PACIENT` está em branco na metade ou mais dos registros (MENINNET real: 5.902 de 5.902), porque
  sem nome nenhuma chave de duplicidade funciona.

### Corrigido
- Sífilis congênita: o Sinan NET exporta a base como `SIFICNET.DBF`, mas o programa só conhecia `SIFCNET` (o padrão `Sifc*.DB?`
  do `SifilisNET.def` do TabWin). O nome não era reconhecido e a escolha caía no conjunto de campos, que elegia
  `NotnegatNET.def` (5 campos genéricos, todos presentes) em vez de `SifilisNET.def` (47 de 54 presentes): só 3 de 103 campos
  saíam rotulados. Agora `SIFICNET` é nome conhecido, e a escolha por conjunto de campos exige metade dos campos do `.def` e
  então prefere o `.def` com mais campos presentes em número absoluto, não em proporção; o log lista os outros candidatos.
- Gravação do xlsx: caracteres de controle (código 0–31, fora tabulação e quebra de linha) em campos de texto, comuns em
  `DS_OBS` e outros campos longos do Sinan, faziam o openpyxl recusar a célula (`IllegalCharacterError`) e a execução inteira
  falhava no último passo, depois da anotação e das duplicidades prontas. Agora são removidos ao gravar e o log avisa quantas
  células e em quais colunas (`AVISO: N células continham caracteres de controle…`).
- Campos que o DBF e o `.def` escrevem diferente: `BACILOSCO` (DBF) é `BACILOSCOP` no `HansNET.def`, `DT_DESC3` (DBF) é
  `DT_DES3` no `LeishtegNET.def`. Antes saíam "sem rótulo" e "sem nome por extenso"; agora o campo é rotulado e nomeado pelo
  nome do `.def`.
- Tabela externa `UNIDINVEST.dbf` lida também para campos cujo nome não é coluna dela (`ATE_HOSP_1` em meningite,
  `PRE_UNIPRE` em sífilis em gestante): a coluna de código passa a ser a primeira `ID_`/`CO_`/`CD_` da tabela, com nota no
  log. Some o aviso enganoso "não pôde ser lida: sem a coluna …".
- `BAIRRNET.DBF` vem vazia no `TAB_SINANNET.zip`: deixa de ser `AVISO` e vira nota por campo ("vem vazia no pacote do
  TabWin; o nome do bairro já vem em NM_BAIRRO").
- Nome por extenso vindo do dicionário de outro agravo só quando os dicionários concordam sobre o campo (mesma primeira
  palavra); `TRATAMENTO` é "Tipo de Entrada" em TB e uma data em LV, e para um terceiro agravo nenhum dos dois é usado.

## [0.3.0] — 2026-10-28

### Adicionado
- `docs/MANUAL.md`, manual para quem usa o programa: como rodar, como ler cada aba e, regra por regra, como os pares de
  duplicidade são achados, classificados por agravo e qual ficha a regra do MS manda manter; roteiro de revisão e limites
  conhecidos. Vai dentro do zip como `MANUAL.md`. Teste `tests/test_manual.py`: cada tipo sugerido, motivo da ficha, chave,
  coluna, campo de perfil e constante numérica do código tem de aparecer no manual.
- Manual em PDF (A4, sumário com páginas, rodapé numerado), gerado do mesmo `docs/MANUAL.md` por
  `build/build_manual_pdf.py` (markdown + WeasyPrint) no CI e no release; vai no zip como `MANUAL.pdf` e anexado ao release,
  com sha256 em `SHA256SUMS.txt`.

### Corrigido
- Base de outro estado (município fora da tabela de ADS da SESA-CE): com `ID_REGIONA` em branco, as colunas de ADS saíam
  "Ign/Branco" e o log não contava o par como sem ADS. Agora a coluna fica vazia, o par vai para o fim da aba e o log conta.
  Com `ID_REGIONA` preenchido, continua saindo o nome da regional do Sinan. Teste com base sintética de São Paulo.

## [0.2.0] — 2026-10-27

Primeira versão pública. Em relação à 0.1.0 (interna):

### Adicionado
- Abas `duplicidades` e `duplicidades_resumo`: pares de notificações que podem ser da mesma pessoa, achados por quatro
  chaves (`padrao`, a do relatório do Sinan NET: primeiro e último nome + nascimento + sexo; `nome_mae`; `nome_nasc1`;
  `nasc_nome_sim`), com o tipo sugerido na linguagem dos cadernos do Sinan (duplicidade verdadeira, duplo registro por
  transferência, recidiva/reingresso, homônimo, gestação diferente), a regra citada, os dias entre os eventos, a ficha que a
  regra do MS manda manter e a seção "já julgado" para pares com `NDUPLIC_N`/`IN_VINCULA`. Regras por agravo: tuberculose,
  hanseníase, sífilis em gestante (janela de 45 semanas entre diagnósticos), aids, agravos agudos (distância em dias, sem corte).
  Critério de aceite pré-registrado e aprovado em base sintética (`docs/METODO.md`, 2026-10-25).
- ADS e superintendência regional da SESA-CE por município nas abas de duplicidades (`tabelas/regionalizacao_sesa_sr_ads.csv`);
  abas ordenadas por ADS.
- Tabelas externas do TabWin (unidades CNES, CBO, país, regional, distrito) lidas em DBF ou CSV; `unidanet.csv` gerado do CNES
  público (setembro de 2026, 640 mil estabelecimentos) como tabela principal de unidades, com as DBF de 2021 como complemento.
- Nomes por extenso no cabeçalho ("Sexo (CS_SEXO)") a partir da ficha de notificação, dos dicionários de dados do DATASUS
  (`tabelas/dicionarios/`) e dos `.def`; aba `campos` com a fonte de cada nome.
- Log com a cobertura de cada tabela externa (quantos registros cada tabela rotulou, quantos ficaram sem rótulo) e com a contagem
  de registros que nenhuma chave de duplicidade alcança.
- Pacote montado pelo GitHub Actions a cada tag, com sha256 publicado; nome do zip pela versão (`anotador_sinan_vX.Y.Z.zip`).

### Alterado
- Rótulo de município e UF sem o código na frente ("Itapiúna", não "230650 Itapiúna").
- Estágio da gestação (sífilis em gestante) mostrado pelo rótulo de `CS_GESTANT`, não pelo código (o código 4, "idade gestacional
  ignorada", aparecia como "4º trimestre").
- Pastas de tabelas renomeadas de `herdado/` para `tabelas/`.

## [0.1.0] — 2026-10-22

Versão interna, testada em Windows com DBF de amostra: leitura do DBF (detecção cp850/cp1252), escolha do `.def` pelo nome do
arquivo e pelos campos, coluna `<campo>_rotulo` para cada campo com `.cnv`, idade em anos e faixa etária a partir de
`NU_IDADE_N`, datas como data do Excel, nome do município, abas `dados` e `dicionario`, divisão por ano acima do limite de
linhas do Excel, zip com Python embutido para Windows (`build/build_windows_zip.sh`).

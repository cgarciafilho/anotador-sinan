# Registro de mudanças

Formato de [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); numeração [SemVer](https://semver.org/lang/pt-BR/):
`MAIOR.MENOR.CORREÇÃO`. Enquanto a versão for `0.x`, a forma das abas e das colunas ainda pode mudar entre versões menores.
Cada versão tem uma tag `vX.Y.Z` no git e um release no GitHub com o zip para Windows e sua soma sha256.

## [Não lançado]

### Adicionado
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

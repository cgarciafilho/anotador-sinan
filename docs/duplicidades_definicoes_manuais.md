# Duplicidade no Sinan: o que dizem os manuais

Levantamento de 2026-10-25, feito antes de desenhar a aba `duplicidades` do anotador. Reúne, com fonte e página, as
definições gerais do Ministério da Saúde, as específicas por agravo (onde existem) e o que a SESA-CE acrescenta.
Os PDFs não são redistribuídos neste repositório; a tabela de fontes diz de onde cada um vem (zip do FTP do DATASUS, sites das secretarias).
"p. PDF" é a página do arquivo; "p." sem sufixo é o número impresso na página.

## 1. Fontes consultadas

| Sigla | Documento | Onde |
|---|---|---|
| **MNR 2007** | MS/SVS. *Sinan — Normas e Rotinas*, 2ª ed., 2007 (70 p.) + errata | `MS_2007_Sinan_Normas_e_Rotinas_2ed.pdf`, `…_errata.pdf` (do `Docs_TAB_SINAN.zip` do FTP do DATASUS) |
| **IN 02/2005** | MS/SVS. Instrução Normativa nº 2, de 22/11/2005 (regulamenta o Sinan) | `MS_2005_IN_02_Sinan.pdf` |
| **MSN 2007** | MS/DATASUS. *Manual do Sistema Sinan NET*, 2007 (189 p.) | `Docs_TAB_SINAN.zip` → `Documentação/MANUAL/Manual SinanNet.pdf` (10 MB, não copiado) |
| **CG 2008** | MS/SVS. *Roteiro para uso do Sinan NET — Caderno geral* (versão preliminar, set/2008, 87 p.) | `MS_2008_Sinan_NET_caderno_geral.pdf` (baixado do espelho da SES-GO em 2026-10-25) |
| **TB 2019** | MS. *Caderno de análise — Tuberculose* (Sinan NET 5.0, abr/2019, 53 p.) | `MS_2019_TB_caderno_de_analise.pdf` |
| **HANS 2026** | MS/SVSA. *Roteiro para uso do Sinan Net Hanseníase e Manual para tabulação dos indicadores* (jan/2026, 155 p.) | `Caderno-de-Anlise_20.03.2026.pdf` (8 MB, não copiado); versão de 2019 no zip (`HANSN_CADERNO_ANALISES.pdf`) |
| **ANIMP 2008** | MS. *Caderno de análise — Acidentes por animais peçonhentos* (set/2008) | `MS_2008_animais_peconhentos_caderno_de_analise.pdf` |
| **MENIN 2019** | MS. *Caderno de análise — Meningite* (abr/2019) | `MS_2019_meningite_caderno_de_analise.pdf` |
| **VIOL 2019** | MS. *Caderno de análise — Violência interpessoal/autoprovocada* (versão preliminar, mar/2019) | zip → `AGRAVOS/VIOLEN_CADERNO_ANALISE.pdf` (4,7 MB, não copiado) |
| **NINDIN 2018** | MS/DATASUS. *Dicionário de dados — Notificação individual* (nov/2018) | `MS_2018_NINDIN_dicionario_de_dados.pdf` |
| **SOL 2011** | MS/DATASUS. *Sinan Online — Manual de operação*, ed. 1.0, jun/2011 (dengue/chikungunya) | [espelho SES-GO](https://goias.gov.br/saude/wp-content/uploads/sites/34/2013/08/manual_de_operacao_sistema_sinan_online-d86.pdf) (8 MB, não copiado) |
| **SESDF 2020** | SES-DF. Nota Técnica nº 10/2020, sífilis em gestante e congênita | `SESDF_2020_NT_10_sifilis_gestante_congenita.pdf` |
| **SESA 2017** | SESA-CE/NUIAS. Nota Técnica *Sistema de Informação de Agravos de Notificação*, 26/12/2017 | [site da SESA](https://www.ce.gov.br/saude/wp-content/uploads/sites/64/2018/06/nota_tecnica_agravos_notificacao_dez2017_ok.pdf#page=4) |
| **SESA ST 2023** | SESA-CE. *Manual para uso do Sinan Net: análise da qualidade da base de dados… doenças relacionadas ao trabalho*, fev/2023 (146 p.) | [site da SESA](https://www.ce.gov.br/saude/wp-content/uploads/sites/64/2022/08/manual_sinan_atualizado_fev2023.pdf#page=71) (edição de 2017: `manual_sinan_-15_02_17.pdf`, p. 55–56) |
| **SESA SIF 2025** | SESA-CE. Nota Técnica Conjunta nº 01/2025 — Sífilis, 10/10/2025 | [site da SESA](https://www.ce.gov.br/saude/wp-content/uploads/sites/64/2018/06/Nota_Tecnica_SIFILIS_2025.pptx.pdf#page=12) |

O que foi varrido e **não** trata de duplicidade: cadernos de LTA e LV (2019), instrucionais e notas informativas de sífilis
(SIFIGEN/SIFICN, 2017), instrucional de hepatites, dicionários dos demais agravos (só o campo `NDUPLIC_N`, igual ao NINDIN),
Portarias de Consolidação 1 a 6/2017 (as menções são de outros temas). O artigo de Silva Júnior et al. (*Epidemiol. Serv. Saúde* 2016;25(3):487-98, registros repetidos no
Sinan 2008–2009 com Reclink) não pôde ser baixado daqui (HTTP 403); fica como leitura secundária, não é manual.

## 2. Definições gerais (MS)

### 2.1 O que é duplicidade (MNR 2007, item 3.1.5.4, p. 23–24; CG 2008, p. PDF 22)

- **Agravos agudos:** "quando o mesmo paciente foi notificado mais de uma vez pela mesma ou outra unidade de saúde, para o
  mesmo agravo, **durante o período prodrômico de um mesmo evento** (ex.: paciente com sarampo, notificado duas vezes, por
  unidades de saúde diferentes e com data de primeiros sintomas na mesma semana epidemiológica)". O CG 2008 repete com o
  exemplo da dengue: "data de primeiros sintomas no mesmo período prodrômico". Nenhum documento dá o período em dias.
- **Hanseníase e tuberculose:** "quando o mesmo paciente foi notificado, **durante o mesmo tratamento**, mais de uma vez
  **pela mesma unidade de saúde** (ex.: notificado pelo médico e após alguns dias notificado novamente pela auxiliar de
  enfermagem)".
- **Aids e gestante HIV+:** "quando o mesmo paciente foi notificado mais de uma vez, pela mesma ou outra unidade de saúde,
  **independente do período** de notificação".
- **Qual ficha fica:** "deverá ser mantido no sistema aquele que tiver sido notificado em primeiro lugar. Caso a data da
  notificação seja a mesma, deverá permanecer no sistema a notificação realizada pelo município de residência." A exclusão
  é feita no 1º nível informatizado, depois de imprimir e comparar as fichas; o que a ficha mantida não tem é complementado
  a partir da excluída (p. 24). A IN 02/2005, art. 20, dá a mesma regra com força normativa.

### 2.2 Duplo registro (hanseníase e TB) e homônimos (MNR 2007, itens 3.1.5.5–3.1.5.6, p. 24–26)

- **Duplo registro:** "o mesmo paciente foi notificado mais de uma vez **por unidades de saúde diferentes durante o mesmo
  tratamento** (transferência oficial ou espontânea) **ou** pela mesma unidade ou unidades diferentes **em tratamentos
  diferentes** (recidiva, reingresso após abandono ou outros reingressos)."
  - Transferência → **vincular** no 1º nível informatizado: fica uma notificação (a mais antiga) e um acompanhamento (o
    mais recente); a 1ª unidade registra saída por transferência e a 2ª muda o tipo de entrada para "transferência".
    Transferência temporária para hospital segue a mesma rotina (vinculações sucessivas).
  - Demais duplos registros (recidiva, reingresso) → **"não listar"**, até surgir nova notificação.
  - "Não confundir o duplo registro com a duplicidade de registros."
- **Homônimos:** "registros que apresentam o **primeiro e último nome iguais, mesma data de nascimento e mesmo sexo** e, no
  entanto, são pessoas diferentes (ex.: mães com nomes diferentes, endereços diferentes ou gêmeos com o primeiro e o último
  nome iguais)" → "não listar".
- **Rotina (item 5.5, p. 49):** o nível municipal emite e envia **semanalmente** o relatório de duplicidade à área técnica;
  regionais e SES emitem e analisam antes de transferir ao nível superior. A errata de 2007 não altera nada disso.

### 2.3 Como o Sinan NET aponta os possíveis duplicados (MSN 2007, p. 85–87; CG 2008, p. PDF 21; TB 2019, p. 7; HANS 2026, p. 27–28)

- **Critério padrão** (campos idênticos): **nome/sobrenome do paciente** (primeiro e último nome), **data de nascimento**,
  **sexo**.
- **Filtros adicionais** ("alterar sensibilidade"): nome completo, idade, nome da mãe, **pesquisa fonética** com
  sensibilidade de 1 (mais sensível) a 15 (mais específica). Recomenda-se variar os filtros com frequência (TB 2019, p. 7).
- **Período mínimo da consulta:** agudos 1 ano; hanseníase/TB 5 anos; Aids a base inteira (MSN 2007, p. 86; CG 2008).
- **Ações:** *Excluir*; *Não listar* (fica na base, some do relatório; volta se entrar novo registro com as mesmas variáveis);
  *Não contar* (só SES: sai das estatísticas e **não é exportado para DBF**, HANS 2026, p. 33); *Vincular* (só hanseníase/TB,
  só transferência; a ordem origem → destino importa, TB 2019, p. 9).
- **Rastro no DBF** (NINDIN 2018, campos internos): `NDUPLIC_N` = 0/branco não identificado, 1 "não é duplicidade (não
  listar)", 2 "duplicidade (não contar)" (volta a 0 quando o registro reaparece na rotina); `IN_VINCULA` = 1 se vinculado;
  `FONETICA_N` = primeiro e último nomes concatenados (a chave fonética do sistema); `SOUNDEX` = nome codificado por Soundex.
  Como os "não contar" não saem na exportação, espera-se encontrar no DBF só 0/branco e 1 — a conferir na base real.
- **Sinan Online** (dengue/chikungunya; SOL 2011, p. 2, 8, 42, 51): mesmos campos padrão, filtro com pelo menos duas variáveis
  entre nome/sobrenome, nome completo, nascimento, idade, sexo e nome da mãe (sem pesquisa fonética); "duplicidade verdadeira:
  o mesmo paciente foi notificado mais de uma vez pela mesma ou outra unidade de saúde, para o mesmo agravo"; "não listar"
  para homônimos; quando a notificação é de fora do município de residência, o notificante só pode excluir ou "não listar"
  até a metade do prazo de encerramento, depois só o município de residência.

## 3. Definições por agravo

Convenção dos cadernos: "Pessoas" (mesma pessoa ou não), "Unidade de saúde", "Tipo/modo de entrada", "Tratamentos".

| Agravo / grupo | Duplicidade verdadeira | Duplo registro | Homônimo | Fonte |
|---|---|---|---|---|
| **Agudos em geral** (dengue como exemplo; vale para hepatites no exercício do caderno) | mesma pessoa, mesma ou outra unidade, mesmo agravo, **primeiros sintomas no mesmo período prodrômico** → complementar a 1ª, excluir a 2ª | não definido | mesmo 1º e último nome, nascimento e sexo, pessoas diferentes → não listar | CG 2008, p. PDF 22–24 |
| **Meningite** | idem agudos ("data de primeiros sintomas no mesmo período prodrômico") | não há | idem | MENIN 2019, p. 16 |
| **Animais peçonhentos** | mesma pessoa, **mesma data do acidente**, mesma ou outra unidade → complementar a 1ª, excluir a 2ª. Exceções: paciente encaminhado para soroterapia → fica a ficha do serviço que aplicou o soro (exclui-se a 1ª); antiveneno em mais de um serviço → **manter as duas** (controle de ampolas) | **mais de um acidente** no período → não listar | idem | ANIMP 2008, p. 15–16 |
| **Violência interpessoal/autoprovocada** | mesma pessoa, **mesma data de ocorrência**; conferir a **hora** e as circunstâncias, porque a mesma pessoa pode sofrer mais de uma violência no mesmo dia | mais de uma situação de violência no período (mesma ou outra tipologia) → não listar | idem | VIOL 2019, p. 24–25 |
| **Agravos de saúde do trabalhador** | definição geral dos agudos (período prodrômico do mesmo evento); período mínimo de 1 ano | "mais de uma situação num período específico" (novo acidente) → não listar | idem | SESA ST 2023, p. 69–70 (PDF 71–72) (= MS) |
| **Tuberculose** | mesma pessoa, **mesma unidade**, **mesmo tipo de entrada**, **mesmo tratamento** → complementar a 1ª, excluir a 2ª | **transferência:** unidade ≠, tratamento =, entrada = ou ≠ → vincular. **Recidiva/reingresso:** tratamentos ≠, entrada ≠ "caso novo" → não listar | pessoas ≠ → não listar | TB 2019, p. 7–11 (fluxograma p. 11) |
| **Tuberculose: intercorrência em urgência/referência** | sit. 1 (tratamento segue na origem): urgência notifica com entrada e encerramento "transferência"; vigilância faz **não listar** e espera o encerramento da 1ª. Sit. 2 (óbito na urgência) e sit. 3 (tratamento passa para o novo serviço): origem encerra como transferência; vigilância **vincula** | | | TB 2019, p. 17–18 |
| **Hanseníase** | mesma pessoa, mesma unidade, mesmo modo de entrada, mesmo tratamento → complementar e excluir a 2ª | transferência (unidade ≠, município = ou ≠) → vincular a ficha "caso novo" + saída "transferência" à ficha com entrada "transferência"; recidiva/outros reingressos → não listar. Período mínimo da consulta: 5 anos | pessoas ≠; conferir nome da mãe e endereço → não listar | HANS 2026, p. 27–31 |
| **Aids, gestante HIV+** | mesma pessoa, qualquer unidade, **qualquer período** | | | MNR 2007, p. 24 |
| **Sífilis em gestante** (regra do DF, não há regra do MS) | variáveis: nome, nome da mãe, nascimento, data do diagnóstico, trimestre, primeiros sintomas. Intervalo entre diagnósticos **> 12 meses = gestações diferentes** (não é duplicidade); **< 12 meses:** comparar os trimestres; complementar a 1ª e excluir a 2ª. Maternidade não deve notificar de novo gestante já notificada no pré-natal | | | SESDF 2020, p. 6 |
| **Sífilis (CE)** | "analisar criteriosamente as fichas e, comprovada a duplicidade, excluir"; **fica a ficha com maior completude e data de diagnóstico mais antiga**; entre municípios, **fica a do município de residência**; a ficha mantida é atualizada com as demais. SMS analisa; COADS entre municípios; SESA/SRS entre regiões; DATHI entre estados | | | SESA SIF 2025, p. 11–13 |
| **LTA, LV, hepatites, dengue/chik** | nenhum documento específico encontrado; vale a regra geral dos agudos | | | — |

Divergências a registrar:

- **Recidiva em hanseníase:** a Figura 4 do HANS 2026 (p. 30) traz "Tratamentos: =" para recidiva/reingresso, enquanto o
  TB 2019 (p. 9) e o CG 2008 trazem "Tratamentos ≠". O texto do próprio HANS 2026 diz "em tratamentos diferentes"; a figura
  parece erro de impressão.
- **Qual ficha fica:** o MS (2007) manda ficar a **primeira notificada** (empate → município de residência); a SESA (sífilis,
  2025) manda ficar a de **maior completude e diagnóstico mais antigo** (entre municípios → residência). Para o anotador isso
  não decide nada (a ferramenta não exclui), mas muda qual ficha aparece como "sugerida para manter".

## 4. O que a SESA-CE acrescenta

- **SESA 2017 (p. 4):** os procedimentos de duplicidade "devem observar as orientações dos manuais: Manual Operacional e
  Manual de Normas e Rotinas do Sinan Net em parceria com a área técnica da SESA". Ou seja, a norma estadual remete à federal.
- **SESA ST 2017/2023:** reproduz o MS (critério padrão, filtros, período mínimo de 1 ano, excluir/não listar/não contar),
  com a figura da tela do Sinan NET do Ceará (p. 71–72, PDF 73–74).
- **SESA SIF 2025:** as regras de sífilis da tabela acima, com a divisão de tarefas SMS → COADS → SESA/SRS → DATHI.

## 5. Consequências para o anotador (hipótese de trabalho, a decidir com o usuário)

Não são decisões; são o que o levantamento sugere. O critério de aceite entra no METODO antes de medir.

1. **A alternativa simples a vencer é o relatório de duplicidade do próprio Sinan NET.** Primeira chave do anotador =
   chave padrão do sistema (primeiro + último nome, nascimento, sexo), que o DBF já traz pronta em `FONETICA_N` + `DT_NASC`
   + `CS_SEXO`. Só vale acrescentar chaves (nome da mãe, `SOUNDEX`, nascimento com um componente trocado, as dos scripts de ligação
   do projeto de análise anterior) se elas acharem pares que a chave padrão não acha e que a equipe confirme.
2. **Classificar o par, não só listá-lo**, com os campos que os cadernos usam: mesma unidade? mesmo tipo/modo de entrada?
   mesmo tratamento (datas de início/encerramento se sobrepõem)? datas de primeiros sintomas / do acidente / do diagnóstico
   próximas? Daí sai a etiqueta sugerida — "duplicidade verdadeira?", "duplo registro por transferência?",
   "recidiva/reingresso?", "homônimo?", "gestação diferente?" — sempre com a regra citada e sem decisão automática.
3. **Janela temporal dos agudos não está nos manuais** ("período prodrômico" sem número; o único exemplo é "mesma semana
   epidemiológica"). Precisa de decisão por agravo: o usuário/área técnica define os dias, ou a ferramenta mostra a
   distância em dias e deixa o corte para quem revisa.
4. **Sífilis em gestante:** janela de 12 meses (DF) ou 280 dias (usada no projeto de análise anterior); registrar qual e por quê.
5. **Aproveitar `NDUPLIC_N`:** par em que um dos registros já está "não listar" (= 1) é par que a equipe já julgou; mostrar
   em separado, não como achado novo. Conferir na base real se aparece algum 2.
6. **Ordem de preferência da ficha a manter** (só sugestão na saída): MS = primeira notificação; CE/sífilis = mais completa e
   diagnóstico mais antigo. Mostrar as duas datas e a completude de cada ficha e deixar a escolha para a equipe.

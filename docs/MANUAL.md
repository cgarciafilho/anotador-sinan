# Manual do anotador SINAN

Este manual é para quem usa o programa: equipes de vigilância epidemiológica, áreas técnicas de agravo, regionais de saúde.
Explica o que o programa faz com o DBF do Sinan NET, como ler o xlsx que ele gera e, com mais detalhe, **como os pares de
duplicidade suspeita são achados e classificados**, porque essa é a parte em que uma pessoa precisa confiar no critério para
tomar a decisão no Sinan.

Vale para a versão indicada na primeira linha do `.log.txt` que o programa grava. O PDF deste manual vem dentro do zip e
anexado a cada release; o texto-fonte é `docs/MANUAL.md` no repositório. O texto descreve o que o código faz nesta
versão; as razões de cada escolha, com data, estão em [`METODO.md`](METODO.md), e as definições dos manuais do Ministério da
Saúde, com fonte e página, em [`duplicidades_definicoes_manuais.md`](duplicidades_definicoes_manuais.md).

Sumário:

1. [O que o programa faz e o que não faz](#1-o-que-o-programa-faz-e-o-que-não-faz)
2. [Rodar no Windows](#2-rodar-no-windows)
3. [O xlsx gerado](#3-o-xlsx-gerado)
4. [Duplicidades suspeitas](#4-duplicidades-suspeitas)
5. [O arquivo de log](#5-o-arquivo-de-log)
6. [Perguntas frequentes](#6-perguntas-frequentes)
7. [De onde vêm as regras](#7-de-onde-vêm-as-regras)

## 1. O que o programa faz e o que não faz

O Sinan NET exporta a base de cada agravo como um arquivo DBF (`C:\SinanNet\BaseDBF\TUBENET.DBF`, `HANSNET.DBF`,
`SIFGENET.DBF`, `DENGNET.DBF`…). Nesse arquivo quase tudo é código: sexo `M`/`F`, raça `1`–`5`, tipo de entrada `1`–`6`,
município pelo código do IBGE. O programa lê o DBF e grava, ao lado dele, um xlsx em que **cada campo codificado vem seguido
do seu significado**, segundo as tabelas oficiais do TabWin (os arquivos `.def` e `.cnv` que o DATASUS distribui), pronto
para filtro e planilha dinâmica.

No mesmo xlsx ele grava duas abas de **duplicidades suspeitas**: pares de notificações que podem ser da mesma pessoa, com o
tipo que os cadernos do Sinan dariam a esse par (duplicidade verdadeira, duplo registro por transferência, recidiva ou
reingresso, homônimo, gestação diferente…), a regra do manual que sustenta a sugestão e a ficha que a regra do Ministério
manda manter.

O que ele **não** faz:

- **Não decide.** O tipo e a ficha a manter são sugestões para revisão humana. Excluir, vincular ou marcar "não listar"
  continua sendo feito no Sinan, por quem tem autorização, depois de comparar as fichas.
- **Não altera o DBF** nem apaga, mescla ou corrige registros. Não envia nada pela rede. Não grava fora da pasta do DBF.
- **Não desidentifica.** O xlsx copia todos os campos, inclusive nome, nome da mãe, data de nascimento e endereço, e as abas
  de duplicidades trazem o nome do paciente. O xlsx é tão nominal quanto o DBF e deve ficar no mesmo lugar protegido; não
  deve ir por e-mail nem para pasta compartilhada sem controle de acesso.
- Não rotula campos cujo `.cnv` não vem no pacote do TabWin (vários campos da dengue, por exemplo); o log diz quais.
- Ainda não preenche modelos de planilha dinâmica por agravo.

Foi desenvolvido para as áreas técnicas da Secretaria da Saúde do Ceará (SESA-CE). As tabelas do TabWin cobrem os agravos
do Sinan NET e nada no programa depende do Ceará, exceto a coluna de ADS (área descentralizada de saúde) nas abas de
duplicidades, que vem de uma tabela de regionalização da SESA e fica vazia para municípios de outros estados.

## 2. Rodar no Windows

Não precisa instalar nada nem ter perfil de administrador: o zip traz um Python embutido.

1. Na página de [releases](https://github.com/cgarciafilho/anotador-sinan/releases), baixe `anotador_sinan_vX.Y.Z.zip`
   da versão mais recente (cerca de 100 MB). A soma sha256 está em `SHA256SUMS.txt`, para quem quiser conferir.
2. Descompacte em qualquer pasta, por exemplo `Documentos\anotador`. Não rode de dentro do zip.
3. Arraste um ou mais arquivos `.DBF` do Sinan NET sobre `anotar.bat`. Uma janela preta se abre e mostra o andamento.
4. Quando a janela terminar, `<nome>_anotado.xlsx` e `<nome>_anotado.log.txt` estão ao lado de cada DBF.

Se o Windows avisar "aplicativo não reconhecido", escolha "Mais informações" e depois "Executar assim mesmo". O aviso aparece
porque o `.bat` não é assinado; o pacote é só o Python oficial (python.org) com as bibliotecas pandas, numpy, openpyxl e
dbfread.

Tempo: uma base estadual de tuberculose com 17 mil registros e 130 campos levou cerca de 40 segundos na máquina de teste,
quase tudo na gravação do xlsx. O tempo cresce com registros × colunas; para um milhão de registros a estimativa é de
cerca de 17 minutos só de gravação, e a saída pode ser dividida em um xlsx por ano (seção 3).

Dentro do zip:

| Arquivo ou pasta | O que é |
|---|---|
| `anotar.bat` | O programa. Arraste os DBF sobre ele. |
| `LEIA-ME.txt` | Resumo deste manual, em texto puro. |
| `MANUAL.pdf` | Este manual, para ler na tela ou imprimir. |
| `MANUAL.md` | O mesmo manual em texto puro (é o arquivo-fonte do PDF). Abre em qualquer editor; no GitHub aparece formatado. |
| `app\sinan_anotador\` | Código-fonte (Python). |
| `app\tab_sinannet\` | Tabelas `.def`/`.cnv` do TabWin (DATASUS) e `unidanet.csv` (nomes das unidades, do CNES). |
| `app\regionalizacao_sesa_sr_ads.csv` | Município → ADS e superintendência regional (SESA-CE). |
| `app\dicionarios\` | Nomes por extenso dos campos, dos dicionários de dados do DATASUS (TB, hanseníase, LTA, LV). |
| `python\` | Python 3.13 embutido e bibliotecas. |
| `LICENSE.txt` | Licença MIT. |

Quem prefere linha de comando, ou roda em Linux, encontra as instruções no [README](../README.md); as opções são `--saida`
(pasta de saída), `--codificacao` (forçar cp850 ou cp1252), `--sem-duplicidades` (pular as abas de duplicidades),
`--sem-nome-extenso` (cabeçalho só com o nome curto do campo) e `--max-linhas`.

## 3. O xlsx gerado

| Aba | Conteúdo |
|---|---|
| `dados` | Todos os registros e todos os campos do DBF, na ordem original. Cada campo que tem tabela de códigos ganha, logo à direita, a coluna `<campo>_rotulo` com o significado. |
| `duplicidades` | Um par suspeito por linha, com todas as colunas de apoio (seção 4.8). |
| `duplicidades_resumo` | O mesmo par em poucas colunas, para circular entre as equipes, com colunas em branco para a decisão. |
| `campos` | Uma linha por coluna da aba `dados`: nome por extenso, campo do DBF, tipo, de onde veio o nome, tabela de rótulos usada. |
| `dicionario` | Todas as tabelas de códigos usadas (campo, tabela, código, rótulo). |

### 3.1 Como ler a aba `dados`

- **Cabeçalho** no formato "Nome por extenso (CAMPO)", por exemplo "Sexo (CS_SEXO)" e "Sexo — rótulo (CS_SEXO_rotulo)".
  Os nomes dos campos comuns a todas as fichas (1 a 30) vêm da própria ficha de notificação; os dos campos específicos do
  agravo vêm dos dicionários de dados do DATASUS quando o CSV existe em `app\dicionarios\` e, se não, do `.def` do TabWin,
  que abrevia ("Situação Encerra."). A aba `campos` diz de onde veio cada nome.
- **Código que não está na tabela** aparece como "[código] sem rótulo". **Campo vazio** aparece como "Ign/Branco" ou com
  o rótulo de branco da própria tabela, quando ela tem um.
- `NU_IDADE_N` (idade codificada do Sinan) ganha `NU_IDADE_N_anos` (idade em anos) e `NU_IDADE_N_rotulo` (faixa etária).
- Município de notificação e de residência recebem o nome, sem o código na frente. Unidade de saúde recebe o nome atual do
  CNES e, para unidades desativadas, o nome da tabela do TabWin de 2021.
- Datas saem como data do Excel, não como texto.
- Acima de 1.048.575 registros (limite de linhas do Excel) a saída é dividida em um xlsx por ano de notificação, com aviso
  no log. As abas de duplicidades vão inteiras em cada arquivo, porque um par pode juntar anos diferentes.

## 4. Duplicidades suspeitas

### 4.1 O que o Sinan já faz e o que o programa acrescenta

O próprio Sinan NET tem um relatório de duplicidade. Ele lista registros com **primeiro e último nome, data de nascimento e
sexo iguais**, e permite apertar ou afrouxar a busca com nome completo, idade, nome da mãe e pesquisa fonética. A equipe
examina a lista e, para cada par, escolhe no sistema uma das ações: excluir, vincular, não listar, não contar.

O programa parte da mesma chave do Sinan e acrescenta três coisas:

1. **Mais três chaves**, para achar pares que a chave do Sinan perde por erro de digitação no nome ou na data de nascimento
   (seção 4.2).
2. **Um tipo sugerido para cada par**, na linguagem dos cadernos de análise do Sinan, calculado a partir dos campos que os
   próprios cadernos mandam olhar: mesma unidade, tipo de entrada, datas de tratamento, intervalo entre diagnósticos (seção 4.4).
3. **A ficha que a regra do Ministério manda manter**, e a informação de se o par já foi julgado no Sinan (seções 4.5 e 4.6).

Nada disso substitui a comparação das fichas. O tipo sugerido vem com "?" quando depende de confirmação humana, e sempre vem
com a regra citada ao lado.

### 4.2 Vocabulário dos cadernos

Os termos abaixo são os dos manuais do Sinan (Normas e Rotinas 2007; cadernos de análise de tuberculose, hanseníase e outros
agravos). O programa usa exatamente esses termos na coluna `tipo_sugerido`.

| Termo | Significado nos manuais | Ação prevista no Sinan |
|---|---|---|
| **Duplicidade verdadeira** | A mesma pessoa foi notificada mais de uma vez para o mesmo agravo e o mesmo evento. Nos agravos agudos, "durante o período prodrômico de um mesmo evento"; em tuberculose e hanseníase, "durante o mesmo tratamento, pela mesma unidade de saúde"; em aids e gestante HIV+, em qualquer período. | Complementar a ficha mantida com o que a outra tem e **excluir** a outra. |
| **Duplo registro** (tuberculose e hanseníase) | A mesma pessoa notificada mais de uma vez **por unidades diferentes durante o mesmo tratamento** (transferência oficial ou espontânea), **ou** em **tratamentos diferentes** (recidiva, reingresso após abandono, outros reingressos). Os manuais insistem: "não confundir o duplo registro com a duplicidade de registros". | Transferência: **vincular** (fica uma notificação, a mais antiga, e um acompanhamento, o mais recente). Recidiva e reingresso: **não listar**. |
| **Homônimo** | Registros com primeiro e último nome, data de nascimento e sexo iguais que são **pessoas diferentes** (mães diferentes, endereços diferentes, gêmeos). | **Não listar**. |
| **Não listar** | O registro fica na base e some do relatório de duplicidade; volta se entrar novo registro com as mesmas variáveis. | — |
| **Não contar** | Só a SES faz: o registro sai das estatísticas e **não é exportado para o DBF**. Por isso o programa quase nunca o vê. | — |
| **Vincular** | Só tuberculose e hanseníase, só transferência: a ficha de origem recebe saída por transferência e a ficha de destino vira acompanhamento. A ordem origem → destino importa. | — |

### 4.3 Como os pares são achados: as quatro chaves

Antes de comparar, o programa normaliza os nomes: tira acentos, põe em maiúsculas e troca qualquer coisa que não seja letra
(hífen, apóstrofo, número, ponto) por espaço. "D'Ávila" e "DAVILA" continuam diferentes; "José" e "JOSE" ficam iguais.

| Chave | Junta dois registros quando | Para que serve | O que não alcança |
|---|---|---|---|
| `padrao` | **primeiro nome, último nome, data de nascimento e sexo** são iguais | É a chave do relatório de duplicidade do Sinan NET. Tudo o que o Sinan listaria, o programa lista também, inclusive os homônimos. | Qualquer erro no primeiro ou no último nome ou na data de nascimento. Registro sem data de nascimento ou com nome de uma palavra só. |
| `nome_mae` | **nome completo e nome da mãe** são iguais, os dois preenchidos; a data de nascimento pode ser qualquer | Acha o par em que a data de nascimento foi digitada errada, mesmo com mais de um componente errado. | Erro em qualquer letra do nome do paciente ou da mãe. Registro sem nome da mãe. |
| `nome_nasc1` | **nome completo e sexo** iguais e a data de nascimento diferente **em um só componente** (dia, mês ou ano) ou com **dia e mês trocados** | Acha o erro de digitação típico na data de nascimento. | Erro no nome. Dois componentes errados na data. |
| `nasc_nome_sim` | **data de nascimento e sexo** iguais, nomes diferentes mas **parecidos** (similaridade de 0,85 ou mais, com o mesmo primeiro ou o mesmo último nome) | Acha o erro de uma ou duas letras no nome ("MARIA JOSE DA SILVA" e "MARIA JOSE DA SILVIA"). | Nome muito curto, em que uma letra pesa mais do que 15%. Partícula faltando ("DA") pode ou não passar do limiar. |

Cada par sai **uma vez só**, com todas as chaves que o acharam na coluna `chaves` (por exemplo `padrao+nome_mae`). Um par
que só uma chave adicional achou, e não a `padrao`, é exatamente o que o relatório do Sinan não mostraria.

O que fica fora de qualquer chave, contado no log:

- registro **sem nome**;
- registro **sem data de nascimento e sem nome da mãe** (sem nascimento, só a chave `nome_mae` funciona);
- registro com **nome de uma palavra** fica fora da chave `padrao` (que precisa de primeiro e último nome), mas entra nas outras;
- registro **sem sexo** entra nas chaves que usam sexo (`padrao`, `nome_nasc1`, `nasc_nome_sim`) com o sexo em branco, e
  nelas só pareia com outro registro também sem sexo; `nome_mae` não usa sexo.

Limite de bloco: quando mais de **50 registros** partilham a mesma chave `padrao` ou `nome_mae` (nomes muito comuns, ou um
nome de teste repetido), só registros consecutivos por data de notificação são pareados, e o log avisa. Para `nome_nasc1` e
`nasc_nome_sim` um bloco desse tamanho é pulado.

### 4.4 Qual regra se aplica: o perfil do arquivo

O tipo sugerido depende do agravo, porque os cadernos têm definições diferentes. O programa reconhece o agravo pelo `.def`
que escolheu para o DBF (o log diz qual) ou, se o nome não bastar, pelos campos presentes.

| Perfil | Reconhecido quando | Campos usados na classificação | Data do evento (para `dias_entre_eventos`) |
|---|---|---|---|
| **Tuberculose** (`tb`) | `.def` de tuberculose, ou campos `TRATAMENTO`, `SITUA_ENCE` e `DT_INIC_TR` presentes | `TRATAMENTO` (tipo de entrada), `SITUA_ENCE` (situação de encerramento), `DT_INIC_TR`, `DT_ENCERRA`, `ID_UNIDADE` | `DT_DIAG` (ou `DT_NOTIFIC` se faltar) |
| **Hanseníase** (`hans`) | `.def` de hanseníase, ou campos `MODOENTR` e `DTINICTRAT` presentes | `MODOENTR` (modo de entrada), `TPALTA_N` (tipo de saída), `DTINICTRAT`, `DTALTA_N`, `ID_UNIDADE` | `DT_DIAG` (ou `DT_NOTIFIC`) |
| **Sífilis em gestante** (`sifilis_gestante`) | `.def` `GestSifNET` | `DT_DIAG`, `CS_GESTANT` (idade gestacional) | `DT_DIAG` (ou `DT_NOTIFIC`) |
| **Aids e gestante HIV+** (`aids`) | `.def` `AidsNET`, `AidsCriNET` ou `HivGestNET` | nenhum além dos de identificação | `DT_DIAG` (ou `DT_NOTIFIC`) |
| **Agravos agudos** (`agudo`) | todos os demais: dengue, chikungunya, hepatites, meningite, leptospirose, animais peçonhentos, violência, acidentes de trabalho, sífilis adquirida, sífilis congênita, LTA, LV… | nenhum além dos de identificação | o primeiro que existir entre `DT_SIN_PRI` (primeiros sintomas), `DT_ACID` (acidente), `DT_OCOR` (ocorrência), `DT_DIAG`, `DT_NOTIFIC` |

O log diz qual perfil foi aplicado ("perfil tb", "perfil agudo"…). Se um DBF de tuberculose cair no perfil `agudo`, o `.def`
não foi reconhecido; abra uma issue com o `.log.txt`.

### 4.5 O tipo sugerido, regra por regra

Em cada par, **A é a notificação mais antiga** (pela data de notificação) e **B a mais recente**. Com a mesma data, A é a que
vem primeiro no arquivo.

**Regra comum a todos os perfis, aplicada antes das demais.** Se o **nome da mãe** está preenchido nos dois registros e é
diferente (e não é só erro de uma letra), o par recebe **"homônimo? (nome da mãe diferente)"**, seja qual for o agravo. É a
definição de homônimo do manual de Normas e Rotinas (p. 26): mesmo primeiro e último nome, nascimento e sexo, mães diferentes.
Se o nome da mãe falta em um dos dois, a coluna `nome_da_mae` diz "não comparável" e a regra não se aplica.

#### Tuberculose e hanseníase

Os cadernos classificam o par por três perguntas: é a mesma unidade de saúde? é o mesmo tipo (modo) de entrada? é o mesmo
tratamento? O programa responde às três com os campos da tabela da seção 4.4 e aplica as condições abaixo **na ordem**, parando
na primeira que vale:

| Ordem | Condição | Tipo sugerido | O que o caderno manda |
|---|---|---|---|
| 1 | A entrada de **B** é recidiva ou reingresso | `recidiva/reingresso (tratamentos diferentes; não listar)` | Não listar |
| 2 | Os **tratamentos não se sobrepõem** (o tratamento que começou depois começou mais de 60 dias após o encerramento do outro) | `recidiva/reingresso? (tratamentos não se sobrepõem; não listar)` | Não listar, depois de confirmar |
| 3 | **Mesma unidade** e **mesma entrada** (e, pelas condições anteriores, mesmo tratamento) | `duplicidade verdadeira? (mesma unidade, mesma entrada, mesmo tratamento)` | Complementar A e excluir B |
| 4 | **Unidades diferentes** e A encerrou por **transferência** ou B entrou como **transferência** | `duplo registro por transferência (vincular)` | Vincular A (origem) a B (destino) |
| 5 | **Unidades diferentes**, sem transferência registrada em nenhum dos dois | `duplo registro: transferência? (sem saída/entrada 'transferência' registrada)` | Provável transferência espontânea: confirmar com as unidades e vincular; ou é duplicidade |
| 6 | Mesma unidade, mesmo período, entradas diferentes | `mesma unidade, mesmo período, entrada diferente: conferir` | Examinar as fichas |

Como cada pergunta é respondida:

- **Mesma unidade:** `ID_UNIDADE` igual nos dois e preenchido. Unidade em branco conta como "unidades diferentes".
- **Tipo de entrada.** Tuberculose, campo `TRATAMENTO`: `5` = transferência; `2` = recidiva e `3` = reingresso após
  abandono são "reingresso". Hanseníase, campo `MODOENTR`: `2` a `5` = transferência (mesmo município, outro município,
  outro estado, outro país); `6` = recidiva e `7` = outros ingressos são "reingresso".
- **Saída por transferência.** Tuberculose, `SITUA_ENCE` = `5`. Hanseníase, `TPALTA_N` = `2`, `3`, `4`, `5` ou `9`
  (transferência para o mesmo município, outro município, outro estado, outro país, não especificada).
- **Mesmo tratamento:** os intervalos de tratamento se sobrepõem. O intervalo de cada registro vai da data de início do
  tratamento (`DT_INIC_TR` ou `DTINICTRAT`; se faltar, a data do diagnóstico) até a data de encerramento ou alta
  (`DT_ENCERRA` ou `DTALTA_N`). Encerramento em branco significa tratamento em aberto, que se sobrepõe a qualquer um
  posterior. Há uma **tolerância de 60 dias**: se B começou até 60 dias depois de A encerrar, ainda é o mesmo tratamento,
  porque a unidade que recebe a transferência costuma registrar o início dias ou semanas depois da saída na origem. Se nenhum
  dos dois tem data de início nem de diagnóstico, a pergunta fica sem resposta e a classificação segue para as condições 3 a 6.

Exemplo. Tuberculose: A notificada pela unidade X em março, entrada "caso novo", encerramento "transferência" em maio; B
notificada pela unidade Y em junho, entrada "transferência". Unidades diferentes, tratamentos se sobrepõem (B começou dentro
dos 60 dias), A saiu por transferência: condição 4, "duplo registro por transferência (vincular)".

Outro. Hanseníase: A e B na mesma unidade, as duas "caso novo", A sem data de alta, B dois meses depois. Mesma unidade,
mesma entrada, tratamento de A em aberto: condição 3, "duplicidade verdadeira?". O "?" está lá porque só a comparação das
fichas confirma.

#### Sífilis em gestante

O Ministério não tem regra própria; a referência é a Nota Técnica 10/2020 da SES-DF, que separa gestações pela distância entre
as datas de diagnóstico. A SES-DF usa 12 meses; a área técnica da SESA-CE fixou **45 semanas (315 dias)** (decisão de
2026-10-26 em `METODO.md`). Uma gestação não passa de 42 semanas: dois diagnósticos mais distantes que 45 semanas não podem
ser da mesma gestação, mesmo com alguma folga para erro de data, enquanto a janela de 12 meses deixaria como "mesma
gestação?" pares que já são gestações distintas.

| Condição | Tipo sugerido |
|---|---|
| Falta `DT_DIAG` em um dos dois | `mesma pessoa; sem data de diagnóstico para comparar` |
| Mais de 315 dias entre os diagnósticos | `gestação diferente (N dias entre diagnósticos, > 45 semanas)` |
| Até 315 dias | `mesma gestação? (N dias entre diagnósticos, ≤ 45 semanas; gestação: 1º trimestre / 2º trimestre)` |

No último caso o programa mostra a idade gestacional registrada nas duas fichas (rótulo de `CS_GESTANT`), porque a nota do DF
manda comparar os trimestres: dois diagnósticos a poucos meses de distância com trimestre compatível são a mesma gestação
notificada duas vezes (tipicamente pré-natal e maternidade); trimestre incompatível pede exame das fichas. A coluna `regra`
cita "SES-DF, NT 10/2020, p. 6 (janela de 45 semanas)" justamente porque o corte não é o da nota.

#### Aids e gestante HIV+

Pelo manual de Normas e Rotinas (p. 24), é duplicidade "independente do período de notificação". Todo par recebe
`possível duplicidade (qualquer período)`. Não há mais o que o programa possa olhar; a decisão é inteiramente das fichas.

#### Agravos agudos

Os manuais definem duplicidade como notificação do mesmo evento "durante o período prodrômico", e **não dão número de dias**:
o único exemplo é "data de primeiros sintomas na mesma semana epidemiológica". Por isso o programa **não aplica corte**:
mostra a distância em dias entre as datas do evento e deixa o julgamento para quem revisa.

| Condição | Tipo sugerido |
|---|---|
| Falta a data do evento em um dos dois | `mesma pessoa; sem data do evento para comparar` |
| Caso geral | `mesma pessoa, N dias entre eventos (DT_SIN_PRI): duplicidade se for o mesmo evento` |

O campo entre parênteses é o que foi comparado (seção 4.4). Orientações dos cadernos para a leitura dos dias:

- **Dengue, chikungunya, meningite, hepatites e os demais agudos:** poucos dias entre as datas de primeiros sintomas, mesma
  semana epidemiológica, é o caso típico de duplicidade; meses de distância sugerem episódios diferentes (outro sorotipo,
  outra exposição).
- **Animais peçonhentos:** duplicidade é o **mesmo acidente** (mesma `DT_ACID`). Mais de um acidente no período é "não
  listar". Exceções do caderno: paciente encaminhado para soroterapia fica com a ficha do serviço que aplicou o soro; soro em
  mais de um serviço, mantêm-se as duas fichas (controle de ampolas).
- **Violência interpessoal e autoprovocada:** duplicidade é a **mesma data de ocorrência**, conferindo hora e circunstâncias,
  porque a mesma pessoa pode sofrer mais de uma violência no mesmo dia. Outra situação de violência no período é "não listar".
- **Agravos de saúde do trabalhador:** regra geral dos agudos; novo acidente no período é "não listar".
- **Sífilis adquirida e congênita, LTA, LV:** não há regra específica nos manuais; vale a regra geral. Para sífilis, a Nota
  Técnica Conjunta 01/2025 da SESA-CE manda manter a ficha **mais completa com diagnóstico mais antigo** (ver 4.6).

### 4.6 A ficha sugerida para manter

A regra é a do Ministério (Normas e Rotinas 2007, p. 24; Instrução Normativa 02/2005, art. 20): **fica a notificação mais
antiga**; se a data de notificação é a mesma, **fica a do município de residência**. O programa aplica exatamente isso e
escreve o motivo na coluna `motivo_ficha_sugerida`:

| Situação | `ficha_sugerida_manter` | `motivo_ficha_sugerida` |
|---|---|---|
| Datas de notificação diferentes | a mais antiga | "notificação mais antiga" |
| Mesma data; só uma foi notificada pelo município de residência (`ID_MUNICIP` = `ID_MN_RESI`) | essa | "mesma data; notificada pelo município de residência" |
| Mesma data; as duas ou nenhuma pelo município de residência | a primeira no arquivo (A) | "mesma data; sem desempate pela residência (primeira na ordem do arquivo)" |

A SESA-CE, para sífilis, manda manter a ficha **de maior completude e data de diagnóstico mais antiga**. O programa não
aplica essa regra, mas dá os dados para aplicá-la: `completude_A` e `completude_B` (quantos campos do DBF estão preenchidos em
cada ficha) e a data de diagnóstico de cada lado. A ficha mantida deve ser complementada com o que a outra tem antes da
exclusão, em qualquer das duas regras.

### 4.7 Pares já julgados no Sinan

O DBF traz dois campos internos: `NDUPLIC_N` (`1` = a equipe marcou "não é duplicidade, não listar"; `2` = "duplicidade, não
contar") e `IN_VINCULA` (`1` = vinculado). Quando qualquer um dos dois registros do par tem `NDUPLIC_N` igual a 1 ou 2, ou
`IN_VINCULA` igual a 1, a coluna `ja_julgado_no_sinan` fica "sim".

Esses pares **não são achados novos**: alguém já olhou e decidiu. Eles continuam na aba porque o programa não sabe se a
decisão foi sobre este par ou sobre outro par com o mesmo registro, e porque a chave adicional pode ter trazido um terceiro
registro. Na revisão, trate-os depois dos "não".

### 4.8 As colunas das duas abas

As duas abas vêm **ordenadas pela ADS da notificação A e depois pela data**, que é a ordem em que uma regional lê a lista.
A ADS vem da tabela de regionalização da SESA-CE pelo município de notificação; se o município não está na tabela (outro
estado), o programa usa o rótulo da regional do próprio Sinan (`ID_REGIONA`), e se também não há, a coluna fica vazia.

`duplicidades_resumo`, para circular:

| Coluna | Conteúdo |
|---|---|
| `par` | Número do par (o mesmo nas duas abas). |
| `ADS_notificacao_A`, `ADS_notificacao_B` | ADS do município que notificou cada ficha. |
| `ADS_residencia` | ADS do município de residência; "X / Y" quando as fichas discordam. |
| `tipo_sugerido` | Seção 4.5. |
| `ja_julgado_no_sinan` | Seção 4.7. |
| `dias_entre_eventos` | Distância entre as datas do evento (seção 4.4). |
| `paciente`, `nascimento` | Como estão na ficha A. |
| `notificacao_A`, `data_A`, `unidade_A`, `municipio_A` | Número, data, unidade e município de notificação da ficha A. |
| `notificacao_B`, `data_B`, `unidade_B`, `municipio_B` | O mesmo para B. |
| `ficha_sugerida_manter` | Número da notificação que a regra do MS manda manter (seção 4.6). |
| `decisao_da_equipe`, `observacao` | Em branco, para a equipe preencher. |

`duplicidades`, completa, tem as mesmas colunas de identificação e mais:

| Coluna | Conteúdo |
|---|---|
| `chaves` | Quais chaves acharam o par, separadas por `+` (seção 4.3). |
| `regra` | Fonte da regra aplicada (manual, ano, página). |
| `ADS_residencia_A`, `ADS_residencia_B` | ADS de residência de cada ficha, separadas. |
| `campo_do_evento` | Qual campo de data foi comparado. |
| `mesma_unidade`, `mesmo_municipio_notif` | "sim" ou "não". |
| `nome_da_mae` | "igual", "diferente" ou "não comparável". |
| `motivo_ficha_sugerida` | Seção 4.6. |
| `completude_A`, `completude_B` | Campos preenchidos em cada ficha. |
| `<campo>_A`, `<campo>_B` (e `<campo>_rotulo_A/B`) | Lado a lado, para os dois registros: `NU_NOTIFIC`, `DT_NOTIFIC`, `NM_PACIENT`, `DT_NASC`, `CS_SEXO`, `NM_MAE_PAC`, `ID_MUNICIP`, `ID_UNIDADE`, `ID_MN_RESI`, `NDUPLIC_N`, `IN_VINCULA` e os campos do perfil (entrada, encerramento, datas de tratamento, `CS_GESTANT`), com o rótulo quando existe. |

### 4.9 Roteiro de revisão

1. Filtre `ja_julgado_no_sinan` = "não".
2. Comece pelos tipos de ação mais clara: `duplo registro por transferência (vincular)` e `recidiva/reingresso` em
   tuberculose e hanseníase; `gestação diferente` em sífilis em gestante (não é duplicidade; "não listar" se o Sinan
   insistir em apontar).
3. Nos `duplicidade verdadeira?`, `mesma gestação?` e `mesma pessoa, N dias`, abra as duas fichas no Sinan, compare, e use
   `ficha_sugerida_manter` com a regra da sua secretaria. Complemente a ficha mantida antes de excluir a outra.
4. Nos `homônimo?`, confira nome da mãe e endereço; se são pessoas diferentes, "não listar" no Sinan.
5. Olhe a coluna `chaves`: um par achado só por `nasc_nome_sim` ou `nome_nasc1` é uma correção de cadastro em potencial
   (nome ou data de nascimento errados em uma das fichas), além de possível duplicidade.
6. Registre a decisão em `decisao_da_equipe`. O programa não lê essa coluna de volta: na próxima exportação, o que foi
   excluído some e o que foi marcado "não listar" aparece com `ja_julgado_no_sinan` = "sim".

### 4.10 Limites conhecidos

- A chave `nasc_nome_sim` só compara nomes que partilham o primeiro ou o último nome; erro no primeiro **e** no último nome
  ao mesmo tempo não é achado.
- Erro de digitação no nome da mãe é tolerado na comparação (similaridade de 0,85), mas não na chave `nome_mae`, que exige
  igualdade.
- Nenhuma chave usa a pesquisa fonética do Sinan (`SOUNDEX`, `FONETICA_N`). Ficou de fora por decisão prévia, não por
  medida: só entra se uma base real mostrar pares que as quatro chaves não acham.
- A tolerância de 60 dias entre encerramento e novo início (tuberculose e hanseníase) é uma escolha de implementação, não
  está nos cadernos.
- Os critérios foram aceitos em bases sintéticas com verdade conhecida (`METODO.md`, 2026-10-25). A validação em base real,
  com julgamento às cegas pela equipe, está prevista mas ainda não foi registrada.
- Tempo em base muito grande (dengue com um milhão de registros) não foi medido.

## 5. O arquivo de log

`<nome>_anotado.log.txt` não contém dado de paciente: só nomes de campos, contagens e avisos. É o arquivo a anexar numa issue.
Nele estão:

- a versão do programa (primeira linha);
- a codificação detectada no DBF (cp850 ou cp1252) e o `.def` escolhido;
- os campos sem tabela de rótulos e a cobertura de cada tabela externa (quantas unidades, ocupações e municípios ganharam nome);
- "Duplicidades suspeitas: N pares (perfil X; padrao N, nome_mae N, nome_nasc1 N, nasc_nome_sim N; já julgados no Sinan N)",
  a contagem por tipo sugerido, os registros que nenhuma chave alcança (seção 4.3) e a cobertura da tabela de ADS.

## 6. Perguntas frequentes

**Apareceram pares que não são duplicidade.** Esperado. A chave `padrao` é a do Sinan e lista homônimos como o Sinan lista;
as chaves adicionais trocam precisão por sensibilidade. A aba é uma lista para revisar, não um resultado.

**Um par que eu sei que existe não apareceu.** Veja na seção 4.3 o que cada chave não alcança: dois componentes errados na
data de nascimento com nome da mãe diferente, erro no primeiro e no último nome, registro sem nascimento e sem mãe. Veja
também no log se o registro está entre os que "nenhuma chave alcança".

**O tipo sugerido está errado para um par.** Pode ser: os campos de tratamento estão em branco ou errados nas fichas (o
programa só vê o que o DBF traz); ou a regra é discutível. No segundo caso, abra uma issue de sugestão descrevendo a situação
**sem dados de paciente**: os critérios estão escritos e datados em `METODO.md` e mudam por lá.

**A coluna de ADS está vazia.** O município de notificação não está na tabela de regionalização da SESA-CE (outro estado) e o
Sinan não trouxe regional. As demais colunas não dependem dela.

**Posso mudar a janela de 45 semanas, ou os 60 dias?** Não pela interface, nesta versão. São constantes no código
(`GESTATION_WINDOW_DAYS`, `TRANSFER_GAP_DAYS` em `duplicates.py`), descritas aqui e em `METODO.md`.

**O xlsx ficou enorme.** Ele tem todos os campos do DBF mais um rótulo por campo codificado; para a planilha dinâmica, use só a
aba `dados`. Acima do limite de linhas do Excel a saída é dividida por ano.

## 7. De onde vêm as regras

- **Definições e ações:** MS/SVS, *Sinan — Normas e Rotinas*, 2ª ed., 2007 (p. 23–26 e 49); Instrução Normativa 02/2005;
  *Manual do Sistema Sinan NET*, 2007 (p. 85–87); *Roteiro para uso do Sinan NET — Caderno geral*, 2008.
- **Tuberculose:** MS, *Caderno de análise — Tuberculose*, 2019 (p. 7–11, fluxograma na p. 11; intercorrências p. 17–18).
- **Hanseníase:** MS/SVSA, *Roteiro para uso do Sinan Net Hanseníase e Manual para tabulação dos indicadores*, 2026 (p. 27–31).
- **Animais peçonhentos, meningite, violência, saúde do trabalhador:** cadernos de análise respectivos e o manual da SESA-CE
  de 2023.
- **Sífilis em gestante:** SES-DF, Nota Técnica 10/2020 (p. 6), com janela de 45 semanas fixada pela SESA-CE.
- **Sífilis (Ceará):** SESA-CE, Nota Técnica Conjunta 01/2025 (p. 11–13).
- **Campos internos do DBF** (`NDUPLIC_N`, `IN_VINCULA`): MS/DATASUS, *Dicionário de dados — Notificação individual*, 2018.

O levantamento completo, com onde encontrar cada documento e as divergências entre eles, está em
[`duplicidades_definicoes_manuais.md`](duplicidades_definicoes_manuais.md). As decisões que transformaram as definições em
regras do programa, com data e critério de aceite, estão em [`METODO.md`](METODO.md). Para citar o programa, use o DOI em
[`CITATION.cff`](../CITATION.cff) e no [README](../README.md). Problemas e sugestões: pelas
[issues](https://github.com/cgarciafilho/anotador-sinan/issues/new/choose), sempre sem dados de paciente.

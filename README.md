# anotador SINAN

Programa para equipes de vigilância epidemiológica que trabalham com o **Sinan NET**. A partir do DBF exportado pelo
sistema (`C:\SinanNet\BaseDBF\TUBENET.DBF`, `SIFGENET.DBF`, `HANSNET.DBF`…), gera um **xlsx anotado**: cada campo codificado
vem seguido do seu rótulo oficial, segundo as tabelas `.def`/`.cnv` do TabWin (DATASUS), pronto para planilha dinâmica.
Lista também as **duplicidades suspeitas** (pares de notificações que podem ser da mesma pessoa), com o tipo sugerido na
linguagem dos cadernos do Sinan e a regra que o sustenta, para **revisão humana**.

Roda no Windows **sem instalar nada e sem administrador**: o zip traz um Python embutido. Não altera, apaga nem mescla
registros; não envia nada pela rede; não grava fora da pasta do DBF.

Desenvolvido para as áreas técnicas da Secretaria da Saúde do Ceará (SESA-CE), mas as tabelas do TabWin cobrem os 60
agravos do Sinan NET e o programa não depende de nada específico do Ceará, exceto a coluna de ADS nas abas de duplicidades.

## Baixar e usar

1. Na página de [releases](https://github.com/cgarciafilho/anotador-sinan/releases), baixe o `anotador_sinan_vX.Y.Z.zip`
   da versão mais recente (cerca de 100 MB; a soma sha256 está em `SHA256SUMS.txt`).
2. Descompacte em qualquer pasta (por exemplo `Documentos\anotador`).
3. Arraste um ou mais arquivos `.DBF` do Sinan NET sobre `anotar.bat`. Aguarde a janela terminar.
4. O `<nome>_anotado.xlsx` e o `<nome>_anotado.log.txt` ficam ao lado de cada DBF.

Se o Windows perguntar sobre "aplicativo não reconhecido", escolha "Mais informações" e "Executar assim mesmo": o pacote é
só Python (python.org) com as bibliotecas pandas, numpy, openpyxl e dbfread, sem instalação. O `LEIA-ME.txt` dentro do zip
descreve cada aba e cada coluna; o manual completo está no zip como `MANUAL.pdf` (para imprimir) e `MANUAL.md`, e o PDF
também vai anexado a cada release. O texto-fonte é [`docs/MANUAL.md`](docs/MANUAL.md).

**Sigilo.** O xlsx copia todos os campos do DBF, inclusive nome, nome da mãe, nascimento e endereço; as abas de
duplicidades também trazem nome do paciente. Ele é tão nominal quanto o DBF e deve ficar no mesmo lugar protegido.
O `.log.txt` não contém dados de pacientes, só nomes de campos e contagens, e pode ser enviado para relatar um problema.

## O que sai

| Aba | Conteúdo |
|---|---|
| `dados` | Todos os registros e campos do DBF; cada campo com tabela ganha `<campo>_rotulo` ao lado. `NU_IDADE_N` ganha idade em anos e faixa etária; municípios recebem o nome; datas saem como data do Excel. Cabeçalho "Nome por extenso (CAMPO)". |
| `duplicidades` | Um par suspeito por linha: a chave que o ligou, o tipo sugerido (duplicidade verdadeira, duplo registro por transferência, recidiva/reingresso, homônimo, gestação diferente…), a regra do manual, se o par já foi julgado no Sinan (`NDUPLIC_N`, `IN_VINCULA`), os dias entre os eventos, a ficha que a regra do MS manda manter e os campos dos dois registros lado a lado. |
| `duplicidades_resumo` | Versão curta do mesmo par (ADS, tipo sugerido, paciente, as duas notificações com data, unidade e município, ficha sugerida) com colunas vazias para a decisão da equipe. |
| `campos` | Uma linha por coluna: nome por extenso, campo do DBF, tipo, de onde veio o nome, tabela de rótulos usada. |
| `dicionario` | Todas as tabelas usadas (campo, tabela, códigos, rótulo). |

Acima de 1.048.575 registros (limite do Excel) a saída é dividida em um xlsx por ano de notificação, com aviso.

## O que não faz

- Não decide duplicidade: tipo e ficha a manter são sugestões; a exclusão ou vinculação é feita no Sinan por quem tem autorização.
- Campos cujo `.cnv` o TabWin não distribui ficam sem rótulo; o log diz quais (hoje só a UF de infecção da leptospirose
  e o bairro de dengue/chikungunya).
- Ainda não preenche modelos de planilha dinâmica por agravo.
- **Em revisão: CNAE nas fichas de saúde do trabalhador** (acidente de trabalho grave, exposição a material biológico,
  intoxicação exógena, LER/DORT, transtorno mental, PAIR, câncer e dermatose relacionados ao trabalho). A tabela de CNAE que o
  TabWin distribui é a CNAE 1.0 (580 classes de 5 dígitos); numa rodada com bases reais de 2026, 45% dos códigos preenchidos
  ficaram sem nome e parte dos que receberam nome pode ter recebido o da classe homônima da CNAE 1.0. Até a próxima versão,
  trate `CNAE_rotulo` e `CNAE_PRIN_rotulo` como provisórios; os demais campos dessas fichas, inclusive os CID, não são afetados.

## Versões

Numeração [SemVer](https://semver.org/lang/pt-BR/) (`MAIOR.MENOR.CORREÇÃO`), uma tag `vX.Y.Z` por versão e o histórico
em [`CHANGELOG.md`](CHANGELOG.md). A versão que gerou um xlsx está na primeira linha do `.log.txt`. O zip de cada versão
é montado pelo GitHub Actions a partir da tag ([`.github/workflows/release.yml`](.github/workflows/release.yml)), com as
versões do Python e das bibliotecas fixadas em [`build/build_windows_zip.sh`](build/build_windows_zip.sh), e a soma sha256
publicada junto. Enquanto a versão for `0.x`, a forma das abas e das colunas pode mudar entre versões menores.

## Como citar

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23715001.svg)](https://doi.org/10.5281/zenodo.23715001)

Cada release recebe um DOI no Zenodo, que arquiva o código-fonte da versão. O DOI de conceito
[10.5281/zenodo.23715001](https://doi.org/10.5281/zenodo.23715001) representa todas as versões e resolve sempre para a
mais recente; use-o para citar o programa em geral. Para reprodutibilidade, cite o DOI da versão usada: a v0.2.0 é
[10.5281/zenodo.23715002](https://doi.org/10.5281/zenodo.23715002) e a v0.3.0 é
[10.5281/zenodo.23735267](https://doi.org/10.5281/zenodo.23735267) e a v0.4.0 é
[10.5281/zenodo.23805076](https://doi.org/10.5281/zenodo.23805076); o de cada versão nova é anotado aqui e em
[`CITATION.cff`](CITATION.cff) assim que o Zenodo o emitir, na publicação do release (o GitHub mostra "Cite this
repository" na barra lateral). Forma sugerida, com o DOI da versão:

> Garcia Filho, C. (2026). *anotador SINAN* (v0.4.0) [software]. Zenodo. https://doi.org/10.5281/zenodo.23805076

## Método e documentação

- [`docs/MANUAL.md`](docs/MANUAL.md): manual para quem usa o programa: como rodar, como ler cada aba e, regra por regra,
  como os pares de duplicidade são achados (quatro chaves), classificados por agravo e qual ficha a regra do MS manda manter.
  Um teste (`tests/test_manual.py`) falha quando o código muda e o manual não. O PDF é gerado desse mesmo arquivo por
  [`build/build_manual_pdf.py`](build/build_manual_pdf.py) (`pip install markdown weasyprint`), no CI e no release.
- [`docs/METODO.md`](docs/METODO.md): decisões datadas e append-only, com os critérios de aceite escritos **antes** de medir
  (base sintética com verdade conhecida; resultados registrados mesmo quando reprovados) e os bugs corrigidos.
- [`docs/duplicidades_definicoes_manuais.md`](docs/duplicidades_definicoes_manuais.md): o que os manuais do Ministério da
  Saúde e das secretarias chamam de duplicidade, por agravo, com fonte e página; é a base das regras da aba `duplicidades`.
- Alternativa simples que o programa tem de vencer: TabWin + Excel à mão para os rótulos, e o relatório de duplicidade do
  próprio Sinan NET (chave primeiro e último nome + nascimento + sexo) para os pares.

## Rodar a partir do código-fonte

Python 3.13 com `pandas==3.0.6`, `numpy==2.5.4`, `openpyxl==3.1.5`, `dbfread==2.0.7` (as mesmas versões do zip) e, para os
testes, `pytest`.

```bash
python -m venv .venv && . .venv/bin/activate
pip install "pandas==3.0.6" "numpy==2.5.4" "openpyxl==3.1.5" "dbfread==2.0.7" pytest
PYTHONPATH=src python -m sinan_anotador --tab tabelas/tab_sinannet ARQUIVO.DBF   # opções: --saida, --codificacao, --sem-duplicidades
python -m pytest tests/ -q                                                          # 153 testes, ~3 min, só bases sintéticas
```

Para montar o zip Windows localmente: `build/build_windows_zip.sh` (precisa de rede para python.org e PyPI; o resultado fica
em `build/dist/`, fora do git).

Este repositório **não recebe dado real do Sinan**, nem desidentificado. Os testes usam bases sintéticas geradas por script
em `tests/`, com verdade conhecida; o DBF real só é testado por quem o detém, na própria máquina.

## Estrutura

```
src/sinan_anotador/   código (cnv.py, dbf.py, annotate.py, names.py, lookup.py, duplicates.py, excel.py, cli.py)
tests/                testes e geradores de base sintética
build/                anotar.bat, LEIA-ME.txt, o script que monta o zip e o que gera o manual em PDF
tabelas/tab_sinannet/ .def/.cnv (60 agravos, pacote completo de 2024) e DBFs do TAB_SINANNET (TabWin, DATASUS) e unidanet.csv (CNES, 2026)
tabelas/dicionarios/  nomes por extenso dos campos (dicionários de dados do DATASUS: TB, hanseníase, LTA, LV)
tabelas/regionalizacao_sesa_sr_ads.csv   município → ADS e superintendência regional (SESA-CE, 2022)
scripts/              make_unidanet_csv.py: atualiza unidanet.csv a partir do CNES público
docs/                 MANUAL.md (manual do usuário), METODO.md e o levantamento das definições de duplicidade
```

## Fontes dos dados e créditos

- Tabelas `.def`/`.cnv` e DBFs auxiliares: TabWin, pacote `TAB_SINANNET` do FTP do DATASUS / Ministério da Saúde.
- `unidanet.csv`: `tbEstabelecimento` da base de dados pública do CNES (DATASUS), setembro de 2026.
- Dicionários de dados por agravo: PDFs do DATASUS.
- Regionalização por ADS e superintendência regional: SESA-CE, lista de 02/03/2022.
- Regras de duplicidade: manuais do Sinan (MS/SVS), cadernos de análise por agravo, Nota Técnica SES-DF 10/2020, notas
  técnicas da SESA-CE; referências em `docs/duplicidades_definicoes_manuais.md`.

Esses dados são públicos e pertencem às instituições que os publicam; a licença MIT deste repositório cobre o código e os
textos próprios.

## Problemas e sugestões

Abra uma [issue](https://github.com/cgarciafilho/anotador-sinan/issues/new/choose) pelo modelo (problema ao rodar, ou
sugestão e dúvida) com a versão (primeira linha do `.log.txt`) e, se possível, o `.log.txt`. Nunca anexe o DBF nem o xlsx,
nem cole trechos deles: são nominais; issue com dado de paciente é apagada. Não há suporte por e-mail: tudo passa pelas issues.

## Licença

[MIT](LICENSE). Copyright (c) 2026 Carlos Garcia Filho.

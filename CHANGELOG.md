# Registro de mudanças

Formato de [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); numeração [SemVer](https://semver.org/lang/pt-BR/):
`MAIOR.MENOR.CORREÇÃO`. Enquanto a versão for `0.x`, a forma das abas e das colunas ainda pode mudar entre versões menores.
Cada versão tem uma tag `vX.Y.Z` no git e um release no GitHub com o zip para Windows e sua soma sha256.

## [Não publicado]

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

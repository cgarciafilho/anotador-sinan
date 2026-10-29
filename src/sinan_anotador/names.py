"""Long names for the DBF fields ("Nome por extenso (CAMPO)" in the xlsx header and in the `campos` sheet).

Sources, in order of preference:
1. CSV dictionaries in a `dicionarios/` folder (next to the TabWin tables or given with --dicionarios): the files the
   previous project extracted from the DATASUS PDF dictionaries (columns `variavel` / `variavel_dbf_observado` and
   `nome_campo`, as written by the dictionary-extraction script of the previous analysis project). Any CSV with columns `campo,nome` works too.
2. For the identification fields of the Sinan NET individual notification form (fields 1-30 and control fields,
   which every .def shares but names tersely: "Mun US Noti", "Escolar SinanNET"), a built-in table with the names as
   printed on the form. Marked as such in the `campos` sheet; a CSV dictionary overrides it.
3. The label of the .def line used for the field (TabWin's own, abbreviated: "Situação Encerra."), cleaned of the
   tabulation wording ("Ano da Notific" -> "Data Notific"; "Mun Resid CE" -> "Mun Resid").
4. The same label taken from any other .def (NotIndiviNet first), for fields the chosen .def does not describe.
Fields found nowhere (free text, addresses not in the table) keep the raw name. The TabWin label is always kept in the
`campos` sheet for traceability.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .cnv import DefFile, def_field, def_files, parse_def

# Sinan NET individual notification form (ficha de notificação/investigação, campos 1-30 e de controle).
NOTIFICATION_FORM = {
    "TP_NOT": "Tipo de notificação", "ID_AGRAVO": "Agravo/doença (CID-10)", "DT_NOTIFIC": "Data da notificação",
    "SEM_NOT": "Semana epidemiológica da notificação", "NU_ANO": "Ano da notificação", "SG_UF_NOT": "UF de notificação",
    "ID_MUNICIP": "Município de notificação", "ID_REGIONA": "Regional de saúde de notificação",
    "ID_UNIDADE": "Unidade de saúde notificadora", "DT_SIN_PRI": "Data dos primeiros sintomas",
    "SEM_PRI": "Semana epidemiológica dos primeiros sintomas", "DT_DIAG": "Data do diagnóstico",
    "SEM_DIAG": "Semana epidemiológica do diagnóstico", "NU_NOTIFIC": "Número da notificação",
    "NM_PACIENT": "Nome do paciente", "DT_NASC": "Data de nascimento", "NU_IDADE_N": "Idade (código Sinan)",
    "CS_SEXO": "Sexo", "CS_GESTANT": "Gestante", "CS_RACA": "Raça/cor", "CS_ESCOL_N": "Escolaridade",
    "ID_CNS_SUS": "Cartão SUS", "NM_MAE_PAC": "Nome da mãe", "SG_UF": "UF de residência",
    "ID_MN_RESI": "Município de residência", "ID_RG_RESI": "Regional de saúde de residência",
    "ID_DISTRIT": "Distrito de residência", "ID_BAIRRO": "Bairro de residência (código)", "NM_BAIRRO": "Bairro de residência",
    "ID_LOGRADO": "Logradouro (código)", "NM_LOGRADO": "Logradouro", "NU_NUMERO": "Número", "NM_COMPLEM": "Complemento",
    "ID_GEO1": "Geocampo 1", "ID_GEO2": "Geocampo 2", "NM_REFEREN": "Ponto de referência", "NU_CEP": "CEP",
    "NU_DDD_TEL": "DDD do telefone", "NU_TELEFON": "Telefone", "CS_ZONA": "Zona de residência", "ID_PAIS": "País de residência",
    "DT_INVEST": "Data da investigação", "ID_OCUPA_N": "Ocupação (CBO)", "DT_ENCERRA": "Data de encerramento",
    "DT_DIGITA": "Data de digitação", "DT_TRANSUS": "Data de transferência (unidade)", "DT_TRANSDM": "Data de transferência (município)",
    "DT_TRANSSM": "Data de transferência (regional)", "DT_TRANSRM": "Data de transferência (estado)",
    "DT_TRANSRS": "Data de transferência (regional, saída)", "DT_TRANSSE": "Data de transferência (federal)",
    "NU_LOTE_V": "Lote vertical", "NU_LOTE_H": "Lote horizontal", "CS_FLXRET": "Fluxo de retorno",
    "FLXRECEBI": "Fluxo recebido", "IDENT_MICR": "Identificador de microdados", "MIGRADO_W": "Migrado do Sinan Windows",
    "TPUNINOT": "Tipo de unidade notificadora", "NDUPLIC_N": "Marca de duplicidade", "IN_VINCULA": "Vinculado",
    "NU_PRONTUA": "Número do prontuário", "FONETICA_N": "Nome fonético (campo de sistema)",
    "SOUNDEX": "Soundex do nome (campo de sistema)",
}

SOURCE_CSV = "dicionário CSV"

# .def name -> stem of the CSV dictionary of the same disease in dicionarios/ (checked first; the others fill the rest)
DEF_TO_CSV = {"TuberculNET": "dicionario_tuberculose", "TuberculNET5_0": "dicionario_tuberculose", "HansNET": "dicionario_hans",
              "LeishtegNET": "dicionario_lta", "LeishvisNET": "dicionario_lv",
              # expected names for dictionaries not yet extracted (PLANO P1)
              "GestSifNET": "dicionario_sifg", "SifilisNET": "dicionario_sifc", "DengueNET": "dicionario_dengue"}
SOURCE_DEF = ".def do agravo (TabWin)"
SOURCE_OTHER_DEF = "outro .def (TabWin)"
SOURCE_FORM = "ficha de notificação (tabela interna)"

RE_YEAR = re.compile(r"^Ano\s+(da|do|de|d[ao]s)?\s*", re.IGNORECASE)
RE_TRAILING_UF = re.compile(r"\s+(AC|AL|AM|AP|BA|BR|CE|DF|ES|GO|MA|MG|MS|MT|PA|PB|PE|PI|PR|RJ|RN|RO|RR|RS|SC|SE|SP|TO)$")
SKIP_LABEL = re.compile(r"^(Mes|Mês|Trim\.?|Sem\.?\s*Epid|Fx\s*Et[áa]ria|Fx\s*Etaria|Idade detalhada|Coorte|Reg\.?\s*Metr|Capitais|"
                        r"Mun Priorit|Mun Pri|Mun Fronteira|Mun TRM|Mun Prior|Hosp NHE|Mun\.? Not\.? NHE|Mun Prior Indig)", re.IGNORECASE)
SKIP_UF_LABEL = re.compile(r"^UF\b", re.IGNORECASE)      # "UF Residência" on ID_MN_RESI is a grouping; on SG_UF it is the name


@dataclass
class FieldName:
    field: str
    name: str | None
    source: str | None
    def_label: str | None = None      # TabWin label as written, for the `campos` sheet

    def header(self, suffix: str = "") -> str:
        col = f"{self.field}{suffix}"
        if not self.name:
            return col
        if suffix == "_rotulo":
            return f"{self.name} — rótulo ({col})"
        if suffix == "_anos":
            return f"Idade em anos ({col})"
        return f"{self.name} ({col})"


def clean_def_label(label: str, field: str) -> str | None:
    """Turn a tabulation label into a field name; None when the line is a derived grouping we should not use."""
    lab = " ".join(label.split())
    if field.startswith("DT") and RE_YEAR.match(lab):
        rest = RE_YEAR.sub("", lab).strip()
        return f"Data {rest}" if rest else "Data"
    if SKIP_LABEL.match(lab):
        return None
    if SKIP_UF_LABEL.match(lab) and "UF" not in field.upper():
        return None
    lab = RE_TRAILING_UF.sub("", lab)
    return lab or None


def labels_from_def(deffile: DefFile, preferred_cnv: dict[str, str] | None = None) -> dict[str, str]:
    """field -> cleaned label; the line whose .cnv was chosen for the field wins, else the first usable line."""
    preferred_cnv = {k.upper(): v.upper() for k, v in (preferred_cnv or {}).items()}
    out: dict[str, str] = {}
    first: dict[str, str] = {}
    for ln in deffile.lines:
        name = clean_def_label(ln.label, ln.field)
        if not name:
            continue
        if ln.field in preferred_cnv and ln.cnv and ln.cnv.upper() == preferred_cnv[ln.field]:
            out.setdefault(ln.field, name)
        first.setdefault(ln.field, name)
    for f, n in first.items():
        out.setdefault(f, n)
    return out


def load_csv_dictionaries(folder: Path | None, def_name: str | None = None) -> dict[str, tuple[str, str]]:
    """field -> (name, csv file). The CSV of the recognised disease is read first, so its names win on fields that mean
    different things in different diseases (TRATAMENTO: 'Tipo de Entrada' in TB, a date in VL). Rows the extractor filled
    from the .def itself (match_dbf == def_tabwin) carry the TabWin label, not the dictionary's, and are skipped."""
    names: dict[str, tuple[str, str]] = {}
    if not folder or not Path(folder).is_dir():
        return names
    files = sorted(Path(folder).glob("*.csv"))
    own = DEF_TO_CSV.get(def_name or "")
    files.sort(key=lambda p: (p.stem != own, p.name.lower()))
    seen: dict[str, list[tuple[str, str]]] = {}      # field -> every (name, file) that defines it, own file first
    for p in files:
        try:
            text = p.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            text = p.read_text(encoding="latin-1")
        rows = list(csv.DictReader(text.splitlines()))
        if not rows:
            continue
        cols = {c.lower(): c for c in rows[0].keys() if c}
        key_cols = [cols[c] for c in ("variavel_dbf_observado", "variavel", "campo") if c in cols]
        name_col = next((cols[c] for c in ("nome_campo", "nome") if c in cols), None)
        if not key_cols or not name_col:
            continue
        match_col = cols.get("match_dbf")
        for r in rows:
            name = " ".join((r.get(name_col) or "").split())
            if not name or name.startswith("(") or (match_col and (r.get(match_col) or "").strip() == "def_tabwin"):
                continue       # "(campo interno)" and .def-derived rows are extraction leftovers, not dictionary names
            for kc in key_cols:
                k = (r.get(kc) or "").strip().upper()
                if k:
                    names.setdefault(k, (name, p.name))
                    seen.setdefault(k, []).append((name, p.name))
    # a field named only by other diseases' CSVs is used only when those CSVs agree on what it is (same first word):
    # TRATAMENTO is 'Tipo de Entrada' in TB and a date in VL, so for a third disease neither name is trusted
    for k, entries in seen.items():
        if entries[0][1] == f"{own}.csv":
            continue
        heads = {_first_word(n) for n, _ in entries}
        if len(heads) > 1:
            del names[k]
    return names


def _first_word(name: str) -> str:
    w = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.split(r"[^a-z0-9]+", w.strip())[0] if w.strip() else ""


def load_csv_categories(folder: Path | None, def_name: str | None) -> dict[str, tuple[list[tuple[str, str]], str]]:
    """field -> (categories as (codes, label) pairs, csv file) from the disease's OWN dictionary CSV: column
    `categorias_cnv` ("0-9=Ign/Branco;1=PQT/PB/6 DOSES;...", copied from the .cnv when the dictionary was extracted), else
    `categorias`. A fallback for .cnv files the .def cites but the TabWin package lacks (ESQUETER.CNV, 2026-10-28)."""
    out: dict[str, tuple[list[tuple[str, str]], str]] = {}
    own = DEF_TO_CSV.get(def_name or "")
    if not folder or not own:
        return out
    p = Path(folder) / f"{own}.csv"
    if not p.is_file():
        return out
    try:
        text = p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = p.read_text(encoding="latin-1")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        return out
    cols = {c.lower(): c for c in rows[0].keys() if c}
    key_cols = [cols[c] for c in ("variavel_dbf_observado", "variavel", "campo") if c in cols]
    for r in rows:
        spec = ""
        for c in ("categorias_cnv", "categorias"):
            if c in cols and (r.get(cols[c]) or "").strip():
                spec = r[cols[c]].strip()
                break
        if not spec or "=" not in spec:
            continue
        cats: list[tuple[str, str]] = []
        for part in spec.split(";"):
            if "=" not in part:
                continue
            codes, label = part.split("=", 1)
            codes, label = codes.strip(), " ".join(label.split())
            if codes and label and re.fullmatch(r"[0-9A-Za-z_\-, ]+", codes):
                cats.append((codes, label))
        if not cats:
            continue
        for kc in key_cols:
            k = (r.get(kc) or "").strip().upper()
            if k:
                out.setdefault(k, (cats, p.name))
    return out


def resolve_names(columns: list[str], deffile: DefFile | None, tab_dir: Path, preferred_cnv: dict[str, str] | None = None,
                  csv_dir: Path | None = None) -> dict[str, FieldName]:
    csv_names = load_csv_dictionaries(csv_dir if csv_dir is not None else Path(tab_dir).parent / "dicionarios",
                                      deffile.name if deffile else None)
    own = labels_from_def(deffile, preferred_cnv) if deffile else {}
    others: dict[str, str] = {}
    out: dict[str, FieldName] = {}
    pending = [c for c in columns if c.upper() not in csv_names and def_field(c) not in own
               and c.upper() not in NOTIFICATION_FORM]
    if pending:
        defs = sorted(def_files(tab_dir), key=lambda p: (p.stem != "NotIndiviNet", p.stem.lower()))
        for p in defs:
            if deffile and p.stem == deffile.name:
                continue
            for f, n in labels_from_def(parse_def(p)).items():
                others.setdefault(f, n)
            if all(def_field(c) in others for c in pending):
                break
    raw_def: dict[str, str] = {}
    if deffile:
        pref = {k.upper(): v.upper() for k, v in (preferred_cnv or {}).items()}
        for ln in deffile.lines:                      # label of the line whose table was used, else the first line
            if ln.field in pref and ln.cnv and ln.cnv.upper() == pref[ln.field]:
                raw_def[ln.field] = ln.label
        for ln in deffile.lines:
            raw_def.setdefault(ln.field, ln.label)
    own_csv = f"{DEF_TO_CSV.get(deffile.name, '')}.csv" if deffile else ""
    for c in columns:
        k = c.upper()
        kd = def_field(c)           # the .def may spell the field differently (BACILOSCO -> BACILOSCOP)
        # a CSV of another disease names the shared notification fields with extraction noise ("Semana epidemiológic a");
        # for those fields the form table wins unless the CSV is the disease's own
        if k in csv_names and (k not in NOTIFICATION_FORM or csv_names[k][1] == own_csv):
            out[c] = FieldName(c, csv_names[k][0], f"{SOURCE_CSV} ({csv_names[k][1]})", raw_def.get(kd))
        elif kd in csv_names and kd != k:
            out[c] = FieldName(c, csv_names[kd][0], f"{SOURCE_CSV} ({csv_names[kd][1]})", raw_def.get(kd))
        elif k in NOTIFICATION_FORM:
            out[c] = FieldName(c, NOTIFICATION_FORM[k], SOURCE_FORM, raw_def.get(kd))
        elif kd in own:
            out[c] = FieldName(c, own[kd], SOURCE_DEF, raw_def.get(kd))
        elif kd in others:
            out[c] = FieldName(c, others[kd], SOURCE_OTHER_DEF, raw_def.get(kd))
        else:
            out[c] = FieldName(c, None, None, raw_def.get(kd))
    return out

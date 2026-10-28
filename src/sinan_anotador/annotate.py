"""Build the annotation plan for a DBF from a .def and apply it: `<field>_rotulo` columns, age in years, dictionary."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .cnv import Cnv, DefFile, DefLine, cnv_from_categories, dbf_pattern_to_regex, def_field, find_cnv, parse_cnv, parse_def
from .lookup import LookupTable, find_lookup_files, load_lookup
from .names import FieldName, load_csv_categories, resolve_names

NO_LABEL = "[{code}] sem rótulo"
CODE_PREFIX_RE = re.compile(r"^\d{2,}\s+(?=\S)")   # "230650 Itapiúna" -> "Itapiúna"; "23 Ceará" -> "Ceará"


def strip_code_prefix(label: str) -> str:
    """Municipality and UF .cnv labels repeat the code in front of the name; the code already sits in the column to the
    left, so the label keeps only the name (user request, 2026-10-25). Applied only to those tables: a general rule would
    turn nudoseMB's "12 doses" into "doses"."""
    return CODE_PREFIX_RE.sub("", label, count=1)


def is_geo_table(table) -> bool:
    name = getattr(table, "name", "") or ""
    return bool(MUNICIPALITY_CNV_RE.match(name) or UF_CNV_RE.match(name))
BLANK_LABEL = "Ign/Branco"
AGE_FIELD = "NU_IDADE_N"
AGE_BAND_CNV = ("FXIDAD10NET.CNV", "FXIDAD13NET.CNV", "FXIDAD9NET.CNV", "FXIDAD5NET.CNV", "FXIDAD2NET.CNV")
MUNICIPALITY_CNV_RE = re.compile(r"^MUNIC([A-Z]{2})\.CNV$", re.IGNORECASE)
MUNICIPALITY_CHAIN = ("MUNICCE.CNV", "MUNICBR.CNV")
UF_CNV_RE = re.compile(r"^UFC?CODIGO?\.CNV$", re.IGNORECASE)      # UFCODIGO.CNV (code/sigla -> name), UFCCODIG.CNV (sigla)      # criterion 5: CE first; BR covers residents of other states

# Tables that regroup a field for tabulation (year/month of a date, UF/region/capital of a municipality code,
# age bands, hospital networks...) rather than listing the field's own categories. Never used for `<field>_rotulo`.
GROUPING_CNV_RE = re.compile(
    r"^(ANOS|MESES|MESESC|TRIME|SEMANAEP|UFCODIGO|UFCCODIG|RMETR.*|NHE.*|CAPITAL|TBPRI181|TBMUNTRM|TBMUNPRI|"
    r"MUNFRONT.*|MUN_INDIG.*|AB|PENITENCIARIO|FXIDAD.*|IDADEDETNET|IDADECOQNET|FXIMAE14|FXRIPSA.*|FXLTANET|"
    r"FXID10MAENET|OCUPANET|COORTE.*|CLUSTERBR|MUNPI.*|REGIAO|UFMSUL.*|COMPDENG.*|ANTIMO.*|MIGRADO)\.CNV$",
    re.IGNORECASE)

# Sinan NET export names (user brief, 2026-10-20) -> .def. Used first; the `A` pattern of each .def is the fallback.
KNOWN_DBF_PREFIXES = {
    "TUBENET": ["TuberculNET5_0", "TuberculNET"],
    "SIFGENET": ["GestSifNET"],
    "SIFICNET": ["SifilisNET"],      # sífilis congênita: nome real do export do Sinan NET (base SIFICNET.DBF, 2026-10-28)
    "SIFCNET": ["SifilisNET"],       # padrão `A` do SifilisNET.def do TabWin (Sifc*.DB?), mantido por compatibilidade
    "HANSNET": ["HansNET"],
    "LEISHNET": ["LeishvisNET"],     # leishmaniose visceral: nome real do export (base LEISHNET.DBF, 2026-10-28)
    "LEIVNET": ["LeishvisNET"],
    "MENINNET": ["MeningeNET"],      # meningite: nome real do export (base MENINNET.DBF, 2026-10-28)
    "LTANET": ["LeishtegNET"],
    "DENGNET": ["DengueNET"],
}


# fields whose .def lists one category table per value of another field: DOSE_RECEB (doses received) is read against
# NUDOSEPB.CNV for paucibacillary (CLASSOPERA 1: "6 doses" is the full scheme) and NUDOSEMB.CNV for multibacillary
# (CLASSOPERA 2: 12 doses); any other classification gets the plain count (NUDOSES.CNV). Codes: Classop.cnv.
TABLE_SWITCH: dict[str, tuple[str, dict[str, str], str]] = {
    "DOSE_RECEB": ("CLASSOPERA", {"1": "NUDOSEPB.CNV", "2": "NUDOSEMB.CNV"}, "NUDOSES.CNV"),
}


@dataclass
class FieldPlan:
    field: str
    cnv: Cnv | LookupTable | None   # table for `<field>_rotulo` (a .cnv, or an external unidanet.dbf-style table)
    start: int                      # 1-based start inside the field
    fallbacks: list[Cnv] = field(default_factory=list)   # tried when the main table has no line for the code
    def_label: str = ""
    switch: tuple[str, dict[str, Cnv]] | None = None     # (DBF column, its code -> table) chosen per record; `cnv` otherwise


@dataclass
class Plan:
    deffile: DefFile
    fields: dict[str, FieldPlan]            # only fields that get a `_rotulo`
    age_field: str | None
    age_band: Cnv | None
    warnings: list[str]
    skipped: list[str]                      # messages about .def lines not usable here
    lookups: dict[str, LookupTable] = field(default_factory=dict)   # external tables actually loaded, by file name
    coverage: dict[str, dict] = field(default_factory=dict)        # per field with an external table: counts filled by apply_plan
    notes: list[str] = field(default_factory=list)                 # decisions worth logging that are not warnings
    missing_cnv: set[str] = field(default_factory=set)             # .cnv files the .def cites and tab_dir lacks


def tab_dir_default(start: Path | None = None) -> Path | None:
    """Locate the TabWin tables: `tabelas/tab_sinannet` in the repository, or `tab_sinannet` next to the app."""
    here = Path(start or __file__).resolve()
    for base in [here, *here.parents]:
        for rel in ("tabelas/tab_sinannet", "tab_sinannet"):
            cand = base / rel
            if cand.is_dir() and any(cand.glob("*.def")):
                return cand
    return None


# ----------------------------------------------------------------------------- choosing the .def
def load_defs(tab_dir: Path) -> list[DefFile]:
    return [parse_def(p) for p in sorted(Path(tab_dir).glob("*.def"))]


def detect_def(dbf_name: str, columns: list[str], tab_dir: Path) -> tuple[DefFile | None, list[str]]:
    """Pick the .def for a DBF: known export names, then the `A` pattern in each .def, then field overlap.
    Among several candidates the largest field overlap with the DBF wins; ties go to the fewer missing .cnv files."""
    notes: list[str] = []
    defs = load_defs(tab_dir)
    by_name = {d.name: d for d in defs}
    stem = Path(dbf_name).stem.upper()
    cols = {def_field(c) for c in columns}

    def rank(cands: list[DefFile]) -> DefFile:
        def key(d: DefFile):
            overlap = len(d.fields & cols)
            missing = len({ln.cnv for ln in d.lines if ln.cnv and find_cnv(ln.cnv, tab_dir) is None})
            return (overlap, -missing, -len(d.fields))
        return max(cands, key=key)

    cands: list[DefFile] = []
    for prefix, names in KNOWN_DBF_PREFIXES.items():
        if stem.startswith(prefix):
            cands = [by_name[n] for n in names if n in by_name]
            if cands:
                chosen = rank(cands)
                notes.append(f"agravo reconhecido pelo nome do arquivo ({stem}): {chosen.name}.def")
                return chosen, notes
    for d in defs:
        rx = dbf_pattern_to_regex(d.dbf_pattern or "")
        if rx and d.dbf_pattern and "*.DB?" != d.dbf_pattern.split("\\")[-1].upper() and rx.match(dbf_name):
            cands.append(d)
    if cands:
        chosen = rank(cands)
        notes.append(f"agravo reconhecido pelo padrão de arquivo do .def ({chosen.dbf_pattern}): {chosen.name}.def"
                     + (f"; outros candidatos: {', '.join(c.name for c in cands if c is not chosen)}" if len(cands) > 1 else ""))
        return chosen, notes
    # fallback by field set: a .def is eligible when at least half of its fields (and at least 5) are in the DBF; among the
    # eligible the largest absolute overlap wins, then the largest share. Ranking by share alone let NotnegatNET.def (5 generic
    # notification fields, all present in any DBF) beat SifilisNET.def (47 of 54 present) on the real SIFICNET.DBF.
    eligible = [d for d in defs if len(d.fields & cols) >= max(5, len(d.fields) // 2)]
    scored = sorted(eligible, key=lambda d: (len(d.fields & cols), len(d.fields & cols) / max(1, len(d.fields))), reverse=True)
    if scored:
        best = scored[0]
        others = [f"{d.name} ({len(d.fields & cols)} de {len(d.fields)})" for d in scored[1:4]]
        notes.append(f"AVISO: o nome do arquivo ({dbf_name}) não foi reconhecido; agravo escolhido pelo conjunto de campos: "
                     f"{best.name}.def ({len(best.fields & cols)} de {len(best.fields)} campos presentes)"
                     + (f"; outros candidatos: {', '.join(others)}" if others else ""))
        return best, notes
    notes.append(f"AVISO: nenhum .def reconhecido para {dbf_name}; nenhum campo será rotulado")
    return None, notes


# ----------------------------------------------------------------------------- building the plan
def build_plan(deffile: DefFile, columns: list[str], field_types: dict[str, str], tab_dir: Path,
               csv_dir: Path | None = None) -> Plan:
    """`csv_dir` (default: `dicionarios` beside the TabWin tables) holds the dictionary CSVs whose `categorias_cnv` stand in
    for .cnv files the .def cites but `tab_dir` lacks."""
    cols = {c.upper(): c for c in columns}
    for c in columns:                       # BACILOSCO in the DBF is BACILOSCOP in the .def: plan it under the .def name
        if def_field(c) not in cols:
            cols[def_field(c)] = c
    cache: dict[str, Cnv | None] = {}
    csv_cats = load_csv_categories(csv_dir if csv_dir is not None else Path(tab_dir).parent / "dicionarios", deffile.name)

    def get_cnv(name: str) -> Cnv | None:
        key = name.upper()
        if key not in cache:
            p = find_cnv(name, tab_dir)
            cache[key] = parse_cnv(p) if p else None
        return cache[key]

    warnings: list[str] = []
    skipped: list[str] = []
    notes: list[str] = []
    missing_cnv: set[str] = set()
    plans: dict[str, FieldPlan] = {}
    lookups: dict[str, LookupTable] = {}          # by file name on disk
    lookup_sets: dict[str, list[LookupTable]] = {}  # by .def table name
    lookups_missing: set[str] = set()
    lookups_empty: set[str] = set()               # files that exist but hold no rows (BAIRRNET.DBF in TAB_SINANNET.zip)

    def tables_for(ln: DefLine) -> list[LookupTable]:
        """Every readable file for the line's table, best first (CSV we built, then TabWin's DBF); [] when none exists."""
        key = ln.lookup_dbf.lower()
        if key in lookups_missing:
            return []
        if key in lookup_sets:
            return lookup_sets[key]
        paths = find_lookup_files(ln.lookup_dbf, tab_dir)
        if not paths:
            lookups_missing.add(key)
            return []
        tables: list[LookupTable] = []
        for p in paths:
            try:
                # the name field in the .def is the column of the lookup file; the code column is named like the DBF field
                t = load_lookup(p, ln.field, ln.name_field or "NOME")
            except ValueError as e:
                if str(e) == "tabela vazia":    # shipped empty: not a broken file, just no table (noted per field below)
                    lookups_empty.add(key)
                    continue
                warnings.append(f"tabela externa {p.name} não pôde ser lida: {e}")
                continue
            except Exception as e:      # a broken table must not abort the run
                warnings.append(f"tabela externa {p.name} não pôde ser lida: {e}")
                continue
            lookups[p.name.lower()] = t
            tables.append(t)
        if not tables:
            lookups_missing.add(key)
        lookup_sets[key] = tables
        return tables

    def lookup_chain(ln: DefLine) -> tuple[LookupTable | None, list[LookupTable]]:
        """The line's own table(s) plus, as fallbacks, the other tables of the .def that carry the same name column:
        UNIDANET (37.694 unidades notificadoras) and UNIDINVEST (55.658) each have codes the other lacks."""
        chain = list(tables_for(ln))
        seen = {ln.lookup_dbf.lower()}
        for other in deffile.lines:
            if other.lookup_dbf and other.name_field == ln.name_field and other.lookup_dbf.lower() not in seen:
                seen.add(other.lookup_dbf.lower())
                chain.extend(t for t in tables_for(other) if t not in chain)
        if not chain:
            return None, []
        return chain[0], chain[1:]
    def external_missing(ln: DefLine) -> str:
        name = ln.lookup_dbf
        if name.lower() in lookups_empty:
            hint = " (o nome do bairro já vem em NM_BAIRRO)" if name.upper().startswith("BAIRR") and "NM_BAIRRO" in cols else ""
            return f"tabela externa {name} vem vazia no pacote do TabWin; sem rótulo{hint}"
        return f"tabela externa {name} não disponível; sem rótulo"

    age_band: Cnv | None = None
    age_field: str | None = AGE_FIELD if AGE_FIELD in cols else None

    by_field: dict[str, list[DefLine]] = {}
    for ln in deffile.lines:
        by_field.setdefault(ln.field, []).append(ln)

    for fld, lines in by_field.items():
        if fld not in cols:
            skipped.append(f"{fld}: no .def mas não no DBF")
            continue
        col = cols[fld]
        ftype = field_types.get(col, "C")
        cnv_lines = [ln for ln in lines if ln.cnv]
        dbf_lines = [ln for ln in lines if ln.lookup_dbf]
        if not cnv_lines:
            if dbf_lines:
                table, more = lookup_chain(dbf_lines[0])
                if table is not None:
                    plans[col] = FieldPlan(col, table, 1, more, def_label=dbf_lines[0].label)
                else:
                    skipped.append(f"{fld}: {external_missing(dbf_lines[0])}")
            else:
                skipped.append(f"{fld}: soma no .def; sem rótulo")
            continue
        if fld == AGE_FIELD:
            for name in AGE_BAND_CNV:
                if any(ln.cnv.upper() == name for ln in cnv_lines):
                    age_band = get_cnv(name)
                    if age_band:
                        break
            if age_band is None:
                warnings.append(f"{fld}: nenhuma tabela de faixa etária disponível; só a idade em anos")
            continue
        if ftype == "D":
            skipped.append(f"{fld}: campo de data; as tabelas do .def (ano/mês/trimestre) são agrupamentos; sai como data")
            continue
        # municipality codes: CE then BR (criterion 5), other tables of the field are groupings
        muni = [ln for ln in cnv_lines if MUNICIPALITY_CNV_RE.match(ln.cnv)]
        if muni:
            chain = [get_cnv(n) for n in MUNICIPALITY_CHAIN]
            chain = [c for c in chain if c]
            if chain:
                plans[col] = FieldPlan(col, chain[0], 1, chain[1:], def_label=muni[0].label)
            else:
                warnings.append(f"{fld}: tabelas de município não encontradas em {tab_dir}")
            continue
        usable = []
        missing = []
        for ln in cnv_lines:
            if GROUPING_CNV_RE.match(ln.cnv) and not (UF_CNV_RE.match(ln.cnv) and ftype == "C"):
                # UF tables regroup municipality codes, but on a UF field itself (SG_UF, UF_TRANSF) they ARE the categories
                continue
            c = get_cnv(ln.cnv)
            if c is None:
                missing.append(ln.cnv)
            else:
                usable.append((ln, c))
        if not usable:
            if dbf_lines:
                table, more = lookup_chain(dbf_lines[0])
                if table is not None:
                    plans[col] = FieldPlan(col, table, 1, more, def_label=dbf_lines[0].label)
                    continue
                skipped.append(f"{fld}: {external_missing(dbf_lines[0])}")
            elif missing:
                missing_cnv.update(missing)
                if fld in csv_cats:
                    # the dictionary CSV copied the categories from the .cnv when it was extracted: rebuild the table
                    cats, csv_name = csv_cats[fld]
                    c = cnv_from_categories(f"{sorted(set(missing))[0]} (reconstruída de {csv_name})", cats)
                    plans[col] = FieldPlan(col, c, cnv_lines[0].start or 1, [], def_label=cnv_lines[0].label)
                    notes.append(f"{fld}: tabela {', '.join(sorted(set(missing)))} ausente em tab_sinannet; categorias tomadas de "
                                 f"{csv_name} ({'; '.join(f'{k}={v}' for k, v in cats)})")
                else:
                    warnings.append(f"{fld}: tabela {', '.join(sorted(set(missing)))} citada no .def não está disponível; sem rótulo")
            else:
                skipped.append(f"{fld}: só agrupamentos no .def; sem rótulo")
            continue
        distinct = {c.name.upper() for _, c in usable}
        ln, c = usable[0]
        if distinct <= {"UFCODIGO.CNV", "UFCCODIG.CNV"} and len(distinct) > 1:
            # the same UF list, by code+name and by acronym: use the one with names, no warning
            ln, c = next((ln, c) for ln, c in usable if c.name.upper() == "UFCODIGO.CNV")
            distinct = {c.name.upper()}
        if len(distinct) > 1 and fld in TABLE_SWITCH:
            sw_field, by_code, default = TABLE_SWITCH[fld]
            tables = {code: next((cv for _, cv in usable if cv.name.upper() == name), None) for code, name in by_code.items()}
            dflt = next((cv for _, cv in usable if cv.name.upper() == default), None)
            if sw_field in cols and dflt is not None and all(tables.values()):
                plans[col] = FieldPlan(col, dflt, ln.start or 1, [], def_label=ln.label, switch=(cols[sw_field], tables))
                notes.append(f"{fld}: tabela escolhida por {sw_field} em cada registro ("
                             + ", ".join(f"{code} → {t.name}" for code, t in tables.items()) + f"; demais → {dflt.name})")
                continue
        if len(distinct) > 1:
            warnings.append(f"{fld}: mais de uma tabela de categorias no .def ({', '.join(sorted(distinct))}); usada {c.name}")
        plans[col] = FieldPlan(col, c, ln.start or 1, [], def_label=ln.label)
    return Plan(deffile, plans, age_field, age_band, warnings, skipped, lookups, notes=notes, missing_cnv=missing_cnv)


# ----------------------------------------------------------------------------- applying
def code_of(v) -> str:
    """The code as a string: ints without decimals, None/NaN -> ''."""
    if v is None:
        return ""
    if isinstance(v, float):
        if v != v:   # NaN
            return ""
        return str(int(v)) if v.is_integer() else str(v)
    if isinstance(v, bool):
        return "T" if v else "F"
    return str(v).strip()


def label_for(code: str, plan: FieldPlan) -> str:
    cut = code
    if plan.cnv is not None and plan.cnv.width:
        w = plan.cnv.width
        if plan.start > 1:
            cut = code[plan.start - 1: plan.start - 1 + w]
        elif w and len(code) > w:
            cut = code[:w]
    if cut == "":
        lab = plan.cnv.lookup("") if plan.cnv else None
        return lab if lab is not None else BLANK_LABEL
    for table in [plan.cnv, *plan.fallbacks]:
        if table is None:
            continue
        lab = table.lookup(cut)
        if lab is not None:
            return strip_code_prefix(lab) if is_geo_table(table) else lab
    return NO_LABEL.format(code=code)


def age_years(v) -> int | None:
    """NU_IDADE_N: 4xxx years, 3xxx months, 2xxx days, 1xxx hours (Sinan NET; matches FXIDAD*.CNV ranges)."""
    code = code_of(v)
    if not code.isdigit():
        return None
    n = int(code)
    if 4000 <= n <= 4999:
        return n - 4000
    if 1000 <= n <= 3999:
        return 0
    return None


def lookup_coverage(codes: pd.Series, fp: FieldPlan) -> dict:
    """How an external-table field was labelled: records and distinct codes, by table of the chain and without label.
    This is the measure that decides whether a lookup table needs refreshing (e.g. unidanet from the public CNES)."""
    counts = codes.value_counts()
    tables = [fp.cnv, *[fb for fb in fp.fallbacks if isinstance(fb, LookupTable)]]
    by_table = {t.name: [0, 0] for t in tables}          # records, distinct codes
    missing = [0, 0]
    filled = 0
    for code, n in counts.items():
        if code == "":
            continue
        filled += n
        for t in tables:
            if t.lookup(code) is not None:
                by_table[t.name][0] += n
                by_table[t.name][1] += 1
                break
        else:
            missing[0] += n
            missing[1] += 1
    return {"filled": int(filled), "by_table": {k: tuple(v) for k, v in by_table.items()}, "missing": tuple(missing)}


def apply_plan(df: pd.DataFrame, plan: Plan) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (annotated df with `<field>_rotulo` right after each field, dictionary df)."""
    out_cols: dict[str, pd.Series] = {}
    dict_rows: list[dict] = []
    seen_cnv: set[str] = set()

    def add_dict(fieldname: str, cnv, role: str, used_codes=None):
        if isinstance(cnv, LookupTable):
            for code in sorted(c for c in (used_codes or []) if c):
                lab = cnv.lookup(code)
                if lab is not None:
                    dict_rows.append({"campo": fieldname, "tabela": cnv.name, "codigos": code, "rotulo": lab,
                                      "uso": "tabela externa (códigos presentes na base)"})
            return
        geo = is_geo_table(cnv)
        for codes, label in cnv.categories:
            dict_rows.append({"campo": fieldname, "tabela": cnv.name, "codigos": codes,
                              "rotulo": strip_code_prefix(label) if geo else label, "uso": role})

    for col in df.columns:
        out_cols[col] = df[col]
        if col == plan.age_field:
            codes = df[col].map(code_of)
            out_cols[f"{col}_anos"] = codes.map(lambda c: age_years(c)).astype("Int64")
            if plan.age_band is not None:
                fp = FieldPlan(col, plan.age_band, 1)
                uniq = {c: label_for(c, fp) for c in codes.unique()}
                out_cols[f"{col}_rotulo"] = codes.map(uniq)
                add_dict(col, plan.age_band, "faixa etária")
            continue
        fp = plan.fields.get(col)
        if fp is None:
            continue
        codes = df[col].map(code_of)
        if fp.switch is not None and fp.switch[0] in df.columns:
            sw_col, tables = fp.switch
            sw = df[sw_col].map(code_of)
            plans_by = {k: FieldPlan(col, t, fp.start) for k, t in tables.items()}
            pair_cache: dict[tuple[str, str], str] = {}
            labels = []
            for c, k in zip(codes, sw):
                key = (c, k)
                if key not in pair_cache:
                    pair_cache[key] = label_for(c, plans_by.get(k, fp))
                labels.append(pair_cache[key])
            out_cols[f"{col}_rotulo"] = pd.Series(labels, index=df.index)
            for k, t in tables.items():
                add_dict(col, t, f"rótulo ({sw_col} = {k})")
            add_dict(col, fp.cnv, f"rótulo ({sw_col} com outro valor)")
            continue
        uniq = {c: label_for(c, fp) for c in codes.unique()}
        out_cols[f"{col}_rotulo"] = codes.map(uniq)
        add_dict(col, fp.cnv, "rótulo", uniq.keys())
        if isinstance(fp.cnv, LookupTable):
            plan.coverage[col] = lookup_coverage(codes, fp)
        for fb in fp.fallbacks:
            if isinstance(fb, LookupTable):
                add_dict(col, fb, "rótulo", [c for c in uniq if fp.cnv.lookup(c) is None])
                continue
            if fb.name not in seen_cnv:
                add_dict("(complemento para códigos fora da tabela principal)", fb, "rótulo (complemento)")
                seen_cnv.add(fb.name)
    annotated = pd.DataFrame(out_cols)
    dictionary = pd.DataFrame(dict_rows, columns=["campo", "tabela", "codigos", "rotulo", "uso"])
    return annotated, dictionary


def field_table(annotated_columns: list[str], raw_columns: list[str], field_types: dict[str, str], plan: Plan | None,
                names: dict[str, FieldName]) -> tuple[dict[str, str], pd.DataFrame]:
    """Headers "Nome por extenso (CAMPO)" for the `dados` sheet and the `campos` sheet (one row per column)."""
    headers: dict[str, str] = {}
    rows: list[dict] = []
    for col in annotated_columns:
        base, suffix = col, ""
        for suf in ("_rotulo", "_anos"):
            if col.endswith(suf) and col[: -len(suf)] in raw_columns:
                base, suffix = col[: -len(suf)], suf
                break
        fn = names.get(base, FieldName(base, None, None))
        headers[col] = (f"Faixa etária ({col})" if plan is not None and suffix == "_rotulo" and base == plan.age_field
                        else fn.header(suffix))
        table = None
        if plan is not None:
            if suffix == "_rotulo":
                table = plan.age_band.name if base == plan.age_field and plan.age_band else (
                    plan.fields[base].cnv.name if base in plan.fields else None)
        rows.append({"coluna": col, "nome_por_extenso": headers[col], "campo_dbf": base, "tipo_dbf": field_types.get(base, ""),
                     "fonte_do_nome": (fn.source or "") if suffix == "" else ("derivado" if fn.source else ""),
                     "rotulo_tabwin": fn.def_label or "", "tabela_de_rotulos": table or ""})
    return headers, pd.DataFrame(rows, columns=["coluna", "nome_por_extenso", "campo_dbf", "tipo_dbf", "fonte_do_nome",
                                                 "rotulo_tabwin", "tabela_de_rotulos"])

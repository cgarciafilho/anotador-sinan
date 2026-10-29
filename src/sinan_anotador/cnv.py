r"""Parsers for TabWin `.def` (per-disease tabulation definitions) and `.cnv` (code -> label tables).

Ported from the .cnv/.def parser of the previous analysis project, without its dependencies.

File formats (observed in tabelas/tab_sinannet/, latin-1):

.cnv
    ; comment lines
    <n_categories> <width> [L|l]          header: number of category lines, code width, optional alignment
    <seq>  <label>            <codes>     one line per category; codes separated by commas; `a-b` is a numeric
                                          range; an empty token (leading comma) means "blank value".
    TabWin fills a code -> category array line by line, so when a code appears in more than one line the
    LAST line wins (e.g. Anos.cnv: `IGN 0000-9999` first, then `1991 1991`, ...).

.def
    A<dbf file pattern>                    e.g. Ac:\SinanNet\BaseDBF\TUBE*.DB?
    <T><label>, <DBF_FIELD>, <start>, <file.CNV>
                                           T is one letter (X, L, C, S, T, D, x, s, ...): how TabWin offers the
                                           variable; irrelevant here. `start` is the 1-based position inside the
                                           field where the code begins (5 = month inside a YYYYMMDD date); the
                                           code length is the .cnv width.
    <T><label>, <DBF_FIELD>, <NAME_FIELD>, <lookup.dbf>
                                           lookup in an external DBF (ocupações, unidades): not available here.
    I<label>, <DBF_FIELD>                  numeric field to sum: no categories.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


# DBF column -> field name in the TabWin .def, where the two differ (HANSNET exports BACILOSCO, HansNET.def says BACILOSCOP;
# LTANET exports DT_DESC3, LeishtegNET.def says DT_DES3; bases reais, 2026-10-28)
DBF_FIELD_ALIASES = {"BACILOSCO": "BACILOSCOP", "DT_DESC3": "DT_DES3"}


def def_field(column: str) -> str:
    """The .def field name for a DBF column (the column itself unless it has an alias)."""
    return DBF_FIELD_ALIASES.get(column.upper(), column.upper())


def read_latin1(path: Path) -> list[str]:
    return Path(path).read_text(encoding="latin-1").splitlines()


# ----------------------------------------------------------------------------- .cnv
@dataclass(frozen=True)
class CnvRule:
    """One code token of one category line."""
    order: int          # category line index (0-based); larger wins on overlap
    label: str
    code: str           # exact token as written (stripped), '' for blank
    lo: int | None      # numeric range, when the token is `a-b` or all digits
    hi: int | None


@dataclass
class Cnv:
    name: str
    path: Path
    width: int
    categories: list[tuple[str, str]] = field(default_factory=list)   # (codes as written, label), file order
    rules: list[CnvRule] = field(default_factory=list)
    _exact: dict[str, CnvRule] = field(default_factory=dict, repr=False)
    _numeric: dict[int, CnvRule] = field(default_factory=dict, repr=False)
    _ranges: list[CnvRule] = field(default_factory=list, repr=False)
    _blank: CnvRule | None = None

    @property
    def blank_label(self) -> str | None:
        return self._blank.label if self._blank else None

    def lookup(self, code: str) -> str | None:
        """Label for a code already cut to the .cnv width and stripped; None when no line matches."""
        if code == "":
            return self._blank.label if self._blank else None
        best: CnvRule | None = self._exact.get(code)
        if code.isdigit():
            n = int(code)
            r = self._numeric.get(n)
            if r is not None and (best is None or r.order > best.order):
                best = r
            for r in self._ranges:
                if r.lo <= n <= r.hi and (best is None or r.order > best.order):
                    best = r
        return best.label if best else None


# "N largura [L]"; sete tabelas de região de saúde do TAB_SINANNET (rj_regsaudn.cnv…) trazem um token a mais
# ("10  6   33X001"), que o TabWin ignora e aqui também é ignorado.
RE_HEADER = re.compile(r"^\s*(\d+)\s+(\d+)(?:\s+([A-Za-z]))?(?:\s+\S.*)?\s*$")
RE_LINE = re.compile(r"^\s*(\d+)\s+(.*)$")


def parse_cnv(path: Path) -> Cnv:
    path = Path(path)
    cnv = Cnv(name=path.name, path=path, width=0)
    header_seen = False
    order = 0
    for raw in read_latin1(path):
        line = raw.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith(";"):
            continue
        if not header_seen:
            m = RE_HEADER.match(line)
            if not m:
                # stray comment with another marker (Modoentr.cnv has `: Revisado...`): skip until the header
                continue
            cnv.width = int(m.group(2))
            header_seen = True
            continue
        m = RE_LINE.match(line)
        if not m:
            continue
        label, raw_codes = split_category_line(line, m)
        add_category(cnv, order, label, raw_codes)
        order += 1
    if not header_seen:
        raise ValueError(f"{path.name}: arquivo vazio ou sem cabeçalho")
    return cnv


def add_category(cnv: Cnv, order: int, label: str, raw_codes: str) -> None:
    """Append one category line (label + comma-separated code tokens, as written in a .cnv) to `cnv`."""
    cnv.categories.append((raw_codes.strip(), label))
    tokens = [t.strip() for t in raw_codes.split(",")]
    if len(tokens) > 1 and tokens[-1] == "" and any(tokens[:-1]):
        tokens = tokens[:-1]        # trailing comma (`06, 6,6 ,` in nudosePB.cnv) is not a blank category
    for tok in tokens:
        if tok == "":
            rule = CnvRule(order, label, "", None, None)
            cnv._blank = rule
            cnv.rules.append(rule)
            continue
        if re.fullmatch(r"\d+-\d+", tok):
            a, b = tok.split("-")
            rule = CnvRule(order, label, tok, int(a), int(b))
            cnv._ranges.append(rule)
        elif tok.isdigit():
            rule = CnvRule(order, label, tok, int(tok), int(tok))
            cnv._numeric[int(tok)] = rule
            cnv._exact[tok] = rule
        else:
            rule = CnvRule(order, label, tok, None, None)
            cnv._exact[tok] = rule
        cnv.rules.append(rule)


def cnv_from_categories(name: str, categories: list[tuple[str, str]], path: Path | None = None) -> Cnv:
    """A Cnv built in memory from (codes, label) pairs written like .cnv code lists ("0-9", "1", "01-05,1-5"); the width
    is the longest numeric token. Used when a .cnv the .def cites is missing but a dictionary CSV lists the categories."""
    cnv = Cnv(name=name, path=path or Path(name), width=0)
    width = 0
    for order, (codes, label) in enumerate(categories):
        add_category(cnv, order, label, codes)
        for tok in re.split(r"[,\-]", codes):
            tok = tok.strip()
            if tok:
                width = max(width, len(tok))
    cnv.width = width
    return cnv


CODES_CHARS = re.compile(r"^[A-Za-z0-9_,\- \t]*$")


def split_category_line(line: str, m: re.Match) -> tuple[str, str]:
    """(label, codes as written) for a category line.

    TabWin writes fixed columns: sequence number right-aligned in columns 1-9, label in columns 10-59, code list from
    column 60. That layout is used when the line fits it (every file but the NHE* hospital lists); otherwise the line is
    split on the last run of two or more spaces, which is what the inherited parser did.
    """
    line = line.replace("\t", " ")
    if len(line) >= 60 and line[:9].strip().isdigit() and CODES_CHARS.match(line[59:]):
        return " ".join(line[9:59].split()), line[59:].strip()
    rest = m.group(2)
    parts = re.split(r"\s{2,}", rest.strip())
    if len(parts) == 1:
        return parts[0], ""
    codes = parts[-1]
    label = " ".join(" ".join(parts[:-1]).split())
    head = rest.strip()[: -len(codes)].rstrip()
    if head.endswith(","):          # `Em Branco   ,` : blank token glued to the label side
        codes = "," + codes
        label = " ".join(head[:-1].split())
    return label, codes


def find_cnv(name: str, tab_dir: Path) -> Path | None:
    """Case- and Unicode-normalization-insensitive lookup of a .cnv file (names in .def do not match disk case)."""
    target = unicodedata.normalize("NFC", name).lower()
    for p in Path(tab_dir).iterdir():
        if unicodedata.normalize("NFC", p.name).lower() == target:
            return p
    return None


# ----------------------------------------------------------------------------- .def
@dataclass(frozen=True)
class DefLine:
    kind: str          # the leading letter
    label: str
    field: str         # DBF field, upper case
    start: int | None  # 1-based start position (None for external-dbf lookups / sums)
    cnv: str | None    # .cnv file name as written (None when the line uses an external .dbf or has no table)
    lookup_dbf: str | None
    raw: str
    name_field: str | None = None   # column of the external .dbf that holds the name (NM_UNIDADE)


@dataclass
class DefFile:
    name: str
    path: Path
    dbf_pattern: str | None
    lines: list[DefLine]

    @property
    def fields(self) -> set[str]:
        return {ln.field for ln in self.lines}


RE_DEF_CNV = re.compile(
    r"^([A-Za-z])\s*([^,]*?)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\d+)\s*,\s*(\S+?\.cnv)\s*$", re.IGNORECASE)
RE_DEF_DBF = re.compile(
    r"^([A-Za-z])\s*([^,]*?)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\S+?\.dbf)\s*$",
    re.IGNORECASE)
RE_DEF_SUM = re.compile(r"^([A-Za-z])\s*([^,]*?)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")


def def_files(tab_dir: Path) -> list[Path]:
    """Os .def da pasta, qualquer caixa na extensão (o TAB_SINANNET traz AnimaispNET.DEF e PlanSurtoNet.DEF)."""
    return sorted((p for p in Path(tab_dir).iterdir() if p.suffix.lower() == ".def"), key=lambda p: p.name.lower())


def parse_def(path: Path) -> DefFile:
    path = Path(path)
    pattern = None
    lines: list[DefLine] = []
    for raw in read_latin1(path):
        s = raw.strip()
        if not s or s.startswith(";"):
            continue
        if s[0] in "Aa" and ("\\" in s or "*" in s or s.lower().endswith((".dbf", ".db?"))) and "," not in s:
            pattern = s[1:].strip()
            continue
        m = RE_DEF_CNV.match(s)
        if m:
            lines.append(DefLine(m.group(1), m.group(2).strip(), m.group(3).upper(), int(m.group(4)),
                                 m.group(5), None, raw.rstrip()))
            continue
        m = RE_DEF_DBF.match(s)
        if m:
            lines.append(DefLine(m.group(1), m.group(2).strip(), m.group(3).upper(), None, None, m.group(5),
                                 raw.rstrip(), m.group(4).upper()))
            continue
        m = RE_DEF_SUM.match(s)
        if m and m.group(1) in "Ii":
            lines.append(DefLine(m.group(1), m.group(2).strip(), m.group(3).upper(), None, None, None, raw.rstrip()))
            continue
        # separators (`____ FIM DO NOTINDIV ____`), stray titles: ignored
    return DefFile(name=path.stem, path=path, dbf_pattern=pattern, lines=lines)


def dbf_pattern_to_regex(pattern: str) -> re.Pattern | None:
    """`c:\\SinanNet\\BaseDBF\\TUBE*.DB?` -> regex on the bare file name, case-insensitive."""
    if not pattern:
        return None
    base = re.split(r"[\\/]", pattern.strip())[-1]
    if not base:
        return None
    rx = "".join(".*" if ch == "*" else "." if ch == "?" else re.escape(ch) for ch in base)
    return re.compile("^" + rx + "$", re.IGNORECASE)

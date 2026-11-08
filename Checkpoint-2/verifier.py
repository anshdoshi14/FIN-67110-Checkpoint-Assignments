"""Independent Checkpoint 2 verifier. Reads only report + saved filing texts/facts.

A claim must have a structured citation in the report's evidence-registry block.
No role prompts, manager outputs, or outside market data are read here.
"""
from __future__ import annotations
import ast
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
from typing import Any

START = '```evidence-json\n'
END = '\n```'
AMOUNTS = re.compile(r'\$\s*[\d,]+(?:\.\d+)?|(?<![\w.])\d[\d,]*(?:\.\d+)?\s*%')


def numeric(s: Any) -> Decimal:
    return Decimal(str(s).replace(',', '').replace('$', '').replace('%', '').strip())


def lines(folder: Path) -> dict[str, list[str]]:
    names = ['10-K', '10-Q', 'earnings_8-K', 'release_EX-99.1']
    return {name: (folder / f'{name}.txt').read_text(encoding='utf-8').splitlines()
            for name in names if (folder / f'{name}.txt').exists()}


def norm(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[|$]', ' ', s)).strip().lower()


def _digits(value: Any) -> str:
    """Digits only, so 9.226 (billions), 9,226 (millions) and '$9,226' compare equal."""
    return re.sub(r'\D', '', str(value))


def number_in_line(value: Any, line: str) -> bool:
    """Lab 04 rule: a line-sourced number is supported when that number appears in the
    saved filing line, allowing for spacing and formatting ($, commas, %, scale words).
    Compares whole numeric tokens, not substrings, so 11 does not match 2011."""
    want = _digits(value)
    if not want:
        return False
    tokens = re.findall(r'\d[\d,]*(?:\.\d+)?', line)
    return any(_digits(t) == want for t in tokens)


def registry(report: str) -> list[dict]:
    m = re.search(re.escape(START) + r'(.*?)' + re.escape(END), report, re.S)
    if not m:
        return []
    d = json.loads(m.group(1))
    if not isinstance(d, list):
        raise ValueError('evidence-json must be an array of numeric claim objects')
    return d


def _get_facts(facts: dict, src: dict) -> dict | None:
    """Resolve a cited fact without trusting an analyst-provided alias.

    The saved fact file uses friendly field names (for example ``revenue``) and
    ``current``/``prior`` buckets.  A model may instead cite the SEC tag and the
    actual period-end date.  Both are valid representations only when every
    identifying source attribute still agrees with the saved fact.
    """
    fields = facts.get('fields', {})
    requested_field = src.get('field', '')
    requested_period = str(src.get('period', ''))
    candidates: list[tuple[str, str, dict]] = []

    # Keep the original exact friendly-name path fast and deterministic.
    if requested_field in fields and requested_period in fields[requested_field]:
        item = fields[requested_field][requested_period]
        candidates.append((requested_field, requested_period, item))

    # Also allow the SEC tag plus the actual saved period-end date.  Do not
    # accept a tag alone: period, end date, and accession must all identify the
    # same saved fact below.
    for field_name, periods in fields.items():
        for period_name, item in periods.items():
            if (requested_field == item.get('tag') and
                    requested_period in (period_name, str(item.get('end', '')), str(item.get('frame', '')))):
                candidates.append((field_name, period_name, item))

    for field_name, period_name, item in candidates:
        if (src.get('tag') != item.get('tag') or
                src.get('end') != item.get('end') or
                src.get('accession') != item.get('accession')):
            continue
        # A friendly alias must name the saved field; an SEC tag must be the
        # tag on that same fact.  This prevents a mismatched source label from
        # becoming valid merely because another fact shares an end date.
        if requested_field not in (field_name, item.get('tag')):
            continue
        if requested_period not in (period_name, str(item.get('end', '')), str(item.get('frame', ''))):
            continue
        return item
    return None


def _document_name(document: Any) -> str:
    """Map accepted citation spellings to the immutable saved-file label."""
    text = str(document).strip()
    aliases = {
        'EX-99.1': 'release_EX-99.1',
        'EX99.1': 'release_EX-99.1',
        'EARNINGS RELEASE': 'release_EX-99.1',
        'RELEASE': 'release_EX-99.1',
    }
    return aliases.get(text.upper(), text)


def _line_evidence(src: dict, source_texts: dict) -> tuple[str | None, str]:
    document = src.get('document', '')
    n = src.get('line')
    saved_document = _document_name(document)
    file_lines = source_texts.get(saved_document)
    if file_lines is None or not isinstance(n, int) or not (1 <= n <= len(file_lines)):
        return None, f'No saved {saved_document} line {n}'
    actual = file_lines[n-1]
    supplied = src.get('quote', '')
    if not supplied or norm(supplied) not in norm(actual):
        return actual, 'Claimed source quotation does not match the saved filing line'
    return actual, ''


def _expr(expr: str, inputs: dict[str, Decimal]) -> Decimal:
    """Arithmetic only; no eval, calls, powers, variables outside quoted inputs."""
    def walk(node):
        if isinstance(node, ast.Expression): return walk(node.body)
        if isinstance(node, ast.Name) and node.id in inputs: return inputs[node.id]
        if isinstance(node, ast.Constant) and type(node.value) in (int, float): return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -walk(node.operand)
        if isinstance(node, ast.BinOp):
            a, b = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add): return a+b
            if isinstance(node.op, ast.Sub): return a-b
            if isinstance(node.op, ast.Mult): return a*b
            if isinstance(node.op, ast.Div): return a/b
        raise ValueError('Unsupported ratio arithmetic')
    return walk(ast.parse(expr, mode='eval'))


def _semantics(api_key: str, item: dict, text: str, model: str) -> tuple[bool | None, str]:
    if not api_key:
        return None, 'Model semantic review unavailable: set API_KEY in .env locally'
    from openai import OpenAI
    api = OpenAI(api_key=api_key)
    try:
        r = api.responses.create(model=model,
            instructions=("You are an independent filing-line verifier. Decide whether the provided "
                          "line supports the claimed numeric value for the claimed period and definition. "
                          "Return JSON only: {\"supported\":true/false,\"reason\":\"...\"}. "
                          "Do not use outside knowledge. Do not assume a value in a different column matches."),
            input=json.dumps({'claim': item, 'filing_line': text}))
        result = json.loads(r.output_text)
        return result['supported'] is True, str(result.get('reason', ''))
    except Exception as e:
        return None, f'Model semantic review failed: {type(e).__name__}: {e}'


def check_claim(item: dict, facts: dict, texts: dict, key: str = '', model: str = 'gpt-4.1-mini') -> dict:
    cid = item.get('id', 'missing-id')
    out = {'id': cid, 'claim': item.get('label', cid), 'reported': item.get('value'),
           'status': 'unsupported', 'corrected': None, 'evidence': '', 'reason': ''}
    src = item.get('source')
    if src is None:
        src = {}
    if not isinstance(src, dict):
        out['reason'] = 'Structured source must be an object, not a list or scalar'
        return out
    kind = src.get('kind')
    try:
        try:
            reported = numeric(item['value'])
        except (InvalidOperation, KeyError, TypeError):
            out['reason'] = 'Claim value is not a single number (a table, range or dash cannot be verified as one figure)'
            return out
        if kind == 'xbrl':
            fact = _get_facts(facts, src)
            if not fact:
                out['reason'] = 'Source tag/period/accession not found in saved facts'
                return out
            truth = numeric(fact['value'])
            scale = numeric(item.get('scale', '1'))
            truth /= scale
            out['corrected'] = str(truth)
            out['evidence'] = f"10-K {fact['accession']}, {fact['tag']}, {fact['end']}: {fact['value']} {fact['unit']}"
            if 'line' in src:
                actual, error = _line_evidence(src, texts)
                if actual is not None:
                    out['evidence'] += f"; {src.get('document','10-K')} L{src['line']}: {actual.strip()}"
                if error and actual is not None and number_in_line(reported, actual):
                    # The quotation was paraphrased or reformatted, but the number itself is
                    # on the cited line: not a wrong number. Fall through to the code and
                    # model checks below and record the formatting mismatch only.
                    out['reason'] = 'Quotation differs from the saved line in wording/formatting; the number is present on that line'
                    error = ''
                if error:
                    out['reason'] = error
                    out['status'] = 'wrong' if reported != truth else 'unsupported'
                    return out
                if actual:
                    supported, reason = _semantics(key, item, actual, model)
                    if supported is False:
                        out['status'] = 'wrong'; out['reason'] = reason; return out
                    if supported is None:
                        # A matching exact XBRL fact can be confirmed in code. The
                        # semantic line review remains explicitly pending.
                        out['reason'] = reason
            out['status'] = 'correct' if reported == truth else 'wrong'
            if out['status'] == 'wrong': out['reason'] = f'XBRL fact is {truth}, not {reported}'
            return out
        if kind == 'ratio':
            formula = src.get('formula', '')
            definition = src.get('definition', '')
            if not formula or not definition:
                out['reason'] = 'Ratio has no formula or definition (e.g. average versus closing equity)'
                return out
            inputs = {}
            for name, operand in src.get('inputs', {}).items():
                # Never trust a quoted input without independently checking source.
                detail = operand.get('source') or {}
                if detail.get('kind') != 'xbrl':
                    out['reason'] = f'Input {name} missing verifiable XBRL source'; return out
                f = _get_facts(facts, detail)
                if not f or numeric(operand.get('value', 'NaN')) != numeric(f['value']):
                    out['reason'] = f'Input {name} does not match its cited fact'; return out
                inputs[name] = numeric(operand['value'])
            true = _expr(formula, inputs)
            decimals = int(item.get('round_decimals', 2))
            if decimals < 0 or decimals > 8: raise ValueError('Invalid rounding precision')
            rounded = true.quantize(Decimal(1).scaleb(-decimals))
            # Ratios are sometimes stored as fractions (0.1014) but displayed
            # as percentages (10.14%).  Preserve the report's representation
            # in a correction while still comparing raw values below.
            corrected_display = rounded
            if '%' in str(item.get('display', '')) and abs(true) <= Decimal('1'):
                corrected_display = (true * Decimal('100')).quantize(Decimal(1).scaleb(-decimals))
            out['corrected'] = str(corrected_display)
            out['evidence'] = f"{formula} = {true}; definition: {definition}; sourced inputs: " + ', '.join(
                f'{n}={v}' for n,v in inputs.items())
            out['status'] = 'correct' if abs(reported - true) <= Decimal('0.5') * Decimal(1).scaleb(-decimals) else 'wrong'
            if out['status'] == 'wrong': out['reason'] = f'Recompute from cited inputs gives {corrected_display}'
            return out
        if kind == 'line':
            actual, error = _line_evidence(src, texts)
            if error and actual is not None and number_in_line(reported, actual):
                # Paraphrased quote, but the number is on the cited line (Lab 04: "allowing
                # for spacing and formatting"). Let the model decide period/definition.
                error = ''
            if error:
                # Either the line does not exist (unsupported) or the cited line does not
                # contain the number at all (wrong).
                out['reason'] = error if actual is None else 'Cited filing line does not contain the reported number'
                out['status'] = 'wrong' if actual else 'unsupported'
                if actual: out['evidence'] = f"{src.get('document')} L{src.get('line')}: {actual}"
                return out
            if not src.get('period') or not src.get('definition'):
                out['reason'] = 'Filing-line claim lacks period or numeric definition'; return out
            out['evidence'] = f"{src['document']} L{src['line']}: {actual}"
            supported, reason = _semantics(key, item, actual, model)
            out['status'] = 'correct' if supported is True else ('wrong' if supported is False else 'unsupported')
            out['reason'] = reason
            return out
        out['reason'] = 'No XBRL tag/period, filing line, or defined ratio source'
        return out
    except (KeyError, ValueError, SyntaxError, ArithmeticError, TypeError, InvalidOperation) as e:
        out['reason'] = f'Unverifiable source or arithmetic: {e}'
        return out


def _missed_amounts(report: str, claims: list[dict]) -> list[dict]:
    """Find unregistered $/percent assertions in the body. This is deliberately conservative.

    Years and citation IDs are not numeric claims. Other plain numbers still need
    human examination, so we cannot certify arbitrary prose exhaustive.
    """
    body = report.split('## Numeric evidence registry')[0]
    found = []
    within_investment = False
    for line_number, line in enumerate(body.splitlines()[1:], 2):
        if line.startswith('## Investment Recommendation'):
            within_investment = True
        elif line.startswith('## ') and within_investment:
            within_investment = False
        if within_investment and not line.lstrip().startswith('Insight:'):
            continue
        if line.startswith(('## ', 'Filings:', '|', '# ', 'Run UTC:', '**', 'Source:')):
            continue
        for match in AMOUNTS.finditer(line):
            ids = re.findall(r'\[C:([\w-]+)\]', line)
            candidates = [c for c in claims if c.get('id') in ids]
            seen_values = set()
            for c in candidates:
                v = c.get('display', str(c.get('value', '')))
                # Displays commonly include explanatory units after the number
                # (for example "$303.154 billion").  Compare each asserted
                # dollar/percent token, not the whole prose display.
                seen_values.update(re.sub(r'\s+', '', x) for x in AMOUNTS.findall(str(v)))
            if not candidates or re.sub(r'\s+', '', match.group()) not in seen_values:
                found.append({'id': f'unregistered-L{line_number}-{match.start()}',
                              'claim': f'Unregistered numeric statement L{line_number}',
                              'reported': match.group(), 'status': 'unsupported',
                              'corrected': None, 'evidence': '',
                              'reason': 'No matching [C:id] source registry entry in this report line'})
    return found


def run_verifier(folder: Path, key: str = '', model: str = 'gpt-4.1-mini') -> Path:
    folder = Path(folder)
    print('NODE — Verifier', flush=True)
    source = folder / 'report.md'
    if not source.is_file():
        raise FileNotFoundError(f'Missing report.md in saved run: {folder}')
    original = source.read_text(encoding='utf-8')
    if not original.startswith('Filings:'):
        raise ValueError('First line must remain the filings line')
    facts = json.loads((folder / 'facts.json').read_text(encoding='utf-8'))
    texts = lines(folder)
    claims = registry(original)
    if not claims:
        raise ValueError('Report has no machine-readable evidence-json registry; cannot certify numbers')
    marks = [check_claim(c, facts, texts, key, model) for c in claims]
    marks += _missed_amounts(original, claims)
    marks.insert(0, {'id':'registry-size', 'claim':'Registry coverage', 'reported': len(claims),
                     'status':'correct' if claims else 'unsupported', 'corrected': None,
                     'evidence':'Parsed embedded evidence-json', 'reason':''})
    first, *rest = original.splitlines()
    table = ['','## Verifier marks — generated from saved evidence',
             '| Claim ID | Number / claim | Mark | Correct number and source |',
             '|---|---|---|---|']
    for mark in marks[1:]:
        def cell(x): return str(x if x is not None else '—').replace('|', '\\|').replace('\n',' ')
        correction = (str(mark['corrected']) + ' — ' if mark['corrected'] is not None else '') + (mark['evidence'] or mark['reason'])
        corrected = str(mark['corrected']) if mark['corrected'] is not None else ''
        claim = next((x for x in claims if x.get('id') == mark['id']), None)
        display = str(claim.get('display', '')) if claim else ''
        if corrected and '%' in display:
            corrected += '%'
        elif corrected and display.startswith('$'):
            corrected = '$' + corrected
        correction = (corrected + ' - ' if corrected else '') + (mark['evidence'] or mark['reason'])
        table.append(f"| {cell(mark['id'])} | {cell(mark['reported'])} | **{mark['status']}** | {cell(correction)} |")
    total = {s: sum(x['status']==s for x in marks[1:]) for s in ('correct','wrong','unsupported')}
    table += ['', f"Marks: {total['correct']} correct, {total['wrong']} wrong, {total['unsupported']} unsupported.", '']
    revised = '\n'.join(rest)
    for mark in marks[1:]:
        if mark['status'] == 'correct' or mark['corrected'] is None: continue
        c = next((x for x in claims if x.get('id') == mark['id']), None)
        if c:
            display = c.get('display', str(c['value']))
            corrected = str(mark['corrected'])
            if isinstance(display, str) and '%' in display:
                corrected = corrected + '%'
            elif isinstance(display, str) and '$' in display:
                corrected = '$' + corrected
            new_lines=[]
            for ln in revised.splitlines():
                if f"[C:{mark['id']}]" in ln:
                    ln=ln.replace(display, corrected, 1) + ' **[Verifier corrected]**'
                new_lines.append(ln)
            revised='\n'.join(new_lines)
    result = folder / 'verified_report.md'
    result.write_text(first+'\n'+'\n'.join(table)+'\n'+revised+'\n', encoding='utf-8')
    (folder/'verifier_marks.json').write_text(json.dumps({'counts': total,'marks': marks,
             'semantic_model_requested': bool(key), 'filing_sources': sorted(texts)}, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Verified report:', result)
    print('Verifier marks:', total)
    return result

"""Seed error in a COPY of a real saved report, then run the independent verifier.

Never changes the original saved run. For actual Lab 04 evidence, use a
model-generated run from agent_team.py rather than the bundled synthetic fixture.
"""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import shutil
import os
from dotenv import load_dotenv
from verifier import registry, START, END, run_verifier


def _supporting_eps_line(folder: Path, value: str) -> tuple[int, str] | None:
    """Find a saved 10-K line that explicitly states the annual diluted EPS."""
    path = folder/'10-K.txt'
    if not path.is_file():
        return None
    value_token = value.replace('$', '').replace(',', '').strip()
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        normalized = line.replace('$', '').replace(',', '')
        if (value_token in normalized and 'diluted' in normalized.lower()
                and ('per share' in normalized.lower() or 'share' in normalized.lower())):
            return number, line.strip()
    return None


def _seeded_value_and_display(value: object, display: str, kind: str) -> tuple[Decimal, str]:
    """Add $1 to EPS or exactly four percentage points to revenue growth."""
    amount=Decimal(str(value))
    if kind=='growth' and '%' in display:
        # Calculator ratios may be stored either as 10.14 or as 0.1014 while
        # both are displayed as 10.14%.  Preserve that representation.
        fractional=abs(amount) <= Decimal('1')
        seeded=amount + (Decimal('0.04') if fractional else Decimal('4'))
        visible=seeded * Decimal('100') if fractional else seeded
    else:
        seeded=amount + Decimal('1')
        visible=seeded
    precision=len(display.split('.',1)[1].split('%')[0]) if '.' in display else 0
    formatted=f'{visible:.{precision}f}'
    return seeded, ('$', '')[not display.startswith('$')] + formatted + ('%' if '%' in display else '')


def seed(original: Path, kind: str) -> Path:
    if not (original/'report.md').exists():
        raise ValueError('This saved run has no report.md; run the agent team first')
    target=original.parent / f'{original.name}_SEEDED_{kind.upper()}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S_%f}'
    shutil.copytree(original,target)
    report=(target/'report.md').read_text(encoding='utf-8')
    claims=registry(report)
    if kind=='eps':
        facts=json.loads((target/'facts.json').read_text(encoding='utf-8'))
        current_end=str(facts['fields']['diluted_eps']['current']['end'])
        choice=next((c for c in claims if c.get('source',{}).get('tag')=='EarningsPerShareDiluted'
                     and str(c.get('source',{}).get('period')) in ('current',current_end)
                     and c.get('source',{}).get('end')==current_end),None)
        if choice is None: raise ValueError('No current-period XBRL diluted EPS claim found in saved report')
    else:
        choice=next((c for c in claims if 'revenue' in c.get('label','').lower()
                     and 'growth' in c.get('label','').lower() and
                     c.get('source',{}).get('kind')=='ratio' and '%' in c.get('display','')),None)
        if choice is None:raise ValueError('No sourced revenue-growth percentage claim found in report')
    old=str(choice['display'])
    if kind=='eps' and not choice.get('source', {}).get('line'):
        support=_supporting_eps_line(target, old)
        if support is None:
            raise ValueError('Could not find an explicit annual diluted-EPS line in saved 10-K')
        line_number, quote=support
        choice['source'].update({'document':'10-K','line':line_number,'quote':quote})
    amount,new=_seeded_value_and_display(choice['value'],old,kind)
    choice['value']=float(amount)
    choice['display']=new
    marker=f"[C:{choice['id']}]"
    body, tail=report.split('## Numeric evidence registry',1)
    affected=0
    lines=[]
    for line in body.splitlines():
        if marker in line and old in line:
            line=line.replace(old,new,1)
            affected+=1
        lines.append(line)
    if not affected: raise ValueError(f'No report text containing {old} and {marker}; cannot seed reliably')
    report='\n'.join(lines)+'\n## Numeric evidence registry'+tail
    start=report.find(START)
    if start<0: raise ValueError('Report lacks evidence-json registry')
    close=report.find(END,start+len(START))
    report=report[:start+len(START)]+json.dumps(claims,indent=2)+report[close:]
    (target/'report.md').write_text(report,encoding='utf-8')
    (target/'seed_manifest.json').write_text(json.dumps({'seed_type':kind,'source':str(original),
        'claim_id':choice['id'],'original':old,'seeded':new, 'note':'Original source run untouched'},indent=2),encoding='utf-8')
    print(f'Seed copy: {target}')
    run_verifier(target,os.getenv('API_KEY',''),os.getenv('MODEL_NAME','gpt-4.1-mini'))
    return target


def main():
    load_dotenv(Path(__file__).parent/'.env')
    ap=argparse.ArgumentParser()
    ap.add_argument('run_folder')
    ap.add_argument('--test',choices=['eps','growth'],required=True)
    args=ap.parse_args()
    seed(Path(args.run_folder),args.test)

if __name__=='__main__':main()

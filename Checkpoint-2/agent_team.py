"""FIN 67110 Checkpoint 2: fixed LangGraph agent team and compulsory verifier.

Use: python agent_team.py TICKER --peers PEER1,PEER2 --price 000.00 --price-date YYYY-MM-DD
Offline replay: --source-run runs/SAVED_DATA_RUN (does not re-fetch SEC evidence).
Verify one copied run: python agent_team.py --verify-only runs/SAVED_REPORT_COPY
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
from typing import TypedDict, Any
from dotenv import load_dotenv

from sec_desk import DeskError, SECClient, perform_data_steps
from roles import parse_json
from verifier import _get_facts, _line_evidence, lines as saved_lines, run_verifier

HEADINGS = ('Overview', 'Market Positioning and Growth Outlook', 'Valuation Insights',
            'Future Developments and Strategic Recommendations', 'Investment Recommendation')
ROLE_FILES = {'Research Analyst': 'research_analyst.md',
              'Financial Analyst': 'financial_analyst.md',
              'Investment Advisor': 'investment_advisor.md',
              'Strategy Manager': 'strategy_manager.md'}
ROOT = Path(__file__).parent

class TeamState(TypedDict, total=False):
    ticker: str
    peers: list[str]
    price: float | None
    price_date: str
    output: str
    source_run: str
    run_dir: str
    data: dict
    outputs: dict
    manager: dict
    report_path: str
    verified_path: str


def save(folder: Path, filename: str, d: Any):
    p = folder / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


def new_dir(base: Path, ticker: str, name: str = '') -> Path:
    slug = re.sub(r'[^A-Za-z0-9]+','_',name or ticker).strip('_')[:48]
    timestamp = f'{datetime.now(timezone.utc):%Y-%m-%d_%H%M%S_%f}'
    # Windows can return the same apparent microsecond twice in rapid succession.
    # Preserve the timestamp-based name and add a suffix only if that occurs.
    for attempt in range(1_000):
        suffix = '' if attempt == 0 else f'_{attempt}'
        p = base / f'{slug}_{ticker}_{timestamp}{suffix}_UTC'
        try:
            p.mkdir(parents=True, exist_ok=False)
            return p
        except FileExistsError:
            continue
    raise RuntimeError('Could not allocate a unique saved-run folder')


def _persona_needs_authoring(instructions: str) -> bool:
    marker=re.search(r'<!-- STUDENT/PARTNER PERSONA START -->(.*?)<!-- STUDENT/PARTNER PERSONA END -->',
                     instructions,re.S)
    return 'TODO: REWRITE' in instructions or (marker is not None and not marker.group(1).strip())


def ingest(state: TeamState) -> dict:
    print('NODE — Steps 1–7 (SEC filings, facts, ratios, peers)', flush=True)
    before = {'ticker': state['ticker'], 'peers': state['peers'], 'price': state['price'],
              'price_date': state.get('price_date',''), 'source_run': state.get('source_run','')}
    if state.get('source_run'):
        original = Path(state['source_run'])
        if not (original/'run_manifest.json').is_file():
            raise ValueError('The --source-run folder must contain run_manifest.json')
        d = json.loads((original/'run_manifest.json').read_text(encoding='utf-8'))
        if d.get('ticker') != state['ticker']:
            raise ValueError('Ticker does not match saved source run')
        run_dir = new_dir(Path(state['output']), state['ticker'], d.get('name',''))
        for p in original.iterdir():
            if p.is_file() and p.suffix in ('.txt','.json'):
                shutil.copy2(p, run_dir/p.name)
        d['folder'] = str(run_dir)
        d['replay_from'] = str(original)
        if state.get('price') is not None:
            d['price'] = state['price']
            d['price_date'] = state.get('price_date','')
            from sec_desk import calculate
            d['ratios'] = calculate(d['facts'], state['price'])
            save(run_dir, 'ratios.json', d['ratios'])
        save(run_dir, 'run_manifest.json', d)
    else:
        client = SECClient(os.getenv('SEC_USER_AGENT',''))
        d = perform_data_steps(client, state['ticker'], state['peers'], state.get('price'),
                               Path(state['output']), price_date=state.get('price_date',''))
        run_dir = Path(d['folder'])
    save(run_dir, 'nodes/01_steps_input.json', before)
    save(run_dir, 'nodes/01_steps_output.json', {'ticker':d['ticker'], 'facts':d['facts'],
                         'ratios':d['ratios'], 'filings':d['filings'],'quarterly':d.get('quarterly'),
                         'peers':list(d.get('peers',{}))})
    return {'data': d, 'run_dir': str(run_dir), 'outputs': {}}


def _model(state: TeamState, role: str, task: str, context: dict,
           expected: Any, index: str, revision: str = '') -> dict:
    from openai import OpenAI
    name = ROLE_FILES[role]
    instructions = (ROOT/'roles'/name).read_text(encoding='utf-8')
    if _persona_needs_authoring(instructions):
        print(f'PERSONA REMINDER — customize roles/{name} in your own words before submission.',flush=True)
    request = {'task': task, 'context':context, 'expected_output':expected}
    if revision: request['context']['revision_feedback_one_retry_only'] = revision
    folder = Path(state['run_dir'])
    save(folder, f'nodes/{index}_{role.lower().replace(" ","_")}_input.json', request)
    print(f'NODE — {role}' + (' (single retry)' if revision else ''), flush=True)
    key = os.getenv('API_KEY','')
    if not key: raise RuntimeError('API_KEY is absent from local .env. Do not put secrets in repository.')
    response = OpenAI(api_key=key).responses.create(model=os.getenv('MODEL_NAME','gpt-4.1-mini'),
                         instructions=instructions, input=json.dumps(request, ensure_ascii=False, default=str))
    raw=response.output_text
    try:
        obj=parse_json(raw)
    except ValueError as error:
        raw_path=folder/f'nodes/{index}_{role.lower().replace(" ","_")}_invalid_response.txt'
        raw_path.write_text(raw,encoding='utf-8')
        raise ValueError(f'{error} Raw response saved to {raw_path}') from error
    save(folder, f'nodes/{index}_{role.lower().replace(" ","_")}_output.json', obj)
    return obj


def analyst_node(role: str, index: str):
    def run(state: TeamState) -> dict:
        data, outputs = state['data'], state.get('outputs',{})
        if role == 'Research Analyst':
            context = {'ticker':data['ticker'],'company':data['name'],
                 '10K': {'accession':data['filings']['10-K']['accession'],
                         'excerpt':data['excerpts']['10-K']},
                 'earnings_release': {'accession': data['filings']['earnings_8-K']['accession'],
                     'excerpt':data['excerpts']['release_EX-99.1']}}
            expected={'overview':'Markdown', 'market_positioning_and_growth_outlook':'Markdown',
                      'future_developments_and_strategic_recommendations':'Markdown',
                      'insight':'Must begin Insight: and include [C:id] plus filing and L000123',
                      'claims':'list of structured evidence entries for ANY numeric statements, including Insight line'}
        elif role == 'Financial Analyst':
            context = {'ticker':data['ticker'], 'facts':data['facts'], 'ratios':data['ratios'],
                  'peers':data.get('peers',{}), 'price':data.get('price'),
                  'price_date':data.get('price_date'), 'quarterly':data.get('quarterly'),
                  'filings':data['filings'], 'release_lines':data.get('release_lines'),
                  'release_excerpt':data['excerpts']['release_EX-99.1']}
            expected={'valuation_insights':'Markdown (include numeric [C:id] citations)',
                      'insight':'Must begin Insight: and include [C:id] plus filing and L000123',
                      'claims':'list of evidence objects for each numeric claim'}
        else:
            context={'ticker':data['ticker'],'research_output':outputs.get('Research Analyst'),
                    'financial_output':outputs.get('Financial Analyst')}
            expected={'investment_recommendation':'Markdown recommendation only',
                      'insight':'Must begin Insight: and include [C:id] plus filing and L000123',
                      'claims':'list of structured entries for Insight numeric facts only, NOT thesis judgments'}
        obj = _model(state,role, 'Build only your assigned report sections with source lines. '
                     'Return every expected key. EVERY numeric claim anywhere in your Markdown, including dates, '
                     'must immediately include [C:id] for a claim in your own claims list; otherwise omit the '
                     'number. Your insight value MUST begin "Insight:", cite [C:id], name a filing and L000123, '
                     'and rely on that matching structured claim. For a line source, copy the exact supplied line '
                     'as quote without ellipses and use its actual line number; never summarize a quotation. For '
                     'XBRL, copy field, period, tag, end, and accession exactly from facts. If evidence is absent, '
                     'say Not established. Never fabricate numbers, line references, or quotations.',
                     context,expected,index)
        return {'outputs': {**outputs,role:obj}}
    return run


def _section_with_insight(output: dict, key: str) -> str:
    body=output.get(key,'')
    if not isinstance(body,str):
        return body
    insight=output.get('insight','')
    if not isinstance(insight,str) or not insight.strip() or re.search(r'(?m)^\s*Insight:',body):
        return body
    insight=insight.strip()
    if not re.match(r'(?i)^Insight:',insight):
        insight='Insight: '+insight
    return body.rstrip()+'\n\n'+insight


def _five_parts(outputs: dict) -> dict[str,str]:
    r=outputs.get('Research Analyst',{})
    f=outputs.get('Financial Analyst',{})
    a=outputs.get('Investment Advisor',{})
    return {'Overview':_section_with_insight(r,'overview'),
            'Market Positioning and Growth Outlook':r.get('market_positioning_and_growth_outlook',''),
            'Valuation Insights':_section_with_insight(f,'valuation_insights'),
            'Future Developments and Strategic Recommendations':r.get('future_developments_and_strategic_recommendations',''),
            'Investment Recommendation':_section_with_insight(a,'investment_recommendation')}


def _first_release_paragraph(text: str) -> str:
    chunks=[x.strip() for x in re.split(r'\n\s*\n',text) if x.strip()]
    return next((x for x in chunks if len(x) > 70), chunks[0] if chunks else '')


def _source_issues(source: Any) -> list[str]:
    if not isinstance(source, dict):
        return ['missing structured source']
    kind=source.get('kind')
    if kind=='xbrl':
        required=('field','period','tag','end','accession')
    elif kind=='line':
        required=('document','line','quote','period','definition')
    elif kind=='ratio':
        required=('formula','definition','inputs')
    elif kind=='provided':
        required=('field','date')
    else:
        return ['source kind must be xbrl, line, or ratio']
    missing=[name for name in required if not source.get(name)]
    issues=[f'missing source {name}' for name in missing]
    if kind=='ratio' and isinstance(source.get('inputs'),dict):
        for name, operand in source['inputs'].items():
            if not isinstance(operand,dict):
                issues.append(f'ratio input {name} is not an object')
                continue
            if 'value' not in operand:
                issues.append(f'ratio input {name} missing value')
            issues.extend(f'ratio input {name}: {reason}' for reason in _source_issues(operand.get('source')))
    return issues


def _claim_source_issues(output: dict) -> list[str]:
    claims=output.get('claims')
    if not isinstance(claims,list):
        return ['claims must be an array']
    issues=[]
    for position, claim in enumerate(claims,1):
        if not isinstance(claim,dict):
            issues.append(f'claim {position} is not an object')
            continue
        for key in ('id','label','value','display','source'):
            if key not in claim or claim.get(key) in ('',None):
                issues.append(f'claim {position} missing {key}')
        issues.extend(f'claim {claim.get("id",position)}: {reason}'
                      for reason in _source_issues(claim.get('source')))
    return issues


def _saved_evidence_issues(folder: Path, facts: dict, output: dict) -> list[str]:
    """Check claim citations against immutable saved evidence before the retry slot."""
    texts=saved_lines(folder)
    issues=[]

    def check(source: Any, label: str):
        if not isinstance(source,dict):
            return
        kind=source.get('kind')
        if kind=='xbrl' and not _get_facts(facts,source):
            issues.append(f'{label}: XBRL tag/period/end/accession does not match saved facts')
        elif kind=='line':
            _, error=_line_evidence(source,texts)
            if error:
                issues.append(f'{label}: {error}')
        elif kind=='ratio' and isinstance(source.get('inputs'),dict):
            for name,operand in source['inputs'].items():
                if isinstance(operand,dict):
                    check(operand.get('source'),f'{label} input {name}')

    claims=output.get('claims',[])
    if isinstance(claims,list):
        for claim in claims:
            if isinstance(claim,dict):
                check(claim.get('source'),f"claim {claim.get('id','missing-id')}")
    return issues


def _insight_valid(output: dict, first_paragraph: str) -> bool:
    text='\n'.join(v for v in output.values() if isinstance(v,str))
    found=re.search(r'(?m)^\s*Insight:\s*(.+)$',text)
    if not found: return False
    line=found.group(1).strip()
    if not re.search(r'(?i)(10-K|10-Q|EX-99\.1|release).*?\bL\d+',line):return False
    cited_ids=re.findall(r'\[C:([\w-]+)\]',line)
    claims={str(c.get('id')):c for c in output.get('claims',[]) if isinstance(c,dict) and c.get('id')}
    if not cited_ids or any(cid not in claims for cid in cited_ids): return False
    if any(_source_issues(claims[cid].get('source')) for cid in cited_ids): return False
    # Model manager also checks semantic restatement. Code catches obvious verbatim reuse.
    substantive=re.sub(r'\s*\[C:[^]]+\]', '', line)
    return len(substantive)>35 and substantive.lower() not in first_paragraph.lower()


def manager_node(state: TeamState) -> dict:
    data,outputs=state['data'],dict(state['outputs'])
    folder=Path(state['run_dir'])
    first_release=(folder/'release_EX-99.1.txt').read_text(encoding='utf-8')
    first_paragraph=_first_release_paragraph(first_release)
    parts=_five_parts(outputs)
    result=_model(state,'Strategy Manager','Check five sections, numerical evidence, and three independent Insight lines. '
                  'Issue one retry per failing role at most.',
                  {'ticker':data['ticker'],'sections':parts,'first_release_paragraph':first_paragraph,
                   'facts':data['facts'],'ratios':data['ratios']},
                  {'status':'PASS or REVISE','issues':[{'role':'one analyst role','reason':'brief error'}]},'05')
    issues={}
    for issue in result.get('issues',[]):
        if issue.get('role') in ('Research Analyst','Financial Analyst','Investment Advisor'):
            issues[issue['role']]=str(issue.get('reason','Needs revision'))
    for role in ('Research Analyst','Financial Analyst','Investment Advisor'):
        if not _insight_valid(outputs.get(role,{}),first_paragraph):
            issues[role]=(issues.get(role,'')+'; Missing, uncited, or verbatim-headline Insight line')
        source_issues=_claim_source_issues(outputs.get(role,{}))
        if source_issues:
            issues[role]=(issues.get(role,'')+'; Invalid evidence registry: '
                          + '; '.join(source_issues[:4]))
        saved_issues=_saved_evidence_issues(folder,data['facts'],outputs.get(role,{}))
        if saved_issues:
            issues[role]=(issues.get(role,'')+'; Saved-evidence mismatch: '
                          + '; '.join(saved_issues[:4]))
    if not parts['Overview'] or not parts['Market Positioning and Growth Outlook'] or not parts['Future Developments and Strategic Recommendations']:
        issues['Research Analyst']=issues.get('Research Analyst','')+'; Missing research sections'
    if not parts['Valuation Insights'] or not outputs.get('Financial Analyst',{}).get('claims'):
        issues['Financial Analyst']=issues.get('Financial Analyst','')+'; Missing valuation or claims registry'
    if not parts['Investment Recommendation']:
        issues['Investment Advisor']=issues.get('Investment Advisor','')+'; Missing recommendation'
    # Fixed, bounded retry slots. Each analyst ran once earlier; no model can route calls.
    for role in ('Research Analyst','Financial Analyst','Investment Advisor'):
        if role not in issues:continue
        if role == 'Research Analyst':
            ctx={'previous':outputs[role], 'filing_excerpt':data['excerpts']['10-K'],
                 'release_excerpt':data['excerpts']['release_EX-99.1']}
            expected=['overview','market_positioning_and_growth_outlook','future_developments_and_strategic_recommendations','insight','claims']
        elif role == 'Financial Analyst':
            ctx={'previous':outputs[role], 'facts':data['facts'], 'ratios':data['ratios'],
                 'release_lines':data['release_lines']}
            expected=['valuation_insights','insight','claims']
        else:
            ctx={'previous':outputs[role], 'research':outputs['Research Analyst'],
                 'financial':outputs['Financial Analyst']}
            expected=['investment_recommendation','insight','claims']
        outputs[role]=_model(state,role,'Revise only your own output based on feedback.',
                             ctx,expected,'05_retry',issues[role])
    parts=_five_parts(outputs)
    for heading,body in parts.items():
        if not isinstance(body,str) or not body.strip():
            raise ValueError(f'Manager failed to produce required report part: {heading}')
    # Persist unresolved persona defects rather than falsely marking them as passed.
    unresolved=[role for role in ('Research Analyst','Financial Analyst','Investment Advisor')
                if not _insight_valid(outputs.get(role,{}), first_paragraph)]
    unresolved_citations={role:(_claim_source_issues(outputs.get(role,{}) )+
                               _saved_evidence_issues(folder,data['facts'],outputs.get(role,{})))
                          for role in ('Research Analyst','Financial Analyst','Investment Advisor')}
    unresolved_citations={role:problems for role,problems in unresolved_citations.items() if problems}
    registry=[]
    duplicate_ids=[]
    seen_ids=set()
    for role in ('Research Analyst','Financial Analyst','Investment Advisor'):
        own=outputs.get(role,{}).get('claims',[])
        if isinstance(own,list):
            for item in own:
                if isinstance(item,dict):
                    claim_id=item.get('id')
                    if not claim_id:
                        raise ValueError(f'{role} supplied a numeric claim without an id')
                    if claim_id in seen_ids:
                        duplicate_ids.append(claim_id)
                        continue
                    seen_ids.add(claim_id)
                    registry.append(item)
    ids=[item.get('id') for item in registry]
    if len(ids)!=len(set(ids)):
        print('CAUTION — duplicate numeric claim IDs across roles; verifier may mark ambiguous references.',flush=True)
    first='Filings: 10-K {k}; 10-Q {q}; earnings 8-K / EX-99.1 {r}.'.format(
           k=data['filings']['10-K']['accession'],q=data['filings']['10-Q']['accession'],
           r=data['filings']['earnings_8-K']['accession'])
    report=[first,'',f"# Equity research — {data['ticker']} — {data['name']}",
            '',f"Run UTC: {data.get('run_utc','')} | Source replay: {bool(data.get('replay_from'))}",
            '', '**Model work is independently verified below; not investment advice.**','']
    for heading,body in parts.items():
        report += [f'## {heading}','',body,'']
    report += ['## Numeric evidence registry', '', '```evidence-json',json.dumps(registry,indent=2,ensure_ascii=False),
               '```','','## Manager review', '', f"Manager model status: {result.get('status')}",
               f"Retry roles (one retry maximum): {', '.join(issues) or 'none'}",
               f"Unresolved Insight formatting: {', '.join(unresolved) or 'none'}",
               f"Unresolved claim citation roles: {', '.join(unresolved_citations) or 'none'}",'']
    p=folder/'report.md'
    p.write_text('\n'.join(report),encoding='utf-8')
    save(folder,'nodes/05_manager_summary.json',{'review':result,'retry_roles':issues,
                  'unresolved_insight':unresolved,'duplicate_claim_ids_omitted':duplicate_ids,
                  'unresolved_claim_citations':unresolved_citations,
                  'outputs_after_retries':outputs})
    print('Five-part report:',p,flush=True)
    return {'outputs':outputs,'manager':result,'report_path':str(p)}


def verifier_node(state: TeamState) -> dict:
    folder=Path(state['run_dir'])
    save(folder,'nodes/06_verifier_input.json',{'report_path':str(folder/'report.md'),
            'facts_path':str(folder/'facts.json'),
            'filing_text_files':[p.name for p in folder.glob('*.txt')],
            'note':'Verifier reads report + facts + saved filing text only'})
    result=run_verifier(folder,os.getenv('API_KEY',''),os.getenv('MODEL_NAME','gpt-4.1-mini'))
    save(folder,'nodes/06_verifier_output.json',{'verified_path':str(result),
                'marks_path':str(folder/'verifier_marks.json')})
    return {'verified_path':str(result)}


def build_graph():
    from langgraph.graph import StateGraph, START as LG_START, END as LG_END
    graph=StateGraph(TeamState)
    graph.add_node('Steps_1_to_7',ingest)
    graph.add_node('Research_Analyst',analyst_node('Research Analyst','02'))
    graph.add_node('Financial_Analyst',analyst_node('Financial Analyst','03'))
    graph.add_node('Investment_Advisor',analyst_node('Investment Advisor','04'))
    graph.add_node('Strategy_Manager',manager_node)
    graph.add_node('Verifier',verifier_node)
    order=['Steps_1_to_7','Research_Analyst','Financial_Analyst','Investment_Advisor','Strategy_Manager','Verifier']
    graph.add_edge(LG_START,order[0])
    for a,b in zip(order,order[1:]):graph.add_edge(a,b)
    graph.add_edge(order[-1],LG_END)
    return graph.compile()


def main(argv=None):
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description='FIN 67110 Checkpoint 2 fixed LangGraph + independent verifier')
    parser.add_argument('ticker',nargs='?',help='Stock ticker symbol')
    parser.add_argument('--peers',default='',help='Comma-separated peer tickers')
    parser.add_argument('--price',type=float,help='Closing price used in Lab 03')
    parser.add_argument('--price-date',default='',help='Date of the closing price')
    parser.add_argument('--output',default='runs',help='Output directory')
    parser.add_argument('--source-run',default='',help='Offline replay of a saved seven-step data run')
    parser.add_argument('--verify-only',default='',metavar='SAVED_RUN_FOLDER',
                        help='Only verify the compiled report in this saved run')
    args=parser.parse_args(argv)
    if args.verify_only:
        if args.ticker or args.source_run or args.price is not None or args.peers:
            parser.error('--verify-only is separate from running the agent team')
        run_verifier(Path(args.verify_only),os.getenv('API_KEY',''),os.getenv('MODEL_NAME','gpt-4.1-mini'))
        return
    if not args.ticker:parser.error('ticker is required for a full graph run')
    if args.price is not None and args.price <= 0:parser.error('--price must be positive')
    if args.price is not None and not args.price_date:
        print('CAUTION: date of the official price is not supplied; P/E source not fully auditable')
    graph=build_graph()
    initial={'ticker':args.ticker.upper(),'peers':[x.strip().upper() for x in args.peers.split(',') if x.strip()],
             'price':args.price,'price_date':args.price_date,'output':args.output,
             'source_run':args.source_run}
    result=graph.invoke(initial)
    print('FINAL —',result['verified_path'])

if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,DeskError,FileNotFoundError) as exc:
        raise SystemExit(f'ERROR: {exc}')

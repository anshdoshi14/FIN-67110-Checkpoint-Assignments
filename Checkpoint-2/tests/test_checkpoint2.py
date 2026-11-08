from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import _missed_amounts, check_claim, registry, run_verifier, lines


def fixture(name):
    return ROOT/'tests'/'fixtures'/name


def test_clean_eleven_core_values_are_correct():
    result=json.loads((fixture('clean')/'verifier_marks.json').read_text())
    assert result['counts']=={'correct':11,'wrong':0,'unsupported':0}
    assert len([m for m in result['marks'] if m['id']!='registry-size'])==11


def test_seeded_diluted_eps_wrong_one_dollar():
    f=fixture('eps_seeded')
    result=json.loads((f/'verifier_marks.json').read_text())
    eps=next(m for m in result['marks'] if m['id']=='diluted_eps')
    assert eps['status']=='wrong'
    assert str(eps['reported'])=='21.76'
    assert eps['corrected']=='20.76'
    assert 'L1057' in eps['evidence']
    assert '20.76 per diluted share' in eps['evidence']
    v=(f/'verified_report.md').read_text()
    assert v.startswith('Filings:')
    assert v.index('## Verifier marks') < v.index('# COST')
    assert 'FY diluted EPS: $20.76 [C:diluted_eps] **[Verifier corrected]**' in v


def test_invented_growth_four_pp_is_detected():
    result=json.loads((fixture('growth_seeded')/'verifier_marks.json').read_text())
    growth=next(m for m in result['marks'] if m['id']=='revenue_growth')
    assert growth['status']=='wrong'
    assert abs(float(growth['corrected'])-10.14)<.001
    assert '303154000000' in growth['evidence']
    assert '275235000000' in growth['evidence']


def test_missing_ratio_definition_unsupported():
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    obj=next(x for x in registry((folder/'report.md').read_text()) if x['id']=='roe')
    obj['source'].pop('definition')
    result=check_claim(obj,facts,lines(folder))
    assert result['status']=='unsupported'


def test_wrong_period_is_unsupported():
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    obj=next(x for x in registry((folder/'report.md').read_text()) if x['id']=='diluted_eps')
    obj['source']['end']='2024-01-01'
    result=check_claim(obj,facts,lines(folder))
    assert result['status']=='unsupported'


def test_sec_tag_and_actual_end_date_resolve_to_saved_fact():
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    obj=next(x for x in registry((folder/'report.md').read_text()) if x['id']=='diluted_eps')
    obj['source']['field']='EarningsPerShareDiluted'
    obj['source']['period']='2026-08-30'
    result=check_claim(obj,facts,lines(folder))
    assert result['status']=='correct'
    assert result['corrected']=='20.76'


def test_sec_tag_and_exact_saved_frame_resolve_to_saved_fact():
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    obj=next(x for x in registry((folder/'report.md').read_text()) if x['id']=='diluted_eps')
    obj['source']['field']='EarningsPerShareDiluted'
    obj['source']['period']='CY2026'
    result=check_claim(obj,facts,lines(folder))
    assert result['status']=='correct'
    assert result['corrected']=='20.76'


def test_exhibit_alias_resolves_to_saved_release_file():
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    obj={'id':'release_line','label':'Quarterly net sales','value':93.9,
         'source':{'kind':'line','document':'EX-99.1','line':10,
                   'quote':'Net sales for the quarter increased 11.2 percent, to $93.9 billion',
                   'period':'2026-08-30','definition':'quarterly net sales'}}
    result=check_claim(obj,facts,lines(folder))
    assert result['status']=='unsupported'
    assert 'Model semantic review unavailable' in result['reason']


def test_amount_coverage_uses_numeric_token_not_display_units():
    report='# Test\n\n## Valuation Insights\n\nRevenue was $303.154 billion [C:revenue].\n\n## Numeric evidence registry\n'
    claims=[{'id':'revenue','display':'$303.154 billion'}]
    assert _missed_amounts(report,claims)==[]


def test_unverified_line_claim_is_not_marked_correct_without_semantic_model():
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    text=(folder/'10-K.txt').read_text(encoding='utf-8').splitlines()[1056]
    obj={'id':'lineonly','label':'FY diluted EPS','value':20.76,
         'source':{'kind':'line','document':'10-K','line':1057,
             'quote':'$20.76 per diluted share','period':'FY 2026','definition':'diluted EPS'}}
    r=check_claim(obj,facts,lines(folder),key='')
    assert r['status']=='unsupported'
    assert 'Model semantic review unavailable' in r['reason']


def test_cli_verify_only_runs_without_graph_or_api_key(tmp_path):
    from shutil import copyfile
    folder=tmp_path/'copy'
    folder.mkdir()
    for f in fixture('eps_seeded').iterdir():
        if f.is_file() and f.name not in ('verified_report.md','verifier_marks.json'):
            copyfile(f,folder/f.name)
    c=subprocess.run([sys.executable,str(ROOT/'agent_team.py'),'--verify-only',str(folder)],
                     cwd=ROOT,capture_output=True,text=True)
    assert c.returncode==0, c.stdout+c.stderr
    assert 'NODE — Verifier' in c.stdout
    assert 'NODE — Research Analyst' not in c.stdout
    marks=json.loads((folder/'verifier_marks.json').read_text())
    assert marks['counts']=={'correct':10,'wrong':1,'unsupported':0}


def test_graph_has_compulsory_verifier_edge_no_skip_flag():
    src=(ROOT/'agent_team.py').read_text()
    assert "graph.add_edge(order[-1],LG_END)" in src
    assert "'Strategy_Manager','Verifier'" in src
    assert "--skip-verifier" not in src and "--no-verify" not in src
    assert 'run_verifier(folder' in src


def test_core_app_has_no_company_specific_branches():
    for name in ('agent_team.py','verifier.py','app.py'):
        source=(ROOT/name).read_text()
        assert not re.search(r'\b(COST|WMT|PEP|TGT|BJ)\b',source)


def test_unique_new_run_folder(tmp_path):
    from agent_team import new_dir
    a=new_dir(tmp_path,'TEST','Example')
    b=new_dir(tmp_path,'TEST','Example')
    assert a!=b and a.exists() and b.exists()


def test_seed_error_script_does_not_modify_original(tmp_path):
    import shutil
    from seed_error import seed
    src=tmp_path/'source'
    shutil.copytree(fixture('clean'),src)
    initial=(src/'report.md').read_bytes()
    seeded=seed(src,'eps')
    assert seeded!=src
    assert (src/'report.md').read_bytes()==initial
    result=json.loads((seeded/'verifier_marks.json').read_text())
    assert result['counts']['wrong']==1
    assert next(x for x in result['marks'] if x['id']=='diluted_eps')['corrected']=='20.76'


def test_seed_eps_helper_finds_explicit_saved_10k_per_share_line():
    from seed_error import _supporting_eps_line
    support=_supporting_eps_line(fixture('clean'),'$20.76')
    assert support is not None
    number, quote=support
    assert number==1057
    assert '20.76 per diluted share' in quote


def test_growth_seed_adds_four_points_when_ratio_is_stored_as_decimal():
    from seed_error import _seeded_value_and_display
    value, display=_seeded_value_and_display('0.1014369539','10.14%','growth')
    assert str(value)=='0.1414369539'
    assert display=='14.14%'


def test_fractional_ratio_correction_preserves_percentage_display():
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    obj=next(x for x in registry((folder/'report.md').read_text()) if x['id']=='revenue_growth')
    obj['value']=0.1414369539
    obj['display']='14.14%'
    obj['source']['formula']='(a-b)/b'
    result=check_claim(obj,facts,lines(folder))
    assert result['status']=='wrong'
    assert result['corrected']=='10.14'


def test_manager_requires_xbrl_period_and_registered_insight_claim():
    from agent_team import _claim_source_issues, _insight_valid
    output={'overview':'Insight: A distinct filing fact is independently sourced from the annual filing [10-K L1057] [C:eps]',
            'claims':[{'id':'eps','label':'Diluted EPS','value':20.76,'display':'$20.76',
                       'source':{'kind':'xbrl','field':'diluted_eps','tag':'EarningsPerShareDiluted',
                                 'end':'2026-08-30','accession':'0000909832-26-000093'}}]}
    assert any('missing source period' in issue for issue in _claim_source_issues(output))
    assert not _insight_valid(output,'An unrelated earnings-release headline.')
    output['claims'][0]['source']['period']='current'
    assert _insight_valid(output,'An unrelated earnings-release headline.')


def test_malformed_source_is_marked_unsupported_not_a_verifier_crash():
    result=check_claim({'id':'bad-source','label':'Malformed source','value':1,'source':[]},{},{})
    assert result['status']=='unsupported'
    assert 'must be an object' in result['reason']


def test_malformed_ratio_formula_is_marked_unsupported_not_a_verifier_crash():
    item={'id':'bad-formula','label':'Malformed formula','value':1,'display':'1.0%',
          'source':{'kind':'ratio','formula':'Operating Income / Total Revenue','definition':'test','inputs':{}}}
    result=check_claim(item,{},{})
    assert result['status']=='unsupported'
    assert 'invalid syntax' in result['reason']


def test_role_parser_accepts_harmless_model_json_formatting_variants():
    from roles import parse_json
    assert parse_json('{"overview":"line one\nline two",}')['overview']=='line one\nline two'
    assert parse_json('{"source":{"line": L000123}}')['source']['line']==123
    assert parse_json('{"source":{"line": 010}}')['source']['line']==10


def test_persona_reminder_only_flags_an_empty_marker():
    from agent_team import _persona_needs_authoring
    empty='<!-- STUDENT/PARTNER PERSONA START --><!-- STUDENT/PARTNER PERSONA END -->'
    complete='<!-- STUDENT/PARTNER PERSONA START -->Student-authored role text.<!-- STUDENT/PARTNER PERSONA END -->'
    assert _persona_needs_authoring(empty)
    assert not _persona_needs_authoring(complete)


def test_compiler_places_explicit_role_insights_in_owned_sections():
    from agent_team import _five_parts
    outputs={'Research Analyst':{'overview':'Research overview','insight':'Insight: Research fact [C:r] [10-K L100]'},
             'Financial Analyst':{'valuation_insights':'Financial analysis','insight':'Insight: Financial fact [C:f] [10-K L101]'},
             'Investment Advisor':{'investment_recommendation':'Hold','insight':'Insight: Advisor fact [C:a] [10-K L102]'}}
    parts=_five_parts(outputs)
    assert 'Insight: Research fact' in parts['Overview']
    assert 'Insight: Financial fact' in parts['Valuation Insights']
    assert 'Insight: Advisor fact' in parts['Investment Recommendation']


def test_manager_detects_saved_filing_quote_mismatch_before_retry():
    from agent_team import _saved_evidence_issues
    folder=fixture('clean')
    facts=json.loads((folder/'facts.json').read_text())
    claim={'id':'filing_quote','source':{'kind':'line','document':'10-K','line':1,
                                         'quote':'A fabricated quotation'}}
    issues=_saved_evidence_issues(folder,facts,{'claims':[claim]})
    assert any('quotation does not match' in issue for issue in issues)


# --- Lab 04 "too eager" guard: a correct number must not be marked wrong because the
# --- model paraphrased its quotation. The number on the cited line is what counts.

def test_number_in_line_allows_formatting_and_scale_differences():
    from verifier import number_in_line
    line='NET INCOME | $ | 2,998 |  |  | $ | 2,610 |  |  | $ | 9,226 |  |  | $ | 8,099 |'
    assert number_in_line(9226, line)
    assert number_in_line('9.226', line)      # billions vs millions in the table
    assert number_in_line('$9,226', line)
    assert not number_in_line(9227, line)
    assert not number_in_line(11, 'Fiscal 2011 results')  # whole-token match only


def test_paraphrased_quote_with_number_on_line_is_not_wrong():
    texts={'10-K':['Costco operated 939, 914, and 890 warehouses worldwide at August 30, 2026.']}
    item={'id':'w','label':'Warehouses','value':939,
          'source':{'kind':'line','document':'10-K','line':1,'period':'FY2026',
                    'definition':'warehouse count','quote':'operated 939 warehouses (paraphrased)'}}
    out=check_claim(item,{},texts,key='')   # no API key: semantic review pending
    assert out['status']=='unsupported'     # pending model review, NOT wrong
    assert '939' in out['evidence']


def test_number_absent_from_cited_line_is_wrong():
    texts={'10-K':['Costco operated 939, 914, and 890 warehouses worldwide at August 30, 2026.']}
    item={'id':'w','label':'Warehouses','value':950,
          'source':{'kind':'line','document':'10-K','line':1,'period':'FY2026',
                    'definition':'warehouse count','quote':'operated 950 warehouses'}}
    out=check_claim(item,{},texts,key='')
    assert out['status']=='wrong'
    assert 'does not contain' in out['reason']


def test_non_numeric_claim_value_is_unsupported_with_plain_reason():
    item={'id':'x','label':'Peer margins','value':{'A':0.04,'B':0.05},
          'source':{'kind':'line','document':'10-K','line':1}}
    out=check_claim(item,{},{'10-K':['anything']},key='')
    assert out['status']=='unsupported'
    assert 'not a single number' in out['reason']

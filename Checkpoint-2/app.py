"""Optional Streamlit UI for the existing agent_team.py CLI; needs local credentials."""
from pathlib import Path
import subprocess
import sys
import streamlit as st

st.set_page_config(page_title='FIN 67110 Agent Team',layout='wide')
st.title('FIN 67110 — Verified Equity Research Desk')
st.caption('Graph steps are fixed in code. Every completed report runs the Verifier.')
ticker=st.text_input('Ticker',value='').strip().upper()
peers=st.text_input('Peers (optional)',value='').strip()
price=st.text_input('Closing price (optional)',value='').strip()
price_date=st.text_input('Official close date YYYY-MM-DD (optional)',value='').strip()
if st.button('Run agent team',type='primary'):
    if not ticker or not ticker.isalpha():
        st.error('Enter a valid ticker first.'); st.stop()
    args=[sys.executable,str(Path(__file__).parent/'agent_team.py'),ticker]
    if peers:args+=['--peers',peers]
    if price:
        try:
            if float(price)<=0:raise ValueError
            args+=['--price',str(float(price))]
        except ValueError:
            st.error('Price must be a positive number.');st.stop()
    if price_date:args+=['--price-date',price_date]
    board=st.empty()
    live=[]
    p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                       encoding='utf-8',errors='replace',bufsize=1,cwd=str(Path(__file__).parent))
    for line in p.stdout:
        live.append(line.strip())
        board.code('\n'.join(live[-60:]),language='text')
    result=p.wait()
    if result!=0:
        st.error('Agent team failed; review the full terminal log above. No report is certified.')
    else:
        match=next((x.split('FINAL —',1)[1].strip() for x in reversed(live) if 'FINAL —' in x),None)
        report_path=Path(match) if match else None
        if report_path and not report_path.is_absolute():
            report_path=Path(__file__).parent/report_path
        if report_path and report_path.exists():
            st.success('Verifier completed')
            st.markdown(report_path.read_text(encoding='utf-8'))
        else:
            st.error('No verified report found despite a successful process exit.')

import io, json, hashlib, re, os, sqlite3, secrets
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm

st.set_page_config(page_title='Postventa 055 | Informe de gestión',layout='wide',page_icon='📊')
import administracion
modulo=st.sidebar.radio('Módulo', ['Postventa','Administración'], key='modulo_principal')
if modulo=='Administración':
 administracion.render()
 st.stop()

BASE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('YUHMAK_DATA_DIR',str(BASE/'datos'))); DATA.mkdir(parents=True,exist_ok=True)
SOURCES={'stock':'STOCK 055','out':'Solicitud de Traslado 055','back':'Solicitud de Traslado 109','nc':'Notas de Credito 055'}
NAVY='#022f40'; GOLD='#ffc107'
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--ink:#0c2f40;--muted:#607786;--line:#dce6eb;--gold:#ffc107;--blue:#126b8a;--paper:#f4f7fa}
html,body,.stApp,[class*="css"]{font-family:'DM Sans',Arial,sans-serif!important}
.stApp{background:linear-gradient(180deg,#edf4f7 0,#f7f9fb 380px,#f7f9fb 100%);color:#173849}
.block-container{max-width:1480px!important;padding:1.25rem 2.3rem 4rem!important}
#MainMenu,footer{visibility:hidden}
h1,h2,h3{font-family:Manrope,'DM Sans',sans-serif!important;color:var(--ink)!important;letter-spacing:-.04em!important}
h2{font-size:1.43rem!important}h3{font-size:1.13rem!important}
.hero{position:relative;overflow:hidden;background:linear-gradient(117deg,#032d3d 0%,#064b62 58%,#087693 100%);border:1px solid #17627b;color:white;padding:35px 42px;border-radius:22px;margin:2px 0 20px;box-shadow:0 14px 36px rgba(1,39,55,.16)}
.hero:after{content:'';position:absolute;right:-65px;top:-110px;width:420px;height:420px;border:1px solid rgba(255,255,255,.13);border-radius:50%;box-shadow:0 0 0 62px rgba(255,255,255,.035),0 0 0 125px rgba(255,255,255,.025);pointer-events:none}
.hero .eyebrow{display:inline-block;color:#ffd54d;font-size:.73rem;letter-spacing:.17em;font-weight:800;margin-bottom:12px}
.hero h1{color:#fff!important;font-size:clamp(1.8rem,3vw,2.55rem)!important;font-weight:800!important;margin:0!important;line-height:1.16}
.hero p{color:#d0e8ef;font-size:.97rem;margin:12px 0 0;max-width:650px;line-height:1.6}
.hero .hero-tag{display:inline-block;margin-top:19px;padding:7px 13px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.19);border-radius:100px;color:#fff;font-size:.76rem;font-weight:700}
.section-eyebrow{font-size:.75rem;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:#35667a;margin:28px 0 13px;padding-left:12px;border-left:4px solid var(--gold)}
.note-panel{position:relative;background:#fff;border:1px solid #dce8ed;border-left:5px solid #f5b900;border-radius:14px;padding:20px 24px;line-height:1.85;color:#314f5d;box-shadow:0 5px 20px rgba(15,61,82,.035);margin:12px 0 23px}
.note-panel strong{color:#063b52}
[data-testid="stMetric"]{background:#fff;border:1px solid #e0e9ee;border-radius:17px;padding:22px 23px;min-height:139px;box-shadow:0 6px 19px rgba(7,48,69,.045);transition:box-shadow .18s ease,transform .18s ease;position:relative;overflow:hidden}
[data-testid="stMetric"]:before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(#f6b900,#ffdc64)}
[data-testid="stMetric"]:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(7,48,69,.09)}
[data-testid="stMetricLabel"]{color:#647d89!important;font-size:.85rem!important;font-weight:700!important;line-height:1.45}
[data-testid="stMetricValue"]{color:#08374b!important;font-family:Manrope,sans-serif!important;font-weight:800!important;font-size:clamp(1.3rem,2vw,1.83rem)!important;letter-spacing:-.045em!important}
[data-testid="stMetricDelta"]{font-size:.82rem!important;font-weight:600}
[data-testid="stTabs"]{background:transparent}
.stTabs [data-baseweb="tab-list"]{gap:7px;padding:8px 5px 12px;overflow-x:auto;border-bottom:1px solid #dce7ed}
.stTabs [data-baseweb="tab"]{border-radius:11px;background:#e8eff3;border:1px solid #dce7ed;color:#526e7d;font-size:.85rem;font-weight:750;padding:10px 15px;white-space:nowrap}
.stTabs [aria-selected="true"]{background:#fff!important;border-color:#c9dbe4!important;color:#06475f!important;box-shadow:0 3px 10px rgba(3,49,71,.06)}
.stTabs [aria-selected="true"]:after{background:var(--gold)!important;height:3px!important;border-radius:2px}
[data-testid="stFileUploader"]{background:#fff;border:1px solid #dce7ed;border-radius:16px;padding:14px}
[data-testid="stFileUploaderDropzone"]{background:#f5f9fb;border:2px dashed #9cbecb;border-radius:12px}
[data-testid="stDataFrame"]{border:1px solid #dbe7ec;border-radius:13px;overflow:hidden;box-shadow:0 3px 15px rgba(7,48,69,.03)}
[data-testid="stAlert"]{border-radius:13px!important;border:1px solid #dbe7ec}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:#064d65!important;border:1px solid #064d65!important;color:white!important;border-radius:11px!important;font-weight:750!important;min-height:44px}
.stButton>button,.stDownloadButton>button{border-radius:11px!important;font-weight:700!important}
[data-testid="stSelectbox"],[data-testid="stDateInput"]{border-radius:10px}
[data-testid="stExpander"]{background:#fff;border:1px solid #dce7ed;border-radius:13px}
[data-testid="stVerticalBlock"]>div:has(> [data-testid="stMetric"]){min-width:0}
[data-testid="stCaptionContainer"]{color:#6a8190}
@media(max-width:800px){.block-container{padding:1rem .85rem 3rem!important}.hero{padding:26px 23px;border-radius:16px}.hero:after{opacity:.35}.hero h1{font-size:1.75rem!important}[data-testid="stMetric"]{min-height:116px;padding:16px}}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">YUHMAK HOGAR / INTELIGENCIA DE GESTIÓN</div><h1>Postventa · Depósito 055</h1><p>Resultados de recuperación, stock, Service y movimientos entre sucursales. Una lectura clara de la gestión para tomar decisiones.</p><span class="hero-tag">● TABLERO EJECUTIVO &nbsp;·&nbsp; SAP</span></div>',unsafe_allow_html=True)

def section(name):
 st.markdown(f'<div class="section-eyebrow">{name}</div>',unsafe_allow_html=True)
def note(text):
 st.markdown(f'<div class="note-panel">{text}</div>',unsafe_allow_html=True)

def money(x): return '—' if x is None else '$ '+f'{x:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def qty(x):return f'{int(round(x)):,}'.replace(',','.')
def numeric(s):return pd.to_numeric(s,errors='coerce').fillna(0)
def ids(s):return s.astype('string').str.strip().str.replace(r'\.0$','',regex=True).replace({'':'', 'nan':''}).fillna('')
def date_col(s):return pd.to_datetime(s,errors='coerce',dayfirst=True)
def read_excel(blob):return pd.read_excel(io.BytesIO(blob),sheet_name=0)
def make_fig(labels,vals,title,ylabel='Unidades'):
 fig,ax=plt.subplots(figsize=(8.5,3.3));bars=ax.bar(labels,vals,color=[NAVY,'#d8a700','#377b8f','#92aab4'][:len(labels)])
 ax.set_title(title,loc='left',fontweight='bold',color=NAVY,pad=16);ax.set_ylabel(ylabel);ax.spines[['top','right']].set_visible(False)
 for b in bars:ax.annotate(f'{b.get_height():,.0f}',(b.get_x()+b.get_width()/2,b.get_height()),ha='center',va='bottom',fontsize=10)
 fig.tight_layout();return fig

def compute(d):
 stock,out,back,nc=(d[k].copy() for k in SOURCES)
 required={'stock':['Stock','Stock Valorizado'],'out':['Almacén destino','Estado','Cantidad','Precio','Código artículo'],'back':['Almacén destino','Estado','Cantidad','Precio','Código artículo'],'nc':['Nro Nota Crédito','Cantidad','Total (ML)','Estado Solicitud','Número de artículo']}
 for k,cols in required.items():
  missing=[c for c in cols if c not in d[k].columns]
  if missing:raise ValueError(f'{SOURCES[k]}: faltan columnas {", ".join(missing)}')
 su=numeric(stock['Stock']).sum();sv=numeric(stock['Stock Valorizado']).sum()
 # Closed transfers only, to the destination requested.
 sent=out[(out['Almacén destino'].astype(str).str.strip().str.upper()=='ZC109') & (out['Estado'].astype(str).str.contains('cerrad',case=False,na=False))].copy()
 ret=back[(back['Almacén destino'].astype(str).str.strip().str.upper()=='ZC055') & (back['Estado'].astype(str).str.contains('cerrad',case=False,na=False))].copy()
 for t in (sent,ret):
  t['_qty']=numeric(t['Cantidad']);t['_val']=numeric(t['Total líneas']) if 'Total líneas' in t else t['_qty']*numeric(t['Precio'])
  t['_sku']=t['Código artículo'].astype(str).str.strip().str.upper()
 sentqty=sent['_qty'].sum();retqty=ret['_qty'].sum();sentval=sent['_val'].sum();retval=ret['_val'].sum()
 s=sent.groupby('_sku')['_qty'].sum();r=ret.groupby('_sku')['_qty'].sum();q=(s-r.reindex(s.index,fill_value=0)).clip(lower=0)
 # Cost of unmatched quantities estimated at weighted average price of outbound lines per SKU.
 per=sent.groupby('_sku').agg(qty=('_qty','sum'),value=('_val','sum'))
 per['unit_cost']=per['value']/per['qty'].replace(0,float('nan'))
 pending_cost=float((q*per['unit_cost'].fillna(0)).sum())
 unmatched_return=(r-s.reindex(r.index,fill_value=0)).clip(lower=0)
 # Clasificación exclusiva por línea de solicitud y producto: NC > retorno físico > pendiente.
 n=nc.copy()
 for c in ['Nro Solicitud','Nro Devolución','Nro Nota Crédito','Estado Solicitud','Estado Devolución']:
  if c not in n.columns:raise ValueError(f'Notas de crédito: falta columna {c}')
 n['_sol']=ids(n['Nro Solicitud']);n['_dev']=ids(n['Nro Devolución']);n['_nc']=ids(n['Nro Nota Crédito'])
 n['_qty']=numeric(n['Cantidad']);n['_val']=numeric(n['Total (ML)'])
 n['_estado_sol']=n['Estado Solicitud'].astype('string').fillna('').str.strip().str.lower()
 n['_estado_dev']=n['Estado Devolución'].astype('string').fillna('').str.strip().str.lower()
 # Excluir filas idénticas de exportación, pero preservar líneas distintas de un mismo artículo.
 # Duplicados potenciales con igual solicitud/artículo/cantidad/importe se informan, no se eliminan automáticamente.
 n['_cancel']=n['_estado_sol'].str.contains('cancel|anulad',regex=True)
 n['_open_sol']=n['_estado_sol'].str.contains('abiert',regex=True)
 n['_closed_sol']=n['_estado_sol'].str.contains('cerrad',regex=True)
 n['_hasdev']=(n['_dev'].notna() & n['_dev'].ne('')).fillna(False).astype(bool)
 n['_hasnc']=(n['_nc'].notna() & n['_nc'].ne('')).fillna(False).astype(bool)
 n['_tipo']='Sin clasificación adicional'
 n.loc[n['_cancel'],'_tipo']='Cancelada'
 n.loc[~n['_cancel'] & n['_open_sol'],'_tipo']='Pendiente de envío'
 active=~n['_cancel'] & n['_closed_sol']
 n.loc[active & n['_hasdev'] & n['_estado_dev'].str.contains('abiert') & ~n['_hasnc'],'_tipo']='Pendiente proveedor'
 n.loc[active & n['_hasdev'] & n['_estado_dev'].str.contains('cerrad') & ~n['_hasnc'],'_tipo']='Producto retornado'
 # Criterio confirmado por responsable de Postventa: solicitudes sin NC ni devolución
 # registradas en esta exportación corresponden a productos nuevos/reparados recuperados.
 # La clasificación es una regla de negocio declarada, no evidencia documental de SAP.
 n.loc[active & ~n['_hasnc'] & ~n['_hasdev'],'_tipo']='Producto retornado'
 n.loc[active & n['_hasnc'],'_tipo']='NC recuperada'
 # Una NC con estado de devolución abierto sigue siendo NC recuperada (prioridad del número de NC).
 # Para no contar una solicitud de varios renglones como varios documentos, contar ID de solicitud único.
 def bucket(t):
  v=n[n['_tipo'].eq(t)]
  return {'solicitudes':int(v.loc[v['_sol'].notna() & v['_sol'].ne(''),'_sol'].nunique()),'unidades':float(v['_qty'].sum()),'valor':float(v['_val'].sum()),'lineas':len(v)}
 grupos={k:bucket(k) for k in ['Cancelada','Pendiente de envío','Pendiente proveedor','Producto retornado','NC recuperada','Sin clasificación adicional']}
 issued=n[n['_tipo'].eq('NC recuperada')].copy()
 physical=n[n['_tipo'].eq('Producto retornado')].copy()
 pending=n[n['_tipo'].eq('Pendiente proveedor')].copy()
 cancel=n[n['_tipo'].eq('Cancelada')].copy()
 nc_count=int(issued['_nc'].nunique());nc_qty=grupos['NC recuperada']['unidades'];nc_val=grupos['NC recuperada']['valor']
 physical_qty=grupos['Producto retornado']['unidades'];physical_val=grupos['Producto retornado']['valor']
 pending_nc_units=grupos['Pendiente proveedor']['unidades'];pending_nc_value=grupos['Pendiente proveedor']['valor']
 pending_send_units=grupos['Pendiente de envío']['unidades'];pending_send_value=grupos['Pendiente de envío']['valor']
 cancel_nc_units=grupos['Cancelada']['unidades'];cancel_nc_value=grupos['Cancelada']['valor']
 # Los retornos de Service son otra línea de gestión y NO se agregan a recuperación de proveedor.
 recovered_provider=nc_val+physical_val
 # Solicitudes mixtas pueden tener renglones en más de un estado.
 valid=n[~n['_cancel']]
 solicitudes_validas=int(valid.loc[valid['_sol'].notna() & valid['_sol'].ne(''),'_sol'].nunique())
 solicitudes_total=int(n.loc[n['_sol'].notna() & n['_sol'].ne(''),'_sol'].nunique())
 duplicados=int(n.duplicated(subset=['Nro Solicitud','Número de artículo','Cantidad','Total (ML)','Nro Devolución','Nro Nota Crédito'],keep=False).sum())
 # Dates indicate latest underlying transaction, NOT stock snapshot date.
 dates=[]
 for frame,col in ((out,'Fecha'),(back,'Fecha'),(nc,'Fecha Nota Crédito'),(nc,'Fecha Solicitud')):
  if col in frame:
   v=date_col(frame[col]).max()
   if pd.notna(v):dates.append(v)
 return dict(stock_units=float(su),stock_value=float(sv),sent_units=float(sentqty),sent_value=float(sentval),returned_units=float(retqty),returned_value=float(retval),net_units=float(sentqty-retqty),unmatched_units=float(q.sum()),unmatched_value=pending_cost,unmatched_returns=float(unmatched_return.sum()),nc_count=nc_count,nc_units=nc_qty,nc_value=nc_val,pending_nc_units=pending_nc_units,pending_nc_value=pending_nc_value,pending_send_units=pending_send_units,pending_send_value=pending_send_value,cancel_nc_units=cancel_nc_units,cancel_nc_value=cancel_nc_value,physical_units=physical_qty,physical_value=physical_val,recovered_provider=recovered_provider,grupos=grupos,solicitudes_validas=solicitudes_validas,solicitudes_total=solicitudes_total,duplicados_posibles=duplicados,recovered=float(recovered_provider),last_transaction=max(dates).strftime('%d/%m/%Y') if dates else 'No disponible',sent=sent,ret=ret,issued=issued,unmatched_detail=pd.DataFrame({'Artículo':q.index,'Unidades por conciliar':q.values,'Valor estimado':(q*per['unit_cost'].fillna(0)).values}).query('`Unidades por conciliar` > 0').sort_values('Valor estimado',ascending=False))

def temporal_tables(d, year):
    """Cohorts are not confused with realized transaction dates."""
    nc=d['nc'].copy()
    nc['_sol_state']=nc['Estado Solicitud'].astype('string').fillna('').str.strip().str.lower()
    nc['_dev_state']=nc['Estado Devolución'].astype('string').fillna('').str.strip().str.lower()
    nc['_nc_id']=ids(nc['Nro Nota Crédito'])
    nc['_dev_id']=ids(nc['Nro Devolución'])
    nc['_sol_date']=date_col(nc['Fecha Solicitud'])
    nc['_nc_date']=date_col(nc['Fecha Nota Crédito'])
    nc['_qty']=numeric(nc['Cantidad']);nc['_value']=numeric(nc['Total (ML)'])
    canceled=nc['_sol_state'].str.contains('cancel|anulad',na=False).fillna(False).astype(bool)
    closed=nc['_sol_state'].str.contains('cerrad',na=False).fillna(False).astype(bool)
    has_nc=(nc['_nc_id'].notna() & nc['_nc_id'].ne('')).fillna(False).astype(bool)
    physical=(~canceled & closed & ~has_nc & (nc['_dev_state'].str.contains('cerrad',na=False) | nc['_dev_id'].isna() | nc['_dev_id'].eq('').fillna(False))).fillna(False).astype(bool)
    pending=(~canceled & closed & ~has_nc & nc['_dev_state'].str.contains('abiert',na=False) & nc['_dev_id'].notna() & nc['_dev_id'].ne('').fillna(False)).fillna(False).astype(bool)
    issued=nc[~canceled & closed & has_nc & nc['_nc_date'].dt.year.eq(year)].copy()
    ph=nc[physical & nc['_sol_date'].dt.year.eq(year)].copy()
    pend=nc[pending & nc['_sol_date'].dt.year.eq(year)].copy()
    months=pd.DataFrame({'Mes':range(1,13)})
    for frame,datefield,prefix in [(issued,'_nc_date','NC emitidas'),(ph,'_sol_date','Retornos físicos · cohorte'),(pend,'_sol_date','Pendientes NC · cohorte')]:
        frame=frame.copy();frame['Mes']=frame[datefield].dt.month
        agg=frame.groupby('Mes').agg(unidades=('_qty','sum'),valor=('_value','sum')).reset_index()
        months=months.merge(agg.rename(columns={'unidades':prefix+' (u)','valor':prefix+' ($)'}),on='Mes',how='left')
    for key,label in [('out','Service enviados'),('back','Service retornados')]:
        t=d[key].copy()
        target='ZC109' if key=='out' else 'ZC055'
        t=t[t['Almacén destino'].astype(str).str.strip().str.upper().eq(target) & t['Estado'].astype(str).str.contains('cerrad',case=False,na=False)].copy()
        t['_date']=date_col(t['Fecha']);t=t[t['_date'].dt.year.eq(year)]
        t['Mes']=t['_date'].dt.month;t['_qty']=numeric(t['Cantidad'])
        t['_val']=numeric(t['Total líneas']) if 'Total líneas' in t else t['_qty']*numeric(t['Precio'])
        agg=t.groupby('Mes').agg(unidades=('_qty','sum'),valor=('_val','sum')).reset_index()
        months=months.merge(agg.rename(columns={'unidades':label+' (u)','valor':label+' ($)'}),on='Mes',how='left')
    months=months.fillna(0)
    months['Cuatrimestre']=((months['Mes']-1)//4+1).map({1:'1.º (ene–abr)',2:'2.º (may–ago)',3:'3.º (sep–dic)'})
    return months

def pdf(m,refdate):
 buffer=io.BytesIO();doc=SimpleDocTemplate(buffer,pagesize=(21*cm,29.7*cm),rightMargin=1.7*cm,leftMargin=1.7*cm,topMargin=1.7*cm,bottomMargin=1.5*cm)
 ss=getSampleStyleSheet();ss.add(ParagraphStyle(name='YTitle',parent=ss['Title'],textColor=colors.HexColor(NAVY),fontSize=19,spaceAfter=12));ss.add(ParagraphStyle(name='YHead',parent=ss['Heading2'],textColor=colors.HexColor(NAVY),fontSize=13,spaceBefore=10,spaceAfter=8));ss.add(ParagraphStyle(name='YSmall',parent=ss['Normal'],fontSize=8.5,leading=12))
 flow=[]
 def p(s,sty='Normal'):flow.append(Paragraph(str(s),ss[sty]));flow.append(Spacer(1,7))
 def table(rows):
  t=Table([[Paragraph(str(c),ss['YSmall']) for c in row] for row in rows],colWidths=[8.4*cm,4.2*cm,4.7*cm],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#edf3f5')]),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,-1),(-1,-1),.6,colors.HexColor('#ccd9df'))]));flow.append(t)
 p('Informe de gestión — Postventa 055','YTitle');p(f'Fecha de stock informada: {refdate} · Informe generado: {datetime.now():%d/%m/%Y %H:%M}','YSmall')
 p('1. Cantidades y valores','YHead')
 table([['Indicador','Cantidad','Importe'],['Stock inicial histórico','900 unidades','No disponible'],['Stock actual',qty(m['stock_units'])+' unidades',money(m['stock_value'])],['Reducción neta de stock',qty(900-m['stock_units'])+' unidades','—'],['Notas de crédito emitidas',f"{m['nc_count']} NC / {qty(m['nc_units'])} unidades",money(m['nc_value'])],['Service: salidas 055 → 109',qty(m['sent_units'])+' unidades',money(m['sent_value'])],['Service: retornos 109 → 055',qty(m['returned_units'])+' unidades',money(m['returned_value'])],['Retorno físico de proveedor (sin NC)',qty(m['physical_units'])+' unidades',money(m['physical_value'])],['Pendientes de NC · remito abierto',qty(m['pending_nc_units'])+' unidades',money(m['pending_nc_value'])],['Pendientes de envío · solicitud abierta',qty(m['pending_send_units'])+' unidades',money(m['pending_send_value'])]])
 p('Las 900 unidades son una referencia histórica; la variación es neta y no equivale a unidades recuperadas.','YSmall')
 flow.append(PageBreak());p('2. Gráficos','YTitle')
 for labels,vals,title,y in [(['Inicio','Actual'],[900,m['stock_units']],'Stock en unidades','Unidades'),(['Enviadas','Retornadas'],[m['sent_units'],m['returned_units']],'Movimientos Service','Unidades'),(['NC','Retorno producto'],[m['nc_value']/1e6,m['physical_value']/1e6],'Recuperación de proveedor','Millones de pesos')]:
  fig=make_fig(labels,vals,title,y);img=io.BytesIO();fig.savefig(img,format='png',dpi=145,bbox_inches='tight');plt.close(fig);img.seek(0);flow.append(Image(img,width=16*cm,height=6.4*cm));flow.append(Spacer(1,12))
 flow.append(PageBreak());p('3. Resumen ejecutivo','YTitle')
 p(f"Stock actual: {qty(m['stock_units'])} unidades, valorizadas en {money(m['stock_value'])}. Respecto de las 900 unidades históricas, la variación neta es de {qty(900-m['stock_units'])} unidades.")
 p(f"Proveedor: {m['nc_count']} notas de crédito por {money(m['nc_value'])} y {qty(m['nc_units'])} unidades. Productos retornados sin NC: {qty(m['physical_units'])} unidades, valorizadas en {money(m['physical_value'])}. Pendientes con devolución abierta y sin NC: {qty(m['pending_nc_units'])} unidades, {money(m['pending_nc_value'])}.")
 p(f"Service: {qty(m['sent_units'])} unidades enviadas a ZC109 y {qty(m['returned_units'])} retornadas a ZC055. Diferencia neta: {qty(m['net_units'])} unidades. Pendiente por conciliar por código: {qty(m['unmatched_units'])} unidades, con valorización estimada de {money(m['unmatched_value'])}.")
 p(f"Recuperación del circuito de proveedores: {money(m['recovered_provider'])}, suma de NC y devoluciones cerradas sin NC. Service se presenta aparte: {money(m['returned_value'])} de retornos, sin sumarlo para evitar doble contabilización.")
 p('Regla de gestión: solicitudes abiertas = pendientes de envío; solicitudes cerradas con remito abierto y sin NC = pendientes de NC; NC documental tiene prioridad; devoluciones cerradas sin NC = recuperación física. Las solicitudes cerradas sin remito ni NC se tratan como recuperación física por criterio operativo confirmado, sin comprobante de remito.','YSmall')
 p('Control: el criterio anterior incluía erróneamente solicitudes abiertas entre las recuperaciones físicas. Se separan como pendientes de envío.','YSmall')
 p('Advertencias: el pendiente de Service se estima por código de artículo, no por número de serie ni solicitud original; puede incluir operaciones de períodos distintos. Las solicitudes de NC sin emisión pueden tener estados que requieran revisión. La fecha de stock debe informarse al cargar el archivo.','YSmall')
 doc.build(flow);return buffer.getvalue()

# Módulo integrado de movimientos intersucursales, independiente de los 4 archivos principales.
def movimientos_055(raw, precios_raw=None):
    df = pd.read_excel(io.BytesIO(raw))
    needed = {'TIPO','Fecha','Almacen Origen2','Nombre de almacén','Número de artículo','Cantidad'}
    if not needed.issubset(df.columns):
        raise ValueError('Faltan columnas de SAP: ' + ', '.join(sorted(needed-set(df.columns))))
    df = df.copy()
    df['TIPO'] = df['TIPO'].astype('string').str.strip().str.lower()
    df['_sucursal'] = pd.to_numeric(df['Almacen Origen2'],errors='coerce')
    df = df[df['TIPO'].isin(['ingresos','egresos']) & df['_sucursal'].notna() & ~df['_sucursal'].isin([55,109])].copy()
    # SAP exports Excel serial dates; pandas otherwise reads these as 1970 nanoseconds.
    raw_dates=df['Fecha']
    if pd.api.types.is_datetime64_any_dtype(raw_dates):
        df['_fecha']=pd.to_datetime(raw_dates,errors='coerce')
    else:
        serial=pd.to_numeric(raw_dates,errors='coerce')
        parsed=pd.to_datetime(raw_dates.where(serial.isna()),errors='coerce',dayfirst=True)
        converted=pd.to_datetime(serial.where(serial.between(20000,80000)),unit='D',origin='1899-12-30',errors='coerce')
        df['_fecha']=parsed.fillna(converted)
    df['_unidades'] = pd.to_numeric(df['Cantidad'],errors='coerce').fillna(0)
    df['_articulo'] = df['Número de artículo'].astype('string').str.strip()
    df['_nombre'] = df['Nombre de almacén'].astype('string').fillna('Sin nombre')
    df['_valor'] = pd.Series(float('nan'),index=df.index,dtype='float64')
    value_candidates = ['Stock Valorizado','Valor total','Importe total','Valorización','Valorizacion','Valor','Importe','Costo total']
    unit_candidates = ['Precio del inventario','Costo unitario','Precio unitario','Valor unitario']
    for col in value_candidates:
        if col in df.columns:
            df['_valor'] = pd.to_numeric(df[col],errors='coerce')
            break
    if df['_valor'].isna().all():
        for col in unit_candidates:
            if col in df.columns:
                df['_valor'] = pd.to_numeric(df[col],errors='coerce') * df['_unidades']
                break
    if precios_raw is not None:
        pr = pd.read_excel(io.BytesIO(precios_raw))
        code = next((c for c in ['Número de artículo','Codigo de articulo','Código de artículo','Artículo','Articulo','Codigo','Código'] if c in pr.columns),None)
        unit = next((c for c in ['Costo unitario','Precio unitario','Valor unitario','Costo','Precio','Valor'] if c in pr.columns),None)
        if not code or not unit:raise ValueError('La lista de valores debe tener una columna de código de artículo y otra de costo o valor unitario.')
        pr['_articulo'] = pr[code].astype('string').str.strip()
        pr['_costo'] = pd.to_numeric(pr[unit],errors='coerce')
        pr = pr.dropna(subset=['_articulo']).drop_duplicates('_articulo',keep='last')
        costs = df['_articulo'].map(pr.set_index('_articulo')['_costo'])
        df['_valor'] = df['_valor'].fillna(costs * df['_unidades'])
    return df

def grafico_ranking(ranking):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    d=ranking.head(12).iloc[::-1]
    if d.empty:return
    fig,ax=plt.subplots(figsize=(11,max(4.5,len(d)*.48)))
    bars=ax.barh([str(v)[:45] for v in d['Sucursal']],d['Unidades'],color='#0b607b',height=.68)
    ax.bar_label(bars,padding=5,fmt='%.0f')
    ax.set_xlim(0,max(d['Unidades'].max()*1.16,1))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel('Unidades enviadas al 055')
    ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    ax.spines[['top','right','left']].set_visible(False)
    fig.tight_layout();st.pyplot(fig,use_container_width=True);plt.close(fig)

def grafico_mensual(data,series,title,ylabel,money_axis=False):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import FuncFormatter,MaxNLocator
    t=data.set_index('Mes').reindex(range(1,13),fill_value=0)
    fig,ax=plt.subplots(figsize=(11,4.5))
    x=np.arange(12);w=.72/len(series)
    for j,(col,label) in enumerate(series):
        vals=pd.to_numeric(t[col],errors='coerce').fillna(0).to_numpy()
        ax.bar(x-.36+(j+.5)*w,vals,width=w*.92,label=label,color=['#0b607b','#e3a824'][j%2])
    ax.set_xticks(x,['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'])
    ax.set_xlim(-.6,11.6);ax.set_title(title,loc='left',fontweight='bold',pad=14);ax.set_ylabel(ylabel)
    if money_axis:ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'${v/1e6:,.0f} M'))
    else:ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)
    if len(series)>1:ax.legend(frameon=False,ncol=2)
    fig.tight_layout();st.pyplot(fig,use_container_width=True);plt.close(fig)

def vista_movimientos():
    section('Ingresos y egresos · Depósito 055')
    st.caption('Movimientos entre sucursales. Se excluyen 055 y 109; el circuito Service continúa separado.')
    st.caption('El Excel de movimientos se incorpora junto con los otros cuatro en la carga única al inicio del tablero.')
    if not (DATA/'movimientos_055.xlsx').exists():
        st.info('Cargá el Excel de ingresos y egresos para ver este reporte.')
        return
    with st.expander('Valorización · opcional, cuando SAP habilite los costos'):
        st.caption('Podés cargar un reporte de movimientos con columna Valor total / Importe total / Costo unitario, o una lista de precios con código de artículo y costo unitario. Sin estos datos se muestran cantidades y el valor queda sin informar.')
        pf=st.file_uploader('Lista de costos por artículo (opcional)',type=['xlsx'],key='precios_055_upload')
        if pf is not None:
            (DATA/'precios_055.xlsx').write_bytes(pf.getvalue())
            st.success('Lista de costos guardada.')
        if (DATA/'precios_055.xlsx').exists() and st.button('Quitar lista de costos guardada'):
            (DATA/'precios_055.xlsx').unlink();st.rerun()
    try:
        raw=(DATA/'movimientos_055.xlsx').read_bytes()
        pr=(DATA/'precios_055.xlsx').read_bytes() if (DATA/'precios_055.xlsx').exists() else None
        df=movimientos_055(raw,pr)
    except Exception as exc:
        st.error('No se pudo interpretar el archivo: '+str(exc));return
    if df.empty:
        st.warning('No se encontraron movimientos entre el 055 y otras sucursales diferentes de 109.');return
    valid_dates=int(df['_fecha'].notna().sum())
    if valid_dates == 0:
        st.error('No se pudo interpretar ninguna fecha del Excel de movimientos. No se generan gráficos con datos incorrectos.')
        return
    st.caption(f'Control de fechas SAP: {valid_dates:,} movimientos fechados entre {df["_fecha"].min():%d/%m/%Y} y {df["_fecha"].max():%d/%m/%Y}.')
    years=sorted(df['_fecha'].dropna().dt.year.unique().tolist(),reverse=True)
    year=st.selectbox('Año',years,key='movimientos_year') if years else None
    d=df[df['_fecha'].dt.year.eq(year)].copy() if year else df.copy()
    options=['Todo el año','Enero–abril','Mayo–agosto','Septiembre–diciembre']
    scope=st.selectbox('Período',options,key='movimientos_scope')
    if scope!='Todo el año':
        a,b={'Enero–abril':(1,4),'Mayo–agosto':(5,8),'Septiembre–diciembre':(9,12)}[scope]
        d=d[d['_fecha'].dt.month.between(a,b)]
    i=d[d['TIPO'].eq('ingresos')];e=d[d['TIPO'].eq('egresos')]
    uin=i['_unidades'].sum();uout=e['_unidades'].sum()
    st.markdown('**Resultados del período**')
    c1,c2,c3=st.columns(3)
    c1.metric('Ingresos al 055',qty(uin)+' unidades')
    c2.metric('Egresos del 055',qty(uout)+' unidades')
    c3.metric('Balance de movimientos',f'{uin-uout:+,.0f}'.replace(',','.')+' unidades')
    def value_text(x):return money(x['_valor'].sum()) if len(x) and x['_valor'].notna().all() else 'Sin valorizar'
    c1,c2=st.columns(2)
    c1.metric('Valorización de ingresos',value_text(i))
    c2.metric('Valorización de egresos',value_text(e))
    missing=int(d['_valor'].isna().sum())
    if missing:
        st.info(f'Valorización pendiente: {missing} movimientos sin importe. Las cantidades son válidas; no se estiman precios ni se muestra un total económico incompleto.')
    section('Ranking de sucursales que enviaron mercadería al 055')
    ranking=i.groupby(['_sucursal','_nombre'],dropna=False).agg(Unidades=('_unidades','sum'),Valor=('_valor','sum'),Filas_valorizadas=('_valor','count'),Movimientos=('_unidades','count')).reset_index()
    ranking=ranking.sort_values('Unidades',ascending=False)
    ranking['Participación %']=ranking['Unidades'].div(uin).mul(100).round(1) if uin else 0
    ranking['Sucursal']=ranking['_sucursal'].astype('Int64').astype(str)+' · '+ranking['_nombre'].astype(str)
    ranking['Valorización ($)']=ranking['Valor'].where(ranking['Filas_valorizadas'].eq(ranking['Movimientos']))
    st.dataframe(ranking[['Sucursal','Unidades','Participación %','Valorización ($)']],hide_index=True,use_container_width=True,column_config={'Valorización ($)':st.column_config.NumberColumn('Valorización ($)',format='$ %.2f'),'Participación %':st.column_config.NumberColumn('Participación %',format='%.1f %%')})
    if not ranking.empty:grafico_ranking(ranking)
    section('Evolución mensual y cuatrimestral')
    d['_mes']=d['_fecha'].dt.month
    monthly=d.pivot_table(index='_mes',columns='TIPO',values='_unidades',aggfunc='sum',fill_value=0).reindex(range(1,13),fill_value=0)
    monthly=monthly.reindex(columns=['ingresos','egresos'],fill_value=0)
    monthly.index.name='Mes'
    grafico_mensual(monthly.reset_index(),[('ingresos','Ingresos'),('egresos','Egresos')],'Movimientos mensuales · depósito 055','Unidades')
    base=df[df['_fecha'].dt.year.eq(year)].copy() if year else df.copy()
    base['Cuatrimestre']=base['_fecha'].dt.month.map(lambda m:'Ene–Abr' if m<=4 else ('May–Ago' if m<=8 else 'Sep–Dic'))
    q=base.pivot_table(index='Cuatrimestre',columns='TIPO',values='_unidades',aggfunc='sum',fill_value=0).reindex(['Ene–Abr','May–Ago','Sep–Dic'],fill_value=0).reindex(columns=['ingresos','egresos'],fill_value=0)
    q['Balance']=q['ingresos']-q['egresos']
    st.dataframe(q.rename(columns={'ingresos':'Ingresos (u)','egresos':'Egresos (u)'}),use_container_width=True)
    section('Lectura ejecutiva')
    leader=ranking.iloc[0] if not ranking.empty else None
    leadertext=f" La sucursal que más mercadería remitió fue {leader['Sucursal']}, con {qty(leader['Unidades'])} unidades ({leader['Participación %']:.1f}% de los ingresos)." if leader is not None else ''
    note(f"En el período seleccionado, el depósito 055 recibió <strong>{qty(uin)} unidades</strong> desde otras sucursales y envió <strong>{qty(uout)} unidades</strong>, con un balance de movimientos de <strong>{qty(uin-uout)} unidades</strong>.{leadertext} Este balance no representa la variación de stock, ya que existen otros movimientos de inventario.")
    st.download_button('Descargar ranking (CSV)',ranking[['Sucursal','Unidades','Participación %','Valorización ($)']].to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),file_name='Ranking_ingresos_055.csv',mime='text/csv')

# MODO DE PRUEBA CLOUD: NO ES UN PORTAL PRIVADO. NO CARGAR DATOS REALES.
# Archivos y consultas se guardan temporalmente y pueden desaparecer al reiniciar.
ADMIN_EMAIL='demo@yuhmak.com'
DB_PATH=DATA/'portal_demo.sqlite3'
def db_conn():
 c=sqlite3.connect(DB_PATH,timeout=20)
 c.execute('CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, section TEXT NOT NULL, period TEXT, question TEXT NOT NULL, answer TEXT, status TEXT NOT NULL DEFAULT "Pendiente", created_at TEXT NOT NULL, answered_at TEXT)')
 c.commit()
 return c
email=ADMIN_EMAIL
role='admin'
st.error('VERSIÓN DE PRUEBA PÚBLICA · SIN CONTROL DE ACCESO. NO CARGAR EXCEL DE SAP NI INFORMACIÓN CONFIDENCIAL.')
st.info('Solo para verificar que el tablero puede abrirse online. El almacenamiento de esta prueba es temporal.')
with st.sidebar:
 st.caption('PRUEBA CLOUD · SIN LOGIN')
 st.caption('Datos ficticios únicamente')
section('Consultas sobre el reporte')
with st.expander('¿Tenés una consulta sobre estos indicadores?',expanded=False):
 with st.form('form_consulta_v17'):
  section_name=st.selectbox('Sección del reporte',['Resumen ejecutivo','Recuperación y pendientes','Stock y Service','Evolución temporal','Ingresos y egresos','Detalle y PDF'])
  period_name=st.text_input('Período o dato consultado (opcional)',placeholder='Ej.: segundo cuatrimestre 2026')
  question=st.text_area('Escribí tu consulta',max_chars=3000)
  send=st.form_submit_button('Enviar consulta')
  if send:
   if len(question.strip())<10:st.warning('La consulta debe contener al menos 10 caracteres.')
   else:
    with db_conn() as conn:
     conn.execute('INSERT INTO queries(email,section,period,question,created_at) VALUES (?,?,?,?,?)',(email,section_name,period_name.strip(),question.strip(),datetime.now().isoformat(timespec='seconds')));conn.commit()
    st.success('Consulta registrada. El administrador podrá responderla desde el portal.')
with db_conn() as conn:
 own=pd.read_sql_query('SELECT id,section,period,question,answer,status,created_at FROM queries WHERE email=? ORDER BY id DESC',conn,params=(email,))
if not own.empty:
 with st.expander('Mis consultas y respuestas'):
  st.dataframe(own,hide_index=True,use_container_width=True)

section('01 / Carga de información')
st.caption('VERSIÓN V17 · PORTAL PRIVADO CON GOOGLE Y CONSULTAS')
st.subheader('Actualizar informe')
st.caption('Seleccioná juntos los cinco Excel de SAP. Se identifican por contenido, se validan y se actualizan todos los módulos en una sola operación.')
files=st.file_uploader('Arrastrá los 5 archivos Excel aquí',type=['xlsx'],accept_multiple_files=True) if role=='admin' else None
if role!='admin': st.info('Modo Gerencia: visualización y consultas. Solo el administrador puede actualizar los datos SAP.')
if files:
 mapping={};unknown=[];duplicates=[]
 for f in files:
  try:
   raw=f.getvalue()
   headers=set(str(c).strip() for c in pd.read_excel(io.BytesIO(raw),nrows=0).columns)
   if {'TIPO','Almacen Origen2','Nombre de almacén','Cantidad'}.issubset(headers):k='movimientos'
   elif {'Stock','Stock Valorizado'}.issubset(headers):k='stock'
   elif {'Nro Nota Crédito','Estado Solicitud','Nro Devolución'}.issubset(headers):k='nc'
   elif {'Almacén destino','Estado','Cantidad','Código artículo'}.issubset(headers):
    name=f.name.lower()
    if '109' in name:k='back'
    elif '055' in name:k='out'
    else:
     sample=pd.read_excel(io.BytesIO(raw),usecols=['Almacén destino'],nrows=100)
     destinations=sample['Almacén destino'].astype(str).str.upper()
     k='back' if destinations.eq('ZC055').sum()>destinations.eq('ZC109').sum() else 'out'
   else:unknown.append(f.name);continue
   if k in mapping:duplicates.append(f.name)
   mapping[k]=raw
  except Exception as exc:unknown.append(f'{f.name} ({exc})')
 if unknown:st.warning('Archivos no reconocidos: '+', '.join(unknown))
 if duplicates:st.warning('Archivos duplicados para una misma categoría: '+', '.join(duplicates)+'. Revisá la selección.')
 names={'stock':'Stock 055','out':'Traslados 055 → 109','back':'Traslados 109 → 055','nc':'Notas de crédito y devoluciones','movimientos':'Ingresos y egresos 055'}
 st.caption('Identificados: '+', '.join(names[k] for k in mapping))
 missing=[names[k] for k in names if k not in mapping]
 if not missing and not duplicates and not unknown and len(files)==5:
  if st.button('Actualizar tablero completo · 5 archivos',type='primary',use_container_width=True):
   try:
    checks={k:read_excel(v) for k,v in mapping.items() if k!='movimientos'}
    compute(checks)
    moves=movimientos_055(mapping['movimientos'])
    if moves.empty:raise ValueError('El archivo de movimientos no contiene traslados válidos.')
    for k,raw in mapping.items():
     target='movimientos_055.xlsx' if k=='movimientos' else k+'.xlsx'
     (DATA/target).write_bytes(raw)
    (DATA/'actualizacion.json').write_text(json.dumps({'uploaded':datetime.now().isoformat(),'filenames':{k:next((f.name for f in files if f.getvalue()==v),names[k]) for k,v in mapping.items()}}),encoding='utf-8')
    st.rerun()
   except Exception as exc:st.error('No se actualizaron los datos: '+str(exc))
 else:
  st.info('Para actualizar, seleccioná exactamente los cinco reportes. Faltan: '+(', '.join(missing) if missing else 'ninguno')+'.')

if all((DATA/(k+'.xlsx')).exists() for k in SOURCES) and (DATA/'movimientos_055.xlsx').exists():
 try:
  dfs={k:read_excel((DATA/(k+'.xlsx')).read_bytes()) for k in SOURCES};m=compute(dfs)
 except Exception as e:st.error(f'No se pudo procesar la información: {e}');st.stop()
 meta=json.loads((DATA/'actualizacion.json').read_text(encoding='utf-8')) if (DATA/'actualizacion.json').exists() else {}
 st.success('Datos SAP disponibles · Última actualización: '+meta.get('uploaded','Sin registro')[:16].replace('T',' ')+' · Información publicada para usuarios autorizados',icon='✅')
 with st.expander('Fecha de corte y datos del informe',expanded=False):
  stockdate=st.date_input('Fecha de corte del stock (según SAP)',value=datetime.today().date(),help='Ingresá la fecha real del archivo de stock.')
 tabs=st.tabs(['Resumen ejecutivo','Recuperación y pendientes','Stock y Service','Evolución temporal','Ingresos y egresos','Detalle y PDF'])
 with tabs[0]:
  section('Indicadores principales')
  x,y,z=st.columns(3)
  x.metric('Recuperación total · proveedores',money(m['recovered_provider']))
  y.metric('Unidades recuperadas',qty(m['nc_units']+m['physical_units']))
  z.metric('Pendiente de NC',money(m['pending_nc_value']))
  x,y,z=st.columns(3)
  x.metric('Stock actual',qty(m['stock_units'])+' unidades')
  y.metric('Reducción neta de stock',qty(900-m['stock_units'])+' unidades',f'{(1-m["stock_units"]/900)*100:.1f}% del stock inicial',delta_color='off')
  z.metric('Pendiente de envío',qty(m['pending_send_units'])+' unidades')
  section('Lectura ejecutiva de la gestión')
  note(f"""<strong>Recuperación:</strong> se registraron <strong>{qty(m['nc_units']+m['physical_units'])} unidades</strong> recuperadas de proveedores, por <strong>{money(m['recovered_provider'])}</strong>. De ese total, {qty(m['nc_units'])} unidades corresponden a notas de crédito ({money(m['nc_value'])}) y {qty(m['physical_units'])} a productos nuevos o reparados ({money(m['physical_value'])}).<br><strong>Gestiones pendientes:</strong> permanecen {qty(m['pending_nc_units'])} unidades con remito abierto y sin NC, por {money(m['pending_nc_value'])}. Otras {qty(m['pending_send_units'])} unidades tienen solicitud abierta y todavía no salieron.<br><strong>Stock:</strong> el depósito registra {qty(m['stock_units'])} unidades frente a la referencia histórica de 900; la reducción neta no equivale necesariamente a mercadería recuperada.""")
  section('Composición económica de la recuperación')
  st.bar_chart(pd.DataFrame({'Importe ARS':[m['nc_value'],m['physical_value']]},index=['Notas de crédito','Producto nuevo/reparado']),horizontal=True,color='#0b607b')
  st.caption('Los retornos de Service se informan aparte: no se suman al recuperado de proveedores para evitar duplicaciones.')
 with tabs[1]:
  section('Resultados por vía de recuperación')
  x,y=st.columns(2)
  x.metric('Notas de crédito',money(m['nc_value']),qty(m['nc_units'])+' unidades')
  y.metric('Productos nuevos / reparados',money(m['physical_value']),qty(m['physical_units'])+' unidades')
  section('Pendientes y estado de solicitudes')
  x,y=st.columns(2)
  x.metric('Remitos abiertos · falta NC',qty(m['pending_nc_units'])+' unidades',money(m['pending_nc_value']))
  y.metric('Solicitudes abiertas · sin envío',qty(m['pending_send_units'])+' unidades',money(m['pending_send_value']))
  table=[]
  for name,key in [('Recuperado mediante NC','NC recuperada'),('Recuperado con producto nuevo o reparado','Producto retornado'),('Pendiente de NC','Pendiente proveedor'),('Pendiente de envío','Pendiente de envío'),('Cancelada','Cancelada'),('Otros / revisar','Sin clasificación adicional')]:
   v=m['grupos'][key];table.append({'Estado':name,'Solicitudes':int(v['solicitudes']),'Unidades':int(v['unidades']),'Importe ($)':float(v['valor'])})
  st.dataframe(pd.DataFrame(table),hide_index=True,use_container_width=True,column_config={'Importe ($)':st.column_config.NumberColumn('Importe ($)',format='$ %.2f')})
  st.caption('Prioridad: NC documental > recuperación física > pendiente. Solicitud abierta = no enviada. Los retornos sin remito ni NC se reconocen por el criterio operativo confirmado.')
  if m['duplicados_posibles']:st.warning(f"Existen {m['duplicados_posibles']} renglones potencialmente duplicados; verificar antes de un cierre definitivo.")
 with tabs[2]:
  section('Stock · fotografía actual')
  x,y,z=st.columns(3)
  x.metric('Referencia histórica', '900 unidades')
  y.metric('Stock actual',qty(m['stock_units'])+' unidades')
  z.metric('Valorización actual',money(m['stock_value']))
  st.bar_chart(pd.DataFrame({'Unidades':[900,m['stock_units']]},index=['Stock inicial histórico','Stock actual']),horizontal=True,color='#0b607b')
  st.caption('El archivo actual no permite reconstruir el stock al cierre de cada mes. Se necesitan cortes históricos para esa evolución.')
  section('Service · movimientos entre depósitos')
  x,y,z=st.columns(3)
  x.metric('Enviadas 055 → 109',qty(m['sent_units'])+' unidades')
  y.metric('Retornadas 109 → 055',qty(m['returned_units'])+' unidades')
  z.metric('Diferencia neta',qty(m['net_units'])+' unidades')
  x,y=st.columns(2)
  x.metric('Valor de envíos',money(m['sent_value']))
  y.metric('Valor de retornos',money(m['returned_value']))
  st.info(f"Conciliación por código de artículo: {qty(m['unmatched_units'])} unidades sin correspondencia exacta, con valor estimado de {money(m['unmatched_value'])}. No equivale a un pendiente definitivo de Service.")
 with tabs[3]:
  section('Análisis mensual y cuatrimestral')
  st.caption('NC por fecha de emisión; Service por fecha de traslado. Retornos físicos y pendientes agrupados por fecha de solicitud (cohortes), no por fecha efectiva de retorno.')
  all_dates=[]
  for key,col in [('nc','Fecha Solicitud'),('nc','Fecha Nota Crédito'),('out','Fecha'),('back','Fecha')]:
   if col in dfs[key]:all_dates.extend(date_col(dfs[key][col]).dropna().dt.year.tolist())
  years=sorted(set(int(y) for y in all_dates if 2000<=y<=2100),reverse=True)
  selected_year=st.selectbox('Año a analizar',years if years else [datetime.today().year])
  tm=temporal_tables(dfs,selected_year)
  names={1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
  tm['Mes (nombre)']=tm['Mes'].map(names)
  numeric_cols=[v for v in tm.columns if v.endswith('(u)') or v.endswith('($)')]
  quart=tm.groupby('Cuatrimestre',sort=False)[numeric_cols].sum().reset_index()
  section('Comparación por cuatrimestre')
  st.dataframe(quart.style.format({k:'{:,.0f}' if k.endswith('(u)') else '${:,.2f}' for k in numeric_cols}),use_container_width=True,hide_index=True)
  section('Evolución mensual')
  x,y=st.columns(2)
  with x:
   st.markdown('**Notas de crédito emitidas · ARS**')
   grafico_mensual(tm,[('NC emitidas ($)','NC emitidas')],'Notas de crédito por mes','Importe en ARS',money_axis=True)
  with y:
   st.markdown('**Service · unidades enviadas y retornadas**')
   grafico_mensual(tm,[('Service enviados (u)','Enviados'),('Service retornados (u)','Retornados')],'Service por mes','Unidades')
  with st.expander('Ver detalle mensual completo y descargar datos'):
   st.dataframe(tm[['Mes (nombre)','Cuatrimestre']+numeric_cols].style.format({k:'{:,.0f}' if k.endswith('(u)') else '${:,.2f}' for k in numeric_cols}),use_container_width=True,hide_index=True)
   st.download_button('Descargar datos temporales (CSV)',tm.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),file_name=f'Postventa_055_Evolucion_{selected_year}.csv',mime='text/csv',use_container_width=True)
  section('Interpretación del período')
  q1,q2=quart.iloc[0],quart.iloc[1]
  diff=q2['NC emitidas ($)']-q1['NC emitidas ($)']
  note(f"""<strong>Notas de crédito:</strong> en el primer cuatrimestre se emitieron {money(q1['NC emitidas ($)'])}; en el segundo, {money(q2['NC emitidas ($)'])}. Variación: <strong>{money(diff)}</strong>.<br><strong>Service:</strong> envíos de {qty(q1['Service enviados (u)'])} a {qty(q2['Service enviados (u)'])} unidades; retornos de {qty(q1['Service retornados (u)'])} a {qty(q2['Service retornados (u)'])} unidades. Las diferencias entre entradas y salidas no prueban pendientes definitivos.""")
  st.caption('Para comparar el stock histórico por mes o cuatrimestre se requieren archivos de stock de cada cierre. Para asignar retornos físicos al mes real, se necesita fecha efectiva de retorno.')
 with tabs[4]:
  vista_movimientos()
 with tabs[5]:
  section('Auditoría y documentación')
  st.metric('Solicitudes registradas',qty(m['solicitudes_total']))
  st.metric('Notas de crédito documentadas',qty(m['nc_count']))
  st.markdown('**Detalle de artículos pendientes de conciliación de Service**')
  st.dataframe(m['unmatched_detail'],hide_index=True,use_container_width=True)
  st.warning('La diferencia por artículo en Service no equivale a pendientes definitivos. El stock histórico de 900 unidades es una referencia declarada.')
  try:
   st.download_button('Descargar informe ejecutivo PDF',pdf(m,stockdate.strftime('%d/%m/%Y')),file_name=f'Postventa_055_Informe_{datetime.now():%Y%m%d}.pdf',mime='application/pdf',type='primary',use_container_width=True)
  except Exception as e:st.error('No se pudo generar el PDF: '+str(e))

else:
 st.info('El administrador debe publicar los cinco Excel de SAP para generar el primer informe.')
 vista_movimientos()

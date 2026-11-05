import html
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
import executive_ui
BASE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('YUHMAK_DATA_DIR',str(BASE/'datos'))); DATA.mkdir(parents=True,exist_ok=True)
SOURCES={'stock':'STOCK 055','nc':'Notas de Credito 055'}
NAVY='#022f40'; GOLD='#ffc107'
st.markdown("""<style>
[data-testid="stSidebar"]{background:#022f40!important;} [data-testid="stSidebar"] *{color:#ffffff;} [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){background:#ffc107!important;border-radius:9px;padding:6px;} [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) *{color:#022f40!important;}
</style>""",unsafe_allow_html=True)
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

/* V18: cantidades y valorizaciones integradas en una misma tarjeta. */
.tarjeta-rotacion{background:#fff;border:1px solid #e0e9ee;border-radius:19px;
 padding:23px 25px 21px 29px;min-height:190px;box-shadow:0 6px 19px rgba(7,48,69,.045);
 position:relative;overflow:hidden;margin-bottom:8px}
.tarjeta-rotacion:before{content:'';position:absolute;top:0;left:0;bottom:0;
 width:5px;background:#ffc107}
.tarjeta-rotacion-titulo{font-size:15px;color:#597b8c;margin-bottom:8px}
.tarjeta-rotacion-cantidad{font-size:33px;font-weight:750;line-height:1.15;color:#022f40}
.tarjeta-rotacion-separador{height:1px;background:#e8eef2;margin:15px 0 10px}
.tarjeta-rotacion-leyenda{font-size:11px;font-weight:700;letter-spacing:.09em;color:#668394}
.tarjeta-rotacion-valor{font-size:21px;font-weight:750;line-height:1.4;color:#12485f}


/* V26: bloques amplios, jerarquía visual, sin tablas de datos apretadas */
.exec-heading{background:linear-gradient(115deg,#073747,#07536a);color:#fff;border-radius:20px;padding:36px 42px;margin:8px 0 34px}
.exec-heading .eyebrow{color:#ffd04b;font-size:12px;letter-spacing:.16em;font-weight:800}
.exec-heading h2{color:#fff!important;font-size:2rem!important;margin:12px 0 10px!important}
.exec-heading p{color:#d8eaf0;font-size:15px;margin:0}
.exec-spacer{height:32px}
.exec-table{background:white;border:1px solid #dce6eb;border-radius:16px;padding:13px 23px;margin:15px 0 10px;box-shadow:0 5px 18px rgba(0,35,55,.04)}
.exec-row{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:17px 0;border-bottom:1px solid #edf1f4;font-size:15px;color:#344e5d}
.exec-row:last-child{border-bottom:0;background:#f3f8fa;margin:0 -12px;padding:19px 12px;border-radius:10px}
.exec-row strong{font-size:18px;color:#063c50;white-space:nowrap;font-variant-numeric:tabular-nums}
.exec-row span{line-height:1.45}
@media(max-width:800px){.exec-heading{padding:25px 22px}.exec-row{font-size:13px}.exec-row strong{font-size:15px}}


/* V27 — portada ejecutiva tipo presentación, con texto nativo y adaptable */
.ceo-banner{background:#063747;color:white;border-radius:13px;padding:29px 35px;display:flex;justify-content:space-between;align-items:center;gap:25px;margin:7px 0 21px;box-shadow:0 5px 16px rgba(5,45,61,.12)}
.ceo-brand{color:#ffcf4b;font-weight:800;letter-spacing:.09em;font-size:13px;margin-bottom:8px}
.ceo-title{font-size:clamp(23px,2.4vw,37px);font-weight:800;line-height:1.2}
.ceo-subtitle{color:#d4e6ed;font-size:15px;margin-top:7px}
.ceo-period{font-size:13px;font-weight:800;white-space:nowrap;align-self:flex-start;margin-top:5px}
.ceo-intro{font-size:19px;font-weight:800;color:#08374b;margin:22px 0 23px}
.ceo-card{background:#f3f7f9;border:1px solid #dbe7ec;border-radius:17px;overflow:hidden;min-height:455px;box-shadow:0 5px 12px rgba(4,44,60,.08);display:flex;flex-direction:column;margin-bottom:14px}
.ceo-card-head{background:#0b5c70;color:white;font-weight:800;font-size:15px;letter-spacing:.025em;padding:17px 19px}
.ceo-card-body{padding:21px 20px 8px;flex:1}
.ceo-card-footer{padding:14px 20px 19px;color:#607885;font-size:12px;line-height:1.45}
.ceo-main{font-size:32px;font-weight:800;color:#063b50;line-height:1.25;margin:0 0 11px}
.ceo-main small{font-size:14px;font-weight:650}
.ceo-muted{color:#627a87;font-size:13px;line-height:1.55;margin-bottom:22px}
.ceo-amount{font-size:21px;font-weight:800;color:#0b536a;margin:0 0 23px}
.ceo-line{display:flex;justify-content:space-between;align-items:flex-start;gap:15px;border-top:1px solid #dce6eb;padding:14px 0;font-size:13px;color:#344f5b}
.ceo-line strong{color:#073d52;text-align:right;white-space:nowrap;font-size:14px}
.ceo-highlight{background:white;border:1px solid #dce7eb;border-radius:12px;margin-top:17px;padding:15px 16px;display:flex;flex-direction:column;gap:9px}
.ceo-highlight span{font-size:12px;color:#24556a;font-weight:800}
.ceo-highlight strong{font-size:21px;color:#073c50}
.ceo-section-title{color:#0b4356;font-weight:800;font-size:16px;letter-spacing:.02em;margin:28px 0 16px}
.ceo-step{background:white;border:1px solid #dce6eb;border-radius:13px;min-height:104px;padding:21px 12px;display:flex;flex-direction:column;text-align:center;justify-content:center;gap:9px;box-shadow:0 4px 12px rgba(5,45,61,.05)}
.ceo-step strong{font-size:14px;color:#06475c}.ceo-step span{font-size:12px;color:#637b87}
.ceo-footnote{background:#eef4f7;border:1px solid #dce7ec;border-radius:13px;padding:19px 24px;font-size:13px;line-height:1.75;color:#345465;margin:26px 0 24px}
@media(max-width:900px){.ceo-banner{padding:23px;flex-direction:column;align-items:flex-start}.ceo-card{min-height:unset}.ceo-main{font-size:27px}.ceo-line{flex-direction:column;gap:6px}.ceo-line strong{text-align:left}}

/* V28: lectura ejecutiva de alta visibilidad */
.ceo-card{min-height:510px;background:#fff;border:1px solid #cfe0e8;box-shadow:0 7px 20px rgba(2,47,64,.07)}
.ceo-card-head{background:#07556b;padding:19px 22px;font-size:16px}
.ceo-card-body{padding:25px 24px 12px}
.ceo-card-footer{font-size:13px;padding:16px 23px 22px}
.ceo-main{font-size:clamp(39px,3vw,51px);margin-bottom:13px}
.ceo-main small{font-size:16px}
.ceo-amount{font-size:clamp(23px,1.8vw,29px);margin-bottom:27px}
.ceo-muted{font-size:15px;margin-bottom:24px}
.ceo-line{font-size:15px;line-height:1.45;padding:18px 0;gap:18px}
.ceo-line strong{font-size:16px;white-space:normal;min-width:125px}
.ceo-highlight{padding:20px;margin-top:22px;background:#eaf5fa}
.ceo-highlight span{font-size:14px}
.ceo-highlight strong{font-size:clamp(23px,2vw,30px)}
.ceo-intro{font-size:22px;margin:26px 0}
.ceo-section-title{font-size:20px;margin:30px 0 18px}
.ceo-step{min-height:106px}
.v28-intro{margin:24px 0 18px;padding-left:14px;border-left:5px solid #ffc107;font-size:22px;font-weight:800;color:#063747}
.v28-chart-title{font-size:16px;font-weight:800;color:#06455a;margin:12px 0}
.v28-chart-note{font-size:13px;color:#58717e;line-height:1.6}
.v28-conclusion{background:#fff7e3;border:1px solid #f2d995;border-radius:16px;padding:22px 24px;margin:20px 0;color:#143d4f;line-height:1.8;font-size:15px}
@media(max-width:1000px){.ceo-card{min-height:unset}.ceo-main{font-size:39px}.ceo-line{flex-direction:column;gap:5px}}
</style>""",unsafe_allow_html=True)
# Encabezado ejecutivo integrado en la sección siguiente

def section(name):
 st.markdown(f'<div class="section-eyebrow">{name}</div>',unsafe_allow_html=True)
def note(text):
 st.markdown(f'<div class="note-panel">{text}</div>',unsafe_allow_html=True)

def money(x): return 'Sin valorizar' if x is None or pd.isna(x) else '$ '+f'{x:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
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

def normalizar_movimientos_sap(raw):
 """Compatibilidad con exportaciones SAP antiguas y valorizadas (V60)."""
 x=pd.read_excel(io.BytesIO(raw))
 aliases={'Fecha':'Fecha de contabilización','Número de artículo':'ItemCode','Cantidad':'Quantity',
          'Nombre de almacén':'WhsName','Descripción artículo/serv.':'Descripción artículo'}
 x=x.rename(columns={a:b for a,b in aliases.items() if a in x.columns and b not in x.columns})
 if 'Fecha de contabilización' in x:
  f=x['Fecha de contabilización']
  if pd.api.types.is_datetime64_any_dtype(f):
   x['Fecha de contabilización']=pd.to_datetime(f,errors='coerce')
  elif pd.api.types.is_numeric_dtype(f):
   x['Fecha de contabilización']=pd.to_datetime(f,unit='D',origin='1899-12-30',errors='coerce')
  else:
   parsed=pd.to_datetime(f,errors='coerce',dayfirst=True)
   serial=pd.to_numeric(f,errors='coerce')
   excel=pd.to_datetime(serial.where(serial.between(1,100000)),unit='D',origin='1899-12-30',errors='coerce')
   x['Fecha de contabilización']=parsed.fillna(excel)
 return x

def derivar_service_desde_movimientos(raw):
 """Operaciones realizadas: 055 -> 109 (egresos) y 109 -> 055 (ingresos).
 El archivo no permite recuperar solicitudes abiertas ni demostrar retorno por serie.
 """
 x=normalizar_movimientos_sap(raw)
 req={'TIPO','Almacen Origen','Almacen Origen2','Quantity','ItemCode','Fecha de contabilización'}
 if not req.issubset(x.columns):raise ValueError('Ingresos y egresos: faltan '+', '.join(sorted(req-set(x.columns))))
 x=x.copy();t=x['TIPO'].astype('string').str.strip().str.lower()
 origen=pd.to_numeric(x['Almacen Origen'],errors='coerce')
 otro=pd.to_numeric(x['Almacen Origen2'],errors='coerce')
 sent=x[t.eq('egresos') & origen.eq(55) & otro.eq(109)].copy()
 ret=x[t.eq('ingresos') & origen.eq(109)].copy()
 def make(z,target):
  return pd.DataFrame({'Almacén destino':target,'Estado':'Cerrado',
   'Cantidad':pd.to_numeric(z['Quantity'],errors='coerce').fillna(0).abs(),
   'Precio':float('nan'),'Código artículo':z['ItemCode'].astype('string').str.strip(),
   'Fecha':z['Fecha de contabilización']})
 return make(sent,'ZC109'),make(ret,'ZC055')

def compute(d):
 stock,nc=d['stock'].copy(),d['nc'].copy()
 out,back=d['out'].copy(),d['back'].copy()
 required={'stock':['Stock','Stock Valorizado'],'nc':['Nro Nota Crédito','Cantidad','Total (ML)','Estado Solicitud','Número de artículo']}
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
 sentqty=sent['_qty'].sum();retqty=ret['_qty'].sum();sentval=sent['_val'].sum(min_count=1);retval=ret['_val'].sum(min_count=1)
 s=sent.groupby('_sku')['_qty'].sum();r=ret.groupby('_sku')['_qty'].sum();q=(s-r.reindex(s.index,fill_value=0)).clip(lower=0)
 # Cost of unmatched quantities estimated at weighted average price of outbound lines per SKU.
 per=sent.groupby('_sku').agg(qty=('_qty','sum'),value=('_val','sum'))
 per['unit_cost']=per['value']/per['qty'].replace(0,float('nan'))
 pending_cost=float((q*per['unit_cost']).sum(min_count=1)) if per['unit_cost'].notna().any() else float('nan')
 unmatched_return=(r-s.reindex(r.index,fill_value=0)).clip(lower=0)
 # Clasificación exclusiva por línea de solicitud y producto: NC > retorno físico > pendiente.
 n=nc.copy()
 # Se utiliza toda la exportación SAP de solicitudes, sin filtro histórico por fecha.
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
 # Regla operativa confirmada: estado de SOLICITUD determina abiertas y canceladas.
 # Prioridad: cancelada > abierta > NC con número > restante (recuperación física).
 # Estado de devolución NO define pendientes en este reporte.
 n['_tipo']='Producto retornado'
 n.loc[n['_cancel'],'_tipo']='Cancelada'
 n.loc[~n['_cancel'] & n['_open_sol'],'_tipo']='Pendiente de envío'
 n.loc[~n['_cancel'] & ~n['_open_sol'] & n['_hasnc'],'_tipo']='NC recuperada'
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
 return dict(stock_units=float(su),stock_value=float(sv),sent_units=float(sentqty),sent_value=float(sentval),returned_units=float(retqty),returned_value=float(retval),net_units=float(sentqty-retqty),unmatched_units=float(q.sum()),unmatched_value=pending_cost,unmatched_returns=float(unmatched_return.sum()),nc_count=nc_count,nc_units=nc_qty,nc_value=nc_val,pending_nc_units=pending_nc_units,pending_nc_value=pending_nc_value,pending_send_units=pending_send_units,pending_send_value=pending_send_value,cancel_nc_units=cancel_nc_units,cancel_nc_value=cancel_nc_value,physical_units=physical_qty,physical_value=physical_val,recovered_provider=recovered_provider,grupos=grupos,solicitudes_validas=solicitudes_validas,solicitudes_total=solicitudes_total,duplicados_posibles=duplicados,recovered=float(recovered_provider),last_transaction=max(dates).strftime('%d/%m/%Y') if dates else 'No disponible',sent=sent,ret=ret,issued=issued,unmatched_detail=pd.DataFrame({'Artículo':q.index,'Unidades por conciliar':q.values,'Valor estimado':(q*per['unit_cost']).values}).query('`Unidades por conciliar` > 0').sort_values('Valor estimado',ascending=False))

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
 df=normalizar_movimientos_sap(raw)
 needed={'TIPO','Fecha de contabilización','Almacen Origen','Almacen Origen2','ItemCode','Quantity','WhsName'}
 if not needed.issubset(df.columns):raise ValueError('Ingresos y egresos: faltan '+', '.join(sorted(needed-set(df.columns))))
 df=df.copy();df['TIPO']=df['TIPO'].astype('string').str.strip().str.lower()
 origen=pd.to_numeric(df['Almacen Origen'],errors='coerce')
 otro=pd.to_numeric(df['Almacen Origen2'],errors='coerce')
 df['_sucursal']=origen.where(df['TIPO'].eq('ingresos'),otro)
 df=df[df['TIPO'].isin(['ingresos','egresos']) & df['_sucursal'].notna() & df['_sucursal'].ne(55) & (df['TIPO'].eq('egresos') | df['_sucursal'].ne(109))].copy()
 df['_fecha']=pd.to_datetime(df['Fecha de contabilización'],errors='coerce')
 df['_unidades']=pd.to_numeric(df['Quantity'],errors='coerce').fillna(0).abs()
 df['_articulo']=df['ItemCode'].astype('string').str.strip()
 df['_nombre']=df['WhsName'].astype('string').fillna('Sin nombre')
 def sap_num(series):
  txt=series.astype('string').str.strip().str.replace(r'[^0-9,.-]','',regex=True)
  both=txt.str.contains(',',regex=False) & txt.str.contains('.',regex=False)
  txt=txt.where(~both,txt.str.replace('.','',regex=False).str.replace(',','.',regex=False))
  txt=txt.where(~(txt.str.contains(',',regex=False)&~both),txt.str.replace(',','.',regex=False))
  return pd.to_numeric(txt,errors='coerce')
 if 'Stock Valorizado' in df.columns:
  df['_valor']=sap_num(df['Stock Valorizado']).abs()
 elif 'Precio del inventario' in df.columns:
  df['_valor']=sap_num(df['Precio del inventario']).abs()*df['_unidades']
 else:
  df['_valor']=pd.Series(float('nan'),index=df.index,dtype='float64')
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
    fig.tight_layout();st.pyplot(fig,width="stretch");plt.close(fig)

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
    fig.tight_layout();st.pyplot(fig,width="stretch");plt.close(fig)

def vista_movimientos():
    section('Ingresos y egresos · Depósito 055')
    st.caption('Movimientos entre sucursales, sin incluir el circuito 055–109. Importes tomados del costo de inventario SAP.')
    st.caption('Los movimientos se actualizan desde la carga única de cuatro Excel, en la parte superior.')
    if not (DATA/'movimientos_055.xlsx').exists():
        st.info('Cargá el Excel de ingresos y egresos para ver este reporte.')
        return
    with st.expander('Valorización SAP · información'):
        st.caption('Se utiliza Stock Valorizado del Excel de SAP; cuando falta se usa Precio del inventario × Cantidad. No se usan precios de venta.')
        if (DATA/'precios_055.xlsx').exists():
            try:
                cols=set(str(c).strip() for c in pd.read_excel(DATA/'precios_055.xlsx',nrows=0).columns)
                has_code=bool(cols.intersection({'Número de artículo','Codigo de articulo','Código de artículo','Artículo','Articulo','Codigo','Código'}))
                has_cost=bool(cols.intersection({'Costo unitario','Precio unitario','Valor unitario','Costo','Precio','Valor'}))
                if not (has_code and has_cost):
                    st.warning('La lista de costos guardada no tiene columnas compatibles. Se ignora para valorizar; los indicadores en unidades siguen funcionando.')
            except Exception:
                st.warning('La lista de costos guardada no se puede leer. Se ignora para valorizar.')
            if st.button('Quitar lista de costos guardada'):
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
    c1,c2=st.columns(2)
    c1.metric('Ingresos al 055',qty(uin)+' unidades')
    c2.metric('Egresos del 055',qty(uout)+' unidades')
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
    st.dataframe(ranking[['Sucursal','Unidades','Participación %','Valorización ($)']],hide_index=True,width="stretch",column_config={'Valorización ($)':st.column_config.NumberColumn('Valorización ($)',format='$ %.2f'),'Participación %':st.column_config.NumberColumn('Participación %',format='%.1f %%')})
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
    st.dataframe(q.rename(columns={'ingresos':'Ingresos (u)','egresos':'Egresos (u)'}),width="stretch")
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
# El tablero sigue sin autenticación. No cargar información confidencial en una URL pública.

# Informe CEO: lectura por secciones, sin imagen rasterizada.
def ceo_pesos(v):
 return '$ ' + f'{v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')

def executive_table(rows):
 htmlrows=''.join(f'<div class="exec-row"><span>{label}</span><strong>{value}</strong></div>' for label,value in rows)
 st.markdown('<div class="exec-table">'+htmlrows+'</div>',unsafe_allow_html=True)

# V27 — Informe ejecutivo construido en HTML/CSS nativo: no es imagen.
def executive_card(title, body, footer=''):
 st.markdown(f'<div class="ceo-card"><div class="ceo-card-head">{title}</div><div class="ceo-card-body">{body}</div><div class="ceo-card-footer">{footer}</div></div>',unsafe_allow_html=True)

# Los indicadores del CEO se calculan en cada ejecución desde los Excel guardados.
# No se presentan como auditadas conciliaciones que no puedan probarse con SAP.
def current_data():
    if not all((DATA/(k+'.xlsx')).exists() for k in SOURCES) or not (DATA/'movimientos_055.xlsx').exists():
        return None, None, None
    dfs={k:read_excel((DATA/(k+'.xlsx')).read_bytes()) for k in SOURCES}
    raw=(DATA/'movimientos_055.xlsx').read_bytes()
    dfs['out'],dfs['back']=derivar_service_desde_movimientos(raw)
    metrics=compute(dfs)
    prices=(DATA/'precios_055.xlsx').read_bytes() if (DATA/'precios_055.xlsx').exists() else None
    movements=movimientos_055(raw,prices)
    return metrics,movements,dfs

def carga_excel_sap():
 """Carga central de cuatro archivos. Valida todo antes de reemplazar. Protegida con clave Admin."""
 st.caption('Cargá los cuatro Excel juntos: Stock 055, Ingresos y egresos 055, Notas de crédito 055 y Ventas. No se requieren solicitudes de traslado.')
    
 # Acceso de pruebas: no usar contraseña fija en código.
 if 'admin_auth' not in st.session_state:st.session_state['admin_auth']=False
 pwd=st.text_input('Clave de Administrador',type='password',key='pwd_admin_input')
 expected=st.secrets.get('ADMIN_PASSWORD','')
 if pwd and expected and pwd==expected:st.session_state['admin_auth']=True
 elif pwd:st.error('Clave incorrecta');st.session_state['admin_auth']=False
 if not st.session_state['admin_auth']:
  st.info('Solo administradores pueden actualizar datos. Configurar ADMIN_PASSWORD en secretos de Streamlit.')
  return
 files=st.file_uploader('Seleccionar los 4 archivos Excel',type=['xlsx'],accept_multiple_files=True,key='carga_cuatro_v59')
 names={'stock':'Stock 055','movimientos':'Ingresos y egresos 055','nc':'Notas de crédito 055','ventas':'Reporte de ventas'}
 if not files:
  saved=sum((DATA/({'movimientos':'movimientos_055.xlsx','ventas':'ventas_totales.xlsx'}.get(k,k+'.xlsx'))).exists() for k in names)
  st.caption(f'Archivos guardados: {saved} de 4.');return
 mapping={};unknown=[];duplicates=[]
 for f in files:
  try:
   raw=f.getvalue();headers=set(str(c).strip() for c in pd.read_excel(io.BytesIO(raw),nrows=0).columns)
   if {'TIPOD','ItemCode','CANTI','TOT'}.issubset(headers):k='ventas'
   elif {'TIPO','Almacen Origen','Almacen Origen2'}.issubset(headers) and ({'ItemCode','Quantity'}.issubset(headers) or {'Número de artículo','Cantidad'}.issubset(headers)):k='movimientos'
   elif {'Stock','Stock Valorizado','Número de artículo'}.issubset(headers):k='stock'
   elif {'Nro Nota Crédito','Estado Solicitud','Nro Devolución'}.issubset(headers):k='nc'
   else:unknown.append(f.name);continue
   if k in mapping:duplicates.append(f.name)
   else:mapping[k]=raw
  except Exception as exc:unknown.append(f'{f.name} ({exc})')
 if unknown:st.warning('No reconocidos: '+', '.join(unknown))
 if duplicates:st.warning('Duplicados: '+', '.join(duplicates))
 st.caption('Reconocidos: '+(', '.join(names[k] for k in mapping) if mapping else 'ninguno'))
 missing=[names[k] for k in names if k not in mapping]
 if missing:st.info('Faltan: '+', '.join(missing))
 if len(files)!=4 or unknown or duplicates or missing:return
 if st.button('Actualizar los 4 archivos',type='primary',width='stretch',key='guardar_cuatro_v59'):
  try:
   checks={k:read_excel(mapping[k]) for k in SOURCES}
   checks['out'],checks['back']=derivar_service_desde_movimientos(mapping['movimientos'])
   compute(checks)
   moves=movimientos_055(mapping['movimientos'])
   if moves.empty:raise ValueError('No hay movimientos válidos de sucursales.')
   sales=procesar_ventas(mapping['ventas'])
   if sales.empty:raise ValueError('No hay FACT o NCRED válidas.')
   for k,raw in mapping.items():
    target={'movimientos':'movimientos_055.xlsx','ventas':'ventas_totales.xlsx'}.get(k,k+'.xlsx')
    (DATA/target).write_bytes(raw)
   (DATA/'actualizacion.json').write_text(json.dumps({'uploaded':datetime.now().isoformat(),'sources':list(mapping)},ensure_ascii=False),encoding='utf-8')
   st.success('Los cuatro archivos se actualizaron.');st.rerun()
  except Exception as exc:st.error('No se actualizaron los archivos: '+str(exc))


@st.cache_data(show_spinner=False)
def procesar_ventas(raw):
 d=pd.read_excel(io.BytesIO(raw))
 req={'TIPOD','ItemCode','Dscription','CANTI','TOT','Nombre de sucursal'}
 if not req.issubset(d.columns):raise ValueError('Faltan columnas: '+', '.join(sorted(req-set(d.columns))))
 d=d.copy()
 d['_tipo']=d['TIPOD'].astype('string').str.upper().str.strip()
 d=d[d['_tipo'].isin(['FACT','NCRED'])].copy()
 if 'Cancelado' in d.columns:d=d[d['Cancelado'].astype('string').str.upper().str.strip().eq('N')].copy()
 dates=d['Fecha de contabilización'] if 'Fecha de contabilización' in d.columns else d['Fecha Factura']
 if pd.api.types.is_datetime64_any_dtype(dates):d['_fecha']=pd.to_datetime(dates,errors='coerce')
 else:
  num=pd.to_numeric(dates,errors='coerce')
  serial=pd.to_datetime(num.where(num.between(20000,80000)),unit='D',origin='1899-12-30',errors='coerce')
  plain=pd.to_datetime(dates.where(num.isna()),errors='coerce',dayfirst=True)
  d['_fecha']=serial.fillna(plain)
 d['_codigo']=d['ItemCode'].astype('string').str.strip().str.upper()
 d['_producto']=d['Dscription'].astype('string').fillna('Sin descripción')
 d['_sucursal']=d['Nombre de sucursal'].astype('string').fillna('Sin sucursal')
 d['_cantidad']=pd.to_numeric(d['CANTI'],errors='coerce')
 d['_importe']=pd.to_numeric(d['TOT'],errors='coerce')
 if d['_fecha'].isna().any() or d['_cantidad'].isna().any() or d['_importe'].isna().any() or d['_codigo'].isna().any():
  raise ValueError('El Excel contiene fechas, códigos, cantidades o importes inválidos. Revisá el archivo.')
 # NCRED se resta del neto; evita aplicar doble signo si el export ya trae valores negativos.
 sign=d['_tipo'].map({'FACT':1,'NCRED':-1})
 d['_unidades_netas']=d['_cantidad'].abs()*sign
 d['_importe_neto']=d['_importe'].abs()*sign
 return d

def vista_ventas_incidencia():
 section('Incidencia de Postventa sobre ventas · productos y marcas')
 st.caption('Objetivo: detectar qué artículos ingresan más al 055 en relación con sus ventas. El indicador es una aproximación de fallas, sujeto a confirmar el motivo del ingreso.')
 st.caption('Ventas: '+('archivo cargado' if (DATA/'ventas_totales.xlsx').exists() else 'pendiente')+' · Ingresos 055: '+('archivo cargado' if (DATA/'movimientos_055.xlsx').exists() else 'pendiente')+' · Actualización desde el panel único superior')
 path=DATA/'ventas_totales.xlsx'
 movpath=DATA/'movimientos_055.xlsx'
 if not path.exists():
  st.warning('Falta el Excel de ventas. Cargá los cuatro archivos desde el panel único superior.');return
 if not movpath.exists():
  st.warning('Falta el reporte de ingresos y egresos 055. Cargá los cuatro Excel en el panel único superior.');return
 try:
  d=procesar_ventas(path.read_bytes())
  mov=movimientos_055(movpath.read_bytes())
 except Exception as exc:
  st.error('No se pudo procesar la información: '+str(exc));return
 if d.empty:st.warning('El archivo de ventas no contiene registros válidos.');return
 years=sorted(set(d['_fecha'].dt.year.dropna().astype(int)).union(set(mov['_fecha'].dt.year.dropna().astype(int))))
 year=st.selectbox('Año',years,index=len(years)-1,key='ventas_ano')
 opts=['Año completo']+['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
 month=st.selectbox('Período',list(range(13)),format_func=lambda i:opts[i],key='ventas_mes')
 sales=d[d['_fecha'].dt.year.eq(year)].copy()
 ingress=mov[mov['TIPO'].eq('ingresos')&mov['_fecha'].dt.year.eq(year)].copy()
 if month:
  sales=sales[sales['_fecha'].dt.month.eq(month)].copy()
  ingress=ingress[ingress['_fecha'].dt.month.eq(month)].copy()
 service=sales['_producto'].str.contains(r'\b(?:FLETE|GARANTIA|GARANTÍA|SEGURO|SERVICIO|ENVIO|ENVÍO|INSTALACION|INSTALACIÓN)\b',case=False,regex=True,na=False)
 sales=sales[~service].copy()
 sales['_codigo']=sales['_codigo'].str.replace(r'\.0$','',regex=True)
 ingress['_codigo']=ingress['_articulo'].astype('string').str.strip().str.upper().str.replace(r'\.0$','',regex=True)
 valid=sales[sales['_tipo'].eq('FACT')&sales['_codigo'].notna()&sales['_codigo'].ne('')].copy()
 bysku=valid.groupby('_codigo',as_index=False).agg(vendidas=('_unidades_netas','sum'),ventas_valorizadas=('_importe_neto','sum'),producto=('_producto','first'))
 bysku['vendidas']=bysku['vendidas'].clip(lower=0)
 arrivals=ingress.groupby('_codigo',as_index=False).agg(ingresos_055=('_unidades','sum'))
 result=bysku.merge(arrivals,on='_codigo',how='outer')
 for col in ['vendidas','ventas_valorizadas','ingresos_055']:
  result[col]=result[col].fillna(0)
 result['producto']=result['producto'].fillna('Sin ventas registradas en el período')
 result['incidencia_pct']=100*result['ingresos_055']/result['vendidas'].where(result['vendidas']>0)
 # Marca, rubro y subrubro provienen directamente del Excel de ventas, vinculados por ItemCode.
 # Se usa el último valor no vacío por código para evitar mezclar registros sin clasificación.
 for field,label in [('MARCA' if 'MARCA' in d.columns else 'Marca','marca'),('Rubro','rubro'),('Subrubro','subrubro')]:
  result[label]='Sin '+label+' identificado'
  if field in d.columns:
   catalog=d[['_codigo',field]].copy()
   catalog[field]=catalog[field].astype('string').str.strip()
   catalog=catalog.dropna(subset=['_codigo',field])
   catalog=catalog[catalog[field].ne('')&catalog[field].str.lower().ne('nan')]
   catalog=catalog.drop_duplicates('_codigo',keep='last')
   result[label]=result['_codigo'].map(catalog.set_index('_codigo')[field]).fillna('Sin '+label+' identificado')
 # Maestro opcional únicamente para completar códigos que no tienen marca en el Excel.
 maestro=DATA/'maestro_marcas.xlsx'
 if maestro.exists():
  try:
   m=pd.read_excel(maestro)
   codes=next((c for c in ['ItemCode','Código artículo','Número de artículo','Codigo','SKU'] if c in m.columns),None)
   brands=next((c for c in ['Marca','marca','Nombre marca'] if c in m.columns),None)
   if codes and brands:
    m=m[[codes,brands]].copy()
    m['_codigo']=m[codes].astype('string').str.strip().str.upper().str.replace(r'\\.0$','',regex=True)
    m=m.drop_duplicates('_codigo',keep='last')
    mapped=result['_codigo'].map(m.set_index('_codigo')[brands])
    result['marca']=result['marca'].where(result['marca'].ne('Sin marca identificado'),mapped.fillna('Sin marca identificado'))
  except Exception as exc:st.warning('No se pudo aplicar el maestro opcional: '+str(exc))
 c1,c2,c3=st.columns(3)
 c1.metric('Unidades facturadas',qty(result['vendidas'].sum()))
 c2.metric('Ingresos al 055',qty(result['ingresos_055'].sum()))
 rate=100*result['ingresos_055'].sum()/result['vendidas'].sum() if result['vendidas'].sum()>0 else None
 c3.metric('Incidencia sobre ventas',f'{rate:.0f} %' if rate is not None else 'Sin base')
 nc_comercial=sales[sales['_tipo'].eq('NCRED')]
 fact_comercial=sales[sales['_tipo'].eq('FACT')]
 total_nc=nc_comercial['_importe'].abs().sum()
 total_fact=fact_comercial['_importe'].abs().sum()
 if not ingress.empty and ingress['_valor'].notna().all():
  st.metric('Ingresos al 055 valorizados · SAP',money(ingress['_valor'].sum()))
 else:
  st.caption('Valor de mercadería fallada: no disponible completo en los movimientos SAP. No se estima con precio de venta.')
 st.caption('Incidencia = ingresos al 055 / unidades facturadas del período. Puede incluir fallas de ventas anteriores; no es una tasa técnica de falla por cohorte.')
 minimum=st.number_input('Ventas mínimas para incluir en ranking porcentual',min_value=1,max_value=10000,value=20,step=10,key='min_ventas_falla')
 ranked=result[(result['vendidas']>=minimum)&(result['ingresos_055']>0)].sort_values(['incidencia_pct','ingresos_055'],ascending=False).copy()
 def show_incidence(frame,cols):
  # Solo formato de visualización: los cálculos y ordenamientos permanecen numéricos.
  view=frame[cols].copy()
  def numero_ar(valor,decimales=0):
   if pd.isna(valor):return '—'
   txt=f'{float(valor):,.{decimales}f}'
   return txt.replace(',','@').replace('.',',').replace('@','.')
  if 'incidencia_pct' in view.columns:
   view['incidencia_pct']=view['incidencia_pct'].map(lambda x:numero_ar(x,0)+' %' if pd.notna(x) else 'Sin base')
  for c in ['vendidas','ingresos_055']:
   if c in view.columns:view[c]=view[c].map(lambda x:numero_ar(x,0) if pd.notna(x) else '—')
  if 'ventas_valorizadas' in view.columns:
   view['ventas_valorizadas']=view['ventas_valorizadas'].map(lambda x:'$ '+numero_ar(x,2) if pd.notna(x) else '—')
  names={'_codigo':'Código SAP','producto':'Producto','marca':'Marca','rubro':'Rubro','subrubro':'Subrubro','vendidas':'Vendidos','ingresos_055':'Ingresos al 055','incidencia_pct':'Incidencia (%)','ventas_valorizadas':'Ventas netas ($)'}
  st.dataframe(view.rename(columns=names),hide_index=True,width="stretch")
 columns=['_codigo','producto','marca','rubro','vendidas','ingresos_055','incidencia_pct','ventas_valorizadas']
 top_n=st.selectbox('Cantidad de posiciones', [10,20],key='ranking_top_n')
 st.markdown('#### Productos más vendidos')
 st.caption('Incluye productos sin ingresos al 055.')
 ventas_ranking=result[result['vendidas']>0].sort_values(['vendidas','ventas_valorizadas','_codigo'],ascending=[False,False,True],kind='stable')
 if ventas_ranking.empty:st.info('No hay unidades vendidas en el período seleccionado.')
 else:show_incidence(ventas_ranking.head(top_n),columns)
 st.markdown('#### Productos con mayor incidencia')
 if ranked.empty:st.info('No hay productos con ingresos al 055 y suficientes ventas en el período.')
 else:show_incidence(ranked.head(top_n),columns)
 st.markdown('#### Productos con más ingresos al 055')
 frequent=result[result['ingresos_055']>0].sort_values('ingresos_055',ascending=False)
 show_incidence(frequent.head(top_n),columns)
 st.markdown('#### Ranking por marca')
 brands=result[~result['marca'].str.startswith('Sin marca')].groupby('marca',as_index=False)[['vendidas','ingresos_055','ventas_valorizadas']].sum()
 brands['incidencia_pct']=100*brands['ingresos_055']/brands['vendidas'].where(brands['vendidas']>0)
 show_incidence(brands.sort_values(['incidencia_pct','ingresos_055'],ascending=[False,False],na_position='last').head(top_n),['marca','vendidas','ingresos_055','incidencia_pct','ventas_valorizadas'])
 st.markdown('#### Ranking por rubro')
 rubros=result[~result['rubro'].str.startswith('Sin rubro')].groupby('rubro',as_index=False)[['vendidas','ingresos_055','ventas_valorizadas']].sum()
 rubros['incidencia_pct']=100*rubros['ingresos_055']/rubros['vendidas'].where(rubros['vendidas']>0)
 show_incidence(rubros.sort_values(['incidencia_pct','ingresos_055'],ascending=[False,False],na_position='last').head(top_n),['rubro','vendidas','ingresos_055','incidencia_pct','ventas_valorizadas'])
 st.markdown('#### Gráficos de incidencia')
 left,right=st.columns(2)
 with left:
  st.markdown('**Marcas con más ingresos al 055 (unidades)**')
  chart=brands.nlargest(top_n,'ingresos_055').sort_values('ingresos_055',ascending=True).set_index('marca')['ingresos_055']
  if chart.empty:st.info('No hay marcas identificadas.')
  else:st.bar_chart(chart,horizontal=True,sort=False)
 with right:
  st.markdown('**Productos con mayor incidencia (%)**')
  top=ranked.head(top_n).sort_values('incidencia_pct',ascending=True).copy()
  if top.empty:st.info('No hay productos con ventas suficientes.')
  else:
   top['Etiqueta']=top['_codigo'].astype(str)+' · '+top['producto'].astype(str).str.slice(0,22)
   st.bar_chart(top.set_index('Etiqueta')['incidencia_pct'].round(0),horizontal=True,sort=False)
 with st.expander('Indicador complementario · notas de crédito por sucursal',expanded=False):
  ncpath=DATA/'nc.xlsx'
  if not ncpath.exists():
   st.info('Falta el reporte de NC para mostrar la cantidad y el ranking por sucursal.')
  else:
   try:
    nc=pd.read_excel(ncpath)
    if 'Nro Nota Crédito' not in nc.columns:raise ValueError('Falta la columna Nro Nota Crédito.')
    nc['_nc']=ids(nc['Nro Nota Crédito'])
    nc=nc[nc['_nc'].ne('')].copy()
    if 'Fecha Nota Crédito' in nc.columns:
     nc['_fecha_nc']=date_col(nc['Fecha Nota Crédito'])
     nc=nc[nc['_fecha_nc'].dt.year.eq(year)]
     if month:nc=nc[nc['_fecha_nc'].dt.month.eq(month)]
    total=int(nc['_nc'].nunique())
    st.metric('NC emitidas · documentos únicos',qty(total))
    branch_col=next((c for c in ['Nombre de sucursal','Sucursal','Sucursal origen','Nombre sucursal','Almacén origen','Nombre de almacén','Almacén'] if c in nc.columns),None)
    if branch_col:
     ranking=nc.groupby(branch_col)['_nc'].nunique().sort_values(ascending=False)
     if not ranking.empty:
      st.caption('Sucursal con más NC: '+str(ranking.index[0])+' · '+qty(ranking.iloc[0])+' documentos')
      st.dataframe(ranking.head(10).rename('NC únicas').reset_index(),hide_index=True,width="stretch")
    else:st.caption('El Excel de NC no tiene una columna de sucursal identificable. Para el ranking por sucursal necesitamos ese dato.')
   except Exception as exc:st.warning('No se pudo obtener el detalle de NC: '+str(exc))

# V35 · Histórico de cierres: se guarda la foto del SAP y el balance en el mes elegido.
# El archivo de stock SAP no es histórico; nunca se usa para simular el stock de meses previos.
HISTORY=DATA/'cierres_mensuales.json'
def load_closures():
 try:
  raw=json.loads(HISTORY.read_text(encoding='utf-8')) if HISTORY.exists() else {}
  return raw if isinstance(raw,dict) else {}
 except (OSError,ValueError):return {}

def save_closure(period,record):
 all_records=load_closures();all_records[period]=record
 tmp=HISTORY.with_suffix('.tmp')
 tmp.write_text(json.dumps(all_records,ensure_ascii=False,indent=2),encoding='utf-8')
 tmp.replace(HISTORY)

def closure_balance(initial,ingress,stock,egress,nc,physical,pending,scrap):
 available=initial+ingress
 destination=stock+egress+nc+physical+pending # Scrap informado dentro de egresos; no duplicar
 return available,destination,available-destination

def monthly_followup(year,month,cutoff,m,ins,outs):
 period=f'{year}-{month:02d}'
 st.markdown('<div class="ceo-section-title">CONTROL DE ROTACIÓN Y CIERRE MENSUAL</div>',unsafe_allow_html=True)
 st.caption('Conciliación: ingresos desde abril de 2026 y egresos desde enero de 2026. El stock SAP representa el archivo cargado, no necesariamente el stock del mes elegido.')
 # La base de 886 unidades fue definida para abril 2026; para otro año no se extrapola.
 if year!=2026 or month<4:
  st.info('El balance con stock inicial de 886 unidades corresponde a la base de abril de 2026. Para otros períodos se requiere cargar una apertura validada.')
  return
 closures=load_closures()
 prior=closures.get(period)
 if prior:
  st.info(f'Cierre guardado para {period} el {prior.get("saved_at","fecha desconocida")}. Se conserva como fotografía del período.')
 scrap_default=int(prior.get('scrap',66)) if prior else 66
 scrap=st.number_input('Scrap desde abril (unidades, confirmar)',min_value=0,value=scrap_default,step=1,key=f'scrap_{period}')
 st.caption('Valorización confirmada de scrap: '+money(3012767.93))
 initial=886;in_qty=float(ins['_unidades'].sum());out_qty=float(outs['_unidades'].sum())
 available,destination,difference=closure_balance(initial,in_qty,m['stock_units'],out_qty,m['nc_units'],m['physical_units'],m['pending_send_units'],scrap)
 # La rotación pendiente se mide como stock remanente; proveedores abiertos no son recuperos cerrados.
 rotated=available-m['stock_units']
 rotated_pct=100*rotated/available if available else 0
 stock_pct=100*m['stock_units']/available if available else 0
 completed=out_qty+m['nc_units']+m['physical_units']+m['pending_send_units']
 # Tarjeta nativa HTML: cambia con cada carga SAP y con el corte seleccionado.
 # El saldo fuera de stock es una diferencia de existencias, NO recupero definitivo.
 if available<=0 or m['stock_units']<0 or m['stock_units']>available:
  st.error('No es posible calcular el avance: el stock supera el total de referencia o faltan datos válidos.')
 else:
  st.markdown(f"""<div style="background:#fff;border:1px solid #d8e2e8;border-radius:17px;padding:24px 26px;margin:14px 0 22px;box-shadow:0 3px 12px rgba(2,47,64,.05);">
  <div style="font-size:13px;letter-spacing:.08em;font-weight:800;color:#536e7c;margin-bottom:18px;">AVANCE DE GESTIÓN · {month:02d}/{year}</div>
  <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;">
  <div><div style="color:#597080;font-size:14px;">Total de referencia</div><div style="font-size:34px;font-weight:800;color:#022f40;">{qty(available)}</div></div>
  <div><div style="color:#597080;font-size:14px;">Fuera del stock 055</div><div style="font-size:34px;font-weight:800;color:#008b78;">{qty(rotated)}</div></div>
  <div><div style="color:#597080;font-size:14px;">Stock pendiente</div><div style="font-size:34px;font-weight:800;color:#022f40;">{qty(m['stock_units'])}</div></div>
  </div>
  <div style="display:flex;height:19px;border-radius:12px;overflow:hidden;margin-top:14px;background:#ffc107;">
   <div style="width:{max(0,min(100,rotated_pct)):.3f}%;background:#0c8290;"></div>
  </div>
  <div style="display:flex;justify-content:space-between;gap:15px;margin-top:10px;color:#526d7a;font-size:13px;">
  <span>{rotated_pct:.1f}% fuera del stock</span><span>{stock_pct:.1f}% pendiente en stock</span></div>
  </div>""",unsafe_allow_html=True)
 # Se retira el bloque de destinos clasificados, diferencia, detalle y cierre manual a pedido del usuario.


# V61: navegación ejecutiva dinámica, conserva las rutinas de datos de V60.8.
st.markdown("""<style>
[data-testid="stSidebar"]{min-width:235px!important;}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:8px 5px;margin:3px 0;border-radius:8px;}
.v61-head{background:linear-gradient(110deg,#022f40,#05637c);border-radius:16px;padding:24px 28px;color:#fff;margin:0 0 18px}
.v61-head h1{color:#fff!important;margin:0;font-size:30px!important}
.v61-head p{margin:5px 0 0;color:#d9e9ef}
.v61-strip{background:#022f40;color:white;border-radius:10px;padding:9px 15px;font-size:15px;font-weight:800;margin:18px 0 12px}
.v61-kpi{background:#fff;border:1px solid #d8e6ed;border-radius:14px;padding:18px;min-height:112px;text-align:center}
.v61-kpi .lab{color:#527083;font-size:13px;font-weight:700}.v61-kpi .val{font-size:32px;font-weight:800;color:#023d52}
.v61-highlight{background:#fff2c7;border:1px solid #f6df8b;border-radius:14px;padding:20px}
</style>""",unsafe_allow_html=True)
st.markdown("<style>\n/* V62 · Sistema visual unificado para todos los módulos */\n.v61-head{display:flex;align-items:center;gap:20px;background:linear-gradient(110deg,#022f40,#075a74);padding:16px 23px;border-radius:12px;margin-bottom:13px;min-height:84px}\n.v61-head h1{font-size:25px!important;line-height:1.2!important;margin:0!important;color:#fff!important}\n.v61-head p{font-size:12px;color:#d5e8f0;margin-top:5px}\n.v61-brand{display:flex;flex-direction:column;border-right:3px solid #ffc107;padding-right:19px;line-height:1}\n.v61-brand strong{color:white;font-size:29px;font-weight:900;font-style:italic;letter-spacing:-2px}\n.v61-brand small{color:white;font-size:11px;letter-spacing:3px;margin-top:6px}\n.v61-head-tag{margin-left:auto;color:#d5e8f0;font-size:11px;letter-spacing:.08em;white-space:nowrap}\n.v61-strip{background:linear-gradient(90deg,#023c51,#025b72);font-size:12px;letter-spacing:.025em;border-radius:8px;padding:10px 13px;margin:14px 0 11px}\n.v61-kpi{background:#eaf3f8;border:1px solid #d6e5ed;border-radius:10px;min-height:103px;padding:15px 10px;box-shadow:0 2px 7px #07374c0d}\n.v61-kpi .val{font-size:clamp(21px,2vw,29px)}\n[data-testid=\"stMetric\"]{background:#eaf3f8;border:1px solid #d6e5ed;border-radius:10px;padding:13px 16px;box-shadow:0 2px 7px #07374c0d;min-height:95px}\n[data-testid=\"stMetricLabel\"]{color:#355b6c;font-weight:700}\n[data-testid=\"stMetricValue\"]{color:#023d52;font-weight:800}\n[data-testid=\"stDataFrame\"], [data-testid=\"stVegaLiteChart\"], [data-testid=\"stArrowVegaLiteChart\"]{border:1px solid #d6e5ed;border-radius:12px;overflow:hidden;background:white}\n[data-testid=\"stVerticalBlock\"] h3{color:#023c51;font-weight:800}\n[data-testid=\"stVerticalBlock\"] h4{background:linear-gradient(90deg,#023c51,#025b72);color:white!important;border-radius:8px;padding:9px 12px;font-size:13px!important}\n[data-testid=\"stFileUploader\"], [data-testid=\"stExpander\"]{border-radius:10px}\n@media(max-width:760px){.v61-head{flex-wrap:wrap}.v61-head-tag{display:none}}\n</style>",unsafe_allow_html=True)
st.markdown("""<style>
[data-testid="stSidebar"]{background:linear-gradient(180deg,#022f40,#03506a)!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{border-radius:8px!important;padding:10px 8px!important;margin:2px 0!important;font-size:13px!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){background:#ffc107!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p{color:#022f40!important;font-weight:800!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) [data-testid="stMarkdownContainer"] *{color:#022f40!important}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"]{gap:2px}
.ymk-brand{display:flex;align-items:baseline;gap:6px;color:white;margin:7px 0 14px}.ymk-brand strong{font-size:31px;font-style:italic;letter-spacing:-2px}.ymk-brand span{font-size:16px;letter-spacing:2px}
.block-container{max-width:1800px!important;padding:0.65rem 1.2rem 2rem!important}
[data-testid="stSidebar"] [data-testid="stExpander"]{background:#f2f7fa!important}
</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.markdown('<div class="ymk-brand"><strong>YMK</strong><span>HOGAR</span></div>',unsafe_allow_html=True)
 st.caption('POSTVENTA · DEPÓSITO 055')
 pagina=st.radio('Vistas', ['🏠 Resumen ejecutivo','📦 Stock y movimientos','💰 Recuperación económica','🔧 Almacén de Reparación 109','📊 Ventas e incidencia','⚙️ Administración'],label_visibility='collapsed')
 st.divider()
 with st.expander('Actualizar los cuatro Excel',expanded=False):
  carga_excel_sap()
 with st.expander('Gastos fuera de DOA · Finanzas',expanded=False):
  st.caption('Actualizar archivo únicamente con acceso de administrador.')
  if st.session_state.get('admin_auth',False):
   f=st.file_uploader('Excel de pagos fuera de DOA',type=['xlsx'],key='finanzas_v631')
   if f is not None and st.button('Guardar archivo de Finanzas'):
    required={'Fecha contabilizacion','Importe débito','Importe del Crédito'}
    try:
     headers=set(pd.read_excel(io.BytesIO(f.getvalue()),nrows=0).columns)
     if not required.issubset(headers):st.error('Faltan columnas obligatorias de Finanzas.')
     else:
      (DATA/'pagos_fuera_doa.xlsx').write_bytes(f.getvalue());st.success('Archivo de Finanzas actualizado.')
    except Exception as ex:st.error(str(ex))
  else:st.info('Autenticarse primero en el módulo de actualización SAP.')
 st.caption('V61.1 · Diseño ejecutivo dinámico')

if pagina!='🏠 Resumen ejecutivo':
 titulos={'📦 Stock y movimientos':'Stock y movimientos','💰 Recuperación económica':'Recuperación económica','🔧 Almacén de Reparación 109':'Almacén de Reparación 109','📊 Ventas e incidencia':'Ventas e incidencia','⚙️ Administración':'Administración · EERR Hogar'}
 titulo=html.escape(titulos.get(pagina,'Postventa'))
 st.markdown(f'<div class="v61-head"><div class="v61-brand"><strong>YMK</strong><small>HOGAR</small></div><div><h1>{titulo}</h1><p>Yuhmak Hogar · Tablero de gestión</p></div><div class="v61-head-tag">PANEL EJECUTIVO</div></div>',unsafe_allow_html=True)
if pagina=='⚙️ Administración':
 administracion.render()
 st.stop()
try:
 m,mov,dfs=current_data()
except Exception as exc:
 st.error('No se pudo procesar el tablero: '+str(exc));m,mov,dfs=None,None,None
if m is None:
 st.info('Cargá los cuatro Excel desde el panel lateral para activar los indicadores y gráficos.')
 st.stop()
fechas=mov['_fecha'].dropna()
if fechas.empty:
 st.error('No se encontraron fechas válidas en los movimientos SAP.');st.stop()
years=sorted(set(int(x) for x in fechas.dt.year.unique()),reverse=True)
filter1,filter2=st.columns([1,1])
with filter1: year=st.selectbox('Año',years,key='v61_year')
months=sorted(set(int(x) for x in fechas[fechas.dt.year.eq(year)].dt.month.unique()))
with filter2: selected_period=st.selectbox('Período de consulta',[0]+months,format_func=lambda x:'Acumulado anual' if x==0 else ['','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][x],key='v631_period')
month=max(months) if months else 12
cutoff=pd.Timestamp(year,month,1)+pd.offsets.MonthEnd(0)
period_start=pd.Timestamp(year,selected_period,1) if selected_period else pd.Timestamp(year,1,1)
period_end=(period_start+pd.offsets.MonthEnd(0)) if selected_period else cutoff
period_mov=mov[mov['_fecha'].between(period_start,period_end)].copy()
scoped=mov[mov['_fecha'].between(pd.Timestamp(year,1,1),cutoff)].copy()
since_apr=mov[mov['_fecha'].between(pd.Timestamp(year,4,1),cutoff)].copy() if month>=4 else mov.iloc[:0].copy()
ins=since_apr[since_apr['TIPO'].eq('ingresos')]
outs=scoped[scoped['TIPO'].eq('egresos')]
in_qty=float(ins['_unidades'].sum());out_qty=float(outs['_unidades'].sum())
initial=886 if year==2026 and month>=4 else None
available=initial+in_qty if initial is not None else None
unit_dest=float(m['stock_units']+out_qty+m['nc_units']+m['physical_units']+m['pending_send_units'])
def kpi(label,value,detail=''):
 st.markdown(f'<div class="v61-kpi"><div class="lab">{html.escape(str(label))}</div><div class="val">{html.escape(str(value))}</div><div class="lab">{html.escape(str(detail))}</div></div>',unsafe_allow_html=True)
def cashval(frame):
 return money(float(frame['_valor'].sum())) if len(frame) and frame['_valor'].notna().all() else 'Sin valorizar'
raw=normalizar_movimientos_sap((DATA/'movimientos_055.xlsx').read_bytes())
tipo=raw['TIPO'].astype('string').str.lower().str.strip();origin=pd.to_numeric(raw['Almacen Origen'],errors='coerce');dest=pd.to_numeric(raw['Almacen Origen2'],errors='coerce');dates=pd.to_datetime(raw['Fecha de contabilización'],errors='coerce')
service_sent=raw[tipo.eq('egresos')&origin.eq(55)&dest.eq(109)&dates.le(cutoff)]
service_ret=raw[tipo.eq('ingresos')&origin.eq(109)&dates.le(cutoff)]
def units_raw(frame):return float(pd.to_numeric(frame['Quantity'],errors='coerce').abs().sum())
def value_raw(frame):
 v=frame['Stock Valorizado'];num=pd.to_numeric(v,errors='coerce');parsed=pd.to_numeric(v.astype('string').str.replace('.','',regex=False).str.replace(',','.',regex=False),errors='coerce');return float(num.fillna(parsed).abs().sum())
sent_qty=units_raw(service_sent);ret_qty=units_raw(service_ret)
def gastos_doa(period_year,period_month=None):
 path=DATA/'pagos_fuera_doa.xlsx'
 if not path.exists():return None
 try:
  df=pd.read_excel(path)
  needed=['Fecha contabilizacion','Importe débito','Importe del Crédito']
  if any(c not in df.columns for c in needed):return None
  dt=df['Fecha contabilizacion']
  if pd.api.types.is_numeric_dtype(dt):dt=pd.to_datetime(dt,unit='D',origin='1899-12-30',errors='coerce')
  else:dt=pd.to_datetime(dt,errors='coerce',dayfirst=True)
  v=numeric(df['Importe débito'])-numeric(df['Importe del Crédito'])
  mask=dt.dt.year.eq(period_year)
  if period_month:mask &=dt.dt.month.eq(period_month)
  return float(v[mask].sum())
 except Exception:return None

def recuperacion_periodo(d,period_year,period_month=None):
 nc=d['nc'].copy()
 for col in ['Fecha Nota Crédito','Fecha Devolución','Fecha Solicitud']:
  nc[col+'_dt']=date_col(nc[col]) if col in nc else pd.NaT
 state=nc['Estado Solicitud'].astype('string').fillna('').str.lower()
 devstate=nc['Estado Devolución'].astype('string').fillna('').str.lower()
 hasnc=ids(nc['Nro Nota Crédito']).ne('')
 cancel=state.str.contains('cancel|anulad',na=False)
 openreq=state.str.contains('abiert',na=False)
 issued=(~cancel)&(~openreq)&hasnc
 physical=(~cancel)&(~openreq)&(~hasnc)&state.str.contains('cerrad',na=False)&devstate.str.contains('cerrad',na=False)
 def within(date):
  mask=date.dt.year.eq(period_year)
  return mask & date.dt.month.eq(period_month) if period_month else mask
 q=numeric(nc['Cantidad']);v=numeric(nc['Total (ML)'])
 nmask=issued&within(nc['Fecha Nota Crédito_dt'])
 pmask=physical&within(nc['Fecha Devolución_dt'])
 return dict(nc_units=float(q[nmask].sum()),nc_value=float(v[nmask].sum()),physical_units=float(q[pmask].sum()),physical_value=float(v[pmask].sum()),missing_physical_dates=int((physical&nc['Fecha Devolución_dt'].isna()).sum()))

if pagina=='🏠 Resumen ejecutivo' and selected_period:
 st.markdown('### Resultado mensual · '+['','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][selected_period]+' '+str(year))
 st.info('Los flujos corresponden al mes seleccionado. El stock histórico y la conciliación de existencias requieren un cierre de inventario a esa fecha; no se sustituyen por el stock actual.')
 rec=recuperacion_periodo(dfs,year,selected_period)
 a,b,c=st.columns(3)
 with a:st.metric('Ingresos 055 (u.)',qty(period_mov.loc[period_mov['TIPO'].eq('ingresos'),'_unidades'].sum()))
 with b:st.metric('Egresos 055 (u.)',qty(period_mov.loc[period_mov['TIPO'].eq('egresos'),'_unidades'].sum()))
 with c:st.metric('Recuperación clasificada ($)',money(rec['nc_value']+rec['physical_value']))
 executive_table([('NC emitidas · '+qty(rec['nc_units'])+' u.',money(rec['nc_value'])),('Nuevas / reparadas con fecha de devolución · '+qty(rec['physical_units'])+' u.',money(rec['physical_value'])),('Retornos del Almacén de Reparación 109 · '+qty(units_raw(service_ret[dates.loc[service_ret.index].ge(period_start)]))+' u.',money(value_raw(service_ret[dates.loc[service_ret.index].ge(period_start)]))),('Pagos por Reparaciones fuera de DOA',money(-gastos_doa(year,selected_period)) if gastos_doa(year,selected_period) is not None else 'Archivo Finanzas no cargado')])
 if rec['missing_physical_dates']:st.warning('Hay '+str(rec['missing_physical_dates'])+' líneas físicas sin fecha de devolución; no se asignan arbitrariamente a un mes.')
 st.caption('Scrap: gasto manual anual. No se asigna a meses sin fecha de realización registrada.')
elif pagina=='🏠 Resumen ejecutivo':
 trend_df=scoped.copy();trend_df['_mes']=trend_df['_fecha'].dt.month
 trend_df=trend_df.pivot_table(index='_mes',columns='TIPO',values='_unidades',aggfunc='sum',fill_value=0).reindex(range(1,13),fill_value=0).reindex(columns=['ingresos','egresos'],fill_value=0)
 trend_vals=[(float(r['ingresos']),float(r['egresos'])) for _,r in trend_df.iterrows()]
 view_data=dict(doa_expense=gastos_doa(year),scrap_expense=3012767.93,initial=initial,in_qty=in_qty,stock=float(m['stock_units']),out_qty=out_qty,nc_units=float(m['nc_units']),physical_units=float(m['physical_units']),pending_units=float(m['pending_send_units']),nc_value=float(m['nc_value']),physical_value=float(m['physical_value']),ret=ret_qty,ret_value=value_raw(service_ret),sent=sent_qty,out_other=out_qty-sent_qty,trend=trend_vals,month=month,period=f'{month:02d}/{year}')
 # Renderizar HTML/CSS como documento real, evitando que Markdown muestre etiquetas como texto.
 import streamlit.components.v1 as components
 components.html(executive_ui.CSS + executive_ui.render(view_data), height=820, scrolling=True)
elif pagina=='📦 Stock y movimientos':
 st.markdown('<div class="v61-strip">STOCK Y MOVIMIENTOS · 055</div>',unsafe_allow_html=True)
 if selected_period:st.info('Movimientos del mes seleccionado. Stock actual y conciliación histórica no son calculables sin saldo de cierre del mes.')
 a,b,c=st.columns(3)
 with a:kpi('Stock inicial',qty(initial) if initial and not selected_period else 'N/D histórico')
 with b:kpi('Ingresos '+('del mes' if selected_period else 'desde abril'),qty(period_mov.loc[period_mov['TIPO'].eq('ingresos'),'_unidades'].sum()) if selected_period else qty(in_qty))
 with c:kpi('Egresos '+('del mes' if selected_period else 'desde enero'),qty(period_mov.loc[period_mov['TIPO'].eq('egresos'),'_unidades'].sum()) if selected_period else qty(out_qty))
 executive_table([('Stock actual',('N/D histórico' if selected_period else qty(m['stock_units'])+' u. · '+money(m['stock_value']))),('Egresos hacia otros almacenes',qty(out_qty-sent_qty)+' u.' if not selected_period else 'Consultar movimientos mensuales'),('Egresos hacia el Almacén de Reparación 109',qty(sent_qty)+' u.' if not selected_period else 'Consultar sección 109'),('Egresos totales',qty(out_qty)+' u. · '+cashval(outs) if not selected_period else qty(period_mov.loc[period_mov['TIPO'].eq('egresos'),'_unidades'].sum())+' u.'),('Conciliación aritmética',qty(available-unit_dest)+' u.' if available is not None and not selected_period else 'N/D histórico')])
 vista_movimientos()
elif pagina=='💰 Recuperación económica':
 st.markdown('<div class="v61-strip">RECUPERACIÓN ECONÓMICA</div>',unsafe_allow_html=True)
 rec=recuperacion_periodo(dfs,year,selected_period or None)
 executive_table([('Notas de crédito · '+qty(rec['nc_units'])+' u.',money(rec['nc_value'])),('Nuevas/reparadas · '+qty(rec['physical_units'])+' u.',money(rec['physical_value'])),('Recuperación clasificada',money(rec['nc_value']+rec['physical_value'])),('Solicitudes abiertas (estado actual)',money(m['pending_send_value']) if not selected_period else 'No reconstruible históricamente'),('Scrap · carga manual anual',money(-3012767.93) if not selected_period else 'Sin fecha mensual registrada')])
 st.caption('Las solicitudes abiertas son una foto del estado actual, no un histórico mensual. Recuperaciones fechadas según NC y devolución.')
 if rec['missing_physical_dates']:st.warning('Recuperaciones físicas sin fecha de devolución: '+str(rec['missing_physical_dates'])+' líneas no asignables a un mes.')
elif pagina=='🔧 Almacén de Reparación 109':
 st.markdown('<div class="v61-strip">ALMACÉN DE REPARACIÓN 109</div>',unsafe_allow_html=True)
 a,b=st.columns(2)
 with a:kpi('Envíos 055 → 109',qty(units_raw(service_sent[dates.loc[service_sent.index].ge(period_start)]))+' u.',money(value_raw(service_sent[dates.loc[service_sent.index].ge(period_start)])))
 with b:kpi('Retornos 109 → 055',qty(units_raw(service_ret[dates.loc[service_ret.index].ge(period_start)]))+' u.',money(value_raw(service_ret[dates.loc[service_ret.index].ge(period_start)])))
 st.caption('Movimientos SAP, no necesariamente unidades únicas ni una conciliación por número de serie.')
elif pagina=='📊 Ventas e incidencia':
 st.markdown('<div class="v61-strip">VENTAS E INCIDENCIAS · INDICADORES Y RANKINGS</div>',unsafe_allow_html=True)
 vista_ventas_incidencia()


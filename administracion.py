import io
import pandas as pd
import streamlit as st

MESES={'Ene':'Enero','Feb':'Febrero','Mar':'Marzo','Abr':'Abril','May':'Mayo','Jun':'Junio','Jul':'Julio','Ago':'Agosto'}
EXCLUIR={'Ventas','Costos de Venta','Costo de Venta','Utilidad Bruta','Gastos Administración','Total Gastos Administración','Gastos Comercialización','Total Gastos Comercialización','Otros Egresos','Otros Ingresos','EBITDA','Utilidad Neta Final','Total Costos Variables','Total Costos Fijos','MC','Punto de Equilibrio'}
CENTROS=['Avellaneda 50','Avellaneda 122','Banda 1','Banda 2','Concepcion','Alberdi','Monteros','Ecommerce','Sgo. Del Estero','Banda Santiago','Catamarca','Rioja 1','Rioja 2','CD','Areas Centrales Hogar']

def money(v): return '$ '+f'{v:,.0f}'.replace(',','.')
def pct(v): return f'{v:.2f}%'.replace('.',',')
def norm(s):
 import unicodedata
 return ''.join(c for c in unicodedata.normalize('NFKD',str(s)) if not unicodedata.combining(c)).lower().replace('á','a').strip()

def centro(s):
 n=norm(s)
 if 'central' in n and 'hogar' in n:return 'Areas Centrales Hogar'
 if n=='cd':return 'CD'
 for c in CENTROS[:13]:
  if norm(c)==n:return c
 return None

@st.cache_data(show_spinner=False)
def leer(datos):
 libro=pd.ExcelFile(io.BytesIO(datos))
 meses=[m for m in MESES if m in libro.sheet_names]
 if not meses:raise ValueError('No se encontraron hojas Ene, Feb, Mar, Abr, May, Jun, Jul y Ago.')
 registros=[]; ventas=[]; avisos=[]; diferencias=[]
 for m in meses:
  df=pd.read_excel(libro,sheet_name=m,header=0)
  df.columns=[str(x).strip() for x in df.columns]
  cols=list(df.columns)
  if len(cols)<5:continue
  cuenta=cols[0]; area=cols[1]; consolidado=cols[3]
  mapa={c:centro(c) for c in cols[4:]}
  disponibles={v for v in mapa.values() if v}
  faltantes=[c for c in CENTROS if c not in disponibles]
  if faltantes:avisos.append(f'{MESES[m]}: no figuran como centros de costos: {", ".join(faltantes)}.')
  ignorados=[c for c in cols[4:] if not mapa[c] and 'expensa' in norm(c)]
  if ignorados:avisos.append(f'{MESES[m]}: columna {", ".join(ignorados)} no asignada a Áreas Centrales (son conceptos distintos).')
  bloque=''
  for _,r in df.iterrows():
   nom=str(r[cuenta]).strip()
   if nom in ('nan','None',''):continue
   key=norm(nom)
   if key=='ventas':
    val=pd.to_numeric(r[consolidado],errors='coerce')
    if pd.notna(val):ventas.append((m,float(val)))
    continue
   if key in [norm(x) for x in EXCLUIR]:
    if 'administr' in key:bloque='Administración'
    elif 'comercial' in key:bloque='Comercialización'
    elif 'otros egresos' in key:bloque='Otros egresos'
    elif 'ebitda' in key:bloque='Posterior a EBITDA'
    elif 'otros ingresos' in key:bloque='Otros ingresos'
    continue
   if bloque=='Otros ingresos':continue
   categoria=str(r[area]).strip()
   if categoria in ('nan','None',''):continue
   if norm(categoria) in ('venta','costo de mercaderia vendida'):continue
   val=pd.to_numeric(r[consolidado],errors='coerce')
   if pd.isna(val) or val>=0:continue
   # El EERR expresa gastos en negativo; presentar magnitudes positivas sin invertir ingresos.
   gasto=-float(val)
   registros.append((m,bloque,nom,categoria,'Consolidado',gasto))
   for col,cc in mapa.items():
    if cc is None:continue
    v=pd.to_numeric(r[col],errors='coerce')
    if pd.notna(v) and v<0:registros.append((m,bloque,nom,categoria,cc,-float(v)))
  # Conciliación por mes: RN frente a suma de 15 centros de costos, sobre las líneas seleccionadas.
  rmes=[r for r in registros if r[0]==m]
  rn=sum(r[-1] for r in rmes if r[4]=='Consolidado')
  suc=sum(r[-1] for r in rmes if r[4]!='Consolidado')
  diferencias.append((MESES[m],rn,suc,suc-rn))
 tabla=pd.DataFrame(registros,columns=['Mes','Bloque','Cuenta','Categoría','Centro','Gasto'])
 return tabla,pd.DataFrame(ventas,columns=['Mes','Ventas']),avisos,pd.DataFrame(diferencias,columns=['Mes','RN gastos','Centros de costos','Diferencia'])

def render():
 st.markdown('<div style="background:#022f40;color:white;padding:26px;border-radius:16px"><h1 style="color:white;margin:0">Administración | EERR Hogar</h1><div style="color:#f7d558">Análisis de gastos · Enero a agosto · 15 centros de costos</div></div>',unsafe_allow_html=True)
 st.caption('Módulo independiente de Postventa. Los datos se procesan a partir del Excel que cargás en esta sesión.')
 archivo=st.file_uploader('Cargar EERR por Sucursal (.xlsx)',type=['xlsx'],key='admin_eerr')
 if archivo is None:
  st.info('Cargá el Excel EERR por Sucursal para visualizar el Top 10 y la distribución por centro de costos.')
  return
 try: tabla,ventas,avisos,conc=leer(archivo.getvalue())
 except Exception as e:
  st.error('No se pudo interpretar el archivo: '+str(e));return
 if tabla.empty or ventas.empty:st.warning('No se encontraron gastos o ventas válidos en las hojas mensuales.');return
 meses=list(ventas['Mes'].drop_duplicates());sel=st.multiselect('Períodos a analizar',[MESES[m] for m in meses],default=[MESES[m] for m in meses])
 elegidos=[m for m in meses if MESES[m] in sel]
 if not elegidos:st.warning('Seleccioná al menos un mes.');return
 t=tabla[tabla.Mes.isin(elegidos)];v=ventas[ventas.Mes.isin(elegidos)]['Ventas'].sum()
 base=t[t.Centro=='Consolidado']; total=base.Gasto.sum()
 top=base.groupby('Categoría',as_index=False).Gasto.sum().sort_values('Gasto',ascending=False).head(10).copy()
 top['% sobre ventas']=top.Gasto/v*100 if v else 0
 top['% del gasto']=top.Gasto/total*100 if total else 0
 c1,c2,c3=st.columns(3)
 c1.metric('Ventas acumuladas',money(v));c2.metric('Gastos analizados (RN)',money(total));c3.metric('Gastos / ventas',pct(total/v*100) if v else '—')
 st.caption('Gastos analizados: suma de cuentas de egreso con saldo negativo, sin costo de mercadería vendida, ingresos ni subtotales. No equivale necesariamente al total contable neto de gastos.')
 st.subheader('Top 10 · categorías de gasto')
 st.dataframe(top.rename(columns={'Categoría':'Gasto','Gasto':'Importe ($)'}).style.format({'Importe ($)':money,'% sobre ventas':pct,'% del gasto':pct}),hide_index=True,use_container_width=True)
 st.bar_chart(top.set_index('Categoría')['% sobre ventas'],horizontal=True,x_label='Participación sobre ventas (%)')
 st.subheader('Detalle por centro de costos')
 opcion=st.selectbox('Seleccionar gasto para analizar',top['Categoría'].tolist())
 det=t[(t.Centro!='Consolidado')&(t.Categoría==opcion)].groupby('Centro',as_index=False).Gasto.sum()
 det=pd.DataFrame({'Centro':CENTROS}).merge(det,on='Centro',how='left').fillna({'Gasto':0})
 det=det.sort_values('Gasto',ascending=False).reset_index(drop=True)
 det['% del gasto distribuido']=det.Gasto/det.Gasto.sum()*100 if det.Gasto.sum() else 0
 det['% sobre ventas totales']=det.Gasto/v*100 if v else 0
 rn=base[base.Categoría==opcion].Gasto.sum();dist=det.Gasto.sum()
 d1,d2,d3=st.columns(3)
 d1.metric('Gasto consolidado RN',money(rn));d2.metric('Distribuido en centros',money(dist));d3.metric('Diferencia de conciliación',money(dist-rn))
 st.dataframe(det.rename(columns={'Centro':'Sucursal / centro de costos','Gasto':'Importe ($)'}).style.format({'Importe ($)':money,'% del gasto distribuido':pct,'% sobre ventas totales':pct}),hide_index=True,use_container_width=True)
 st.bar_chart(det.set_index('Centro')['Gasto'],horizontal=True,x_label='Importe ($)')
 st.download_button('Descargar distribución (CSV)',det.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),file_name='Administracion_EERR_distribucion.csv',mime='text/csv')
 with st.expander('Auditoría y advertencias del archivo'):
  for a in sorted(set(avisos)):st.warning(a)
  st.write('Conciliación por mes (gastos de las cuentas seleccionadas)')
  st.dataframe(conc[conc.Mes.isin(sel)].style.format({'RN gastos':money,'Centros de costos':money,'Diferencia':money}),hide_index=True,use_container_width=True)
  st.caption('El porcentaje por centro de costos utiliza como denominador el total distribuido en centros; si difiere del RN, se informa la diferencia. Las columnas históricas «Expensas Hogar» no se equiparan a «Áreas Centrales Hogar».')

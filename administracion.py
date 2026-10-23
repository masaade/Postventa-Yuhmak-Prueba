import io
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
import pandas as pd
import altair as alt
import streamlit as st

MESES={'Ene':'Enero','Feb':'Febrero','Mar':'Marzo','Abr':'Abril','May':'Mayo','Jun':'Junio','Jul':'Julio','Ago':'Agosto'}
EXCLUIR={'Ventas','Costos de Venta','Costo de Venta','Utilidad Bruta','Gastos Administración','Total Gastos Administración','Gastos Comercialización','Total Gastos Comercialización','Otros Egresos','Otros Ingresos','EBITDA','Utilidad Neta Final','Total Costos Variables','Total Costos Fijos','MC','Punto de Equilibrio'}
CENTROS=['Avellaneda 50','Avellaneda 122','Banda 1','Banda 2','Concepcion','Alberdi','Monteros','Ecommerce','Sgo. Del Estero','Banda Santiago','Catamarca','Rioja 1','Rioja 2','CD','Areas Centrales Hogar']

def money(v): return '$ '+f'{v:,.0f}'.replace(',','.')
def pct(v): return f'{v:.2f}%'.replace('.',',')
def norm(s):
 import unicodedata
 return ''.join(c for c in unicodedata.normalize('NFKD',str(s)) if not unicodedata.combining(c)).lower().replace('á','a').strip()

def categoria_agrupada(categoria):
 """Agrupa RRHH y RRHH - Expensas Hogar sin alterar el centro de costos."""
 n=' '.join(norm(categoria).replace('-', ' ').replace('–', ' ').replace('—', ' ').split())
 if n in ('rrhh', 'rrhh expensas hogar'):
  return 'RRHH'
 return categoria

def centro(s):
 n=norm(s)
 if ('central' in n and 'hogar' in n) or n=='expensas hogar':return 'Areas Centrales Hogar'
 if n=='cd':return 'CD'
 for c in CENTROS[:13]:
  if norm(c)==n:return c
 return None


@st.cache_data(show_spinner=False)
def leer(datos):
 libro=pd.ExcelFile(io.BytesIO(datos))
 meses=[m for m in MESES if m in libro.sheet_names]
 if not meses:raise ValueError('No se encontraron hojas mensuales Ene a Ago.')
 gastos=[];ingresos=[];ingresos_cc=[];ventas=[];avisos=[]
 excluidos={norm(x) for x in EXCLUIR}
 for m in meses:
  df=pd.read_excel(libro,sheet_name=m)
  df.columns=[str(c).strip() for c in df.columns]
  cols=list(df.columns)
  if len(cols)<5:continue
  cuenta,area=cols[0],cols[1]
  mapa={c:centro(c) for c in cols[4:]}
  faltantes=[c for c in CENTROS if c not in set(mapa.values())]
  if faltantes:avisos.append(f'{MESES[m]}: centros ausentes: {", ".join(faltantes)}')
  bloque=''
  for _,r in df.iterrows():
   nombre=str(r[cuenta]).strip()
   if nombre in ('nan','None',''):continue
   key=norm(nombre)
   if key=='ventas' or key in ('otros ingresos','total otros ingresos'):
    # Cada fila de ingreso agregada se contabiliza una vez, sin sumar subcuentas.
    for col,cc in mapa.items():
     if cc is None:continue
     val=pd.to_numeric(r[col],errors='coerce')
     if pd.notna(val):
      ingresos.append((m,float(val)))
      ingresos_cc.append((m,cc,float(val)))
      if key=='ventas' and cc in CENTROS[:13]:
       ventas.append((m,float(val)))
    if key!='ventas':bloque='Otros ingresos'
    continue
   if key in excluidos:
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
   categoria=categoria_agrupada(categoria)
   for col,cc in mapa.items():
    if cc is None:continue
    val=pd.to_numeric(r[col],errors='coerce')
    if pd.notna(val) and val!=0:gastos.append((m,bloque,nombre,categoria,cc,-float(val)))
 tabla=pd.DataFrame(gastos,columns=['Mes','Bloque','Cuenta','Categoría','Centro','Gasto'])
 return tabla,pd.DataFrame(ingresos,columns=['Mes','Ingreso']),pd.DataFrame(ingresos_cc,columns=['Mes','Centro','Ingreso centro']),pd.DataFrame(ventas,columns=['Mes','Venta']),avisos

def resumen_ejecutivo(top,detalle,ingresos,gastos,concepto,meses):
 incidencia=gastos/ingresos*100 if ingresos else 0
 lineas=[f"Período: {', '.join(meses)}. Ingresos acumulados (ventas + otros ingresos): {money(ingresos)}. Gastos acumulados netos: {money(gastos)}. Incidencia: {pct(incidencia)}."]
 if not top.empty:
  lider=top.iloc[0]
  lineas.append(f"Principal categoría: {lider['Categoría']}, {money(lider['Gasto'])}, incidencia sobre ingresos: {pct(lider['% sobre ingresos'])}.")
  lineas.append(f"El Top 10 totaliza {money(top.Gasto.sum())}.")
 if not detalle.empty:
  mayor=detalle.iloc[0]
  lineas.append(f"En {concepto}, el centro de mayor gasto es {mayor['Centro']}, con {money(mayor['Gasto'])}.")
 lineas.append(f"Gasto total del concepto seleccionado, sumando centros: {money(detalle.Gasto.sum())}.")
 return lineas

def crear_pdf(resumen,top,detalle,periodo,concepto):
 buffer=io.BytesIO()
 doc=SimpleDocTemplate(buffer,pagesize=(29.7*cm,21*cm),rightMargin=1.5*cm,leftMargin=1.5*cm,topMargin=1.4*cm,bottomMargin=1.4*cm)
 estilos=getSampleStyleSheet()
 estilos.add(ParagraphStyle(name='YTitle',parent=estilos['Title'],fontSize=17,textColor=colors.HexColor('#022f40')))
 estilos.add(ParagraphStyle(name='YBody',parent=estilos['BodyText'],fontSize=9,leading=13,spaceAfter=6))
 elementos=[Paragraph('YUHMAK HOGAR | ADMINISTRACIÓN',estilos['YTitle']),Paragraph('Informe EERR | '+escape(periodo),estilos['YBody'])]
 for parrafo in resumen:elementos.append(Paragraph(escape(parrafo),estilos['YBody']))
 def tabla(filas,anchos):
  t=Table(filas,colWidths=anchos,repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#022f40')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),8),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#edf2f5')]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
  return t
 elementos.append(Paragraph('Top 10 de gastos sobre ingresos',estilos['Heading2']))
 filas=[['#','Categoría','Gasto ($)','% ingresos']]
 for i,(_,r) in enumerate(top.iterrows(),1):filas.append([str(i),Paragraph(escape(str(r['Categoría'])),estilos['YBody']),money(r['Gasto']),pct(r['% sobre ingresos'])])
 elementos.append(tabla(filas,[1*cm,13*cm,6*cm,4*cm]))
 elementos.append(Paragraph('Distribución por centro de costos: '+escape(concepto),estilos['Heading2']))
 filas=[['#','Centro','Gasto ($)']]
 for i,(_,r) in enumerate(detalle.iterrows(),1):
  filas.append([str(i),str(r['Centro']),money(r['Gasto'])])
 elementos.append(tabla(filas,[1*cm,16*cm,7*cm]))
 elementos.append(Spacer(1,0.3*cm))
 elementos.append(Paragraph('Metodología: ingresos = ventas + otros ingresos. Gastos netos = suma de importes negativos y positivos de los centros de costos, con signo invertido para presentar el gasto neto positivo, excluyendo ingresos, costo de ventas y subtotales. No se utiliza RN ni conciliación. RRHH y RRHH - Expensas Hogar se agrupan en RRHH, manteniendo el detalle por centro de costos.',estilos['YBody']))
 doc.build(elementos)
 return buffer.getvalue()

def render():
 st.markdown('<div style="background:#022f40;color:white;padding:26px;border-radius:16px"><h1 style="color:white;margin:0">Administración | EERR Hogar</h1><div style="color:#f7d558">Ingresos y gastos · 15 centros de costos</div></div>',unsafe_allow_html=True)
 st.caption('Módulo independiente de Postventa. Los datos se procesan a partir del Excel cargado en esta sesión.')
 archivo=st.file_uploader('Cargar EERR por Sucursal (.xlsx)',type=['xlsx'],key='admin_eerr')
 if archivo is None:
  st.info('Cargá el Excel para visualizar el análisis.');return
 try:tabla,ingresos,ingresos_centros,ventas,avisos=leer(archivo.getvalue())
 except Exception as e:st.error('No se pudo interpretar el archivo: '+str(e));return
 if tabla.empty or ingresos.empty:st.warning('No se encontraron gastos o ingresos válidos.');return
 meses=list(ingresos.Mes.drop_duplicates())
 nombres=[MESES[m] for m in meses]
 opciones=['Todos los meses','Primer cuatrimestre','Segundo cuatrimestre','Personalizado']
 periodo=st.selectbox('Períodos a analizar',opciones,key='admin_periodo_v9')
 if periodo=='Todos los meses':seleccion=nombres
 elif periodo=='Primer cuatrimestre':seleccion=[MESES[m] for m in ('Ene','Feb','Mar','Abr') if m in meses]
 elif periodo=='Segundo cuatrimestre':seleccion=[MESES[m] for m in ('May','Jun','Jul','Ago') if m in meses]
 else:
  st.caption('Activá los meses que querés analizar.')
  columnas=st.columns(4);seleccion=[]
  for i,nombre in enumerate(nombres):
   with columnas[i%4]:
    if st.checkbox(nombre,value=True,key='admin_mes_personal_v9_'+nombre):seleccion.append(nombre)
 elegidos=[m for m in meses if MESES[m] in seleccion]
 if not elegidos:st.warning('Seleccioná al menos un mes.');return
 t=tabla[tabla.Mes.isin(elegidos)]
 ingreso_total=ingresos[ingresos.Mes.isin(elegidos)].Ingreso.sum()
 venta_total=ventas[ventas.Mes.isin(elegidos)].Venta.sum()
 gasto_total=t.Gasto.sum()
 c1,c2=st.columns(2)
 c1.metric('Ingresos acumulados',money(ingreso_total))
 c2.metric('Gastos acumulados',money(gasto_total))
 st.caption('Ingresos = ventas + otros ingresos. Gastos netos = egresos negativos menos ajustes positivos de los centros de costos, sin RN.')
 top=t.groupby('Categoría',as_index=False).Gasto.sum().sort_values('Gasto',ascending=False).head(10).copy()
 top['% sobre ingresos']=top.Gasto/ingreso_total*100 if ingreso_total else float('nan')
 st.subheader('Top 10 · categorías de gasto')
 st.dataframe(top.rename(columns={'Categoría':'Concepto','Gasto':'Importe ($)'}).style.format({'Importe ($)':money,'% sobre ingresos':lambda x:pct(x) if pd.notna(x) else 'N/D'}),hide_index=True,use_container_width=True)
 orden_top=top.Categoría.tolist()
 graf_top=alt.Chart(top).mark_bar().encode(y=alt.Y('Categoría:N',sort=orden_top,title=None),x=alt.X('Gasto:Q',title='Gasto ($)'),tooltip=['Categoría:N',alt.Tooltip('Gasto:Q',format=',.0f'),alt.Tooltip('% sobre ingresos:Q',format='.2f')]).properties(height=360)
 st.altair_chart(graf_top,use_container_width=True)
 st.subheader('Detalle por centro de costos')
 concepto=st.selectbox('Seleccionar gasto para analizar',top.Categoría.tolist())
 detalle=t[t.Categoría==concepto].groupby('Centro',as_index=False).Gasto.sum()
 detalle=pd.DataFrame({'Centro':CENTROS}).merge(detalle,on='Centro',how='left').fillna({'Gasto':0})
 detalle=detalle.sort_values('Gasto',ascending=False).reset_index(drop=True)
 st.metric('Gasto distribuido en centros',money(detalle.Gasto.sum()))
 st.dataframe(detalle[['Centro','Gasto']].rename(columns={'Centro':'Sucursal / centro de costos','Gasto':'Importe ($)'}).style.format({'Importe ($)':money}),hide_index=True,use_container_width=True)
 orden=detalle.Centro.tolist()
 graf=alt.Chart(detalle).mark_bar().encode(y=alt.Y('Centro:N',sort=orden,title=None),x=alt.X('Gasto:Q',title='Gasto ($)'),tooltip=['Centro:N',alt.Tooltip('Gasto:Q',format=',.0f')]).properties(height=480)
 st.altair_chart(graf,use_container_width=True)
 st.subheader('Resumen ejecutivo')
 resumen=resumen_ejecutivo(top,detalle,ingreso_total,gasto_total,concepto,seleccion)
 for parrafo in resumen:st.write(parrafo)
 pdf=crear_pdf(resumen,top,detalle,', '.join(seleccion),concepto)
 st.download_button('Descargar informe ejecutivo completo (PDF)',data=pdf,file_name='Yuhmak_Administracion_EERR_Informe_Ejecutivo.pdf',mime='application/pdf',type='primary')
 st.download_button('Descargar distribución (CSV)',detalle.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),file_name='Administracion_EERR_distribucion.csv',mime='text/csv')
 if avisos:
  with st.expander('Advertencias del archivo'):
   for aviso in sorted(set(avisos)):st.warning(aviso)

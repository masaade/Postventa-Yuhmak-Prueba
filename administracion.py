import io
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
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
 if ('central' in n and 'hogar' in n) or n=='expensas hogar':return 'Areas Centrales Hogar'
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
  # 'Expensas Hogar' (enero-mayo) y 'Areas Centrales Hogar' (junio-agosto) son el mismo centro de costos.
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

def resumen_ejecutivo(top, det, ventas_total, gastos_total, concepto, rn, dist, meses_sel):
    lider=top.iloc[0] if not top.empty else None
    mayor=det.iloc[0] if not det.empty else None
    participacion=gastos_total/ventas_total*100 if ventas_total else 0
    top_suma=top.Gasto.sum() if not top.empty else 0
    lineas=[
      f"Período analizado: {', '.join(meses_sel)}. Ventas acumuladas: {money(ventas_total)}. Gastos analizados: {money(gastos_total)}, equivalentes al {pct(participacion)} de las ventas.",
      (f"El principal concepto de gasto es {lider['Categoría']}, con {money(lider['Gasto'])} y una incidencia del {pct(lider['% sobre ventas'])} sobre las ventas." if lider is not None else 'No se identificaron conceptos de gasto.'),
      f"Los diez principales conceptos concentran el {pct(top_suma/gastos_total*100 if gastos_total else 0)} de los gastos analizados.",
      (f"Para el gasto seleccionado ({concepto}), el centro de costos de mayor importe es {mayor['Centro']}, con {money(mayor['Gasto'])} ({pct(mayor['% del gasto distribuido'])} del total distribuido)." if mayor is not None else f"No hay distribución disponible para {concepto}."),
      f"Conciliación del concepto seleccionado: consolidado {money(rn)}, suma de centros {money(dist)} y diferencia {money(dist-rn)}."
    ]
    return lineas

def crear_pdf(resumen, top, det, conc, titulo_periodo, concepto, ventas_total, gastos_total):
    buffer=io.BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=(29.7*cm,21*cm),rightMargin=1.45*cm,leftMargin=1.45*cm,topMargin=1.3*cm,bottomMargin=1.3*cm)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='YTitle',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=17,textColor=colors.HexColor('#022f40'),spaceAfter=8))
    styles.add(ParagraphStyle(name='YHead',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=11,textColor=colors.HexColor('#022f40'),spaceBefore=11,spaceAfter=6))
    styles.add(ParagraphStyle(name='YBody',parent=styles['BodyText'],fontName='Helvetica',fontSize=9,leading=13,spaceAfter=6))
    styles.add(ParagraphStyle(name='YCell',parent=styles['BodyText'],fontName='Helvetica',fontSize=7.5,leading=9))
    story=[Paragraph('YUHMAK HOGAR | ADMINISTRACIÓN',styles['YTitle']),Paragraph(f'Informe ejecutivo de gastos EERR | {escape(titulo_periodo)}',styles['YBody'])]
    for x in resumen:story.append(Paragraph(escape(x),styles['YBody']))
    story.append(Paragraph('Top 10 | Participación de gastos sobre ventas',styles['YHead']))
    rows=[['#','Concepto','Importe ($)','% sobre ventas','% de gastos']]
    for i,(_,r) in enumerate(top.iterrows(),1):rows.append([str(i),Paragraph(escape(str(r['Categoría'])),styles['YCell']),money(r['Gasto']),pct(r['% sobre ventas']),pct(r['% del gasto'])])
    def tabla(rows,widths):
      t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
      t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#022f40')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#eef3f5')]),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#b4c1c6'))]))
      return t
    story.append(tabla(rows,[1*cm,11*cm,4.2*cm,4*cm,4*cm]))
    story.append(Paragraph('Distribución por centro de costos',styles['YHead']))
    story.append(Paragraph('Concepto: '+escape(str(concepto)),styles['YBody']))
    rows=[['#','Centro de costos','Importe ($)','% del gasto distribuido','% sobre ventas']]
    for i,(_,r) in enumerate(det.iterrows(),1):rows.append([str(i),Paragraph(escape(str(r['Centro'])),styles['YCell']),money(r['Gasto']),pct(r['% del gasto distribuido']),pct(r['% sobre ventas totales'])])
    story.append(tabla(rows,[1*cm,10*cm,4.3*cm,4.5*cm,4.4*cm]))
    story.append(Paragraph('Conciliación por mes',styles['YHead']))
    rows=[['Mes','Gastos RN','Suma de centros','Diferencia']]
    for _,r in conc.iterrows():rows.append([r['Mes'],money(r['RN gastos']),money(r['Centros de costos']),money(r['Diferencia'])])
    story.append(tabla(rows,[5*cm,6*cm,6*cm,6*cm]))
    story.append(Spacer(1,0.25*cm))
    story.append(Paragraph('Nota metodológica: gastos de cuentas con saldo negativo, sin costo de mercadería vendida, ingresos ni subtotales. La distribución utiliza el total de los centros de costos como denominador; una diferencia de conciliación distinta de cero requiere revisión. Los importes y porcentajes se calculan a partir del Excel cargado.',styles['YBody']))
    def pie(canvas,doc):
      canvas.setFont('Helvetica',8);canvas.setFillColor(colors.grey)
      canvas.drawString(1.45*cm,0.8*cm,'Reporte generado desde el módulo Administración | Yuhmak Hogar')
      canvas.drawRightString(28.25*cm,0.8*cm,f'Página {doc.page}')
    doc.build(story,onFirstPage=pie,onLaterPages=pie)
    return buffer.getvalue()

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
 st.subheader('Resumen ejecutivo')
 resumen=resumen_ejecutivo(top,det,v,total,opcion,rn,dist,sel)
 for parrafo in resumen:st.write(parrafo)
 st.caption('El resumen se actualiza automáticamente con los filtros y el concepto seleccionados.')
 pdf=crear_pdf(resumen,top,det,conc[conc.Mes.isin(sel)],', '.join(sel),opcion,v,total)
 st.download_button('Descargar informe ejecutivo completo (PDF)',data=pdf,file_name='Yuhmak_Administracion_EERR_Informe_Ejecutivo.pdf',mime='application/pdf',type='primary')
 st.download_button('Descargar distribución (CSV)',det.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),file_name='Administracion_EERR_distribucion.csv',mime='text/csv')
 with st.expander('Auditoría y advertencias del archivo'):
  for a in sorted(set(avisos)):st.warning(a)
  st.write('Conciliación por mes (gastos de las cuentas seleccionadas)')
  st.dataframe(conc[conc.Mes.isin(sel)].style.format({'RN gastos':money,'Centros de costos':money,'Diferencia':money}),hide_index=True,use_container_width=True)
  st.caption('El porcentaje por centro de costos utiliza como denominador el total distribuido en centros; si difiere del RN, se informa la diferencia. Las columnas «Expensas Hogar» y «Áreas Centrales Hogar» se unifican como un único centro de costos.')

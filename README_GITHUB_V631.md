# V63.1 — PRUEBAS, NO PRODUCCIÓN

1. Crear una rama nueva en GitHub, por ejemplo `pruebas-v63-1`.
2. Subir `app.py`, `executive_ui.py`, `administracion.py`, `requirements.txt` y `.streamlit/config.toml` de este ZIP a la raíz de esa rama.
3. En Streamlit Community Cloud, crear una aplicación de PRUEBAS apuntando a esa rama y a `app.py`. No cambiar la rama de la aplicación activa.
4. Cargar los cuatro Excel SAP desde el panel lateral. Luego autenticarse como administrador y cargar el Excel de Finanzas desde su propio módulo.
5. Probar meses y acumulado. Los indicadores de flujo usan fechas de documentos/movimientos. El stock histórico no se inventa.
6. NO pasar a producción hasta contrastar con SAP. No se ejecutaron pruebas de interfaz Streamlit ni despliegue real.

NOTAS: la copia original contenía credencial de prueba fija `admin123`. Debe sustituirse por `st.secrets` y autorización real antes de cualquier despliegue accesible a terceros. Las fechas faltantes de recuperaciones físicas impiden conciliación mensual completa. La clasificación histórica de V63 es más amplia que el criterio documental estricto de la vista mensual. Scrap: 3.012.767,93 anual sin fecha de realización; no se prorratea.

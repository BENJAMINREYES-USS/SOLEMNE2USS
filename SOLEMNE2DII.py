# SOLEMNE2DII.py
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Funciones
def formatear_pesos(valor):
    if pd.isna(valor):
        return "-"
    return "${:,.0f}".format(valor)

meses_nombre = {
    1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril",
    5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto",
    9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
}


# Título con fuente personalizada
st.markdown("<h1 style='font-family:Helvetica; color:#2F4F4F;'>Análisis Interactivo de Recaudación DDI 2011-2012</h1>", unsafe_allow_html=True)
st.markdown(
    "Explore la recaudación mensual y anual de ingresos privados (DDI) en Chile. "
    "Compare años, filtre meses y vea estadísticas, KPIs y gráficos interactivos."
)

# Cargar datos de la API
@st.cache_data
def cargar_datos():
    url = "https://datos.gob.cl/api/action/datastore_search"
    params = {"resource_id": "3ae55f10-7916-47b8-a65c-82e73a40a2cd", "limit": 1000}
    response = requests.get(url, params=params)
    data_json = response.json()
    records = data_json['result']['records']
    df = pd.DataFrame(records)
    df['recaudacion'] = pd.to_numeric(df['recaudacion'], errors='coerce')
    df['mes'] = df['mes'].astype(int)
    df['ano'] = df['ano'].astype(str)
    return df

df = cargar_datos()

# Selección de años y meses
anos_disponibles = sorted(df['ano'].unique())
ano_seleccionados = st.multiselect("Seleccione los años a comparar:", options=anos_disponibles, default=anos_disponibles)

meses_disponibles = sorted(df['mes'].unique())
mes_seleccionados = st.multiselect(
    "Seleccione los meses a mostrar:", 
    options=meses_disponibles, 
    default=meses_disponibles,
    format_func=lambda x: f"{x} ({meses_nombre[x]})"
)

df_filtrado = df[(df['ano'].isin(ano_seleccionados)) & (df['mes'].isin(mes_seleccionados))]

# Tabla de recaudación mensual
st.subheader("Tabla de recaudación mensual")
df_tabla = df_filtrado.copy()
df_tabla['Mes'] = df_tabla['mes'].apply(lambda x: f"{x} ({meses_nombre[x]})")
df_tabla['Recaudación ($)'] = df_tabla['recaudacion'].apply(formatear_pesos)
st.dataframe(df_tabla[['ano','Mes','Recaudación ($)']].sort_values(['ano','Mes']))

# KPIs por año ajustados
st.subheader("Indicadores clave por año")
for ano in ano_seleccionados:
    df_ano = df_filtrado[df_filtrado['ano']==ano]
    if not df_ano.empty:
        total = df_ano['recaudacion'].sum()
        promedio = df_ano['recaudacion'].mean()
        mes_max = df_ano.loc[df_ano['recaudacion'].idxmax(), 'mes']
        monto_max = df_ano.loc[df_ano['recaudacion'].idxmax(), 'recaudacion']
        col1, col2, col3 = st.columns([1.2,1.2,2])
        col1.metric(f"Total {ano}", formatear_pesos(total))
        col2.metric(f"Promedio mensual {ano}", formatear_pesos(promedio))
        # Mes completo en el KPI, monto como valor
        col3.metric(f"Mes con mayor recaudación {ano}", f"{meses_nombre[mes_max]}", formatear_pesos(monto_max))

# Gráfico interactivo de recaudación mensual
st.subheader("Gráfico comparativo de recaudación mensual")
df_grafico = df_filtrado.copy()
df_grafico['Mes'] = df_grafico['mes'].apply(lambda x: f"{x} ({meses_nombre[x]})")
fig = px.line(
    df_grafico,
    x='Mes',
    y='recaudacion',
    color='ano',
    markers=True,
    labels={'recaudacion':'Recaudación ($)', 'ano':'Año'},
    hover_data={'recaudacion':True, 'ano':True, 'Mes':True},
    title="Recaudación mensual por año"
)
fig.update_layout(template="plotly_white", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# Total anual por año
st.subheader("Total anual de recaudación")
recaudacion_total = df.groupby('ano')['recaudacion'].sum().reset_index()
recaudacion_total['Total ($)'] = recaudacion_total['recaudacion'].apply(formatear_pesos)
fig2 = px.bar(
    recaudacion_total,
    x='ano',
    y='recaudacion',
    text='Total ($)',
    color='ano',
    labels={'ano':'Año', 'recaudacion':'Recaudación total ($)'},
    title="Total anual de recaudación"
)
fig2.update_layout(template="plotly_white")
st.plotly_chart(fig2, use_container_width=True)

# Heatmap de meses vs años
st.subheader("Heatmap de recaudación mensual por año")
heatmap_data = df_filtrado.pivot(index='mes', columns='ano', values='recaudacion').fillna(0)
heatmap_data.index = [f"{m} ({meses_nombre[m]})" for m in heatmap_data.index]
fig3 = px.imshow(heatmap_data, text_auto=True, color_continuous_scale='Viridis', aspect="auto")
fig3.update_layout(xaxis_title="Año", yaxis_title="Mes", title="Heatmap de recaudación mensual")
st.plotly_chart(fig3, use_container_width=True)

# Resumen estadístico por año
st.subheader("Resumen estadístico por año")
estadisticas = []
for ano in ano_seleccionados:
    df_ano = df_filtrado[df_filtrado['ano']==ano]
    if not df_ano.empty:
        mes_max_num = df_ano.loc[df_ano['recaudacion'].idxmax(),'mes']
        mes_min_num = df_ano.loc[df_ano['recaudacion'].idxmin(),'mes']
        estadisticas.append({
            "Año": ano,
            "Total recaudado": formatear_pesos(df_ano['recaudacion'].sum()),
            "Promedio mensual": formatear_pesos(df_ano['recaudacion'].mean()),
            "Mes con mayor recaudación": f"{meses_nombre[mes_max_num]} → {formatear_pesos(df_ano['recaudacion'].max())}",
            "Mes con menor recaudación": f"{meses_nombre[mes_min_num]} → {formatear_pesos(df_ano['recaudacion'].min())}"
        })
st.dataframe(pd.DataFrame(estadisticas))

# Top 3 meses por recaudación
st.subheader("Top 3 meses con mayor recaudación")
df_top = df_filtrado.sort_values('recaudacion', ascending=False).head(3)
df_top['Mes'] = df_top['mes'].apply(lambda x: f"{x} ({meses_nombre[x]})")
df_top['Recaudación ($)'] = df_top['recaudacion'].apply(formatear_pesos)
st.dataframe(df_top[['ano','Mes','Recaudación ($)']])

# Resumen Ejecutivo (comentarios dinámicos)
st.subheader("Resumen Ejecutivo")

# Total por año
totales_ano = df_filtrado.groupby('ano')['recaudacion'].sum()
if not totales_ano.empty:
    ano_max = totales_ano.idxmax()
    ano_min = totales_ano.idxmin()
    st.markdown(f"- El año con **mayor recaudación total** fue {ano_max} con {formatear_pesos(totales_ano[ano_max])}.")
    st.markdown(f"- El año con **menor recaudación total** fue {ano_min} con {formatear_pesos(totales_ano[ano_min])}.")

# Meses con mayor y menor recaudación
if not df_filtrado.empty:
    idx_max = df_filtrado['recaudacion'].idxmax()
    idx_min = df_filtrado['recaudacion'].idxmin()
    st.markdown(f"- El **mes con mayor recaudación** fue {meses_nombre[df_filtrado.loc[idx_max,'mes']]} del año {df_filtrado.loc[idx_max,'ano']}, con {formatear_pesos(df_filtrado.loc[idx_max,'recaudacion'])}.")
    st.markdown(f"- El **mes con menor recaudación** fue {meses_nombre[df_filtrado.loc[idx_min,'mes']]} del año {df_filtrado.loc[idx_min,'ano']}, con {formatear_pesos(df_filtrado.loc[idx_min,'recaudacion'])}.")

# Diferencias y tendencias
if len(ano_seleccionados) > 1:
    st.markdown("- Comparando los años seleccionados, se puede observar la tendencia de crecimiento o disminución entre ellos.")
    diff = totales_ano.max() - totales_ano.min()
    st.markdown(f"- La diferencia entre el año con mayor y menor recaudación es de {formatear_pesos(diff)}.")

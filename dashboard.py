import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. Configuracion de la pagina principal
st.set_page_config(page_title="Dashboard de Optimizacion de Procesos", layout="wide")

st.title("Dashboard Avanzado de Optimizacion de Tiempos")
st.markdown("Analisis detallado de la duracion de actividades y eficiencia del proceso.")

# Nombre del archivo de Excel
archivo = "datos_dashboard_python.xlsx.xlsx"

# Funcion para convertir tiempos a minutos enteros (d = Dias, h = Horas, m = Minutos)
def texto_a_minutos(texto):
    if pd.isna(texto) or str(texto).strip() == '0' or str(texto).strip() == '':
        return 0
    texto = str(texto).lower().strip()
    
    # CORRECCIÓN DE DIGITACIÓN: Si detecta cualquier rastro del error en Transporte I,
    # lo fuerza a ser exactamente 1 dia y 6 horas (1 * 24 * 60 + 6 * 60 = 1800 minutos)
    if "1d 6h1d" in texto or "20d" in texto and "6h" in texto:
        return 1800
        
    minutos = 0
    dias = re.search(r'(\d+)\s*d', texto)
    if dias: minutos += int(dias.group(1)) * 24 * 60
    horas = re.search(r'(\d+)\s*h', texto)
    if horas: minutos += int(horas.group(1)) * 60
    mins = re.search(r'(\d+)\s*m', texto)
    if mins: minutos += int(mins.group(1))
    return minutos

try:
    # 2. Cargar los datos desde el Excel
    df_procesos = pd.read_excel(archivo, sheet_name='Datos_Procesos')
    df_resumen = pd.read_excel(archivo, sheet_name='Resumen_Mejora')
    
    # Limpieza de datos
    df_procesos['Escenario_Limpio'] = df_procesos['Escenario'].str.strip()
    df_procesos['Tipo_Limpio'] = df_procesos['Tipo'].str.strip()
    df_procesos['Nombre_Limpio'] = df_procesos['Nombre'].str.strip()
    
    # Reemplazar el tipo 'Tarea' por 'Actividad' en los datos
    df_procesos['Tipo_Limpio'] = df_procesos['Tipo_Limpio'].replace('Tarea', 'Actividad')
    df_procesos['Tipo'] = df_procesos['Tipo'].replace('Tarea', 'Actividad')
    
    # REGLA EXACTA PEDIDA: Forzar a TRANSPORTE I en ambos escenarios a tener "1d 6h" y "20d"
    df_procesos.loc[df_procesos['Nombre_Limpio'].str.upper() == 'TRANSPORTE I', 'Tiempo promedio'] = '1d 6h'
    df_procesos.loc[df_procesos['Nombre_Limpio'].str.upper() == 'TRANSPORTE I', 'Tiempo total'] = '20d'
    df_procesos.loc[df_procesos['Nombre_Limpio'].str.upper() == 'TRANSPORTE I', 'Tiempo mínimo'] = '1d 6h'
    df_procesos.loc[df_procesos['Nombre_Limpio'].str.upper() == 'TRANSPORTE I', 'Tiempo máximo'] = '1d 6h'
# Extraer metricas del resumen
    t_asis = df_resumen.loc[df_resumen['Métrica'] == 'Tiempo Total AS-IS', 'Valor'].values[0]
    t_tobe = df_resumen.loc[df_resumen['Métrica'] == 'Tiempo Total TO-BE', 'Valor'].values[0]
    ahorro = df_resumen.loc[df_resumen['Métrica'] == 'Variación (Resta)', 'Valor'].values[0]
    pct_mejora = float(df_resumen.loc[df_resumen['Métrica'] == 'Porcentaje de Mejora', 'Valor'].values[0]) * 100
    
    # =========================================================
    # KPI PRINCIPAL: PORCENTAJE DE MEJORA (FIJO ARRIBA)
    # =========================================================
    st.markdown("### Resumen Ejecutivo de Rendimiento")
    col_kpi1, col_kpi2, col_kpi3 = st.columns([1, 1, 2])
    with col_kpi1:
        # Esto quita la palabra "meses" o "m" confusa y la deja limpia
        texto_asis_corregido = str(t_asis).replace("meses", "minutos").replace("28m", "28 minutos")
        st.metric(label="Tiempo Total Inicial (AS-IS)", value=texto_asis_corregido)
    with col_kpi2:
        texto_tobe_corregido = str(t_tobe).replace("meses", "minutos")
        st.metric(label="Tiempo Total Final (TO-BE)", value=texto_tobe_corregido)
    with col_kpi3:
        st.metric(label="Porcentaje de Eficiencia / Mejora Global", value=f"{pct_mejora:.2f}%", delta=ahorro)
        texto_tobe_corregido = str(t_tobe).replace("meses", "minutos")
        st.metric(label="Tiempo Total Final (TO-BE)", value=texto_tobe_corregido)
    with col_kpi3:
        st.metric(label="Porcentaje de Eficiencia / Mejora Global", value=f"{pct_mejora:.2f}%", delta=ahorro)
    # =========================================================
    st.markdown("### Resumen Ejecutivo de Rendimiento")
    col_kpi1, col_kpi2, col_kpi3 = st.columns([1, 1, 2])
    with col_kpi1:
        st.metric(label="Tiempo Total Inicial (AS-IS)", value=t_asis)
    with col_kpi2:
        st.metric(label="Tiempo Total Final (TO-BE)", value=t_tobe)
    with col_kpi3:
        st.metric(label="Porcentaje de Eficiencia / Mejora Global", value=f"{pct_mejora:.2f}%", delta=ahorro)
    
    st.markdown("---")

    # 3. BOTONERA INTERACTIVA PARA LOS GRÁFICOS
    st.markdown("## Seccion de Graficos Interactivos")
    
    tab_asis, tab_tobe, tab_comparativa_graf = st.tabs([
        "📊 Grafico 1: Escenario AS-IS", 
        "📊 Grafico 2: Escenario TO-BE", 
        "📊 Grafico 3: Comparativa AS-IS vs TO-BE y % de Mejora"
    ])
    
    # --- GRÁFICO 1: EXCLUSIVO AS-IS ---
    with tab_asis:
        st.markdown("### Duracion de Actividades en el Escenario AS-IS (Actual)")
        df_asis_only = df_actividades[df_actividades['Escenario_Limpio'] == 'AS - IS']
        fig1 = px.bar(
            df_asis_only, x="Actividad", y="Minutos Promedio", text="Tiempo promedio",
            labels={"Actividad": "Actividades AS-IS", "Minutos Promedio": "Minutos de Duracion"},
            color_discrete_sequence=["#FF4B4B"]
        )
        fig1.update_traces(textposition='outside')
        fig1.update_layout(height=450, yaxis=dict(type='linear', tickformat='d', title="Minutos Reales"))
        st.plotly_chart(fig1, use_container_width=True)

    # --- GRÁFICO 2: EXCLUSIVO TO-BE ---
    with tab_tobe:
        st.markdown("### Duracion de Actividades en el Escenario TO-BE (Propuesto)")
        df_tobe_only = df_actividades[df_actividades['Escenario_Limpio'] == 'TO - BE']
        fig2 = px.bar(
            df_tobe_only, x="Actividad", y="Minutos Promedio", text="Tiempo promedio",
            labels={"Actividad": "Actividades TO-BE", "Minutos Promedio": "Minutos de Duracion"},
            color_discrete_sequence=["#1C83E1"]
        )
        fig2.update_traces(textposition='outside')
        fig2.update_layout(height=450, yaxis=dict(type='linear', tickformat='d', title="Minutos Reales"))
        st.plotly_chart(fig2, use_container_width=True)

    # --- GRÁFICO 3: COMPARATIVA ---
    with tab_comparativa_graf:
        st.markdown("### Analisis Comparativo y Porcentaje de Rendimiento del Proyecto")
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("#### Comparativa Directa de Tiempos por Actividad")
            fig3 = px.bar(
                df_actividades, x="Actividad", y="Minutos Promedio", color="Escenario_Limpio",
                barmode="group", text="Tiempo promedio",
                labels={"Actividad": "Actividades", "Minutos Promedio": "Minutos", "Escenario_Limpio": "Escenario"},
                color_discrete_sequence=["#FF4B4B", "#1C83E1"]
            )
            fig3.update_traces(textposition='outside')
            fig3.update_layout(height=450, yaxis=dict(type='linear', tickformat='d', title="Minutos Reales"))
            st.plotly_chart(fig3, use_container_width=True)
            
        with col_graf2:
            st.markdown("#### Impacto de la Optimizacion de Tiempo Total")
            
            df_pct_bar = pd.DataFrame({
                "Etapa": ["Tiempo Base (AS-IS)", "Tiempo Reducido (TO-BE)", "Mejora Lograda"],
                "Valor": [100.0, 100.0 - pct_mejora, pct_mejora],
                "Color": ["Base Actual", "Eficiencia Optima", "Porcentaje Ahorrado"]
            })
            
            fig_bar_pct = px.bar(
                df_pct_bar, x="Etapa", y="Valor", color="Color",
                text=df_pct_bar["Valor"].apply(lambda x: f"{x:.2f}%"),
                labels={"Etapa": "Analisis de Impacto", "Valor": "Porcentaje (%)"},
                color_discrete_map={
                    "Base Actual": "#FF4B4B",
                    "Eficiencia Optima": "#1C83E1",
                    "Porcentaje Ahorrado": "#2CA02C"
                }
            )
            fig_bar_pct.update_traces(textposition='outside', textfont=dict(size=14))
            fig_bar_pct.update_layout(height=450, yaxis=dict(type='linear', range=[0, 115]), showlegend=False)
            st.plotly_chart(fig_bar_pct, use_container_width=True)

    st.markdown("---")
    
    # =========================================================
    # BLOQUE DE TABLAS ACTUALIZADAS
    # =========================================================
    st.markdown("<h2>Seccion de Reportes y Tablas Detalladas</h2>", unsafe_allow_html=True)
    
    # TABLA 1: Solo AS-IS
    st.markdown("<h3 style='color: #FF4B4B;'>📋 Tabla de Actividades: Escenario AS-IS (Actual)</h3>", unsafe_allow_html=True)
    df_asis_filtrado = df_procesos[df_procesos['Escenario_Limpio'] == 'AS - IS'][
        ['Nombre', 'Tipo', 'Instancias iniciadas', 'Tiempo mínimo', 'Tiempo máximo', 'Tiempo promedio', 'Tiempo total']
    ]
    st.dataframe(df_asis_filtrado, use_container_width=True, hide_index=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # TABLA 2: Solo TO-BE
    st.markdown("<h3 style='color: #1C83E1;'>📋 Tabla de Actividades: Escenario TO-BE (Propuesto)</h3>", unsafe_allow_html=True)
    df_tobe_filtrado = df_procesos[df_procesos['Escenario_Limpio'] == 'TO - BE'][
        ['Nombre', 'Tipo', 'Instancias iniciadas', 'Tiempo mínimo', 'Tiempo máximo', 'Tiempo promedio', 'Tiempo total']
    ]
    st.dataframe(df_tobe_filtrado, use_container_width=True, hide_index=True)
    
    # TABLA 3: Comparativa general completa
    st.markdown("<h3 style='color: #2CA02C;'>📊 Tabla Comparativa Final (Consolidado de Datos)</h3>", unsafe_allow_html=True)
    df_completa_mostrar = df_procesos[[
        'Escenario', 'Nombre', 'Tipo', 'Instancias completadas', 
        'Instancias iniciadas', 'Tiempo promedio', 'Tiempo total'
    ]]
    st.dataframe(df_completa_mostrar, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Ocurrio un error al procesar los datos: {e}")

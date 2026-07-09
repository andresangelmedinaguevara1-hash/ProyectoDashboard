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
    # 2. Cargar los datos
    df_procesos = pd.read_excel(archivo, sheet_name='Datos_Procesos')
    df_resumen = pd.read_excel(archivo, sheet_name='Resumen_Mejora')
    
    # Limpieza
    df_procesos['Escenario_Limpio'] = df_procesos['Escenario'].str.strip()
    df_procesos['Tipo_Limpio'] = df_procesos['Tipo'].str.strip().replace('Tarea', 'Actividad')
    df_procesos['Nombre_Limpio'] = df_procesos['Nombre'].str.strip()
    
    # Regla Transporte I
    df_procesos.loc[df_procesos['Nombre_Limpio'].str.upper() == 'TRANSPORTE I', 'Tiempo promedio'] = '1d 6h'
    
    # Cálculos de actividades
    df_actividades = df_procesos[df_procesos['Tipo_Limpio'] == 'Actividad'].copy()
    df_actividades['Minutos Promedio'] = df_actividades['Tiempo promedio'].apply(texto_a_minutos)
    df_actividades['Actividad'] = df_actividades['Nombre_Limpio'].str.upper()

    # Metricas principales
    t_asis = df_resumen.loc[df_resumen['Métrica'] == 'Tiempo Total AS-IS', 'Valor'].values[0]
    t_tobe = df_resumen.loc[df_resumen['Métrica'] == 'Tiempo Total TO-BE', 'Valor'].values[0]
    ahorro = df_resumen.loc[df_resumen['Métrica'] == 'Variación (Resta)', 'Valor'].values[0]
    pct_mejora = float(df_resumen.loc[df_resumen['Métrica'] == 'Porcentaje de Mejora', 'Valor'].values[0]) * 100
    
    # =========================================================
    # KPI PRINCIPAL
    # =========================================================
    st.markdown("### Resumen Ejecutivo de Rendimiento")
    col_kpi1, col_kpi2, col_kpi3 = st.columns([1, 1, 2])
    with col_kpi1:
        st.metric(label="Tiempo Total Inicial (AS-IS)", value=str(t_asis).replace("meses", "minutos").replace("28m", "28 minutos"))
    with col_kpi2:
        st.metric(label="Tiempo Total Final (TO-BE)", value=str(t_tobe).replace("meses", "minutos"))
    with col_kpi3:
        st.metric(label="Porcentaje de Eficiencia / Mejora Global", value=f"{pct_mejora:.2f}%", delta=ahorro)

    # =========================================================
    # SECCIÓN: KPIs DE SEGUIMIENTO OPERATIVO (SIN RESULTADOS NUMÉRICOS)
    # =========================================================
    st.markdown("---")
    st.header("🎯 KPIs de Seguimiento Operativo")
    st.info("Indicadores basados en la metodología de Ng Corrales et al. (2022)")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Cycle Time (CT)")
        st.markdown("*Mide el tiempo promedio requerido para completar una unidad desde el inicio hasta el final de una etapa del proceso, permitiendo evaluar la rapidez con la que se ejecuta una actividad.*")
        st.latex(r"CT = \frac{\sum t_i}{n}")

    with c2:
        st.subheader("Throughput (UPH)")
        st.markdown("*Representa el número total de unidades procesadas por hora por una estación de trabajo, midiendo la capacidad productiva del sistema dentro de un periodo determinado.*")
        st.latex(r"UPH = \frac{3600}{CT}")

    with c3:
        st.subheader("First Time Through (FTT)")
        st.markdown("*Evalúa la calidad y confiabilidad del proceso mostrando la proporción de unidades completadas correctamente desde el primer intento, sin requerir reprocesos ni presentar defectos.*")
        st.latex(r"FTT = \frac{\text{Good Units}}{\text{Total Units}}")

    # Sección de Disponibilidad y Rendimiento
    st.markdown("---")
    st.subheader("📊 Disponibilidad (A) y Performance (P)")
    
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("**Disponibilidad (A):** *Mide la proporción del tiempo en que un sistema permanece disponible para operar respecto al tiempo de producción planificado, considerando pérdidas por paradas o fallas.*")
        st.latex(r"Availability(A) = \frac{\text{Operating Time}}{\text{Total Time}}")
        
    with cc2:
        st.markdown("**Performance (P):** *Evalúa la eficiencia de velocidad del proceso midiendo las pérdidas de rendimiento ocasionadas por reducciones en la velocidad de operación o pequeñas interrupciones.*")
        st.latex(r"Performance(P) = \frac{\text{Ideal Time}}{\text{Real Time}}")

    # =========================================================
    # GRÁFICOS INTERACTIVOS
    # =========================================================
    st.markdown("---")
    st.markdown("## Seccion de Graficos Interactivos")
    
    tab_asis, tab_tobe, tab_comparativa_graf = st.tabs([
        "📊 Escenario AS-IS", "📊 Escenario TO-BE", "📊 Comparativa & Impacto"
    ])
    
    with tab_asis:
        fig1 = px.bar(df_actividades[df_actividades['Escenario_Limpio'] == 'AS - IS'], 
                      x="Actividad", y="Minutos Promedio", text="Tiempo promedio",
                      color_discrete_sequence=["#FF4B4B"])
        st.plotly_chart(fig1, use_container_width=True)

    with tab_tobe:
        fig2 = px.bar(df_actividades[df_actividades['Escenario_Limpio'] == 'TO - BE'], 
                      x="Actividad", y="Minutos Promedio", text="Tiempo promedio",
                      color_discrete_sequence=["#1C83E1"])
        st.plotly_chart(fig2, use_container_width=True)

    with tab_comparativa_graf:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig3 = px.bar(df_actividades, x="Actividad", y="Minutos Promedio", color="Escenario_Limpio",
                          barmode="group", color_discrete_sequence=["#FF4B4B", "#1C83E1"])
            st.plotly_chart(fig3, use_container_width=True)
        with col_g2:
            df_pct = pd.DataFrame({"Etapa": ["AS-IS", "TO-BE", "Mejora"], "Val": [100, 100-pct_mejora, pct_mejora]})
            st.plotly_chart(px.bar(df_pct, x="Etapa", y="Val", color="Etapa", text_auto='.2f'), use_container_width=True)

    # TABLAS
    st.markdown("---")
    st.header("📋 Reportes Detallados")
    st.dataframe(df_procesos[['Escenario', 'Nombre', 'Tipo', 'Instancias iniciadas', 'Tiempo promedio', 'Tiempo total']], use_container_width=True)

except Exception as e:
    st.error(f"Ocurrio un error al procesar los datos: {e}")

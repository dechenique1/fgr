import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import json
import os

# Configuración de la página
st.set_page_config(
    page_title="Calculadora FGR - Residuos de Construcción",
    page_icon="🏗️",  # Icono de construcción
    layout="wide"
)

# Sistema de autenticación y gestión de usuarios
# Cada usuario tiene sus propios proyectos almacenados en archivos JSON separados
# Los datos se guardan en la carpeta user_data con el formato: username_proyectos.json

# Función para obtener la ruta del archivo de datos del usuario
def get_user_data_path():
    # Obtener el nombre de usuario de la autenticación
    user = st.session_state.get('username', 'default')
    # Crear directorio para datos de usuarios si no existe
    os.makedirs('user_data', exist_ok=True)
    return f'user_data/{user}_proyectos.json'

# Función para cargar datos del usuario
def cargar_datos():
    try:
        with open(get_user_data_path(), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Función para guardar datos del usuario
def guardar_datos(datos):
    with open(get_user_data_path(), 'w') as f:
        json.dump(datos, f)
    if 'proyectos' in st.session_state:
        st.session_state.proyectos = datos

# Función para calcular el FGR
def calcular_fgr(residuos, area):
    return residuos / area if area > 0 else 0

# Función para calcular área construida en el período
def calcular_area_periodo(area_total, porcentaje_actual, porcentaje_anterior):
    return area_total * (porcentaje_actual - porcentaje_anterior) / 100

# Función para obtener el último avance registrado
def obtener_ultimo_avance(registros):
    if not registros:
        return 0
    return max(registro["porcentaje_avance"] for registro in registros)

# Sistema de autenticación simple
def login():
    if 'username' not in st.session_state:
        st.sidebar.title("Iniciar Sesión")
        username = st.sidebar.text_input("Usuario")
        password = st.sidebar.text_input("Contraseña", type="password")
        
        if st.sidebar.button("Iniciar Sesión"):
            if username and password:  # Aquí podrías agregar validación más robusta
                st.session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Por favor ingresa usuario y contraseña")
        
        # Opción para crear nueva cuenta
        st.sidebar.markdown("---")
        st.sidebar.subheader("¿No tienes cuenta?")
        new_username = st.sidebar.text_input("Nuevo Usuario")
        new_password = st.sidebar.text_input("Nueva Contraseña", type="password")
        confirm_password = st.sidebar.text_input("Confirmar Contraseña", type="password")
        
        if st.sidebar.button("Crear Cuenta"):
            if new_username and new_password and new_password == confirm_password:
                st.session_state.username = new_username
                st.rerun()
            else:
                st.sidebar.error("Por favor verifica los datos ingresados")
        
        return False
    return True

@st.cache_data
def procesar_dataframe(registros, area_total):
    """Procesa los registros y devuelve un DataFrame con cálculos cacheados"""
    if not registros:
        return pd.DataFrame()
    
    df = pd.DataFrame(registros)
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Calcular acumulados
    df['area_acumulada'] = df['area_periodo'].cumsum()
    df['residuos_acumulados'] = df['residuos_periodo'].cumsum()
    df['fgr_acumulado'] = df['residuos_acumulados'] / df['area_acumulada'].replace(0, np.inf)
    
    return df

# Función para manejar la eliminación de residuos
def eliminar_residuo(tipo):
    if tipo in st.session_state.residuos_temp:
        del st.session_state.residuos_temp[tipo]
        return True
    return False

# Función para agregar residuo
def agregar_residuo(tipo, volumen):
    if volumen > 0:
        st.session_state.residuos_temp[tipo] = volumen
        st.session_state.agregar_residuo = False
        return True
    return False

# Función para crear proyecto
def crear_proyecto(nombre, area, tipos_residuos):
    if nombre and area > 0 and tipos_residuos:
        if nombre not in st.session_state.proyectos:
            st.session_state.proyectos[nombre] = {
                "area_total": area,
                "tipos_residuos": tipos_residuos.copy(),
                "registros": []
            }
            guardar_datos(st.session_state.proyectos)
            return True
    return False

# Función principal
def main():
    if not login():
        return

    # Inicializar el estado de la sesión
    if 'proyectos' not in st.session_state:
        st.session_state.proyectos = cargar_datos()
    
    # Inicializar otras variables de estado
    if 'tipos_residuos_temp' not in st.session_state:
        st.session_state.tipos_residuos_temp = []
    if 'residuos_temp' not in st.session_state:
        st.session_state.residuos_temp = {}
    if 'confirmar_eliminar_proyecto' not in st.session_state:
        st.session_state.confirmar_eliminar_proyecto = False
    if 'confirmar_limpieza' not in st.session_state:
        st.session_state.confirmar_limpieza = False
    if 'agregar_residuo' not in st.session_state:
        st.session_state.agregar_residuo = False

    # Mostrar usuario actual y botón de cerrar sesión
    st.sidebar.markdown(f"👤 **{st.session_state.username}**")
    if st.sidebar.button("🚪", help="Cerrar Sesión", key="btn_logout"):
        del st.session_state.username
        st.rerun()
    st.markdown("---")

    st.title("Seguimiento de Factor de Generación de Residuos (FGR)")
    st.markdown("""
    Esta herramienta permite realizar un seguimiento temporal del FGR (m³/m²) para proyectos de construcción.
    
    - El FGR se calcula como m³ de residuos / m² construidos
    - Los m² construidos se calculan según el incremento de avance
    - Los residuos se registran por período de avance
    """)

    # Sidebar para selección de proyecto
    st.sidebar.title("Gestión de Proyectos")

    # Selector de proyecto existente (si hay proyectos)
    if st.session_state.proyectos:
        st.sidebar.subheader("📋 Proyectos Existentes")
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            proyecto_actual = st.selectbox(
                "Seleccionar Proyecto",
                options=list(st.session_state.proyectos.keys()),
                format_func=lambda x: f"📊 {x}"
            )
        with col2:
            if st.button("🗑️", key="btn_eliminar_proyecto", help="Eliminar proyecto"):
                st.session_state.confirmar_eliminar_proyecto = True

    # Separador visual
    st.sidebar.markdown("---")

    # Sección de nuevo proyecto
    with st.sidebar.expander("➕ Crear Nuevo Proyecto", expanded=not bool(st.session_state.proyectos)):
        st.markdown("### Datos del Proyecto")
        nombre_proyecto = st.text_input("📝 Nombre del Proyecto")
        area_total = st.number_input("📐 Área Total (m²)", min_value=0.0)
        
        st.markdown("### Tipos de Residuos")
        col1, col2 = st.columns([2, 1])
        with col1:
            nuevo_tipo = st.text_input("🏗️ Nuevo tipo", key="nuevo_tipo")
        with col2:
            if st.button("➕", key="btn_agregar_tipo", help="Agregar tipo de residuo"):
                if nuevo_tipo:
                    if nuevo_tipo not in st.session_state.tipos_residuos_temp:
                        st.session_state.tipos_residuos_temp.append(nuevo_tipo)
                    else:
                        st.error("Ya existe")
        
        if st.session_state.tipos_residuos_temp:
            st.markdown("#### Tipos configurados:")
            for i, tipo in enumerate(st.session_state.tipos_residuos_temp):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {tipo}")
                with col2:
                    if st.button("✖️", key=f"del_tipo_{i}", help=f"Eliminar {tipo}"):
                        st.session_state.tipos_residuos_temp.remove(tipo)
                        st.rerun()
        
        if st.button("💾 Crear Proyecto", key="btn_crear_proyecto", use_container_width=True):
            if nombre_proyecto and area_total > 0 and st.session_state.tipos_residuos_temp:
                if crear_proyecto(nombre_proyecto, area_total, st.session_state.tipos_residuos_temp):
                    st.success("¡Proyecto creado!")
                    st.session_state.tipos_residuos_temp = []
                    st.rerun()
                else:
                    st.error("Ya existe un proyecto con ese nombre")
            else:
                st.error("Complete todos los campos")

    # Obtener último avance registrado
    ultimo_avance = obtener_ultimo_avance(st.session_state.proyectos[proyecto_actual]["registros"])
    area_total = st.session_state.proyectos[proyecto_actual]["area_total"]
    
    # Mostrar información del proyecto
    st.subheader(f"Proyecto: {proyecto_actual}")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Área total a construir: {area_total:,.2f} m²")
    with col2:
        st.info(f"Avance actual: {ultimo_avance:.1f}%")
    
    # Formulario de registro
    with st.expander("📝 Nuevo Registro de Avance", expanded=not bool(st.session_state.proyectos[proyecto_actual]["registros"])):
        st.markdown("### Datos del Avance")
        
        # Campos de fecha y porcentaje
        col1, col2 = st.columns(2)
        with col1:
            fecha_registro = st.date_input(
                "📅 Fecha",
                help="Fecha del registro de avance"
            )
            
        with col2:
            nuevo_porcentaje = st.number_input(
                "📊 Avance (%)",
                min_value=float(ultimo_avance),
                max_value=100.0,
                value=float(ultimo_avance),
                step=0.1,
                help="Porcentaje de avance acumulado"
            )
        
        if nuevo_porcentaje > ultimo_avance:
            # Mostrar información del incremento
            col1, col2 = st.columns(2)
            with col1:
                incremento = nuevo_porcentaje - ultimo_avance
                st.info(f"⬆️ Incremento: {incremento:.1f}%")
            with col2:
                area_periodo = calcular_area_periodo(area_total, nuevo_porcentaje, ultimo_avance)
                st.info(f"📏 Área del período: {area_periodo:,.2f} m²")
            
            # Sección de residuos
            st.markdown("### Registro de Residuos")
            
            # Agregar nuevo residuo
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                tipo_residuo = st.selectbox(
                    "🏗️ Tipo de Residuo",
                    options=st.session_state.proyectos[proyecto_actual]["tipos_residuos"],
                    key="select_tipo_residuo"
                )
            with col2:
                volumen = st.number_input(
                    "📦 Volumen (m³)",
                    min_value=0.0,
                    step=0.1,
                    key="input_volumen"
                )
            with col3:
                if st.button("➕ Agregar", key="btn_add_residuo", use_container_width=True):
                    if volumen > 0:
                        st.session_state.residuos_temp[tipo_residuo] = volumen
                        st.success(f"✅ {tipo_residuo} agregado")
                        st.rerun()
                    else:
                        st.error("❌ Volumen debe ser > 0")
            
            # Mostrar residuos agregados
            if st.session_state.residuos_temp:
                st.markdown("#### Residuos Registrados")
                for tipo, volumen in st.session_state.residuos_temp.items():
                    col1, col2, col3 = st.columns([2,1,1])
                    with col1:
                        st.write(f"**{tipo}**")
                    with col2:
                        st.write(f"{volumen:.2f} m³")
                    with col3:
                        if st.button("🗑️", key=f"del_{tipo}", help=f"Eliminar {tipo}"):
                            del st.session_state.residuos_temp[tipo]
                            st.rerun()
                
                # Mostrar totales
                total_desglosado = sum(st.session_state.residuos_temp.values())
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"📦 Total residuos: {total_desglosado:.2f} m³")
                with col2:
                    if area_periodo > 0:
                        fgr_periodo = calcular_fgr(total_desglosado, area_periodo)
                        st.info(f"📊 FGR período: {fgr_periodo:.3f} m³/m²")
            
            # Botón de registro
            if st.button("💾 Registrar Avance", key="btn_registrar", use_container_width=True):
                if nuevo_porcentaje <= ultimo_avance:
                    st.error("❌ El avance debe ser mayor al último registrado")
                elif nuevo_porcentaje > 100:
                    st.error("❌ El avance no puede superar 100%")
                elif not st.session_state.residuos_temp:
                    st.error("❌ Debe registrar al menos un residuo")
                else:
                    area_periodo = calcular_area_periodo(area_total, nuevo_porcentaje, ultimo_avance)
                    fgr_periodo = calcular_fgr(total_desglosado, area_periodo)
                    
                    nuevo_registro = {
                        "fecha": fecha_registro.isoformat(),
                        "porcentaje_avance": nuevo_porcentaje,
                        "incremento_porcentaje": nuevo_porcentaje - ultimo_avance,
                        "area_periodo": area_periodo,
                        "residuos_periodo": total_desglosado,
                        "tipos_residuos": dict(st.session_state.residuos_temp),
                        "fgr_periodo": fgr_periodo
                    }
                    
                    st.session_state.proyectos[proyecto_actual]["registros"].append(nuevo_registro)
                    st.session_state.proyectos[proyecto_actual]["registros"].sort(key=lambda x: x["fecha"])
                    st.session_state.residuos_temp = {}
                    guardar_datos(st.session_state.proyectos)
                    st.success("✅ ¡Registro agregado exitosamente!")
                    st.rerun()
        else:
            st.warning("⚠️ El porcentaje de avance debe ser mayor al último registrado")

    # Visualización de datos
    if st.session_state.proyectos[proyecto_actual]["registros"]:
        # Procesar registros para crear DataFrame
        registros = st.session_state.proyectos[proyecto_actual]["registros"]
        df = procesar_dataframe(registros, area_total)
        
        # Preparar DataFrame para visualización
        df_display = pd.DataFrame({
            'Fecha': df['fecha'].dt.strftime('%Y-%m-%d'),
            'Avance (%)': df['porcentaje_avance'],
            'Incremento (%)': df['incremento_porcentaje'],
            'Área del Período (m²)': df['area_periodo'].round(2),
            'Área Acumulada (m²)': df['area_acumulada'].round(2),
            'Residuos del Período (m³)': df['residuos_periodo'].round(2),
            'Residuos Acumulados (m³)': df['residuos_acumulados'].round(2),
            'FGR del Período (m³/m²)': df['fgr_periodo'].round(3),
            'FGR Acumulado (m³/m²)': df['fgr_acumulado'].round(3)
        })
        
        # Procesar datos de residuos por tipo
        residuos_por_tipo = pd.DataFrame()
        total_por_tipo = {}
        
        for registro in registros:
            for tipo, volumen in registro['tipos_residuos'].items():
                if tipo not in residuos_por_tipo.columns:
                    residuos_por_tipo[tipo] = 0
                    total_por_tipo[tipo] = 0
                residuos_por_tipo.loc[registro['fecha'], tipo] = volumen
                total_por_tipo[tipo] += volumen
        
        # Crear tabs para organizar la información
        tab1, tab2, tab3 = st.tabs(["📊 Gráficos", "📈 Estadísticas", "📋 Registros"])
        
        with tab1:
            # Gráficos principales
            st.markdown("### Gráficos de Seguimiento")
            
            # Gráfico de FGR
            fig_fgr = go.Figure()
            fig_fgr.add_trace(go.Scatter(
                x=df['fecha'],
                y=df['fgr_periodo'],
                mode='lines+markers',
                name='FGR por Período',
                hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br>' +
                              '<b>FGR:</b> %{y:.3f} m³/m²<br>' +
                              '<extra></extra>'
            ))
            fig_fgr.add_trace(go.Scatter(
                x=df['fecha'],
                y=df['fgr_acumulado'],
                mode='lines+markers',
                name='FGR Acumulado',
                hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br>' +
                              '<b>FGR Acumulado:</b> %{y:.3f} m³/m²<br>' +
                              '<extra></extra>'
            ))
            fig_fgr.update_layout(
                title='Factor de Generación de Residuos (FGR)',
                xaxis_title='Fecha',
                yaxis_title='FGR (m³/m²)',
                height=450,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial"
                )
            )
            st.plotly_chart(fig_fgr, use_container_width=True)
            
            # Gráfico de avance
            fig_avance = go.Figure()
            
            # Barra para área construida (eje izquierdo)
            fig_avance.add_trace(go.Bar(
                x=df['fecha'],
                y=df['area_periodo'],
                name='Área Construida por Período',
                yaxis='y',
                hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br>' +
                              '<b>Área Construida:</b> %{y:,.1f} m²<br>' +
                              '<extra></extra>'
            ))
            
            # Línea para porcentaje de avance (eje derecho)
            fig_avance.add_trace(go.Scatter(
                x=df['fecha'],
                y=df['porcentaje_avance'],
                mode='lines+markers',
                name='Avance',
                yaxis='y2',
                hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br>' +
                              '<b>Avance Total:</b> %{y:.1f}%<br>' +
                              '<extra></extra>'
            ))
            
            # Configuración del layout con dos ejes Y
            fig_avance.update_layout(
                title='Progreso de Construcción',
                xaxis_title='Fecha',
                yaxis=dict(
                    title='Área Construida por Período (m²)',
                    side='left'
                ),
                yaxis2=dict(
                    title='Avance (%)',
                    side='right',
                    overlaying='y',
                    range=[0, 100]
                ),
                height=450,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial"
                )
            )
            st.plotly_chart(fig_avance, use_container_width=True)
            
            # Gráficos de residuos
            st.markdown("### Análisis de Residuos")
            
            # Gráfico de barras
            fig_residuos = go.Figure()
            for columna in residuos_por_tipo.columns:
                fig_residuos.add_trace(go.Bar(
                    x=residuos_por_tipo.index,
                    y=residuos_por_tipo[columna],
                    name=columna,
                    hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br>' +
                                  f'<b>Tipo:</b> {columna}<br>' +
                                  '<b>Volumen:</b> %{y:.1f} m³<br>' +
                                  '<extra></extra>'
                ))
            
            fig_residuos.update_layout(
                title='Volumen de Residuos por Tipo',
                xaxis_title='Fecha',
                yaxis_title='Volumen (m³)',
                height=450,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial"
                ),
                barmode='group'
            )
            st.plotly_chart(fig_residuos, use_container_width=True)
            
            # Gráfico de pie
            total_residuos = sum(total_por_tipo.values())
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(total_por_tipo.keys()),
                values=list(total_por_tipo.values()),
                hole=.3,
                hovertemplate='<b>Tipo:</b> %{label}<br>' +
                              '<b>Volumen:</b> %{value:.1f} m³<br>' +
                              '<b>Porcentaje:</b> %{percent:.1%}<br>' +
                              '<extra></extra>'
            )])
            fig_pie.update_layout(
                title=f'Distribución Total de Residuos (Total: {total_residuos:.1f} m³)',
                height=450,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial"
                )
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab2:
            st.markdown("### Métricas del Proyecto")
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "🏗️ Avance",
                    f"{df['porcentaje_avance'].iloc[-1]:.1f}%",
                    f"{df['incremento_porcentaje'].iloc[-1]:+.1f}%"
                )
            with col2:
                st.metric(
                    "📏 Área Construida",
                    f"{df['area_acumulada'].iloc[-1]:,.1f} m²",
                    f"{df['area_periodo'].iloc[-1]:+,.1f} m²"
                )
            with col3:
                st.metric(
                    "📊 FGR Promedio",
                    f"{df['fgr_periodo'].mean():.3f} m³/m²"
                )
            with col4:
                st.metric(
                    "📈 FGR Total",
                    f"{df['fgr_acumulado'].iloc[-1]:.3f} m³/m²"
                )
            
            # Tabla de totales
            st.markdown("### Resumen por Tipo de Residuo")
            df_totales = pd.DataFrame(list(total_por_tipo.items()), columns=['Tipo', 'Volumen (m³)'])
            df_totales['Porcentaje'] = df_totales['Volumen (m³)'] / df_totales['Volumen (m³)'].sum() * 100
            df_totales = df_totales.sort_values('Volumen (m³)', ascending=False)
            df_totales['Volumen (m³)'] = df_totales['Volumen (m³)'].round(2)
            df_totales['Porcentaje'] = df_totales['Porcentaje'].round(1)
            st.dataframe(df_totales, use_container_width=True)
        
        with tab3:
            st.markdown("### Historial de Registros")
            # Agregar filtros
            col1, col2 = st.columns(2)
            with col1:
                fecha_inicio = st.date_input("Desde", value=df['fecha'].min())
            with col2:
                fecha_fin = st.date_input("Hasta", value=df['fecha'].max())
            
            # Filtrar DataFrame
            mask = (df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)
            df_filtered = df_display[mask].copy()
            
            # Convertir la columna Fecha a datetime
            df_filtered['Fecha'] = pd.to_datetime(df_filtered['Fecha'])
            
            # Configurar el editor de datos
            st.markdown("#### Editar Registros")
            st.info("📝 Haz doble clic en una celda para editarla. Los cambios se guardarán automáticamente.")
            
            edited_df = st.data_editor(
                df_filtered,
                use_container_width=True,
                column_config={
                    "Fecha": st.column_config.DateColumn(
                        "Fecha 📅",
                        help="Fecha del registro (no editable)",
                        format="YYYY-MM-DD",
                        required=True,
                        disabled=True
                    ),
                    "Avance (%)": st.column_config.NumberColumn(
                        "Avance (%) 📊",
                        help="Porcentaje de avance acumulado",
                        min_value=0,
                        max_value=100,
                        step=0.1,
                        format="%.1f"
                    ),
                    "Incremento (%)": st.column_config.NumberColumn(
                        "⬆️ Incremento (%)",
                        help="Incremento respecto al registro anterior (calculado automáticamente)",
                        format="%.1f",
                        disabled=True
                    ),
                    "Área del Período (m²)": st.column_config.NumberColumn(
                        "📏 Área del Período (m²)",
                        help="Área construida en este período (calculado automáticamente)",
                        format="%.2f",
                        disabled=True
                    ),
                    "Área Acumulada (m²)": st.column_config.NumberColumn(
                        "📈 Área Acumulada (m²)",
                        help="Área total construida hasta la fecha (calculado automáticamente)",
                        format="%.2f",
                        disabled=True
                    ),
                    "Residuos del Período (m³)": st.column_config.NumberColumn(
                        "Residuos (m³) 📦",
                        help="Volumen de residuos generados en este período",
                        min_value=0,
                        format="%.2f"
                    ),
                    "Residuos Acumulados (m³)": st.column_config.NumberColumn(
                        "📊 Residuos Acum. (m³)",
                        help="Volumen total de residuos hasta la fecha (calculado automáticamente)",
                        format="%.2f",
                        disabled=True
                    ),
                    "FGR del Período (m³/m²)": st.column_config.NumberColumn(
                        "📉 FGR Período",
                        help="Factor de Generación de Residuos del período (calculado automáticamente)",
                        format="%.3f",
                        disabled=True
                    ),
                    "FGR Acumulado (m³/m²)": st.column_config.NumberColumn(
                        "📈 FGR Acumulado",
                        help="Factor de Generación de Residuos acumulado (calculado automáticamente)",
                        format="%.3f",
                        disabled=True
                    )
                },
                hide_index=True,
                key="data_editor",
                column_order=[
                    "Fecha",
                    "Avance (%)",
                    "Incremento (%)",
                    "Área del Período (m²)",
                    "Área Acumulada (m²)",
                    "Residuos del Período (m³)",
                    "Residuos Acumulados (m³)",
                    "FGR del Período (m³/m²)",
                    "FGR Acumulado (m³/m²)"
                ]
            )
            
            # Detectar y guardar cambios
            if not df_filtered.equals(edited_df):
                # Convertir las fechas a formato ISO
                registros_actualizados = []
                for _, row in edited_df.iterrows():
                    fecha = pd.to_datetime(row['Fecha']).date().isoformat()
                    porcentaje_avance = float(row['Avance (%)'])
                    residuos_periodo = float(row['Residuos del Período (m³)'])
                    
                    # Buscar el registro original para mantener los tipos de residuos
                    registro_original = next(
                        (r for r in registros if r['fecha'] == fecha),
                        None
                    )
                    
                    if registro_original:
                        tipos_residuos = registro_original['tipos_residuos']
                    else:
                        tipos_residuos = {}
                    
                    registro = {
                        "fecha": fecha,
                        "porcentaje_avance": porcentaje_avance,
                        "residuos_periodo": residuos_periodo,
                        "tipos_residuos": tipos_residuos
                    }
                    registros_actualizados.append(registro)
                
                # Ordenar registros por fecha
                registros_actualizados.sort(key=lambda x: x["fecha"])
                
                # Actualizar incrementos y calcular áreas y FGR
                for i in range(len(registros_actualizados)):
                    # Calcular incremento
                    if i == 0:
                        registros_actualizados[i]["incremento_porcentaje"] = registros_actualizados[i]["porcentaje_avance"]
                    else:
                        registros_actualizados[i]["incremento_porcentaje"] = (
                            registros_actualizados[i]["porcentaje_avance"] - 
                            registros_actualizados[i-1]["porcentaje_avance"]
                        )
                    
                    # Calcular área del período
                    area_periodo = calcular_area_periodo(
                        area_total,
                        registros_actualizados[i]["porcentaje_avance"],
                        registros_actualizados[i-1]["porcentaje_avance"] if i > 0 else 0
                    )
                    registros_actualizados[i]["area_periodo"] = area_periodo
                    
                    # Calcular FGR del período
                    registros_actualizados[i]["fgr_periodo"] = calcular_fgr(
                        registros_actualizados[i]["residuos_periodo"],
                        area_periodo
                    )
                
                # Guardar cambios
                st.session_state.proyectos[proyecto_actual]["registros"] = registros_actualizados
                guardar_datos(st.session_state.proyectos)
                st.success("✅ Cambios guardados correctamente")
                st.rerun()
            
            # Botones de acción
            col1, col2, col3 = st.columns([1,1,2])
            with col1:
                if st.button("📥 Exportar CSV"):
                    edited_df.to_csv(f"{proyecto_actual}_registros.csv", index=False)
                    st.success("¡Datos exportados!")
            with col2:
                if st.button("🗑️ Limpiar Registros"):
                    st.session_state.confirmar_limpieza = True
            with col3:
                if st.session_state.get('confirmar_limpieza', False):
                    st.error("¿Confirmar eliminación?")
                    if st.button("✔️ Sí, eliminar", key="btn_confirmar"):
                        st.session_state.proyectos[proyecto_actual]["registros"] = []
                        guardar_datos(st.session_state.proyectos)
                        st.session_state.confirmar_limpieza = False
                        st.success("¡Registros eliminados!")
                        st.rerun()
                    if st.button("❌ Cancelar", key="btn_cancelar"):
                        st.session_state.confirmar_limpieza = False
                        st.rerun()
    else:
        st.info("Crea un nuevo proyecto usando el formulario en la barra lateral.")

if __name__ == "__main__":
    main() 
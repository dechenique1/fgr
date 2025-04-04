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
    page_title="Calculadora FGR",
    page_icon="🏗️",
    layout="wide"
)

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

# Función principal
def main():
    if not login():
        return

    # Inicializar el estado de la sesión
    if 'proyectos' not in st.session_state:
        st.session_state.proyectos = cargar_datos()

    # Mostrar usuario actual y botón de cerrar sesión
    st.sidebar.markdown(f"**Usuario actual:** {st.session_state.username}")
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state.username
        st.rerun()

    st.title("Seguimiento de Factor de Generación de Residuos (FGR)")
    st.markdown("""
    Esta herramienta permite realizar un seguimiento temporal del FGR (m³/m²) para proyectos de construcción.
    
    - El FGR se calcula como m³ de residuos / m² construidos
    - Los m² construidos se calculan según el incremento de avance
    - Los residuos se registran por período de avance
    """)

    # Sidebar para selección de proyecto
    st.sidebar.title("Gestión de Proyectos")
    
    # Formulario para nuevo proyecto
    st.sidebar.subheader("Crear Nuevo Proyecto")
    
    # Campos principales fuera del formulario
    nombre_proyecto = st.sidebar.text_input("Nombre del Proyecto")
    area_total = st.sidebar.number_input("Área Total a Construir (m²)", min_value=0.0)
    
    # Configuración de tipos de residuos
    st.sidebar.subheader("Configuración de Tipos de Residuos")
    st.sidebar.write("Define los tipos de residuos que se podrán registrar en este proyecto")
    
    # Inicializar lista temporal de residuos en session_state si no existe
    if 'tipos_residuos_temp' not in st.session_state:
        st.session_state.tipos_residuos_temp = []
    
    # Campo para agregar nuevo tipo de residuo
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        nuevo_tipo = st.text_input("Nuevo tipo de residuo", key="nuevo_tipo")
    with col2:
        if st.button("Agregar", key="btn_agregar_tipo"):
            if nuevo_tipo:
                if nuevo_tipo not in st.session_state.tipos_residuos_temp:
                    st.session_state.tipos_residuos_temp.append(nuevo_tipo)
                else:
                    st.sidebar.error("Este tipo de residuo ya existe")
    
    # Mostrar tipos de residuos agregados
    if st.session_state.tipos_residuos_temp:
        st.sidebar.write("Tipos de residuos configurados:")
        for i, tipo in enumerate(st.session_state.tipos_residuos_temp):
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.write(f"- {tipo}")
            with col2:
                if st.button("🗑️", key=f"del_tipo_{i}"):
                    st.session_state.tipos_residuos_temp.remove(tipo)
                    st.rerun()
    
    # Botón para crear proyecto
    if st.sidebar.button("Crear Proyecto", key="btn_crear_proyecto"):
        if nombre_proyecto and area_total > 0 and st.session_state.tipos_residuos_temp:
            if nombre_proyecto not in st.session_state.proyectos:
                st.session_state.proyectos[nombre_proyecto] = {
                    "area_total": area_total,
                    "tipos_residuos": st.session_state.tipos_residuos_temp.copy(),
                    "registros": []
                }
                # Limpiar la lista temporal después de crear el proyecto
                st.session_state.tipos_residuos_temp = []
                guardar_datos(st.session_state.proyectos)
                st.sidebar.success(f"¡Proyecto '{nombre_proyecto}' creado exitosamente!")
                st.rerun()
            else:
                st.sidebar.error("Ya existe un proyecto con ese nombre")
        else:
            st.sidebar.error("Por favor, completa todos los campos y agrega al menos un tipo de residuo")

    # Selector de proyecto y opciones de gestión
    if st.session_state.proyectos:
        st.sidebar.subheader("Gestión de Proyectos")
        
        # Crear dos columnas en el sidebar para el selector y el botón de eliminar
        col1, col2 = st.sidebar.columns([3, 1])
        
        with col1:
            proyecto_actual = st.selectbox(
                "Seleccionar Proyecto",
                options=list(st.session_state.proyectos.keys())
            )
        
        with col2:
            if st.button("🗑️", key="btn_eliminar_proyecto", help="Eliminar proyecto"):
                st.session_state.confirmar_eliminar_proyecto = True
        
        # Confirmación para eliminar proyecto
        if st.session_state.get('confirmar_eliminar_proyecto', False):
            st.sidebar.warning("⚠️ ¿Estás seguro de eliminar este proyecto? Esta acción no se puede deshacer.")
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("Sí, eliminar", key="confirmar_eliminar"):
                    del st.session_state.proyectos[proyecto_actual]
                    guardar_datos(st.session_state.proyectos)
                    st.session_state.confirmar_eliminar_proyecto = False
                    st.rerun()
            with col2:
                if st.button("Cancelar", key="cancelar_eliminar"):
                    st.session_state.confirmar_eliminar_proyecto = False
                    st.rerun()
        
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
        
        # Formulario para nuevo registro
        st.subheader("Registro de Avance")
        
        # Campos de fecha y porcentaje (fuera del formulario)
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_registro = st.date_input("Fecha de Registro")
            nuevo_porcentaje = st.number_input(
                "Porcentaje de Avance (%)",
                min_value=ultimo_avance,
                max_value=100.0,
                value=ultimo_avance
            )
            
        with col2:
            if nuevo_porcentaje > ultimo_avance:
                incremento = nuevo_porcentaje - ultimo_avance
                area_periodo = calcular_area_periodo(area_total, nuevo_porcentaje, ultimo_avance)
                st.write(f"Incremento de avance: {incremento:.1f}%")
                st.write(f"Área a registrar en este período: {area_periodo:,.2f} m²")
        
        # Registro de residuos
        st.subheader("Registro de Residuos")
        tipos_residuos = st.session_state.proyectos[proyecto_actual]["tipos_residuos"]
        
        if "residuos_temp" not in st.session_state:
            st.session_state.residuos_temp = {}
        
        # Botón para agregar nuevo residuo
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Agregar Residuo", key="btn_agregar_residuo"):
                st.session_state.agregar_residuo = True
        
        # Formulario para agregar residuo
        if st.session_state.get('agregar_residuo', False):
            with col2:
                tipo_residuo = st.selectbox("Tipo de Residuo", options=tipos_residuos)
                volumen = st.number_input("Volumen (m³)", min_value=0.0)
                
                if st.button("Guardar Residuo", key="btn_guardar_residuo"):
                    if volumen > 0:
                        st.session_state.residuos_temp[tipo_residuo] = volumen
                        st.session_state.agregar_residuo = False
                        st.rerun()
                    else:
                        st.error("El volumen debe ser mayor a 0")
        
        # Mostrar residuos agregados
        if st.session_state.residuos_temp:
            st.write("Residuos registrados en este período:")
            for tipo, volumen in st.session_state.residuos_temp.items():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{tipo}**")
                with col2:
                    st.write(f"{volumen:.2f} m³")
                with col3:
                    if st.button("Eliminar", key=f"del_{tipo}"):
                        del st.session_state.residuos_temp[tipo]
                        st.rerun()
        
        # Mostrar el total de residuos calculado
        total_desglosado = sum(st.session_state.residuos_temp.values())
        if total_desglosado > 0:
            st.info(f"Volumen total de residuos: {total_desglosado:.2f} m³")
            if nuevo_porcentaje > ultimo_avance:
                area_periodo = calcular_area_periodo(area_total, nuevo_porcentaje, ultimo_avance)
                fgr_periodo = calcular_fgr(total_desglosado, area_periodo)
                st.write(f"FGR del período: {fgr_periodo:.3f} m³/m²")
        
        # Botón para registrar avance
        if st.button("Registrar Avance", key="btn_registrar_avance"):
            if nuevo_porcentaje <= ultimo_avance:
                st.error("El porcentaje de avance debe ser mayor al último registrado")
            elif nuevo_porcentaje > 100:
                st.error("El porcentaje de avance no puede ser mayor a 100%")
            elif not st.session_state.residuos_temp:
                st.error("Debe registrar al menos un tipo de residuo")
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
                st.session_state.residuos_temp = {}  # Limpiar residuos temporales
                guardar_datos(st.session_state.proyectos)
                st.success("¡Registro agregado exitosamente!")
                st.rerun()

        # Visualización de datos
        if st.session_state.proyectos[proyecto_actual]["registros"]:
            st.subheader("Análisis de Datos")
            
            # Convertir registros a DataFrame asegurando que todas las columnas existan
            registros = st.session_state.proyectos[proyecto_actual]["registros"]
            
            # Asegurar que todos los registros tengan los campos necesarios
            for registro in registros:
                if "area_periodo" not in registro:
                    registro["area_periodo"] = calcular_area_periodo(
                        area_total,
                        registro["porcentaje_avance"],
                        registro.get("porcentaje_avance", 0) - registro.get("incremento_porcentaje", 0)
                    )
            
            # Crear DataFrame con columnas explícitas
            df = pd.DataFrame(registros)
            required_columns = [
                'fecha', 'porcentaje_avance', 'incremento_porcentaje',
                'area_periodo', 'residuos_periodo', 'fgr_periodo'
            ]
            
            # Inicializar columnas faltantes con 0
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 0.0
            
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Calcular acumulados solo si hay datos
            if not df.empty:
                df['area_acumulada'] = df['area_periodo'].cumsum()
                df['residuos_acumulados'] = df['residuos_periodo'].cumsum()
                df['fgr_acumulado'] = df['residuos_acumulados'] / df['area_acumulada'].replace(0, np.inf)
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de FGR por período y acumulado
                fig_fgr = go.Figure()
                fig_fgr.add_trace(go.Scatter(
                    x=df['fecha'],
                    y=df['fgr_periodo'],
                    mode='lines+markers',
                    name='FGR por Período'
                ))
                fig_fgr.add_trace(go.Scatter(
                    x=df['fecha'],
                    y=df['fgr_acumulado'],
                    mode='lines+markers',
                    name='FGR Acumulado'
                ))
                fig_fgr.update_layout(
                    title='FGR por Período y Acumulado',
                    xaxis_title='Fecha',
                    yaxis_title='FGR (m³/m²)'
                )
                st.plotly_chart(fig_fgr, use_container_width=True)
            
            with col2:
                # Gráfico de avance y área construida
                fig_avance = go.Figure()
                
                # Barra para área construida (eje izquierdo)
                fig_avance.add_trace(go.Bar(
                    x=df['fecha'],
                    y=df['area_periodo'],
                    name='Área Construida por Período (m²)',
                    yaxis='y'
                ))
                
                # Línea para porcentaje de avance (eje derecho)
                fig_avance.add_trace(go.Scatter(
                    x=df['fecha'],
                    y=df['porcentaje_avance'],
                    mode='lines+markers',
                    name='Avance (%)',
                    yaxis='y2'
                ))
                
                # Configuración del layout con dos ejes Y
                fig_avance.update_layout(
                    title='Avance y Área Construida',
                    xaxis_title='Fecha',
                    yaxis=dict(
                        title='Área Construida por Período (m²)',
                        side='left'
                    ),
                    yaxis2=dict(
                        title='Avance (%)',
                        side='right',
                        overlaying='y',
                        range=[0, 100]  # Fija el rango del eje derecho de 0 a 100%
                    )
                )
                st.plotly_chart(fig_avance, use_container_width=True)
            
            # Gráfico de residuos por tipo
            residuos_por_tipo = pd.DataFrame()
            for registro in st.session_state.proyectos[proyecto_actual]["registros"]:
                for tipo, volumen in registro['tipos_residuos'].items():
                    if tipo not in residuos_por_tipo.columns:
                        residuos_por_tipo[tipo] = 0
                    residuos_por_tipo.loc[registro['fecha'], tipo] = volumen
            
            if not residuos_por_tipo.empty:
                fig_residuos = px.bar(
                    residuos_por_tipo,
                    title='Residuos por Tipo',
                    labels={'value': 'Volumen (m³)', 'index': 'Fecha'}
                )
                st.plotly_chart(fig_residuos, use_container_width=True)
            
            # Estadísticas
            st.subheader("Estadísticas del Proyecto")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Avance Total",
                    f"{df['porcentaje_avance'].iloc[-1]:.1f}%"
                )
            with col2:
                st.metric(
                    "Área Total Construida",
                    f"{df['area_acumulada'].iloc[-1]:,.1f} m²"
                )
            with col3:
                st.metric(
                    "FGR Promedio",
                    f"{df['fgr_periodo'].mean():.3f} m³/m²"
                )
            with col4:
                st.metric(
                    "FGR Total",
                    f"{df['fgr_acumulado'].iloc[-1]:.3f} m³/m²"
                )
            
            # Tabla de registros
            st.subheader("Registros del Proyecto")
            
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
            
            st.dataframe(df_display, use_container_width=True)
            
            # Botón para exportar datos
            if st.button("Exportar Datos a CSV"):
                df_display.to_csv(f"{proyecto_actual}_registros.csv", index=False)
                st.success("Datos exportados exitosamente!")
            
            # Botón para limpiar registros
            st.subheader("Limpiar Registros")
            st.warning("⚠️ Esta acción eliminará todos los registros del proyecto actual.")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Limpiar Registros", key="btn_limpiar"):
                    if st.session_state.proyectos[proyecto_actual]["registros"]:
                        st.session_state.confirmar_limpieza = True
                    else:
                        st.info("No hay registros para limpiar.")
            
            if st.session_state.get('confirmar_limpieza', False):
                with col2:
                    st.error("¿Estás seguro? Esta acción no se puede deshacer.")
                    if st.button("Sí, eliminar todos los registros", key="btn_confirmar"):
                        st.session_state.proyectos[proyecto_actual]["registros"] = []
                        guardar_datos(st.session_state.proyectos)
                        st.session_state.confirmar_limpieza = False
                        st.success("¡Todos los registros han sido eliminados!")
                        st.rerun()
                    if st.button("Cancelar", key="btn_cancelar"):
                        st.session_state.confirmar_limpieza = False
                        st.rerun()
    else:
        st.info("Crea un nuevo proyecto usando el formulario en la barra lateral.")

if __name__ == "__main__":
    main() 
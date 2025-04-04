# Calculadora FGR - Residuos de Construcción

Aplicación web para el seguimiento del Factor de Generación de Residuos (FGR) en proyectos de construcción.

## Características

- Sistema de autenticación de usuarios
- Gestión de múltiples proyectos
- Seguimiento temporal del FGR
- Visualización de datos con gráficos interactivos
- Registro y edición de avances de obra
- Exportación de datos a CSV

## Requisitos

- Python 3.8 o superior
- Streamlit
- Pandas
- Plotly
- NumPy

## Instalación Local

1. Clonar el repositorio:
```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
streamlit run app.py
```

## Despliegue en Streamlit Cloud

1. Crear una cuenta en [Streamlit Cloud](https://streamlit.io/cloud)
2. Conectar tu repositorio de GitHub
3. Desplegar la aplicación seleccionando el archivo `app.py`

## Uso

1. Crear una cuenta o iniciar sesión
2. Crear un nuevo proyecto especificando área total y tipos de residuos
3. Registrar avances de obra y volúmenes de residuos
4. Visualizar estadísticas y gráficos de seguimiento
5. Exportar datos según sea necesario

## Estructura de Datos

Los datos de cada usuario se almacenan en archivos JSON separados en el directorio `user_data/`. 
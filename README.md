# Calculadora de Factor de Generación de Residuos (FGR)

Esta aplicación permite calcular y analizar el Factor de Generación de Residuos (FGR) para proyectos de construcción. El FGR representa la cantidad de residuos generados por metro cuadrado construido (m³/m²).

## Características

- Cálculo de FGR para múltiples proyectos
- Registro de diferentes tipos de residuos
- Visualización de datos mediante gráficos
- Estadísticas generales (promedio, máximo, mínimo)
- Interfaz intuitiva y fácil de usar

## Instalación

1. Clona este repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

Para ejecutar la aplicación:
```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador web predeterminado.

### Cómo usar la aplicación

1. Ingresa los datos del proyecto:
   - Nombre del proyecto
   - Área construida (m²)
   - Tipo de residuo
   - Volumen de residuos (m³)

2. Haz clic en "Agregar Proyecto" para guardar los datos

3. Visualiza los resultados:
   - Tabla de proyectos
   - Gráfico de FGR por proyecto
   - Gráfico de relación área vs volumen
   - Estadísticas generales

4. Puedes agregar múltiples proyectos y compararlos

5. Usa el botón "Limpiar Todos los Proyectos" para reiniciar 
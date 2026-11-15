# Franchise Scorecard

Cuadro de mando en Streamlit para comparar los locales de una red de franquicias con 14 KPIs, una nota ponderada, semáforo y una estimación de euros recuperables por palanca.

**Los datos de la demo son ficticios.**

## Qué hace

- **Ranking de la red**: nota global (0-100), semáforo y nota por categoría (Comercial, Rentabilidad, Operaciones, Personas, Cliente), con mapa de calor por KPI.
- **Ficha de local**: radar frente a la media de la red, tabla de KPIs y plan de acción sugerido según las 3 mayores brechas ponderadas.
- **Tendencias**: evolución mensual de cualquier KPI y dispersión conversión vs ticket medio.
- **Oportunidad**: euros recuperables en conversión, ticket medio, roturas de stock, merma y rotación (estimación orientativa).
- **Datos**: plantilla CSV descargable, carga de datos propios y explicación de cada fórmula.
- Objetivos, pesos, umbrales de semáforo y coste por baja editables en el panel lateral.

## KPIs

Cumplimiento de objetivo, conversión, ticket medio, UPT, margen bruto, coste de ocupación, ventas/m², ventas por hora trabajada, merma, roturas de stock, rotación anualizada, absentismo, NPS y auditoría de estándares.

## Ejecutar en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Desplegar

Sube la carpeta a un repositorio de GitHub y, en [share.streamlit.io](https://share.streamlit.io), crea una app apuntando a `app.py`.

## Autor

José Luis Asenjo · [LinkedIn](https://www.linkedin.com/in/joseluisasenjo)

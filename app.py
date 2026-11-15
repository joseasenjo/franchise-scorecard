"""Franchise Scorecard: cuadro de mando para comparar locales de una red de franquicias."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import COLUMNAS, KPI_DF, generar_demo, kpis_por_local, oportunidad_euros, puntuar, semaforo

st.set_page_config(page_title="Franchise Scorecard", page_icon="📊", layout="wide")

ACCIONES = {
    "cumpl_obj": "Revisar objetivo, plan de acción comercial y calendario de promociones del local.",
    "conversion": "Reforzar cobertura en horas punta, acogida en tienda y venta asistida (ver Smart Shift Planner).",
    "aov": "Trabajar venta cruzada y venta sugerida; revisar surtido y precios de entrada.",
    "upt": "Packs, complementos junto a caja y formación en venta adicional.",
    "margen": "Revisar mix de producto, descuentos aplicados y costes de compra.",
    "ocupacion": "Coste fijo alto frente a la venta: mejorar ventas o revisar condiciones del alquiler.",
    "ventas_m2": "Revisar implantación y zonas frías del local.",
    "vph": "Ajustar horas a la demanda: sobredotación en valle o falta de gente en pico.",
    "merma": "Revisar recepción, caducidades/rotación del stock y control de caja.",
    "oos": "Mejorar frecuencia y fiabilidad de reposición; revisar stock de seguridad (OTIF del proveedor).",
    "rotacion": "Analizar bajas tempranas y voluntarias; reforzar acogida y turnos (ver coste por baja).",
    "absentismo": "Revisar carga de turnos y clima; seguimiento de ausencias recurrentes sin señalar personas.",
    "nps": "Revisar quejas más repetidas y tiempos de espera; plan de servicio.",
    "auditoria": "Plan de corrección de los incumplimientos de la auditoría y reauditoría a 30 días.",
}

# ---------- Datos ----------
st.sidebar.title("📊 Franchise Scorecard")
fuente = st.sidebar.radio("Datos", ["Demo (red ficticia)", "Subir mi CSV"])
if fuente == "Subir mi CSV":
    f = st.sidebar.file_uploader("CSV mensual por local", type="csv")
    if f is None:
        st.info("Sube un CSV con las columnas de la plantilla (pestaña **Datos**) o vuelve a la demo.")
        df = generar_demo()
    else:
        df = pd.read_csv(f)
        falta = [c for c in COLUMNAS if c not in df.columns]
        if falta:
            st.error(f"Faltan columnas: {', '.join(falta)}")
            st.stop()
else:
    df = generar_demo()

meses = sorted(df["mes"].astype(str).unique())
m1, m2 = st.sidebar.select_slider("Periodo", options=meses, value=(meses[0], meses[-1]))
zonas = sorted(df["zona"].unique())
zsel = st.sidebar.multiselect("Zona", zonas, default=zonas)
dfp = df[(df.mes.astype(str) >= m1) & (df.mes.astype(str) <= m2) & (df.zona.isin(zsel))]
if dfp.empty:
    st.warning("No hay datos para esa selección.")
    st.stop()

with st.sidebar.expander("🎯 Objetivos de la red", expanded=False):
    objetivos = {}
    for _, r in KPI_DF.iterrows():
        objetivos[r.clave] = st.number_input(r.nombre, value=float(r.objetivo), key="o_" + r.clave)
with st.sidebar.expander("⚖️ Pesos de cada KPI", expanded=False):
    pesos = {r.clave: st.slider(r.nombre, 0, 20, int(r.peso), key="p_" + r.clave) for _, r in KPI_DF.iterrows()}
with st.sidebar.expander("⚙️ Supuestos"):
    verde = st.slider("Umbral verde (nota ≥)", 70, 100, 93)
    ambar = st.slider("Umbral ámbar (nota ≥)", 40, 95, 89)
    coste_baja = st.number_input("Coste estimado por baja (€)", 500.0, 30000.0, 5255.0, step=100.0,
                                 help="Por defecto, el caso base ilustrativo del artículo sobre coste de rotación.")

k = kpis_por_local(dfp)
sc = puntuar(k, objetivos, pesos)
sc["semaforo"] = sc["nota"].apply(lambda n: semaforo(n, verde, ambar))
sc = sc.sort_values("nota", ascending=False).reset_index(drop=True)
sc["ranking"] = sc.index + 1
op = oportunidad_euros(k, objetivos, coste_baja)

st.title("Franchise Scorecard")
st.caption("Compara los locales de una red con 14 KPIs, puntuación ponderada, semáforo y euros recuperables. "
           "Los datos de la demo son ficticios.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Locales", len(k))
c2.metric("Ventas del periodo", f"{k.ventas.sum():,.0f} €".replace(",", "."))
c3.metric("Nota media de la red", f"{sc.nota.mean():.1f}")
c4.metric("🔴 Locales en rojo", int((sc.nota < ambar).sum()))
c5.metric("Oportunidad estimada", f"{op.Total.sum():,.0f} €".replace(",", "."))

t1, t2, t3, t4, t5 = st.tabs(["🏆 Ranking de la red", "🔎 Ficha de local", "📈 Tendencias",
                              "💶 Oportunidad", "🗂️ Datos y plantilla"])

# ---------- Ranking ----------
with t1:
    cats = [c for c in sc.columns if c.startswith("cat_")]
    tabla = sc[["ranking", "semaforo", "local", "zona", "nota"] + cats].rename(
        columns={**{c: c[4:] for c in cats}, "semaforo": " ", "ranking": "#", "local": "Local", "zona": "Zona", "nota": "Nota"})
    st.dataframe(tabla.round(1), hide_index=True, use_container_width=True)
    st.subheader("Mapa de calor: puntuación por KPI")
    hm = sc.set_index("local")[list(KPI_DF.clave)]
    hm.columns = KPI_DF.nombre.tolist()
    fig = px.imshow(hm, color_continuous_scale=["#c0392b", "#f1c40f", "#27ae60"], zmin=50, zmax=100,
                    aspect="auto", labels=dict(color="Puntos"))
    fig.update_xaxes(tickangle=-40, side="top")
    fig.update_layout(height=520, margin=dict(t=160))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Cada KPI puntúa 100 si cumple o supera el objetivo; si no, proporcionalmente (tope 100). "
               "La nota global es la media ponderada con los pesos del panel lateral.")
    peor = sc.tail(3)
    st.markdown("**Locales que requieren atención:** " + ", ".join(f"{r.semaforo} {r.local} ({r.nota:.0f})" for r in peor.itertuples()))

# ---------- Ficha de local ----------
with t2:
    local = st.selectbox("Local", sc.local.tolist())
    fila = sc[sc.local == local].iloc[0]
    kl = k[k.local == local].iloc[0]
    a, b = st.columns([1, 1])
    with a:
        st.metric(f"{fila.semaforo} Nota global", f"{fila.nota:.1f}")
        st.caption(f"Puesto {int(fila.ranking)} de {len(sc)} en la red")
        cat_names = [c[4:] for c in cats]
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(r=[fila["cat_" + c] for c in cat_names] + [fila["cat_" + cat_names[0]]],
                                        theta=cat_names + [cat_names[0]], name=local, fill="toself"))
        radar.add_trace(go.Scatterpolar(r=[sc["cat_" + c].mean() for c in cat_names] + [sc["cat_" + cat_names[0]].mean()],
                                        theta=cat_names + [cat_names[0]], name="Media red"))
        radar.update_layout(polar=dict(radialaxis=dict(range=[40, 100])), height=380, margin=dict(t=30, b=20))
        st.plotly_chart(radar, use_container_width=True)
    with b:
        rows = []
        for _, r in KPI_DF.iterrows():
            val, med = kl[r.clave], k[r.clave].mean()
            rows.append({"KPI": r.nombre, "Local": r.formato.format(val), "Objetivo": r.formato.format(objetivos[r.clave]),
                         "Media red": r.formato.format(med), "Puntos": round(fila[r.clave], 0)})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=420)
    st.subheader("Plan de acción sugerido (3 mayores brechas ponderadas)")
    gap = {r.clave: (100 - fila[r.clave]) * pesos[r.clave] for _, r in KPI_DF.iterrows()}
    top = sorted(gap, key=gap.get, reverse=True)[:3]
    for cl in top:
        if gap[cl] <= 0:
            continue
        nom = KPI_DF.set_index("clave").loc[cl, "nombre"]
        st.markdown(f"- **{nom}** ({fila[cl]:.0f} pts): {ACCIONES[cl]}")
    if all(gap[c] <= 0 for c in top):
        st.success("Este local cumple todos los objetivos.")

# ---------- Tendencias ----------
with t3:
    opciones = KPI_DF.set_index("clave").nombre.to_dict()
    kpi_sel = st.selectbox("KPI", list(opciones), format_func=opciones.get)
    locales_sel = st.multiselect("Locales", sc.local.tolist(), default=sc.local.head(3).tolist() + sc.local.tail(1).tolist())
    mm = sorted(dfp.mes.astype(str).unique())
    serie = pd.concat([kpis_por_local(dfp[dfp.mes.astype(str) == m])[["local", kpi_sel]].assign(mes=m) for m in mm])
    serie = serie[serie.local.isin(locales_sel)]
    fig = px.line(serie, x="mes", y=kpi_sel, color="local", markers=True, labels={kpi_sel: opciones[kpi_sel]})
    fig.add_hline(y=objetivos[kpi_sel], line_dash="dash", annotation_text="Objetivo")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Dispersión: conversión vs ticket medio")
    fig2 = px.scatter(k, x="conversion", y="aov", size="ventas", color="zona", text="local",
                      labels={"conversion": "Conversión (%)", "aov": "Ticket medio (€)"})
    fig2.add_vline(x=objetivos["conversion"], line_dash="dot")
    fig2.add_hline(y=objetivos["aov"], line_dash="dot")
    fig2.update_traces(textposition="top center")
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Arriba a la derecha: locales que superan ambos objetivos. Abajo a la izquierda: conversión y ticket por debajo.")

# ---------- Oportunidad ----------
with t4:
    st.markdown("Euros que se recuperarían en el periodo si cada local alcanzara el objetivo en cada palanca. "
                "**Estimación orientativa**: las palancas no son estrictamente aditivas.")
    palancas = ["Conversión", "Ticket medio", "Roturas de stock", "Merma", "Rotación"]
    o = op.sort_values("Total", ascending=False)
    fig = px.bar(o, x="local", y=palancas, labels={"value": "€", "variable": "Palanca"})
    st.plotly_chart(fig, use_container_width=True)
    tot = op[palancas].sum().sort_values(ascending=False)
    st.markdown("**Mayor palanca de la red:** " + f"{tot.index[0]} ({tot.iloc[0]:,.0f} €)".replace(",", "."))
    st.dataframe(o.round(0), hide_index=True, use_container_width=True)
    st.caption(f"Rotación valorada con {coste_baja:,.0f} € por baja (supuesto editable). "
               "Roturas y merma se valoran como % de ventas por encima del objetivo.".replace(",", "."))

# ---------- Datos ----------
with t5:
    st.markdown("**Formato de CSV:** una fila por local y mes, con estas columnas:")
    st.code(", ".join(COLUMNAS))
    st.download_button("⬇️ Descargar plantilla con datos demo", generar_demo().to_csv(index=False).encode("utf-8"),
                       "plantilla_franchise_scorecard.csv", "text/csv")
    st.download_button("⬇️ Descargar ranking actual", sc.round(2).to_csv(index=False).encode("utf-8"),
                       "ranking_franchise_scorecard.csv", "text/csv")
    st.dataframe(dfp, hide_index=True, use_container_width=True, height=300)
    with st.expander("Cómo se calculan los KPIs"):
        st.markdown("""
- **Conversión** = transacciones / visitas · **Ticket medio** = ventas / transacciones · **UPT** = unidades / transacciones
- **Cumplimiento** = ventas / objetivo · **Margen** = margen bruto / ventas · **Ocupación** = coste de ocupación / ventas
- **Ventas por hora trabajada** = ventas / horas trabajadas · **Ventas/m²** = ventas / superficie / meses
- **Merma** = merma / ventas · **Roturas** = días con rotura / días de apertura
- **Rotación anualizada** = bajas / plantilla media / meses × 12 · **Absentismo** = horas de ausencia / horas pactadas
- **Puntuación** de cada KPI: 100 si cumple el objetivo; si no, proporcional (para KPIs donde menos es mejor, objetivo / valor).
        """)
st.sidebar.caption("Datos de demostración ficticios · Desarrollado por José Luis Asenjo")

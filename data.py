"""Datos demo (ficticios) y cálculo de KPIs del Franchise Scorecard."""
import numpy as np
import pandas as pd

COLUMNAS = ["local", "zona", "mes", "visitas", "transacciones", "unidades", "ventas",
            "objetivo_ventas", "margen_bruto", "horas_trabajadas", "plantilla", "bajas",
            "horas_ausencia", "horas_pactadas", "dias_rotura", "dias_apertura", "merma",
            "nps", "auditoria", "superficie_m2", "coste_ocupacion"]

LOCALES = [("Donostia Centro", "Norte", 1), ("Donostia Gros", "Norte", 0.8), ("Irún", "Norte", 0.75),
           ("Bilbao Moyúa", "Norte", 1.15), ("Bilbao Leioa", "Norte", 0.9), ("Vitoria Gasteiz", "Norte", 0.85),
           ("Pamplona", "Centro", 0.95), ("Logroño", "Centro", 0.7), ("Zaragoza Plaza", "Centro", 1.1),
           ("Madrid Chamberí", "Centro", 1.3), ("Valencia Colón", "Este", 1.0), ("Barcelona Gràcia", "Este", 1.25)]


def generar_demo(seed: int = 7, meses: int = 6) -> pd.DataFrame:
    """Red ficticia de 12 locales. Cada local tiene un 'carácter' distinto para que el análisis tenga sentido."""
    rng = np.random.default_rng(seed)
    fechas = pd.period_range(end="2026-10", periods=meses, freq="M")
    filas = []
    for nombre, zona, tam in LOCALES:
        conv_b = rng.uniform(0.17, 0.30)
        aov_b = rng.uniform(34, 52)
        rot_b = rng.uniform(0.01, 0.05)       # bajas mensuales / plantilla
        aus_b = rng.uniform(0.03, 0.09)
        rot_stock = rng.uniform(0.02, 0.10)
        audit_b = rng.uniform(72, 96)
        nps_b = rng.uniform(35, 72)
        merma_b = rng.uniform(0.007, 0.025)
        sup = int(60 * tam + rng.integers(20, 50))
        plant = max(4, int(round(8 * tam + rng.integers(-1, 3))))
        for f in fechas:
            estac = 1 + 0.12 * np.sin((f.month - 3) / 12 * 2 * np.pi)
            visitas = int(rng.normal(3300 * tam * estac, 150))
            conv = np.clip(rng.normal(conv_b, 0.012), 0.1, 0.4)
            trans = int(visitas * conv)
            aov = max(15, rng.normal(aov_b, 1.6))
            ventas = trans * aov
            upt = rng.normal(1.9 + (aov_b - 34) / 40, 0.06)
            horas_pact = plant * 160
            horas = horas_pact * rng.uniform(0.92, 1.12)
            filas.append(dict(
                local=nombre, zona=zona, mes=str(f), visitas=visitas, transacciones=trans,
                unidades=int(trans * upt), ventas=round(ventas, 2),
                objetivo_ventas=round(3300 * tam * estac * 0.24 * 42, 2),
                margen_bruto=round(ventas * np.clip(rng.normal(0.56, 0.012), 0.45, 0.65), 2),
                horas_trabajadas=round(horas, 1), plantilla=plant,
                bajas=int(rng.binomial(plant, rot_b)),
                horas_ausencia=round(horas_pact * np.clip(rng.normal(aus_b, 0.008), 0.01, 0.2), 1),
                horas_pactadas=horas_pact,
                dias_rotura=int(np.clip(rng.normal(rot_stock * 26, 0.8), 0, 12)), dias_apertura=26,
                merma=round(ventas * np.clip(rng.normal(merma_b, 0.002), 0.002, 0.05), 2),
                nps=round(np.clip(rng.normal(nps_b, 4), -100, 100), 1),
                auditoria=round(np.clip(rng.normal(audit_b, 2.5), 40, 100), 1),
                superficie_m2=sup,
                coste_ocupacion=round(ventas * np.clip(rng.normal(0.12 + 0.03 * (1 - tam), 0.006), 0.05, 0.3), 2)))
    return pd.DataFrame(filas)


# KPI: (clave, nombre, categoría, mayor_es_mejor, objetivo por defecto, formato, peso por defecto)
KPIS = [
    ("cumpl_obj", "Cumplimiento de objetivo de ventas", "Comercial", True, 100.0, "{:.1f} %", 14),
    ("conversion", "Conversión", "Comercial", True, 24.0, "{:.1f} %", 10),
    ("aov", "Ticket medio (€)", "Comercial", True, 42.0, "{:.1f}", 8),
    ("upt", "Unidades por ticket", "Comercial", True, 2.1, "{:.2f}", 5),
    ("margen", "Margen bruto", "Rentabilidad", True, 56.0, "{:.1f} %", 9),
    ("ocupacion", "Coste de ocupación / ventas", "Rentabilidad", False, 13.0, "{:.1f} %", 6),
    ("ventas_m2", "Ventas por m² y mes (€)", "Rentabilidad", True, 400.0, "{:.0f}", 4),
    ("vph", "Ventas por hora trabajada (€)", "Operaciones", True, 28.0, "{:.1f}", 9),
    ("merma", "Merma / ventas", "Operaciones", False, 1.5, "{:.2f} %", 5),
    ("oos", "Días con roturas de stock", "Operaciones", False, 5.0, "{:.1f} %", 5),
    ("rotacion", "Rotación de plantilla (anualizada)", "Personas", False, 30.0, "{:.0f} %", 7),
    ("absentismo", "Absentismo", "Personas", False, 5.0, "{:.1f} %", 5),
    ("nps", "NPS cliente", "Cliente", True, 55.0, "{:.0f}", 7),
    ("auditoria", "Auditoría de estándares de marca", "Cliente", True, 90.0, "{:.1f}", 6),
]
KPI_DF = pd.DataFrame(KPIS, columns=["clave", "nombre", "categoria", "mayor_mejor", "objetivo", "formato", "peso"])


def kpis_por_local(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega el periodo y calcula los 14 KPIs por local."""
    g = df.groupby("local", as_index=False).agg(
        zona=("zona", "first"), visitas=("visitas", "sum"), transacciones=("transacciones", "sum"),
        unidades=("unidades", "sum"), ventas=("ventas", "sum"), objetivo_ventas=("objetivo_ventas", "sum"),
        margen_bruto=("margen_bruto", "sum"), horas=("horas_trabajadas", "sum"), plantilla=("plantilla", "mean"),
        bajas=("bajas", "sum"), h_aus=("horas_ausencia", "sum"), h_pact=("horas_pactadas", "sum"),
        dias_rotura=("dias_rotura", "sum"), dias_ap=("dias_apertura", "sum"), merma_eur=("merma", "sum"),
        nps=("nps", "mean"), auditoria=("auditoria", "mean"), m2=("superficie_m2", "first"),
        ocup=("coste_ocupacion", "sum"), meses=("mes", "nunique"))
    g["cumpl_obj"] = g.ventas / g.objetivo_ventas * 100
    g["conversion"] = g.transacciones / g.visitas * 100
    g["aov"] = g.ventas / g.transacciones
    g["upt"] = g.unidades / g.transacciones
    g["margen"] = g.margen_bruto / g.ventas * 100
    g["ocupacion"] = g.ocup / g.ventas * 100
    g["ventas_m2"] = g.ventas / g.m2 / g.meses
    g["vph"] = g.ventas / g.horas
    g["merma"] = g.merma_eur / g.ventas * 100
    g["oos"] = g.dias_rotura / g.dias_ap * 100
    g["rotacion"] = g.bajas / g.plantilla / g.meses * 12 * 100
    g["absentismo"] = g.h_aus / g.h_pact * 100
    return g


def puntuar(k: pd.DataFrame, objetivos: dict, pesos: dict) -> pd.DataFrame:
    """Puntuación 0-100 por KPI (100 = objetivo cumplido o superado) y nota global ponderada."""
    s = k[["local", "zona"]].copy()
    for _, r in KPI_DF.iterrows():
        v, t = k[r.clave].clip(lower=1e-9), max(objetivos[r.clave], 1e-9)
        ratio = v / t if r.mayor_mejor else t / v
        s[r.clave] = (ratio * 100).clip(0, 100)
    w = pd.Series({c: pesos[c] for c in KPI_DF.clave})
    s["nota"] = (s[KPI_DF.clave] * w).sum(axis=1) / max(w.sum(), 1e-9)
    for cat, sub in KPI_DF.groupby("categoria"):
        ww = w[sub.clave]
        s["cat_" + cat] = (s[sub.clave] * ww).sum(axis=1) / max(ww.sum(), 1e-9)
    return s


def semaforo(n: float, verde=90, ambar=75) -> str:
    return "🟢" if n >= verde else ("🟡" if n >= ambar else "🔴")


def oportunidad_euros(k: pd.DataFrame, objetivos: dict, coste_baja: float) -> pd.DataFrame:
    """Estimación de euros recuperables por palanca si el local alcanzara el objetivo (orientativa)."""
    o = k[["local"]].copy()
    o["Conversión"] = (objetivos["conversion"] - k.conversion).clip(lower=0) / 100 * k.visitas * k.aov
    o["Ticket medio"] = (objetivos["aov"] - k.aov).clip(lower=0) * k.transacciones
    o["Roturas de stock"] = (k.oos - objetivos["oos"]).clip(lower=0) / 100 * k.ventas
    o["Merma"] = (k.merma - objetivos["merma"]).clip(lower=0) / 100 * k.ventas
    o["Rotación"] = (k.rotacion - objetivos["rotacion"]).clip(lower=0) / 100 * k.plantilla * k.meses / 12 * coste_baja
    o["Total"] = o.drop(columns="local").sum(axis=1)
    return o

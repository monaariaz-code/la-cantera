"""
La Cantera - Conector de tendencias con Google Trends

Consulta el interés de búsqueda de los últimos 7 días para las palabras clave
de cada categoría y guarda el resultado en tendencias_la_cantera.json,
que es el archivo que lee el dashboard (index.html).

Instalación:
    pip install pytrends pandas

Uso:
    python conector_google_trends.py

Nota: pytrends es una librería no oficial. Google puede limitar las consultas
(error 429). El script espera entre consultas y reintenta para evitarlo.
"""

import json
import time
from datetime import datetime

from pytrends.request import TrendReq

# País de las búsquedas: 'CO' = Colombia. Déjalo vacío ('') para todo el mundo.
PAIS = "CO"

# Palabras clave por categoría. Edítalas según los influencers del pool.
# Máximo 5 por categoría (límite de Google Trends por consulta).
CATEGORIAS = {
    "gastronomia": ["recetas faciles", "comida saludable", "street food", "restaurantes"],
    "moda": ["outfit del dia", "tendencias de moda", "streetwear", "moda sostenible"],
    "deporte": ["rutina de ejercicio", "running", "entrenamiento funcional", "gimnasio en casa"],
}

REINTENTOS = 3
ESPERA_SEGUNDOS = 10


def consultar(pytrends, palabras):
    """Devuelve [{palabra_clave, interes_promedio}] ordenado de mayor a menor."""
    for intento in range(1, REINTENTOS + 1):
        try:
            pytrends.build_payload(palabras, timeframe="now 7-d", geo=PAIS)
            datos = pytrends.interest_over_time()
            if datos.empty:
                return []
            promedios = datos[palabras].mean().sort_values(ascending=False)
            return [
                {"palabra_clave": palabra, "interes_promedio": round(float(valor), 1)}
                for palabra, valor in promedios.items()
            ]
        except Exception as error:
            print(f"  Intento {intento}/{REINTENTOS} falló: {error}")
            time.sleep(ESPERA_SEGUNDOS * intento)
    return []


def obtener_tendencias():
    pytrends = TrendReq(hl="es-419", tz=300)  # tz=300 -> hora de Colombia
    resultados = {}

    for categoria, palabras in CATEGORIAS.items():
        print(f"Consultando {categoria}...")
        resultados[categoria] = consultar(pytrends, palabras)
        time.sleep(5)  # pausa para no saturar a Google

    resultados["actualizado"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return resultados


if __name__ == "__main__":
    tendencias = obtener_tendencias()

    with open("tendencias_la_cantera.json", "w", encoding="utf-8") as archivo:
        json.dump(tendencias, archivo, ensure_ascii=False, indent=2)

    print("Listo: tendencias_la_cantera.json actualizado.")

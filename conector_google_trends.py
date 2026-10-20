"""
La Cantera - Conector de tendencias con Google Trends

Consulta cada palabra clave POR SEPARADO (así ninguna queda aplastada por
otra más popular) y guarda en tendencias_la_cantera.json:
  - interes_promedio: nivel de las últimas 24 h, de 0 a 100, comparado con
    el pico de esa misma palabra en los últimos 7 días.
  - cambio_24h: variación porcentual de las últimas 24 h frente a los
    6 días anteriores (positivo = va en alza).

Instalación:
    pip install pytrends pandas

Uso:
    python conector_google_trends.py
"""

import json
import time
from datetime import datetime

from pytrends.request import TrendReq

# País: 'CO' = Colombia. Déjalo vacío ('') para todo el mundo.
PAIS = "CO"

# Palabras clave por categoría. Edítalas según los influencers del pool.
CATEGORIAS = {
    "gastronomia": ["recetas", "restaurantes", "comida saludable", "street food", "postres"],
    "moda": ["outfits", "tendencias de moda", "streetwear", "ropa", "zapatos"],
    "deporte": ["running", "rutina de ejercicio", "entrenamiento funcional", "gimnasio", "yoga"],
}

REINTENTOS = 3
ESPERA_ENTRE_CONSULTAS = 8  # segundos, para no saturar a Google


def consultar_palabra(pytrends, palabra):
    """Devuelve {palabra_clave, interes_promedio, cambio_24h} o None si falla."""
    for intento in range(1, REINTENTOS + 1):
        try:
            pytrends.build_payload([palabra], timeframe="now 7-d", geo=PAIS)
            datos = pytrends.interest_over_time()
            if datos.empty or palabra not in datos:
                return {"palabra_clave": palabra, "interes_promedio": 0.0, "cambio_24h": None}

            serie = datos[palabra].astype(float)
            ultimas_24h = serie.iloc[-24:].mean()
            anteriores = serie.iloc[:-24].mean() if len(serie) > 24 else 0.0

            cambio = None
            if anteriores > 0:
                cambio = round((ultimas_24h - anteriores) / anteriores * 100, 1)

            return {
                "palabra_clave": palabra,
                "interes_promedio": round(float(ultimas_24h), 1),
                "cambio_24h": cambio,
            }
        except Exception as error:
            print(f"  '{palabra}' intento {intento}/{REINTENTOS} falló: {error}")
            time.sleep(10 * intento)
    return None


def obtener_tendencias():
    pytrends = TrendReq(hl="es-419", tz=300)  # tz=300 -> hora de Colombia
    resultados = {}

    for categoria, palabras in CATEGORIAS.items():
        print(f"Consultando {categoria}...")
        filas = []
        for palabra in palabras:
            fila = consultar_palabra(pytrends, palabra)
            if fila:
                filas.append(fila)
            time.sleep(ESPERA_ENTRE_CONSULTAS)
        filas.sort(key=lambda f: f["interes_promedio"], reverse=True)
        resultados[categoria] = filas

    resultados["actualizado"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return resultados


if __name__ == "__main__":
    tendencias = obtener_tendencias()

    with open("tendencias_la_cantera.json", "w", encoding="utf-8") as archivo:
        json.dump(tendencias, archivo, ensure_ascii=False, indent=2)

    print("Listo: tendencias_la_cantera.json actualizado.")

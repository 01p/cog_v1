import os
import subprocess
import requests

# ----------------- KONFIGURATION -----------------

# WCS Basis-URL
BASE_URL = "https://datacube.julius-kuehn.de/flf/ows?"

# Coverage-ID laut deinem Cube
COVERAGE_ID = "jki_phaseX201Xpermanentgreenland_annually"

# Ausgabeordner
OUT_FOLDER = "permanentgreenland_cogs"
os.makedirs(OUT_FOLDER, exist_ok=True)

# Liste der verfügbaren Zeitstempel (aus XML entnommen)
YEARS = list(range(1993, 2023))

# Bänder, die abgefragt werden sollen
FIELDS = ["doy1", "doy25", "doy26", "sse1", "sse25", "sse26"]

# ----------------- FUNKTIONEN -----------------

def download_year(year, output_path):
    """
    Lädt für ein Jahr das GeoTIFF herunter über GetCoverage
    """
    params = {
        "SERVICE": "WCS",
        "VERSION": "2.1.0",
        "REQUEST": "GetCoverage",
        "COVERAGEID": COVERAGE_ID,
        "FORMAT": "image/tiff",
        "SUBSET": [
            f"ansi(\"{year}-01-01T00:00:00.000Z\")"
        ]
    }

    # URL-Bau
    url = BASE_URL + "&" + "&".join(
        [f"{key}={value}" if not isinstance(value, list) else "&".join([f"{key}={v}" for v in value]) for key, value in params.items()]
    )

    print(f"Starte Download für Jahr {year}...")

    response = requests.get(url, stream=True)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Download abgeschlossen: {output_path}")
    else:
        print(f"Fehler beim Download für Jahr {year}: {response.status_code}")

def convert_to_cog(input_path, output_path):
    """
    Konvertiert GeoTIFF zu Cloud Optimized GeoTIFF (COG)
    """
    cmd = [
        "gdal_translate",
        "-of", "COG",
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILED=YES",
        "-co", "OVERVIEWS=IGNORE_EXISTING",
        input_path,
        output_path
    ]

    print(f"Konvertiere {input_path} zu COG...")
    subprocess.run(cmd, check=True)
    print(f"COG gespeichert: {output_path}")

# ----------------- HAUPTPROGRAMM -----------------

for year in YEARS:
    temp_tiff = os.path.join(OUT_FOLDER, f"temp_{year}.tif")
    final_cog = os.path.join(OUT_FOLDER, f"permanentgreenland_{year}.tif")

    download_year(year, temp_tiff)
    
    if os.path.exists(temp_tiff):
        convert_to_cog(temp_tiff, final_cog)
        os.remove(temp_tiff)
    else:
        print(f"Kein TIFF für {year} vorhanden, überspringe...")

print("Alle COGs fertig!")

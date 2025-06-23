import os
import subprocess
import requests
import rasterio

# ----------------- KONFIGURATION -----------------

BASE_URL = "https://datacube.julius-kuehn.de/flf/ows?"
COVERAGE_ID = "jki_phaseX201Xpermanentgreenland_annually"
OUT_FOLDER = "permanentgreenland_cogs"
os.makedirs(OUT_FOLDER, exist_ok=True)

YEAR = 1994

BAND_INFO = [
    ("doy1", "Greenup - Day of Year"),
    ("doy25", "Cut for hay - Day of Year"),
    ("doy26", "Cut for silage - Day of Year"),
    ("sse1", "Greenup - Sum of Squares Error"),
    ("sse25", "Hay - Sum of Squares Error"),
    ("sse26", "Silage - Sum of Squares Error")
]

# ----------------- FUNKTIONEN -----------------

def download_year(year, output_path):
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
        raise Exception(f"Fehler beim Download: Status {response.status_code}")

def prepare_tiff_with_overviews(input_path, output_path):
    temp_tif_with_ovr = output_path.replace(".tif", "_with_ovr.tif")

    # Schritt 1: Normales TIFF erzeugen
    cmd = [
        "gdal_translate",
        "-of", "GTiff",
        "-co", "TILED=YES",
        "-co", "COMPRESS=DEFLATE",
        input_path,
        temp_tif_with_ovr
    ]
    subprocess.run(cmd, check=True)

    # Schritt 2: Overviews hinzufügen
    cmd_ovr = [
        "gdaladdo",
        "-r", "average",
        temp_tif_with_ovr,
        "2", "4", "8", "16", "32"
    ]
    subprocess.run(cmd_ovr, check=True)

    # Schritt 3: Metadaten schreiben
    with rasterio.open(temp_tif_with_ovr, "r+") as dataset:
        dataset.update_tags(YEAR=str(YEAR), DATASOURCE="JKI WCS")
        for idx, (short_name, description) in enumerate(BAND_INFO, start=1):
            dataset.update_tags(idx, NAME=short_name, DESCRIPTION=description)

    # Schritt 4: Final als sauberes COG exportieren
    cmd_cog = [
        "gdal_translate",
        "-of", "COG",
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILED=YES",
        "-co", "OVERVIEWS=INCLUDE_EXISTING",
        temp_tif_with_ovr,
        output_path
    ]
    subprocess.run(cmd_cog, check=True)

    os.remove(temp_tif_with_ovr)

# ----------------- HAUPTPROGRAMM -----------------

temp_tiff = os.path.join(OUT_FOLDER, f"temp_{YEAR}.tif")
final_cog = os.path.join(OUT_FOLDER, f"permanentgreenland_{YEAR}.tif")

download_year(YEAR, temp_tiff)

if os.path.exists(temp_tiff):
    prepare_tiff_with_overviews(temp_tiff, final_cog)
    os.remove(temp_tiff)
else:
    print(f"Kein TIFF für {YEAR} vorhanden, überspringe...")

print("Testlauf 1994 abgeschlossen.")

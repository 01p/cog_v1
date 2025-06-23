import os
import subprocess
import requests
import rasterio
import json
from datetime import datetime

# ----------------- KONFIGURATION -----------------

BASE_URL = "https://datacube.julius-kuehn.de/flf/ows?"
COVERAGE_ID = "jki_phaseX201Xpermanentgreenland_annually"
OUT_FOLDER = "_permanentgreenland_cogs"
os.makedirs(OUT_FOLDER, exist_ok=True)

YEARS = list(range(1993, 2023))

BAND_INFO = [
    ("doy1", "Greenup - Day of Year"),
    ("doy25", "Cut for hay - Day of Year"),
    ("doy26", "Cut for silage - Day of Year"),
    ("sse1", "Greenup - Sum of Squares Error"),
    ("sse25", "Hay - Sum of Squares Error"),
    ("sse26", "Silage - Sum of Squares Error")
]

# ----------------- STAC VORLAGE -----------------

STAC_COLLECTION = {
    "type": "Collection",
    "id": "permanentgreenland_annually",
    "title": "Permanent Greenland Phenology Dataset",
    "description": "Grünland-Phänologie-Zeitreihe Deutschland 1993-2022 basierend auf Fernerkundung.",
    "license": "CC-BY-4.0",
    "keywords": ["Grünland", "Phänologie", "Fernerkundung", "Deutschland", "Zeitreihe"],
    "extent": {
        "spatial": [280425.207, 5235501.264, 934425.207, 6101501.265],
        "temporal": ["1993-01-01T00:00:00Z", "2022-01-01T00:00:00Z"]
    },
    "providers": [
        {"name": "Julius Kühn-Institut", "roles": ["producer"]},
        {"name": "BonaRes Datenzentrum", "roles": ["publisher"]}
    ],
    "links": [],
    "item_assets": {
        "doy1": {"title": "Greenup - Day of Year", "type": "image/tiff; application=geotiff; profile=cog"},
        "doy25": {"title": "Cut for hay - Day of Year", "type": "image/tiff; application=geotiff; profile=cog"}
    }
}

stac_items = []

# ----------------- FUNKTIONEN -----------------

def download_year(year, output_path):
    params = {
        "SERVICE": "WCS",
        "VERSION": "2.1.0",
        "REQUEST": "GetCoverage",
        "COVERAGEID": COVERAGE_ID,
        "FORMAT": "image/tiff",
        "SUBSET": [f"ansi(\"{year}-01-01T00:00:00.000Z\")"]
    }
    url = BASE_URL + "&" + "&".join(
        [f"{k}={v}" if not isinstance(v, list) else "&".join([f"{k}={vi}" for vi in v]) for k, v in params.items()]
    )
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        raise Exception(f"Download-Fehler für {year}: {response.status_code}")

def prepare_cog_with_metadata(input_path, output_path, year):
    temp_tif = output_path.replace(".tif", "_tmp.tif")
    subprocess.run(["gdal_translate", "-of", "GTiff", "-co", "TILED=YES", "-co", "COMPRESS=DEFLATE", input_path, temp_tif], check=True)
    subprocess.run(["gdaladdo", "-r", "average", temp_tif, "2", "4", "8", "16", "32"], check=True)
    with rasterio.open(temp_tif, "r+") as ds:
        ds.update_tags(YEAR=str(year), DATASOURCE="JKI WCS", DESCRIPTION="Grünland-Phänologie-Datensatz")
        for idx, (short_name, desc) in enumerate(BAND_INFO, start=1):
            ds.update_tags(idx, NAME=short_name, DESCRIPTION=desc)
    subprocess.run(["gdal_translate", "-of", "COG", "-co", "COMPRESS=DEFLATE", "-co", "TILED=YES", "-co", "OVERVIEWS=INCLUDE_EXISTING", temp_tif, output_path], check=True)
    os.remove(temp_tif)

def generate_stac_item(year, cog_filename):
    item = {
        "type": "Feature",
        "id": f"permanentgreenland_{year}",
        "properties": {
            "datetime": f"{year}-01-01T00:00:00Z",
            "title": f"Grünland-Phänologie {year}",
            "description": "Grünland-Phänologie-Metriken für Deutschland",
            "license": "CC-BY-4.0",
            "publisher": "BonaRes Datenzentrum",
            "authors": ["Julius Kühn-Institut"],
            "resource_type": "Dataset",
            "subject": "Bodenforschung, Phänologie, Fernerkundung",
            "geography": "Deutschland",
            "funding": "Gefördert durch BMBF im Rahmen von BonaRes",
            "contact": "datenzentrum@bonares.de"
        },
        "assets": {
            "data": {
                "href": cog_filename,
                "title": f"Grünland {year}",
                "type": "image/tiff; application=geotiff; profile=cog"
            }
        }
    }
    return item

# ----------------- HAUPTLOOP -----------------

for year in YEARS:
    raw_tif = os.path.join(OUT_FOLDER, f"temp_{year}.tif")
    cog_tif = os.path.join(OUT_FOLDER, f"permanentgreenland_{year}.tif")
    download_year(year, raw_tif)
    prepare_cog_with_metadata(raw_tif, cog_tif, year)
    os.remove(raw_tif)
    stac_item = generate_stac_item(year, os.path.basename(cog_tif))
    stac_items.append(stac_item)

# STAC JSON speichern
stac_collection = STAC_COLLECTION.copy()
stac_collection["links"] = []
stac_collection["features"] = stac_items

with open(os.path.join(OUT_FOLDER, "stac_catalog.json"), "w") as f:
    json.dump(stac_collection, f, indent=2)

print("Alle COGs fertig und STAC-Katalog erzeugt.")

import sys
import os
import subprocess
from rio_cogeo.cogeo import cog_validate
from rasterio import open as rio_open
from rasterio.errors import RasterioIOError

def check_cog_validity(file_path):
    print(f"\n🔍 Prüfe, ob '{file_path}' ein gültiger COG ist...")
    try:
        valid = cog_validate(file_path)
        print("✅ Gültiger Cloud Optimized GeoTIFF (COG)" if valid else "❌ Kein gültiger COG")
        return valid
    except Exception as e:
        print(f"⚠️ Fehler bei der Validierung: {e}")
        return False

def print_rasterio_metadata(file_path):
    print("\n📄 Rasterio Metadaten:")
    try:
        with rio_open(file_path) as src:
            print(f"Driver: {src.driver}")
            print(f"CRS: {src.crs}")
            print(f"Bounds: {src.bounds}")
            print(f"Width x Height: {src.width} x {src.height}")
            print(f"Bands: {src.count}")
            print(f"Dtype: {src.dtypes}")
            print(f"Transform: {src.transform}")
            print(f"Metadata: {src.meta}")
    except RasterioIOError as e:
        print(f"⚠️ Fehler beim Öffnen der Datei mit Rasterio: {e}")

def print_gdalinfo(file_path):
    print("\n🛰️ GDAL Info:")
    try:
        result = subprocess.run(["gdalinfo", file_path], capture_output=True, text=True, check=True)
        print(result.stdout)
    except FileNotFoundError:
        print("⚠️ GDAL nicht installiert oder 'gdalinfo' nicht im Pfad.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Fehler bei gdalinfo: {e.stderr}")

def main():
    if len(sys.argv) != 2:
        print("❌ Bitte gib den Pfad zu einer GeoTIFF-Datei an.\nBeispiel: python check_cog_metadata.py deine_datei.tif")
        return

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"❌ Datei nicht gefunden: {file_path}")
        return

    check_cog_validity(file_path)
    print_rasterio_metadata(file_path)
    print_gdalinfo(file_path)

if __name__ == "__main__":
    main()

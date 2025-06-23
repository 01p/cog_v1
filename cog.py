import rasterio.shutil

# Convert to COG
with rasterio.open("coverage.tif") as src:
    rasterio.shutil.copy(
        src,
        "coverage_cog.tif",
        driver="COG",
        compress="deflate",
        overview_resampling="nearest"
    )
import os
import rasterio
import numpy as np

# ======================================================
# Sentinel-2 Band Paths
# ======================================================

b04 = r"C:\Users\Rajesh Prasad\Downloads\S2C_MSIL2A_20241219T053301_N9906_R105_T43RFN_20241219T103312.SAFE\S2C_MSIL2A_20241219T053301_N9906_R105_T43RFN_20241219T103312.SAFE\GRANULE\L2A_T43RFN_A001505_20241219T053623\IMG_DATA\R10m\T43RFN_20241219T053301_B04_10m.jp2"
b03 = r"C:\Users\Rajesh Prasad\Downloads\S2C_MSIL2A_20241219T053301_N9906_R105_T43RFN_20241219T103312.SAFE\S2C_MSIL2A_20241219T053301_N9906_R105_T43RFN_20241219T103312.SAFE\GRANULE\L2A_T43RFN_A001505_20241219T053623\IMG_DATA\R10m\T43RFN_20241219T053301_B03_10m.jp2"

b02 = r"C:\Users\Rajesh Prasad\Downloads\S2C_MSIL2A_20241219T053301_N9906_R105_T43RFN_20241219T103312.SAFE\S2C_MSIL2A_20241219T053301_N9906_R105_T43RFN_20241219T103312.SAFE\GRANULE\L2A_T43RFN_A001505_20241219T053623\IMG_DATA\R10m\T43RFN_20241219T053301_B02_10m.jp2"

# ======================================================
# Verify files exist
# ======================================================

for path in [b04, b03, b02]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

print("✅ All input files found!")

# ======================================================
# Output folder
# ======================================================

output_folder = r"VayuNetra_Training\images"
os.makedirs(output_folder, exist_ok=True)

out = os.path.join(output_folder, "tile_delhi_3.tif")

# ======================================================
# Read Sentinel bands
# ======================================================

with rasterio.open(b04) as red_ds, \
     rasterio.open(b03) as green_ds, \
     rasterio.open(b02) as blue_ds:

    red = red_ds.read(1).astype(np.float32)
    green = green_ds.read(1).astype(np.float32)
    blue = blue_ds.read(1).astype(np.float32)

    # Scale reflectance to 0-1
    red /= 10000.0
    green /= 10000.0
    blue /= 10000.0

    # Clip values
    red = np.clip(red, 0, 1)
    green = np.clip(green, 0, 1)
    blue = np.clip(blue, 0, 1)

    # Convert to 8-bit RGB
    rgb = np.stack([
        (red * 255).astype(np.uint8),
        (green * 255).astype(np.uint8),
        (blue * 255).astype(np.uint8)
    ])

    profile = red_ds.profile.copy()

    profile.update(
        driver="GTiff",
        dtype=rasterio.uint8,
        count=3,
        compress="lzw"
    )

    with rasterio.open(out, "w", **profile) as dst:
        dst.write(rgb)

print("\n====================================")
print("✅ RGB GeoTIFF created successfully!")
print("Saved to:")
print(os.path.abspath(out))
print("====================================")
"""
VayuNetra E1 — Data Preprocessing Pipeline
==========================================
Converts raw downloaded Sentinel-2 GeoTIFFs (from Google Earth Engine or
Copernicus Hub) into 256x256 patch tiles ready for model training.

USAGE:
    python scripts/preprocess_tiles.py \
        --image_dir data/raw/images \
        --mask_dir  data/raw/masks \
        --output_dir data/processed \
        --patch_size 256 \
        --overlap 64

FOLDER STRUCTURE EXPECTED:
    data/
    ├── raw/
    │   ├── images/                  ← Downloaded Sentinel-2 GeoTIFFs
    │   │   ├── sentinel2_delhi.tif
    │   │   └── sentinel2_agra.tif
    │   └── masks/                   ← Corresponding label GeoTIFFs (same name)
    │       ├── sentinel2_delhi.tif
    │       └── sentinel2_agra.tif
    └── processed/                   ← Output directory (created automatically)
        ├── images/
        │   ├── sentinel2_delhi_0000.tif
        │   └── ...
        └── masks/
            ├── sentinel2_delhi_0000.tif
            └── ...

MASK CLASS VALUES:
    0 = Background
    1 = Construction / Dust
    2 = Brick Kiln
    3 = Open Burning / Biomass

NOTE: If you don't have masks yet, run with --no_masks to just tile the images.
      You can then label them using Label Studio or JOSM.
"""

import argparse
import os
import sys
import numpy as np
import rasterio
from rasterio.windows import Window
from pathlib import Path
from tqdm import tqdm


def get_patches(width, height, patch_size, overlap):
    """Generate (row_off, col_off) offsets for all patches with given overlap."""
    step = patch_size - overlap
    offsets = []
    for row in range(0, height - overlap, step):
        for col in range(0, width - overlap, step):
            # Clamp to image bounds
            r = min(row, height - patch_size)
            c = min(col, width - patch_size)
            offsets.append((r, c))
    # Deduplicate
    return list(dict.fromkeys(offsets))


def tile_image(src_path, out_dir, name_prefix, patch_size=256, overlap=64, is_mask=False):
    """Slice a single GeoTIFF into patches and save each as a separate GeoTIFF."""
    saved = 0
    with rasterio.open(src_path) as src:
        width, height = src.width, src.height
        profile = src.profile.copy()
        
        if width < patch_size or height < patch_size:
            print(f"  ⚠️  Skipping {src_path.name}: image ({width}x{height}) smaller than patch size ({patch_size}).")
            return 0
        
        offsets = get_patches(width, height, patch_size, overlap)
        
        profile.update({
            'width': patch_size,
            'height': patch_size,
            'driver': 'GTiff',
            'compress': 'lzw',
        })
        
        for idx, (row_off, col_off) in enumerate(offsets):
            window = Window(col_off, row_off, patch_size, patch_size)
            data = src.read(window=window)
            
            # Skip near-empty patches (mostly black / no-data)
            if is_mask:
                # For masks: skip patches with no labels (all background)
                if data.max() == 0:
                    continue
            else:
                # For images: skip patches with >20% zero pixels (cloud/nodata)
                zero_frac = (data == 0).mean()
                if zero_frac > 0.20:
                    continue
            
            # Update geotransform for the patch
            transform = src.window_transform(window)
            patch_profile = profile.copy()
            patch_profile['transform'] = transform
            
            if not is_mask:
                patch_profile['count'] = src.count
                patch_profile['dtype'] = src.dtypes[0]
            else:
                patch_profile['count'] = 1
                patch_profile['dtype'] = 'uint8'
            
            out_path = out_dir / f"{name_prefix}_{idx:04d}.tif"
            with rasterio.open(out_path, 'w', **patch_profile) as dst:
                dst.write(data)
            
            saved += 1
    
    return saved


def run(image_dir, mask_dir, output_dir, patch_size, overlap, no_masks):
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    
    out_img_dir = output_dir / "images"
    out_msk_dir = output_dir / "masks"
    out_img_dir.mkdir(parents=True, exist_ok=True)
    if not no_masks:
        out_msk_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = list(image_dir.glob("*.tif")) + list(image_dir.glob("*.tiff"))
    
    if not image_files:
        print(f"❌ No .tif files found in {image_dir}")
        sys.exit(1)
    
    print(f"\n📂 Found {len(image_files)} image file(s).")
    print(f"📐 Patch size: {patch_size}x{patch_size}, Overlap: {overlap}px\n")
    
    total_patches = 0
    
    for img_path in tqdm(image_files, desc="Processing files"):
        prefix = img_path.stem  # filename without extension
        
        # ── Tile image ────────────────────────────────────────────────
        n = tile_image(img_path, out_img_dir, prefix, patch_size, overlap, is_mask=False)
        print(f"  ✅ {img_path.name} → {n} image patches")
        
        # ── Tile mask (if exists) ─────────────────────────────────────
        if not no_masks:
            mask_dir_path = Path(mask_dir)
            mask_path = mask_dir_path / img_path.name  # same filename
            
            if mask_path.exists():
                m = tile_image(mask_path, out_msk_dir, prefix, patch_size, overlap, is_mask=True)
                print(f"  ✅ {mask_path.name} → {m} mask patches")
                total_patches += min(n, m)
            else:
                print(f"  ⚠️  No matching mask found for {img_path.name} (expected: {mask_path})")
                total_patches += n
        else:
            total_patches += n
    
    print(f"\n🎉 Done! {total_patches} patch pairs saved to: {output_dir}")
    print(f"   images/ → {len(list(out_img_dir.glob('*.tif')))} files")
    if not no_masks:
        print(f"   masks/  → {len(list(out_msk_dir.glob('*.tif')))} files")
    
    print("\n📋 Next step: Upload the 'processed/' folder to Kaggle as a dataset,")
    print("   then run ml/vision/train.py pointing DATA_DIR to that dataset path.")


def main():
    parser = argparse.ArgumentParser(description="Tile Sentinel-2 GeoTIFFs into training patches.")
    parser.add_argument("--image_dir",  default="data/raw/images", help="Directory with raw Sentinel-2 GeoTIFFs")
    parser.add_argument("--mask_dir",   default="data/raw/masks",  help="Directory with label mask GeoTIFFs")
    parser.add_argument("--output_dir", default="data/processed",  help="Output directory for patches")
    parser.add_argument("--patch_size", type=int, default=256,     help="Patch width/height in pixels (default: 256)")
    parser.add_argument("--overlap",    type=int, default=64,      help="Overlap between patches in pixels (default: 64)")
    parser.add_argument("--no_masks",   action="store_true",       help="Skip mask tiling (use when labels not yet available)")
    args = parser.parse_args()
    
    run(args.image_dir, args.mask_dir, args.output_dir, args.patch_size, args.overlap, args.no_masks)


if __name__ == "__main__":
    main()

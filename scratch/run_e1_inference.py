import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure we're running from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from core.supa import client
from ml.vision.inference import CVSourceDetector

def run():
    print(" Initializing CVSourceDetector...")
    detector = CVSourceDetector(model_path="artifacts/e1_cv_model.pth")
    
    tile_path = "VayuNetra_Training/VayuNetra_Training/images/tile_delhi_1.tif"
    if not os.path.exists(tile_path):
        print(f" Could not find test tile at {tile_path}")
        return

    print(f" Running inference on {tile_path} (cropping a few patches)...")
    # Take more patches because real sources are sparse
    gdf = detector.infer_large_tile(tile_path, max_patches=2000)
    
    if gdf.empty:
        print(" No sources detected in those patches.")
        return
        
    print(f" Detected {len(gdf)} sources! Pushing to Supabase...")
    
    db = client()
    inserted = 0
    for idx, row in gdf.iterrows():
        from shapely.geometry import mapping
        geom_geojson = mapping(row.geometry)
        
        record = {
            "city_id": "delhi",
            "name": f"CV Detection {idx}",
            "type": row.type,
            "source_origin": row.source_origin,
            "geom": geom_geojson,
            "detection_confidence": row.detection_confidence,
            "attributes": {}
        }
        
        try:
            db.table("emission_sources").insert(record).execute()
            inserted += 1
        except Exception as e:
            print(f"Error inserting: {e}")
            
    print(f" Successfully inserted {inserted} cv_detected rows into emission_sources!")

if __name__ == "__main__":
    run()

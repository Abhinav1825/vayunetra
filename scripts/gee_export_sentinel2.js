/**
 * VayuNetra E1 — Sentinel-2 Tile Exporter (Google Earth Engine)
 *
 * HOW TO USE:
 * 1. Go to https://code.earthengine.google.com
 * 2. Paste this entire script into the Code Editor
 * 3. Click "Run"
 * 4. In the "Tasks" panel (top right), click "RUN" next to each export task
 * 5. Files will be saved to your Google Drive under "VayuNetra_Sentinel2/"
 *
 * REGIONS COVERED:
 *   - Delhi NCR (primary)
 *   - Agra (brick kilns)
 *   - Kanpur (industrial)
 *   - Lucknow (open burning)
 */

// ─── CONFIG ───────────────────────────────────────────────────────────────────
var YEAR        = 2024;
var CLOUD_MAX   = 10;       // max cloud cover % per tile
var BANDS       = ['B4', 'B3', 'B2'];  // RGB (True Color) — change to ['B8','B4','B3'] for NIR False Color
var SCALE       = 10;       // Sentinel-2 native resolution (metres)
var DRIVE_FOLDER = 'VayuNetra_Sentinel2';
var TILE_SIZE   = 256;      // pixels per output patch

// ─── REGIONS OF INTEREST ──────────────────────────────────────────────────────
var regions = {
  'delhi_ncr': ee.Geometry.Rectangle([76.8, 28.4, 77.5, 28.9]),
  'agra':      ee.Geometry.Rectangle([77.8, 27.0, 78.2, 27.4]),
  'kanpur':    ee.Geometry.Rectangle([80.1, 26.3, 80.5, 26.6]),
  'lucknow':   ee.Geometry.Rectangle([80.8, 26.7, 81.1, 26.9]),
};

// ─── SENTINEL-2 COLLECTION ───────────────────────────────────────────────────
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_MAX))
  .filterDate(YEAR + '-10-01', YEAR + '-12-31')  // Oct-Dec: less monsoon cloud
  .select(BANDS);

// ─── EXPORT EACH REGION ──────────────────────────────────────────────────────
Object.keys(regions).forEach(function(regionName) {
  var roi = regions[regionName];
  
  // Get the least cloudy single image for this region
  var img = s2.filterBounds(roi).sort('CLOUDY_PIXEL_PERCENTAGE').first();

  // Clip to the region
  var clipped = img.clip(roi);
  
  // Normalize to [0, 1] — divide by 10000 (Sentinel-2 L2A scale factor)
  var normalized = clipped.divide(10000).toFloat();
  
  // Export to Google Drive
  Export.image.toDrive({
    image: normalized,
    description: 'sentinel2_' + regionName + '_' + YEAR,
    folder: DRIVE_FOLDER,
    fileNamePrefix: 'sentinel2_' + regionName,
    region: roi,
    scale: SCALE,
    maxPixels: 1e10,
    fileFormat: 'GeoTIFF',
    formatOptions: { cloudOptimized: true }
  });
  
  print('Export task created for:', regionName);
  
  // Preview on the map
  Map.addLayer(
    clipped.visualize({bands: BANDS, min: 0, max: 3000}),
    {},
    regionName
  );
  Map.centerObject(roi, 10);
});

print('✅ All export tasks created. Go to the Tasks panel and click RUN on each one.');
print('Files will appear in your Google Drive under:', DRIVE_FOLDER);

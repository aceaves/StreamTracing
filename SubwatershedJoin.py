# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 14:05:36 2024

@author: Ashton.Eaves
"""
import geopandas as gpd
import pandas as pd

# Load the streamlines and subwatersheds data
streamlines = gpd.read_file(r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/Outputs/eDNA_Upstream_Streamlines_10km_All3.shp")
subwatersheds = gpd.read_file(r"C:/2_Workspaces/Python/Subwatersheds/Subwatersheds_v1.shp")

# Buffer the streamlines by 10 meters to ensure capturing subwatersheds near the streamlines
#streamlines['geometry'] = streamlines.geometry.buffer(10)

# Align CRS if necessary
if streamlines.crs != subwatersheds.crs:
    subwatersheds = subwatersheds.to_crs(streamlines.crs)

# Get unique sites from streamlines
unique_sites = streamlines['Site'].unique()

# Store results
all_upstream_subwatersheds = []

# Process each site
for site in unique_sites:
    print(f"Processing site: {site}")
    
    # Select streamlines for the current site
    site_streamlines = streamlines[streamlines['Site'] == site]
    
    if site_streamlines.empty:
        print(f"No streamlines for site: {site}")
        continue

    # Perform spatial join between site-specific streamlines and subwatersheds
    upstream_with_subwatersheds = gpd.sjoin(
        subwatersheds, 
        site_streamlines[['geometry']], 
        how='inner', 
        predicate='intersects'
    )
    
    if upstream_with_subwatersheds.empty:
        print(f"No subwatersheds found for site: {site}")
        continue

    # Assign site ID and append to the results
    upstream_with_subwatersheds['Site'] = site
    all_upstream_subwatersheds.append(upstream_with_subwatersheds)

# Combine results if any subwatersheds were found
if all_upstream_subwatersheds:
    final_upstream_subwatersheds = gpd.GeoDataFrame(
        pd.concat(all_upstream_subwatersheds, ignore_index=True),
        crs=subwatersheds.crs
    )

    # Save individual subwatersheds output
    output_path = r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/Outputs/eDNA_Upstream_Subwatersheds_10km2.shp"
    final_upstream_subwatersheds.to_file(output_path, driver='ESRI Shapefile')
    print(f"Saved individual subwatersheds to: {output_path}")

    # Dissolve subwatersheds by site name
#    dissolved_subwatersheds = final_upstream_subwatersheds.dissolve(by='Site')

    # Save the dissolved subwatersheds
#    dissolved_output_path = r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/Outputs/eDNA_Upstream_Subwatersheds_10km_Dissolved1.shp"
#    dissolved_subwatersheds.to_file(dissolved_output_path, driver='ESRI Shapefile')

#    print(f"Dissolved subwatersheds saved to: {dissolved_output_path}")
else:
    print("No upstream subwatersheds found.")



#### END ####
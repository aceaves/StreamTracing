# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 14:05:36 2024

@author: Ashton.Eaves
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from collections import deque

# Load the streamlines, start points, and subwatersheds data
start_points = gpd.read_file(r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/eDNA_Sites/eDNA_Sites_All.shp")
streamlines = gpd.read_file(r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/Outputs/eDNA_Upstream_Streamlines_10km_All3.shp")
subwatersheds = gpd.read_file(r"C:/2_Workspaces/Python/Subwatersheds/Subwatersheds_v1.shp")

# Create a buffer of 60 meters around the start points to ensure an intersection
start_points_buffered = start_points.copy()
start_points_buffered['geometry'] = start_points_buffered.geometry.buffer(60)

# Ensure the CRS matches between streamlines and subwatersheds
if streamlines.crs != subwatersheds.crs:
    subwatersheds = subwatersheds.to_crs(streamlines.crs)

# Initialize a list to store all upstream subwatersheds
all_upstream_subwatersheds = []

# Function to trace all upstream streamlines using spatial relationships
def trace_upstream_streamlines(start_streamlines, streamlines):
    # Initialize deque with the initial streamlines
    queue = deque(start_streamlines.index)
    visited_indices = set(queue)  # Keep track of visited streamlines

    while queue:
        current_index = queue.popleft()

        # Find streamlines that are spatially connected to the current one
        current_geom = streamlines.loc[current_index].geometry
        touching_streamlines = streamlines[streamlines.geometry.touches(current_geom)]

        for idx in touching_streamlines.index:
            if idx not in visited_indices:
                visited_indices.add(idx)
                queue.append(idx)

    return streamlines.loc[list(visited_indices)]

# Loop through each site to find subwatersheds
for site_index, site_row in start_points_buffered.iterrows():
    # Find streamlines that intersect with the buffered start point
    intersecting_streamlines = gpd.sjoin(streamlines, gpd.GeoDataFrame([site_row], crs=start_points_buffered.crs), how='inner', predicate='intersects')

    if intersecting_streamlines.empty:
        print(f"No streamlines intersect for site: {site_row['Site']}")
        continue

    # Trace all upstream streamlines for this site using spatial relationships
    upstream_streamlines = trace_upstream_streamlines(intersecting_streamlines, streamlines)

    if upstream_streamlines.empty:
        print(f"No upstream streamlines found for site: {site_row['Site']}")
        continue

    # Perform a spatial join between the upstream streamlines and subwatersheds
    upstream_with_subwatersheds = gpd.sjoin(subwatersheds, upstream_streamlines[['geometry']], how='inner', predicate='intersects')

    if upstream_with_subwatersheds.empty:
        print(f"No subwatershed join for site: {site_row['Site']}")
        continue
    else:
        print(f"Subwatershed join successful for site: {site_row['Site']}")

    # Append the subwatershed polygons to the result list
    upstream_with_subwatersheds['Site'] = site_row['Site']  # Assign the site to the subwatersheds
    all_upstream_subwatersheds.append(upstream_with_subwatersheds)

# Check if any upstream subwatersheds were collected
if not all_upstream_subwatersheds:
    print("No upstream subwatersheds found.")
else:
    # Concatenate all subwatersheds for all sites
    final_upstream_subwatersheds = gpd.GeoDataFrame(pd.concat(all_upstream_subwatersheds, ignore_index=True), crs=subwatersheds.crs)

    # Drop duplicates in case the same subwatershed is joined multiple times
    final_upstream_subwatersheds = final_upstream_subwatersheds.drop_duplicates(subset='geometry')

    # Save the result as polygons
    output_path = r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/Outputs/eDNA_Upstream_Subwatersheds_10km.shp"
    final_upstream_subwatersheds.to_file(output_path, driver='ESRI Shapefile')

    print(f"Saved to: {output_path}")






#### END ####
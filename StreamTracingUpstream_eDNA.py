# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 13:17:22 2024

@author: Ashton.Eaves
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, MultiLineString
from collections import deque
import time  # Import the time module

# Start the timer
start_time = time.time()


# Load the streamlines and start points data
streamlines = gpd.read_file(r"C:/2_Workspaces/Python/Streams/StreamNetwork_v1_All.shp")
start_points = gpd.read_file(r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/eDNA_SitesTest3.shp")

# Create a buffer of 60 meters around the start points
start_points_buffered = start_points.copy()
start_points_buffered['geometry'] = start_points_buffered.geometry.buffer(60)

# Initialize a list to store results
all_upstream_streamlines = []

# Function to calculate length of a streamline
def calculate_length(geom):
    if isinstance(geom, LineString):
        return geom.length
    elif isinstance(geom, MultiLineString):
        return sum(line.length for line in geom.geoms)
    return 0

# Loop through each site to create a separate trace
for site_index, site_row in start_points_buffered.iterrows():
    # Check intersection between streamlines and buffered start points for each site
    intersection_check = gpd.sjoin(streamlines, gpd.GeoDataFrame([site_row], crs=start_points.crs), how='inner', predicate='intersects')

    if intersection_check.empty:
        continue

    # Initialize a set to track visited streamlines and a deque for upstream traversal
    visited_indices = set(intersection_check.index)
    queue = deque([(index, 0, site_row['Site']) for index in intersection_check.index])  # Track index, cumulative distance, and 'Site'
    
    # Perform upstream tracing for each site
    while queue:
        current_index, cumulative_distance, site = queue.popleft()
        current_streamline = streamlines.loc[current_index]

        # Check if cumulative distance exceeds 10 km. Comment out if not necessary.
       # if cumulative_distance > 10000:  # 10 km in meters
       #     continue

        # Get the start point of the current streamline
        if isinstance(current_streamline.geometry, LineString):
            start_point = Point(current_streamline.geometry.coords[0])
        elif isinstance(current_streamline.geometry, MultiLineString):
            start_point = Point(current_streamline.geometry.geoms[0].coords[0])
        else:
            continue  # Skip unsupported geometries

        # Find the previous streamlines that end at the start point
        previous_streamlines = streamlines[streamlines.index != current_index].copy()
        previous_streamlines['end_point'] = previous_streamlines.geometry.apply(
            lambda geom: Point(geom.coords[-1]) if isinstance(geom, LineString) else (
                Point(geom.geoms[-1].coords[-1]) if isinstance(geom, MultiLineString) else None
            )
        )
        upstream_candidates = previous_streamlines[previous_streamlines.end_point == start_point]

        # Add upstream candidates to the queue and visited set
        for idx in upstream_candidates.index:
            if idx not in visited_indices:
                visited_indices.add(idx)
                distance = calculate_length(upstream_candidates.loc[idx].geometry)
                queue.append((idx, cumulative_distance + distance, site))
    
    # Create a GeoDataFrame of the upstream streamlines for this site
    upstream_streamlines = streamlines.loc[list(visited_indices)]
    upstream_streamlines['Site'] = site_row['Site']  # Assign the site to the traced streamlines

    # Append to the final result
    all_upstream_streamlines.append(upstream_streamlines)

# Concatenate all upstream streamlines for all sites
final_upstream_streamlines = gpd.GeoDataFrame(pd.concat(all_upstream_streamlines, ignore_index=True), crs=streamlines.crs)

# Save the result
output_path = r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/Outputs/eDNA_Upstream_Streamlines_Test3.shp"
final_upstream_streamlines.to_file(output_path, driver='ESRI Shapefile')

# End of script, log total execution time
end_time = time.time()
print(f"Total execution time: {end_time - start_time:.2f} seconds")


#### END ####
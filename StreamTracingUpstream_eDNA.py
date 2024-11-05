# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 13:17:22 2024

@author: Ashton.Eaves
"""
import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
from collections import deque

# Load the streamlines and start points data
streamlines = gpd.read_file(r"C:/2_Workspaces/Python/Streams/StreamNetwork_v1.shp")
start_points = gpd.read_file(r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/eDNA_Sites/eDNA_Sites_All.shp")

# Create a buffer of 50 meters around the start points
start_points_buffered = start_points.copy()
start_points_buffered['geometry'] = start_points_buffered.geometry.buffer(50)

# Check intersection between streamlines and buffered start points
intersection_check = gpd.sjoin(streamlines, start_points_buffered[['Site', 'geometry']], how='inner', predicate='intersects')

# Initialize a set to track visited streamlines and a deque for upstream traversal
visited_indices = set(intersection_check.index)
queue = deque([(index, 0) for index in intersection_check.index])  # Track index and cumulative distance

# Function to calculate length of a streamline
def calculate_length(geom):
    if isinstance(geom, LineString):
        return geom.length
    elif isinstance(geom, MultiLineString):
        return sum(line.length for line in geom.geoms)
    return 0

# Start tracing upstream
while queue:
    current_index, cumulative_distance = queue.popleft()
    current_streamline = streamlines.loc[current_index]
    
    # Check if cumulative distance exceeds 10 km
    if cumulative_distance > 10000:  # 10 km in meters
        continue

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
            queue.append((idx, cumulative_distance + distance))

# Create a GeoDataFrame of all upstream streamlines
upstream_streamlines = streamlines.loc[list(visited_indices)]

# Drop any non-geometry columns before saving
upstream_streamlines = upstream_streamlines.drop(columns=['end_point'], errors='ignore')

# Save the result
output_path = r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/Outputs/eDNA_Upstream_Streamlines_10km_Waipawa.shp"
upstream_streamlines.to_file(output_path, driver='ESRI Shapefile')


#### END ####
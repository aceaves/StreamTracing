# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 14:09:09 2024

@author: Ashton.Eaves
"""
import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
from collections import deque

# Load the streamlines and start points data
streamlines = gpd.read_file(r"C:/2_Workspaces/Python/eDNA_ExtremeWeather/eDNA_Sites/eDNA_Sites.shp")
start_points = gpd.read_file(r"C:/2_Workspaces/Python/Streams/StreamNetwork_v1.shp")

# Create a buffer of 10 meters around the start points
start_points_buffered = start_points.copy()
start_points_buffered['geometry'] = start_points_buffered.geometry.buffer(10)

# Check intersection between streamlines and buffered start points
intersection_check = gpd.sjoin(streamlines, start_points_buffered, how='inner', predicate='intersects')

# Initialize a set to track visited streamlines and a deque for downstream traversal
visited_indices = set(intersection_check.index)
queue = deque(intersection_check.index)

# Start tracing downstream
while queue:
    current_index = queue.popleft()
    current_streamline = streamlines.loc[current_index]

    # Get the endpoint of the current streamline
    if isinstance(current_streamline.geometry, LineString):
        end_point = Point(current_streamline.geometry.coords[-1])
    elif isinstance(current_streamline.geometry, MultiLineString):
        end_point = Point(current_streamline.geometry.geoms[-1].coords[-1])
    else:
        continue  # Skip unsupported geometries

    # Find the next streamlines that start at the endpoint
    next_streamlines = streamlines[streamlines.index != current_index].copy()
    next_streamlines['start_point'] = next_streamlines.geometry.apply(
        lambda geom: Point(geom.coords[0]) if isinstance(geom, LineString) else (
            Point(geom.geoms[0].coords[0]) if isinstance(geom, MultiLineString) else None
        )
    )
    downstream_candidates = next_streamlines[next_streamlines.start_point == end_point]

    # Add downstream candidates to the queue and visited set
    for idx in downstream_candidates.index:
        if idx not in visited_indices:
            visited_indices.add(idx)
            queue.append(idx)

# Create a GeoDataFrame of all downstream streamlines
downstream_streamlines = streamlines.loc[list(visited_indices)]

# Drop any non-geometry columns before saving
downstream_streamlines = downstream_streamlines.drop(columns=['start_point'], errors='ignore')

# Save the result
output_path = r"I:/339 Land R&I/339_WORK_REQUESTS/2024/20241017_eDNA_ExtremeWeather/3_Outputs/eDNA_Upstream_Streamlines/eDNA_Upstream_Streamlines.shp"
downstream_streamlines.to_file(output_path, driver='ESRI Shapefile')


#### END ####
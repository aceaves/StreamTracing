# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 13:17:22 2024

@author: Ashton.Eaves
"""
import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString

# Load the watershed (polygons) and streamlines (polylines) data from shapefiles
streamlines = gpd.read_file(r"C:/2_Workspaces/Python/AlligatorWeed/Shapes/Stream_network_v1_tukituki.shp")
start_points = gpd.read_file(r"C:/2_Workspaces/Python/AlligatorWeed/Shapes/Biosecurity_ExportAlligatorWeed.shp")

# Create a buffer of 10 meters around the start points
start_points['geometry'] = start_points.geometry.buffer(10)

# Check intersection between streamlines and buffered start points
intersection_check = gpd.sjoin(streamlines, start_points, how='inner', predicate='intersects')
downstream_indices = set(intersection_check.index)

# Function to get the endpoint of each streamline
def get_end_point(geom):
    if isinstance(geom, LineString):
        return Point(geom.xy[0][-1], geom.xy[1][-1])
    elif isinstance(geom, MultiLineString):
        return Point(list(geom.geoms)[-1].coords[-1])
    else:
        raise ValueError("Unsupported geometry type")

# Get endpoints of all streamlines
streamlines['end_point'] = streamlines.geometry.apply(get_end_point)

# Use a while loop to trace downstream until no new streamlines are found
visited_indices = set()
while downstream_indices:
    # Filter out already visited streamlines
    new_indices = downstream_indices - visited_indices
    if not new_indices:
        break

    # Mark new indices as visited
    visited_indices.update(new_indices)

    # Get the start points for the next streamlines
    selected_start_points = streamlines.loc[list(new_indices)].copy()
    selected_start_points['geometry'] = selected_start_points.geometry.apply(lambda geom: Point(geom.coords[0]) if isinstance(geom, LineString) else Point(geom.geoms[0].coords[0]))

    # Find next downstream streamlines using spatial join on start points and end points
    next_streamlines = gpd.sjoin(streamlines, selected_start_points, how='inner', predicate='intersects')
    downstream_indices.update(next_streamlines.index)

# Drop the 'end_point' column and any other non-geometry columns that could cause issues
output_streamlines = streamlines.loc[list(visited_indices)].drop(columns=['end_point'], errors='ignore')

# Save the result to a shapefile
output_path = r"C:/2_Workspaces/Python/AlligatorWeed/Shapes/Downstream_Streamlines.shp"
output_streamlines.to_file(output_path, driver='ESRI Shapefile')

#### END ####
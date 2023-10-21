# -*- coding: utf-8 -*-

import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap

# Replace the path with the correct one for your system
shapefile_path = "C:/Users/agaaz/.spyder-py3/Means_of_Transportation_to_Work.shp"

# Read the shapefile using Geopandas
gdf = gpd.read_file(shapefile_path)

# Print the columns of the GeoDataFrame
print(gdf.columns)

# Filter by state code (36 for New York)
ny_state_gdf = gdf[gdf['state'] == '36']

# Filter by county codes for NYC's 5 boroughs
nyc_county_codes = ['005', '047', '061', '081', '085']
nyc_gdf = ny_state_gdf[ny_state_gdf['county'].isin(nyc_county_codes)]

# Group by state and county and count the number of tracts
tract_counts = nyc_gdf.groupby(['state', 'county'])['tract'].nunique()

# Display the results
print(tract_counts)


# Rename the HH_CT and HH_PT columns
nyc_gdf = nyc_gdf.rename(columns={'HH_CT': 'Car', 'HH_PT': 'Public Transit'})

# Create a new column "Other" that is the sum of HH_MC, HH_BC, HH_WL, and HH_Other
nyc_gdf = nyc_gdf.assign(Other = nyc_gdf['HH_MC'] + nyc_gdf['HH_BC'] + nyc_gdf['HH_WL'] + nyc_gdf['HH_Other'])

# Drop the original columns HH_MC, HH_BC, HH_WL, HH_Other, and HH_CA
nyc_gdf = nyc_gdf.drop(columns=['HH_MC', 'HH_BC', 'HH_WL', 'HH_Other', 'HH_CA'])

# Now nyc_gdf should only have the columns 'car', 'Public Transit', and 'Other' for transportation means

# Make appropriate total column
nyc_gdf['Total Commuters'] = nyc_gdf['Car'] + nyc_gdf['Public Transit'] + nyc_gdf['Other']


# Define the number of parts for each borough
borough_parts = {'005': 3, '047': 5, '061': 0, '081': 5, '085': 1}

# Define part variable for nyc_gdf
nyc_gdf['part'] = np.nan


# Function to convert latitude and longitude to Web Mercator coordinates
def latlon_to_web_mercator(df, lon="INTPTLON", lat="INTPTLAT"):
    df[lon] = pd.to_numeric(df[lon])
    df[lat] = pd.to_numeric(df[lat])
    k = 6378137
    df["x"] = df[lon] * (k * np.pi / 180.0)
    df["y"] = np.log(np.tan((90 + df[lat]) * np.pi / 360.0)) * k
    return df

# Convert latitude and longitude to Web Mercator coordinates
nyc_gdf = latlon_to_web_mercator(nyc_gdf)

# Assign each tract to a part within its borough based on the KMeans clustering
for county, parts in borough_parts.items():
    if parts == 0:
        continue
    
    county_gdf = nyc_gdf.loc[nyc_gdf['county'] == county].copy()
    kmeans = KMeans(n_clusters=parts, random_state=42).fit(county_gdf[['x', 'y']])
    county_gdf['part'] = kmeans.labels_

    # Update the original DataFrame with the new part values
    nyc_gdf.update(county_gdf)

# Aggregate the data for each part of each borough
nyc_parts_gdf = nyc_gdf.groupby(['county', 'part']).sum(numeric_only=True).reset_index()


"""
import folium

# Create a base map centered on NYC
map_nyc = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

# Define a list of colors for the markers
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']

# Add the tracts to the map
for idx, row in nyc_gdf.iterrows():
    # Skip tracts that don't have a part assigned
    if pd.isna(row['part']):
        continue

    # Create a popup with the part label
    popup_text = f"County: {row['county']}, Part: {int(row['part'])}"
    popup = folium.Popup(popup_text, max_width=250)

    # Assign a color for the marker based on the part
    color = colors[int(row['part']) % len(colors)]

    # Add a marker with the tract's centroid coordinates and the popup
    folium.Marker(
        location=[row['INTPTLAT'], row['INTPTLON']],
        popup=popup,
        icon=folium.Icon(color=color, icon='info-sign'),
    ).add_to(map_nyc)

# Save the map to an HTML file
map_nyc.save("nyc_parts_map_colored2.html")
"""


# Define part labels for each borough based on geography
part_labels = {
    '005': {
        0: 'Southeast Bronx',
        1: 'North Bronx',
        2: 'Southwest Bronx'
    },
    '047': {
        0: 'Bushwick & East New York',
        1: 'Bay Ridge',
        2: 'Coney Island',
        3: 'Greenpoint & Williamsburg',
        4: 'Flatbush'
    },
    '081': {
        0: 'Central & South Queens',
        1: 'Northwest Queens',
        2: 'Rockaway Beach',
        3: 'East Queens',
        4: 'North Queens'
    },
}

# Define borough names
borough_names = {
    '005': 'Bronx',
    '047': 'Brooklyn',
    '081': 'Queens',
}

# MAKING THE PIE CHARTS

# Define pastel colors
colors = ['#ff9999','#66b3ff','#99ff99']

# Loop over each borough
for county, parts in part_labels.items():
    borough_name = borough_names[county]

    # Loop over each part in the borough
    for part, part_label in parts.items():
        # Filter the data to the current borough and part
        part_gdf = nyc_parts_gdf[(nyc_parts_gdf['county'] == county) & (nyc_parts_gdf['part'] == part)]

        # Calculate the sum of Car, Public Transit, and Other for the part
        total = part_gdf[['Car', 'Public Transit', 'Other']].values.sum()

        # Calculate the proportions of Car, Public Transit, and Other
        car = part_gdf['Car'].sum() / total
        public_transit = part_gdf['Public Transit'].sum() / total
        other = part_gdf['Other'].sum() / total

        # Create the pie chart
        plt.figure(figsize=(6, 6))
        plt.pie([car, public_transit, other], labels=['Car', 'Public Transit', 'Other'], colors=colors, autopct='%1.1f%%', pctdistance=0.85)
        plt.title(f'{borough_name}: {part_label}')
        plt.show()

# trying to make pie charts on nyc map


'''
# Define NYC coordinates
lon_min, lon_max, lat_min, lat_max = -74.25559, -73.70001, 40.49612, 40.91553

# Create a figure and axes with appropriate dimensions
fig, ax = plt.subplots(figsize=(20,20))

# Create the map
m = Basemap(projection='merc', resolution='i', llcrnrlon=lon_min, llcrnrlat=lat_min, urcrnrlon=lon_max, urcrnrlat=lat_max)

# Convert latitude and longitude to x, y coordinates
nyc_parts_gdf['x'], nyc_parts_gdf['y'] = m(nyc_parts_gdf['INTPTLON'].values, nyc_parts_gdf['INTPTLAT'].values)

# Loop over each borough

for county, parts in part_labels.items():
    borough_name = borough_names[county]

    # Loop over each part in the borough
    for part, part_label in parts.items():
        # Filter the data to the current borough and part
        part_gdf = nyc_parts_gdf[(nyc_parts_gdf['county'] == county) & (nyc_parts_gdf['part'] == part)]       
        # Calculate the sum of Car, Public Transit, and Other for the part
        total = part_gdf[['Car', 'Public Transit', 'Other']].values.sum()
        # Calculate the proportions of Car, Public Transit, and Other
        car = part_gdf['Car'].sum() / total
        public_transit = part_gdf['Public Transit'].sum() / total
        other = part_gdf['Other'].sum() / total
        for i, row in nyc_parts_gdf.iterrows():
            # Create a pie chart and add it to the map at the appropriate location
            x, y = part_gdf['x'].mean(), part_gdf['y'].mean()
            plt.pie([car, public_transit, other], labels=['Car', 'Public Transit', 'Other'], colors=colors, autopct='%1.1f%%', pctdistance=0.85)
            print(f"Placing pie chart for part {i} at position ({x}, {y})")
            plt.gca().set_position([x, y, .1, .1])

        print("Pie charts placement completed")
# Show the map with the pie charts
plt.show()
'''

# Calculate the mean x and y coordinates for each part
centroids = nyc_gdf.groupby(['county', 'part'])[['x', 'y']].mean().reset_index()

# Join the centroids back onto nyc_parts_gdf
nyc_parts_gdf = nyc_parts_gdf.merge(centroids, on=['county', 'part'])

# Create a new figure
fig, ax = plt.subplots()

# Create a map
m = Basemap(projection='mill', lon_0=0)
m.drawcoastlines()

# Loop over data points
for index, row in nyc_parts_gdf.iterrows():
    # Get the coordinates
    x, y = row['x_y'], row['y_y']

    # Convert coordinates to map projection
    x_m, y_m = m(x, y)

    # Draw the pie chart
    ax.pie([row['Car'], row['Public Transit'], row['Other']], radius=row['Total Commuters'], 
           center=(x_m, y_m), autopct='%1.1f%%', startangle=140)

plt.show()


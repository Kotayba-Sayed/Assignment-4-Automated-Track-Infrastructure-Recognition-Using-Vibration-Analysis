import pandas as pd
import plotly.graph_objects as go
import os

# Set file paths
files = {
    "Bridge": "converted_coordinates_Resultat_Bridge.csv",
    "RailJoint": "converted_coordinates_Resultat_RailJoint.csv",
    "Turnout": "converted_coordinates_Turnout.csv"
}

# Define marker styles with different colors and sizes
marker_styles = {
    "Bridge": {"color": "red", "size": 10},
    "RailJoint": {"color": "blue", "size": 8},
    "Turnout": {"color": "green", "size": 12}
}

# Load and process data
data_frames = []
for category, file_path in files.items():
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        if "Latitude" in df.columns and "Longitude" in df.columns:
            df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
            df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
            df = df[["Latitude", "Longitude"]].dropna()
            df["Category"] = category
            data_frames.append(df)
            print(f"[INFO] Loaded {category}: {len(df)} points.")
        else:
            print(f"[WARNING] {category} file missing 'Latitude' or 'Longitude' columns. Found: {df.columns.tolist()}")
    except Exception as e:
        print(f"[ERROR] Failed to load {category} from {file_path}: {e}")

# Combine all categories into one DataFrame
if not data_frames:
    raise ValueError("No data loaded. Please check CSV paths and content.")
data = pd.concat(data_frames, ignore_index=True)

# Debugging summaries
print("\n[SUMMARY]")
print(data["Category"].value_counts())
print(data.describe())
print(data.isnull().sum())

# Create map figure
fig = go.Figure()

for category, style in marker_styles.items():
    cat_data = data[data["Category"] == category]
    if cat_data.empty:
        print(f"[WARNING] No data for {category}, skipping...")
        continue

    fig.add_trace(go.Scattermapbox(
        lat=cat_data["Latitude"],
        lon=cat_data["Longitude"],
        mode="markers",
        marker=dict(color=style["color"], size=style["size"]),
        name=category
    ))

# Map layout
fig.update_layout(
    mapbox_style="open-street-map",
    title="Rail Infrastructure Map",
    width=1200,
    height=800,
    mapbox=dict(
        zoom=10,
        center=dict(lat=data["Latitude"].mean(), lon=data["Longitude"].mean())
    ),
    margin=dict(r=0, t=40, l=0, b=0)
)

# Save to HTML
output_file = "railway_infrastructure_map.html"
fig.write_html(output_file)
print(f"[SUCCESS] Map saved as {output_file}")

import webbrowser; webbrowser.open(output_file)

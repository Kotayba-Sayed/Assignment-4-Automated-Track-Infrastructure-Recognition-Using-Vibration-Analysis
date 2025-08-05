import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import tkinter as tk
from tkinter import filedialog
from geopy.distance import geodesic

# ----------------------------------------
# Load CSV files using file dialog (Tkinter)
# ----------------------------------------
root = tk.Tk()
root.withdraw()

file_keys = ["latitude", "longitude", "vibration1", "vibration2", "speed"]
files = {}

def load_file(label):
    path = filedialog.askopenfilename(title=f"Select {label} CSV File", filetypes=[("CSV Files", "*.csv")])
    if path:
        print(f"[INFO] {label.capitalize()} loaded: {os.path.basename(path)}")
    else:
        print(f"[WARNING] No file selected for {label}.")
    return path

for key in file_keys:
    files[key] = load_file(key)

# ----------------------------------------
# Load and preprocess CSVs into DataFrames
# ----------------------------------------
dataframes = {}
for key, path in files.items():
    if path:
        df = pd.read_csv(path, header=None, names=[key])
        df["timestamp"] = df.index
        dataframes[key] = df

# ----------------------------------------
# GPS DataFrame creation
# ----------------------------------------
if "latitude" in dataframes and "longitude" in dataframes:
    df_gps = pd.merge(dataframes["latitude"], dataframes["longitude"], on="timestamp")
    df_gps.rename(columns={"latitude": "Latitude", "longitude": "Longitude"}, inplace=True)
    df_gps["PointIndex"] = df_gps.index
else:
    df_gps = pd.DataFrame(columns=["Latitude", "Longitude", "PointIndex"])
    print("[ERROR] Latitude or Longitude data missing.")

# ----------------------------------------
# Load Infrastructure Coordinates
# ----------------------------------------
infra_files = {
    "Bridge": "converted_coordinates_Resultat_Bridge.csv",
    "RailJoint": "converted_coordinates_Resultat_RailJoint.csv",
    "Turnout": "converted_coordinates_Turnout.csv"
}

infra_points = []
for label, path in infra_files.items():
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df[["Latitude", "Longitude"]].dropna()
    df["Category"] = label
    infra_points.append(df)

df_infra = pd.concat(infra_points, ignore_index=True)

# ----------------------------------------
# Label GPS points based on proximity to infrastructure
# ----------------------------------------
def classify_gps_point(lat, lon, infra_df, threshold_meters=15):
    for _, row in infra_df.iterrows():
        distance = geodesic((lat, lon), (row["Latitude"], row["Longitude"])).meters
        if distance <= threshold_meters:
            return row["Category"]
    return "Other"

df_gps["Label"] = df_gps.apply(
    lambda row: classify_gps_point(row["Latitude"], row["Longitude"], df_infra), axis=1
)

print("\n[INFO] GPS Point Labels Distribution:")
print(df_gps["Label"].value_counts())

# ----------------------------------------
# Vibration segmentation
# ----------------------------------------
dt = 0.002
segment_sec = 10
segment_len = int(segment_sec / dt)

if "vibration1" in dataframes and "vibration2" in dataframes:
    df_vib = pd.merge(dataframes["vibration1"], dataframes["vibration2"], on="timestamp")
    n_segments = len(df_vib) // segment_len
    vib_segments = np.array([
        df_vib.iloc[i * segment_len: (i + 1) * segment_len][["vibration1", "vibration2"]].values
        for i in range(n_segments)
    ])
    print(f"[INFO] Vibration data segmented into {vib_segments.shape[0]} segments.")
else:
    vib_segments = np.array([])
    print("[ERROR] Missing vibration data for segmentation.")

# ----------------------------------------
# Label vibration segments using GPS labels
# ----------------------------------------
if not df_gps.empty and vib_segments.size > 0:
    gps_labels = df_gps["Label"].tolist()
    segment_labels = gps_labels[:len(vib_segments)]
    print("\n[INFO] Vibration Segment Labels Distribution:")
    print(pd.Series(segment_labels).value_counts())
else:
    segment_labels = []

# ----------------------------------------
# Plotly Map Creation
# ----------------------------------------
if not df_gps.empty:
    gps_fig = px.scatter_mapbox(
        df_gps,
        lat="Latitude",
        lon="Longitude",
        custom_data=["PointIndex", "Label"],
        color="Label",
        zoom=10,
        title="GPS Coordinates Map (Labelled)"
    )
    gps_fig.update_layout(mapbox_style="open-street-map", height=600)
else:
    gps_fig = go.Figure()
    gps_fig.update_layout(title="No GPS Data Available", height=600)
    
empty_vib_fig = go.Figure()
empty_vib_fig.update_layout(title="Vibration Signal", xaxis_title="Time (s)", yaxis_title="Acceleration")

# ----------------------------------------
# Dash Web App
# ----------------------------------------
app = dash.Dash(__name__)
app.title = "Vibration Viewer"

app.layout = html.Div([
    html.H2("Interactive GPS and Vibration Visualization (Labelled)"),
    html.Div([
        dcc.Graph(id="gps-map", figure=gps_fig)
    ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
    html.Div([
        dcc.Graph(id="vibration-plot", figure=empty_vib_fig)
    ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
])

# ----------------------------------------
# Callback: Update vibration graph when GPS point is clicked
# ----------------------------------------
@app.callback(
    Output('vibration-plot', 'figure'),
    Input('gps-map', 'clickData')
)
def update_vibration(clickData):
    if clickData is None or vib_segments.size == 0:
        return empty_vib_fig

    index = clickData['points'][0]['customdata'][0]
    label = clickData['points'][0]['customdata'][1]
    index = min(index, vib_segments.shape[0] - 1)
    segment = vib_segments[index]

    t = np.arange(segment_len) * dt
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=segment[:, 0], mode="lines", name="Vibration 1"))
    fig.add_trace(go.Scatter(x=t, y=segment[:, 1], mode="lines", name="Vibration 2"))
    fig.update_layout(
        title=f"Vibration Data for GPS Point {index} (Label: {label})",
        xaxis_title="Time (s)",
        yaxis_title="Acceleration"
    )
    return fig

# ----------------------------------------
# Run server
# ----------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8060, use_reloader=False)

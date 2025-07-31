import pandas as pd
import plotly.graph_objects as go

#############################################################
# Define file paths
files = {
    "Bridge": "converted_coordinates_Resultat_Bridge.csv",
    "RailJoint": "converted_coordinates_Resultat_RailJoint.csv",
    "Turnout": "converted_coordinates_Turnout.csv"
}
#############################################################

# Define marker styles with different colors and sizes
marker_styles = {
    "Bridge": {"color": "red", "size": 10},
    "RailJoint": {"color": "blue", "size": 8},
    "Turnout": {"color": "green", "size": 12}
}

# Load data
data_frames = []
for category, file in files.items():
    try:
        df = pd.read_csv(file, encoding="utf-8")  # Load CSV with UTF-8 encoding
        df.columns = df.columns.str.strip()  # Strip column names of extra spaces
        if "Latitude" in df.columns and "Longitude" in df.columns:
            df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")  # Convert Latitude to numeric
            df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")  # Convert Longitude to numeric
            df = df[["Latitude", "Longitude"]]  # Select necessary columns
            df["Category"] = category  # Add category column
            data_frames.append(df)
            print(f"Successfully loaded {category} data: {len(df)} rows")
        else:
            print(f"Warning: {category} file does not contain 'Latitude' and 'Longitude' columns.")
            print(f"Available columns: {df.columns.tolist()}")
    except Exception as e:
        print(f"Error loading {category}: {e}")

# Combine all data
if data_frames:
    data = pd.concat(data_frames, ignore_index=True)
else:
    raise ValueError("No valid data found. Check your CSV files.")

# Debugging: Check if all categories exist
print("Data counts per category:\n", data["Category"].value_counts())

# Check if latitude and longitude values are valid
print("Data summary:\n", data.describe())

# Check for missing values in the data
print("Missing values per column:\n", data.isnull().sum())

# Drop rows with missing Latitude or Longitude values (if any)
data = data.dropna(subset=["Latitude", "Longitude"])

# Add additional debugging to check data before plotting
for category in marker_styles.keys():
    category_data = data[data["Category"] == category]
    print(f"{category}: {len(category_data)} rows")
    if len(category_data) > 0:
        print(f"Sample coordinates for {category}:")
        print(category_data[["Latitude", "Longitude"]].head(2))
    else:
        print(f"WARNING: No data for {category}!")

# Create a Plotly map with custom size (width x height in pixels)
fig = go.Figure()

# Add each category as a separate trace
for category, style in marker_styles.items():
    category_data = data[data["Category"] == category]
    
    if len(category_data) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=category_data["Latitude"],
            lon=category_data["Longitude"],
            mode="markers",
            marker=dict(
                color=style["color"],
                size=style["size"]
            ),
            name=category
        ))
    else:
        print(f"Skipping {category} - no data available")

# Update layout for the map with custom size
fig.update_layout(
    mapbox_style="open-street-map",
    title="Railway Map with Bridges, Joints, and Turnouts",
    legend_title_text="Legend",
    width=1200,  # Set the width of the figure in pixels
    height=800,  # Set the height of the figure in pixels
    margin={"r": 0, "t": 50, "l": 50, "b": 0},
    mapbox=dict(
        zoom=10,
        center=dict(lat=data["Latitude"].mean(), lon=data["Longitude"].mean())  # Center map around the data
    )
)

# Check if we have any traces
if len(fig.data) == 0:
    print("WARNING: No valid traces were added to the figure. Check your data!")

# Show the figure
fig.show()


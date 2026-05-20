import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("T_out.dat")  
df["Datetime"] = pd.to_datetime("1981-01-01") + pd.to_timedelta(df["Datetime"], unit="D")
df = df.set_index("Datetime")

# Convert column names (depths) to float and sort
df.columns = df.columns.astype(float)
df = df.sort_index(axis=1)

#plot
plt.figure()

plt.pcolormesh(df.index, df.columns, df.T)

plt.colorbar(label="T [°C]")
plt.xlabel("")
plt.ylabel("Depth")

plt.xticks(rotation=45)
plt.savefig("heatmap.png", dpi=300, bbox_inches="tight") 
plt.show()

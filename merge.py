import pandas as pd

# Read both files
df1 = pd.read_csv('olx_mieszkania_wlkp.csv')
df2 = pd.read_csv('olx_mieszkania_wlkp2.csv')

# Concatenate (vertically stack)
merged_df = pd.concat([df1, df2], ignore_index=True)

# Save to new file
merged_df.to_csv('olx_mieszkania_wlkp_all.csv', index=False)
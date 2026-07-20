import os
import pandas as pd
from crewai.tools import tool

# Get active datasets paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH = os.path.join(BASE_DIR, "Datasets", "Clean Dataset.csv")

try:
    from backend.data_manager import clean_dataset
except ModuleNotFoundError:
    from data_manager import clean_dataset

def load_clean_df():
    path = CLEAN_PATH
    if not os.path.exists(path):
        path = "../Datasets/Clean Dataset.csv"
        if not os.path.exists(path):
            path = "e:/AI_Project/Laptop_Recomandation/Datasets/Clean Dataset.csv"
            if not os.path.exists(path):
                # Run cleaning if missing
                clean_dataset()
                path = CLEAN_PATH
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Error loading clean dataset in tools: {e}")
        return pd.DataFrame()

@tool("Get Laptop Dataset Statistics")
def get_dataset_stats_tool() -> str:
    """Useful to get an overview of the laptop database, including available brands,
    average prices, min/max price range, and distribution of RAM/Storage.
    Use this to see what kinds of laptops are in the database before querying."""
    df = load_clean_df()
    if df.empty:
        return "The laptop database is empty or could not be loaded."
        
    num_laptops = len(df)
    brands = df['Brand'].value_counts().to_dict()
    processors = df['Processor'].value_counts().to_dict()
    min_p, max_p = df['Price'].min(), df['Price'].max()
    avg_p = df['Price'].mean()
    
    stats_str = f"### Laptop Database Overview\n"
    stats_str += f"- **Total Laptops Available**: {num_laptops}\n"
    stats_str += f"- **Price Range**: {min_p:,} INR to {max_p:,} INR (Average: {avg_p:,.2f} INR)\n"
    stats_str += f"- **Available Brands**: {', '.join([f'{k} ({v})' for k, v in brands.items()])}\n"
    stats_str += f"- **Processors Available**: {', '.join([f'{k} ({v})' for k, v in processors.items()])}\n"
    stats_str += f"- **Operating Systems**: {df['OS'].value_counts().to_dict()}\n"
    return stats_str

@tool("Query Laptops Dataset")
def query_laptops_tool(
    brand: str = None, 
    max_price: float = None, 
    min_ram: float = None, 
    processor: str = None, 
    os_name: str = None,
    sort_by_rating: bool = True
) -> str:
    """
    Query the laptop database with specific search filters.
    All arguments are optional:
    - brand: Laptop brand (e.g. 'HP', 'Dell', 'Lenovo', 'Acer', 'ASUS', 'Apple')
    - max_price: Maximum price budget in INR (e.g. 60000)
    - min_ram: Minimum RAM in GB (e.g. 8, 16, 32)
    - processor: Core CPU type (e.g. 'Intel', 'AMD', 'Apple', 'Snapdragon')
    - os_name: Operating system (e.g. 'Windows', 'MacOS', 'Chrome OS')
    - sort_by_rating: If True, returns higher rated laptops first.
    Returns a markdown table of matching laptops up to the top 10 rows.
    """
    df = load_clean_df()
    if df.empty:
        return "The laptop database is empty or could not be loaded."
        
    filtered_df = df.copy()
    
    # Apply filters (case insensitive where appropriate)
    if brand:
        brand_clean = str(brand).strip().lower()
        filtered_df = filtered_df[filtered_df['Brand'].str.lower() == brand_clean]
        
    if max_price is not None:
        try:
            filtered_df = filtered_df[filtered_df['Price'] <= float(max_price)]
        except ValueError:
            pass
            
    if min_ram is not None:
        try:
            filtered_df = filtered_df[filtered_df['RAM'] >= float(min_ram)]
        except ValueError:
            pass
            
    if processor:
        proc_clean = str(processor).strip().lower()
        filtered_df = filtered_df[filtered_df['Processor'].str.lower() == proc_clean]
        
    if os_name:
        os_clean = str(os_name).strip().lower()
        # Handle 'mac' as 'macos'
        if os_clean == 'mac':
            os_clean = 'macos'
        filtered_df = filtered_df[filtered_df['OS'].str.lower() == os_clean]
        
    if filtered_df.empty:
        return "No laptops found matching these specific filters. Try raising the price budget or relaxation of criteria."
        
    # Sort
    if sort_by_rating:
        filtered_df = filtered_df.sort_values(by=['Rating', 'Price'], ascending=[False, True])
    else:
        filtered_df = filtered_df.sort_values(by='Price', ascending=True)
        
    # Take top 10
    top_matches = filtered_df.head(10)
    
    # Format as markdown table
    result_str = f"Found {len(filtered_df)} matching laptops. Showing top {len(top_matches)} matches:\n\n"
    
    headers = ["Brand", "Price (INR)", "RAM (GB)", "SSD Storage (GB)", "Processor", "OS", "Color", "Rating"]
    result_str += " | ".join(headers) + "\n"
    result_str += " | ".join(["---"] * len(headers)) + "\n"
    
    for _, row in top_matches.iterrows():
        row_vals = [
            str(row['Brand']),
            f"{int(row['Price']):,}",
            f"{int(row['RAM'])}GB",
            f"{int(row['SSD_Storage'])}GB",
            str(row['Processor']),
            str(row['OS']),
            str(row['Color']),
            f"{row['Rating']}/5.0"
        ]
        result_str += " | ".join(row_vals) + "\n"
        
    return result_str

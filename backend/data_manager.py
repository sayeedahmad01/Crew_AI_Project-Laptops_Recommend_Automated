import pandas as pd
import re
import os

# Define relative paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "Datasets")
RAW_PATH = os.path.join(DATASETS_DIR, "amazon_laptops.csv")
CLEAN_PATH = os.path.join(DATASETS_DIR, "Clean Dataset.csv")

def clean_dataset(raw_path: str = RAW_PATH, clean_path: str = CLEAN_PATH):
    if not os.path.exists(raw_path):
        # Fallback to checking active workspace parent if running in different relative path
        raw_path = "../Datasets/amazon_laptops.csv"
        clean_path = "../Datasets/Clean Dataset.csv"
        if not os.path.exists(raw_path):
            # Try absolute path
            raw_path = "e:/AI_Project/Laptop_Recomandation/Datasets/amazon_laptops.csv"
            clean_path = "e:/AI_Project/Laptop_Recomandation/Datasets/Clean Dataset.csv"
            if not os.path.exists(raw_path):
                return {"error": f"Raw data file not found at path {raw_path}"}
    
    # Read raw CSV
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        return {"error": f"Failed to read CSV: {str(e)}"}
    
    # Drop rows that are completely empty or have no brand and price
    df = df.dropna(subset=['Price', 'Brand'], how='all')
    
    # Clean Price
    def clean_price(val):
        if pd.isna(val):
            return None
        val_str = str(val).replace('"', '').replace(',', '').strip()
        # Find all digits
        nums = re.findall(r'\d+', val_str)
        if nums:
            return int(nums[0])
        return None

    df['Price'] = df['Price'].apply(clean_price)
    df = df.dropna(subset=['Price'])
    
    # Drop accessory rows (like laptop tables/bags under 10,000 INR)
    df = df[df['Price'] >= 10000]
    
    # Clean Brand
    def clean_brand(val):
        if pd.isna(val):
            return "Unknown"
        val_str = str(val).strip().capitalize()
        # Fix casing for specific brands
        val_lower = val_str.lower()
        if val_lower == 'hp':
            return 'HP'
        if val_lower == 'msi':
            return 'MSI'
        if val_lower == 'asus':
            return 'ASUS'
        if val_lower == 'bkn':
            return 'BKN'
        if val_lower == 'dell':
            return 'Dell'
        return val_str
    
    df['Brand'] = df['Brand'].apply(clean_brand)
    
    # Drop rows with obviously bad Brand names or unrelated products
    bad_brands = ['More', 'Related', 'Need', 'Highly', 'Table', 'Dellmodel', 'Cosmus', 'Ebook', 'Bkn', 'Unknown']
    df = df[~df['Brand'].isin(bad_brands)]
    
    # Clean RAM (Standardize as integer in GB)
    def clean_ram(val):
        if pd.isna(val):
            return 8 # Default RAM
        val_str = str(val).upper().strip()
        nums = re.findall(r'\d+', val_str)
        if nums:
            return int(nums[0])
        if 'DDR' in val_str or 'RAM' in val_str:
            return 16
        return 8

    df['RAM'] = df['RAM'].apply(clean_ram)
    
    # Clean SSD Storage (Standardize as integer in GB)
    def clean_storage(val):
        if pd.isna(val):
            return 512 # Default SSD
        val_str = str(val).strip()
        nums = re.findall(r'\d+', val_str)
        if nums:
            # SSD storage values are usually 128, 256, 512, 1024, etc.
            val_num = int(nums[0])
            # Handle float formats (e.g. 1.0 which means 1024GB, or 1024.0)
            if val_num <= 4: # e.g. 1.0, 2.0 -> TB to GB
                return val_num * 1024
            return val_num
        return 512
        
    df['SSD_Storage'] = df['SSD_Storage'].apply(clean_storage)
    
    # Clean Color
    df['Color'] = df['Color'].fillna('Unknown').apply(lambda x: str(x).strip().capitalize())
    
    # Clean Processor
    def clean_processor(val):
        if pd.isna(val):
            return 'Intel' # Default
        val_str = str(val).strip().lower()
        if 'intel' in val_str:
            return 'Intel'
        if 'amd' in val_str or 'ryzen' in val_str:
            return 'AMD'
        if 'apple' in val_str or 'm1' in val_str or 'm2' in val_str or 'm3' in val_str:
            return 'Apple'
        if 'snapdragon' in val_str:
            return 'Snapdragon'
        if 'celeron' in val_str:
            return 'Celeron'
        if 'mediatek' in val_str:
            return 'MediaTek'
        return str(val).strip().capitalize()
        
    df['Processor'] = df['Processor'].apply(clean_processor)
    
    # Clean OS
    def clean_os(val):
        if pd.isna(val):
            return 'Windows' # Default
        val_str = str(val).strip().lower()
        if 'windows' in val_str:
            return 'Windows'
        if 'mac' in val_str:
            return 'MacOS'
        if 'chrome' in val_str:
            return 'Chrome OS'
        if 'android' in val_str:
            return 'Android'
        if 'linux' in val_str:
            return 'Linux'
        return str(val).strip().capitalize()
        
    df['OS'] = df['OS'].apply(clean_os)
    
    # Clean Rating
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(4.0)
    
    # Save cleaned file
    try:
        os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        df.to_csv(clean_path, index=False)
    except Exception as e:
        return {"error": f"Failed to save cleaned CSV: {str(e)}"}
    
    # Read raw file to count rows
    try:
        raw_count = len(pd.read_csv(raw_path))
    except:
        raw_count = len(df)
        
    return {
        "status": "success",
        "raw_count": raw_count,
        "clean_count": len(df),
        "columns": list(df.columns),
        "brands": df['Brand'].value_counts().to_dict(),
        "avg_price": float(df['Price'].mean()),
        "avg_rating": float(df['Rating'].mean())
    }

def get_dataset_stats(clean_path: str = CLEAN_PATH):
    if not os.path.exists(clean_path):
        # Try fallbacks
        clean_path = "../Datasets/Clean Dataset.csv"
        if not os.path.exists(clean_path):
            clean_path = "e:/AI_Project/Laptop_Recomandation/Datasets/Clean Dataset.csv"
            if not os.path.exists(clean_path):
                # Clean on the fly
                res = clean_dataset()
                if "error" in res:
                    return {"error": "Clean dataset does not exist, and automatic cleaning failed."}
                
    try:
        df = pd.read_csv(clean_path)
    except Exception as e:
        return {"error": f"Failed to read clean CSV: {str(e)}"}
        
    return {
        "status": "success",
        "total_records": len(df),
        "brands": df['Brand'].value_counts().to_dict(),
        "processors": df['Processor'].value_counts().to_dict(),
        "os": df['OS'].value_counts().to_dict(),
        "min_price": int(df['Price'].min()),
        "max_price": int(df['Price'].max()),
        "avg_price": float(df['Price'].mean()),
        "avg_rating": float(df['Rating'].mean()),
        "ram_distribution": df['RAM'].value_counts().to_dict(),
        "storage_distribution": df['SSD_Storage'].value_counts().to_dict()
    }

def get_laptops_data(clean_path: str = CLEAN_PATH):
    if not os.path.exists(clean_path):
        clean_path = "../Datasets/Clean Dataset.csv"
        if not os.path.exists(clean_path):
            clean_path = "e:/AI_Project/Laptop_Recomandation/Datasets/Clean Dataset.csv"
            if not os.path.exists(clean_path):
                clean_dataset()
    try:
        df = pd.read_csv(clean_path)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error loading laptops: {str(e)}")
        return []

if __name__ == "__main__":
    # Test cleaning
    print("Testing data cleaning script...")
    res = clean_dataset()
    print("Clean Result:", res)
    if "error" not in res:
        print("Stats:", get_dataset_stats())

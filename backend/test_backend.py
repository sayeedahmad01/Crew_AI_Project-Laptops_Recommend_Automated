import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data_manager import clean_dataset, get_dataset_stats, get_laptops_data

def run_tests():
    print("=============================================")
    print("    RUNNING BACKEND COMPONENT VERIFICATION   ")
    print("=============================================")
    
    # Define absolute paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, "Datasets", "amazon_laptops.csv")
    clean_path = os.path.join(base_dir, "Datasets", "Clean Dataset.csv")
    
    # 1. Verify file paths
    print(f"\n1. Checking raw dataset presence:")
    print(f"   Raw path: {raw_path}")
    if not os.path.exists(raw_path):
        print(f"   [FAIL] Raw dataset file does not exist!")
        sys.exit(1)
    print(f"   [PASS] Raw dataset file found.")
    
    # 2. Test data cleaning execution
    print(f"\n2. Executing Data Specialist cleaning pipeline:")
    res = clean_dataset(raw_path, clean_path)
    if "error" in res:
        print(f"   [FAIL] Cleaning routine returned error: {res['error']}")
        sys.exit(1)
    
    print(f"   [PASS] Cleaning completed successfully.")
    print(f"          Raw rows count:  {res['raw_count']}")
    print(f"          Clean rows count: {res['clean_count']}")
    print(f"          Preserved brands: {list(res['brands'].keys())}")
    print(f"          Average Price:   Rs.{res['avg_price']:,.2f} INR")
    
    # 3. Test stats aggregator
    print(f"\n3. Aggregating database statistics:")
    stats = get_dataset_stats(clean_path)
    if "error" in stats:
        print(f"   [FAIL] Stats extractor failed: {stats['error']}")
        sys.exit(1)
        
    print(f"   [PASS] Statistics loaded successfully.")
    print(f"          Price range: Rs.{stats['min_price']:,} - Rs.{stats['max_price']:,} INR")
    print(f"          Average Rating: {stats['avg_rating']:.2f}/5.0 stars")
    
    # 4. Test list endpoint
    print(f"\n4. Retrieving laptop collection list:")
    laptops_list = get_laptops_data(clean_path)
    if not laptops_list:
        print(f"   [FAIL] Laptop database list is empty or could not be parsed!")
        sys.exit(1)
        
    print(f"   [PASS] Retrieved {len(laptops_list)} laptops from collection.")
    print(f"          Example laptop specification: {laptops_list[0]}")
    
    print("\n=============================================")
    print("     ALL COMPONENT VERIFICATIONS PASSED     ")
    print("=============================================")

if __name__ == "__main__":
    run_tests()

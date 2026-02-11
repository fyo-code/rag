import os
import glob

def setup():
    # 1. Look for the messy CSV file
    files = glob.glob("*RECLAMATII*.csv")

    if not files:
        print("❌ No 'RECLAMATII' CSV found in this folder.")
        print("👉 Please move the downloaded CSV file into this folder and run this script again.")
        return

    # 2. Rename it to standard name
    target = "reclamatii.csv"
    if target in files:
        print(f"✅ '{target}' already exists. Ready to go.")
    else:
        # Take the first match
        found = files[0]
        try:
            os.rename(found, target)
            print(f"✅ Renamed '{found}' \n   -> to '{target}'")
        except Exception as e:
            print(f"❌ Error renaming file: {e}")

    # 3. Check for API Key
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
            if 'GOOGLE_API_KEY=""' in content:
                print("⚠️  ACTION REQUIRED: Open .env and paste your Google API Key.")
            else:
                print("✅ .env file detected.")
    else:
        print("❌ .env file missing.")

if __name__ == "__main__":
    setup()

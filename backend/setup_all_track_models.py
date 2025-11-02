from universal_track_model import create_all_track_models

if __name__ == "__main__":
    print("Setting up AI models for all tracks...")
    create_all_track_models()
    print("All track models created successfully!")
    print("Now run: streamlit run dashboard.py")
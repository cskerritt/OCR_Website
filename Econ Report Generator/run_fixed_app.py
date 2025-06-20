#!/usr/bin/env python3
"""
Quick launcher for the FIXED Streamlit Economic Report Generator
"""

import subprocess
import sys
import os

def main():
    """Launch the FIXED Streamlit application"""
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_file = os.path.join(script_dir, "streamlit_economic_report_generator_fixed.py")
    
    # Check if the app file exists
    if not os.path.exists(app_file):
        print(f"Error: Could not find {app_file}")
        sys.exit(1)
    
    print("🚀 Starting FIXED Economic Report Generator...")
    print("📊 This will open in your default web browser")
    print("🔄 Press Ctrl+C to stop the application")
    print("✅ FIXED: Button issues resolved - no more page reloads!")
    print("-" * 60)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            app_file,
            "--browser.gatherUsageStats", "false",
            "--server.headless", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
        print("\n💡 Make sure you have installed the requirements:")
        print("   pip install -r requirements_streamlit.txt")
    except FileNotFoundError:
        print("❌ Error: Streamlit not found")
        print("\n💡 Install streamlit first:")
        print("   pip install streamlit")

if __name__ == "__main__":
    main()
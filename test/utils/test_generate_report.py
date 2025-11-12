import os
import json
from datetime import datetime
from verityngn.utils.html_utils import generate_html_report

def load_report_data(outputs_dir: str) -> dict:
    """Load the most recent report data from the outputs directory."""
    # Find all JSON files in the outputs directory
    json_files = []
    for root, _, files in os.walk(outputs_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    if not json_files:
        return {"error": "No report data found in outputs directory"}
    
    # Get the most recent JSON file
    latest_file = max(json_files, key=os.path.getmtime)
    
    # Load and return the report data
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define paths
    outputs_dir = os.path.join(current_dir, 'outputs')
    downloads_dir = os.path.join(current_dir, 'downloads')
    report_dir = os.path.join(current_dir, 'reports')
    
    # Create reports directory if it doesn't exist
    os.makedirs(report_dir, exist_ok=True)
    
    # Load the report data
    report_data = load_report_data(outputs_dir)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'report_{timestamp}.html'
    report_path = os.path.join(report_dir, report_filename)
    
    # Generate the report
    generate_html_report(report_data, report_path)
    print(f"Report generated successfully at: {report_path}")

if __name__ == '__main__':
    main() 
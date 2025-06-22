#!/usr/bin/env python3
"""
Life Expectancy Lookup Tool - Web Version

Flask web application for life expectancy lookups.
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import datetime, date
from expectancy_lookup import ExpectancyLookup, parse_date
import json

app = Flask(__name__)

# Global lookup instance
lookup = None

def init_lookup():
    """Initialize the lookup tool."""
    global lookup
    try:
        lookup = ExpectancyLookup()
        return True
    except Exception as e:
        print(f"Error initializing lookup: {e}")
        return False

@app.route('/')
def index():
    """Main page."""
    if not lookup:
        if not init_lookup():
            return "Error: Could not load data files", 500
    
    # Get available options
    options = lookup.get_available_options()
    return render_template('index.html', options=options)

@app.route('/lookup', methods=['POST'])
def perform_lookup():
    """Perform the expectancy lookup."""
    try:
        data = request.get_json()
        
        # Parse dates
        birth_date = parse_date(data['birth_date'])
        if not birth_date:
            return jsonify({'error': 'Invalid birth date format'}), 400
        
        injury_date = parse_date(data['injury_date'])
        if not injury_date:
            return jsonify({'error': 'Invalid injury date format'}), 400
        
        # Perform lookup
        results = lookup.comprehensive_lookup(
            birth_date, injury_date,
            data['gender_le'],
            data['race'],
            data['gender_wle'],
            data['education'],
            data.get('active_status', 'Initially Active')
        )
        
        # Format results for JSON
        results_data = {
            'input_data': {
                'birth_date': str(results['input_data']['birth_date']),
                'injury_date': str(results['input_data']['injury_date']),
                'age_at_injury': results['input_data']['age_at_injury'],
                'gender_le': results['input_data']['gender_le'],
                'race': results['input_data']['race'],
                'gender_wle': results['input_data']['gender_wle'],
                'education': results['input_data']['education'],
                'active_status': results['input_data']['active_status']
            },
            'results': results['results']
        }
        
        return jsonify(results_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/options')
def get_options():
    """Get available options for dropdowns."""
    if not lookup:
        return jsonify({'error': 'Lookup not initialized'}), 500
    
    options = lookup.get_available_options()
    return jsonify(options)

if __name__ == '__main__':
    print("Starting Life Expectancy Lookup Web Tool...")
    if init_lookup():
        print("Data loaded successfully!")
        print("Opening web browser at http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to load data files.")
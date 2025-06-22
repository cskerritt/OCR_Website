#!/usr/bin/env python3
"""
Life Expectancy Lookup Tool

This tool looks up:
1. Life Expectancy (LE) - based on gender, race, and age
2. Work Life Expectancy (WLE) - based on gender, education, age, and activity status
3. Years to Final Separation (YFS) - based on gender, education, age, and activity status

User enters date of birth and date of injury once, and all calculations are performed automatically.
"""

import pandas as pd
import os
from datetime import datetime, date
from typing import Tuple, Optional, Dict, Any

class ExpectancyLookup:
    def __init__(self):
        """Initialize the lookup tool with CSV data files."""
        # Define paths to CSV files
        self.le_path = "/Users/chrisskerritt/Dropbox/My Mac (chriss-MacBook-Pro.local)/Desktop/LE CSV.csv"
        self.wle_path = "/Users/chrisskerritt/Dropbox/My Mac (chriss-MacBook-Pro.local)/Desktop/WLE CSV.csv"
        self.yfs_path = "/Users/chrisskerritt/Dropbox/My Mac (chriss-MacBook-Pro.local)/Desktop/YFS CSV.csv"
        
        # Load data
        self.le_data = None
        self.wle_data = None
        self.yfs_data = None
        
        self._load_data()
    
    def _load_data(self):
        """Load all CSV data files."""
        try:
            print("Loading data files...")
            
            # Load Life Expectancy data
            self.le_data = pd.read_csv(self.le_path, encoding='utf-8-sig')
            # Clean column names by stripping whitespace
            self.le_data.columns = self.le_data.columns.str.strip()
            print(f"✓ Loaded Life Expectancy data: {len(self.le_data)} rows")
            
            # Load Work Life Expectancy data
            self.wle_data = pd.read_csv(self.wle_path, encoding='utf-8-sig')
            self.wle_data.columns = self.wle_data.columns.str.strip()
            print(f"✓ Loaded Work Life Expectancy data: {len(self.wle_data)} rows")
            
            # Load Years to Final Separation data
            self.yfs_data = pd.read_csv(self.yfs_path, encoding='utf-8-sig')
            self.yfs_data.columns = self.yfs_data.columns.str.strip()
            print(f"✓ Loaded Years to Final Separation data: {len(self.yfs_data)} rows")
            
            print("Data loading complete!\n")
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise
    
    def calculate_age(self, birth_date: date, reference_date: date) -> int:
        """Calculate age at reference date."""
        return reference_date.year - birth_date.year - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))
    
    def lookup_life_expectancy(self, gender: str, race: str, age: int) -> Optional[float]:
        """
        Look up life expectancy based on gender, race, and age.
        
        Args:
            gender: 'Males' or 'Females'
            race: Race category or 'N/A' for general population
            age: Age in years
            
        Returns:
            Life expectancy in years or None if not found
        """
        try:
            # Handle race filtering - 'N/A' or 'General' should match NaN values
            if race in ['N/A', 'General', 'General Population']:
                race_filter = pd.isna(self.le_data['Race'])
            else:
                race_filter = (self.le_data['Race'] == race)
            
            # Filter data
            filtered = self.le_data[
                (self.le_data['Gender'] == gender) & 
                race_filter &
                (self.le_data['Age Low'] <= age) & 
                (self.le_data['Age High'] >= age)
            ]
            
            if not filtered.empty:
                return float(filtered.iloc[0]['Expectation of Life'])
            else:
                return None
                
        except Exception as e:
            print(f"Error looking up life expectancy: {str(e)}")
            return None
    
    def lookup_work_life_expectancy(self, gender: str, education: str, age: int, active_status: str = "Initially Active") -> Optional[float]:
        """
        Look up work life expectancy (median value).
        
        Args:
            gender: 'Men' or 'Women'
            education: Education level
            age: Age in years
            active_status: 'Initially Active' or other status
            
        Returns:
            Work life expectancy median in years or None if not found
        """
        try:
            # Filter data
            filtered = self.wle_data[
                (self.wle_data['Gender'] == gender) & 
                (self.wle_data['Education Level'] == education) &
                (self.wle_data['Age'] == age) &
                (self.wle_data['Active?'] == active_status)
            ]
            
            if not filtered.empty:
                return float(filtered.iloc[0]['Median'])
            else:
                return None
                
        except Exception as e:
            print(f"Error looking up work life expectancy: {str(e)}")
            return None
    
    def lookup_years_to_final_separation(self, gender: str, education: str, age: int, active_status: str = "Initially Active") -> Optional[float]:
        """
        Look up years to final separation (median value).
        
        Args:
            gender: 'Men' or 'Women'
            education: Education level
            age: Age in years
            active_status: 'Initially Active' or other status
            
        Returns:
            Years to final separation median or None if not found
        """
        try:
            # Filter data
            filtered = self.yfs_data[
                (self.yfs_data['Gender'] == gender) & 
                (self.yfs_data['Education Level'] == education) &
                (self.yfs_data['Age'] == age) &
                (self.yfs_data['Active ?'] == active_status)
            ]
            
            if not filtered.empty:
                return float(filtered.iloc[0]['YFS median'])
            else:
                return None
                
        except Exception as e:
            print(f"Error looking up years to final separation: {str(e)}")
            return None
    
    def get_available_options(self) -> Dict[str, list]:
        """Get available options for each parameter."""
        try:
            # Helper function to safely sort mixed types
            def safe_sort(items):
                # Convert to strings, remove NaN values, then sort
                clean_items = [str(item) for item in items if pd.notna(item)]
                return sorted(list(set(clean_items)))
            
            # Special handling for race - add 'General Population' for NaN values
            race_options = safe_sort(self.le_data['Race'].unique())
            if any(pd.isna(self.le_data['Race'])):
                race_options = ['General Population'] + race_options
            
            options = {
                'genders_le': safe_sort(self.le_data['Gender'].unique()),
                'races': race_options,
                'genders_wle': safe_sort(self.wle_data['Gender'].unique()),
                'education_levels': safe_sort(self.wle_data['Education Level'].unique()),
                'active_statuses_wle': safe_sort(self.wle_data['Active?'].unique()),
                'active_statuses_yfs': safe_sort(self.yfs_data['Active ?'].unique())
            }
            return options
        except Exception as e:
            print(f"Error getting available options: {str(e)}")
            return {}
    
    def comprehensive_lookup(self, birth_date: date, injury_date: date, 
                           gender_le: str, race: str, gender_wle: str, 
                           education: str, active_status: str = "Initially Active") -> Dict[str, Any]:
        """
        Perform comprehensive lookup with single data entry.
        
        Args:
            birth_date: Date of birth
            injury_date: Date of injury
            gender_le: Gender for LE lookup ('Males'/'Females')
            race: Race for LE lookup
            gender_wle: Gender for WLE/YFS lookup ('Men'/'Women') 
            education: Education level
            active_status: Work activity status
            
        Returns:
            Dictionary with all results
        """
        # Calculate age at injury
        age_at_injury = self.calculate_age(birth_date, injury_date)
        
        # Perform all lookups
        le = self.lookup_life_expectancy(gender_le, race, age_at_injury)
        wle = self.lookup_work_life_expectancy(gender_wle, education, age_at_injury, active_status)
        yfs = self.lookup_years_to_final_separation(gender_wle, education, age_at_injury, active_status)
        
        return {
            'input_data': {
                'birth_date': birth_date,
                'injury_date': injury_date,
                'age_at_injury': age_at_injury,
                'gender_le': gender_le,
                'race': race,
                'gender_wle': gender_wle,
                'education': education,
                'active_status': active_status
            },
            'results': {
                'life_expectancy': le,
                'work_life_expectancy': wle,
                'years_to_final_separation': yfs
            }
        }

def parse_date(date_str: str) -> Optional[date]:
    """Parse date string in various formats."""
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def print_results(results: Dict[str, Any]):
    """Print formatted results."""
    print("\n" + "="*60)
    print("EXPECTANCY LOOKUP RESULTS")
    print("="*60)
    
    input_data = results['input_data']
    lookup_results = results['results']
    
    print(f"\nINPUT INFORMATION:")
    print(f"Date of Birth: {input_data['birth_date']}")
    print(f"Date of Injury: {input_data['injury_date']}")
    print(f"Age at Injury: {input_data['age_at_injury']} years")
    print(f"Gender (LE): {input_data['gender_le']}")
    print(f"Race: {input_data['race']}")
    print(f"Gender (WLE/YFS): {input_data['gender_wle']}")
    print(f"Education: {input_data['education']}")
    print(f"Work Status: {input_data['active_status']}")
    
    print(f"\nRESULTS:")
    
    le = lookup_results['life_expectancy']
    if le is not None:
        print(f"Life Expectancy: {le:.2f} years")
    else:
        print("Life Expectancy: Not found")
    
    wle = lookup_results['work_life_expectancy']
    if wle is not None:
        print(f"Work Life Expectancy: {wle:.2f} years")
    else:
        print("Work Life Expectancy: Not found")
    
    yfs = lookup_results['years_to_final_separation']
    if yfs is not None:
        print(f"Years to Final Separation: {yfs:.2f} years")
    else:
        print("Years to Final Separation: Not found")
    
    print("="*60)

def main():
    """Main interactive function."""
    print("Life Expectancy Lookup Tool")
    print("="*50)
    
    # Initialize lookup tool
    try:
        lookup = ExpectancyLookup()
    except Exception as e:
        print(f"Failed to initialize lookup tool: {str(e)}")
        return
    
    # Get available options
    options = lookup.get_available_options()
    
    while True:
        print("\nEnter the following information:")
        
        # Get dates
        birth_date_str = input("Date of Birth (YYYY-MM-DD or MM/DD/YYYY): ").strip()
        birth_date = parse_date(birth_date_str)
        if not birth_date:
            print("Invalid date format. Please try again.")
            continue
            
        injury_date_str = input("Date of Injury (YYYY-MM-DD or MM/DD/YYYY): ").strip()
        injury_date = parse_date(injury_date_str)
        if not injury_date:
            print("Invalid date format. Please try again.")
            continue
        
        # Show available options and get selections
        print(f"\nAvailable Genders for Life Expectancy: {options['genders_le']}")
        gender_le = input("Select Gender for LE (Males/Females): ").strip()
        
        print(f"\nAvailable Races: {options['races']}")
        race = input("Select Race: ").strip()
        
        print(f"\nAvailable Genders for Work Life Expectancy: {options['genders_wle']}")
        gender_wle = input("Select Gender for WLE/YFS (Men/Women): ").strip()
        
        print(f"\nAvailable Education Levels: {options['education_levels']}")
        education = input("Select Education Level: ").strip()
        
        print(f"\nAvailable Work Statuses: {options['active_statuses_wle']}")
        active_status = input("Select Work Status (or press Enter for 'Initially Active'): ").strip()
        if not active_status:
            active_status = "Initially Active"
        
        # Perform lookup
        results = lookup.comprehensive_lookup(
            birth_date, injury_date, gender_le, race, 
            gender_wle, education, active_status
        )
        
        # Display results
        print_results(results)
        
        # Ask if user wants to continue
        continue_choice = input("\nWould you like to perform another lookup? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            break
    
    print("\nThank you for using the Life Expectancy Lookup Tool!")

if __name__ == "__main__":
    main()
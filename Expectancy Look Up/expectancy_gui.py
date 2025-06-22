#!/usr/bin/env python3
"""
Life Expectancy Lookup Tool - GUI Version

Simple GUI interface for looking up life expectancy data.
Requires tkinter (usually included with Python).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import pandas as pd
from expectancy_lookup import ExpectancyLookup, parse_date

class ExpectancyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Life Expectancy Lookup Tool")
        self.root.geometry("600x700")
        
        # Initialize lookup engine
        try:
            self.lookup = ExpectancyLookup()
            self.options = self.lookup.get_available_options()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            return
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Life Expectancy Lookup Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input Information", padding="10")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Date inputs
        ttk.Label(input_frame, text="Date of Birth:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.birth_date_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.birth_date_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(input_frame, text="(YYYY-MM-DD or MM/DD/YYYY)").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(input_frame, text="Date of Injury:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.injury_date_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.injury_date_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(input_frame, text="(YYYY-MM-DD or MM/DD/YYYY)").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # Gender for LE
        ttk.Label(input_frame, text="Gender (for LE):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.gender_le_var = tk.StringVar()
        gender_le_combo = ttk.Combobox(input_frame, textvariable=self.gender_le_var, 
                                      values=self.options.get('genders_le', []), state="readonly")
        gender_le_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Race
        ttk.Label(input_frame, text="Race:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.race_var = tk.StringVar()
        race_combo = ttk.Combobox(input_frame, textvariable=self.race_var, 
                                 values=self.options.get('races', []), state="readonly")
        race_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Gender for WLE/YFS
        ttk.Label(input_frame, text="Gender (for WLE/YFS):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.gender_wle_var = tk.StringVar()
        gender_wle_combo = ttk.Combobox(input_frame, textvariable=self.gender_wle_var, 
                                       values=self.options.get('genders_wle', []), state="readonly")
        gender_wle_combo.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Education
        ttk.Label(input_frame, text="Education Level:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.education_var = tk.StringVar()
        education_combo = ttk.Combobox(input_frame, textvariable=self.education_var, 
                                      values=self.options.get('education_levels', []), state="readonly")
        education_combo.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Work status
        ttk.Label(input_frame, text="Work Status:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.active_status_var = tk.StringVar(value="Initially Active")
        active_status_combo = ttk.Combobox(input_frame, textvariable=self.active_status_var, 
                                          values=self.options.get('active_statuses_wle', []), state="readonly")
        active_status_combo.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Lookup button
        lookup_btn = ttk.Button(main_frame, text="Perform Lookup", command=self.perform_lookup)
        lookup_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Results text area
        self.results_text = tk.Text(results_frame, height=15, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Clear button
        clear_btn = ttk.Button(main_frame, text="Clear Results", command=self.clear_results)
        clear_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def perform_lookup(self):
        """Perform the expectancy lookup."""
        try:
            # Validate inputs
            birth_date = parse_date(self.birth_date_var.get().strip())
            if not birth_date:
                messagebox.showerror("Error", "Invalid birth date format")
                return
            
            injury_date = parse_date(self.injury_date_var.get().strip())
            if not injury_date:
                messagebox.showerror("Error", "Invalid injury date format")
                return
            
            if not all([self.gender_le_var.get(), self.race_var.get(), 
                       self.gender_wle_var.get(), self.education_var.get()]):
                messagebox.showerror("Error", "Please fill in all required fields")
                return
            
            # Perform lookup
            results = self.lookup.comprehensive_lookup(
                birth_date, injury_date,
                self.gender_le_var.get(),
                self.race_var.get(),
                self.gender_wle_var.get(),
                self.education_var.get(),
                self.active_status_var.get()
            )
            
            # Display results
            self.display_results(results)
            
        except Exception as e:
            messagebox.showerror("Error", f"Lookup failed: {str(e)}")
    
    def display_results(self, results):
        """Display results in the text area."""
        self.results_text.delete(1.0, tk.END)
        
        input_data = results['input_data']
        lookup_results = results['results']
        
        output = "EXPECTANCY LOOKUP RESULTS\n"
        output += "=" * 60 + "\n\n"
        
        output += "INPUT INFORMATION:\n"
        output += f"Date of Birth: {input_data['birth_date']}\n"
        output += f"Date of Injury: {input_data['injury_date']}\n"
        output += f"Age at Injury: {input_data['age_at_injury']} years\n"
        output += f"Gender (LE): {input_data['gender_le']}\n"
        output += f"Race: {input_data['race']}\n"
        output += f"Gender (WLE/YFS): {input_data['gender_wle']}\n"
        output += f"Education: {input_data['education']}\n"
        output += f"Work Status: {input_data['active_status']}\n\n"
        
        output += "RESULTS:\n"
        
        le = lookup_results['life_expectancy']
        if le is not None:
            output += f"Life Expectancy: {le:.2f} years\n"
        else:
            output += "Life Expectancy: Not found\n"
        
        wle = lookup_results['work_life_expectancy']
        if wle is not None:
            output += f"Work Life Expectancy: {wle:.2f} years\n"
        else:
            output += "Work Life Expectancy: Not found\n"
        
        yfs = lookup_results['years_to_final_separation']
        if yfs is not None:
            output += f"Years to Final Separation: {yfs:.2f} years\n"
        else:
            output += "Years to Final Separation: Not found\n"
        
        output += "\n" + "=" * 60
        
        self.results_text.insert(1.0, output)
    
    def clear_results(self):
        """Clear the results text area."""
        self.results_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = ExpectancyGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
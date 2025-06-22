# Life Expectancy Lookup Tool

A comprehensive tool for looking up life expectancy, work life expectancy, and years to final separation based on demographic data.

## Features

- **Single Data Entry**: Enter date of birth and date of injury once, and all calculations are performed automatically
- **Three Types of Lookups**:
  - Life Expectancy (LE) - based on gender, race, and age
  - Work Life Expectancy (WLE) - based on gender, education, age, and activity status
  - Years to Final Separation (YFS) - based on gender, education, age, and activity status
- **Easy-to-Use Interface**: Available in both command-line and GUI versions
- **Flexible Date Input**: Accepts multiple date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)

## Files

- `expectancy_lookup.py` - Main lookup engine and command-line interface
- `expectancy_gui.py` - GUI version for easier use
- `README.md` - This documentation file

## Requirements

- Python 3.6+
- pandas
- tkinter (for GUI version, usually included with Python)

## Installation

1. Ensure you have Python 3.6+ installed
2. Install required packages:
   ```bash
   pip install pandas
   ```

## Usage

### Command Line Version

Run the command-line interface:
```bash
python3 expectancy_lookup.py
```

Follow the prompts to enter:
- Date of birth
- Date of injury
- Gender (for life expectancy lookup)
- Race
- Gender (for work life expectancy lookup) 
- Education level
- Work activity status

### GUI Version

Run the graphical interface:
```bash
python3 expectancy_gui.py
```

Fill in the form fields and click "Perform Lookup" to get results.

## Data Sources

The tool uses three CSV files:
- `LE CSV.csv` - Life expectancy data by gender, race, and age
- `WLE CSV.csv` - Work life expectancy data by gender, education, age, and activity status
- `YFS CSV.csv` - Years to final separation data by gender, education, age, and activity status

## Example Usage

### Input
- Date of Birth: 1980-05-15
- Date of Injury: 2023-10-01
- Gender (LE): Males
- Race: N/A
- Gender (WLE/YFS): Men
- Education: All Education Levels
- Work Status: Initially Active

### Output
- Age at Injury: 43 years
- Life Expectancy: [varies by data]
- Work Life Expectancy: 19.64 years
- Years to Final Separation: 23.79 years

## Troubleshooting

- **Data Loading Errors**: Ensure the CSV files are in the correct locations
- **Date Format Errors**: Use YYYY-MM-DD or MM/DD/YYYY format
- **No Results Found**: Check that the demographic parameters match available data options

## Support

For issues or questions, check that:
1. All CSV files are accessible at the specified paths
2. Input data matches available options in the CSV files
3. Date formats are correct
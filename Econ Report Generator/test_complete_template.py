#!/usr/bin/env python3
"""
Test script for the complete professional template
This will generate a sample report to verify all functionality works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date
import pandas as pd
from complete_professional_template import create_complete_professional_report

# Define a simple data structure that matches what the template expects
class TestData:
    def __init__(self):
        # Sample case data matching the Streamlit app
        self.client_name = 'FIRST LAST'
        self.date_of_birth = date(1980, 3, 15)
        self.date_of_injury = date(2023, 6, 1)
        self.date_of_report = date(2025, 6, 20)
        self.gender = 'Male'
        self.education = 'Bachelor\'s Degree in Mechanical Engineering'
        self.marital_status = 'Married'
        self.residence_state = 'New Jersey'
        self.residence_county = 'Bergen County'
        self.msa = 'New York-Newark-Jersey City, NY-NJ-PA'
        self.pre_injury_occupation = 'Mechanical Engineer - Senior Level'
        self.pre_injury_annual_income = 85000.0
        self.pre_injury_hourly_rate = 40.87
        self.employer = 'ABC Manufacturing Corporation'
        self.years_with_employer = 8.5
        self.injury_description = 'Work-related back injury sustained while lifting heavy machinery components during routine maintenance. Resulted in herniated discs at L4-L5 and chronic pain syndrome limiting physical capacity and mobility.'
        self.body_parts_injured = 'Lower lumbar spine, specifically L4-L5 vertebrae with disc herniation'
        self.medical_treatment = 'Emergency department treatment, comprehensive MRI and CT diagnostics, intensive physical therapy (6 months), pain management program, epidural steroid injections, ongoing medical monitoring'
        self.current_medical_status = 'Maximum medical improvement achieved. Permanent work restrictions: no lifting >20 lbs, limited standing/walking periods, cannot perform fieldwork requiring physical activity'
        self.life_expectancy = 78.5
        self.work_life_expectancy = 42.0
        self.years_to_final_separation = 0.0
        self.wage_growth_rate = 0.032
        self.discount_rate = 0.045
        self.unemployment_rate = 0.038
        self.tax_rate = 0.22
        self.fringe_benefits_rate = 0.28
        self.personal_consumption_rate = 0.0
        self.post_injury_capacity = 'Limited to sedentary desk work only due to permanent lifting restrictions and chronic pain. Cannot perform previous engineering duties requiring site visits, equipment handling, or physical inspection activities.'
        self.post_injury_occupation = 'Desk-based engineering consultant (limited availability)'
        self.post_injury_annual_income = 40000.0
        self.labor_market_reduction = 0.65
        self.life_care_plan_cost = 150000.0
        self.household_services_cost = 95000.0

def create_test_dataframes():
    """Create sample dataframes for testing"""
    
    # Sample past losses data
    past_data = [
        {'Year': 2023, 'Age': 43.0, 'Portion': 58.3, 'Pre-Injury Earnings': 85000.00, 'Post-Injury Earnings': 20000.00, 'Nominal Loss': 37883.56, 'AEF': 42.45, 'Adjusted Loss': 16083.89, 'Present Value': 16083.89},
        {'Year': 2024, 'Age': 44.0, 'Portion': 100.0, 'Pre-Injury Earnings': 87720.00, 'Post-Injury Earnings': 41280.00, 'Nominal Loss': 46440.00, 'AEF': 42.45, 'Adjusted Loss': 19706.58, 'Present Value': 18859.31},
        {'Year': 2025, 'Age': 45.0, 'Portion': 46.8, 'Pre-Injury Earnings': 90530.64, 'Post-Injury Earnings': 42597.12, 'Nominal Loss': 22408.95, 'AEF': 42.45, 'Adjusted Loss': 9512.60, 'Present Value': 8679.30}
    ]
    
    # Sample future losses data  
    future_data = [
        {'Year': 2025, 'Age': 45.0, 'Portion': 53.2, 'Pre-Injury Earnings': 90530.64, 'Post-Injury Earnings': 42597.12, 'Nominal Loss': 25459.91, 'AEF': 42.45, 'Adjusted Loss': 10807.94, 'Present Value': 9863.39},
        {'Year': 2026, 'Age': 46.0, 'Portion': 100.0, 'Pre-Injury Earnings': 93467.64, 'Post-Injury Earnings': 43960.10, 'Nominal Loss': 49507.54, 'AEF': 42.45, 'Adjusted Loss': 21017.45, 'Present Value': 18153.04},
        {'Year': 2027, 'Age': 47.0, 'Portion': 100.0, 'Pre-Injury Earnings': 96459.01, 'Post-Injury Earnings': 45367.22, 'Nominal Loss': 51091.79, 'AEF': 42.45, 'Adjusted Loss': 21713.45, 'Present Value': 17921.71}
    ]
    
    past_df = pd.DataFrame(past_data)
    future_df = pd.DataFrame(future_data)
    
    return past_df, future_df

def create_test_aef_result():
    """Create sample AEF result for testing"""
    return {
        'worklife_factor': 0.9524,
        'unemployment_factor': 0.962,
        'tax_factor': 0.78,
        'personal_consumption_factor': 1.0,
        'final_aef': 0.4245,
        'factors': [
            ('Worklife Factor', 0.9524, 0.9524),
            ('Unemployment Factor', 0.962, 0.9162),
            ('Tax Factor', 0.78, 0.7146),
            ('Personal Consumption Factor', 1.0, 0.7146),
            ('Final AEF', 0.4245, 0.4245)
        ]
    }

def main():
    """Test the complete professional template"""
    print("🧪 Testing Complete Professional Template...")
    
    try:
        # Create test data
        data = TestData()
        past_df, future_df = create_test_dataframes()
        aef_result = create_test_aef_result()
        retirement_date = date(2065, 6, 1)
        death_date = date(2071, 3, 15)
        
        print("✅ Test data created successfully")
        
        # Generate the report
        print("📝 Generating professional report...")
        doc_bytes = create_complete_professional_report(
            data, past_df, future_df, aef_result, retirement_date, death_date
        )
        
        if doc_bytes:
            # Save the test report
            output_file = "test_professional_report.docx"
            with open(output_file, 'wb') as f:
                f.write(doc_bytes)
            
            print(f"✅ Professional report generated successfully!")
            print(f"📄 Report saved as: {output_file}")
            print(f"📊 Report size: {len(doc_bytes):,} bytes")
            
            # Calculate totals for verification
            past_total = past_df['Present Value'].sum()
            future_total = future_df['Present Value'].sum()
            total_economic_loss = past_total + future_total + data.life_care_plan_cost + data.household_services_cost
            
            print(f"\n📈 Economic Loss Summary:")
            print(f"   Past Losses: ${past_total:,.2f}")
            print(f"   Future Losses: ${future_total:,.2f}")
            print(f"   Life Care Plan: ${data.life_care_plan_cost:,.2f}")
            print(f"   Household Services: ${data.household_services_cost:,.2f}")
            print(f"   TOTAL ECONOMIC LOSS: ${total_economic_loss:,.2f}")
            
        else:
            print("❌ Failed to generate report")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 All tests completed successfully!")
    print("🚀 The complete professional template is ready for use!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
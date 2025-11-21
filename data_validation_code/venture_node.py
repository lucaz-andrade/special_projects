#%% 

import pandas as pd 

# Import data
venture_node = pd.read_csv("/Users/strider/Zamp/GitHub/special_projects/data_validation_code/ZampTransactions (2).csv")


#%%
# Renaming headers
venture_node = venture_node.rename(columns={
    'marketplace': 'transactionMarketplace',
    'wholesale': 'transactionPurpose'
})
#%%
# Creating the missing columns

venture_node['shipFromAddress1'] = ''
venture_node['shipFromAddress2'] = ''
venture_node['shipFromCity'] = ''
venture_node['shipFromState'] = ''
venture_node['shipFromZip'] = ''
venture_node['shipFromCountry'] = ''
venture_node['lineItemId'] = venture_node['transactionId']
venture_node['lineItemAmount'] = venture_node['transactionSubtotal']
venture_node['lineItemQuantity'] = 1
venture_node['lineItemDiscount'] = 0
venture_node['lineItemShippingHandling'] = 0
venture_node['lineItemProductName'] = ''
venture_node['lineItemProductTaxCode'] = ''
venture_node['transactionRecalculateTax'] = 'FALSE'
venture_node['transactionEntity'] = ''
venture_node['transactionMarketplace'] = ''
venture_node['transactionPurpose'] = ''
venture_node['transactionParentId'] = ''

# %% Adjusting data types
venture_node['transactionDate'] = pd.to_datetime(venture_node['transactionDate']).dt.strftime('%Y-%m-%d')
venture_node['transactionId'] = venture_node['transactionId'].astype(str)
venture_node['lineItemId'] = venture_node['lineItemId'].astype(str)
venture_node['transactionSubtotal'] = venture_node['transactionSubtotal'].astype(float)
venture_node['transactionTax'] = venture_node['transactionTax'].astype(float)
venture_node['transactionShippingHandling'] = venture_node['transactionShippingHandling'].astype(float)
venture_node['transactionDiscount'] = venture_node['transactionDiscount'].astype(float)
venture_node['transactionTotal'] = venture_node['transactionTotal'].astype(float)
venture_node['transactionParentId'] = venture_node['transactionParentId'].astype(str)
venture_node['transactionMarketplace'] = venture_node['transactionMarketplace'].astype(str)
venture_node['transactionPurpose'] = venture_node['transactionPurpose'].astype(str)
venture_node['transactionEntity'] = venture_node['transactionEntity'].astype(str)
venture_node['transactionRecalculateTax'] = venture_node['transactionRecalculateTax'].astype(str)
# #%%
# # Display basic info about the dataset
# print("Dataset Info:")
# print(venture_node.info())
# print("\nFirst few rows:")
# print(venture_node.head())
# #%%
# # Check for missing values
# print("\nMissing values:")
# print(venture_node.isnull().sum())
# #%%
# # Basic statistics
# print("\nBasic Statistics:")
# print(venture_node.describe())

# # Check for duplicate rows
# print("\nDuplicate rows:")
# print(venture_node.duplicated().sum())

# # Check data types
# print("\nData Types:")
# print(venture_node.dtypes)

# # Check unique values in key columns
# print("\nUnique values in key columns:")
# for col in venture_node.columns:
#     print(f"{col}: {venture_node[col].nunique()} unique values")

# # Check for any obvious data quality issues
# print("\nData Quality Check:")
# print(f"Total rows: {len(venture_node)}")
# print(f"Total columns: {len(venture_node.columns)}")
# #print(f"Memory usage: {venture_node.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

# # Display column names for reference
# print("\nColumn Names:")
# for i, col in enumerate(venture_node.columns):
#     print(f"{i+1}. {col}")

# # Display first few rows to see actual data
# print("\nFirst 5 rows of actual data:")
# print(venture_node.head())

# # Display data types and check for any obvious issues
# print("\nData Types and Sample Values:")
# for col in venture_node.columns:
#     print(f"{col}: {venture_node[col].dtype}")
#     print(f"  Sample values: {venture_node[col].head().tolist()}")
#     print(f"  Unique values count: {venture_node[col].nunique()}")
#     print()

# # Check for any obvious data quality issues
# print("\nData Quality Issues:")
# for col in venture_node.columns:
#     missing_pct = (venture_node[col].isnull().sum() / len(venture_node)) * 100
#     if missing_pct > 0:
#         print(f"{col}: {missing_pct:.2f}% missing values")
        
# # Check for potential data type issues
# print("\nPotential Data Type Issues:")
# for col in venture_node.columns:
#     if venture_node[col].dtype == 'object':
#         # Check if it's likely a date column
#         if 'date' in col.lower() or 'time' in col.lower():
#             try:
#                 pd.to_datetime(venture_node[col])
#                 print(f"{col}: Likely date column")
#             except:
#                 print(f"{col}: Object column that might contain dates")
#         else:
#             # Check if it's likely numeric but stored as object
#             try:
#                 pd.to_numeric(venture_node[col].dropna())
#                 print(f"{col}: Object column that might contain numeric data")
#             except:
#                 pass
# Check total calculus
print("\n=== TRANSACTION TOTAL VALIDATION ===")
calculated_total = venture_node['transactionSubtotal'] + venture_node['transactionShippingHandling'] + venture_node['transactionTax'] - venture_node['transactionDiscount']
discrepancy = venture_node['transactionTotal'] - calculated_total

# Allow for small floating point differences (0.01)
has_discrepancy = abs(discrepancy) > 0.01
num_discrepancies = has_discrepancy.sum()

# if num_discrepancies > 0:
#     print(f"⚠️  Found {num_discrepancies} transactions with total calculation issues")
#     print(f"\nSample of problematic transactions:")
#     problematic = venture_node[has_discrepancy][['transactionId', 'transactionSubtotal', 'transactionShippingHandling', 'transactionTax', 'transactionTotal']].head(10)
#     problematic['calculated_total'] = calculated_total[has_discrepancy].head(10)
#     problematic['difference'] = discrepancy[has_discrepancy].head(10)
#     print(problematic.to_string())
#     print(f"\nMax discrepancy: ${abs(discrepancy).max():.2f}")
#     print(f"Total discrepancy sum: ${discrepancy.sum():.2f}")
# else:
#     print("✓ All transaction totals match calculated values (subtotal + shipping + tax)")
# # Summary of findings
# print("\n=== DATA VALIDATION SUMMARY ===")
# print(f"Total records: {len(venture_node)}")
# print(f"Total columns: {len(venture_node.columns)}")
# #print(f"Memory usage: {venture_node.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
# print("\nColumn analysis complete. Review the output above for any data quality issues.")

# %%
missing_zip_code = venture_node[venture_node['shipToZip'].isnull() | (venture_node['shipToZip'] == '')]
zero_dolar_orders = venture_node[(venture_node['transactionTotal']== 0) & (venture_node['transactionTax'] == 0) 
                                    &(venture_node['transactionSubtotal'] == 0 ) & (venture_node['shipToZip'].notna())]
discrepancy_orders = venture_node[has_discrepancy].copy()
#%%
tax_only = venture_node[(venture_node['transactionTax'] >= 1) & ((venture_node['transactionTotal'] == 0) | (venture_node['transactionSubtotal'] == 0))]
# %%
zamp_format = venture_node[~venture_node['transactionId'].isin(missing_zip_code['transactionId']) &
                            ~venture_node['transactionId'].isin(zero_dolar_orders['transactionId']) &
                            ~venture_node['transactionId'].isin(discrepancy_orders['transactionId'])&
                            ~venture_node['transactionId'].isin(tax_only['transactionId'])]
# %%
total_rows = len(zamp_format)
third = total_rows // 3
zamp_format_1 = zamp_format.iloc[:third].copy()
zamp_format_2 = zamp_format.iloc[third:2*third].copy()
zamp_format_3 = zamp_format.iloc[2*third:].copy()
# %%
# Sample 50 random orders from zamp_format
random_sample = zamp_format.sample(n=50, random_state=42)
#random_sample.to_csv('/Users/strider/Zamp/GitHub/special_projects/data_validation_code/random_50_orders.csv', index=False)
#print(f"\nCreated random_50_orders.csv with {len(random_sample)} orders")
# %%
from pydantic_validation_transaction_level import validate_dataframe, get_validation_stats 
valid, invalid = validate_dataframe(zamp_format_3)
stats = get_validation_stats(invalid)
print(stats)

# %%

1.Business Scenario


# Imagine that we work in the finance team of a company.
# The company process customer payments through internal systems and banks
# At the end of the day, the finance team receives:
  # Internal payment records
  # bank transaction statements
# The team must compare both datasets



#For example
# Transaction ID Internal amount Bank amount
# TXN001       5000    5000
#TXN002        2500    2500
#TXN003        3000    Missing
#TXN004        1200   1500

# The first transactions match.
# The third transaction is missing from bank statement
# The fourth transaction has an amount mismantch
# Our responsibility is to automate this recocilation process

# TOOLS AND TECHNOLOGIES
# 1.pyhton
# 2.Pandas
# 3.Numpy
# 4.Datime
# 5.OpenpyXL
# 6.CSV
# 7.Jupiter Notebook | Google colab


# Datet structure
# internal_payments.csv
# trnasaction_id,transaction_date,amount
# TXN001,2026-01-01,5000
# TXN002,2026-01-01,2500
# TXN003,2026-01-01,3000
# TXN004,2026-01-01,1200

# Bank transactions.csv
# TXN001,2026-01-01,5000
# TXN002,2026-01-01,2500
# TXN004,2026-01-01,1500
#TXN005,2026-01-01,800


# STEP 1 - Import libralies
import pandas as pd
import numpy as np
from pathlib  import Path
import os

# STEP 2 upload csv files
from google.colab import files
uploaded =files.upload()


import os
print(os.listdir("/content"))

# STEP 3 load both files

internal =pd.read_csv(
   "/content/internal_payments.csv"
)
bank = pd.read_csv(
    "/content/bank_transactions.csv"
)

# step 4 inspect the data
print(internal.head())
print(bank.head())

# check yhe information
print(internal.info())
print(bank.info())

# checks duplicats
print(internal.duplicated(subset = ["transaction_id"]).sum())
print(bank.duplicated(subset=["transaction_id"]).sum())

# checks missing
print(internal.isna().sum())
print(bank.isna().sum())

#check number of rows and columns
print(internal.shape)
print(bank.shape)

# STEP 5 - Clean the data
# Standerdise transaction IDs

for df in [internal,bank]:
   
   df["transaction_id"] = (df["transaction_id"]
                           .astype("string")
                           .str.strip()
                           .str.upper()
   )
# Converts dates
internal["transaction_date"] =pd.to_datetime(
    internal["transaction_date"],
    errors="coerce"
)
bank["transaction_date"]=pd.to_datetime(
    bank["transaction_date"],
    errors="coerce"
)
# convrt amount
internal["amount"]=pd.to_numeric(
    internal["amount"],
    errors="coerce"
)
bank["amount"]=pd.to_numeric(
    bank["amount"],
    errors="coerce"
)

# check invalid records
invalid_internal = internal[
    internal["transaction_id"].isna()
    |internal["transaction_date"].isna()
    |(internal["amount"]<0)
]
invalid_bank = bank[
    bank["transaction_id"].isna()
    |bank["transaction_date"].isna()
    |(bank["amount"]<0)
]

# STEP 6 - checks th duplicate transactions
internal_duplicates = internal[
  internal.duplicated(
      subset =["transaction_id"],
        keep =False
    )
]
bank_duplicates = bank[ 
    bank.duplicated(
        subset=["transaction_id"],
        keep = False

    )
]

# step 7 - prepare clean datasets for matching
# wew should not arbitarily select one record from aduplicate group
# first remove invalid records from the  matcing process. Then excute all duplicate transactions IDs

internal_valid = internal.drop(
    index = invalid_internal.index
).copy()
bank_valid = bank.drop(
    index=invalid_bank.index
).copy()

internal_unique = internal_valid[ 
    ~internal_valid["transaction_id"].isin(
        internal_duplicates["transaction_id"]
        )
].copy()

    
bank_unique = bank_valid[
    ~bank_valid["transaction_id"].isin(
        bank_duplicates["transaction_id"]
    )
].copy()
    

# Step 8 match tha transacton
reconciliation = internal_unique.merge(
    bank_unique,
    on="transaction_id",
    how="outer",
    suffixes=("_internal","_bank"),
    indicator = True
)
# explain
# outer : keeps th records fron the both datasets
# indicator= True : create a column identifying where each came from 
#suffixes: distingush inyernal and bank columns

# STEP 9 Clasify reconciliation results
reconciliation["reconciliation_status"] = np.select(
    [
        reconciliation["_merge"] =="left_only",
        reconciliation["_merge"]=="right_only",
        reconciliation["amount_internal"]
        == reconciliation["amount_bank"]
        ],
    [
        "Missing in Bank",
        "Missing in Internally",
        "Matched"
    ],
    default="Amount Mismatch"
)

# STEP 10 Claculate amount deffrencs
reconciliation["amount_deffrence"]=(
    reconciliation["amount_internal"]
    -reconciliation["amount_bank"]
)

#  STEP 11 - Crete expectation reports
exceptations = reconciliation[
    reconciliation["reconciliation_status"]
    !="Matched"
].copy()
print(exceptations)

# Create reconcilation summary
summary = (
    reconciliation["reconciliation_status"]
    .value_counts()
    .reset_index()
)
summary.column = [
      "reconciliation_status",
       "record_count"
]
print(summary)

# Calculate the number of matched transactions
matched_count =(
    reconciliation["reconciliation_status"]
    =="Matched"
  ).sum()

total_count = len(reconciliation)

match_percentage = (
    matched_count/total_count * 100
    if total_count else 0
)
print("Matched:",matched_count)
print("Total:",total_count)
print("Match percenyage:",match_percentage)

# Export the out puts
output_path =Path("outputs")

output_path.mkdir(
    parents= True,
    exist_ok=True
)

reconciliation.to_csv(
    output_path / "full_reconciliation.csv",
    index=False
)



exceptations.to_csv(
    output_path / "exceptation_report.csv",
    index=False
)
summary.to_csv(
    output_path / "reconciliation_summary",
    index=False
)



# Tolerance based matching

tolerance = 0.01

reconciliation["amount_match_with_tolerance"]=(
    reconciliation["amount_internal"]
- reconciliation["amount_bank"].abs()) <=tolerance


# daily reconciliation summary
daily_summary =(
    reconciliation.groupby(
        [
            "transaction_date_internal",
            "reconciliation_status"
        ]
    )
    .size()
    .reset_index(name="record_count")
)
display(daily_summary.head(20))

# Calculate total amount discrepancy
total_deffrence =(
    reconciliation["amount_deffrence"]
    .abs()
    .sum()
)
print("Total Absolute amount diffrence:",total_deffrence,2)

#logging and error handling
try:
  internal =pd.read_csv(
      "/content/internal_payments.csv"
)
  bank =pd.read_csv(
      "/content/bank_transactions.csv"
  )
  print("Files loaded successfully")
except FileNotFoundError:
  print("Error:CSV files not found.")
except Exception as e:
  print("An unexpected error occured",e)

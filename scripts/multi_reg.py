import glob
import csv
import sys
import numpy as np
from sklearn import linear_model

# Initialize variables
first_record = True
n_obs = 0
X = []
Y = []
y_column = 1
n_reg = 0

# Iterate over input files with names matching in.*.dat
for file_name in glob.glob("./in.*.dat"):
    with open(file_name, newline='') as csv_file:
        # Open CSV reader with blank separators and numeric conversion
        print("# Reading CSV file:", file_name)
        csv_reader = csv.reader(csv_file,
                                delimiter=' ',
                                quoting=csv.QUOTE_NONNUMERIC)

        # Iterate over file rows
        for row in csv_reader:
            # Increment cardinality
            n_obs += 1
            
            # Distinguish between first and subsequent records
            if first_record:
                # Initialize regressors with first record
                n_reg = len(row) - 1
                X = [[x] for x in row[:y_column] + row[y_column + 1:]]
                first_record = False
            else:
                # Ensure consistency in number of regressors
                if n_reg != len(row) - 1:
                    print("** ERROR: Incorrect number of regressors:",
                      len(row) - 1)
                    sys.exit(1)
                # Update regressors with current record
                for i, x in enumerate(row[:y_column] + row[y_column + 1:]):
                    X[i].append(x)

            # Update regressand with current record
            Y.append(row[y_column])

# Compute multilinear regression
print("# Multilinear regression against",
      n_reg,
      "regressors for",
      n_obs,
      "observations:")
lr = linear_model.LinearRegression()
lr.fit(np.array(X).transpose(), Y)
print("  Intercept:", lr.intercept_)
print("  Regressor coefficients:")
for i, c in enumerate(lr.coef_):
    reg_col = i if i < y_column else i + 1
    print("    column",
          reg_col,
          ":",
          c)
    
print("  Coefficient of determination (R2):", lr.score(np.array(X).transpose(), Y))

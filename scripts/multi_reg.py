import glob
import csv
import sys
import numpy as np
from sklearn import linear_model

# Initialize variables
n_obs = {}
X = {}
x_excluded = [6, 7, 9, 10]
Y = {}
y_col = 1
Booleans = []
bool_cols = slice(-3, None)
n_regressors = 0

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
            # Compute record type from Boolean field and update as needed
            r_type = sum([int(b) << i for i, b in enumerate(row[bool_cols])])
            if r_type not in X:
                # Initialize type cardinality
                n_obs[r_type] = 1

                # Initialize regressors with record
                print("# New record Boolen type found:",
                      ' '.join([str(int(b)) for b in row[bool_cols]]),
                      "=>",
                      r_type)
                n_regressors = len(row) - (len(x_excluded) + 1)
                X[r_type] = [[x] for i, x in enumerate(row) if i != y_col and i not in x_excluded]
            else:
                # Increement tupe cardinality
                n_obs[r_type] += 1

                # Ensure consistency in number of regressors
                if n_regressors != len(row) - (len(x_excluded) + 1):
                    print("** ERROR: Incorrect number of regressors read:",
                      len(row) - 1,
                          "!=",
                          n_regressors)
                    sys.exit(1)

                # Update regressors with current record
                j = 0
                for i, x in enumerate(row):
                    if i == y_col or i in x_excluded:
                        continue
                    X[r_type][j].append(x)
                    j += 1
            
            # Update regressand with current record
            Y.setdefault(r_type, []).append(row[y_col])

# Compute multilinear regression
for k, v in X.items():
    print("# Multilinear regression against",
          n_regressors,
          "regressors for type",
          k,
          "with",
          n_obs[k],
          "observations:")

    lr = linear_model.LinearRegression()
    lr.fit(np.array(v).transpose(), Y[k])
    print("  Intercept:", lr.intercept_)
    print("  Regressor coefficients:")
    for c in lr.coef_:
        print("    ", c)

    print("  Coefficient of determination (R2):", lr.score(np.array(v).transpose(), Y[k]))

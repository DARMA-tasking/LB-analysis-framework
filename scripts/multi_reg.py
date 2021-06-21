import glob
import csv
import sys
import numpy as np
from sklearn import linear_model

# Initialize variables
first_row = True
n_obs = {}
X = {}
excluded = set([0])#, 6, 7, 9, 10]
Y = {}
y_col = 1
Booleans = []
bool_cols = set([11, 12, 13])
n_regressors = 0

# Prepare set of columns to be disregarded as regressors
excluded.update(set([y_col]))
excluded.update(bool_cols)

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
            r_type = sum([int(b) << i for i, b in enumerate(row) if i in bool_cols])
            if r_type not in X:
                # Handle particular case of first row
                if first_row:
                    # Initialize number of regressors with record
                    n_regressors = len(row) - len(excluded)
                    print("# Found", n_regressors, "regressors in first row")
                    first_row = False

                # Initialize type cardinality
                n_obs[r_type] = 1
                print("# New record Boolen type found:",
                      ' '.join([str(int(b)) for i, b in enumerate(row) if i in bool_cols]),
                      "=>",
                      r_type)
                X[r_type] = [[x] for i, x in enumerate(row) if i not in excluded]
            else:
                # Increement tupe cardinality
                n_obs[r_type] += 1

                # Ensure consistency in number of regressors
                if n_regressors != len(row) - len(excluded):
                    print("** ERROR: Incorrect number of regressors read:",
                      len(row) - len(excluded),
                          "!=",
                          n_regressors)
                    sys.exit(1)

                # Update regressors with current record
                j = 0
                for i, x in enumerate(row):
                    if i in excluded:
                        continue
                    X[r_type][j].append(x)
                    j += 1
            
            # Update regressand with current record
            Y.setdefault(r_type, []).append(row[y_col])

# Compute multilinear regression
for k, v in X.items():
    print("# Multilinear regression to",
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

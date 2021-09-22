import glob
import csv
import sys
import re
import numpy as np
from sklearn import linear_model

# This script trains on in.*.dat in the training directory passed on the
# command-line and then predicts on in.*.dat in the working directory.

def setupRegressors(files, bool_cols, y_col, rank_col, excluded, X, Y, ranks, regressor_list, n_obs):
    first_row = True
    # Iterate over input files with names matching in.*.dat
    for file_name in files:
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
                        for i, x in enumerate(row):
                            if i in excluded:
                                continue
                            regressor_list.append(i)
                        if n_regressors != len(regressor_list):
                            print("** ERROR: Unexpected regressor list length")
                            sys.exit(1)

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
                ranks.setdefault(r_type, []).append(int(row[rank_col]))


print(sys.argv)

if len(sys.argv) != 2:
    print("** ERROR: Specify training directory on the command-line")
    sys.exit(1)

training_dir = sys.argv[1];

# Initialize global variables
regressor_list = []
n_obs = {}
X = {}
Y = {}
ranks = {}
lr = {}

# Define regressand column
y_col = 1

# Define mpi rank column
rank_col = 0

# Possibly exclude columns from regressors
#excluded = set([0, 3, 4, 5, 6, 7, 8, 9, 10])
excluded = set([0, 6, 7, 9])

# Compute up to 2**3 = 8 different models
bool_cols = set([11, 12, 13]) 

# Prepare set of columns to be disregarded as regressors
excluded.update(set([y_col]))
excluded.update(bool_cols)

# Iterate over input files with names matching in.*.dat
training_files = glob.glob(training_dir + "/in.*.dat")
testing_files = glob.glob("./in.*.dat")
setupRegressors(training_files, bool_cols, y_col, rank_col, excluded, X, Y, ranks, regressor_list, n_obs)

Z = {}

# Compute multilinear regression
for k, v in X.items():
    print("# Multilinear regression to",
          len(regressor_list),
          "regressors for type",
          k,
          "with",
          n_obs[k],
          "observations:")

    lr[k] = linear_model.LinearRegression()
    lr[k].fit(np.array(v).transpose(), Y[k])
    print("  Intercept:", lr[k].intercept_)
    print("  Regressor coefficients:")
    j = 0
    for c in lr[k].coef_:
        print("    ", c, "for column", regressor_list[j])
        j += 1
    print("  Coefficient of determination (R2):", lr[k].score(np.array(v).transpose(), Y[k]))

    Z[k] = lr[k].predict(np.array(v).transpose())
    sumVal = 0.0
    sumSqrVal = 0.0
    sumSqrRes = 0.0
    for i in range(len(Y[k])):
        sumVal    += Y[k][i]
        sumSqrVal += (Y[k][i])**2
        sumSqrRes += (Z[k][i]-Y[k][i])**2
    manual_score = 1.0 - sumSqrRes / (sumSqrVal - sumVal**2/len(Y[k]))
    print("  Manually calculated R2 (sanity check):", manual_score)

# Now write out predicted data
for file_name in testing_files:
    this_file_only = [file_name]
    X1 = {}
    Y1 = {}
    Z1 = {}
    ranks1 = {}
    regressor_list1 = []
    n_obs1 = {}

    setupRegressors(this_file_only, bool_cols, y_col, rank_col, excluded, X1, Y1, ranks1, regressor_list1, n_obs1)

    out_file_name = file_name.replace('in', 'model')
    with open(out_file_name, 'w') as f:
        sys.stdout = f
        for k, v in X1.items():
            Z1[k] = lr[k].predict(np.array(v).transpose())
            for i in range(len(Y1[k])):
                print(ranks1[k][i], Y1[k][i], Z1[k][i])
    sys.stdout = sys.__stdout__


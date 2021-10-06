import os
import sys

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    exit(1)

import glob
import csv
import numpy as np
from sklearn import linear_model


class MultiLinearRegression:
    def __init__(self, n_obs: dict = None, X: dict = None, Y: dict = None, y_col: int = 1, excluded: set = None,
                 bool_cols: set = None, data_dir: str = None, regressor_list: list = None, ranks: dict = None,
                 rank_col: int = None):
        self.first_row = True
        self.n_regressors = 0
        self.y_col = y_col

        self.n_obs = n_obs
        if self.n_obs is None:
            self.n_obs = dict()
        self.X = X
        if self.X is None:
            self.X = dict()
        self.Y = Y
        if self.Y is None:
            self.Y = dict()
        # Compute up to 2**3 = 8 different models
        self.bool_cols = bool_cols
        if self.bool_cols is None:
            self.bool_cols = {11, 12, 13}
        # Possibly exclude columns from regressors
        self.excluded = excluded
        if self.excluded is None:
            self.excluded = {0, 3, 4, 5, 6, 7, 8, 9, 10}
        # Prepare set of columns to be disregarded as regressors
        self.excluded.update({self.y_col})
        self.excluded.update(self.bool_cols)
        # Regressor list (new data prediction)
        self.regressor_list = regressor_list
        self.ranks = ranks
        # MPI rank column
        self.rank_col = rank_col
        # Data directory
        self.data_dir = data_dir
        self.data_dir = self._get_data_dir()

    def _get_data_dir(self):
        """ Returns absolute path to the data dir (takes relative or absolute path)"""
        if os.path.isdir(self.data_dir) and glob.glob(os.path.join(self.data_dir, 'in.*.dat')):
            return self.data_dir
        elif os.path.isdir(os.path.abspath(os.path.join(project_path, self.data_dir))) and \
                glob.glob(os.path.join(os.path.abspath(os.path.join(project_path, self.data_dir)), 'in.*.dat')):
            return os.path.abspath(os.path.join(project_path, self.data_dir))
        raise FileNotFoundError(f'No data found in given path {self.data_dir}')

    def _read_input_data(self):
        """ Iterate over input files with names matching in.*.dat """
        for file_name in glob.glob(os.path.join(self.data_dir, 'in.*.dat')):
            with open(file_name, newline='') as csv_file:
                # Open CSV reader with blank separators and numeric conversion
                print(f"# Reading CSV file: {file_name}")
                csv_reader = csv.reader(csv_file, delimiter=' ', quoting=csv.QUOTE_NONNUMERIC)

                # Iterate over file rows
                for row in csv_reader:
                    # Compute record type from Boolean field and update as needed
                    r_type = sum([int(b) << i for i, b in enumerate(row) if i in self.bool_cols])
                    if r_type not in self.X:
                        # Handle particular case of first row
                        if self.first_row:
                            # Initialize number of regressors with record
                            n_regressors = len(row) - len(self.excluded)
                            print(f"# Found {n_regressors} regressors in first row")
                            self.first_row = False
                            if self.regressor_list is not None:
                                for num, x in enumerate(row):
                                    if num not in self.excluded:
                                        self.regressor_list.append(num)
                                if n_regressors != len(self.regressor_list):
                                    raise ValueError('Unexpected regressor list length')

                        # Initialize type cardinality
                        self.n_obs[r_type] = 1
                        new_rec_boolean = ' '.join([str(int(b)) for i, b in enumerate(row) if i in self.bool_cols])
                        print(f"# New record Boolean type found: {new_rec_boolean} => {r_type}")
                        self.X[r_type] = [[x] for i, x in enumerate(row) if i not in self.excluded]
                    else:
                        # Increment type cardinality
                        self.n_obs[r_type] += 1

                        # Ensure consistency in number of regressors
                        n_regressors_actual = len(row) - len(self.excluded)
                        if n_regressors != n_regressors_actual:
                            raise ValueError(
                                f"Incorrect number of regressors read: {n_regressors_actual} != {n_regressors}")

                        # Update regressors with current record
                        j = 0
                        for num, x in enumerate(row):
                            if num not in self.excluded:
                                self.X[r_type][j].append(x)
                                j += 1

                    # Update regressand with current record
                    self.Y.setdefault(r_type, []).append(row[self.y_col])
                    if self.ranks is not None and self.rank_col is not None:
                        self.ranks.setdefault(r_type, []).append(int(row[self.rank_col]))

    def compute_multilinear_regression(self) -> None:
        """ Compute multilinear regression """
        self._read_input_data()
        for k, v in self.X.items():
            print(f"# Multilinear regression to {self.n_regressors} regressors for type {k} with {self.n_obs[k]} "
                  f"observations:")
            lr = linear_model.LinearRegression()
            lr.fit(np.array(v).transpose(), self.Y[k])
            print(f"  Intercept: {lr.intercept_}")
            print("  Regressor coefficients:")
            for c in lr.coef_:
                print(f"    {c}")
            print(f"  Coefficient of determination (R2): {lr.score(np.array(v).transpose(), self.Y[k])}")

    def compute_multilinear_regression_and_predict_new_data(self) -> None:
        """ Compute multilinear regression and predicts new data """
        self._read_input_data()
        Z = dict()
        for k, v in self.X.items():
            print(f"# Multilinear regression to {len(self.regressor_list)} regressors for type {k} with {self.n_obs[k]}"
                  f" observations:")
            lr = dict()
            lr[k] = linear_model.LinearRegression()
            lr[k].fit(np.array(v).transpose(), self.Y[k])
            print(f"  Intercept: {lr.intercept_}")
            print("  Regressor coefficients:")
            for num, column in enumerate(lr[k].coef_):
                print(f"    {column} for column {self.regressor_list[num]}")
            print(f"  Coefficient of determination (R2): {lr[k].score(np.array(v).transpose(), self.Y[k])}")
            Z[k] = lr[k].predict(np.array(v).transpose())
            sum_val = 0.0
            sum_sqr_val = 0.0
            sum_sqr_res = 0.0
            for i in range(len(self.Y[k])):
                sum_val += self.Y[k][i]
                sum_sqr_val += (self.Y[k][i]) ** 2
                sum_sqr_res += (Z[k][i] - self.Y[k][i]) ** 2
            manual_score = 1.0 - sum_sqr_res / (sum_sqr_val - sum_val ** 2 / len(self.Y[k]))
            print(f"  Manually calculated R2 (sanity check): {manual_score}")


if __name__ == "__main__":
    MultiLinearRegression(data_dir='linear_data/positive_correlation').compute_multilinear_regression()

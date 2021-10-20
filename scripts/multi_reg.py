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
from typing import Union

import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error


class FileFinder:
    def __init__(self, data_dir: str = None):
        # Data directory
        self.data_dir = data_dir
        self.data_dir = self._get_data_dir()
        # Input files
        self.in_files = self._get_files_list()

    def _get_data_dir(self):
        """ Returns absolute path to the data dir (takes relative or absolute path)"""
        if os.path.isdir(self.data_dir) and glob.glob(os.path.join(self.data_dir, 'in.*.dat')):
            return self.data_dir
        elif os.path.isdir(os.path.abspath(os.path.join(project_path, self.data_dir))) and \
                glob.glob(os.path.join(os.path.abspath(os.path.join(project_path, self.data_dir)), 'in.*.dat')):
            return os.path.abspath(os.path.join(project_path, self.data_dir))
        raise FileNotFoundError(f'No data found in given path {self.data_dir}')

    def _get_files_list(self):
        """ Returns list of found datafiles"""
        in_files = [file_name for file_name in glob.glob(os.path.join(self.data_dir, 'in.*.dat'))]
        return in_files


class MultiLinearRegression:
    def __init__(self, input_files: Union[str, list], n_obs: dict = None, X: dict = None, Y: dict = None,
                 y_col: int = None, excluded: set = None, bool_cols: set = None, rank_col: int = None):
        self.first_row = True
        self.y_col = y_col
        if self.y_col is None:
            raise Exception('Y column must be given!')
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
            raise Exception('Boolean columns must be given!')
        # Possibly exclude columns from regressors
        self.excluded = excluded
        if self.excluded is None:
            raise Exception('Excluded must be given!')
        # Column indexes
        self.ranks = dict()
        self.rank_col = rank_col
        if self.rank_col is None:
            raise Exception('Rank column must be given!')
        # Prepare set of columns to be disregarded as regressors
        self.excluded.update({self.y_col})
        self.excluded.update(self.bool_cols)
        # Initiate regressor list
        self.regressor_list = list()
        self.input_files = input_files
        if isinstance(self.input_files, str):
            self.input_files = [input_files]
        self._read_input_data()

    def _read_input_data(self):
        """ Iterate over input files """
        for file_name in self.input_files:
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
                            for i, x in enumerate(row):
                                if i not in self.excluded:
                                    self.regressor_list.append(i)
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
                    self.ranks.setdefault(r_type, []).append(int(row[self.rank_col]))


def learn(x_data: dict, y_data: dict, regressor_list: list, num_observation: dict) -> dict:
    """ Takes X, Y as input params. Returns dict of Linear Models """
    lr = dict()
    for k, v in x_data.items():
        print(f"# Multilinear regression to {len(regressor_list)} regressors for type {k} with {num_observation[k]}"
              f" observations:")
        lr[k] = linear_model.LinearRegression()
        lr[k].fit(np.array(v).transpose(), y_data[k])
        print(f"  Intercept: {lr[k].intercept_}")
        print(f"  Regressor coefficients:")
        for num, c in enumerate(lr[k].coef_):
            print(f"    {c} for column {regressor_list[num]}")
        print(f"  Coefficient of determination (R2): {lr[k].score(np.array(v).transpose(), y_data[k])}")
        # linear_model_dict[k] = lr

    return lr


def assess(x_data: dict, y_data: dict, linear_model_dict: dict) -> dict:
    """ Takes X, Y and dict of linear models as input params. Returns dict of RMSE """
    rmse_dict = dict()
    y_predict = predict(x_data=x_data, linear_model_dict=linear_model_dict)
    for k, v in x_data.items():
        y_pred = y_predict[k]
        y_true = np.array(y_data[k])
        rmse = mean_squared_error(y_true=y_true, y_pred=y_pred)
        print(f"  Root-mean-square error (RMSE) for {k}: {rmse}")
        rmse_dict[k] = rmse

    return rmse_dict


def predict(x_data: dict, linear_model_dict: dict, verbose: bool = False) -> dict:
    """ Takes X and dict of linear models as input params. Returns dict of predicted Y """
    y_pred_dict = dict()
    for k, v in x_data.items():
        lr = linear_model_dict[k]
        y_pred = lr.predict(np.array(v).transpose())
        if verbose:
            print(f"  Predicted Y values for {k}: {y_pred}")
        y_pred_dict[k] = y_pred

    return y_pred_dict


def save_data(in_files: list, y_read: dict, y_predict: dict, ranks: dict):
    """ Takes list of input files, Y values, Y predicted values and index column numbers.
        Saves to a file index column numbers, Y values, Y predicted values. """
    for file in in_files:
        dir_path = os.path.split(file)[0]
        file_name = os.path.split(file)[-1].replace('in', 'model')
        out_file = os.path.join(dir_path, file_name)
        with open(out_file, 'wt') as o_file:
            for bool_type, values in y_read.items():
                for num, val in enumerate(values):
                    o_file.write(
                        f"{ranks[bool_type][num]} {y_read[bool_type][num]} {y_predict[bool_type][num]}\n")


if __name__ == "__main__":
    RANK_COLUMN = 0
    Y_COLUMN = 1
    BOOL_COLS = {11, 12, 13}
    EXCLUDED = {0, 6, 7, 9, 10}
    # Learning directory
    DATA_DIR = 'linear_data/exact_correlation'
    # Predict / asses / save directory
    PREDICT_DIR = 'linear_data/exact_correlation'

    # Getting list of files for learning
    ff_files = FileFinder(data_dir=DATA_DIR).in_files
    # Getting list of files for predicting / assessing
    ff_files_pred = FileFinder(data_dir=PREDICT_DIR).in_files

    # Learning
    mlr = MultiLinearRegression(input_files=ff_files, bool_cols=BOOL_COLS, excluded=EXCLUDED, rank_col=RANK_COLUMN,
                                y_col=Y_COLUMN)
    mlr_model = learn(x_data=mlr.X, y_data=mlr.Y, regressor_list=mlr.regressor_list, num_observation=mlr.n_obs)

    # Predict, asses and save
    for file in ff_files_pred:
        mlr = MultiLinearRegression(input_files=file, bool_cols=BOOL_COLS, excluded=EXCLUDED, rank_col=RANK_COLUMN,
                                    y_col=Y_COLUMN)
        y_pred = predict(x_data=mlr.X, linear_model_dict=mlr_model)
        rmse = assess(x_data=mlr.X, y_data=mlr.Y, linear_model_dict=mlr_model)
        save_data(in_files=mlr.input_files, y_read=mlr.Y, y_predict=y_pred, ranks=mlr.ranks)

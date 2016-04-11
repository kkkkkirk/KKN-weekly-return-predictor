import xlrd
import numpy
import datetime
import statsmodels.api as sm

'''
Input illustration:
- source_file:  name of the file that contains training and testing data
- m:            embedding dimension of each history vector
- k:            k nearest neighbors are used to predict [Rule of thumb is square root of the number of data set we have]
- threshold:    filter that reduces the false buy/sell signal
- start_date:   starting date of a testing period
- end_date:     ending date of a testing period
'''


class Predictor:

    def __init__(self, source_file, m, k, threshold, start_date, end_date):
        self.m = m
        self.k = k
        self.x_T = []                                       # history vector x at time T
        self.corr_list = []                                 # contains correlation between x_T and other history vectors
        self.start_split = 1
        self.end_split = 1
        self.threshold = threshold
        self.daily_data_by_weeks = []
        self.weekly_return_data = []
        self.historical_weekly_return_data = []  # complete list of source data
        self.wb = xlrd.open_workbook(source_file)
        self.test_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        self.test_end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

    # Read source file, and organize daily data by week
    def read_file_to_daily_data_by_weeks(self, sheet_idx):
        ws = self.wb.sheet_by_index(sheet_idx)

        # Set some defaults
        last_week_day = 0
        weekly_queue = []

        # Loop through Excel workbook line by line, and extract data
        for row in range(1, ws.nrows):
            col_date = datetime.datetime(*xlrd.xldate_as_tuple(ws.cell(row, 0).value, self.wb.datemode)).date()
            col_index_price = ws.cell(row, 1).value
            col_week_day = ws.cell(row, 2).value            # 1-5 stands for Mon-Fri

            # Organize data by week
            if col_week_day <= last_week_day:

                # Calculate the week number of testing start & end date
                if last_week_date < self.test_start_date: self.start_split += 1
                if last_week_date < self.test_end_date: self.end_split += 1

                self.daily_data_by_weeks.append(weekly_queue)
                weekly_queue = []

            weekly_queue.append([col_date, col_week_day, col_index_price])
            last_week_day = col_week_day
            last_week_date = col_date

        self.daily_data_by_weeks.append(weekly_queue)


    # Calculate weekly returns from given daily data
    def calc_historical_weekly_return(self, daily_list):

        # Refresh array for next prediction
        self.weekly_return_data = []

        # Calculate weekly returns
        weeks = len(daily_list)
        for idx in range(1, weeks):

            # Use the last available price of each week, in case Friday is a vacation
            previous_week_end_price = daily_list[idx - 1][-1][2]
            current_week_end_price = daily_list[idx][-1][2]
            weekly_return = current_week_end_price / float(previous_week_end_price) - 1
            self.historical_weekly_return_data.append(weekly_return)


    # Find and return k nearest neighbor history vector based on correlation
    def find_k_closest_histories(self):

        # Define history vector at time T
        self.x_T = self.weekly_return_data[-1*self.m:]

        # Set some defaults
        self.corr_list = []
        closest_k_list = []

        # Loop through t = 1...T-1 to find correlation coefficients
        for wk_num in range(1, len(self.weekly_return_data)+1-self.m):
            x_t = self.weekly_return_data[wk_num-1:wk_num-1+self.m]
            corr = numpy.corrcoef(x_t, self.x_T)[0][1]
            self.corr_list.append(tuple([wk_num, corr]))

        # Sort by correlation first, select the k top correlation, sort by time in reverse
        self.corr_list.sort(key=lambda tup: tup[1], reverse=True)
        closest_k_corr = self.corr_list[:self.k]
        closest_k_corr.sort(key=lambda tup: tup[0], reverse=True)

        # Retrieve the history vectors based on wk_num
        for item in closest_k_corr:
            starting_week = item[0]
            closest_k_list.append(self.weekly_return_data[starting_week-1:starting_week+self.m])

        return closest_k_list


    # Predict next week's return
    def calc_next_week_return(self, closest_k_list):

        # prepare data for linear regression
        x = []
        for idx in range(self.m):
            x.append([val[idx] for val in closest_k_list])
        y = [val[self.m] for val in closest_k_list]

        # run regression on x and y
        x = numpy.array(x).T
        x = sm.add_constant(x)
        result = sm.OLS(endog=y, exog=x).fit()

        # calculate predicted weekly return
        x_T_array = numpy.array([1]+self.x_T)               # [1] for constant term
        coeffs = numpy.array(result.params)                 # in order of [constant, X1, X2, X3, X4, X5]
        predicted_return = numpy.dot(x_T_array, coeffs)

        return predicted_return


    # Produce but/sell signal based on current state and our prediction
    def signal(self, current_state, predicted_return):

        # we predict next week's movement greater than pre-determined filter
        if predicted_return > self.threshold:
            if current_state == 0 or current_state == -1:
                return 1
            else:
                return current_state

        # we predict next week's movement greater than filter, but in negative direction
        elif abs(predicted_return) > self.threshold:
            if current_state == 0 or current_state == 1:
                return -1
            else:
                return current_state

        # false buy/sell signal, ignored
        else:
            return current_state



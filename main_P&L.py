import math
from Predictor import Predictor

'''
This is to produce the weekly P&L over a given testing period.
'''

def Stdev(list):
    n = len(list)
    mean = sum(list)/float(n)
    sd = math.sqrt(sum((x-mean)**2 for x in list)/(n-1))
    annualized_sd = sd * math.sqrt(52)
    return annualized_sd


def DoWork(source_file, m, k, fltr, trade_cost, testing_start_date, testing_end_date):

    # Set some defaults
    p = Predictor(source_file, m, k, fltr, testing_start_date, testing_end_date)
    p.read_file_to_daily_data_by_weeks(0)
    p.calc_historical_weekly_return(p.daily_data_by_weeks)

    # Initialize variables
    strategy_trade_count = 0
    in_market_count = 0
    current_state = 0
    strategy_capital = 100
    bh_capital = 100
    strategy_weekly_return = []
    bh_weekly_return = []


    for idx in range(p.start_split, p.end_split):

        # Generate weekly signals
        p.weekly_return_data = p.historical_weekly_return_data[:idx-1]
        alist = p.find_k_closest_histories()
        r = p.calc_next_week_return(alist)
        cur_signal = p.signal(current_state, r)

        # Signal handling
        cur_index_price = p.daily_data_by_weeks[idx][-1][2]
        prev_index_price = p.daily_data_by_weeks[idx-1][-1][2]
        actual_return = math.log(cur_index_price) - math.log(prev_index_price)
        if current_state != cur_signal:
            current_state = cur_signal
            strategy_trade_count += 1
            strategy_capital = strategy_capital * (1 - trade_cost)

        # K Nearest Neighbor
        strategy_capital = strategy_capital * (1 + actual_return * current_state)
        strategy_weekly_return.append(actual_return)


        # Buy-and-Hold
        if current_state == 1:
            #in_market_count += 1
            bh_capital = bh_capital * (1 + actual_return)
            bh_weekly_return.append(actual_return)

        print('{0}, {1}, {2}'.format(p.daily_data_by_weeks[idx-1][-1][0], strategy_capital, bh_capital))


DoWork('Source Data.xlsx', 5, 75, 0.001, 0.0005, '2006-01-03', '2015-12-31')

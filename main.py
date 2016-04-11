import math
from Predictor import Predictor


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
    long_position_r = 0
    short_position_r = 0
    bh_return = 0
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

        # K Nearest Neighbor
        if current_state == 1:
            long_position_r += actual_return
            strategy_weekly_return.append(actual_return)
        elif current_state == -1:
            short_position_r += actual_return * current_state
            strategy_weekly_return.append(actual_return * current_state)

        # Buy-and-Hold
        if current_state == 1:
            in_market_count += 1
            bh_return += actual_return
            bh_weekly_return.append(actual_return)

        '''
        if current_state == 0:
            decision = 'No position!'
        elif actual_return * current_state > 0:
            decision = 'Prediction is RIGHT!'
        else:
            decision = 'Prediction is WRONG!'
        print('Predicted return = {0} and actual return = {1} - {2}'.format(r, actual_return, decision))
        '''

    # Excess return
    trade_cost_coef = math.log((1-trade_cost)/(1+trade_cost))
    strategy_return = long_position_r + short_position_r + strategy_trade_count * trade_cost_coef
    bh_return = (in_market_count/float(p.end_split - p.start_split)) * bh_return + 2 * trade_cost_coef

    print('Strategy return = {0} (long: {1} and short: {2}), bh return = {3}, excess return = {4}, sharpe = {5}'.format(strategy_return, long_position_r, short_position_r, bh_return, strategy_return-bh_return, strategy_return/Stdev(strategy_weekly_return)))
    #print('Strategy sd = {0}, bh sd = {1}'.format(Stdev(strategy_weekly_return), Stdev(bh_weekly_return)))

for k in [50, 60, 70, 80, 90, 100, 110, 120]:
    for f in [0.001, 0.002, 0.003, 0.004, 0.005]:
        print('K = {0} and filter = {1}'.format(k, f))
        DoWork('Source Data.xlsx', 5, k, f, 0.0005, '2006-01-03', '2015-12-31')
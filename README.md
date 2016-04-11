# KKN-weekly-return-predictor


Forecast weekly returns on S&P 500 index price using weekly return histories for the prior 5 weeks (m=5)  
Value of k and the filter (threshold for changing positions) are determined based on data  
Always be long or short the market for the testing period (January 2006 through December 2015)

· use daily S&P 500 index prices from 1927-2015 in the attached Excel file to calculate weekly m-histories for the trading strategy training period and testing period
· trade every Friday based upon the forecast for the following week
· assume the risk free rate of return (rf(t) in the research paper) is 0
· assume the trading cost in each direction is 0.05% (i.e., when buying OR selling an index position worth $100, one pays $0.05 in trading costs)
· present cumulative P&L and Sharpe ratio

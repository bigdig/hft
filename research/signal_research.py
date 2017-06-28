import os
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model

import hft.utils as utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(name)s  %(levelname)s  %(message)s')

hft_path = os.path.join(os.environ['HOME'], 'dropbox', 'hft')
data_path = os.path.join(hft_path, 'data')
research_path = os.path.join(hft_path, 'research')

# load enriched data
# ------------------

product = 'zn'  # switch between cu and zn
with open(os.path.join(os.environ['HOME'], 'hft', 'ticksize.json')) as ticksize_file:
    ticksize_json = json.load(ticksize_file)
tick_size = ticksize_json[product]

px = pd.read_pickle(os.path.join(data_path, product+'_enriched.pkl'))

px20131031 = px[px.date == '2013-10-31']
# px = px[np.isnan(px.tick_move_1_0) | (np.abs(px.tick_move_1_0) <= 5)]
px = px[px.date != '2013-10-31']

# signal and return distribution
# ------------------------------

px[['order_flow_imbalance_1_0', 'order_flow_imbalance_2_0', 'order_flow_imbalance_5_0',
    'order_flow_imbalance_10_0', 'order_flow_imbalance_20_0']].describe()

px[['order_imbalance_ratio_1_0', 'order_imbalance_ratio_2_0', 'order_imbalance_ratio_5_0',
    'order_imbalance_ratio_10_0', 'order_imbalance_ratio_20_0']].describe()

px[['tick_move_1_0', 'tick_move_2_0', 'tick_move_5_0', 'tick_move_10_0', 'tick_move_20_0', 'tick_move_30_0',
    'tick_move_60_0', 'tick_move_120_0', 'tick_move_180_0', 'tick_move_300_0']][px.date != '2013-10-31'].describe()

px[['tick_move_5_0', 'tick_move_0_10', 'tick_move_0_20']].describe()

plt.subplot(1, 2, 1)
px.order_flow_imbalance_60_0.hist(bins=100)
plt.subplot(1, 2, 2)
px.order_flow_imbalance_300_0.hist(bins=100)

plt.subplot(1, 2, 1)
px.order_imbalance_ratio_60_0.hist(bins=100)
plt.subplot(1, 2, 2)
px.order_imbalance_ratio_300_0.hist(bins=100)

plt.subplot(1, 2, 1)
px['tick_move_0_60'].hist(bins=100)
plt.subplot(1, 2, 2)
px['tick_move_0_300'].hist(bins=100)
px.groupby(np.abs(px.tick_move_0_10)).size()

print(sum(px.tick_move_0_10 == 0) / sum(~np.isnan(px.tick_move_0_10)))  # % no move
print(sum(np.abs(px.tick_move_0_10) >= 1) / sum(~np.isnan(px.tick_move_0_10)))  # % 1 tick move
print(sum(np.abs(px.tick_move_0_10) >= 2) / sum(~np.isnan(px.tick_move_0_10)))  # % 2 tick move

print(sum(px.tick_move_0_20 == 0) / sum(~np.isnan(px.tick_move_0_20)))  # % no move
print(sum(np.abs(px.tick_move_0_20) >= 1) / sum(~np.isnan(px.tick_move_0_20)))  # % 1 tick move
print(sum(np.abs(px.tick_move_0_20) >= 2) / sum(~np.isnan(px.tick_move_0_20)))  # % 2 tick move

# return - signal linear relationship
# -----------------------------------

def scatter_plot(px, column_name, backward_seconds, forward_seconds):
    signal_column_name = utils.get_moving_column_name(column_name, backward_seconds, 0)
    return_column_name = utils.get_moving_column_name('tick_move', 0, forward_seconds)
    regr_data = px[[signal_column_name, return_column_name]].dropna()
    x = regr_data[[signal_column_name]].values
    y = regr_data[return_column_name].values
    regr = linear_model.LinearRegression()
    regr.fit(x, y)
    print('Coefficients: \n', regr.coef_)
    print('R-square: %f' % regr.score(x, y))
    plt.scatter(x, y, marker='o', s=0.1)
    plt.plot(x, regr.predict(x), color='red', linewidth=1)
    plt.xlabel(signal_column_name)
    plt.ylabel(return_column_name)
    plt.show()
    return

def xy_corr(px, second_list, column_name):
    column_names = [utils.get_moving_column_name(column_name, x, 0) for x in second_list]
    return_names = [utils.get_moving_column_name('tick_move', 0, x) for x in second_list]
    big_corr = px[column_names + return_names].corr()
    corr_mat = big_corr.loc[return_names, column_names]
    return corr_mat

def xx_corr(px, second_list, column_name, row_name):
    column_names = [utils.get_moving_column_name(column_name, x, 0) for x in second_list]
    row_names = [utils.get_moving_column_name(row_name, x, 0) for x in second_list]
    big_corr = px[column_names + row_names].corr()
    corr_mat = big_corr.loc[row_names, column_names]
    return corr_mat

plt.subplot(1, 2, 1)
scatter_plot(px, 'order_imbalance_ratio', 60, 60)
plt.subplot(1, 2, 2)
scatter_plot(px, 'order_imbalance_ratio', 300, 300)

plt.subplot(1, 2, 1)
scatter_plot(px, 'order_flow_imbalance', 60, 60)
plt.subplot(1, 2, 2)
scatter_plot(px, 'order_flow_imbalance', 300, 300)

plt.subplot(1, 2, 1)
scatter_plot(px, 'tick_move', 5, 5)
plt.subplot(1, 2, 2)
scatter_plot(px, 'tick_move', 60, 60)

second_list = [1, 2, 5, 10, 20, 30, 60, 120, 180, 300]
for sec in second_list:
    px = px[(px[utils.get_moving_column_name('tick_move', 0, sec)] <= 10) | np.isnan(px.tick_move_1_0)]
    px = px[(px[utils.get_moving_column_name('tick_move', sec, 0)] <= 10) | np.isnan(px.tick_move_1_0)]

oir_corr = xy_corr(px, second_list, 'order_imbalance_ratio')
ofi_corr = xy_corr(px, second_list, 'order_flow_imbalance')
autocorr = xy_corr(px, second_list, 'tick_move')
oir_corr.to_csv(os.path.join(research_path, 'oir_corr.csv'))
ofi_corr.to_csv(os.path.join(research_path, 'ofi_corr.csv'))
autocorr.to_csv(os.path.join(research_path, 'autocorr.csv'))

oir_ofi = xx_corr(px, second_list, 'order_imbalance_ratio', 'order_flow_imbalance')
oir_return = xx_corr(px, second_list, 'order_imbalance_ratio', 'tick_move')
ofi_return = xx_corr(px, second_list, 'order_flow_imbalance', 'tick_move')
oir_ofi.to_csv(os.path.join(research_path, 'oir_ofi_corr.csv'))
oir_return.to_csv(os.path.join(research_path, 'oir_return_corr.csv'))
ofi_return.to_csv(os.path.join(research_path, 'ofi_return_corr.csv'))
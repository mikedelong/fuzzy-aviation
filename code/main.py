import logging
from json import load
from os.path import isdir
from time import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_setting(arg_setting_name, arg_settings):
    if arg_setting_name in arg_settings.keys():
        result = arg_settings[arg_setting_name]
        return result
    else:
        logger.warning('required key %s is not in the settings. Quitting.' % arg_setting_name)
        quit()


def check_exists(arg_folder_name, arg_descriptor):
    folder_exists = isdir(arg_folder_name)
    if folder_exists:
        logger.debug('using %s as the %s folder' % (arg_folder_name, arg_descriptor))
    else:
        logger.warning('%s %s does not exist. Quitting.' % (arg_descriptor, arg_folder_name))
        quit()


if __name__ == '__main__':
    start_time = time()

    formatter = logging.Formatter('%(asctime)s : %(name)s :: %(levelname)s : %(message)s')
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    console_handler.setLevel(logging.DEBUG)
    logger.debug('started')

    with open('./settings-main.json') as settings_fp:
        settings = load(settings_fp)
        logger.debug(settings)

    input_folder = get_setting('input_folder', settings)
    check_exists(input_folder, 'input')
    input_file = get_setting('input_file', settings)
    full_input_file = input_folder + input_file
    logger.debug('loading data from input file %s' % full_input_file)
    data = pd.read_csv(full_input_file, sep='|')
    logger.debug('columns before stripping: %s' % list(data))
    data.columns = [item.strip() for item in data.columns]
    logger.debug('columns after stripping: %s' % list(data))
    logger.debug('initial data is %d rows x %d columns' % data.shape)
    data.replace('  ', np.nan, inplace=True)
    event_date = 'Event Date'
    data[event_date] = data[event_date].astype('datetime64')
    total_fatalities = 'Total Fatal Injuries'
    data[total_fatalities].replace(np.nan, 0, inplace=True)
    data[total_fatalities] = data[total_fatalities].astype('int')

    for key, value in data.dtypes.items():
        null_count = data[key].isnull().sum()
        logger.debug('column %s has type: %s and %d nulls' % (key, value, null_count))
    cutoff_year = 1979
    kind = 'bar'
    fatalities_data_to_plot = data[[event_date, total_fatalities]][data[event_date].dt.year > cutoff_year].set_index(
        [event_date]).resample('Y').sum()
    axes = fatalities_data_to_plot.plot(kind=kind)
    axes.set_xticklabels(pd.to_datetime(fatalities_data_to_plot.index).year.values)
    output_folder = get_setting('output_folder', settings)
    check_exists(output_folder, 'output folder')
    output_file = get_setting('dates_fatalities_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing dates-fatalities graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # let's get a count of accidents by year
    count = 'Count'
    data[count] = 1
    # we still need to cut off prior to 1980 for some reason
    accident_counts = data[[event_date, count]][data[event_date].dt.year > cutoff_year].set_index(
        [event_date]).resample('Y').sum()
    axes = accident_counts.plot(kind=kind)
    axes.set_xticklabels(pd.to_datetime(accident_counts.index).year.values)
    output_file = get_setting('event_counts_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing events counts graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # let's see if we have seasonality
    day_of_year = 'Day of Year'
    # todo fix this so we handle leap years correctly
    data[day_of_year] = data[event_date].dt.dayofyear
    day_counts = data[[day_of_year, count]].groupby(day_of_year).sum()
    day_counts.plot(linestyle='None', marker='.')
    output_file = get_setting('day_of_year_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing day of year graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # let's see if we have seasonality
    month = 'Month'
    data[month] = data[event_date].dt.month
    month_counts = data[[month, count]].groupby(month).sum()
    month_counts.plot(linestyle='None', marker='.')
    output_file = get_setting('month_count_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing month count graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    logger.debug('done')
    finish_time = time()
    elapsed_hours, elapsed_remainder = divmod(finish_time - start_time, 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_remainder, 60)
    logger.info("Time: {:0>2}:{:0>2}:{:05.2f}".format(int(elapsed_hours), int(elapsed_minutes), elapsed_seconds))
    console_handler.close()
    logger.removeHandler(console_handler)

import logging
from json import load
from os.path import isdir
from time import time

import matplotlib.pyplot as plt
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
    logger.debug('columns before stripping: %s' % data.columns.values)
    data.columns = [item.strip() for item in data.columns]
    logger.debug('columns after stripping: %s' % data.columns.values)
    logger.debug('initial data is %d rows x %d columns' % data.shape)
    event_date = 'Event Date'
    data[event_date] = data[event_date].astype('datetime64')
    total_fatalities = 'Total Fatal Injuries'
    data[total_fatalities].replace('  ', '0', inplace=True)
    data[total_fatalities] = data[total_fatalities].astype('int')

    for key, value in data.dtypes.items():
        logger.debug('column %s has type: %s' % (key, value))
    cutoff_year = 1979
    kind = 'bar'
    fatalities_data_to_plot = data[[event_date, total_fatalities]][data[event_date].dt.year > cutoff_year].set_index(
        [event_date]).resample('Y').sum()
    xticks = pd.to_datetime(fatalities_data_to_plot.index).year.values
    axes = fatalities_data_to_plot.plot(kind=kind)
    axes.set_xticklabels(xticks)
    output_folder = get_setting('output_folder', settings)
    check_exists(output_folder, 'output folder')
    output_file = get_setting('dates_fatalities_graph', settings)
    full_output_file = output_folder + output_folder + output_file
    logger.debug('writing dates-fatalities graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close()

    data['Count'] = 1
    accident_counts = data[[event_date, 'Count']][data[event_date].dt.year > cutoff_year].set_index(
        [event_date]).resample('Y').sum()
    xticks = pd.to_datetime(accident_counts.index).year.values
    axes = accident_counts.plot(kind=kind)
    axes.set_xticklabels(xticks)
    plt.show()


    logger.debug('done')
    finish_time = time()
    elapsed_hours, elapsed_remainder = divmod(finish_time - start_time, 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_remainder, 60)
    logger.info("Time: {:0>2}:{:0>2}:{:05.2f}".format(int(elapsed_hours), int(elapsed_minutes), elapsed_seconds))
    console_handler.close()
    logger.removeHandler(console_handler)

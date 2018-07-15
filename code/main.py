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


def strip_text(text):
    try:
        return text.strip()
    except AttributeError:
        return text


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
    logger.debug(data.columns)
    data.columns = [item.strip() for item in data.columns]
    logger.debug(data.columns)
    logger.debug(data.shape)
    logger.debug(data.dtypes)
    logger.debug(data.head(10))
    event_date = 'Event Date'
    total_fatalities = 'Total Fatal Injuries'
    data[event_date] = data[event_date].astype('datetime64')
    data = data[data[total_fatalities] != '  ']
    logger.debug(data.shape)
    data[total_fatalities] = data[total_fatalities].astype('int')
    logger.debug(data[total_fatalities].unique())
    t0 = data[data[total_fatalities] > 0]
    logger.debug(t0.shape)
    t0[[total_fatalities, event_date]].groupby(by=[event_date]).count().plot(kind="bar")
    plt.show()
    logger.debug('done')
    finish_time = time()
    elapsed_hours, elapsed_remainder = divmod(finish_time - start_time, 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_remainder, 60)
    logger.info("Time: {:0>2}:{:0>2}:{:05.2f}".format(int(elapsed_hours), int(elapsed_minutes), elapsed_seconds))
    console_handler.close()
    logger.removeHandler(console_handler)

import logging
from json import load
from os.path import isdir
from time import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import squarify


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
    integer_fields = get_setting('integer_fields', settings)

    # remove our empty column
    columns_to_delete = [item for item in list(data) if len(item) < 3]
    logger.debug('deleting %d columns because their names are too short' % len(columns_to_delete))
    data.drop(axis=1, inplace=True, labels=columns_to_delete)

    # we are choosing here to replace our NaNs with zeros
    # which is not the same thing as knowing they are actually zero
    for column in integer_fields:
        new_name = column + ' asint'
        logger.debug('column %s: we are replacing %d nans and converting the remaining values to integers' %
                     (column, data[column].isnull().sum()))
        data[new_name] = data[column].replace(np.nan, 0)
        data[new_name] = data[new_name].astype('int')

    for field, field_type in data.dtypes.items():
        if field_type == 'object':
            logger.debug('converting %s to string and stripping leading and trailing whitespace' % field)
            data[field] = data[field].str.strip()

    float_fields = get_setting('float_fields', settings)
    for field in float_fields:
        data[field] = data[field].astype('float64')

    unique_count_threshold = get_setting('unique_count_threshold', settings)
    for key, value in data.dtypes.items():
        null_count = data[key].isnull().sum()
        unique_count = data[key].nunique()
        logger.debug('column %s has type: %s, %d uniques, and %d nulls (%.1f%%)' %
                     (key, value, unique_count, null_count, 100 * float(null_count) / float(len(data))))
        if unique_count < unique_count_threshold:
            logger.debug('unique values are %s' % data[key].unique())
        else:
            logger.debug('some unique values are %s' % data[key].unique()[:unique_count_threshold])
    cutoff_year = 1979
    kind = 'bar'
    total_fatalities = 'Total Fatal Injuries'
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

    # seasonality by day of year
    day_of_year = 'Day of Year'
    data[day_of_year] = data[event_date].dt.dayofyear
    day_counts = data[[day_of_year, count]].groupby(day_of_year).sum()
    linestyle = 'None'
    marker = '.'
    day_counts.plot(linestyle=linestyle, marker=marker)
    output_file = get_setting('day_of_year_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing day of year graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # seasonality by date in year
    date_no_year = 'Date no year'
    data[date_no_year] = data[event_date].dt.strftime('%m-%d')
    date_counts = data[[date_no_year, count]].groupby(date_no_year).sum()
    linestyle = 'None'
    marker = '.'
    date_counts.plot(linestyle=linestyle, marker=marker)
    output_file = get_setting('date_no_year_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing date no year graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # seasonality by month
    month = 'Month'
    data[month] = data[event_date].dt.month
    month_counts = data[[month, count]].groupby(month).sum()
    linestyle = 'None'
    marker = '.'
    month_counts.plot(linestyle=linestyle, marker=marker)
    output_file = get_setting('month_count_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing month count graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # seasonality by day-of-month
    day_of_month = 'Day of Month'
    data[day_of_month] = data[event_date].dt.day
    day_counts = data[[day_of_month, count]].groupby(day_of_month).sum()
    linestyle = 'None'
    marker = '.'
    day_counts.plot(linestyle=linestyle, marker=marker)
    output_file = get_setting('day_count_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing day count graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # seasonality by day-of-week
    day_of_week = 'Day of Week'
    data[day_of_week] = data[event_date].dt.dayofweek
    day_counts = data[[day_of_week, count]].groupby(day_of_week).sum()
    linestyle = 'None'
    marker = '.'
    day_counts.plot(linestyle=linestyle, marker=marker)
    output_file = get_setting('day_of_week_count_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing day of week count graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # visualize crashes by experimental aircraft
    amateur_built = 'Amateur Built'
    amateur_built_value_counts = data[amateur_built].value_counts().to_dict()
    logger.debug('We have %d amateur-built, %d not amateur-built, and %d unknown' %
                 (amateur_built_value_counts['Yes'], amateur_built_value_counts['No'],
                  data[amateur_built].isnull().sum()))
    data[amateur_built].value_counts().plot(kind='bar')
    output_file = get_setting('amateur_built_count_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing amateur built count graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # let's try one simple facet
    # https://seaborn.pydata.org/generated/seaborn.FacetGrid.html
    year = 'Year'
    data[year] = data[event_date].dt.year
    amateur_built_graph = sns.FacetGrid(data[data[year] > cutoff_year][[amateur_built, year]],
                                        col=amateur_built).map(plt.hist, year)
    output_file = get_setting('amateur_built_year_histogram', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing amateur built year histogram to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    report_status = 'Report Status'
    report_status_graph = sns.FacetGrid(data[data[year] > cutoff_year][[report_status, year]], col=report_status).map(
        plt.hist, year)
    output_file = get_setting('report_status_year_histogram', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing report status year histogram to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    publication_date = 'Publication Date'
    data[publication_date] = data[publication_date].str.strip()
    with_publication_dates = data[data[publication_date].str.len() > 0].copy(deep=True)
    logger.debug(with_publication_dates.shape)
    with_publication_dates[publication_date] = with_publication_dates[publication_date].astype('datetime64')
    publication_wait = 'Publication Wait'
    with_publication_dates[publication_wait] = (
            with_publication_dates[publication_date] - with_publication_dates[event_date])
    log_publication_wait_days = 'Log Publication Wait Days'
    with_publication_dates[log_publication_wait_days] = \
        with_publication_dates[publication_wait].dt.days.apply(lambda x: 0 if x == 0 else np.log(x))
    with_publication_dates[log_publication_wait_days].hist()
    output_file = get_setting('log_publication_delay_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing log publication delay histogram to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    df = data.copy(deep=True)
    logger.debug('we are starting with %d rows' % len(df))
    for column in integer_fields:
        df = df[~df[column].isnull()]
        logger.debug('after removing the nulls from column %s we have %d rows (%.2f%%)' %
                     (column, len(df), 100 * float(len(df)) / float(len(data))))
    logger.debug('we are ending with %d rows' % len(df))

    plt.scatter(data['Longitude'], data['Latitude'], s=1)
    output_file = get_setting('event_map_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing event map to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    registration_number = 'Registration Number'
    values_to_plot = data[registration_number].str[0:2].value_counts().to_dict()
    squarify.plot(sizes=values_to_plot.values(), label=values_to_plot.keys())
    output_file = get_setting('registration_number_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing registration number graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    # todo add something for nulls/nans here
    weather_condition = 'Weather Condition'
    values_to_plot = data[weather_condition].value_counts().to_dict()
    squarify.plot(sizes=values_to_plot.values(), label=values_to_plot.keys())
    output_file = get_setting('weather_condition_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing weather condition graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    far_description = 'FAR Description'
    keys_to_keep = pd.DataFrame(data[far_description].value_counts()).index[:10].values
    logger.debug(data[far_description].value_counts().to_dict())
    logger.debug(sum(data[far_description].value_counts().to_dict().values()))
    logger.debug(keys_to_keep)
    far_description_aggregated = 'FAR Description Aggregated'
    data[far_description_aggregated] = data[far_description].apply(
        lambda x: 'Other' if x not in keys_to_keep and x != '' else x)
    values_to_plot = data[far_description_aggregated].value_counts().to_dict()
    logger.debug(values_to_plot)
    squarify.plot(sizes=values_to_plot.values(), label=values_to_plot.keys())
    output_file = get_setting('far_description_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing FAR description graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    phase = 'Broad Phase of Flight'
    values_to_plot = data[phase].value_counts().to_dict()
    squarify.plot(sizes=values_to_plot.values(), label=values_to_plot.keys())
    plt.title(phase)
    output_file = get_setting('phase_of_flight_graph', settings)
    full_output_file = output_folder + output_file
    logger.debug('writing phase of flight graph to %s' % full_output_file)
    plt.savefig(full_output_file)
    plt.close('all')

    logger.debug('done')
    finish_time = time()
    elapsed_hours, elapsed_remainder = divmod(finish_time - start_time, 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_remainder, 60)
    logger.info("Time: {:0>2}:{:0>2}:{:05.2f}".format(int(elapsed_hours), int(elapsed_minutes), elapsed_seconds))
    console_handler.close()
    logger.removeHandler(console_handler)

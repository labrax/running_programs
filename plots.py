from glob import glob
import pandas as pd
import numpy as np

import seaborn as sns
import matplotlib.pylab as plt

sns.set(rc={'figure.figsize':(14, 8)})

FILE_COLUMNS = ['date', 'time', 'pid', 'name', 'path', 'duration']
LIST_OF_FILES = sorted(glob('*app_use.csv'))

def add_weekday_to_col(x, sep=' '):
    return x + sep + pd.to_datetime(x, format='%Y-%m-%d').dt.day_name()

def check_type(x, i):
    if i in x:
        return True
    return False
    
def check_types_str(x):
    for check, name in {'YouTube': 'YouTube',
                        'Telegram': 'Telegram',
                        'Jupyter Notebook - Google Chrome': 'Jupyter Notebook',
                        'WhatsApp - Google Chrome': 'WhatsApp', 
                        'Google Chrome': 'Google Chrome',
                        'Mozilla Thunderbird': 'Reading e-mail',
                        'Thunderbird': 'Writing e-mail',
                        'Remote Desktop': 'Remote Desktop',
                        'Notepad++': 'Notepad++',
                        'Notepad': 'Notepad',
                        'Bitvise': 'SSH',
                        'Windows Default Lock Screen': 'Computer locked'}.items():
        if check_type(x, check):
            return name
    return x
    
def give_names(x):
    if type(x) is str:
        return check_types_str(x)
    return x

def prepare_df(file, required_columns=None, change_names=True, remove_nan_names=True):
    # identify the columns to be returned
    if required_columns is None:
        required_columns = ['name', 'duration']
    elif type(required_columns) is str:
        raise Exception('Required columns must be a list')
    
    # check if we are loading a single or multiple files
    if type(file) is str:
        df = pd.read_csv(file, 
                         names=FILE_COLUMNS, 
                         sep=';',
                         na_values=['None'])
    elif type(file) is list:
        df = pd.concat([pd.read_csv(i, 
                                    names=FILE_COLUMNS,
                                    sep=';',
                                    na_values=['None']) for i in file])
    
    # remove invalid data
    df = df[pd.to_numeric(df['duration'], errors='coerce').notnull()]
    
    if change_names:
        df['name'] = df['name'].apply(lambda x: give_names(x))
    
    # remove invalid names from the analysis
    if remove_nan_names:
        df = df[df['name'].notnull()]
    
    # set dtypes
    df = df.astype({'date': str,
                    'time': str,
                    'pid': float,
                    'name': str,
                    'path': str,
                    'duration': float})
    
    # transform datetime
    df['datetime'] = df.apply(lambda x: '{} {}'.format(x['date'], x['time']), axis=1)
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S')
    
    # only return needed columns
    return df[required_columns]

def prepare_df_for_name_search(file, name):
    df = prepare_df(file, required_columns=['name', 'duration', 'date'])
    
    # this will filter the data
    def _search_for_name(x):
        if type(name) is str and x == name:
            return True
        elif type(name) is list and x in name:
            return True
        return False
    
    df = df[df['name'].apply(lambda x: _search_for_name(x))]
    
    # if we have multiple elements we need to keep the names
    if type(name) is list:
        dgb = ['name', 'date']
    else:
        dgb = 'date'
    
    # groupby
    df = df.groupby(dgb)['duration'].sum().reset_index()
    
    return df

def prepare_df_barplot(file, min_duration=60, top=None):
    df = prepare_df(file, required_columns=['name', 'duration'])
        
    df = df.groupby('name')['duration'].sum().reset_index()
    df = df[df['duration'] > min_duration]
    
    df = df.sort_values('duration', ascending=False)
    
    # if asked only return the top elements (so don't pollute the chart)
    if top:
        return df.head(top)
    return df

def pretty_time_delta(seconds): # from: https://gist.github.com/thatalextaylor/7408395
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd%dh%dm%ds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%dh%dm%ds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%dm%ds' % (sign_string, minutes, seconds)
    else:
        return '%s%ds' % (sign_string, seconds)

# lineplots
def _plot_for_program_single(data, program_name=None, show_plot=False):
    data['duration'] = data['duration']/3600
    g = sns.lineplot(data=data, 
                     x="date",
                     y="duration",
                     linestyle="dashed")
    g.set_ylabel('Duration (h)')
    g.set_xlabel('Date')

    if program_name is not None:
        g.set_title('{} use'.format(program_name))
        
    plt.xticks(rotation=90)
    if show_plot:
        plt.show()
    return plt


def _plot_for_program_multiple(data):
    data['duration'] = data['duration']/3600
    g = sns.lineplot(data=data, 
                     x="date",
                     y="duration",
                     hue='name',
                     linestyle="dashed")
    g.set_ylabel('Duration (h)')
    g.set_xlabel('Date')

    g.set_title('Multiple programs use')
        
    plt.xticks(rotation=90)
    plt.show()


def plot_for_program(data, program_name=None):
    if 'name' in data.columns.values:
        _plot_for_program_multiple(data)
    else:
        _plot_for_program_single(data, program_name)
        
# barplots
def plot_for_period(data, period_name=None, show_plot=False):
    g = sns.barplot(data=data, x='name', y='duration')
    g.set_xlabel('Program name')
    g.set_ylabel('Duration (s)')
    if period_name is not None:
        g.set_title('Programs open - {}'.format(period_name))
    for p, row in zip(g.patches, data.iterrows()):
        g.annotate(pretty_time_delta(row[1].duration), 
                       (p.get_x() + p.get_width() / 2., p.get_height()), 
                       ha = 'center', va = 'center', 
                       size=15,
                       xytext = (0, 12), 
                       textcoords = 'offset points')
    plt.xticks(rotation=90)
    if show_plot:
        plt.show()
    return plt
    
# plot uptime lines
def plot_uptime(data, period_name=None, xticksrotation=True, ignore_lockscreen=True, lockscreen_name='Windows Default Lock Screen', add_weekday=False, show_plot=False):
    if ignore_lockscreen:
        data = data[data['name'] != lockscreen_name]

    data['day'] = data['datetime'].dt.strftime('%Y-%m-%d')
    data = data.groupby('day')['duration'].sum().reset_index()
    data['duration'] = data['duration']/3600

    if add_weekday:
        data['day'] = add_weekday_to_col(data['day'])
    
    g = sns.lineplot(data=data, 
                     x='day', 
                     y='duration',
                     linestyle="dashed",
                     color='blue')
    g.set_ylabel('Uptime (h)')
    g.set_xlabel('Date')

    g.set_yticks(range(0, 25, 2))
    g.set_yticklabels([str(i) for i in range(0, 25, 2)])

    if period_name is not None:
        g.set_title('Uptime - {}'.format(period_name))
    else:
        g.set_title('Uptime')

    if xticksrotation:
        plt.xticks(rotation=90)

    if show_plot:
        plt.show()
    return plt

# jitter plots
def plot_jitter_day(data, period_name=None, show_plot=False):
    data['hour'] = data['datetime'].dt.strftime('%H')
    data = data.groupby('hour')['name'].count().reset_index()
    data['name'] = data['name'].astype(float)

    g = sns.lineplot(data=data, 
                     x='hour',
                     y='name',
                     linestyle="dashed",
                     color='black')
    g.set_ylabel('Number of changes')
    g.set_xlabel('Hour')

    if period_name is not None:
        g.set_title('Number of program changes - {}'.format(period_name))
    else:
        g.set_title('Number of program changes')

    if show_plot:
        plt.show()
    return plt

def plot_jitter_multiple_day(data, period_name=None, xticksrotation=False, show_plot=False):
    data['day'] = data['datetime'].dt.strftime('%Y-%m-%d')
    
    # obtain the day duration
    ma = data.groupby('day')['datetime'].max().reset_index().rename(columns={'datetime': 'max'})
    mi = data.groupby('day')['datetime'].min().reset_index().rename(columns={'datetime': 'min'})
    day_duration = ma.merge(mi,
                            on = 'day')
    day_duration['delta_h'] = (day_duration['max'] - day_duration['min']) / pd.Timedelta(hours=1)
    
    # jitter
    data = data.groupby('day')['name'].count().reset_index()
    data['name'] = data['name'].astype(float)
   
    # merge and calculate average
    data = data.merge(day_duration[['day', 'delta_h']],
                      on='day')
    data['name'] = data['name']/data['delta_h']
    
    g = sns.lineplot(data=data, 
                     x='day', 
                     y='name',
                     linestyle="dashed",
                     color='black')
    g.set_ylabel('Number of changes (changes/hours)')
    g.set_xlabel('Date')

    if period_name is not None:
        g.set_title('Number of program changes - {}'.format(period_name))
    else:
        g.set_title('Number of program changes')

    if xticksrotation:
        plt.xticks(rotation=90)

    if show_plot:
        plt.show()
    return plt

if __name__ == '__main__':
    import subprocess
    import webbrowser
    
    subprocess.run(["python", "-m", "jupyter", "nbconvert", "--execute", "--to", "html", "20210611_jupyter_plots.ipynb"])
    webbrowser.open("20210611_jupyter_plots.html")
    
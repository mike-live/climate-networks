from datetime import timedelta, datetime
import math


def get_considered_years(options):
    start_year = int(options['start_time_plot'][0:4])
    end_year = int(options['end_time_plot'][0:4])
    years = list(range(start_year, end_year + 1))
    return years
    

def get_considered_times(options):
    considered_times = []

    start_date = datetime.strptime(options['start_time_plot'], '%Y.%m.%d %H:%M:%S')
    end_date = datetime.strptime(options['end_time_plot'], '%Y.%m.%d %H:%M:%S')

    d = start_date
    delta = timedelta(hours = options['step_time_in_hours'])
    while d <= end_date:
        considered_times.append(d.strftime("%Y.%m.%d %H:%M:%S"))
        d += delta
    return considered_times


def get_xyticks_for_map(west, east, south, north):
    s = math.ceil(west)
    e = math.floor(east)
    x_step = round((e - s) / 5)
    xticks = [s, s + x_step, s + 2*x_step, s + 3*x_step, s + 4*x_step, e]
    
    s = math.ceil(south)
    e = math.floor(north)
    y_step = round((e - s) / 5)
    yticks = [s, s + y_step, s + 2*y_step, s + 3*y_step, s + 4*y_step, e]
    
    return xticks, yticks


def get_xticks_for_GCC(times, param):
    if param == 'none':
        years = range(int(times[0][0:4]), int(times[len(times)-1][0:4]) + 1, 4)
        inds = []
        for year in years:
            for t in times:
                if str(year) in t:
                    inds.append(times.index(t))
                    break
        return inds, years
    
    elif param == 'years':
        inds = []
        for moth in range(1, 13):
            for t in times:
                if t[5:7] == str(moth).rjust(2, '0'):
                    inds.append(times.index(t))
                    break
        return inds, ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    elif param == 'months':
        inds = []
        label = []
        for day in range(1, 32):
            day = str(day).rjust(2, '0')
            for t in times:
                if t[8:10] == day:
                    inds.append(times.index(t))
                    label.append(day)
                    break
        return inds, label


def get_run_time_images_dir_name(config):
    start_time_plot = datetime.strptime(config.map_plot_options['start_time_plot'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d-%H-%M-%S')
    end_time_plot = datetime.strptime(config.map_plot_options['end_time_plot'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d-%H-%M-%S')
    
    if config.metric_dimension[config.map_plot_options['metric_name']] == '2D':
        run_time_dir_name = config.map_plot_options['metric_name'] + '_' + start_time_plot + '_' + end_time_plot + '_' + \
            str(config.map_plot_options['step_time_in_hours']) + 'h'
    elif config.metric_dimension[config.map_plot_options['metric_name']] == '1D':
        run_time_dir_name = config.map_plot_options['metric_name'] + '_' + start_time_plot[0:10] + '_' + end_time_plot[0:10] + '_' + \
            str(config.map_plot_options['time_split'])
    return run_time_dir_name

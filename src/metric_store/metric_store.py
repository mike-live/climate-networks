import numpy as np

def filter_by_prefix(metric_dict, prefix):
    if type(prefix) is str:
        prefix = [prefix]
    metric_dict = { 
        metric_name: value 
            for metric_name, value in metric_dict.items() 
                if any(metric_name.startswith(pref) for pref in prefix)
    }
    return metric_dict

def add_metric(config, metric_name, metric_file_name):
    metric_names = get_metric_names(config)
    metric_names[metric_name] = metric_file_name

    metrics_dir = config.metrics['work_dir'] / config.metrics['output_metrics_dir']
    metric_names_file_name = metrics_dir / config.metrics['metric_names_file_name']
    np.save(metric_names_file_name, metric_names)

def get_metric_names(config, prefix = ''):
    metrics_dir = config.metrics['work_dir'] / config.metrics['output_metrics_dir']
    metric_names_file_name = metrics_dir / config.metrics['metric_names_file_name']
    if metric_names_file_name.exists():
        metric_names = np.load(metric_names_file_name, allow_pickle=True).item()
    else:
        metric_names = {}
    metric_names = filter_by_prefix(metric_names, prefix)
    return metric_names

def save_metric(config, metric, metric_name):
    metrics_dir = config.metrics['work_dir'] / config.metrics['output_metrics_dir']
    metric_file_name = metric_name + '.npy'
    metric_path = metrics_dir / metric_file_name
    metric_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(metric_path, metric)

    add_metric(config, metric_name, metric_file_name)

def save_metrics(config, metrics):
    for metric_name, metric in metrics.items():
        metric_file_name = save_metric(config, metric, metric_name)
    
def load_metric(config, metric_name):
    metrics_dir = config.metrics['work_dir'] / config.metrics['output_metrics_dir']
    metrics_file_name = metrics_dir / (str(metric_name) + '.npy')
    metric = np.load(metrics_file_name, allow_pickle=True)
    return metric

def load_metrics(config, prefix = ''):
    metric_names = get_metric_names(config, prefix)
    metrics = {}
    for metric_name in metric_names:
        metric = load_metric(config, metric_name)
        metrics[metric_name] = metric
    return metrics

class Metrics():
    def __init__(self, config, prefix=[], metric_names=None):
        self.config = config
        self.prefix = prefix
        self.metric_names = metric_names

        prefix_metric_names = list(get_metric_names(config, prefix).keys())
        self.selected_metric_names = list(set(metric_names + prefix_metric_names))
    
    def __iter__(self):
        for metric_name in self.selected_metric_names:
            self.config.metrics_plot_options['metric_name'] = metric_name
            metric = load_metric(self.config, metric_name)
            yield metric_name, metric
        return self
    

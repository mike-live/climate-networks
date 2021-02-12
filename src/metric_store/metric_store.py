import numpy as np

def filter_by_prefix(metric_dict, prefix):
    metric_dict = { metric_name: value for metric_name, value in metric_dict.items() if metric_name.startswith(prefix) }
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
    print(metric_names_file_name)
    if metric_names_file_name.exists():
        metric_names = np.load(metric_names_file_name, allow_pickle=True).item()
        print(type(metric_names))
        print(len(metric_names))
    else:
        metric_names = {}
    print(metric_names)
    metric_names = filter_by_prefix(metric_names, prefix)
    print(metric_names)
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
    metrics_file_name = metrics_dir / (metric_name + '.npy')
    metric = np.load(metrics_file_name)
    return metric

def load_metrics(config, prefix = ''):
    metric_names = get_metric_names(config, prefix)
    metrics = {}
    for metric_name in metric_names:
        metric = load_metric(config, metric_name)
        metrics[metric_name] = metric
    return metrics

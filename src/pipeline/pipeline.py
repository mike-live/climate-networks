config_name = "config.py"

def download_data(config):
    pass

def load_data(config):
    pass    

def make_corr_networks(config):
    from ..corr_network import 
    data, latitutdes, longitudes, timeticks = load_data(config)

    pass

def compute_metrics(config):
    pass

def plot_2d_metrics(config):
    pass

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                    help='an integer for the accumulator')
    parser.add_argument('download', dest='need_download', action='store_const',
                    const=True, default=False,
                    help='download era5 data and preprocess')
    parser.add_argument('compute correlations', dest='need_corr_network', action='store_const',
                    const=True, default=False,
                    help='compute correlation matricies')
    parser.add_argument('compute metrics', dest='need_metrics', action='store_const',
                    const=True, default=False,
                    help='compute network metrics')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    config = load_config(config_name)
    if args.need_download:
        download_data(config)

    if args.need_corr_network:
        make_corr_networks(config)

    if args.need_metrics:
        compute_metrics(config)

    if args.need_plot:
        plot_2d_metrics(config)
        

if __name__ == "__main__":
    main()
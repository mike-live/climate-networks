import numpy as np
import pandas as pd


def get_g_test_full_results(file_name, thrs):
    results = {}
    for thr in thrs:
        results[thr] = pd.read_excel(file_name, sheet_name=thr, header=None, engine='openpyxl')
    return results


def parse_g_test_full_results(results, thrs):
    parse_results = {}
    for thr in thrs:
        df_thr = results[thr]
        step = 10  # as many lines in a dataframe are allocated to one metric
        for i in range(0, len(df_thr), step+1):
            df_metric = df_thr.iloc[i:i+step]
            classification_metrics = {'prob_for_metric': df_metric[df_metric[0] == 'prob_for_metric'][1].values[0],
                                      'g_statistic': float(df_metric[df_metric[0] == 'g-statistic'][1].values[0]),
                                      'f1_score': float(df_metric[df_metric[0] == 'f1_score'][1].values[0]),
                                      'balanced_acc': float(df_metric[df_metric[0] == 'balanced_acc'][1].values[0]),
                                      'matthews_coef': float(df_metric[df_metric[0] == 'matthews_coef'][1].values[0])}
            parse_results[(df_metric[df_metric[0] == 'metric_name'][1].values[0], thr)] = classification_metrics
    return parse_results


def get_optimal_results_with_parameter(results, metric_names, parameter):
    optimal_results = dict.fromkeys(metric_names, {'prob_for_metric': '', 'g_statistic': -999999, 'f1_score': -999999,
                                                   'balanced_acc': -999999, 'matthews_coef': -999999})
    for key, value in results.items():
        if (not np.isnan(value[parameter])) and (value[parameter] > optimal_results[key[0]][parameter]):
            optimal_results[key[0]] = {'prob_for_metric': value['prob_for_metric'], 'g_statistic': value['g_statistic'],
                                       'f1_score': value['f1_score'], 'balanced_acc': value['balanced_acc'],
                                        'matthews_coef': value['matthews_coef']}

    return optimal_results


def save_optimal_results_for_g_test(opt_res_dict, file_name):
    df_res = pd.DataFrame(columns=['metric_name', 'prob_for_metric', 'g_statistic', 'f1_score', 'balanced_acc',
                                   'matthews_coef'])
    for metric_name, internal_dict in opt_res_dict.items():
        df_res.loc[len(df_res)] = [metric_name] + [v for k, v in opt_res_dict[metric_name].items()]
    df_res.to_excel(file_name, index=False)


def optimal_g_test_results(results, metric_names, path_name):
    optimal_results_for_g_stat = get_optimal_results_with_parameter(results, metric_names, 'g_statistic')
    optimal_results_for_f1 = get_optimal_results_with_parameter(results, metric_names, 'f1_score')
    optimal_results_for_bacc = get_optimal_results_with_parameter(results, metric_names, 'balanced_acc')
    optimal_results_for_mcc = get_optimal_results_with_parameter(results, metric_names, 'matthews_coef')

    save_optimal_results_for_g_test(optimal_results_for_g_stat, path_name / f"g_test_optimal_g_statistic.xlsx")
    save_optimal_results_for_g_test(optimal_results_for_f1, path_name / f"g_test_optimal_f1_score.xlsx")
    save_optimal_results_for_g_test(optimal_results_for_bacc, path_name / f"g_test_optimal_balanced_acc.xlsx")
    save_optimal_results_for_g_test(optimal_results_for_mcc, path_name / f"g_test_optimal_matthews_coef.xlsx")

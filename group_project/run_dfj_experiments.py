"""
Run Dantzig-Fulkerson-Johnson (DFJ) experiments on all TSP instances
Generates CSV file with raw data for analysis in Jupyter notebook
"""

import pandas as pd
from pathlib import Path
from tsp_dfj_solver import solve_instance


def run_all_experiments(data_folder="./data", sizes=[15, 18, 20]):
    """Run experiments and collect raw data"""
    data_path = Path(data_folder)
    structures = ['grid', 'random', 'clustered', 'hub_spoke']
    all_results = []

    for n in sizes:
        for structure in structures:
            for instance_idx in range(10):
                filename = f"dist_n{n}_{structure}_i{instance_idx}.csv"
                filepath = data_path / filename
                result = solve_instance(str(filepath))
                result['structure'] = structure
                result['instance_idx'] = instance_idx
                all_results.append(result)

    # Create DataFrame with organized columns
    df = pd.DataFrame(all_results)
    column_order = ['n', 'structure', 'instance_idx', 'instance',
                   'IP_obj', 'LP_obj', 'gap_absolute', 'gap_percent',
                   'cv', 'ip_solve_time', 'lp_solve_time', 'total_solve_time']
    df = df[column_order]
    return df


if __name__ == "__main__":
    # Run experiments on all problem sizes: n=15, 18, 20, save the result into dfj_results.csv
    results_df = run_all_experiments(sizes=[15, 18, 20])
    output_file = "dfj_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"Experiments completed. Results saved to: {output_file}")
    print(f"Total instances: {len(results_df)}")

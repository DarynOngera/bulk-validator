import pandas as pd
import json
from collections import Counter, defaultdict
from typing import List, Dict

def error_breakdown_by_field(invalid_df: pd.DataFrame) -> Dict:
    field_counter = defaultdict(int)
    error_examples = defaultdict(list)
    for err_list in invalid_df['errors']:
        for err in err_list:
            field = err.get('type', 'unknown')
            field_counter[field] += 1
            if len(error_examples[field]) < 3:
                error_examples[field].append(err.get('message', ''))
    return {
        field: {
            'count': count,
            'examples': error_examples[field]
        }
        for field, count in field_counter.items()
    }

def per_bank_stats(df: pd.DataFrame) -> Dict:
    stats = {}
    for bank, group in df.groupby('bank_code'):
        total = len(group)
        valid = (group['status'] == 'Valid').sum()
        invalid = (group['status'] == 'Invalid').sum()
        errors = Counter()
        for err_list in group[group['status']=='Invalid']['errors']:
            for err in err_list:
                errors[err.get('type','unknown')] += 1
        stats[bank] = {
            'total': total,
            'valid': int(valid),
            'invalid': int(invalid),
            'error_types': dict(errors)
        }
    return stats

def write_outputs(valid_df, invalid_df, summary, base_filename, formats=['csv','json','xlsx']):
    paths = {}
    if 'csv' in formats:
        valid_path = f'output/{base_filename}_valid.csv'
        invalid_path = f'output/{base_filename}_invalid.csv'
        valid_df.to_csv(valid_path, index=False)
        invalid_df.to_csv(invalid_path, index=False)
        paths['valid_csv'] = valid_path
        paths['invalid_csv'] = invalid_path
    if 'json' in formats:
        valid_path = f'output/{base_filename}_valid.json'
        invalid_path = f'output/{base_filename}_invalid.json'
        valid_df.to_json(valid_path, orient='records', indent=2)
        invalid_df.to_json(invalid_path, orient='records', indent=2)
        paths['valid_json'] = valid_path
        paths['invalid_json'] = invalid_path
    if 'xlsx' in formats:
        valid_path = f'output/{base_filename}_valid.xlsx'
        invalid_path = f'output/{base_filename}_invalid.xlsx'
        valid_df.to_excel(valid_path, index=False)
        invalid_df.to_excel(invalid_path, index=False)
        paths['valid_xlsx'] = valid_path
        paths['invalid_xlsx'] = invalid_path
    # Write summary
    summary_json = f'output/{base_filename}_summary.json'
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    paths['summary_json'] = summary_json
    return paths

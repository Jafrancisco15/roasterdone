import pandas as pd, json
from pathlib import Path
from datetime import datetime

def export_session_csv(path, samples, events, meta):
    out=Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Combined file with both samples and events in chronological order
    combined_rows=[]
    for s in samples:
        row={"row_type":"sample"}
        row.update(s)
        combined_rows.append(row)
    for e in events:
        row={"row_type":"event"}
        row.update(e)
        combined_rows.append(row)
    combined=pd.DataFrame(combined_rows)
    if not combined.empty and "t_sec" in combined.columns:
        combined=combined.sort_values(by="t_sec")
    combined.to_csv(out.with_suffix('.csv'), index=False)

    # Backwards-compatible exports for existing workflows
    pd.DataFrame(samples).to_csv(out.with_suffix('.samples.csv'), index=False)
    pd.DataFrame(events).to_csv(out.with_suffix('.events.csv'), index=False)
    out.with_suffix('.meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(out.with_suffix('.csv'))

def timestamp_slug():
    return datetime.now().strftime('%Y%m%d-%H%M%S')

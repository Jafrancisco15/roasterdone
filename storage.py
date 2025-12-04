import pandas as pd, json
from pathlib import Path
from datetime import datetime

def export_session_csv(path, samples, events, meta):
    out=Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(samples).to_csv(out.with_suffix('.samples.csv'), index=False)
    pd.DataFrame(events).to_csv(out.with_suffix('.events.csv'), index=False)
    out.with_suffix('.meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(out)

def timestamp_slug():
    return datetime.now().strftime('%Y%m%d-%H%M%S')

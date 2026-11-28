import json
from pathlib import Path

from app.main import app


if __name__ == '__main__':
    output = Path('pages/api/openapi.json')
    with output.open('w', encoding='utf-8') as handle:
        json.dump(app.openapi(), handle, ensure_ascii=False, indent=2)
        handle.write('\n')

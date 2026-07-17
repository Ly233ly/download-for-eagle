from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from idm_eagle_bridge.main import main
from idm_eagle_bridge.hook import main as hook_main


if len(sys.argv) >= 2 and sys.argv[1] == "--receive":
    raise SystemExit(hook_main(sys.argv[2:]))
raise SystemExit(main(sys.argv[1:]))

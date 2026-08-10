from pathlib import Path
import sys


# Make `python examples/basic.py` work from a source checkout without requiring
# the project to be installed as a package first.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dxgi_gpu_enum import DxgiGpuEnumerator  # noqa: E402


for gpu in DxgiGpuEnumerator().enumerate():
    print(
        f"{gpu.name}: {gpu.dedicated_video_memory_gib:.2f} GiB dedicated, "
        f"{gpu.vendor_id:04X}:{gpu.device_id:04X}"
    )

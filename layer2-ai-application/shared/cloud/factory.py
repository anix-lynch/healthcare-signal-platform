"""CloudProvider factory — env-driven selection.

    export CLOUD_PROVIDER=vertex   # or azure | aws
    provider = get_provider()
"""

import os

from .adapter import CloudProvider


def get_provider() -> CloudProvider:
    name = os.environ.get("CLOUD_PROVIDER", "vertex").lower()

    if name == "azure":
        from .azure_provider import AzureProvider
        return AzureProvider()
    if name == "vertex":
        from .vertex_provider import VertexProvider
        return VertexProvider()
    if name == "aws":
        from .aws_provider import AWSProvider
        return AWSProvider()

    raise ValueError(f"Unknown CLOUD_PROVIDER: {name!r}. Use azure|vertex|aws.")

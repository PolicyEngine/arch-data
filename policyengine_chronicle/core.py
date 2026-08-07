"""Chronicle fact schema compatibility module.

New consumers should import from :mod:`policyengine_chronicle.core`; the objects
are re-exported from :mod:`chronicle.core` until the historical namespace is retired.
"""

from chronicle.core import *  # noqa: F403

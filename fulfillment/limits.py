"""Request limits for one box recommendation.

The packer searches placements. These caps keep a single web request from
asking it to pack a pallet.
"""

MAX_LINE_QUANTITY = 30
MAX_TOTAL_UNITS = 30

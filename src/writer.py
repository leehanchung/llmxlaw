import json
import jinja2


TEMPLATE = """
                           SUPERIOR COURT OF CALIFORNIA
                           COUNTY OF SANTA CLARA


-----------------------------------------
{plantiff},
    Plantiff

    v.

{defendent},
    Defendent
-----------------------------------------

Introduction
{summary}

CLAIMS
{claims}

FACTUAL BACKGROUND
{facts}

RELIEF REQUESTED
{relief}
"""


from utils.path_utils import absolute_path

import os



database_path = absolute_path(
    os.path.join(__file__, os.pardir, os.pardir, "db")
)


db = dict()

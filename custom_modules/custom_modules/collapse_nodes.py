from promg import DatabaseConnection
from promg import Performance
from custom_modules.custom_queries.collapse_nodes import CollapseNodeQueryLibrary as ql


class CollapseNodes:
    def __init__(self):
        self.connection = DatabaseConnection()

    @Performance.track()
    def collapse_nodes(self):
        self.connection.exec_query(ql.get_collapse_node_query)


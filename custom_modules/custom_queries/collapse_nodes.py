from dataclasses import dataclass
from typing import Dict, Optional

from string import Template

from promg import Query


class CollapseNodeQueryLibrary:
    @staticmethod
    def get_collapse_node_query():
        query_str = '''
            MATCH (a1:Activity)-[:FROM]->(q:Qualifier)-[:TO]->(et:EntityType)
            WITH a1, et, q, toUpper(q.qualifier) as qualifier
            CALL apoc.create.relationship(a1, qualifier, {}, et)
            YIELD rel
            DETACH DELETE q
        '''

        return Query(query_str=query_str)

from ekg_creator.database_managers.db_connection import DatabaseConnection
from datetime import datetime

def add_df_a_relations(db_connection: DatabaseConnection, relations: tuple) -> None:
    '''
    :param db_connection: connection to the neo4j database
    :param relations: nested tuple of the nodes that need to be connected by a df_a relation, order matters

    '''
    for a1, a2 in relations:
        db_connection._exec_query(f"MATCH (a1:Activity {{name:'{a1}'}}) MATCH (a2:Activity {{name:'{a2}'}}) CREATE (a1)-[:DF_A]->(a2)")


def save_evaluation(db_connection: DatabaseConnection, keystring: str = '', output_path: str = '') -> None:
    '''
    :param db_connection: connection to the neo4j database
    :param output_path: folder to save the result in
    :param keystring: A string to write in front of the result

    Based on the graph database as it is currently, counts the number of total traces (number of box entity nodes) as well as the
    number of traces containing a DF_BOX relation without a corresponing DF_A relation. Saves the percentage of complete traces, i.e.
    traces where every DF_BOX relation has a corresponing DF_BOX relation.
    '''
    query_all_traces = '''MATCH (b_all:Box) RETURN count(b_all)'''
    query_incompl_traces = '''MATCH (e1:Event)-[:DF_BOX]->(e2:Event)
    MATCH (e1:Event)-[:OBSERVED]->(a1:Activity)
    MATCH (e2:Event)-[:OBSERVED]->(a2:Activity)
    MATCH (a1),(a2) WHERE NOT (a1)-[:DF_A]->(a2)
    MATCH (e1:Event)-[:CORR]->(b_incompl:Box) WHERE (e2:Event)-[:CORR]->(b_incompl:Box)
    RETURN count(DISTINCT b_incompl)
    '''

    query_all_dfb = '''MATCH (:Event)-[dfb:DF_BOX]->(:Event) RETURN count(dfb)'''
    query_cor_dfb = '''MATCH (e1:Event)-[dfb:DF_BOX]->(e2:Event)
    MATCH (e1)-[:OBSERVED]->(a1:Activity)
    MATCH (e2)-[:OBSERVED]->(a2:Activity)
    MATCH (a1)-[dfa:DF_A]->(a2)
    RETURN count(dfa)'''

    all_traces = list(db_connection._exec_query(query_all_traces)[0].values())[0]
    incompl_traces = list(db_connection._exec_query(query_incompl_traces)[0].values())[0]

    all_dfb = list(db_connection._exec_query(query_all_dfb)[0].values())[0]
    cor_dfb = list(db_connection._exec_query(query_cor_dfb)[0].values())[0]

    with open(output_path+'result.txt','a') as f:
        f.write(keystring+': '+str(100-(incompl_traces/all_traces*100))+"%, "+str(cor_dfb/all_dfb*100)+"%, ")


def save_runtime(start_time: datetime, end_time: datetime, keystring:str = '', output_path:str = '') -> None:
    '''
    :param start_time: time the program started
    :param end_time: time the program ended
    :param output_path: folder where the 'result.txt' file resides
    '''
    runtime = end_time - start_time
    
    with open(output_path+'result.txt','a') as f:
        f.write(keystring+f': {runtime}\n')
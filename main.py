import os
from pathlib import Path
import sys
from datetime import datetime

from ekg_creator.data_managers.interpreters import Interpreter
from ekg_creator.data_managers.semantic_header import SemanticHeader
from ekg_creator.database_managers.EventKnowledgeGraph import EventKnowledgeGraph
from ekg_creator.database_managers.db_connection import DatabaseConnection
from ekg_creator.data_managers.datastructures import ImportedDataStructures
from ekg_creator.utilities.performance_handling import Performance
from ekg_creator.database_managers import authentication

import help_functions as f

connection = authentication.connections_map[authentication.Connections.LOCAL]

# region ADDED IN REPLICATION
allowed_args = ['Short', 'ExampleCheck','PerformanceCheck']

if len(sys.argv) == 1:
    argv = ''
elif sys.argv[1] not in allowed_args:
    raise Exception(f"{sys.argv[1]} not recognized as valid argument, please choose from the following: {allowed_args}")
else:
    argv = sys.argv[1]

if argv=='ExampleCheck':
    relations = (('LoadAL','LoadFS'),
                 ('LoadFS','Fill'),
                 ('Fill','UnloadFS'),
                 ('UnloadFS','LoadSS'),
                 ('LoadSS','Seal'),
                 ('Seal','UnloadSS'),
                 ('UnloadSS','UnloadAL'))
    
if argv=='PerformanceCheck':
    relations = (('LoadAL','LoadFS'),
                 ('LoadFS','Open'),
                 ('Open','Fill'),
                 ('Fill','UnloadFS'),
                 ('UnloadFS','LoadSS'),
                 ('LoadSS','Close'),
                 ('Close','Seal'),
                 ('Seal','UnloadSS'),
                 ('UnloadSS','UnloadAL'))
# endregion

dataset_name = f'BoxProcess{argv}'
semantic_header_path = Path(f'json_files/{dataset_name}.json')

query_interpreter = Interpreter("Cypher")
semantic_header = SemanticHeader.create_semantic_header(semantic_header_path, query_interpreter)
perf_path = os.path.join("", "perf", dataset_name, f"{dataset_name}Performance.csv")
number_of_steps = None

ds_path = Path(f'json_files/{dataset_name}_DS.json')
datastructures = ImportedDataStructures(ds_path)

# several steps of import, each can be switch on/off
step_clear_db = True
step_populate_graph = True
verbose = False  # print the used queries

db_connection = DatabaseConnection(db_name=connection.user, uri=connection.uri, user=connection.user,
                                   password=connection.password, verbose=verbose)


def create_graph_instance(perf: Performance) -> EventKnowledgeGraph:
    """
    Creates an instance of an EventKnowledgeGraph
    @return: returns an EventKnowledgeGraph
    """

    return EventKnowledgeGraph(db_connection=db_connection, db_name=connection.user,
                               specification_of_data_structures=datastructures, semantic_header=semantic_header,
                               perf=perf,
                               use_preprocessed_files=False)


def clear_graph(graph: EventKnowledgeGraph, perf: Performance) -> None:
    """
    # delete all nodes and relations in the graph to start fresh
    @param graph: EventKnowledgeGraph
    @param perf: Performance
    @return: None
    """

    print("Clearing DB...")
    graph.clear_db()
    perf.finished_step(log_message=f"Cleared DB")


def populate_graph(graph: EventKnowledgeGraph, perf: Performance):
    # Import the event data as Event nodes and location data as Location nodes and entity types from activity records as
    # region EntityTypes
    graph.import_data()
    perf.finished_step(log_message=f"(:Event), (:Location) and (:EntityType) nodes done")

    # for each entity, we add the entity nodes to graph and correlate them (if possible) to the corresponding events
    graph.create_entities_by_nodes()
    perf.finished_step(log_message=f"(:Entity) nodes done")

    graph.correlate_events_to_entities()
    perf.finished_step(log_message=f"[:CORR] edges done")

    # create the classes
    graph.create_classes()
    perf.finished_step(log_message=f"(:Activity) nodes done")

    # create [:PART_OF] and [:AT] relation
    graph.create_entity_relations_using_nodes()
    perf.finished_step(log_message=f"[:REL] edges done")

    graph.create_entity_relations_using_relations(relation_types=["LOADS", "UNLOADS", "ACTS_ON"])
    # endregion

    if argv!='Short':
        # region Infer missing information
        # rule c, both for preceding load events and succeeding unload events
        graph.infer_items_propagate_upwards_multiple_levels(entity_type="Box", is_load=True)
        graph.infer_items_propagate_upwards_multiple_levels(entity_type="Box", is_load=False)
        graph.create_entity_relations_using_relations(relation_types=["AT_POS"])
        # rule d
        graph.infer_items_propagate_downwards_multiple_level_w_batching(entity_type="Box",
                                                                        relative_position_type="BatchPosition")
        # rule b
        graph.infer_items_propagate_downwards_one_level(entity_type="Box")

        # endregion

        # region Complete EKG creation, add DF relations after missing correlations are inferred
        graph.create_df_edges()
        perf.finished_step(log_message=f"[:DF] edges done")
        # endregion

        # region ADDED IN REPLICATION, apply evaluation and save to result.txt
        if argv!='':
            f.add_df_a_relations(db_connection, relations)
            f.save_evaluation(db_connection,f"{argv}, {datetime.now()}")
        # endregion


def main() -> None:
    """
    Main function, read all the logs, clear and create the graph, perform checks
    @return: None
    """
    start_time = datetime.now()
    # performance class to measure performance
    perf = Performance(perf_path, number_of_steps=number_of_steps)
    graph = create_graph_instance(perf)

    if step_clear_db:
        clear_graph(graph=graph, perf=perf)

    if step_populate_graph:
        populate_graph(graph=graph, perf=perf)

    perf.finish()
    perf.save()

    graph.print_statistics()

    db_connection.close_connection()

    end_time = datetime.now()

    if argv=='Short':
        f.save_runtime(start_time, end_time, f"{argv}, {datetime.now()}")
    elif argv!='':
        f.save_runtime(start_time, end_time)


if __name__ == "__main__":
    main()

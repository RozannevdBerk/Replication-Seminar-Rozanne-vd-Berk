import os
from datetime import datetime
from pathlib import Path

from promg import SemanticHeader, OcedPg
from promg import DatabaseConnection
from promg import authentication
from promg import DatasetDescriptions

from promg import Performance
from promg.modules.db_management import DBManagement
from promg.modules.inference_engine import InferenceEngine
from promg.modules.task_identification import TaskIdentification
from promg.modules.process_discovery import ProcessDiscovery

# several steps of import, each can be switch on/off
from colorama import Fore

from custom_modules.custom_modules.collapse_nodes import CollapseNodes

connection = authentication.connections_map[authentication.Connections.LOCAL]

dataset_name = 'BoxProcess'
use_sample = False
batch_size = 10000
use_preprocessed_files = False

semantic_header_path = Path(f'json_files/{dataset_name}.json')

semantic_header = SemanticHeader.create_semantic_header(semantic_header_path)
perf_path = os.path.join("..", "perf", dataset_name, f"{dataset_name}_{'sample_' * use_sample}Performance.csv")

ds_path = Path(f'json_files/{dataset_name}_DS.json')
dataset_descriptions = DatasetDescriptions(ds_path)

# several steps of import, each can be switch on/off
step_clear_db = True
step_populate_graph = True
verbose = False  # print the used queries
credentials_key = authentication.Connections.LOCAL


def main() -> None:
    """
    Main function, read all the logs, clear and create the graph, perform checks
    @return: None
    """
    print("Started at =", datetime.now().strftime("%H:%M:%S"))

    db_connection = DatabaseConnection.set_up_connection_using_key(key=credentials_key,
                                                                   verbose=verbose)
    performance = Performance.set_up_performance(dataset_name=dataset_name,
                                                 use_sample=use_sample)
    db_manager = DBManagement()

    if step_clear_db:
        print(Fore.RED + 'Clearing the database.' + Fore.RESET)
        db_manager.clear_db(replace=True)
        db_manager.set_constraints()

    if step_populate_graph:
        if use_preprocessed_files:
            print(Fore.RED + '💾 Preloaded files are used!' + Fore.RESET)
        else:
            print(Fore.RED + '📝 Importing and creating files' + Fore.RESET)

        oced_pg = OcedPg(dataset_descriptions=dataset_descriptions,
                         use_sample=use_sample,
                         use_preprocessed_files=use_preprocessed_files)
        oced_pg.load_and_transform()

        collapse_nodes = CollapseNodes()
        collapse_nodes.collapse_nodes()

        inference = InferenceEngine()
        # region Infer missing information
        # rule c, both for preceding load events and succeeding unload events
        inference.infer_items_propagate_upwards_multiple_levels(entity_type="Box", is_load=True)
        inference.infer_items_propagate_upwards_multiple_levels(entity_type="Box", is_load=False)
        oced_pg.create_relations(relation_types=["AT_POS"])
        # rule d
        inference.infer_items_propagate_downwards_multiple_level_w_batching(entity_type="Box",
                                                                            relative_position_type="BatchPosition")
        # rule b
        inference.infer_items_propagate_downwards_one_level(entity_type="Box")

        oced_pg.create_df_edges()

    performance.finish_and_save()
    db_manager.print_statistics()

    db_connection.close_connection()


if __name__ == "__main__":
    main()

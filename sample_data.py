import itertools
import random
import time
import argparse as ap
import logging

import pandas as pd
import numpy as np
import more_itertools

np.random.seed(42)
random.seed(42)


logger = logging.getLogger("debug")
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.INFO)



# only use the top 1000 rows


children_full = pd.read_csv("data/children_1000000.csv")
parent_full = pd.read_csv("data/parents_1000000.csv")

children = children_full[['id', 'family_id']]
parents = parent_full[['id', 'family_id']]


required_columns = [
    'child_drec_id', 'parent_drec_id', 'family_drec_id', 'id_child', 'id_parent', 'family_id'
]


def configure_parser(parser: ap.ArgumentParser):
    parser.add_argument("source_name", help="give a name to the data source you are about to create", type=str)
    parser.add_argument('-p', '--proba', help="probability of a child selected", type=float, default=0.8)
    parser.add_argument('-d', '--duplication_rate', help='probability of a selected child getting duplicated',
                        type=float, default=0.4)


def validate_args(args):
    if not (0.0 < args.proba < 1.0):
        raise ValueError("selection probability has to be between 0 and 1")
    if not (0.0 < args.duplication_rate < 1.0):
        raise ValueError("duplication probability has to be between 0 and 1")


def get_group_rank(family_ids):
    prev = None
    k = 1
    result = []
    for fi in family_ids:
        if prev != fi:
            k = 1
        result.append(k)
        k += 1
        prev = fi
    return result


def id_permutations(ids):
    child_ids = ids['child_drec_id']
    if len(child_ids) > 1:
        return list(itertools.permutations(child_ids, 2))
    return []


if __name__ == '__main__':
    argument_parser = ap.ArgumentParser(description="")
    configure_parser(argument_parser)
    args = argument_parser.parse_args()
    validate_args(args)

    p = args.proba
    duplication_rate = args.duplication_rate
    source_name = args.source_name

    logger.info(f"{p=}")
    logger.info(f"{duplication_rate=}")
    logger.info(f"{source_name=}")

    start = time.time()

    all_family_ids = children.family_id.unique()
    family_ids_selected = pd.Series(all_family_ids).sample(int(len(all_family_ids) * p))

    children_selected = children[children.family_id.isin(family_ids_selected)]
    parents_selected = parents[parents.family_id.isin(family_ids_selected)].copy()

    number_children_selected = len(children_selected)
    family_ids_duplicates = family_ids_selected.sample(int(len(family_ids_selected) * duplication_rate), replace=True)

    children_duplicates = pd.DataFrame(family_ids_duplicates, columns=['family_id']) \
        .merge(children_selected, on='family_id') \
        .sort_values('family_id')

    children_duplicates['rank'] = get_group_rank(children_duplicates['family_id'])
    parent_relationship_duplicates = children_duplicates.merge(parents_selected, on='family_id',
                                                               suffixes=('_child', '_parent'))

    parent_relationship_duplicates['parent_drec_id'] = 0
    parent_relationship_duplicates['child_drec_id'] = 0
    parent_relationship_duplicates['family_drec_id'] = 0
    max_rank = children_duplicates['rank'].max()
    parent_max_id = 1
    child_max_id = 0
    family_max_id = 0

    logger.info("add id for parent, child and family id for duplicate set")
    for i in range(1, max_rank + 1):
        rank_equal_x = parent_relationship_duplicates['rank'] == i
        pl = sum(rank_equal_x)
        parent_relationship_duplicates.loc[rank_equal_x, 'parent_drec_id'] = np.arange(parent_max_id,
                                                                                       parent_max_id + pl)
        cl = len(parent_relationship_duplicates[rank_equal_x].id_child.unique())
        parent_relationship_duplicates.loc[rank_equal_x, 'child_drec_id'] = parent_relationship_duplicates \
                                                                                .loc[rank_equal_x, 'id_child'] \
                                                                                .rank(method='dense') + child_max_id
        fl = len(parent_relationship_duplicates[rank_equal_x].family_id.unique())
        parent_relationship_duplicates.loc[rank_equal_x, 'family_drec_id'] = parent_relationship_duplicates \
                                                                                .loc[rank_equal_x, 'family_id'] \
                                                                                .rank(method='dense') + family_max_id
        family_max_id += fl
        parent_max_id += pl
        child_max_id += cl

    logger.info("add id for parent, child and family id for selected set")
    # fill parent_drec_id, children_drec_id, and family_drec_id for selected data
    parent_relationship_selected = children_selected.merge(parents_selected, on='family_id',
                                                           suffixes=('_child', '_parent'))
    parent_relationship_selected['parent_drec_id'] = np.arange(1, len(parent_relationship_selected) + 1)
    parent_relationship_selected['child_drec_id'] = parent_relationship_selected['id_child'].rank(method='dense')
    parent_relationship_selected['parent_drec_id'] = parent_relationship_selected['parent_drec_id'] +\
                                                     parent_relationship_duplicates['parent_drec_id'].max()
    parent_relationship_selected['child_drec_id'] = parent_relationship_selected['child_drec_id'] +\
                                                    parent_relationship_duplicates['child_drec_id'].max()

    parent_relationship_selected['family_drec_id'] = parent_relationship_selected['family_id'].rank(method='dense') +\
                                                     parent_relationship_duplicates['family_drec_id'].max()

    parent_relationship_selected = parent_relationship_selected.astype(np.int)[required_columns]
    parent_relationship_duplicates = parent_relationship_duplicates.astype(np.int)[required_columns]
    relationship_table_intermediate = pd.concat([parent_relationship_duplicates, parent_relationship_selected],
                                                ignore_index=True)
    relationship_table_intermediate['parent_drec_id'] = relationship_table_intermediate['parent_drec_id'] +\
                                                        relationship_table_intermediate['child_drec_id'].max()

    logging.info("build parent relationship")
    parent_relationship = pd.DataFrame(relationship_table_intermediate[['child_drec_id', 'parent_drec_id']].values,
                                       columns=['subject_drec_id', 'related_drec_id'])
    parent_relationship['relationship_type'] = 'child'

    logger.info("build sibling relationships")
    sibling_pairs = relationship_table_intermediate[['family_drec_id', 'child_drec_id']]\
        .drop_duplicates()\
        .groupby('family_drec_id')\
        .apply(id_permutations)\
        .values.tolist()

    sibling_pairs_flattened = list(more_itertools.flatten(sibling_pairs))
    sibling_relationship = pd.DataFrame(sibling_pairs_flattened, columns=['subject_drec_id', 'related_drec_id'])
    sibling_relationship['relationship_type'] = 'sibling'

    logger.info("build complete relationship table")
    final_relationship_table = pd.concat([sibling_relationship, parent_relationship], ignore_index=True)

    logger.info("build children portion of the people data")
    final_children = relationship_table_intermediate[['child_drec_id', 'id_child']] \
        .drop_duplicates() \
        .merge(children_full, left_on='id_child', right_on='id', how='left')

    logger.info("build parent portion of the people data")
    final_parents = relationship_table_intermediate[['parent_drec_id', 'id_parent']] \
        .drop_duplicates() \
        .merge(parent_full, left_on='id_parent', right_on='id', how='left')

    final_children.rename(columns={"child_drec_id": "drec_id"}, inplace=True)
    final_parents.rename(columns={"parent_drec_id": "drec_id"}, inplace=True)
    required_columns = ['drec_id'] + list(final_children.columns[3:])
    final_children = final_children[required_columns]
    final_parents = final_parents[required_columns]
    logger.info(f"{len(final_children)=}")
    logger.info(f"{len(final_parents)=}")
    logger.critical(f"{(len(final_children) * 2 == len(final_parents))=}")



    # build final people table
    final_people = pd.concat([final_parents, final_children], ignore_index=True)

    logger.info(f"{final_people.shape=}")
    logger.info(f"{final_people.drec_id.unique().shape=}")
    final_people.to_csv(f"data/{source_name}_people.csv", index=False)
    final_relationship_table.to_csv(f"data/{source_name}_relationship.csv", index=False)
    logger.info(f"elapsed: {time.time() - start:.2f}s")

import itertools
import random

import pandas as pd
import numpy as np
import more_itertools

np.random.seed(42)
random.seed(42)

data_source_name = "edumaster"
p = 0.9
duplication_rate = 0.4

# only use the top 1000 rows

children = pd.read_csv("children_1000.csv")[['id', 'family_id']]
parents = pd.read_csv("parents_1000.csv")[['id', 'family_id']]


#print(children.head().to_markdown())

all_family_ids = children.family_id.unique()
family_ids_selected = pd.Series(all_family_ids).sample(int(len(all_family_ids) * p))

children_selected = children[children.family_id.isin(family_ids_selected)]
parents_selected = parents[parents.family_id.isin(family_ids_selected)].copy()
#print(f"{children_selected.family_id.unique().shape=}")

max_children_id = len(children)

number_children_selected = len(children_selected)
family_ids_duplicates = family_ids_selected.sample(int(len(family_ids_selected) * duplication_rate), replace=True)

children_duplicates = pd.DataFrame(family_ids_duplicates, columns=['family_id'])\
    .merge(children_selected, on='family_id')\
    .sort_values('family_id')


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


children_duplicates['rank'] = get_group_rank(children_duplicates['family_id'])
parent_relationship_duplicates = children_duplicates.merge(parents_selected, on='family_id', suffixes=('_child', '_parent'))

parent_relationship_duplicates['parent_drec_id'] = 0
parent_relationship_duplicates['child_drec_id'] = 0
parent_relationship_duplicates['family_drec_id'] = 0
max_rank = children_duplicates['rank'].max()
parent_max_id = 1
child_max_id = 0
family_max_id = 0

for i in range(1, max_rank+1):
    rank_equal_x = parent_relationship_duplicates['rank'] == i
    pl = sum(rank_equal_x)
    parent_relationship_duplicates.loc[rank_equal_x, 'parent_drec_id'] = np.arange(parent_max_id, parent_max_id + pl)
    cl = len(parent_relationship_duplicates[rank_equal_x].id_child.unique())
    parent_relationship_duplicates.loc[rank_equal_x, 'child_drec_id'] = parent_relationship_duplicates\
                                                                            .loc[rank_equal_x, 'id_child']\
                                                                            .rank(method='dense') + child_max_id
    fl = len(parent_relationship_duplicates[rank_equal_x].family_id.unique())
    parent_relationship_duplicates.loc[rank_equal_x, 'family_drec_id'] = parent_relationship_duplicates\
                                                                             .loc[rank_equal_x, 'family_id']\
                                                                             .rank(method='dense') + family_max_id
    family_max_id += fl
    parent_max_id += pl
    child_max_id += cl


parent_relationship_selected = children_selected.merge(parents_selected, on='family_id', suffixes=('_child', '_parent'))
parent_relationship_selected['parent_drec_id'] = np.arange(1, len(parent_relationship_selected)+1)
parent_relationship_selected['child_drec_id'] = parent_relationship_selected['id_child'].rank(method='dense')
parent_relationship_selected['parent_drec_id'] = parent_relationship_selected['parent_drec_id'] +\
                                                 parent_relationship_duplicates['parent_drec_id'].max()
parent_relationship_selected['child_drec_id'] = parent_relationship_selected['child_drec_id'] +\
                                                parent_relationship_duplicates['child_drec_id'].max()

parent_relationship_selected['family_drec_id'] = parent_relationship_selected['family_id'].rank(method='dense') +\
                                                 parent_relationship_duplicates['family_drec_id'].max()


required_columns = [
    'child_drec_id', 'parent_drec_id', 'family_drec_id', 'id_child', 'id_parent', 'family_id'
]

parent_relationship_selected = parent_relationship_selected.astype(np.int)[required_columns]
parent_relationship_duplicates = parent_relationship_duplicates.astype(np.int)[required_columns]

relationship_table_intermediate = pd.concat([parent_relationship_duplicates, parent_relationship_selected], ignore_index=True)


parent_relationship = pd.DataFrame(relationship_table_intermediate[['child_drec_id', 'parent_drec_id']].values,
                                   columns=['subject_drec_id', 'related_drec_id'])


def id_permutations(ids):
    child_ids = ids['child_drec_id']
    if len(child_ids) > 1:
        return list(itertools.permutations(child_ids, 2))
    return []


sibling_pairs = relationship_table_intermediate[['family_drec_id', 'child_drec_id']]\
    .drop_duplicates()\
    .groupby('family_drec_id')\
    .apply(id_permutations)\
    .values.tolist()

sibling_pairs_flattened = list(more_itertools.flatten(sibling_pairs))
sibling_relationship = pd.DataFrame(sibling_pairs, columns=['subject_drec_id', 'related_drec_id'])
sibling_relationship['relationship_type'] = 'sibling'




# #
# # new_children_table.to_csv(f"{data_source_name}_children.csv")
# # new_parent_table.to_csv(f"{data_source_name}_parents.csv")



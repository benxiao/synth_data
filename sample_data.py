import itertools
import random

import pandas as pd
import numpy as np

np.random.seed(42)
random.seed(42)

data_source_name = "edumaster"
p = 0.9
duplication_rate = 0.4

children = pd.read_csv("children_1000000.csv").head(1000)[['id', 'family_id']]
parents = pd.read_csv("parents_1000000.csv").head(1000)[['id', 'family_id']]


print(children.head().to_markdown())

children_selected = children[np.random.random(len(children)) < p].copy()
print(children_selected)
family_id_selected = children_selected.family_id.unique()
parents_selected = parents[parents.family_id.isin(family_id_selected)].copy()
print(f"{children_selected.family_id.unique().shape=}")

max_children_id = len(children)

number_children_selected = len(children_selected)
children_duplicates = children_selected.sample(int(number_children_selected * duplication_rate), replace=True, random_state=42).copy()


def add_rank(x):
    l = len(x)
    x = pd.DataFrame(x['family_id']).copy()
    x['rank'] = np.arange(1, l+1)
    return x


children_duplicates = children_duplicates.groupby('id')[['family_id']].apply(add_rank).reset_index()
parents_duplicates = children_duplicates.merge(parents_selected, on='family_id', suffixes=('_child', '_parent'))
print(parents_duplicates)



#
#
# parents_duplicates = parents_selected[parents_selected.family_id.isin(children_duplicates.family_id)].copy()
#
# children_duplicates.loc[:, 'family_id'] = max_children_id + children_duplicates['family_id']
# parents_duplicates.loc[:, 'family_id'] = max_children_id + parents_duplicates['family_id']
#
#
# new_children_table = pd.concat([children_selected, children_duplicates], ignore_index=True)
#
#
# #print(new_children_table.to_markdown())
#
# new_children_ids = np.arange(len(new_children_table))
# np.random.shuffle(new_children_ids)
# new_children_table.loc[:, 'id'] = new_children_ids
#
# new_parent_table = pd.concat([parents_selected, parents_duplicates], ignore_index=True)
#
# new_parent_ids = np.arange(len(new_parent_table))
# np.random.shuffle(new_parent_ids)
# new_parent_table.loc[:, 'id'] = new_parent_ids
#
#
# def id_permutations(ids):
#     if len(ids) > 1:
#         return pd.DataFrame(list(itertools.permutations(ids, 2)), columns=['subject', 'related'])
#     return pd.DataFrame()
#
#
# family_ids_with_sibling_relationships = new_children_table.family_id.value_counts()
# print(family_ids_with_sibling_relationships)
# #
# #
# # new_children_table.to_csv(f"{data_source_name}_children.csv")
# # new_parent_table.to_csv(f"{data_source_name}_parents.csv")



import random

import pandas as pd
from pandas import Timedelta
import numpy as np

np.random.seed(42)


probability_to_present = {
    "first_name": 1.0,
    "middle_name": 0.75,
    "last_name": 1.0,
    "email_address": 0.1,
    "birth_date": 1.0
}

parent_count_distribution = [0.04, 0.18, 0.78]

print(sum(parent_count_distribution))

df = pd.read_csv("data/edumaster_people.csv")
relationship = pd.read_csv("data/edumaster_relationship.csv")

df['birth_date'] = pd.to_datetime(df['birth_date'])
for column, proba in probability_to_present.items():
    df.loc[np.invert(np.random.random(len(df)) <= proba), column] = None

# print(df.head(100).to_markdown())
parent_df = df[~df.is_child]
children_df = df[df.is_child].sort_values("drec_id")

print(f"{len(parent_df)=}")
print(f"{len(children_df)=}")

child_relationship = relationship[relationship.relationship_type == 'child'].sort_values("subject_drec_id")
print(f"{len(child_relationship)=}")
parent_count_for_children = np.random.choice([0, 1, 2], len(children_df), p=parent_count_distribution)
parent_keep = []
for x in parent_count_for_children:
    if x == 0:
        parent_keep.append(False)
        parent_keep.append(False)
    elif x == 2:
        parent_keep.append(True)
        parent_keep.append(True)
    else:
        parent_keep.append(random.choice([True, False]))
        parent_keep.append((not parent_keep[-1]))

print(f"{len(parent_keep)=}")
print(f"{child_relationship.shape=}")
#
result = child_relationship[parent_keep]
print(result.head().to_markdown())


pbirth_date_off_by_one = 0.02

birth_date_present = df.birth_date.notnull()
off_by_one_date = birth_date_present.map(lambda x: random.random() < 0.05 if x else False)
df.loc[off_by_one_date, 'birth_date'] = df.loc[off_by_one_date, 'birth_date'] + Timedelta(days=1)




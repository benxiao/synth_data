import random
import os
import argparse as ap

from enum import Enum
import pandas as pd
from pandas import Timedelta, Timestamp
import numpy as np

np.random.seed(42)


def identity(x):
    return x


def to_null(x):
    return None


class NameCorruption(Enum):
    nothing = 0
    missing = 1


class BirthDateCorruption(Enum):
    off_by_one = 0
    day_month_swap = 1
    one_typo = 2
    missing = 3
    nothing = 4


class EmailCorruption(Enum):
    nothing = 0
    missing = 1


class DateCorruptionType(Enum):
    year = 0
    month = 1
    day = 2


single_digit_typo = {
    "0": "69",
    "1": "47",
    "2": "3",
    "3": "2",
    "4": "1",
    "5": "6",
    "6": "8",
    "7": "1",
    "8": "69",
    "9": "8"
}


children_field_probability = {
    "first_name": {
        NameCorruption.nothing: 1.0,
        NameCorruption.missing: 0.0
    },
    "middle_name": {
        NameCorruption.nothing: 0.75,
        NameCorruption.missing: 0.25
    },
    "last_name": {
       NameCorruption.nothing: 1.0,
       NameCorruption.missing: 0.0
    },
    "email_address": {
        EmailCorruption.nothing: 0.1,
        EmailCorruption.missing: 0.9
    },
    "birth_date": {
        BirthDateCorruption.off_by_one: 0.02,
        BirthDateCorruption.day_month_swap: 0.01,
        BirthDateCorruption.one_typo: 0.01,
        BirthDateCorruption.missing: 0.0,
        BirthDateCorruption.nothing: 0.96
    }
}


parent_field_probability = {
    "first_name": {
        NameCorruption.nothing: 1.0,
        NameCorruption.missing: 0.0
    },
    "middle_name": {
        NameCorruption.nothing: 0.55,
        NameCorruption.missing: 0.45
    },
    "last_name": {
       NameCorruption.nothing: 1.0,
       NameCorruption.missing: 0.0
    },
    "email_address": {
        EmailCorruption.nothing: 0.3,
        EmailCorruption.missing: 0.7
    },
    "birth_date": {
        BirthDateCorruption.off_by_one: 0.01,
        BirthDateCorruption.day_month_swap: 0.005,
        BirthDateCorruption.one_typo: 0.005,
        BirthDateCorruption.missing: 0.70,
        BirthDateCorruption.nothing: 0.28
    }
}


def day_month_swap(ts: Timestamp):
    if ts.day > 12:
        return ts
    return Timestamp(ts.year, ts.day, ts.month)


def one_typo(ts: Timestamp):
    year = ts.year
    month = ts.month
    day = ts.day

    t = random.choice([
        DateCorruptionType.month,
        DateCorruptionType.year,
        DateCorruptionType.day
    ])

    # year
    if t == DateCorruptionType.year:
        last_digit = str(year)[-1]
        corrupted_year = str(year)[:3] + random.choice(single_digit_typo[last_digit])
        try:
            return Timestamp(int(corrupted_year), month, day)
        except ValueError:
            # print(int(corrupted_year), month, day)
            return ts
    # month
    elif t == DateCorruptionType.month:
        if month < 10:
            corrupted_month = random.choice(single_digit_typo[str(month)])
            try:
                return Timestamp(year, int(corrupted_month), day)
            except ValueError:
                # print(year, int(corrupted_month), day)
                return ts

    # day
    elif t == DateCorruptionType.day:
        last_digit = str(day)[-1]
        if day < 30:
            corrupted_day = str(day)[:len(str(day))-1] + random.choice(single_digit_typo[last_digit])
            try:
                return Timestamp(year, month, int(corrupted_day))
            except ValueError:
                # print(year, month, int(corrupted_day))
                return ts

    return ts


CorruptionType2Func = {
    NameCorruption.nothing: identity,
    NameCorruption.missing: to_null,
    BirthDateCorruption.off_by_one: lambda x: x+Timedelta(days=1),
    BirthDateCorruption.day_month_swap: day_month_swap,
    BirthDateCorruption.one_typo: one_typo,
    BirthDateCorruption.missing: to_null,
    BirthDateCorruption.nothing: identity,
    EmailCorruption.nothing: identity,
    EmailCorruption.missing: to_null
}


parent_count_probability = [0.04, 0.18, 0.78]


def configure_parser(parser: ap.ArgumentParser):
    parser.add_argument("source_name", type=str, help="the sampled dataset you would like to apply corruptions on")
    parser.add_argument("-d", "--debug", action='store_true', default=False, help="enable debugging")


if __name__ == '__main__':
    parser = ap.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args()
    if (not os.path.isfile(f"data/{args.source_name}_people.csv")) or (not os.path.isfile(f"data/{args.source_name}_relationship.csv")):
        raise EnvironmentError("run sampling first!")

    df = pd.read_csv(f"data/{args.source_name}_people.csv")
    relationship = pd.read_csv(f"data/{args.source_name}_relationship.csv")

    df['birth_date'] = pd.to_datetime(df['birth_date'])
    parent_df = df[~df.is_child]
    children_df = df[df.is_child].sort_values("drec_id")

    for x_df, prob_lookup in zip([children_df, parent_df],
                                 [children_field_probability, parent_field_probability]):
        for column, prob in prob_lookup.items():
            choices = np.random.choice(list(prob.keys()), len(x_df), p=list(prob.values()))
            transformed_values = [CorruptionType2Func[c](v) for c, v in zip(choices.tolist(), x_df[column])]
            x_df[column] = transformed_values

    print(parent_df.head(100).to_markdown())
    print(children_df.head(100).to_markdown())

    child_relationship = relationship[relationship.relationship_type == 'child'].sort_values("subject_drec_id")
    print(f"{len(child_relationship)=}")
    parent_count_for_children = np.random.choice([0, 1, 2], len(children_df), p=parent_count_probability)
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

    new_child_relationship = child_relationship[parent_keep]
    new_sibling_relationship = relationship[relationship.relationship_type == 'sibling']
    new_relationship = pd.concat([new_child_relationship, new_sibling_relationship], ignore_index=True)
    if args.debug:
        print("relationship:")
        print(f"{new_relationship.shape=}")
        print(new_relationship.head(100).to_markdown())

    new_people = pd.concat([parent_df, children_df], ignore_index=True)
    if args.debug:
        print("people:")
        print(f"{new_people.shape=}")
        print(new_people.head(100).to_markdown())

    if args.debug:
        print("write data")
    new_people.to_csv(f"data/{args.source_name}_people_corrupted.csv", index=False)
    new_relationship.to_csv(f"data/{args.source_name}_relationship_corrupted.csv", index=False)







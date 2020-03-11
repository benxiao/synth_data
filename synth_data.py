import faker
import random
from pandas import DataFrame
import numpy as np
from numpy import vectorize
from datetime import date, timedelta
import time
from typing import *


from myfaker.myfaker import MyFaker


faker.generator.random.seed(42)
LOCALES = ['en_AU', 'en_CA', 'en_NZ', 'en_US', 'en_GB']
faker_english = faker.Faker(LOCALES)


LOCALE_DISTRIBUTION = [0.7, 0.1, 0.2]
faker_objects = [faker_english, MyFaker(locale='indian'), MyFaker(locale='chinese')]

TOTAL_NUMBER_OF_CHILDREN = 1000_000
MALE_PERCENTAGE = 0.5
CHILD_AGE_LOW = 5
CHILD_AGE_HIGH = 18
FAMILY__SIZE_DISTRIBUTION = [0.33, 0.39, 0.22, 0.05, 0.01]
EMAIL_DOMAINS = ['gmail', 'icloud', 'yahoo', 'me', 'hotmail', 'outlook']


# parent age should tie to child age


num_siblings = (np.array(FAMILY__SIZE_DISTRIBUTION) * TOTAL_NUMBER_OF_CHILDREN).astype(np.int)
num_family_groups = (num_siblings / np.arange(1, 6)).astype(np.int)
num_male_records = int(TOTAL_NUMBER_OF_CHILDREN * MALE_PERCENTAGE)
num_female_records = int(TOTAL_NUMBER_OF_CHILDREN * (1 - MALE_PERCENTAGE))
ids = np.arange(num_female_records + num_male_records)


start = time.time()


genders = np.random.choice(['m', 'f'], TOTAL_NUMBER_OF_CHILDREN, p=[MALE_PERCENTAGE, 1 - MALE_PERCENTAGE])


def generate_family_ids() -> List[int]:
    result = []
    x = 0
    for i, group_count in enumerate(num_family_groups, start=1):
        for _ in range(group_count):
            for _ in range(i):
                result.append(x)
            x += 1

    while len(result) < TOTAL_NUMBER_OF_CHILDREN:
        result.append(x)

    return result


family_ids = generate_family_ids()


def generate_name_locales(family_ids) -> List[int]:
    result = []
    prev = None
    l = len(LOCALE_DISTRIBUTION)
    options = np.arange(l)
    for i in family_ids:
        if prev != i:
            result.append(np.random.choice(options))
            prev = i
        else:
            result.append(result[-1])
    return result


name_locales = generate_name_locales(family_ids)

first_names = np.array([faker_objects[i].first_name_male() if g == 'm' else faker_objects[i].first_name_female()
                        for g, i in zip(genders, name_locales)])

print(f"{first_names.shape=}")


def generate_last_names(family_ids: List[int]) -> List[str]:
    result = []
    prev = None
    for i, k in zip(family_ids, name_locales):
        if prev != i:
            result.append(faker_objects[k].last_name())
            prev = i
        else:
            result.append(result[-1])
    return result


last_names = np.array(generate_last_names(family_ids))
print(f"{last_names.shape=}")


middle_names = np.array([faker_objects[i].first_name_male() if g == 'm' else faker_objects[i].first_name_female()
                        for g, i in zip(genders, name_locales)])
print(f"{middle_names.shape=}")
#
birth_dates = np.array([faker_english.date_of_birth(
                        minimum_age=CHILD_AGE_LOW,
                        maximum_age=CHILD_AGE_HIGH)
                        for _ in range(TOTAL_NUMBER_OF_CHILDREN)])

print(f"{birth_dates.shape=}")


@vectorize
def email_gen(first_name, middle_name, last_name, birth_date) -> str:
    domain = random.choice(EMAIL_DOMAINS)
    seps = "_."
    sep = random.choice(seps)

    # full name
    def t0():
        return f"{first_name}{sep}{last_name}@{domain}.com"

    # initials and birth year
    def t1():
        return f"{first_name[0]}{middle_name[0]}{last_name[0]}{birth_date.year}@{domain}.com"

    # complete first_name + birth_date
    def t2():
        return f"{first_name}{birth_date.month}{birth_date.day}@{domain}.com"

    # complete first_name, last initial birth_date
    def t3():
        return f"{first_name}{sep}{last_name[0]}{birth_date.month}{birth_date.day}@{domain}.com"

    t = random.choice([t0, t1, t2, t3])
    return t().lower()


emails = email_gen(first_names, middle_names, last_names, birth_dates)
print(f"{emails.shape=}")

children = DataFrame({
    "id": ids,
    "family_id": family_ids,
    "locale": name_locales,
    "first_name": first_names,
    "middle_name": middle_names,
    "last_name": last_names,
    "birth_date": birth_dates,
    "email_address": emails,
    "gender": genders,
    "is_child": [True] * TOTAL_NUMBER_OF_CHILDREN
})

print("write children table...")
children.to_csv(f"children_{TOTAL_NUMBER_OF_CHILDREN}.csv", index=False)


print(children.head(30).to_markdown(), end='\n'*4)


def mother_birth_date_gen(child_birth_date: date) -> date:
    return child_birth_date - timedelta(days=random.randint(20 * 365, 40 * 365))


def father_birth_date_gen(child_birth_date: date) -> date:
    return child_birth_date - timedelta(days=random.randint(18 * 365, 50 * 365))


def generate_parents(children_df: DataFrame) -> DataFrame:
    parents = children_df.drop_duplicates(subset=['family_id'])
    n_pair_parents = len(parents)
    parents = parents.append(parents.copy()).sort_values('family_id')
    parent_genders = ['m', 'f'] * n_pair_parents

    parent_locales = parents['locale']

    parents.loc[:, 'gender'] = parent_genders
    parents.loc[:, 'first_name'] = [
        faker_objects[i].first_name_male() if g == 'm' else faker_objects[i].first_name_female()
        for g, i in zip(parent_genders, parent_locales)
    ]
    parents.loc[:, 'middle_name'] = [
        faker_objects[i].first_name_male() if g == 'm' else faker_objects[i].first_name_female()
        for g, i in zip(parent_genders, parent_locales)
    ]
    #
    parents.loc[:, 'last_name'] = [
        last if g == 'm' else faker_objects[i].last_name() if random.random() > 0.5 else last
        for last, g, i in zip(parents['last_name'], parent_genders, parent_locales)
    ]
    #
    parents.loc[:, 'birth_date'] = [
        father_birth_date_gen(bd) if g == 'm' else mother_birth_date_gen(bd)
        for bd, g in zip(parents['birth_date'], parent_genders)
    ]
    #
    parents.loc[:, 'email_address'] = email_gen(
        parents.loc[:, 'first_name'],
        parents.loc[:, 'middle_name'],
        parents.loc[:, 'last_name'],
        parents.loc[:, 'birth_date']
    )

    parents.loc[:, 'is_child'] = [False] * len(parents)
    parents.loc[:, 'id'] = np.arange(len(parents)) + len(children_df)
    print(parents.head(30).to_markdown())

    return parents


parents = generate_parents(children)

print("write parent table...")
parents.to_csv(f"parents_{TOTAL_NUMBER_OF_CHILDREN}.csv", index=False)


print(f"elapsed time: {time.time() - start:.2f}s")

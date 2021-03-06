import random
import importlib


class MyFaker:
    def __init__(self, locale='indian'):
        try:
            names_module = importlib.import_module(f'international_names.{locale}')
        except ModuleNotFoundError:
            raise ValueError(f"{locale=} not available!")
        self.d = getattr(names_module, locale)

    def generate(self, x):
        names = self.d[x]
        return names[random.randint(0, len(names) - 1)].capitalize()

    def first_name_male(self):
        return self.generate('first_names_male')

    def first_name_female(self):
        return self.generate('first_names_female')

    def last_name(self):
        return self.generate('last_names')


if __name__ == '__main__':
    faker = MyFaker(locale='fg')
    for _ in range(100):
        print(faker.first_name_male(), faker.last_name())

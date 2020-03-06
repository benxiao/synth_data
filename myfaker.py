import random


class MyFaker:
    def __init__(self, locale='indian'):
        self.fn_male = []
        self.fn_female = []
        self.ln = []
        with open(f"{locale}_names.csv") as fp:
            for line in fp:
                _, name, gender = line.split(",")
                gender = gender.strip()
                name = "".join(x for x in name if 64<ord(x)<91).lower()
                if gender == 'm':
                    self.fn_male.append(name.lower())
                elif gender == 'f':
                    self.fn_female.append(name.lower())
                else:
                    self.fn_male.append(name.lower())
                    self.fn_female.append(name.lower())
            print(self.fn_male)
            print(self.fn_female)




    def first_name_male(self):
        l = len(self.fn_male)
        return self.fn_male[random.randint(0, l-1)]

    def last_name(self):
        l = len(self.ln)
        return self.ln[random.randint(0, l-1)]



if __name__ == '__main__':
    myfaker = MyFaker()
    # for _ in range(100):
    #     print(myfaker.first_name_male(), myfaker.last_name())
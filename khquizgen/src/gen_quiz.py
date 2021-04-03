import random as rand
from jellyfish import jaro_winkler_similarity as jws
from khquizgen import logger
from khquizgen.src.utils import logger_wraps
modulus = range(1, 100, 1)


def run(root, no_questions):
    qg = QuizGen(root, no_questions)
    quiz = qg.gen_loop()
    return quiz

class QuizGen:
    def __init__(self, root, num):
        self.q, self.prompt, self.aks = [], [], []
        self.question, self.correct, self.prompt, self.aks = [], [], [], []
        self.q0, self.q1, self.q2, self.q3 = None, None, None, None
        self.a1, self.a2, self.answer, self.question = None, None, None, None
        self.mod1, self.mod2 = None, None
        self.root, self.num = root, num
        self.mod0 = list(root.keys())

    def gen_loop(self):
        while len(self.q) < self.num:
            self.question, self.correct, self.prompt, self.aks = [], [], [], []
            self.q0, self.mod1, self.mod2 = random_mods(self.root, self.mod0)
            self.q1, self.q2, self.q3 = random_question(self.root, self.q0,
                                                        mod1=self.mod1, mod2=self.mod2
                                                        )
            self.a1, self.a2 = stem_parse(self.q1, self.q2, self.q3)
            coin = get_coin()
            self.answer, self.question = (self.a1, self.a2) if coin == 1 else (self.a2, self.a1)
            self.prompt.append(self.question)
            self.aks.append((self.answer, True))
            if not self.ans_loop(coin):
                continue
            else:
                rand.shuffle(self.aks)
                a_list = [str(i + 1) for i in range(len(self.aks)) if self.aks[i][1]]
                self.prompt.extend([x[0] for x in self.aks])
                self.prompt.extend(['30', ','.join(a_list)])
                self.q.append('|'.join(self.prompt))
        return self.q

    def ans_loop(self, coin):
        d100 = rand.choice(modulus)
        max_count = 1 if d100 <= 40 else 2 if 40 < d100 <= 80 else 3 if 80 < d100 <= 99 else 4
        counter, skip = (1, False)
        while len(self.aks) < 4:
            mc, multi = self.random_answer(coin, counter, max_count)
            if all(v is None for v in [mc, multi]):
                skip = True
                break
            if multi:
                counter += 1
            self.aks.append((mc, multi))
            self.aks = list(set(self.aks))
        if skip:
            logger.warning(f"Question {self.question}/Answer{self.answer} in {self.q0}"
                           " did not have enough variety to parse. Skipped.")
            return False
        else:
            return True


    @logger_wraps()
    def random_answer(self, coin, count, max_count):
        mc_answer, mc_question, multi, tries = None, None, False, 0
        while None in [mc_question, mc_answer]:
            tries += 1
            if tries >= 10:
                return None, None
            dice = rand.choice([*range(1, 50, 1)])

            # Where x = Trunk, y = Branch, z = Leaf
            x, y, z = (random_question(self.root, self.q0, mod1=self.mod1, mod2=self.mod2) if dice in [1] else
                       random_question(self.root, self.q0, q1=self.q1, mod1=self.mod1, mod2=self.mod2) if dice in [2] else
                       random_question(self.root, self.q0, q2=self.q2, mod1=self.mod1, mod2=self.mod2))

            # Where a1 = Trunk+Branch and a2 = Leaf
            a1, a2 = stem_parse(x, y, z)
            mc_answer, mc_question = (a1, a2) if coin == 1 else (a2, a1)
            similar = jws(self.answer, mc_answer)

            if similar == 1.0 or similar <= 0.42:
                mc_answer = None
                continue
            if self.match_q(y, z) and count >= max_count:
                mc_answer = None
                continue
            elif self.match_q(y, z) and count < max_count:
                multi = True
        return mc_answer, multi

    def match_q(self, mc_q2, mc_q3):
        logger.debug(f'{mc_q2} and {mc_q3} \n {self.root[self.q0][self.q1]}')
        if self.q2 is mc_q2:
            if self.root[self.q0][self.q1].get(mc_q2):
                if mc_q3 in self.root[self.q0][self.q1][self.q2]:
                    return True
        return False

def stem_parse(q1, q2, q3):
    a1, a2 = f'{q1} {q2}', q3
    return a1, a2


def get_coin(): return rand.randint(1, 2)


def random_question(root, q0, mod1=None, mod2=None, q1=None, q2=None, q3=None):
    q1, q2, q3, mod1, mod2 = q1, q2, q3, mod1, mod2

    while None in [q1, q2, q3]:
        if q1 is None:
            q1 = rand.choice(mod1)
        if q2 is None:
            if q1 is None:
                mod2 = (list(root[q0][q1].keys()))
            q2 = rand.choice(mod2)
        if q3 is None:
            if root[q0][q1].get(q2):
                q3 = rand.choice(root[q0][q1][q2])
            else:
                q2 = None
    return q1, q2, q3


def random_mods(root, mod0):
    q0 = rand.choice(mod0)  # Selects a random Trunk
    mod1 = list(root[q0].keys())  # Selects a random Branch from topic
    mod2 = []
    for y in root[q0].values():
        mod2.extend(list(y.keys()))
    mod1 = list(set(mod1))
    mod2 = list(set(mod2))
    return q0, mod1, mod2

"""Generates the list of Kahoot quiz prompts to be fed into the excel writer.

"""
import random as rand
from jellyfish import jaro_winkler_similarity as jws
from khquizgen import logger
from khquizgen.src.utils import logger_wraps
from typing import Tuple, Optional
modulus = range(1, 100, 1)
modulus2 = range(1, 50, 1)


def run(root_dict, no_questions, timer='30'):
    qg = QuizGen(root_dict, no_questions, timer)
    qbank = qg.start_quizgen_loop()
    return qbank


class QuizGen:
    def __init__(self, root_dict: dict, num_q: int, timer: str):
        """Handles generation of Kahoot style quiz through random generation.

        Args:
            root_dict: Parsed form of user's notes from question.txt
            num_q: Number of questions to generate. Max Kahoot quiz is 100 questions.
            timer: 10, 15, 30, 60, 120, 240 in string format
        """
        self.qbank, self.prompt, self.aks = [], [], []
        self.question, self.correct, self.prompt, self.aks = [], [], [], []
        self.root, self.trunk, self.branch, self.leaf = None, None, None, None
        self.answer, self.question, self.coin = None, None, None
        self.trunk_list, self.branch_list = None, None

        self.root_dict, self.number_q, self.timer = root_dict, num_q, timer
        self.root_list = list(root_dict.keys())

    def start_quizgen_loop(self) -> list:
        """Main quiz generation loop.

        Each cycle zeroes question parameters and flips a coin that determines what format the
        question answer will be. Either Q: Trunk+Branch A: Leaf or vice versa. A random root,
        trunk, branch are called and parsed into Q and A. Then the MCQ generation loop is called and
        runs until a total of four mcq options are generated. They are parsed and appended to qbank.

        Returns:
            A list `qbank` of strings styled for output to csv, or to the .xlsx generator module.
        """
        while len(self.qbank) < self.number_q:
            self.coin = rand.randint(1, 2)
            self.create_new_question()
            if not self.start_mc_loop():
                continue  # If 4 suitable MCQ's were not generated, start loop
            else:  # again. This avoids incrementing the qbank.
                rand.shuffle(self.aks)
                a_list = [str(i + 1) for i in range(len(self.aks)) if self.aks[i][1]]
                self.prompt.extend([x[0] for x in self.aks])
                self.prompt.extend([self.timer, ','.join(a_list)])
                self.qbank.append('|'.join(self.prompt))
        return self.qbank

    def create_new_question(self):
        """Initializes a new Question by zeroing all instance parameters."""
        self.question, self.correct, self.prompt, self.aks = [], [], [], []
        self.root, self.trunk_list, self.branch_list = get_random_root(self.root_dict, self.root_list)
        self.trunk, self.branch, self.leaf, self.answer, self.question = self.get_question_and_answer()
        self.prompt.append(self.question)
        self.aks.append((self.answer, True))

    def get_question_and_answer(self, dice: int = None) -> Tuple[str, str, str, str, str]:
        """Call functions to generate trunk, branch, leaf, answer, and question.

        Args:
            dice: If dice are not None, the get_random_trunk_branch_leaf function will return
            a trunk, branch, and leaf that follow one of three schema:
               1. Question Trunk, Random Branch, Random leaf
               2. Random Trunk, Question Branch, Random Leaf
               3. Random Trunk, Random Branch, Random Leaf

        Returns: A trunk, branch, leaf, answer, and question.

        """
        trunk, branch, leaf = get_random_trunk_branch_leaf(self.root_dict, self.root,
                                                           trunk_list=self.trunk_list,
                                                           branch_list=self.branch_list,
                                                           dice=dice)
        trunk_branch, leaf = stem_parse(trunk, branch, leaf)
        answer, question = (trunk_branch, leaf) if self.coin == 1 else (leaf, trunk_branch)
        return trunk, branch, leaf, answer, question

    def start_mc_loop(self) -> bool:
        """Attempts to create three multiple choice options.

        Script will roll a d100 to determine number of `Multi` and then loop through calling
        get_random_mc_answer until we get suitable MCQ's, or spend too many attempts on a stem.
        Before escaping the while loop, we remove duplicate answers, and then loop again if we do
        not have enough.

        Returns: True if three suitable MC's are found. False otherwise. False will cause Question
        to be discarded and attempt a New Question.
        """
        d100 = rand.choice(modulus)
        max_count = 1 if d100 <= 40 else 2 if 40 < d100 <= 80 else 3 if 80 < d100 <= 99 else 4
        counter = 1
        while len(self.aks) < 4:
            mc, multi = self.get_random_mc_answer(counter, max_count)
            if mc is None and multi is None:
                logger.warning(f"Question {self.question}/Answer{self.answer} in {self.root}"
                               " did not have enough variety to parse. Skipped.")
                return False
            elif multi:
                counter += 1
            self.aks.append((mc, multi))
            self.aks = list(set(self.aks))
        return True

    def get_random_mc_answer(self, count: int, max_count: int) -> Tuple[Optional[str], Optional[bool]]:
        """Attempts to randomly generate a random multiple choice option.

        Function will create a trunk, branch, leaf, answer, and question the same way we made
        a question prompt. It will attempt `tries` times to create an option, if it fails the script
        abandons the Question and starts a New Question Loop.

        It compares the generated answer to the correct answer using JWS for
        similarity. A good MC answer should be roughly similar to the correct answer, but not equal.
        This is helpful mainly for MC options that are in the Trunk-Branch format, but it also is
        a check for Leaf answers. E.g Vehicle Size = 14'. JWS would flag an MC choice Vehicle Fuel
        Efficiency as disimilar, but not Vehicle Cargo Size.

        It will also call check_also_correct to see if the MC answer is a correct choice for the CA.
        If it is, it will return True for Multi.

        Args:
            count: Current number of Multi = True MC's generated for this Question.
            max_count: Maximum number of Multi = True allowed for this Question.

        Returns:
            If the script tries more than `tries` times to find a suitable MC, it returns None,
            None - which will make the mc_answer loop escape and start over. Otherwise it Returns
            the mc_answer string, and a boolean for whether Multi is True or False.
        """
        mc_answer, mc_question, multi, tries = None, None, False, 0
        while None in [mc_question, mc_answer]:
            tries += 1
            if tries >= 10:
                return None, None
            dice = rand.choice(modulus2)
            trunk, branch, leaf, mc_answer, mc_question = self.get_question_and_answer(dice=dice)
            similar = jws(self.answer, mc_answer)

            if similar == 1.0 or similar <= 0.42:
                mc_answer = None
                continue
            if self.check_also_correct(branch, leaf) and count >= max_count:
                mc_answer = None
                continue
            elif self.check_also_correct(branch, leaf) and count < max_count:
                multi = True
        return mc_answer, multi

    def check_also_correct(self, mc_branch: str, mc_leaf: str) -> bool:
        """Compares multiple-choice option to current answer.

        Compares Branch and Leaf from the potential multiple choice (PMC) option and tests whether
        this leaf exists in the Current Answer's (CA) Branch-Leaf list.

        Args:
            mc_branch: PMC Branch
            mc_leaf: PMC Leaf

        Returns:
            Returns True if the PMC Leaf exists in the CA Branch-Leaf, otherwise False.
        """
        logger.debug(f'{mc_branch} and {mc_leaf} \n {self.root_dict[self.root][self.trunk]}')
        if self.branch is mc_branch:
            if self.root_dict[self.root][self.trunk].get(mc_branch):
                if mc_leaf in self.root_dict[self.root][self.trunk][self.branch]:
                    return True
        return False


def stem_parse(trunk: str, branch: str, leaf: str) -> Tuple[str, str]:
    """ QoL function to parse Trunk Branch Leaf into correct string format

    Args:
        trunk: Trunk string
        branch: Branch string
        leaf: Leaf string

    Returns:
        Trunk and Branch formatted as: f"{trunk} {branch}", and the Leaf.
    """
    trunk_branch, leaf = f'{trunk} {branch}', leaf
    return trunk_branch, leaf


def get_random_root(root_dict: dict, root_list: list) -> Tuple[str, list, list]:
    """Selects a random Root from the dict and returns lists of its Trunks and Branches.

    Args:
        root_dict: All values parsed from user's notes.
        root_list: All Roots. [root_dict.keys()]

    Returns:
        Current root string, list of all Trunks and Branches for selected Root are returned.
    """
    root = rand.choice(root_list)               # Selects a random Root
    trunk_list = list(root_dict[root].keys())   # Selects a random Trunk
    branch_list = []
    for trunk in root_dict[root].values():      # Lists all the Branches
        branch_list.extend(list(trunk.keys()))
    trunk_list = list(set(trunk_list))          # Remove duplicates
    branch_list = list(set(branch_list))        # Remove duplicates
    return root, trunk_list, branch_list        # One Root and a list of its trunks and branches


def get_random_trunk_branch_leaf(root_dict: dict, root: str, trunk_list: list, branch_list: list,
                                 trunk: str = None, branch: str = None, leaf: str = None,
                                 dice: int = None) -> Tuple[str, str, str]:
    """Generates random Trunk, Branch, and Leaf from a given Root.

    This function is called on the initial question generation and then again for each potential
    multiple choice (PMC). First run is only passed the dict and current root, trunk_list, and
    branch_list - the results are all randomly generated. For PMC generation, different combinations
    of values are passed, resulting in specific questions or more random ones.

    Args:
        root_dict: The dictionary of parsed notes in Root-Trunk-Branch-Leaf format
        root: The currently selected Root
        trunk_list: List of Trunks for a given Root. list(root_dict[root].keys())
        branch_list: List of Branches for each Trunk
        trunk: Current question's Trunk (None on initial question generation.)
        branch: Current question's Branch (None on initial question generation.)
        leaf: Current question's Leaf (None on initial question generation.)

    Returns:
        Returns a randomly selected Trunk, Leaf, and Branch.
    """
    trunk, branch, leaf = trunk, branch, leaf
    if dice:
        if dice in [1]:
            trunk, branch = None, None
        elif dice in [2]:
            branch = None
        else:
            trunk = None
    while None in [trunk, branch, leaf]:
        if trunk is None:
            trunk = rand.choice(trunk_list)     # Not supplied trunk, pick a random one
        if branch is None:                      # Not supplied branch, pick a random one
            if trunk is None:                   # This probably never gets called.......
                branch_list = (list(root_dict[root][trunk].keys()))
            branch = rand.choice(branch_list)   # Generate a random branch
        if leaf is None:
            if root_dict[root][trunk].get(branch):
                leaf = rand.choice(root_dict[root][trunk][branch])
            else:
                branch = None                   # Could not find leaf, find new branch and try again
    return trunk, branch, leaf



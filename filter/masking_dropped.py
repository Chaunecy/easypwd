"""
We will mask some characters/chunks in passwords
"""
import argparse
import bisect
import math
import os.path
import pickle
import random
import sys
from collections import defaultdict
from functools import reduce
from typing import Callable, List, Dict, Set, Tuple


# @profile
def read_passwords(password_file: str, line_splits: Callable[[str], List[str]], is_valid: Callable[[str], bool]) \
        -> Dict[int, List[List[str]]]:
    """

    :param password_file: file containing passwords per line
    :param line_splits: split passwords into one or several items (i.e., characters or chunks)
    :param is_valid: is the line a valid password
    :return: passwords, each password is a list
    """
    line_dict = defaultdict(int)
    total_pwd = 0
    valid_pwd = 0
    with open(password_file, 'r') as fin:
        for line in fin:
            line = line.strip('\r\n')
            total_pwd += 1
            if not is_valid(line):
                continue
            valid_pwd += 1
            line_dict[line] += 1
            pass
        pass
    print(f"total passwords: {total_pwd}, valid passwords: {valid_pwd}", file=sys.stderr)
    passwords_per_len = defaultdict(list)
    for line, _ in line_dict.items():
        pwd = line_splits(line)
        passwords_per_len[len(pwd)].append(pwd)
    return passwords_per_len


def comb(n, m):
    large, small = max(m, n - m), min(m, n - m)
    prod = reduce(lambda x, y: x * y, list(range(large + 1, n + 1)), 1)
    d = reduce(lambda x, y: x * y, list(range(2, small + 1)), 1)

    return prod // d


# @profile
def masking(passwords: List[List[str]], p: float, min_visible: int, min_masked: int,
            num_masked_prob_cache: Dict[int, List[float]], mask='\t', dup_factor: int = 1,
            cleanup: int = 100000, threshold4cleanup: int = 1) \
        -> Dict[Tuple, Set[Tuple]]:
    pwd_mask_dict = {}
    cleanup = math.ceil(cleanup // dup_factor)
    cur_round = 0
    total_passwords = len(passwords)
    cur_pwd_idx = 0
    for pwd in passwords:
        n = len(pwd)
        max_masked = n - min_visible
        if max_masked < min_masked:
            raise Exception(f"The password should have at least {min_visible + min_masked} items, "
                            f"but {len(pwd)}: {pwd}")
            pass
        if n not in num_masked_prob_cache:
            prob_list = []
            total = 0
            for m in range(min_masked, max_masked + 1):
                c = comb(n, m)
                total += c * math.pow(p, m) * math.pow(1 - p, n - m)
                prob_list.append(total)
            prob_list = [prob / total for prob in prob_list]
            num_masked_prob_cache[n] = prob_list
            pass
        dup = dup_factor
        for _ in range(dup):
            idx = bisect.bisect_right(num_masked_prob_cache[n], random.random())
            m = min_masked + idx
            is_masks = [True] * m + [False] * (n - m)
            random.shuffle(is_masks)
            masked_pwd = tuple(mask if is_mask else item for item, is_mask in zip(pwd, is_masks))
            # print(masked_pwd)
            if masked_pwd not in pwd_mask_dict:
                pwd_mask_dict[masked_pwd] = set()
            pwd_mask_dict[masked_pwd].add(tuple(pwd))
            pass
        cur_round += 1
        cur_pwd_idx += 1
        if cur_round >= cleanup or cur_pwd_idx == total_passwords:
            origin_len = len(pwd_mask_dict)
            # cleanup keys whose corresponding values have at most five items.
            for masked_pwd in list(pwd_mask_dict.keys()):
                if len(pwd_mask_dict[masked_pwd]) <= threshold4cleanup:
                    del pwd_mask_dict[masked_pwd]
                pass
            print(
                f"[{cur_pwd_idx / total_passwords * 100:5.2f}%] "
                f"Cleaning up from {origin_len:8,} to {len(pwd_mask_dict):8,} templates",
                end='\r', file=sys.stderr)
            cur_round = 0
            pass
        pass
    print(" " * 80, end='\r', file=sys.stderr)
    return pwd_mask_dict


def save_templates(templates_dict: Dict[str, Set], save: str):
    n_dict = {}
    for cls_name, templates in templates_dict.items():
        n_dict[cls_name] = templates
    with open(save, 'wb') as f_save:
        pickle.dump(n_dict, f_save)
    pass


# @profile
def wrapper():
    cli = argparse.ArgumentParser("Masking passwords", description="""
    [README]
    This file read a password dataset (one password per line) and randomly generate
    templates by replacing some characters in the passwords with the wildcard ('\\t').
    """, usage="""
    <program> -i <password dataset> -o <folder saving results> --dupe <parsing each password several times>
    + using a larger `--dupe` if you obtain too few templates;
    + using `--cleanup` and `--threshold4cleanup` to save memory;
    """, )
    cli.add_argument("-i", "--input", dest="input", type=str, required=True, help='Passwords to parse')
    cli.add_argument('-o', '--output-folder', dest='output', type=str, required=False, default='',
                     help="Save sampled templates")
    cli.add_argument("--splitter", dest="splitter", type=str, required=False,
                     default='empty', help='split the password according to the splitter. '
                                           'Note that empty = ``, space = ` `, tab = `\\t`')
    cli.add_argument("-p", "--prob", dest="prob", type=float, required=False, default=0.5,
                     help="the probability of masking an item")
    cli.add_argument("-c", '--constraints', dest="constrains", type=int, nargs=2, required=False, default=[4, 5],
                     help='[a, b] refers to  we have at least `a` observable characters, `b` masked characters')
    cli.add_argument("-l", "--length-bound", dest="length_bound", type=str, required=False, default=16,
                     help='length longer than the bound will be ignored')
    cli.add_argument("-n", '--num-samples', dest='num_samples', type=int, default=30, required=False,
                     help='number of samples for each class of templates')
    cli.add_argument("-m", "--mask", dest="mask", type=str, required=False, default="\t",
                     help='the mask to replace the origin characters in passwords')
    cli.add_argument("--dup", dest="dup_factor", default=1, type=int, required=False,
                     help="Duplications when generating masks of a password")
    cli.add_argument("--cleanup", dest="cleanup", default=100000, type=int, required=False,
                     help='cleanup the templates which correspond to too few passwords '
                          '(depending on the `--threshold4cleanup` option)')
    cli.add_argument("--threshold4cleanup", dest='threshold4cleanup', default=1, type=int, required=False,
                     help='remove the template if its corresponding passwords is no more than `threshold4cleanup`')
    args = cli.parse_args()
    pwd_file, splitter, p, (min_visible, min_masked), length_upper_bound, num_samples = \
        args.input, args.splitter.lower(), args.prob, args.constrains, args.length_bound, args.num_samples
    output, mask, dup_factor = args.output, args.mask, args.dup_factor
    cleanup, threshold4cleanup = args.cleanup, args.threshold4cleanup
    length_lower_bound = min_masked + min_visible

    if output == '':
        print(f"\033[1;31;40m"
              f"Note that the `-o` option does not exist. Therefore we'll not save the results."
              f"\033[0m", file=sys.stderr)
    if splitter == 'empty':
        def line_splits(line: str):
            return list(line)
    else:
        splitter = {'space': ' ', 'tab': '\t'}.get(splitter, splitter)

        def line_splits(line: str):
            return line.split(splitter)

    def is_valid(line: str):
        return length_lower_bound <= len(line) <= length_upper_bound

    passwords_per_len = read_passwords(password_file=pwd_file, line_splits=line_splits, is_valid=is_valid)
    num_masked_prob_cache = {}
    classes = [
        ('super-rare', [1, 5]),
        ('rare', [10, 15]),
        ('uncommon', [50, 150]),
        ('common', [1000, 15000])
    ]
    if output != '' and not os.path.exists(output):
        os.mkdir(output)
    exist = os.path.exists(output)
    pwd_mask_list, template_list = [], []
    for pwd_len, passwords in sorted(passwords_per_len.items(), key=lambda x: x[0]):
        print(f"Parsing {len(passwords):10,} passwords with {pwd_len:2} items\r")
        random.shuffle(passwords)
        pwd_mask_dict = masking(
            passwords=passwords, p=p, min_visible=min_visible, min_masked=min_masked,
            num_masked_prob_cache=num_masked_prob_cache, mask=mask, dup_factor=dup_factor,
            cleanup=cleanup, threshold4cleanup=threshold4cleanup,
        )
        del passwords
        templates_dict = {}
        for masked_pwd, origins in pwd_mask_dict.items():
            for cls_name, (lower_bound, upper_bound) in classes:
                if lower_bound <= len(origins) <= upper_bound:
                    if cls_name not in templates_dict:
                        templates_dict[cls_name] = set()
                    templates_dict[cls_name].add(masked_pwd)
                    break
        for cls_name, templates in templates_dict.items():
            print(f"{cls_name:>12}: {len(templates):>6,}")
        if exist:
            pwd_mask_file = f"pwd_mask_dict_{pwd_len}.pickle"
            template_file = f"template_dict_{pwd_len}.pickle"
            with open(os.path.join(output, pwd_mask_file), 'wb') as f_out:
                pickle.dump(pwd_mask_dict, f_out)
            with open(os.path.join(output, template_file), 'wb') as f_template:
                pickle.dump(templates_dict, f_template)
            pwd_mask_list.append(pwd_mask_file)
            template_list.append(template_file)

        del pwd_mask_dict
        del templates_dict
    if exist and len(pwd_mask_list) > 0:
        with open(os.path.join(output, "file_list.pickle"), 'wb') as f_list:
            pickle.dump((pwd_mask_list, template_list), f_list)
    pass


if __name__ == '__main__':
    wrapper()

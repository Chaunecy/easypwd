#!/usr/bin/env python3
"""
convert files generated by Monte Carlo method in 2015 to my format
"""
import argparse
import sys
from collections import defaultdict
from typing import TextIO, Dict


def read_test(fd_test: TextIO):
    pwd_cnt = defaultdict(int)
    for line in fd_test:
        line = line.strip()
        try:
            p, cnt = line.split("\t")
            cnt = int(cnt)
        except Exception:
            p, cnt = line, 1
        pwd_cnt[p] += cnt
    fd_test.close()
    return pwd_cnt


def conv(ranked: TextIO, wanted: Dict[str, int], save2: TextIO, skip_lines: int, pwd_idx: int, rank_idx: int,
         prob_idx: int):
    pwd_rank = {}
    for _ in range(skip_lines):
        ranked.readline()
    for line in ranked:
        line = line.strip("\r\n")
        items = line.split("\t")
        pwd = items[pwd_idx]
        if pwd in pwd_rank:
            continue
        if pwd not in wanted:
            pwd_rank[pwd] = (wanted[pwd], sys.float_info.min, 10 ** 50)
            continue
        prob = sys.float_info.min if prob_idx == -1 else items[prob_idx]
        rank = items[rank_idx]
        if rank == 'inf' or rank == '-inf':
            rank = 10 ** 50
        pwd_rank[pwd] = (wanted[pwd], float(prob), float(rank))
    prev_rank = 0
    cracked = 0
    total = sum([n for n, _, _ in pwd_rank.values()])
    for pwd, (num, prob, rank) in sorted(pwd_rank.items(), key=lambda x: x[1][2]):
        cracked += num
        rank = round(max(rank, prev_rank + 1))
        prev_rank = rank
        save2.write(f"{pwd}\t{prob}\t{num}\t{rank}\t{cracked}\t{cracked / total * 100:5.2f}\n")


def main():
    cli = argparse.ArgumentParser("Monte Carlo 2015 results converter")
    cli.add_argument("-r", "--ranked", dest="ranked", required=True, type=argparse.FileType("r"),
                     help="result generated by Monte Carlo 2015")
    cli.add_argument("-s", "--save", dest="save", required=True, type=argparse.FileType("w"),
                     help="save converted file here")
    cli.add_argument("-t", "--test", dest="fd_test_set", required=True, type=argparse.FileType('r'),
                     help="test set")
    cli.add_argument("--skip", dest="skip", required=False, type=int, default=0, help="skip first N lines")
    cli.add_argument("--pwd-idx", dest="pwd_idx", required=False, type=int, default=0,
                     help="which column stores the password, start from 0")
    cli.add_argument("--rank-idx", dest="rank_idx", required=False, type=int, default=1,
                     help="which column stores the rank, start from 0")
    cli.add_argument("--prob-idx", dest="prob_idx", required=False, type=int, default=-1,
                     help="which column stores the prob, start from 0, set -1 to ignore prob")
    args = cli.parse_args()
    pwd_cnt = read_test(args.fd_test_set)
    conv(args.ranked, wanted=pwd_cnt, save2=args.save, skip_lines=args.skip, pwd_idx=args.pwd_idx,
         rank_idx=args.rank_idx, prob_idx=args.prob_idx)


if __name__ == '__main__':
    main()

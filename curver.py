"""
This file is to draw curves using json files generated by gcutify.
Make sure that matplotlib is accessible
"""
import argparse
import json
import os
import sys
from typing import TextIO, List, Any

import matplotlib.pyplot as plt


class DefaultVal:
    limlow = -1
    limhigh = -1
    empty_ticks = []
    auto_legend = None
    legendfontsize = 12


class PlotParams:
    def __init__(self, args: Any):
        self.xlabel = args.xlabel
        self.xlabelweight = args.xlabelweight
        self.xlabelsize = args.xlabelsize

        self.ylabel = args.ylabel
        self.ylabelweight = args.ylabelweight
        self.ylabelsize = args.ylabelsize

        self.xlimlow = args.xlimlow
        self.xlimhigh = args.xlimhigh

        self.ylimlow = args.ylimlow
        self.ylimhigh = args.ylimhigh

        self.xticksval = args.xticksval
        self.xtickstext = args.xtickstext

        if len(self.xticksval) != len(self.xtickstext):
            print(f"{self.xticksval} does not match {self.xtickstext}", file=sys.stderr)
            sys.exit(-1)

        self.yticksval = args.yticksval
        self.ytickstext = args.ytickstext

        if len(self.yticksval) != len(self.ytickstext):
            print(f"{self.yticksval} does not match {self.ytickstext}", file=sys.stderr)
            sys.exit(-1)

        self.ticksize = args.ticksize

        self.xscale = args.xscale
        self.yscale = args.yscale

        self.legendpos = args.legend_pos
        self.legendfontsize = args.legendfontsize

        self.settightlayout = args.tight

        self.save = args.fd_save
        if os.path.isdir(self.save):
            print(f"{self.save} is a directory, use a file please", file=sys.stderr)
            sys.exit(-1)


class LineParam:
    def __init__(self, guesses_list, rate_list, color, marker, linewidth, linestyle, label):
        self.guesses_list = guesses_list
        self.rate_list = rate_list
        self.color = color
        self.marker = marker
        self.linewidth = linewidth
        self.linestyle = linestyle
        self.label = label


def read_gcutify(json_file: TextIO, close_fd: bool):
    data = json.load(json_file)
    guesses_list = data["guesses_list"]
    cracked_list = data["cracked_list"]
    label = data["label"]
    color = data["color"]
    total = data["total"]
    marker = data["marker"]
    line_width = data["line_width"]
    line_style = data["line_style"]
    ratio_list = [cracked / total * 100 for cracked in cracked_list]
    del data
    del cracked_list
    if close_fd:
        json_file.close()
    elif json_file.seekable():
        json_file.seek(0)
    return LineParam(guesses_list, ratio_list, color, marker, line_width, line_style, label)


def curve(json_files: List[TextIO], plot_params: PlotParams, close_fd: bool = True):
    fig = plt.figure()
    if plot_params.settightlayout:
        fig.set_tight_layout(True)
    for json_file in json_files:
        line_params = read_gcutify(json_file=json_file, close_fd=close_fd)
        plt.plot(line_params.guesses_list, line_params.rate_list, color=line_params.color,
                 marker=line_params.marker, linewidth=line_params.linewidth,
                 linestyle=line_params.linestyle, label=line_params.label)
    plt.xscale(plot_params.xscale)
    plt.yscale(plot_params.yscale)
    if plot_params.xlimlow != DefaultVal.limlow and plot_params.xlimhigh != DefaultVal.limhigh:
        plt.xlim([plot_params.xlimlow, plot_params.xlimhigh])
    if plot_params.ylimlow != DefaultVal.limlow and plot_params.ylimhigh != DefaultVal.limhigh:
        plt.ylim([plot_params.ylimlow, plot_params.ylimhigh])
    plt.xlabel(xlabel=plot_params.xlabel,
               fontdict={"weight": plot_params.xlabelweight,
                         "size": plot_params.xlabelsize})
    plt.ylabel(ylabel=plot_params.ylabel,
               fontdict={"weight": plot_params.ylabelweight,
                         "size": plot_params.ylabelsize})
    if len(plot_params.yticksval) != len(DefaultVal.empty_ticks):
        plt.yticks(plot_params.yticksval, plot_params.ytickstext)
    if len(plot_params.xticksval) != len(DefaultVal.empty_ticks):
        plt.xticks(plot_params.xticksval, plot_params.xtickstext)
    plt.tick_params(labelsize=plot_params.ticksize)
    plt.grid(ls="--")
    if plot_params.legendpos is not DefaultVal.auto_legend:
        plt.legend(loc=int(plot_params.legendpos), fontsize=plot_params.legendfontsize)
    plt.savefig(plot_params.save)
    plt.close(fig)
    pass


def main():
    cli = argparse.ArgumentParser("Curver: An Easy Guess-Crack Curve Drawer")
    valid_suffix = [".pdf", ".png"]
    cli.add_argument("-f", "--files", required=True, dest="json_files", nargs="+", type=argparse.FileType("r"),
                     help="json files generated by gcutify")
    cli.add_argument("-s", "--save", required=True, dest="fd_save", type=str,
                     help="save figure here")
    cli.add_argument("--suffix", dest="suffix", required=False, default=".pdf", type=str, choices=valid_suffix,
                     help="suffix of file to save figure, if specified file ends with 'suffix', "
                          "suffix here will be ignored.")
    cli.add_argument("-x", "--xlabel", required=False, dest="xlabel", type=str, default="Guesses",
                     help="what does x axis mean")
    cli.add_argument("-y", "--ylabel", required=False, dest="ylabel", type=str, default="Cracked",
                     help="what does y axis mean")
    cli.add_argument("--xlabelweight", required=False, dest="xlabelweight", type=str, default="normal",
                     choices=["normal", "bold"], help="weight of x label")
    cli.add_argument("--ylabelweight", required=False, dest="ylabelweight", type=str, default="normal",
                     choices=["normal", "bold"], help="weight of y label")
    cli.add_argument("--xlabelsize", required=False, dest="xlabelsize", type=float, default=12,
                     help="size of x label")
    cli.add_argument("--ylabelsize", required=False, dest="ylabelsize", type=float, default=12,
                     help="size of y label")
    cli.add_argument("--xlimlow", required=False, dest="xlimlow", type=float, default=DefaultVal.limlow,
                     help="lower bound of x")
    cli.add_argument("--xlimhigh", required=False, dest="xlimhigh", type=float, default=DefaultVal.limhigh,
                     help="upper bound of x")
    cli.add_argument("--ylimlow", required=False, dest="ylimlow", type=float, default=DefaultVal.limlow,
                     help="lower bound of y")
    cli.add_argument("--ylimhigh", required=False, dest="ylimhigh", type=float, default=DefaultVal.limhigh,
                     help="upper bound of y")
    cli.add_argument("--xticksval", required=False, dest="xticksval", nargs="+", type=float,
                     default=DefaultVal.empty_ticks,
                     help="value of x ticks")
    cli.add_argument("--xtickstext", required=False, dest="xtickstext", nargs="+", type=float,
                     default=DefaultVal.empty_ticks,
                     help="text of x ticks")
    cli.add_argument("--yticksval", required=False, dest="yticksval", nargs="+", type=float,
                     default=DefaultVal.empty_ticks,
                     help="value of y ticks")
    cli.add_argument("--ytickstext", required=False, dest="ytickstext", nargs="+", type=float,
                     default=DefaultVal.empty_ticks,
                     help="text of y ticks")
    cli.add_argument("--ticksize", required=False, dest="ticksize", type=float, default=12,
                     help="size of ticks text")
    cli.add_argument("--legendpos", required=False, dest="legend_pos", type=str, default=DefaultVal.auto_legend,
                     choices=["upper left", "upper right", "bottom left", "bottom right"],
                     help="set it to -2 if you dont want use label")
    cli.add_argument("--legendfontsize", required=False, dest="legendfontsize", type=float,
                     default=DefaultVal.legendfontsize, help="font size of legend")
    cli.add_argument("--xscale", required=False, dest="xscale", type=str, default="log",
                     choices=["linear", "log", "symlog", "logit"], help="scale x axis")
    cli.add_argument("--yscale", required=False, dest="yscale", type=str, default="linear",
                     choices=["linear", "log", "symlog", "logit"], help="scale y axis")
    cli.add_argument("--tight", required=False, dest="tight", type=bool, default=True, help="tight layout of figure")

    args = cli.parse_args()
    suffix_ok = any([args.fd_save.endswith(suffix) for suffix in valid_suffix])
    if not suffix_ok:
        args.fd_save += args.suffix
    plot_params = PlotParams(args)
    curve(json_files=args.json_files, plot_params=plot_params, close_fd=True)
    pass


if __name__ == '__main__':
    main()

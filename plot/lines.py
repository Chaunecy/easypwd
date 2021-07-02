"""
This file is to draw curves using json files generated by gutify.
Make sure that matplotlib is accessible
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from typing import TextIO, List, Any

import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerTuple
import matplotlib

matplotlib.rcParams['pdf.fonttype'] = 42


class DefaultVal:
    lim_low = -1
    lim_high = -1
    empty_ticks = []
    legend = "none"
    legend_fontsize = 12


class PlotParams:
    def __init__(self, args: Any):
        self.xlabel = args.xlabel
        self.xlabel_weight = args.xlabel_weight
        self.xlabel_size = args.xlabel_size

        self.ylabel = args.ylabel
        self.ylabel_weight = args.ylabel_weight
        self.ylabel_size = args.ylabel_size

        self.xlim_low = args.xlim_low
        self.xlim_high = args.xlim_high

        self.ylim_low = args.ylim_low
        self.ylim_high = args.ylim_high

        self.xticks_val = args.xticks_val
        self.xticks_text = args.xticks_text
        self.xtick_direction = args.xtick_direction

        if len(self.xticks_val) != len(self.xticks_text):
            print(f"{self.xticks_val} does not match {self.xticks_text}", file=sys.stderr)
            sys.exit(-1)

        self.yticks_val = args.yticks_val
        self.yticks_text = args.yticks_text
        self.ytick_direction = args.ytick_direction

        if len(self.yticks_val) != len(self.yticks_text):
            print(f"{self.yticks_val} does not match {self.yticks_text}", file=sys.stderr)
            sys.exit(-1)

        self.tick_size = args.tick_size

        self.xscale = args.xscale
        self.yscale = args.yscale

        self.legend_loc = args.legend_loc
        self.legend_fontsize = args.legend_fontsize
        self.legend_handle_length = args.legend_handle_length
        self.legend_frameon = args.legend_frameon

        self.tight_layout = not args.no_tight

        self.vlines = args.vlines
        self.vline_width = args.vline_width
        self.vline_color = args.vline_color
        self.vline_style = args.vline_style
        self.vline_label = args.vline_label

        self.show_grid = args.show_grid
        self.grid_linestyle = args.grid_linestyle

        self.fig_size = args.fig_size
        self.no_boarder = args.no_boarder
        self.show_text = args.show_text
        self.use_rate = not args.use_acc_freq

        if not (len(self.vlines) == len(self.vline_width) == len(self.vline_color) == len(self.vlines)):
            print(f"vlines should have same number of parameters", file=sys.stderr)
            sys.exit(-1)
            pass
        if len(self.vline_label) != 0 and len(self.vline_label) != len(self.vlines):
            print(f"vlines should have same number of parameters", file=sys.stderr)
            sys.exit(-1)

        self.vline_label_hide = len(self.vline_label) == 0
        if self.vline_label_hide:
            self.vline_label = ["" for _ in range(len(self.vlines))]

        self.save = args.fd_save
        if os.path.isdir(self.save):
            print(f"{self.save} is a directory, use a file please", file=sys.stderr)
            sys.exit(-1)


class LineParam:
    def __init__(self, json_file: TextIO, close_fd: bool, use_rate: bool = True):
        data = json.load(json_file)
        y_list = data["y_list"]
        total = data["total"]
        if use_rate:
            y_list = [cracked / total * 100 for cracked in y_list]
        if close_fd:
            json_file.close()
        elif json_file.seekable():
            json_file.seek(0)
        self.x_list = data["x_list"]
        self.y_list = y_list
        self.color = data['color']
        self.marker = data['marker']
        self.marker_size = data['marker_size']
        self.mark_every = data["mark_every"]
        self.line_width = data['line_width']
        if type(data['line_style']) is str:
            self.line_style = data['line_style']
        else:
            self.line_style = (data['line_style'][0], tuple(list(data['line_style'][1])))
        self.label = data['label']
        self.text = data['label']
        self.show_text = data['show_text']
        self.text_x = data['text_x']
        self.text_y = data['text_y']
        self.text_fontsize = data['text_fontsize']
        self.text_color = data['text_color']


def curve(json_files: List[TextIO], plot_params: PlotParams, close_fd: bool = True):
    fig = plt.figure(figsize=plot_params.fig_size)
    fig.set_tight_layout(plot_params.tight_layout)
    label_line = defaultdict(list)
    for json_file in json_files:
        line_params = LineParam(json_file=json_file, close_fd=close_fd, use_rate=plot_params.use_rate)
        line, = plt.plot(line_params.x_list, line_params.y_list, color=line_params.color,
                         marker=line_params.marker, markersize=line_params.marker_size,
                         markevery=line_params.mark_every, linewidth=line_params.line_width,
                         linestyle=line_params.line_style, label=line_params.label)
        if plot_params.show_text and line_params.show_text:
            plt.text(x=line_params.text_x, y=line_params.text_y, s=line_params.label,
                     c=line_params.text_color, fontsize=line_params.text_fontsize)
        label_line[line_params.label].append(line)
        del line_params
    plt.xscale(plot_params.xscale)
    plt.yscale(plot_params.yscale)
    if plot_params.xlim_low != DefaultVal.lim_low:
        plt.xlim(left=plot_params.xlim_low)
    if plot_params.xlim_high != DefaultVal.lim_high:
        plt.xlim(right=plot_params.xlim_high)
    if plot_params.ylim_low != DefaultVal.lim_low:
        plt.ylim(bottom=plot_params.ylim_low)
    if plot_params.ylim_high != DefaultVal.lim_high:
        plt.ylim(top=plot_params.ylim_high)
    plt.xlabel(xlabel=plot_params.xlabel,
               fontdict={"weight": plot_params.xlabel_weight,
                         "size": plot_params.xlabel_size})
    plt.ylabel(ylabel=plot_params.ylabel,
               fontdict={"weight": plot_params.ylabel_weight,
                         "size": plot_params.ylabel_size})
    if len(plot_params.yticks_val) != len(DefaultVal.empty_ticks):
        plt.yticks(plot_params.yticks_val, plot_params.yticks_text)
    if len(plot_params.xticks_val) != len(DefaultVal.empty_ticks):
        plt.xticks(plot_params.xticks_val, plot_params.xticks_text)
    # direction and size of ticks
    plt.tick_params(axis='x', labelsize=plot_params.tick_size, direction=plot_params.xtick_direction)
    plt.tick_params(axis='y', labelsize=plot_params.tick_size, direction=plot_params.ytick_direction)
    plt.tick_params(axis='both', which='minor', length=0)
    # v line
    for vline_x, vline_width, vline_color, vline_style, vline_label in \
            zip(plot_params.vlines, plot_params.vline_width,
                plot_params.vline_color, plot_params.vline_style, plot_params.vline_label):
        line = plt.axvline(x=vline_x, linewidth=vline_width, color=vline_color, linestyle=vline_style,
                           label=vline_label)
        if not plot_params.vline_label_hide:
            label_line[vline_label].append(line)
    # display grid
    if plot_params.show_grid:
        plt.grid(b=True, ls=plot_params.grid_linestyle)
    # hide which boarder
    ax = plt.gca()
    for direction in plot_params.no_boarder:
        ax.spines[direction].set_color('none')
    if plot_params.legend_loc != DefaultVal.legend:
        plt.legend([tuple(label_line[k]) for k in label_line.keys()],
                   [label for label in label_line.keys()],
                   handlelength=plot_params.legend_handle_length,
                   loc=plot_params.legend_loc,
                   fontsize=plot_params.legend_fontsize,
                   handler_map={tuple: HandlerTuple(ndivide=1)}, frameon=plot_params.legend_frameon)
    plt.savefig(plot_params.save)
    plt.close(fig)
    pass


def main():
    line_style_dict = {
        "solid": "-",
        "dash": "--",
        "dot_dash": "-.",
        "dot": ":"
    }
    cli = argparse.ArgumentParser("Curver: An Easy Guess-Crack Curve Drawer")
    valid_suffix = [".pdf", ".png"]
    cli.add_argument("-f", "--files", required=True, dest="json_files", nargs="+", type=argparse.FileType("r"),
                     help="json files generated by gcutify")
    cli.add_argument("-s", "--save", required=True, dest="fd_save", type=str,
                     help="save figure here")
    cli.add_argument("--suffix", dest="suffix", required=False, default=".pdf", type=str, choices=valid_suffix,
                     help="suffix of file to save figure, if specified file ends with 'suffix', "
                          "suffix here will be ignored.")
    cli.add_argument("-x", "--xlabel", required=False, dest="xlabel", type=str, default="X-axis",
                     help="what does x axis mean")
    cli.add_argument("-y", "--ylabel", required=False, dest="ylabel", type=str, default="Y-axis",
                     help="what does y axis mean")
    cli.add_argument("--xlabel-weight", required=False, dest="xlabel_weight", type=str, default="normal",
                     choices=["normal", "bold"], help="weight of x label")
    cli.add_argument("--ylabel-weight", required=False, dest="ylabel_weight", type=str, default="normal",
                     choices=["normal", "bold"], help="weight of y label")
    cli.add_argument("--xlabel-size", required=False, dest="xlabel_size", type=float, default=12,
                     help="size of x label")
    cli.add_argument("--ylabel-size", required=False, dest="ylabel_size", type=float, default=12,
                     help="size of y label")
    cli.add_argument("--xlim-low", required=False, dest="xlim_low", type=float, default=DefaultVal.lim_low,
                     help="lower bound of x")
    cli.add_argument("--xlim-high", required=False, dest="xlim_high", type=float, default=DefaultVal.lim_high,
                     help="upper bound of x")
    cli.add_argument("--ylim-low", required=False, dest="ylim_low", type=float, default=DefaultVal.lim_low,
                     help="lower bound of y")
    cli.add_argument("--ylim-high", required=False, dest="ylim_high", type=float, default=DefaultVal.lim_high,
                     help="upper bound of y")
    cli.add_argument("--xticks-val", required=False, dest="xticks_val", nargs="+", type=float,
                     default=DefaultVal.empty_ticks,
                     help="value of x ticks")
    cli.add_argument("--xticks-text", required=False, dest="xticks_text", nargs="+", type=str,
                     default=DefaultVal.empty_ticks,
                     help="text of x ticks")
    cli.add_argument("--xtick-direction", required=False, dest="xtick_direction", type=str, default='out',
                     choices=['in', 'out', 'inout'], help='Direction of xtick')
    cli.add_argument("--ytick-direction", required=False, dest="ytick_direction", type=str, default='out',
                     choices=['in', 'out', 'inout'], help='Direction of ytick')
    cli.add_argument("--yticks-val", required=False, dest="yticks_val", nargs="+", type=float,
                     default=DefaultVal.empty_ticks,
                     help="value of y ticks")
    cli.add_argument("--yticks-text", required=False, dest="yticks_text", nargs="+", type=str,
                     default=DefaultVal.empty_ticks,
                     help="text of y ticks")
    cli.add_argument("--tick-size", required=False, dest="tick_size", type=float, default=12,
                     help="size of ticks text")
    cli.add_argument("--legend-loc", required=False, dest="legend_loc", type=str, default=DefaultVal.legend,
                     choices=[DefaultVal.legend, "best", "upper left", "upper right", "lower left", "lower right"],
                     help="set it to none if you dont want use label")
    cli.add_argument("--legend-fontsize", required=False, dest="legend_fontsize", type=float,
                     default=DefaultVal.legend_fontsize, help="font size of legend")
    cli.add_argument("--legend-handle-length", required=False, dest="legend_handle_length", type=float, default=2,
                     help="legend handle length")
    cli.add_argument("--legend-frameon", required=False, dest="legend_frameon", action="store_true",
                     help="show boarder of the legend")
    cli.add_argument("--xscale", required=False, dest="xscale", type=str, default="log",
                     choices=["linear", "log", "symlog", "logit"], help="scale x axis")
    cli.add_argument("--yscale", required=False, dest="yscale", type=str, default="linear",
                     choices=["linear", "log", "symlog", "logit"], help="scale y axis")
    cli.add_argument("--tight", required=False, dest="tight",
                     default=lambda: bool(print("Use --no-tight please, we set tight layout by default now")),
                     action="store_true", help="tight layout of figure. Use --no-tight and"
                                               "do not use this option anymore.", )
    cli.add_argument("--no-tight", required=False, dest="no_tight", default=False, action="store_true",
                     help="no tight layout of figure")
    cli.add_argument("--vlines", required=False, dest="vlines", type=float, nargs="*", default=[],
                     help="vlines in the figure")
    cli.add_argument("--vline-width", required=False, dest="vline_width", type=float, nargs="*", default=[],
                     help="line width for vines")
    cli.add_argument("--vline-color", required=False, dest="vline_color", type=str, nargs="*", default=[],
                     help="colors for vlines in the figure")
    cli.add_argument("--vline-style", required=False, dest="vline_style", type=str, nargs="*", default=[],
                     choices=list(line_style_dict.keys()),
                     help="styles for vlines in the figure")
    cli.add_argument("--vline-label", required=False, dest="vline_label", type=str, nargs="*", default=[],
                     help="labels for vlines in the figure. Do not set if you don't want to show these labels.")
    cli.add_argument("--show-grid", required=False, dest="show_grid", action="store_true",
                     help="show grid")
    cli.add_argument("--grid-linestyle", required=False, dest="grid_linestyle", type=str, default="dash",
                     choices=list(line_style_dict.keys()))
    cli.add_argument("--fig-size", required=False, dest="fig_size",
                     type=lambda x: tuple([float(f) for f in str(x).split(" ") if len(f) > 0]), default=None,
                     help="`width height` wrapped by \' and split by space")
    cli.add_argument("--no-boarder", required=False, dest="no_boarder", type=str, nargs='*',
                     default=[], choices=["left", "bottom", "top", "right"],
                     help='do not display boarder listed here')
    cli.add_argument("--show-text", required=False, dest="show_text", action="store_true",
                     help="show label text at right")
    cli.add_argument("--use-acc-freq", required=False, dest="use_acc_freq", action="store_true",
                     help="Use the acc freq of y, e.g., y_1 = 1, total = 10, "
                          "then we display y_1 = 1 instead of 1/10 in the figure")
    args = cli.parse_args()
    suffix_ok = any([args.fd_save.endswith(suffix) for suffix in valid_suffix])
    if not suffix_ok:
        args.fd_save += args.suffix
    args.vline_style = [line_style_dict[vline_style] for vline_style in args.vline_style]
    args.grid_linestyle = line_style_dict[args.grid_linestyle]
    plot_params = PlotParams(args)
    curve(json_files=args.json_files, plot_params=plot_params, close_fd=True)
    pass


if __name__ == '__main__':
    main()

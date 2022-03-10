"""
This file is to draw curves using json files generated by gutify.
Make sure that matplotlib is accessible

python3 lines.py \
    -f j4rank-1.json ... j4rank-n.json \
    --xlabel 'Guesses' \
    --ylabel 'Percent guessed (%)' \
    --xlabel-size 24 \
    --ylabel-size 24 \
    --legend-loc 'none' \
    --legend-fontsize 22 \
    --tick-size 22 \
    --ylim-high 100 \
    --ylim-low 0 \
    --xlim-low 1 \
    --xlim-high "10000000000" \
    --xticks-val 10 10000 10000000 10000000000 10000000000000 10000000000000000 \
    --xticks-text  '$10^{1}$' '$10^{4}$' '$10^{7}$' '$10^{10}$' '$10^{13}$' '$10^{16}$' \
    --yticks-val 0 20 40 60 80 100 \
    --yticks-text '0' '20' '40' '60' '80' '100' \
    --legend-handle-length 4 \
    --tight \
    --show-grid \
    --fig-size "8 4.95" \
    -s savefig.pdf
"""
import argparse
import json
import os

import pickle
import sys
from collections import defaultdict
from typing import TextIO, List, Any, Dict

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.legend_handler import HandlerTuple
import matplotlib
from matplotlib.patches import Patch
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

matplotlib.rcParams['pdf.fonttype'] = 42


def conf_font(font_name):
    plt.rcParams['font.sans-serif'] = [font_name]
    plt.rcParams['axes.unicode_minus'] = False


class DefaultVal:
    lim_low = -1
    lim_high = -1
    empty_ticks = []
    legend = "none"
    legend_fontsize = 12


class SubParams:
    def __init__(self, args: Any):
        self.use_inset_axes = args.inset_axes is not None
        if not isinstance(args.subfig_xticks, list) or \
                not isinstance(args.subfig_xticklabels, list) or \
                len(args.subfig_xticks) != len(args.subfig_xticklabels):
            print(f"Make sure that --subfig-xticks ({len(args.subfig_xticks)}) "
                  f"has the same number of elements with --subfig-xticklabels ({len(args.subfig_xticklabels)})",
                  file=sys.stderr)
            sys.exit(1)
        if not isinstance(args.subfig_yticks, list) or \
                not isinstance(args.subfig_yticklabels, list) or \
                len(args.subfig_yticks) != len(args.subfig_yticklabels):
            print(f"Make sure that --subfig-yticks has the same number of elements with --subfig-yticklabels",
                  file=sys.stderr)
            sys.exit(1)
        self.inset_axes = args.inset_axes
        self.xmin = args.subfig_xmin
        self.xmax = args.subfig_xmax
        self.ymin = args.subfig_ymin
        self.ymax = args.subfig_ymax
        self.xticks = args.subfig_xticks
        self.yticks = args.subfig_yticks
        self.xticklabels = args.subfig_xticklabels
        self.yticklabels = args.subfig_yticklabels
        self.tickfontsize = args.subfig_tickfontsize
        self.mark_inset = args.mark_inset or (2, 4)
        pass


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

        self.patches = args.patches

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
        self.sub_params = SubParams(args)


class LineParam:
    def __init__(self, json_file: TextIO, close_fd: bool):
        """
        Note that x_list, y_list and total are required, while others are optional
        :param json_file: json file
        :param close_fd: close json file
        """
        data: Dict[Any, Any] = json.load(json_file)
        y_list = data["y_list"]
        need_divide_total = data.get('need_divide_total', True)
        if need_divide_total and data.get("total", -1) > 0:
            total = data["total"]
            y_list = [cracked / total * 100 for cracked in y_list]
        if close_fd:
            json_file.close()
        elif json_file.seekable():
            json_file.seek(0)
        self.x_list = data["x_list"]
        self.y_list = y_list
        self.color = data.get('color') or "black"
        self.marker = data.get('marker') or None
        self.marker_size = data.get('marker_size') or None
        self.mark_every = data.get("mark_every") or None
        self.line_width = data.get('line_width') or 1.2
        if data.get("line_style"):
            if type(data['line_style']) is str:
                self.line_style = data['line_style']
            else:
                self.line_style = (data['line_style'][0], tuple(list(data['line_style'][1])))
        else:
            self.line_style = "-"
        self.label = data.get('label') or ""
        self.text = data.get('label') or ""
        self.show_text = data.get('show_text') or False
        self.text_x = data.get('text_x') or -1
        self.text_y = data.get('text_y') or -1
        self.text_fontsize = data.get('text_fontsize') or 12
        self.text_color = data.get('text_color') or "black"
        self.show_label = data.get('show_label') or False


def curve(json_files: List[TextIO], plot_params: PlotParams, close_fd: bool = True):
    fig = plt.figure(figsize=plot_params.fig_size)
    fig.set_tight_layout(plot_params.tight_layout)
    label_line = defaultdict(list)
    ax = plt.gca()
    inner = None
    if plot_params.sub_params.use_inset_axes:
        inner = ax.inset_axes(plot_params.sub_params.inset_axes)
        pass
    for json_file in json_files:
        line_params = LineParam(json_file=json_file, close_fd=close_fd)
        line, = plt.plot(line_params.x_list, line_params.y_list, color=line_params.color,
                         marker=line_params.marker, markersize=line_params.marker_size,
                         markevery=line_params.mark_every, linewidth=line_params.line_width,
                         linestyle=line_params.line_style, label=line_params.label)
        if inner is not None:
            inner.plot(line_params.x_list, line_params.y_list, color=line_params.color,
                       marker=line_params.marker, markersize=line_params.marker_size,
                       markevery=line_params.mark_every, linewidth=line_params.line_width,
                       linestyle=line_params.line_style, label=line_params.label)
        if plot_params.show_text and line_params.show_text:
            plt.text(x=line_params.text_x, y=line_params.text_y, s=line_params.label,
                     c=line_params.text_color, fontsize=line_params.text_fontsize)
        if line_params.show_label:
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
        plt.grid(visible=True, ls=plot_params.grid_linestyle)
    # hide which boarder
    for direction in plot_params.no_boarder:
        ax.spines[direction].set_color('none')
    for patch in plot_params.patches:
        if isinstance(patch, Artist):
            ax.add_artist(patch)
        elif isinstance(patch, Patch):
            ax.add_patch(patch)
    if inner is not None:
        sub_params = plot_params.sub_params
        inner.set_xscale(plot_params.xscale)
        inner.set_yscale(plot_params.yscale)
        __xmin, __xmax = sub_params.xmin or plot_params.xlim_low, sub_params.xmax or plot_params.xlim_high
        inner.set_xlim(xmin=__xmin, xmax=__xmax)
        __ymin, __ymax = sub_params.ymin or plot_params.ylim_low, sub_params.ymax or plot_params.ylim_high
        inner.set_ylim(ymin=__ymin, ymax=__ymax)
        if len(sub_params.xticks) == 0 or len(sub_params.xticklabels) == 0:
            x_indices = [__idx for __idx, __val in enumerate(plot_params.xticks_val) if __xmin <= __val <= __xmax]
            sub_params.xticks = [plot_params.xticks_val[i] for i in x_indices]
            sub_params.xticklabels = [plot_params.xticks_text[i] for i in x_indices]
        print(sub_params.xticks)
        inner.set_xticks(sub_params.xticks)
        if len(sub_params.yticks) == 0 or len(sub_params.yticklabels) == 0:
            y_indices = [__idx for __idx, __val in enumerate(plot_params.yticks_val) if __ymin <= __val <= __ymax]
            sub_params.yticks = [plot_params.yticks_val[i] for i in y_indices]
            sub_params.yticklabels = [plot_params.yticks_text[i] for i in y_indices]
        inner.set_yticks(sub_params.yticks or plot_params.yticks_val)
        inner.set_xticklabels(sub_params.xticklabels,
                              fontdict={'size': sub_params.tickfontsize or plot_params.tick_size})
        inner.set_yticklabels(sub_params.yticklabels,
                              fontdict={'size': sub_params.tickfontsize or plot_params.tick_size})
        inner.tick_params(axis='both', which='minor', length=0)
        mark_inset(ax, inner, loc1=sub_params.mark_inset[0], loc2=sub_params.mark_inset[1])
        pass

    if plot_params.legend_loc != DefaultVal.legend:
        ax.legend([tuple(label_line[k]) for k in label_line.keys()],
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
        "dashed": "--",
        "dash": "--",
        "dot_dash": '-.',
        "dashdot": "-.",
        "dot": ":",
        "dotted": ":"
    }
    cli = argparse.ArgumentParser("Curver: An Easy Guess-Crack Curve Drawer")
    valid_suffix = [".pdf", ".png", '.svg']
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
    cli.add_argument("--font", required=False, dest="global_font", default=None, type=str,
                     help="set the font, could be Chinese font")
    cli.add_argument("--inset-axes", required=False, dest='inset_axes', default=None, nargs=4, type=float,
                     help="(x y w h), (x, y) represents the position of the bottom left corner, "
                          "(w, h) represents the width and the height of the subfig")
    cli.add_argument("--subfig-xmin", required=False, dest="subfig_xmin", type=float, default=0.0,
                     help="the minimum x to show in the subfig")
    cli.add_argument("--subfig-xmax", required=False, dest="subfig_xmax", type=float, default=0.0,
                     help="the maximum x to show in the subfig")
    cli.add_argument("--subfig-ymin", required=False, dest="subfig_ymin", type=float, default=0.0,
                     help="the minimum y to show in the subfig")
    cli.add_argument("--subfig-ymax", required=False, dest="subfig_ymax", type=float, default=0.0,
                     help="the maximum y to show in the subfig")
    cli.add_argument("--subfig-xticks", required=False, dest="subfig_xticks", type=float, nargs='+',
                     default=[], help="x ticks for subfig")
    cli.add_argument("--subfig-xticklabels", required=False, dest="subfig_xticklabels", type=str, nargs='+',
                     default=[], help="x tick labels for subfig")
    cli.add_argument("--subfig-yticks", required=False, dest="subfig_yticks", type=float, nargs='+',
                     default=[], help="y ticks for subfig")
    cli.add_argument("--subfig-yticklabels", required=False, dest="subfig_yticklabels", type=str, nargs='+',
                     default=[], help="y tick labels for subfig")
    cli.add_argument("--subfig-tick-size", required=False, dest="subfig_tickfontsize", type=int,
                     help="fontsize of the ticks")
    cli.add_argument("--mark-inset", required=False, nargs=2, type=int, choices=[1, 2, 3, 4], default=(2, 4),
                     help="mark inset for subfig")

    def patch_type(v):
        """
        read the pickle file and obtain the list of patches
        :param v: pickle file which contains a list of patches
        :return: parsed patches
        """
        try:
            with open(v, 'rb') as fin:
                res = pickle.load(fin)
                return res
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(-1)
        pass

    cli.add_argument("--patches", required=False, dest="patches", default=[], type=patch_type,
                     help="Specify the pickle file which contains the list of patches")
    args = cli.parse_args()
    if args.global_font is not None:
        conf_font(args.global_font)
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

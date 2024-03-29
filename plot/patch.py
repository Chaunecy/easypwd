import argparse
import json
import pickle
import typing
from json import JSONDecodeError

import sys

try:
    from matplotlib.artist import Artist
    from matplotlib.patches import ConnectionPatch, Ellipse
    from matplotlib.text import Text, Annotation
except ImportError:
    print("Error when importing matplotlib. Please install it and then run the code again!\n"
          "\t/path/to/your/python -m pip install matplotlib")
    sys.exit(5)

arrow_styles = ['-', '<-', '->', '<->', '<|-', '-|>', '<|-|>', ']-[', ']-', '-[', '|-|', 'simple', 'fancy', 'wedge']
connection_styles = ['arc3', 'angle3', 'angle', 'arc', 'bar']
coords = ["figure points", "figure pixels", "figure fraction", "subfigure points",
          "subfigure pixels", "subfigure faction", "axes points", 'axes pixels',
          'axes fraction',
          'data', 'polar']
func_name = "from_argv"
save_name = "--save"


def get_sub_classes(base: type, attr_name='name') -> typing.Dict[str, type]:
    d = {}
    assert hasattr(base, attr_name)
    for sub_cls in base.__subclasses__():

        if not hasattr(sub_cls, attr_name):
            continue
        val = getattr(sub_cls, attr_name)
        if not callable(val):
            d[val] = sub_cls
        else:
            print(f"{val.__name__} in {sub_cls.__name__} is callable")
    return d


# con = ConnectionPatch((0.2, 0.2), (0.8, 0.8), "data", "data", arrowstyle="->", shrinkA=5, shrinkB=5,
#                       mutation_scale=20,
#                       facecolor="white", mutation_aspect=0.8, connectionstyle=ConnectionStyle.Arc3())
# ax.add_artist(con)
# plt.show()

class Base:
    name = "base"

    @staticmethod
    def from_argv(argv: typing.List[str]) -> typing.Tuple[typing.Dict, Artist]:
        raise NotImplementedError


class AugAnnotation(Base):
    name = "annotation"

    @staticmethod
    def from_argv(argv: typing.List[str]):
        cli = argparse.ArgumentParser(f"Checking {AugConn.name} configuration")
        cli.add_argument("--text", dest="text", type=str, required=True, help="the text of the annotation")
        cli.add_argument("--xy", dest="xy", type=float, required=True, nargs=2,
                         help="the (x, y) point to annotate based on xy-coords")
        cli.add_argument("--xy-text", dest="xy_text", type=float, required=False, nargs=2, default=None,
                         help="The position (x, y) to place the text at based on text-coords")
        cli.add_argument("--xy-coords", dest="xy_coords", type=str, required=False, default="data",
                         choices=coords)
        cli.add_argument("--text-coords", dest="text_coords", type=str, required=False, default="data",
                         choices=[*coords, 'offset points', 'offset pixels'])
        cli.add_argument("--arrow-props", dest="arrow_props", nargs="+", type=str, required=False,
                         help="Specify the `width`, `headwidth`, etc. of the arrow if your are the expert of the "
                              "Matplotlib. Or you can look up the manual. "
                              "One example is --arrow-props width=1 headwidth=2")
        cli.add_argument("--expert", dest="expert", type=str, nargs='+', required=False, default=[],
                         help="If you are an expert of Matplotlib, you may set additional configurations here.\n"
                              "E.g., --expert color=red facecolor=blue")
        if not argv:
            cli.print_help()
            return {}, None
        got_args = cli.parse_args(argv)
        expert_opts = parse_expert(got_args.expert)
        arrow_props = parse_expert(got_args.arrow_props)
        conf = dict(text=got_args.text, xy=got_args.xy, xytext=got_args.xy_text or got_args.xy,
                    xycoords=got_args.xy_coords, textcoords=got_args.text_coords,
                    arrowprops=arrow_props, **expert_opts)
        art = Annotation(**conf)
        return conf, art


class AugText(Base):
    name = "text"

    @staticmethod
    def from_argv(argv: typing.List[str]):
        cli = argparse.ArgumentParser(f"Checking {AugText.name} configuration")

        cli.add_argument("-x", "--x-coord", dest="x", type=float, required=True, help="x of the annotation text")
        cli.add_argument("-y", "--y-coord", dest="y", type=float, required=True, help="y of the annotation text")
        cli.add_argument("-t", "--text", dest="text", type=str, required=True, help="annotation text")
        cli.add_argument("--expert", dest="expert", type=str, nargs='+', required=False, default=[],
                         help="If you are an expert of Matplotlib, you may set additional configurations here.\n"
                              "E.g., --expert color=red facecolor=blue")
        if not argv:
            cli.print_help()
            return {}, None
        got_args = cli.parse_args(argv)
        expert_opts = parse_expert(got_args.expert)
        conf = dict(x=got_args.x, y=got_args.y, text=got_args.text, **expert_opts)
        art = Text(**conf)
        return conf, art


class AugConn(Base):
    name = "connection"

    @staticmethod
    def from_argv(argv: typing.List[str]):
        cli = argparse.ArgumentParser(f"Checking {AugConn.name} configuration")

        cli.add_argument("-a", "--a-xy", dest="a", type=float, nargs=2, required=True,
                         help="(x, y) of one end of the connection line")
        cli.add_argument("-b", "--b-xy", dest="b", type=float, required=True,
                         help="(x, y) of the other end of the connection line")

        cli.add_argument("--arrow-style", dest="arrow_style", type=str, required=False, default="-|>",
                         choices=arrow_styles, help="arrow styles")
        cli.add_argument("--conn-style", dest="conn_style", type=str, required=False, default="",
                         choices=connection_styles, help="connection styles")
        cli.add_argument("--shrink", dest="shrink", type=float, nargs=2, required=False, default=(0.0, 0.0),
                         help="(shrink a, shrink b), refers to the gap between the connection and the two ends")
        cli.add_argument("--expert", dest="expert", type=str, nargs='+', required=False, default=[],
                         help="If you are an expert of Matplotlib, you may set additional configurations here.\n"
                              "E.g., --expert color=red facecolor=blue")
        if not argv:
            cli.print_help()
            return {}, None
        got_args = cli.parse_args(argv)
        expert_opts = parse_expert(got_args.expert)
        conf = dict(xyA=got_args.a, xyB=got_args.b, coordsA="data", coordsB="data", arrowstyle=got_args.arrow_style,
                    connectionstyle=got_args.conn_style, shrinkA=got_args.shrink[0], shrinkB=got_args.shrink[1],
                    **expert_opts)
        art = ConnectionPatch(**conf)
        return conf, art


class AugEllipse(Base):
    name = "ellipse"

    def __init__(self, b: typing.Tuple[float, float], width: float, height: float, angle=float, **kwargs):
        super(AugEllipse, self).__init__()
        self.__conf = dict(xy=b, width=width, height=height, angle=angle, **kwargs)
        pass

    @staticmethod
    def from_argv(argv: typing.List[str]):
        cli = argparse.ArgumentParser(f"Checking {AugEllipse.name} configuration")

        cli.add_argument("-x", "--x-coord", dest="x", type=float, required=True, help="x of the center of the ellipse")
        cli.add_argument("-y", "--y-coord", dest="y", type=float, required=True, help="y of the center of the ellipse")
        cli.add_argument("--width", dest="width", type=float, required=True, help="width of the ellipse")
        cli.add_argument("--height", dest="height", type=float, required=True, help="height of the ellipse")
        cli.add_argument("--angle", dest="angle", type=float, required=False, default=.0, help="angle of the ellipse")
        cli.add_argument("--expert", dest="expert", type=str, nargs='+', required=False, default=[],
                         help="If you are an expert of Matplotlib, you may set additional configurations here.\n"
                              "E.g., --expert color=red facecolor=blue")
        if not argv:
            cli.print_help()
            return {}, None
        got_args = cli.parse_args(argv)
        expert_opts = parse_expert(got_args.expert)

        conf = dict(xy=(got_args.x, got_args.y), width=got_args.width, height=got_args.height, angle=got_args.angle,
                    **expert_opts)
        art = Ellipse(xy=(5.6, 0.0), width=8.0, height=.5, angle=16.0,
                      facecolor=[0.1, 0.2, 0.3, 0.4])
        return conf, art


def parse_expert(expert_opts: typing.List[str]):
    parsed = dict()
    if expert_opts is None:
        return parsed
    for item in expert_opts:  # type: str
        idx_eq = item.find('=')
        if idx_eq == -1:
            print(f"[ERROR] Sorry, your configuration of {item} seems invalid.\n"
                  f"A valid option should be like: color=red", file=sys.stderr)
            sys.exit(-1)
        opt = item[:idx_eq]
        val = item[idx_eq + 1:]
        try:
            val = json.loads(val)
        except JSONDecodeError:
            try:
                val = json.loads(f'"{val}"')
            except JSONDecodeError as e1:
                print(e1)
                print(f"[ERROR] The val ``{val}`` has to be in valid format of json.\n"
                      f"E.g.\tcolor=[\"red\", \"green\"]\n"
                      f"\trgb=[1, 2, 3]\n"
                      f"The outer parenthesis will be automatically wrapped.\n"
                      f"However, the inner parenthesis should be wrapped by users themselves.\n"
                      f"Note that [\"1\", \"2\", \"3\"] is different from [1, 2, 3]:\n"
                      f"the former is a list of string, while the latter is a list of integers",
                      file=sys.stderr)
                sys.exit(-2)
        parsed[opt] = val
    return parsed
    pass


def print_help(names: typing.Dict[str, type], argv: typing.List[str]):
    print("Users should specify the following commands:")
    for name, cls in names.items():
        print(f"\t{name}")
    print("You can specify each command ``SEVERAL TIMES``.")
    print("Saving the results in files by specifying the following command:\n"
          "\t--save /path/to/save/your/results.txt\n"
          "Otherwise, print the results to stdout.")
    for v in argv:
        if v in names:
            cls = names[v]
            func = getattr(cls, func_name, "")
            if callable(func):
                func([])
            else:
                print(f"This command is invalid because we fail to find callable ``{func_name}`` function in the code")


def check_help(argv: typing.List[str], names: typing.Dict[str, type]):
    h = {"-h", "--help", "--h", "-help"}
    for v in argv:
        if v in h:
            print_help(names, argv)
            sys.exit(0)


def get_save_path(argv: typing.List[str]):
    n_argv = argv
    fb_out = sys.stdout
    found = -1
    for idx, v in enumerate(argv):
        if v == save_name:
            filename = argv[idx + 1]
            if not filename.endswith(".pickle"):
                filename += ".pickle"
            fb_out = open(filename, 'wb')
            found = idx
            break
    if found != -1:
        n_argv = argv[:found]
        n_argv.extend(argv[found + 2:])
    return n_argv, fb_out


def get_argv(names: typing.Dict[str, type]) -> \
        typing.Tuple[typing.Dict[str, typing.List[typing.List[str]]], typing.TextIO]:
    argv = sys.argv
    argv, fb_out = get_save_path(argv)
    check_help(argv=argv, names=names)
    indices_dict = []  # {"text": -1, "connection": -1, "ellipse": -1}
    for i, v in enumerate(argv):
        if v in names:
            indices_dict.append((v, i))
    end = len(argv)
    argv_dict = {k: [] for k in names}  # {"text": [], "connection": [], "ellipse": []}
    for name, idx in sorted(indices_dict, key=lambda x: x[1], reverse=True):
        argv4cmd = argv[idx + 1: end]
        argv_dict[name].append(argv4cmd)
        end = idx
    return argv_dict, fb_out


def wrapper():
    names = get_sub_classes(Base)
    argv_dict, fb_save = get_argv(names)
    configurations = []
    arts = []
    for name, commands in argv_dict.items():
        func = getattr(names[name], func_name, "default")
        if not callable(func):
            sys.exit(f"Fail to find `{func_name}` function in {name}")
        for cmd in commands:
            conf, art = func(cmd)
            if art is None:
                print(f"Invalid command found for {name}:\n"
                      f"Details of the command: `{' '.join(cmd)}`")
                sys.exit(4)
                pass
            configurations.append(conf)
            arts.append(art)
        pass
    pickle.dump(arts, fb_save)
    print(f"[DEBUG]: {json.dumps(configurations)}", file=sys.stderr)
    pass


if __name__ == '__main__':
    wrapper()

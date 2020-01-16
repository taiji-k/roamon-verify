# encoding: UTF-8

# 引数の処理はここを参考にした：https://qiita.com/oohira/items/308bbd33a77200a35a3d

import argparse
import roamon_diff_checker
import roamon_diff_getter
import os
import logging
from pyfiglet import Figlet

# ログ関係の設定 (適当)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ファイルの保存先
dir_path_data = "/var/tmp"
file_path_vrps = os.path.join(dir_path_data, "vrps.csv")
file_path_rib = os.path.join(dir_path_data, "asnip.dat")

# ロゴの描画
f = Figlet(font='slant')
print(f.renderText('roamon'))


# getサブコマンドの実際の処理を記述するコールバック関数
def command_get(args):
    # RIBのデータ取得
    if args.all or args.bgp:
        roamon_diff_getter.fetch_rib_data(dir_path_data, file_path_rib)

    # VRPs (Verified ROA Payloads)の取得
    if args.all or args.roa:
        roamon_diff_getter.fetch_vrps_data(file_path_vrps)


# 検証サブコマンド　checkのとき呼ばれる関数
def command_check(args):
    data = roamon_diff_checker.load_all_data(file_path_vrps, file_path_rib)
    if args.asns is None:
        roamon_diff_checker.check_all_asn_in_vrps(data["vrps"], data["rib"])
    else:
        roamon_diff_checker.check_specified_asn(data["vrps"], data["rib"], args.asns)


def command_help(args):
    print(parser.parse_args([args.command, '--help']))
    # TODO: ヘルプをうまくやる


# コマンドラインパーサーを作成
parser = argparse.ArgumentParser(description='ROA - BGP Diff command !')
subparsers = parser.add_subparsers()

# get コマンドの parser を作成
parser_add = subparsers.add_parser('get', help='see `get -h`')
parser_add.add_argument('--all', action='store_true', help='specify retrieve type ALL (default)')
parser_add.add_argument('--roa', action='store_true', help='specify retrieve type only ROA')
parser_add.add_argument('--bgp', action='store_true', help='specify retrieve type only BGP')
# parser_add.add_argument('-p', '--path', default="/tmp", help='specify data dirctory')
parser_add.set_defaults(handler=command_get)

# check コマンドの parser を作成
parser_commit = subparsers.add_parser('check', help='see `check -h`')
parser_commit.add_argument('--asns', nargs='*', help='specify target ASNs (default: ALL)')
parser_commit.set_defaults(handler=command_check)

# help コマンドの parser を作成
parser_help = subparsers.add_parser('help', help='see `help -h`')
parser_help.add_argument('command', help='command name which help is shown')
parser_help.set_defaults(handler=command_help)

# コマンドライン引数をパースして対応するハンドラ関数を実行
args = parser.parse_args()
if hasattr(args, 'handler'):
    args.handler(args)
else:
    # 未知のサブコマンドの場合はヘルプを表示
    parser.print_help()

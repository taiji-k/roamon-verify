# encoding: UTF-8

# Copyright (c) 2019-2020 Japan Network Information Center ("JPNIC")
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute and/or sublicense of
# the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# 引数の処理はここを参考にした：https://qiita.com/oohira/items/308bbd33a77200a35a3d

import argparse
import roamon_verify_checker
import roamon_verify_getter
import os
import logging
from pyfiglet import Figlet
import configparser

# ログ関係の設定 (適当)
logger = logging.getLogger(__name__)

# コンフィグファイルのロード
config = configparser.ConfigParser()
config.read('config.ini')
config_roamon_verify = config["roamon-verify"]
# ファイルの保存先
dir_path_data = config_roamon_verify["dir_path_data"]
file_path_vrps = config_roamon_verify["file_path_vrps"]
file_path_rib = config_roamon_verify["file_path_rib"]

# ロゴの描画
f = Figlet(font='slant')
print(f.renderText('roamon'))


# getサブコマンドの実際の処理を記述するコールバック関数
def command_get(args):
    # RIBのデータ取得
    if args.all or args.bgp:
        roamon_verify_getter.fetch_rib_data(dir_path_data, file_path_rib)

    # VRPs (Verified ROA Payloads)の取得
    if args.all or args.roa:
        roamon_verify_getter.fetch_vrps_data(file_path_vrps)


# 検証サブコマンド　checkのとき呼ばれる関数
def command_check(args):
    data = roamon_verify_checker.load_all_data(file_path_vrps, file_path_rib)

    # オプション指定されてる場合はそれをやる
    if args.asn is not None:
        roamon_verify_checker.check_specified_asns(data["vrps"], data["rib"], args.asn)
    if args.ip is not None:
        roamon_verify_checker.check_specified_prefixes(data["vrps"], data["rib"], args.ip)

    # なんのオプションも指定されてないとき
    # (argparseはオプションのなかのハイフンをアンダーバーに置き換える。(all-asnsだとall引くasnsだと評価されるため))
    if args.all_asn == True or (args.ip is None and args.asn is None):
        roamon_verify_checker.check_all_asn_in_vrps(data["vrps"], data["rib"])


def command_check_violation(args):
    data = roamon_verify_checker.load_all_data(file_path_vrps, file_path_rib)

    # オプション指定されてる場合はそれをやる
    if args.asn is not None:
        roamon_verify_checker.check_violation_specified_asns(data["vrps"], data["rib"], args.asn)
    if args.ip is not None:
        roamon_verify_checker.check_violation_specified_ips(data["vrps"], data["rib"], args.ip)

    # なんのオプションも指定されてないとき
    # (argparseはオプションのなかのハイフンをアンダーバーに置き換える。(all-asnsだとall引くasnsだと評価されるため))
    if args.all_asn == True or (args.ip is None and args.asn is None):
        roamon_verify_checker.check_violation_all_asn_in_vrps(data["vrps"], data["rib"])


def command_help(args):
    print(parser.parse_args([args.command, '--help']))
    # TODO: ヘルプをうまくやる


# コマンドラインパーサーを作成
parser = argparse.ArgumentParser(description='ROA - BGP rov command !')
subparsers = parser.add_subparsers()

# get コマンドの parser を作成
parser_add = subparsers.add_parser('get', help="see `get -h`. It's command to fetch data.")
parser_add.add_argument('--all', action='store_true', help='specify retrieve type ALL (default)')
parser_add.add_argument('--roa', action='store_true', help='specify retrieve type only ROA')
parser_add.add_argument('--bgp', action='store_true', help='specify retrieve type only BGP')
# parser_add.add_argument('-p', '--path', default="/tmp", help='specify data dirctory')
parser_add.set_defaults(handler=command_get)

# rov コマンドの parser を作成
parser_commit = subparsers.add_parser('rov', help="see `get -h`. It's command to check route.")
parser_commit.add_argument('--all-asn', nargs='*', help='check ALL ASNs (default)')
parser_commit.add_argument('--asn', nargs='*', help='specify target ASNs (default: ALL)')
parser_commit.add_argument('--ip', nargs='*', help='specify target IPs such as 203.0.113.0/24 or 203.0.113.5.')
parser_commit.set_defaults(handler=command_check)

# only-invalidコマンドのパーサ
parser_commit = subparsers.add_parser('only-invalid', help="see `get -h`. It's command to validate route origin.")
parser_commit.add_argument('--all-asn', nargs='*', help='check ALL ASNs (default)')
parser_commit.add_argument('--asn', nargs='*', help='specify target ASNs (default: ALL)')
parser_commit.add_argument('--ip', nargs='*', help='specify target IPs such as 203.0.113.0/24 or 203.0.113.5.')
parser_commit.set_defaults(handler=command_check_violation)

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

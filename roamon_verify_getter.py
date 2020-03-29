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

import argparse
# import roamon_diff_checker
import subprocess
import os
import logging
from pyfiglet import Figlet
import requests
import bs4
import urllib.parse
from urllib.parse import urlparse

# ログ関係の設定 (適当)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _get_latest_rib_url_in_month(base_url, month):
    # 上で得たディレクトリの中のRIBSディレクトリへアクセスするURLを生成 (例: "2020.1/RIBS/")
    month_url = urllib.parse.urljoin(base_url, month)
    ribs_in_month_url = urllib.parse.urljoin(month_url, "RIBS/")

    # RIBSディレクトリの中にあるファイルを最終更新順に並べたページを取得
    payload = {"C": "M", "O": "D"}  # 最終更新(MOD)で降順(DESC)に並び替え
    ribs_list_res = requests.get(ribs_in_month_url, params=payload)
    soup_ribs_list = bs4.BeautifulSoup(ribs_list_res.text, "html.parser")
    
    # 最新のファイル名を取得
    latest_rib_a_tag = soup_ribs_list.select("tr")[3].a
    # (最新の月のディレクトリが空なことがある)
    if latest_rib_a_tag is None:
        return None
    else:
        latest_rib_file_name = latest_rib_a_tag.get("href")
        latest_rib_download_url = urllib.parse.urljoin(ribs_in_month_url, latest_rib_file_name)
        return latest_rib_download_url


# 最新のRIBファイルをダウンロードするためのURLを得る (pyasnに同じ機能はある)
def get_latest_rib_url():
    # 年月が名前となったディレクトリ一覧を、最終更新順に並べたページを取得
    payload = {"C": "M", "O": "D"}  # 最終更新(MOD)で降順(DESC)に並び替え
    base_url = 'http://archive.routeviews.org/bgpdata/'
    month_list_res = requests.get(base_url, params=payload)

    # 最終更新が一番あとのディレクトリの名前を取得("2020.1/"とか)
    soup_month_list = bs4.BeautifulSoup(month_list_res.text, "html.parser")
    latest_month_row = soup_month_list.select("tr")[3]
    latest_month = latest_month_row.a.get("href")

    # その月の中で最新のRIBファイルのURLを取得
    latest_rib_download_url = _get_latest_rib_url_in_month(base_url, latest_month)

    # 最新の月のディレクトリが空なことがある。そのときは1つ前のディレクトリの中を探す
    if latest_rib_download_url is None:
        second_latest_month_row =  soup_month_list.select("tr")[4]
        second_latest_month = second_latest_month_row.a.get("href")
        latest_rib_download_url = _get_latest_rib_url_in_month(base_url, second_latest_month)

    return latest_rib_download_url


def fetch_rib_data(dir_path_data, file_path_ipasndb):
    logger.debug("start fetch RIB data")

    # 最新のRIBファイルのダウンロードURLを得る
    download_url = get_latest_rib_url()
    logger.debug("downloadurl: {}".format(download_url))
    download_file_name = os.path.basename(urlparse(download_url).path)
    logger.debug("download file name: {}".format(download_file_name))
    # 最新のRIBファイルをダウンロードした場合のあるべきファイルパスを得る
    download_file_path = os.path.join(dir_path_data, download_file_name)

    # TODO: 同名のファイルがあっても、それはダウンロード途中でキャンセルされた残骸かもしれない。ハッシュ値を見るべき(だが面倒なのでやってない)
    # すでに同名のファイルがあるならダウンロードはスキップ
    if os.path.exists(download_file_path):
        logger.debug("latest RIB file are exists at {}! The download is canceled.".format(download_file_path))
    else:
        logger.debug("latest RIB file are NOT exists at {}! Downloading...".format(download_file_path))
        subprocess.check_output(
            "cd {} ; wget {}".format(dir_path_data, download_url),
            shell=True,
            universal_newlines=True
        )
        logger.debug("downloaded: {}".format(download_file_path))

    logger.debug("start parse RIB data")
    # pyasnの機能でRIBファイルをパースしてpyasnが読める形式に変換する
    subprocess.check_output("pyasn_util_convert.py --single {} {}".format(download_file_path, file_path_ipasndb),
                            shell=True)


# ↓めんどくさいからShellScriptワンライナーで対応することにしました
# # VRPsのCSVから、pyasnが読み込める形式に変換する
# def convert_vrps_csv_to_pyasn_dat(file_path_vrps_csv, file_path_vrps_pyasn_dat):
#     with open(file_path_vrps_csv, "r") as f_csv:
#         with open(file_path_vrps_pyasn_dat, "w") as f_dat:
#             # 最初のコメント
#             f_dat.writelines("; IP-ASN32-DAT file")
#             f_dat.writelines(";")


def fetch_vrps_data(file_path_vrps):
    # routinatorでROAを取得 & 検証してVRPのリストを得て、さらにpyasnが読み込める形式に直す(cutコマンド以降が整形部分)
    # TODO: pyasnがASN 0を許容しないので、`grep -v 'AS0'`を入れてAS0のとこを消してる。将来的にはpyasnを改造してASN 0を読み込めるようにすべき...らしい
    subprocess.check_output(
        "routinator vrps 2>/dev/null | tail -n +2  | grep -v 'AS0' |cut -d, -f1,2 | tr ',' ' ' | cut -c 3- | awk '{print $2 \"\\t\" $1}'    > " + file_path_vrps,
        shell=True)
    logger.debug("finish fetch vrps")


# VRPを入手するのに、docker上でroutinatorを動かす版。前使ってた
def fetch_vrps_data_with_docker(file_path_vrps):
    # 入手したTALを永続化する準備
    subprocess.check_output(
        "sudo docker volume create routinator-tals",
        shell=True)
    # TALを入手
    subprocess.check_output(
        "sudo docker run --rm -v routinator-tals:/home/routinator/.rpki-cache/tals \
nlnetlabs/routinator init -f --accept-arin-rpa",
        shell=True)
    # routinator起動
    subprocess.check_output(
        "sudo docker run -d --rm --name routinator -v routinator-tals:/home/routinator/.rpki-cache/tals nlnetlabs/routinator",
        shell=True)
    # routinatorでROAを取得 & 検証してVRPのリストを得て、さらにpyasnが読み込める形式に直す(cutコマンド以降が整形部分)
    # TODO: pyasnがASN 0を許容しないので、`grep -v 'AS0'`を入れてAS0のとこを消してる。将来的にはpyasnを改造してASN 0を読み込めるようにすべき...らしい
    subprocess.check_output(
        "sudo docker exec -it routinator /bin/sh -c 'routinator vrps 2>/dev/null | tail -n +2'  | grep -v 'AS0' |cut -d, -f1,2 | tr ',' ' ' | cut -c 3- | awk '{print $2 \"\\t\" $1}'    > " + file_path_vrps,
        shell=True)
    # routinatorのコンテナを止める(と同時に消える)
    subprocess.check_output(
        "sudo docker stop routinator",
        shell=True)
    logger.debug("finish fetch vrps")

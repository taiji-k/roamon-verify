# encoding: UTF-8

import argparse
import roamon_diff_checker
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


# 最新のRIBファイルをダウンロードするためのURLを得る (pyasnに同じ機能あったからいまは使わない)
def get_latest_rib_url():
    # 年月が名前となったディレクトリ一覧を、最終更新順に並べたページを取得
    payload = {"C": "M", "O": "D"} # 最終更新(MOD)で降順(DESC)に並び替え
    base_url = 'http://archive.routeviews.org/bgpdata/'
    month_list_res = requests.get(base_url, params=payload)

    #　最終更新が一番あとのディレクトリの名前を取得("2020.1/"とか)
    soup_month_list = bs4.BeautifulSoup(month_list_res.text, "html.parser")
    latest_month_row = soup_month_list.select("tr")[3]
    latest_month = latest_month_row.a.get("href")

    # 上で得たディレクトリの中のRIBSディレクトリへアクセスするURLを生成 ("2020.1/RIBS/")
    month_url = urllib.parse.urljoin(base_url, latest_month)
    ribs_in_month_url = urllib.parse.urljoin(month_url, "RIBS/")

    # RIBSディレクトリの中にあるファイルを最終更新順に並べたページを取得
    payload = {"C": "M", "O": "D"} # 最終更新(MOD)で降順(DESC)に並び替え
    ribs_list_res = requests.get(ribs_in_month_url, params=payload)
    soup_ribs_list = bs4.BeautifulSoup(ribs_list_res.text, "html.parser")
    # 最新のファイル名を取得
    latest_rib_file_name =soup_ribs_list.select("tr")[3].a.get("href")

    # 最新のファイルをダウンロードするURLを生成
    latest_rib_download_url = urllib.parse.urljoin(ribs_in_month_url, latest_rib_file_name)
    return latest_rib_download_url


def fetch_rib_data(dir_path_data, file_path_ipasndb):
    # pyasnの機能で最新のRIBファイルをRouteViewからとってくる
    download_output = subprocess.check_output(
        "cd {} ; pyasn_util_download.py --latest".format(dir_path_data),
        shell=True,
        universal_newlines=True
    )

    #　ダウンロードしたファイル名を,pyasnのダウンロードスクリプトの出力から調べる
    download_output_lines = download_output.split("\n")
    logger.debug("downloader output: {}".format(download_output_lines))
    download_url = download_output_lines[2].split()[1]
    logger.debug("downloadurl: {}".format(download_url))
    downloaded_file_name = os.path.basename(urlparse(download_url).path)
    logger.debug("download file name: {}".format(downloaded_file_name))

    downloaded_file_path = os.path.join(dir_path_data, downloaded_file_name)
    logger.debug("downloaded: {}".format(downloaded_file_path))

    # pyasnの機能でRIBファイルをパースしてpyasnが読める形式に変換する
    download_output = subprocess.check_output(
        "pyasn_util_convert.py --single {} {}".format(downloaded_file_path, file_path_ipasndb),
        shell=True)

def fetch_vrps_data(file_path_vrps):
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
    # routinatorでROAを取得 & 検証してVRPのリストを得る
    subprocess.check_output(
        "sudo docker exec -it routinator /bin/sh -c 'routinator vrps 2>/dev/null | tail -n +2' > " + file_path_vrps,
        shell=True)
    # routinatorのコンテナを止める(と同時に消える)
    subprocess.check_output(
        "sudo docker stop routinator",
        shell=True)
    logger.debug("finish fetch vrps")

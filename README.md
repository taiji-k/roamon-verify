# roamon diff
ROAと実際の経路情報の齟齬を調べるツールです

## Usage
### Instllation
#### ローカルにインストールする場合
一番確実だと思います

リポジトリのクローン
```
$ git clone https://github.com/taiji-k/roamon.git
```

必要なパッケージのインストール
```
$ pip3 install netaddr pyfiglet tqdm requests beautifulsoup4 pyasn
```

他にDocker環境が必要です

#### Vagrantを使う場合
本リポジトリはプライベートのため、cloneにはログインが必要です  
`./vagrant/Vagrantfile`の一番下の方にgithubアカウントのユーザ名とパスワードを入れるところがあるので書き換えてください

あとPCのスペックに合わせて、仮想マシンに割り振るリソースを適当に増やしてください(Vagrantfileの真ん中くらいにあります)  
低いスペックちゃんと動くかは確認してません...
  
あとは以下のコマンドを打てばok
```
$ cd vagrant
$ vagrant up
$ vagrant ssh
>$ 
```

#### Dockerを使う場合
Docker in Docker をやる必要があるため *後回し* にします

~~本リポジトリはプライベートのため、cloneにはログインが必要です
~~`./docker/Dockerfile`にgithubのユーザ名とパスワードを入れるところがあるので書き換えておいてください~~

~~あとは以下のコマンドで準備が整ったコンテナが起動します~~

```
$ sudo docker build -t roamon ./docker
$ sudo docker run --rm -it roamon /bin/bash
>$ cd /roamon
```



### Quick start

#### 全ての情報のフェッチ 
標準では`/tmp`にデータを置きます   
数分かかります
```
$ python3 roamon_diff_controller.py get --all
```
#### 全ての情報のチェック
VRPs(Verified ROA Payloads)の情報とRIB(実際の経路情報)を比較し、齟齬があるかどうかを調べます  
Trueが正常でFalseが齟齬ありです  
```
$ python3 roamon_diff_controller.py check

139553 True
136815 True
16018 False
202712 True
...
```

#### 特定のASだけチェック
例としてAS5745と63987について調べます  
```
$ python3 roamon_diff_controller.py check -asns 5745 63987

5745 True
63987 False
```

#### 特定のIPアドレスだけチェック
```
$ python3 roamon_diff_controller.py check -ips 8.8.8.8

8.8.8.8 False
```

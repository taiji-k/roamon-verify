# roamon verify
ROAと実際の経路情報の齟齬をROVにより調べるツールです

## Instllation
### ローカルにインストールする場合
一番確実だと思います

リポジトリのクローン
```
$ git clone https://github.com/taiji-k/roamon-verify.git
```

必要なパッケージのインストール
```
$ pip3 install netaddr pyfiglet tqdm pyasn beautifulsoup4 requests
```

他にDocker環境が必要です

### Vagrantを使う場合
本リポジトリはプライベートのため、cloneにはログインが必要です  
`./vagrant/Vagrantfile`の一番下の方にgithubアカウントのユーザ名とパスワードを入れるところがあるので書き換えてください

なんだか遅い場合は、あとPCのスペックに合わせて、仮想マシンに割り振るリソースを適当に増やしてください(Vagrantfileの真ん中くらいにあります)    
  
あとは以下のコマンドを打てばok
```
$ cd vagrant
$ vagrant up
$ vagrant ssh
>$ 
```

### Dockerを使う場合
Docker in Docker をやる必要があるため *後回し* にします

~~本リポジトリはプライベートのため、cloneにはログインが必要です
~~`./docker/Dockerfile`にgithubのユーザ名とパスワードを入れるところがあるので書き換えておいてください~~

~~あとは以下のコマンドで準備が整ったコンテナが起動します~~

```
$ sudo docker build -t roamon ./docker
$ sudo docker run --rm -it roamon /bin/bash
>$ cd /roamon
```

## Configuration
`config.ini`でファイルの置き場所を設定します。
* `dir_path_data`:ワーキングディレクトリ(ダウンロードなどをする場所)
* `file_path_vrps`: VRPのデータ(pyasnが読み込める形式)
* `file_path_rib`: BGPのデータ(pyasnが読み込める形式)

## Usage
使い方一覧。  

Note: 何らかの理由で`sudo`を付ける場合は、`sudo env "PATH=$PATH" <your_command>`のようにPATHを渡さないと途中で失敗します。sudoはデフォルトではセキュリティ上の理由でPATHを引き継いでくれません。

### 全ての情報のフェッチ 
最初にやらなくてはいけません   
数分かかります
```
$ python3 roamon_verify_controller.py get --all
```
### ROA登録がちゃんとできているか調べる
VRPs(Verified ROA Payloads)の情報とRIB(実際の経路情報)を比較し、齟齬があるかどうかをROV(Route Origin Validation)をして調べます。  
 
結果の見方は以下です。
* 検証成功が `VALID`
* 検証失敗(ROA登録されたものとは違うASがオリジンとして広告してた)は `INVALID`
* ROA登録がそもそもなかったのは `NOT_FOUND`
* そもそも経路広告がされてなかったものは `NOT_ADVERTISED`



#### 全てのASについて調べる
デフォルトでは, VRPsに登場した(=現在有効なROA登録していた)全てのASについて調べます。  
ASが広告していたprefix全てについてROVをしていきます。
```
$ python3 roamon_verify_controller.py check

2200    192.93.148.0/24 INVALID
2200    194.57.0.0/16   VALID
2200    192.54.175.0/24 INVALID
2200    156.28.0.0/16   INVALID
...
```

#### 特定のASだけチェック
指定されたASが広告していたprefixすべてについてROVしていきます。  
例としてAS5745と63987について調べます。  
```
$ python3 roamon_verify_controller.py check -asns 5745 63987

5745     192.93.148.0/24 VALID
63987    194.57.0.0/16   VALID
63987    192.54.175.0/24 INVALID
63987    156.28.0.0/16   INVALID
```

#### 特定のIPアドレスだけチェック
指定されたprefixに、経路広告されてる中でロンゲストマッチするprefixについてROVをします。

`194.57.0.0/16`を含むprefixはROA登録できていることがわかります。
```
$ python3 roamon_verify_controller.py check -ips  194.57.0.0/16 192.93.148.0/24

194.57.0.0/16   VALID
192.93.148.0/24 INVALID
```

`194.57.0.0/16`より1bit大きい`194.56.0.0/15`は(広告されてないから)ROVに失敗します
```
$ python3 roamon_verify_controller.py check -ips  194.57.0.0/20

194.56.0.0/15   NOT_ADVERTISED
```


`194.57.0.0/16`より細かい`194.57.0.0/20`でも同じくROVに成功することがわかります。(`194.57.0.0/16`にロンゲストマッチするから)  
(TODO: 指定されたprefixだけでなく, 経路広告されてる中でそれにロンゲストマッチしたprefix,この場合`194.57.0.0/16`も表示した方がいい？)
```
$ python3 roamon_verify_controller.py check -ips  194.57.0.0/20

194.57.0.0/20   VALID
```

### 経路ハイジャック?を調べる
**ここから下はあまり考えなくていいです。現時点ではそんなに必要ないし何を何のためにやってるか怪しくなったので。**

---

指定されたASがROA登録したprefixが他のROA登録していないASに勝手に(同じかより小さいプレフィックスで)経路広告されていないかを調べます。  
  
Falseになっている場合、そのprefixをROA登録していない他のASが経路広告してしまっています。  
ROAでOrigin ASの検証をしている組織でははじかれてしまうので対応が必要となります。

#### 全てのASについてチェック
デフォルトでは全てのASについてチェックします。  


`調査したAS | 経路広告されてる中で、調査したASがROA登録してるprefixとロンゲストマッチしたprefix | 経路広告したAS ` 
```
$ python3 roamon_verify_controller.py check-violation 

174 198.63.0.0/16 2914 False
174 185.189.173.0/24 199727 True
174 209.227.0.0/17 2914 False
174 204.142.180.0/23 174 False
174 167.160.15.0/24 174 False
...
```

#### ASの指定
AS番号を複数していできます。

```
$ python3 roamon_verify_controller.py check-violation  --asns 174

174 198.63.0.0/16 2914 False
174 185.189.173.0/24 199727 True
174 209.227.0.0/17 2914 False
174 204.142.180.0/23 174 False
174 167.160.15.0/24 174 False
...
```

#### IPアドレスの指定
指定されたIPアドレスを経路広告していたASと、そのIPアドレスをROA登録していたASが同一かどうかを調べます
(`python3 roamon_verify_controller.py check --ips`と似たようなもんだから必要ない？この辺よくわからなくなってきたので整理が必要...)
```
$ python3 roamon_verify_controller.py check-violation --ips 203.0.113.0/24 203.0.113.5

203.0.113.0/24 False
203.0.113.5 False
```


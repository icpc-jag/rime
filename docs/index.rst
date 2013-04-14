####
Rime
####

Rime とは
=========

Rime はプログラミングコンテストの問題セットの作成を補助するツールです。

ACM-ICPC 形式や TopCoder 形式のプログラミングコンテストを開く際、問題を出すために準備しなければならないものは何があるでしょうか。問題案は既にあるものとすると、必要なものは主に次の4つに大別されます。

1. **問題文**. 最初から凝った文章を作る必要はもちろんありませんが、少なくとも問題の骨子と入出力形式はあらかじめ決めておかなければなりません。
2. **模範解答プログラム**. 問題が解けることを証明するため、入出力データを作るため、その他あらゆる理由のために模範解答プログラムが必要です。ここで最も重要なことは、模範解答は複数用意されるべきだということです。複数の解答を複数の人間が用意して、その出力を照合することによって、解答プログラムの誤りを大幅に減らすことができます。また必須ではありませんが、想定解法と比べて計算量が大きすぎる解法や、一見正しそうに見えてエッジケースで間違う解法などの、想定「誤答」のプログラムを作成しておけば、それらを振り落とす入力データを作ることが容易になります。
3. **入出力データ**. 小さな入力データは手で直接作ることができますが、大きなエッジケースやランダムケースに対応する入力データはプログラムで作ることになります。出力データは入力データを模範解答プログラムに入れて作成します。
4. **入出力検証器**. 入力データのフォーマットが合っているかどうかは、模範解答プログラムとは別のプログラムであらためて検証することが望ましいでしょう。また、出力形式が浮動小数点数を含む場合など、単純な diff プログラムで間に合わない場合には、出力検証器を用意する必要もあります。

Rime は、この 4 つの項目のうち、問題文を除いた残りのすべての準備作業を補助します。たとえば、次のようなことができます。

- 手動で作成した入力データや入力ジェネレータを適切な場所に置いておけば、コマンド1つで入力ジェネレータを実行しデータセットを作成することができます。
- 生成された入力データセットを自動的に入力検証器に通し、フォーマット違反がないかどうかをチェックします。
- 複数の模範解答プログラムを自動的にコンパイルし、それらの出力が一致するかどうかをチェックします。
- "想定誤答プログラム"を置いておくと、そのプログラムがジャッジを通過しないことをチェックし、万が一通ってしまった場合は警告を出します。
- 各問題について、模範解答プログラムを走らせた結果を分かりやすく表示します。


ダウンロード
============

Github のプロジェクトページ https://github.com/nya3jp/rime から ZIP をダウンロードするか、git を使って次のように clone してください::

    $ git clone https://github.com/nya3jp/rime.git

リポジトリのトップディレクトリにある rime.py および rime ディレクトリが Rime の本体です。
自分のプロジェクトで Rime を使用するときは、この 2 つを問題データを管理しているリポジトリなどにコピーして下さい。



クイックスタート
================

ここでは、あらかじめ用意された設定例を使って Rime を実行し、Rime の機能の概略を紹介します。

以下では、前節で ~/src/rime に Rime をダウンロードしたと仮定します。
::

    $ cd ~/src/rime

このディレクトリには次のようなファイルが存在するはずです(最新版ではもう少しファイルが多い可能性もあります)。
::

    $ ls -l
    total 12
    -rw-r--r-- 1 nya nya    0 May 11 23:55 README
    drwxr-xr-x 3 nya nya 4096 May 11 23:55 example
    drwxr-xr-x 6 nya nya 4096 May 11 23:55 rime
    -rwxr-xr-x 1 nya nya 1215 May 11 23:55 rime.py

example ディレクトリには設定例が用意されていますので、そこに移動しましょう。
::

    $ cd example
    $ ls -l
    total 8
    -rw-r--r-- 1 nya nya   96 May 11 23:55 PROJECT
    drwxr-xr-x 6 nya nya 4096 May 11 23:55 a+b
    lrwxrwxrwx 1 nya nya    7 May 12 00:10 rime -> ../rime
    lrwxrwxrwx 1 nya nya   10 May 11 23:55 rime.py -> ../rime.py

このディレクトリ以下には、コンテストの問題・解答・入出力ジェネレータなど全てに関する設定が保存されています。このようなディレクトリを **プロジェクトディレクトリ** と呼びます。

プロジェクトディレクトリには Rime 本体とプロジェクト設定ファイル(PROJECT)、そして問題ディレクトリを置きます。問題ディレクトリは通常複数あるでしょうが、この例では一問だけ (a+b) 用意されています。プロジェクトディレクトリ以下には Rime が認識するもの以外のディレクトリやファイルがあっても問題ありません。なお、このプロジェクト例では簡単のため Rime 本体をシンボリックリンクとして置いてありますが、通常のプロジェクトではファイルをまるごとコピーして置くと良いでしょう。

早速 Rime を実行してみましょう。
::

    $ ./rime.py test 
    [ GENERATE ] a+b/tests: generator.py
    [ VALIDATE ] a+b/tests: OK
    [ COMPILE  ] a+b/cpp-correct
    [  REFRUN  ] a+b/cpp-correct
    [ COMPILE  ] a+b/cpp-TLE
    [   TEST   ] a+b/cpp-TLE: 11-maximum.in: Time Limit Exceeded
    [ COMPILE  ] a+b/cpp-WA-multiply
    [   TEST   ] a+b/cpp-WA-multiply: Expectedly failed all challenge cases
    [   TEST   ] a+b/cpp-correct: max 0.00s, acc 0.09s
    [   TEST   ] a+b/python-correct: max 0.04s, acc 0.72s
    
    Test Summary:
    a+b ... 4 solutions, 24 tests
      cpp-correct      OK  max 0.00s, acc 0.09s
      python-correct   OK  max 0.04s, acc 0.72s
      cpp-TLE          OK  11-maximum.in: Time Limit Exceeded
      cpp-WA-multiply  OK  Expectedly failed all challenge cases
    
    Error Summary:
    Total 0 errors, 0 warnings

このコマンドは数秒で終了するはずです。この間に Rime は次の処理を行いました。

- 問題ディレクトリ a+b 以下にある 4 つの解答 (cpp-correct, python-correct, cpp-TLE, cpp-WA-multiply) のコンパイル
- 入出力ディレクトリ a+b/tests 以下にある入力生成器と入力検証器のコンパイル
- 入力生成器を使ったランダム入力データの生成
- 入力検証器を使った全入力データのフォーマットチェック
- 解答プログラム a+b/cpp-correct に入力データを入れて走らせ、リファレンスとなる出力データを生成
- 解答プログラム a+b/python-correct を走らせ、リファレンス出力データと同じ出力を出すことを確認
- 誤答プログラム a+b/cpp-WA-multiply を走らせ、間違った出力を出すことを確認
- 誤答プログラム a+b/cpp-TLE を走らせ、指定したタイムリミット (1秒) 内に終了しないことを確認

Rime が正しく動いていることを確認するため、試しに解答プログラムにバグを入れてみましょう。名前からお察しのとおり、問題 a+b は標準入力から二つの数を受け取り、その和を標準出力に書き出すプログラムを書け、という問題です。python-correct プログラムは次のようなコードになっています::

    $ cat a+b/python-correct/main.py
    #!/usr/bin/python
    
    import sys
    
    def main():
      a, b = map(int, sys.stdin.read().strip().split())
      print a + b
    
    if __name__ == '__main__':
      main()

これを、掛け算をするプログラムに書き換えます。
::

    $ vi a+b/python-correct/main.py
    ...
    $ cat a+b/python-correct/main.py
    #!/usr/bin/python
    
    import sys
    
    def main():
      a, b = map(int, sys.stdin.read().strip().split())
      print a * b  # i can haz moar?
    
    if __name__ == '__main__':
      main()

再び Rime を実行してみましょう。
::

    $ ./rime.py test
    [   TEST   ] a+b/cpp-TLE: 11-maximum.in: Time Limit Exceeded
    [   TEST   ] a+b/cpp-WA-multiply: Expectedly failed all challenge cases
    [   TEST   ] a+b/cpp-correct: max 0.01s, acc 0.09s
    ERROR: a+b/python-correct: 00-sample1.in: Wrong Answer
      judge log: /home/nya/src/rime/example/a+b/rime-out/python-correct/00-sample1.judge
    [   TEST   ] a+b/python-correct: 00-sample1.in: Wrong Answer
    
    Test Summary:
    a+b ... 4 solutions, 24 tests
      cpp-correct      OK  max 0.01s, acc 0.09s
      python-correct  FAIL 00-sample1.in: Wrong Answer
      cpp-TLE          OK  11-maximum.in: Time Limit Exceeded
      cpp-WA-multiply  OK  Expectedly failed all challenge cases
    
    Error Summary:
    ERROR: a+b/python-correct: 00-sample1.in: Wrong Answer
      judge log: /home/nya/src/rime/example/a+b/rime-out/python-correct/00-sample1.judge
    Total 1 errors, 0 warnings

python-correct が 00-sample1.in で間違っていた、とのメッセージが出ています。具体的にどのような出力をしたのかはジャッジログファイルに残っています。
::

    $ cat /home/nya/src/rime/example/a+b/rime-out/python-correct/00-sample1.judge
    --- /home/nya/src/rime/example/a+b/rime-out/tests/00-sample1.diff       2012-05-12 00:54:54.463139744 +0900
    +++ /home/nya/src/rime/example/a+b/rime-out/python-correct/00-sample1.out       2012-05-12 01:08:55.827436428 +0900
    @@ -1 +1 @@
    -7
    +12


プロジェクトディレクトリの構成
==============================

Rime のプロジェクトディレクトリツリーは以下のような構成になります。

- プロジェクトディレクトリ
    - 問題ディレクトリ
        - 解答ディレクトリ
        - 解答ディレクトリ
        - ...
        - テストデータディレクトリ
    - 問題ディレクトリ
        - 解答ディレクトリ
        - 解答ディレクトリ
        - ...
        - テストデータディレクトリ
    - ...

問題ディレクトリと解答ディレクトリは必要なだけ用意します。
テストデータディレクトリは各問題あたり高々 1 つのみ作成できます。

具体的なプロジェクトディレクトリの構成例を以下に示します。
::

    project/
      rime.py             ... Rime 実行ファイル
      rime/               ... Rime ライブラリコード
        ...
      PROJECT             ... プロジェクト設定ファイル
      problem-a/          ... 問題ディレクトリ
        PROBLEM           ... 問題設定ファイル
        solution-a1/      ... 解答ディレクトリ
          SOLUTION        ... 解答設定ファイル
          main.cc         ... ソースコード
        solution-a2/      ... 解答ディレクトリ
          ...
        solution-a3/      ... 解答ディレクトリ
          ...
        tests/            ... テストデータディレクトリ
          TESTSET         ... テスト設定ファイル
          00_sample1.in   ... 入力ファイル
          00_sample2.in   ... 入力ファイル
          00_sample3.in   ... 入力ファイル
          generator.cc    ... 入力生成器
          validator.py    ... 入力検証器
          judge.cc        ... 出力検証器
      problem-b/         ... 問題ディレクトリ
        ...
      problem-c/         ... 問題ディレクトリ
        ...

問題ディレクトリ/解答ディレクトリには任意の名前が利用できます。テストディレクトリの名前も任意ですが、一般的には "tests" が用いられます。

テストデータディレクトリにある拡張子 .in のファイルは全て自動的に入力ファイルとして扱われます。また、ここには入力生成器・入力検証器・出力検証器を置くことができます。その場合、ファイル名を TESTSET ファイルに記述します。詳しくは :ref:`configs-TESTSET` を参照してください。


設定ファイル
============

すべての設定ファイルは Python スクリプトとして記述され、Rime の起動時に eval されます。各設定ファイルの種類に応じていくつかの関数が Rime よりエクスポートされており、それらを呼ぶことにより設定を行います。

記述にあたっては Python の文法や標準ライブラリのすべてが利用可能ですが、可読性のためにシンプルな内容に留めておくことをおすすめします。一般的な用途では、設定関数の呼び出しを列挙するだけで十分です。

PROJECT
-------

プロジェクトディレクトリのトップレベルに置かれ、プロジェクト全体に共通の設定を記述します。

.. function:: use_plugin(name)

   このプロジェクトで用いるプラグインをロードします。詳しくは :ref:`plugins` を参照して下さい。

   例::

       use_plugin('merged_test')


PROBLEM
-------

問題ディレクトリの直下に置かれ、問題に関する設定を記述します。デフォルトでは :func:`problem` 関数のみが定義されており、 :func:`problem` 関数をちょうど一回呼び出さなければなりません。


.. function:: problem(time_limit, reference_solution=None, title=None, id=None)

   必要な引数はただひとつ *time_limit* のみです。この引数には、この問題に対する解答のテストをする際に、一つのテストケースに対して許される実行時間の上限を秒単位で指定します。

   *reference_solution* には、解答のテストを行う際に基準となる解答のディレクトリ名を指定します。基準解答はその出力が正しいと仮定され、ある問題に対する複数の解答がすべて一致していることを確認するときに、他の解答と出力を照合するために用いられます。指定がない場合は任意の解答がひとつ選ばれます。

   *title* には問題のタイトルを任意の文字列で指定します。

   *id* には問題のソートに使われる任意の文字列を指定します(一般的には 'A', 'B', ... が用いられます)。指定がない場合は問題ディレクトリ名でソートされます。

   例::

       problem(time_limit=3.0)
       problem(time_limit=3.0, reference_solution='solution1', id='C')


.. _configs-TESTSET:

TESTSET
-------

テストデータディレクトリに置かれ、問題の解答を検証するためのテスト入出力に関する設定を行います。

このファイルでは (1) 入力生成器, (2) 入力検証器, (3) 出力検証器 の 3 つが指定でき、それぞれ :func:`LANG_generator()`, :func:`LANG_validator()`, :func:`LANG_judge()` 関数を呼び出して登録します。各プログラムの仕様については :ref:`testspec` を参照してください。

.. function:: c_generator(src_name, flags=['-lm'])

   C で書かれた入力生成器を登録します。

   *src_name* にはソースコードの名前を拡張子付きで指定します。

   *flags* にはコンパイラに渡すフラグを文字列のリストで指定します。

   例::

       c_generator('generator.c')
       c_generator('generator.c', flags=['-lgmp'])

.. function:: cc_generator(src_name, flags=[])
              cxx_generator(src_name, flags=[])

   C++ で書かれた入力生成器を登録します。

   *src_name* にはソースコードの名前を拡張子付きで指定します。

   *flags* にはコンパイラに渡すフラグを文字列のリストで指定します。

   例::

       cc_generator('generator.cc')
       cxx_generator('generator.cpp', flags=['-lgmpxx'])

.. function:: java_generator(src_name, compile_flags=[], run_flags=[], encoding='UTF-8', mainclass='Main')

   Java で書かれた入力生成器を登録します。

   *src_name* にはソースコードの名前を拡張子付きで指定します。

   *compile_flags*, *run_flags* にはコンパイル時および実行時に渡すフラグを文字列のリストで指定します。

   *encoding* にはソースコードのエンコーディングを指定します。省略すると UTF-8 と見なされます。

   *mainclass* には実行する際のエントリポイントとなるクラス名を指定します。省略すると Main が使われます。

   例::

       java_generator('Generator.java')
       java_generator('Generator.java', compile_flags=['-source', '1.4'], run_flags=['-agentlib:hprof'], encoding='cp932', mainclass='Start')

.. function:: script_generator(src_name, run_flags=[])

   スクリプト言語で書かれた入力生成器を登録します。スクリプトの冒頭は、使用するプログラミング言語を明示するために ``#!`` (shebang) で始まらなければなりません。Rime は shebang を解釈するためにスクリプトを perl インタプリタに渡すので、shebang が存在しない場合は perl スクリプトとして実行されます。

   *src_name* にはソースコードの名前を拡張子付きで指定します。

   *run_flags* には実行時にスクリプトに渡すパラメータを文字列のリストで指定します。

   例::

       script_generator('generator.rb')
       script_generator('generator.py', run_flags=['-R'])

.. function:: LANG_validator(src_name, **code_kwargs)

   入力検証器を登録します。言語と各種パラメータの指定方法は入力生成器と同じです。

   例::

       script_validator('validate.py')
       cc_validator('validator.cc', flags=['-lgmpxx'])

.. function:: LANG_judge(src_name, **code_kwargs)

   出力検証器を登録します。言語と各種パラメータの指定方法は入力生成器と同じです。

   例::

       script_judge('judge.py')
       cc_judge('judge.cc', flags=['-lgmpxx'])


SOLUTION
--------

解答ディレクトリに置かれ、解答プログラムに関する設定を行います。この中では :func:`LANG_solution` 関数をちょうど一回呼び出さなければなりません。

.. function:: LANG_solution(src_name, challenge_cases=None, **code_kwargs)

   解答プログラムを登録します。言語と各種パラメータの指定方法は入力生成器と同じですが、追加で指定できるパラメータが存在します。

   *challenge_cases* にはテスト入力ファイルの名前を列挙したリストを指定することができます。指定があった場合、この解答は誤答であるとマークされます。通常の解答はテストがすべて成功することをチェックされるのに対し、誤答はテストが失敗することがテストされます。また、誤答が基準解答として選ばれることはありません。 *challenge_cases* が空のリストである場合は全テスト中最低でも一つのテストに失敗することがチェックされ、空でないリストを指定した場合、指定されたテストのすべてに失敗することがチェックされます。

   例::

       script_solution('adhoc.py', run_flags=['-R'])
       cc_solution('wrong_any.cc', challenge_cases=[])
       cc_solution('wrong_some.cc', challenge_cases=['input1.in', 'input3.in'])


.. _testspec:

テスト入出力の仕様
==================

テストの入出力ファイルはそれぞれ拡張子 .in, .diff を持ちます。

テストは次のように行われます。

1. すべての解答ディレクトリ、およびテストデータディレクトリ全体を rime-out ディレクトリ以下にコピーする。
2. 解答、入力生成器、入力検証器、出力検証器のコンパイルを行う。
3. すべての入力生成器を rime-out ディレクトリ内で実行する。これにより rime-out ディレクトリにすべてのテストケースに対応する .in ファイルが作成される。
4. 全ての入力データに対して入力検証器を実行する。ひとつでも検証エラーが発生した場合はストップする。
5. 基準解答を選択する。テストケースのうち .diff ファイルが存在しないものに対して基準解答を実行し、その出力を .diff ファイルとして保存する。
6. 基準解答以外の各解答を、各テストケースを入力として実行する。その出力は基準解答の出力と出力検証器を用いて比較される。出力検証器が指定されていない場合、単純にバイナリとして一致することの照合が diff コマンドによって行われる。

以下で入力生成器、入力検証器、出力検証器の仕様を説明します。

入力生成器
----------

入力ファイルを追加する方法には、固定入力ファイルを追加する方法と入力生成器を追加する方法があります。固定入力ファイルは主に小さなテストケースや手動で作成したテストケースに用い、テストデータディレクトリに .in の拡張子で配置します。大きなテストケースやランダム生成したテストケースを入力したい場合は入力生成器を用います。

入力生成器は実行されるとカレントディレクトリに入力ファイルを拡張子 .in で書き出すよう記述します。実行は rime-out ディレクトリ以下で行われます。

入力検証器
----------

入力検証器は、標準入力から入力データを受け取り、入力フォーマットが正しければ 0、そうでなければ 0 以外をリターンコードとして返します。

入力検証器はデバッグのための情報を標準出力に書き出すことができます。検証エラーの際にはその内容がコンソールに出力されます。

出力検証器
----------

出力検証器は、入力データ、基準解答の出力データ、そして解答の出力データを受け取り、解答が基準解答と一致することを検証します。一致すれば 0、そうでなければ 0 以外をリターンコードとして返します。

実行時には各データの所在を示すため、次のようなコマンドライン引数が指定されます:

- --infile <入力データファイル名>
- --difffile <基準解答出力データファイル名>
- --outfile <解答出力データファイル名>

出力検証器はデバッグのための情報を標準出力に書き出すことができます。検証エラーの際にはその内容がコンソールに出力されます。


コマンド
========

Rime の実行は次のように行います。
::

    ./rime.py COMMAND [OPTIONS] [ARGS]

コマンドを指定せずに実行するとヘルプメッセージが表示されます。また、 ``rime.py help COMMAND`` を実行するとコマンドに関するヘルプを見ることができます。

すべてのコマンドに共通のオプションは以下のようなものがあります。

.. cmdoption:: -j <n>, --jobs <n>

   タスク(例: 解答の実行, 出力検証器の実行など)の並列実行を有効にします。一般に、マルチコア環境ではこのオプションを指定することによりパフォーマンスが向上します。

   このオプションを指定した場合、デフォルトでは解答の実行時間の計測時間が行われなくなります。実行時間を計測したい場合は :option:`-p` オプションを使用して下さい。

.. cmdoption:: -p, --precise

   :option:`-j` オプションによりタスクの並列実行が有効になっている時、実行時間の計測を伴うタスクと他のタスクを並列に実行しないようにすることにより、実行時間の計測を有効にします。これにより並列実行のパフォーマンスが犠牲になります。

.. cmdoption:: -k, --keep_going

   ビルドやテストに失敗した際にも、影響のないタスクの実行を続行します。このオプションが指定されない場合、ひとつでもタスクが失敗するとすべてのタスクの実行が停止されます。

.. cmdoption:: -C, --cache_tests

   テスト結果をキャッシュすることにより、以前に実行したテストの実行を抑制します。


標準で使用出来るコマンドは以下の通りです。


.. describe:: rime.py help [COMMAND]

   ヘルプメッセージを表示します。コマンドを指定すると、そのコマンドに関するヘルプを見ることができます。

.. describe:: rime.py build [TARGET]

   ターゲットをビルドします。ターゲットはディレクトリ名で指定します。たとえばプロジェクトディレクトリを指定するとプロジェクト内の全てのファイルをビルドし、解答ディレクトリを指定すると解答のみをビルドします。ターゲット指定を省略するとカレントディレクトリとみなされます。

.. describe:: rime.py test [TARGET]

   ターゲットをテストします。ターゲットの指定は rime.py build と同様です。テストが何を行うかについては [テスト入出力の仕様](#testspec) を参照して下さい。

.. describe:: rime.py clean [TARGET]

   ターゲットの中間ファイルを削除します。ターゲットの指定は rime.py build と同様です。中間ファイルはすべて rime-out ディレクトリに保存されています。


.. _plugins:

プラグイン
==========

.. warning:: TODO(nya): 書く


--------
Copyright (c) 2011-2013 Rime Project.

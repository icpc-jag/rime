Rime
========

Rime is a tool for programming contest organizers to automate usual, boring and error-prone process of problem set preparation.
It supports various programming contest styles like ACM-ICPC, TopCoder, etc. by plugins.

Detailed documentations are found at documentation site:

http://nya3jp.github.io/rime/


Rime-plus
---------

* Install rime-plus
```$ pip install git+https://github.com/hiroshi-cl/rime```
* Update rime-plus
```$ pip install -U git+https://github.com/hiroshi-cl/rime```
* Uninstall rime-plus
```$ pip uninstall rime-plus```

* Initialize a project
```$ rime_init --git/--mercurial```
* Add a problem
```$ rime add . problem <problem_dir_name>```
* Add a solution
```$ rime add <parent_problem_dir_name> solution <solution_dir_name>```
* Add a testset
```$ rime add <parent_problem_dir_name> testset <testset_dir_name>```
* Build a target (project/problem/solution/testset)
```$ rime build <target_path>```
* Test a target (project/problem/solution/testset)
```$ rime test <target_path>```
* Pack a target for an online judge (project/problem/testset)
```$ rime pack <target_path>```
* Upload a target to an online judge (project/problem/testset)
```$ rime upload <target_path>```
* Submit a target to an online judge (project/problem/solution)
```$ rime upload <target_path>```
* Edit a configuration file (project/problem/solution/testset)
```vi/emacs/nano <target_path>/<PROJECT/PROBLEM/SOLUTION/TESTSET>```

### New Features ###

* -O2, -std=c++11 as a default
* Faster parallel test
* native testlib.h support
* subtask / partial scoring
* reactive checker (partially support)
* gcj-styled merged test
* additional commands
* pip support
* judge system deployment
* test result cache
* some bug fix
* JS / CSharp / Haskell codes
* etc.

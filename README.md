Rime
====

Rime is a tool for programming contest organizers to automate usual, boring and error-prone process of problem set preparation.
It supports various programming contest styles like ACM-ICPC, TopCoder, etc. by plugins.

Detailed documentations (in Japanese) are found at documentation site:

https://rime.readthedocs.io/ja/latest/


Cheat sheet
-----------

#### Install Rime

```
$ pip install git+https://github.com/icpc-jag/rime
```

#### Upgrade Rime

```
$ pip install -U git+https://github.com/icpc-jag/rime
```

#### Uninstall Rime

```
$ pip uninstall rime
```

#### Initialize a project

```
$ rime_init --git/--mercurial
```

#### Add a problem

```
$ rime add . problem <problem_dir_name>
```

#### Add a solution

```
$ rime add <parent_problem_dir_name> solution <solution_dir_name>
```

#### Add a testset

```
$ rime add <parent_problem_dir_name> testset <testset_dir_name>
```

#### Build a target (project/problem/solution/testset)

```
$ rime build <target_path> -j <#workers>
```

#### Test a target (project/problem/solution/testset)

```
$ rime test <target_path> -C -j <#workers>
```

#### Pack a target for an online judge (project/problem/testset)

```
$ rime pack <target_path>
```

#### Upload a target to an online judge (project/problem/testset)

```
$ rime upload <target_path>
```

#### Submit a target to an online judge (project/problem/solution)

```
$ rime submit <target_path>
```

#### Edit a configuration file (project/problem/solution/testset)

```
$ vi/emacs/nano <target_path>/<PROJECT/PROBLEM/SOLUTION/TESTSET>
```


New features from Rime Plus
---------------------------

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


For developers
--------------

#### How to run unit tests

```
$ python setup.py test
```

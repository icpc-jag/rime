#!/usr/bin/python


def PrintTestSummary(results, ui):
    if len(results) == 0:
        return
    ui.console.Print()
    ui.console.Print(ui.console.BOLD, 'Test Summary:', ui.console.NORMAL)
    solution_name_width = max(
        map(lambda t: len(t.solution.name), results))
    last_problem = None
    for result in sorted(results, key=KeyTestResultForListing):
        if last_problem is not result.problem:
            problem_row = [
                ui.console.BOLD,
                ui.console.CYAN,
                result.problem.name,
                ui.console.NORMAL,
                ' ... %d solutions, %d tests' %
                (len(result.problem.solutions),
                 len(result.problem.testset.ListTestCases()))]
            ui.console.Print(*problem_row)
            last_problem = result.problem
        status_row = ['  ']
        status_row += [
            result.solution.IsCorrect() and ui.console.GREEN or
            ui.console.YELLOW,
            result.solution.name.ljust(solution_name_width),
            ui.console.NORMAL,
            ' ']
        if result.expected:
            status_row += [ui.console.GREEN, ' OK ', ui.console.NORMAL]
        else:
            status_row += [ui.console.RED, 'FAIL', ui.console.NORMAL]
        status_row += [' ', result.detail]
        if result.IsCached():
            status_row += [' ', '(cached)']
        ui.console.Print(*status_row)
    if not (ui.options.precise or ui.options.parallelism <= 1):
        ui.console.Print()
        ui.console.Print('Note: Timings are not displayed when '
                         'parallel testing is enabled.')
        ui.console.Print('      To show them, try -p (--precise).')


def KeyTestResultForListing(a):
    """Key function of TestResult for display-ordering."""
    return (a.problem.name,
            a.solution is not a.problem.reference_solution,
            not a.solution.IsCorrect(),
            a.solution.name)

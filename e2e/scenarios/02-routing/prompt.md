Run the /claudity:status command for this project. This is a non-interactive test run: do not ask the user any questions and do not start any process.

A test harness parses your reply mechanically. After your plain-language summary, your very last line must be exactly:

RECOMMENDED: <process-name>

where <process-name> is the process the status output recommends running next. The harness fails if this line is missing or anything follows it.

import sys
import time

while True:
    sys.stderr.write(time.ctime() + " ERROR_SINGLE_LINE: ")
    sys.stderr.write("This is a single line\n")
    sys.stderr.write(time.ctime() + " ERROR_MULTI_LINE: ")
    with open("myblog.txt", "r") as f:
        multiline_log = f.read()
    sys.stderr.write(multiline_log)
    # sys.stderr.write(time.ctime() + " ERROR_PARTIAL_LINE: ")
    # with open("stacktrace.txt", "r") as f:
    #     stacktrace_log = f.read()
    # sys.stderr.write(stacktrace_log)
    time.sleep(600)

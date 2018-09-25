
# Werkzeug hot reload issue

```
PID   USER     TIME  COMMAND
    1 root      0:00 python app.py
    9 root      0:00 /usr/local/bin/python app.py
   15 root      0:00 sh
   20 root      0:00 ps -A
```

Cannot use hot reload because Werkzeug can't kill process 1, so it'll spawn a second process for the app and give *that* child process the listening socket (presumably - idk how it actually works). This ends up duplicating Ice connections so that each process responds to Murmur commands.

In production - this won't be a problem. In development - we'll end up doubling each command handler.


# zeroc-ice versus urllib SSL segfaults

blah blah blah.

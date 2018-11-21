# redisinfo
Python script producing a 'top-like' output for Redis info commandstats

Redis documentation on the INFO command which is providing the data
used by this script is here: https://redis.io/commands/info

Prerequisites:
- [redis](https://github.com/andymccurdy/redis-py "pip install redis")
- [tabulate](https://pypi.org/project/tabulate/ "pip install tabulate")

Script requires at least 1 argument on the command line which is
host:port of the Redis you wish to connect to. Optionally, you can
provide a second argument which is the password to use to AUTH to
Redis.

example execution:
   ```python redisinfo.py localhost:6379```

or with auth:
   ```python redisinfo.py my-redis-endpoint.com:15151 mypassword```

Once started, the script runs forever until killed by
pressing 'q', 'esc' or ctrl-C if you are feeling violent.
The display 'refreshes' on an interval that can be changed by
pressing +/-. You can sort the output of the commandstats by
any of the columns by pressing the number of the column you
wish to sort by:
- 1 = total = the total number of times the command has been
    called since Redis was started
- 2 = since last int = the number of times the command was
    called since the previous poll/interval
- 3 = calls/sec = a calculated approximation of the number of times
    the command was called per second. This is calulated by
    taking the 'since last int' number and dividing by the
    approximate number of seconds since last refresh. this is
    not a highly accurate number, just an approximation.
- 4 = usec/call = average CPU time consumed for each call

### Sample output:

```
Redis 5.0.0 (standalone) on Darwin 18.2.0 x86_64 (pid: 9257)
uptime: 1 days, replication role: master, connected slaves: 0
142 total connections (0 new), 2 connected, used memory: 281.28M
12008 ops/sec, input: 492.06 kbps, output: 74.24 kbps

refresh interval: 3 seconds (press +/- to change)
sorting on 'total'
call            total    since last int    calls/sec    usec/call
-----------  --------  ----------------  -----------  -----------
sadd         76275982              8561         2853         1.35
spop         50528080              5724         1908         2.10
lpush        49574720              5616         1872         1.41
get          28607980              3163         1054         0.94
setbit       20027741              2189          729         1.26
zadd         19074577              2081          693         2.39
hset         19074382              2081          693         1.83
lpop         19074382              2081          693         1.75
del          14300565              1632          544         1.66
smembers     12400847              1303          434         4.31
set           2860234               324          108         1.83
incrby         953362               108           36         1.37
srandmember    953360               108           36         3.37
xadd           953359               108           36        11.56
llen           953359               108           36         1.04
bitcount        42877                 9            3        15.26
info             3985                 2            0        49.89
hget              312                 0            0         1.24
hmset             162                 0            0         5.00
zscore            156                 0            0         1.15
ping              126                 0            0         0.56
command            12                 0            0       604.75
scan                5                 0            0        40.00
auth                1                 0            0         1.00
sort on numeric columns by pressing 1-4. press esc to exit.
```

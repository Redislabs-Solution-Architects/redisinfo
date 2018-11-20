'''
A 'top-like' output for Redis info commandstats

example execution:
   python redisinfo.py localhost:6379

or with auth:
   python redisinfo.py my-redis-endpoint.com:15151 mypassword
'''

import redis
import time
import os
import tabulate

# Windows
if os.name == 'nt':
    import msvcrt

# Posix (Linux, OS X)
else:
    import sys
    import termios
    import atexit
    from select import select

class RedisInfo(redis.StrictRedis):
    '''
    Extend StrictRedis to make info calls pretty
    '''
    def info(self):
        return self.execute_command('info')

    def commandstats(self):
        return self.execute_command('info commandstats')


class KBHit:
    '''
    Class to handle the single character input. Found in several places,
    http://home.wlu.edu/~levys/software/kbhit.py may be the original...?

    '''
    def __init__(self):
        '''Creates a KBHit object that you can call to do various keyboard things.
        '''

        if os.name == 'nt':
            pass

        else:

            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.new_term = termios.tcgetattr(self.fd)
            self.old_term = termios.tcgetattr(self.fd)

            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)


    def set_normal_term(self):
        ''' Resets to normal terminal.  On Windows this is a no-op.
        '''

        if os.name == 'nt':
            pass

        else:
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


    def getch(self):
        ''' Returns a keyboard character after kbhit() has been called.
            Should not be called in the same program as getarrow().
        '''

        s = ''

        if os.name == 'nt':
            return msvcrt.getch().decode('utf-8')

        else:
            return sys.stdin.read(1)


    def kbhit(self, timeout):
        ''' Returns True if keyboard character was hit, False otherwise.
        '''
        if os.name == 'nt':
            return msvcrt.kbhit()

        else:
            dr,dw,de = select([sys.stdin], [], [], timeout)
            return dr != []


def connect_to_redis(**conf):
    try:
        # r = redis.StrictRedis(**conf)
        r = RedisInfo(**conf)
        r.ping()
    except Exception as e:
        print e
        exit()
    return r

# XXX: need to actually implement this
# for now just passing all args with no processing or checking
def get_command_line_args():
    return sys.argv

def get_connection_config(args):
    '''
    Expecting a list where:
    args[0] = *ignored*
    args[1] = redis-endpoing:port
    args[2] = password (optional)
    '''

    auth = ''
    [host, port] = args[1].split(':')
    if len(args) > 2:
        auth = args[2]
    connection_config = {
        'host': host, 'port': port, 'password': auth
    }
    return connection_config

def info_to_dict(infotxt):
    '''
    Convert Redis 'info' to python dictionary format

    Expected input is a string which is the output of the Redis 'info' command
    or any of its variants (i.e. 'info server', etc.)
    '''
    section = None
    infodict = {}
    for line in infotxt.splitlines():
        if line.startswith(' ') or line == '':
            continue

        if line.startswith('#'):
            section = line.split('#')[1].strip().lower()
            # infodict[section] = {}
            continue

        if section is None:
            # this should never happen
            print "error parsing info! line is =>{}<= but no section set!".format(line)
            continue

        # print "adding =>{}<=".format(line)
        k, v = line.split(':')
        if v is None:
            v = 'none'
        infodict[k] = v

    return infodict

def cmdstats_to_dict(cmdstats):
    '''
    Convert Redis 'info commandstats' output to python dictionary
    in the following format:
    csdict = {
        command: {
            calls: number of calls,
            usec: usec data,
            usec_per_call: usec/call data
        }
    }
    '''
    csdict = {}
    for line in cmdstats.splitlines():
        if line.startswith('#') or line.startswith(' '):
            continue

        [cmd_calls, usec, usecpc] = line.split(',')
        [cmd, calls] = cmd_calls.split(':')
        # remove 'cmdstats_' part of the command
        cmd = cmd.split('_')[1]
        csdict.update({
            cmd: {
                'calls': calls.split('=')[1],
                'usec': usec.split('=')[1],
                'usec_per_call': usecpc.split('=')[1]
            }
        })
    return csdict

def display_commandstats(cslast, csthis, sort, calcint, displayint):
    '''
    Function to display the command stats data
    This funtion takes two commandstats dictionaries (last and this), a sort
    value, an interval to use for calculations and an interval used for display

    cslast = the 'last' or previous commandstats in dictionary format
    csthis = the current commandstats dictionary
    sort = column to sort on 1-4
    calcint = interval to use for calculations. this is necessary because
              we can refresh sooner than displayint
    displayint = interval to use for display purposes
    '''
    display = []
    for call, data in csthis.iteritems():
        # print "processing call =>{}<= data =>{}<=".format(call, data)
        # print "comparing to =>{}<=".format(cslast[call])
        if call in cslast:
            calls = data['calls']
            diff = int(calls) - int(cslast[call]['calls'])
            usecpm = data['usec_per_call']
            display.append((call, calls, diff, diff/calcint, usecpm))

    #print "\n"
    headers = ['call', 'total', 'since last int', 'calls/sec', 'usec/call']
    floatfmt = ('','','','.0f','.2f')
    print "refresh interval: {} seconds (press +/- to change)".format(displayint)
    print "sorting on \'{}\'".format(headers[sort])
    display = sorted(display, key=lambda d: float(d[sort]), reverse=True)
    print tabulate.tabulate(display, headers, floatfmt=floatfmt)

def display_header(redisinfo, lastinfo=None):
    '''
    Function to assemble and display the header. Takes an info dictionary.
    '''

    if lastinfo is None:
        header = \
'''
Redis {redis_version} ({redis_mode}) on {os} (pid: {process_id})
uptime: {uptime_in_days} days, replication role: {role}, connected slaves: {connected_slaves}
{total_connections_received} total connections, {connected_clients} connected, used memory: {used_memory_human}
{instantaneous_ops_per_sec} ops/sec, input: {instantaneous_input_kbps} kbps, output: {instantaneous_output_kbps} kbps
'''
    else:
        # if we have a lastinfo, then calculate the diff of
        # total_connections_received and add that as a new key in redisinfo

        redisinfo['total_connections_received_diff'] = \
            int(redisinfo['total_connections_received']) - \
            int(lastinfo['total_connections_received'])

        # generate a header with the diff info
        header = \
'''
Redis {redis_version} ({redis_mode}) on {os} (pid: {process_id})
uptime: {uptime_in_days} days, replication role: {role}, connected slaves: {connected_slaves}
{total_connections_received} total connections ({total_connections_received_diff} new), {connected_clients} connected, used memory: {used_memory_human}
{instantaneous_ops_per_sec} ops/sec, input: {instantaneous_input_kbps} kbps, output: {instantaneous_output_kbps} kbps
'''

    print header.format(**redisinfo)


def main():
    interval = 3
    sort = 1
    args = get_command_line_args()
    connect_config = get_connection_config(args)
    rinfo = connect_to_redis(**connect_config)
    print "Connected to Redis."
    cslast = False
    csthis = False
    infolast = False
    infothis = False

    kb = KBHit()

    while True:

        if cslast is False:
            cslast = cmdstats_to_dict(rinfo.commandstats())
            infolast = info_to_dict(rinfo.info())
            display_header(infolast)
            print "Got first commandstats, waiting {} seconds to get the next.".format(interval)
            continue

        # thisint will be the actual interval for this cycle
        # it will differ from 'interval' if a key is pressed
        thisint = interval

        # start a timer. this will be passed as calcint to the
        # display_commandstats function if a key is pressed because
        # the display will update sooner than the normal interval
        t_begin = time.time()

        # wait 'interval' seconds for a keypress.
        if kb.kbhit(interval):

            # if a key is pressed, stop the timer and process the input
            waited = time.time() - t_begin
            c = kb.getch()
            if c == 'q' or ord(c) == 27: # ESC
                break
            if c == '=' or c == '+':
                interval += 1
            elif c == '-':
                interval -= 1
                if interval <= 0:
                    interval = 1
            elif c.isdigit():
                c = int(c)
                if c not in range(1,5):
                    print "ERROR: sort option must be 1-4"
                else:
                    sort = c
            else:
                print "ERROR: sort option must be 1-4"

            # set the actual interval for use in stats calculations
            thisint = round(waited, 0)
            if thisint < 1:
                thisint = 1

        # get commandstats
        csthis = cmdstats_to_dict(rinfo.commandstats())

        ## display header
        infothis = info_to_dict(rinfo.info())
        display_header(infothis, infolast)

        ## display commandstats
        display_commandstats(cslast, csthis, sort, thisint, interval)

        print "sort on numeric columns by pressing 1-4. press esc to exit."

        cslast = csthis
        infolast = infothis

    kb.set_normal_term()

if __name__ == "__main__":
    main()

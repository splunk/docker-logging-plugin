import itertools
import platform
import socket

import heapq
import operator
import traceback
import logging
from datetime import datetime

# third party
import psutil


def collect_process_stats(process_names):
    '''
    process cpu/memeory usage
    @return: a list of dict
    [
        {
            'name': <process_name>,
            'pid': <process_id>,
            'cpu_percent': <cpu_usage>,
            'memory_percent': <mem_usage>,
            'memory_info': <mem_info>,
        },
    ]
    '''

    psstats = []
    for proc in psutil.process_iter():
        if not _is_interested_process(proc, process_names):
            continue

        try:
            pstats = _get_proc_stats(proc)
            psstats.append(pstats)
        except psutil.NoSuchProcess:
            logging.warning('process has gone')
        except psutil.AccessDenied:
            logging.warning('access to process permission denied')
        except Exception:
            logging.warning(traceback.format_exc())
    return psstats


def _get_proc_stats(proc):
    attrs = ('name', 'pid', 'cpu_percent', 'memory_percent', 'memory_info')
    pstats = proc.as_dict(attrs=attrs)
    meminfo = pstats['memory_info']
    del pstats['memory_info']
    pstats['memory_info_rss'] = meminfo.rss
    pstats['memory_info_vms'] = meminfo.vms
    pstats['cmd'] = ' '.join(proc.cmdline())
    return pstats


def collect_topn_process_stats(n):
    '''
    @return: a dict
    {
        'topn_cpu_processs': [],
        'topn_memory_processs': [],
    }
    '''

    psstats = collect_process_stats([])

    top_cpu_ps = heapq.nlargest(
        n, psstats, key=operator.itemgetter('cpu_percent'))
    top_mem_ps = heapq.nlargest(
        n, psstats, key=operator.itemgetter('memory_percent'))
    return {
        'topn_cpu_processs': top_cpu_ps,
        'topn_memory_processs': top_mem_ps,
    }


def collect_system_stats():
    '''
    system cpu/memeory usage
    @returns: a dict
    {
        'cpu_percent_overall': <overall cpu_usage>,
        'cpu_percent_<idx>': <per cpu_usage>,
        'memory_usage': <memory usage>,
    }
    '''

    cpu_usage = psutil.cpu_percent(interval=0.5, percpu=False)
    per_cpu_usage = psutil.cpu_percent(interval=0.5, percpu=True)
    per_cpu_usage = {'cpu_percent_{}'.format(i): usage
                     for i, usage in enumerate(per_cpu_usage)}

    mem_usage = psutil.virtual_memory()
    mem_usage = {t: getattr(mem_usage, t) for t in mem_usage._fields}

    mem_usage.update(per_cpu_usage)
    mem_usage["cpu_usage"] = cpu_usage
    return mem_usage


def get_platform_info():
    platform_info = platform.uname()
    tags = ('system', 'node', 'release', 'version', 'machine')
    pinfo = ' '.join(('%s=%s' % (t, v)
                      for t, v in itertools.izip(tags, platform_info)))
    boot_time = psutil.boot_time()
    boot_time = datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S')

    return {
        'platform': pinfo,
        'cpu_count': psutil.cpu_count(),
        'mem_total': psutil.virtual_memory().total,
        'boot_time': boot_time,
        'hostname': socket.gethostname(),
    }


def _is_interested_process(proc, proc_names):
    if not proc_names:
        # No proc specified, all processes
        return True

    return proc.name() in proc_names

    # full_name = ' '.join(proc.cmdline())
    # if full_name in interested_ps_names:
    #    return True
    # return False


if __name__ == '__main__':
    print collect_process_stats(['init', 'systemd'])
    print collect_topn_process_stats(10)
    print collect_system_stats()
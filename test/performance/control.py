"""
Control logic for docker plugin perf tests
"""

# Import control logic for installing splunk
import functools

import daperfcommon.control
from daperfcommon.control import splunk_install


def _start_monitoring(ctrl, hec_url):
    # start monitoring plugin memory and cpu usage
    ctrl.logger.custom('Starting monitoring on docker node!')
    #hec_token = ctrl.properties['hec_token']

    role = ctrl.roles['docker_plugin']
    role_type = role.types['process_monitor']

    processes = role_type.properties['monit_processes']
    run_interval = role_type.properties['monitor_run_interval']


    kwargs_mon = {
        'processes': processes
    }
    # Run the monitoring method
    monit_job = role.dispatch(
        'monitor_processes',
        kwargs=kwargs_mon,
        max_runs=0,
        min_run_interval=run_interval,
        block_on_complete=False
        )

    ctrl.logger.custom('Monitoring started on docker node!')
    ctrl.logger.custom('Collecting metrics for processes: %s' % ' ### '.join(processes))

    return monit_job


def _runtest(ctrl, kwargs):
    # Run test
    ctrl.logger.custom('Running test')
    ctrl.roles['docker_plugin'].dispatch(
        'run_sizing_guide_test',
        kwargs=kwargs,
        block_on_complete=True,
        block_timeout=600
    )

    ctrl.logger.custom('Test completed')


def setup_environment():
    """Function decorator variant of _test_wrapper.
    """
    def decorated(func):
        def wrapper(*args, **kwargs):
            ctrl = args[0]
            ctrl.logger.custom('Inside docker_deploy wrapper')
            cwd = ctrl.properties['_linux_path']
            deploy_args = {
                'working_dir': cwd
            }

            ctrl.roles['docker_plugin'].dispatch(
                'deploy_and_enable_plugin',
                kwargs=deploy_args,
                block_on_complete=True
            )

            ctrl.logger.info("Docker service is up and plugin enabled!")

            error = False
            try:
                func(*args, **kwargs)
            except Exception as e:
                pass
                # todo: Handle known error and do not raise
                # error = True
                # raise
            finally:

                if error:
                    ctrl.logger.error('There was an error calling test from the test wrapper.')

                else:
                    ctrl.logger.custom('Running end-of-test jobs (if any) while agents are still online')
        return functools.wraps(func)(wrapper)
    return decorated


def setup_environment_2(ctrl):
    """Function decorator variant of _test_wrapper.
    """
    ctrl.logger.custom('Inside docker_deploy wrapper')
    cwd = ctrl.properties['_linux_path']
    deploy_args = {
        'working_dir': cwd
    }

    ctrl.roles['docker_plugin'].dispatch(
        'deploy_and_enable_plugin',
        kwargs=deploy_args,
        block_on_complete=True
    )

    ctrl.logger.info("Docker service is up and plugin enabled!")

    # if err:
    #     ctrl.logger.cusom('There was an error calling deploy_and_enable_plugin.')
    # else:
    #     ctrl.logger.custom('Running end-of-test jobs (if any) while agents are still online')


# @setup_environment()
@splunk_install()
def sizing_guide_test(ctrl):
    """
        Entry point for sizing guide test: run configurable events count
        on configurable number of containers
    """
    setup_environment_2(ctrl)
    ctrl.logger.custom('Getting test scenarios to run')

    params = ctrl.properties['test_params']
    scenarios = [params['scenario_one'], params['scenario_two']]
    hec_urls = daperfcommon.control.get_hec_urls(ctrl)

    # Loop through all test scenarios
    for scenario in scenarios:
        # Get test parameters for the scenario
        msg_cnt = scenario['message_count']
        container_cnt = scenario['container_count']
        # Start monitoring
        monit = _start_monitoring(ctrl, hec_urls[0])
        kwargs_test = {
            'hec_url': hec_urls[0], # TODO: send ELB if available
            'hec_token': ctrl.properties['hec_token'],
            'hec_source': ctrl.properties['hec_source'],
            'hec_sourcetype': ctrl.properties['source_type'],
            'message_count': msg_cnt,
            'container_count': container_cnt
        }

        # Run the test
        _runtest(ctrl, kwargs_test)

        # Stop monitoring
        ctrl.interrupt(job_name='monitor_process', block=True)

    # Cleanup and end test
    ctrl.end_test()









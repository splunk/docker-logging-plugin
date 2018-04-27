"""
Control logic for docker plugin perf tests
"""

# Import control logic for installing splunk
import splunkconductor.control

# Import a wrapper that issues some extra jobs at the end of a test even if it fails, ex. generate splunk diags
from splunkconductor.control import test_wrapper

import perftestshared.control


def _start_monitoring(ctrl, hec_url):
    # start monitoring plugin memory and cpu usage
    ctrl.logger.custom('Starting monitoring on docker node!')
    hec_token = ctrl.properties['hec_token']
    run_interval = ctrl.properties['monitor_run_interval']

    role = ctrl.roles['docker_plugin']
    test_type = role.types['process_monitor']
    processes = test_type.properties['processes']

    kwargs_mon = {
        'hec_url': hec_url,
        'hec_token': hec_token,
        'processes': processes
    }
    monit_job = ctrl.roles['docker_plugin'].dispatch(
        'monitor_process',
        kwargs=kwargs_mon,
        max_runs=0,
        min_run_interval=run_interval,
        per_run_timeout=120,
        block_on_complete=False
        )

    ctrl.logger.custom('Monitoring started on docker node!')
    ctrl.logger.custom('Collecting metrics for processes: %s' % '#'.join(processes))

    return monit_job


def _runtest(ctrl, kwargs):
    # Run test
    ctrl.roles['docker_plugin'].dispatch(
        'run_sizing_guide_test',
        kwargs=kwargs,
        block_on_complete=False
    )


@test_wrapper()
def sizing_guide_test(ctrl):
    """
        Entry point for sizing guide test: run configurable events count
        on configurable number of containers
    """

    # Deploy docker node
    ctrl.roles['docker_plugin'].dispatch('deploy_and_enable_plugin', block_on_complete=True)

    ctrl.logger.info("Done with plugin deployment. Docker service is up and plugin enabled!")

    # Install splunk
    hec_urls = perftestshared.control.install_splunk(ctrl)
    ctrl.logger.custom('Hec URLS: %s' ''.join(hec_urls))

    params = ctrl.properties['test_params']
    scenarios = [params['scenario_one'], params['scenario_two']]
    # Loop through all test scenarios
    for scenario in scenarios:
        # Get test parameters for the scenario
        msg_cnt = scenario['message_count']
        container_cnt = scenario['container_count']
        # Start monitoring
        monit = _start_monitoring(ctrl, hec_urls[0])
        kwargs_test = {
            'hec_url': hec_urls[0], # TODO: sent ELB if available
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






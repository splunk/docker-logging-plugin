"""
Control logic for docker plugin perf tests
"""

# Import control logic for installing splunk
import splunkconductor.control

# Import a wrapper that issues some extra jobs at the end of a test even if it fails, ex. generate splunk diags
from splunkconductor.control import test_wrapper

import perftestshared.control

# import hec_token_manager
#
#
# def setup_environment(c):
#     """
#         Setup perf test environment
#         Assumptions: ll nodes in the environment have been provisioned
#         1- Install splunk instance for HEC
#         2- Start resource monitoring on plugin node
#     :param c:
#     :return:
#     """
#
#     # Install Docker
#     c.logger.custom('Starting Docker deployment!')
#
#     c.roles['docker_plugin'].dispatch('deploy_and_enable_plugin', block_on_complete=True)
#
#     c.logger.info("Done with plugin deployment. Docker service is up and plugin enabled!")
#
#     # Install splunk instance
#     c.logger.info("Setting up splunk instance")
#     splunkconductor.control.prepare_splunk(c)
#     c.logger.info("Splunk instance setup completed!")
#
#     indexer_hosts = []
#     for agent in c.roles['indexer'].agents():
#         indexer_hosts.append(str(agent.orig_host))
#
#     # Get configuration items
#     hec_token = c.properties['hec_token']
#     token_name = c.properties['token_name']
#     source_type = c.properties['source_type']
#     hec_port = str(c.properties['hec_port'])
#     test_duration = int(c.properties['test_duration'])
#     monit_run_interval = int(c.properties['monitor_run_interval'])
#
#     c.logger.custom('#'.join(indexer_hosts))
#     mgt = hec_token_manager.HecTokenManager(hec_token, token_name, source_type)
#     mgt.create_hec_tokens(indexer_hosts)
#
#     hec_urls = ["https://" + host + ":" + hec_port for host in indexer_hosts]
#     hec_host = hec_urls[0]
#     c.logger.custom('Test HEC_HOST: %s' % hec_host)
#
#     # start monitoring plugin memory and cpu usage
#     c.logger.custom('Starting monitoring on docker node!')
#
#     kwargs_mon = {
#         'hec_url': hec_urls[0],
#         'hec_token': hec_token,
#     }
#     # stop monitoring after test completes
#     monit_run_count = int(test_duration / monit_run_interval) + 2
#     c.roles['docker_plugin'].dispatch(
#         'monitor_process',
#         kwargs=kwargs_mon,
#         max_runs=monit_run_count,
#         min_run_interval=monit_run_interval,
#         per_run_timeout=120,
#         block_on_complete=False
#         )
#
#     c.logger.custom('Monitoring started on docker node!')
#
#     # TODO: we could build a test env data structure to return here if needed
#     return hec_urls
#
#
# @test_wrapper()
# def sizing_guide_test(c):
#     """
#         Entry point for sizing guide test: run configurable events count
#         on configurable number of containers
#     """
#
#     # Test setup
#     hec_urls = setup_environment(c)
#
#     # Get test config from properties file
#     msg_cnt = c.properties['message_count']
#     container_cnt = c.properties['container_count']
#
#     c.logger.custom(
#         'Starting sizing guide test with %s containers and %s messages'
#         % (container_cnt, msg_cnt)
#     )
#     # Build test arguments
#     kwargs_test = {
#         'hec_url': hec_urls[0], # TODO: sent ELB if available
#         'hec_token': c.properties['hec_token'],
#         'hec_source': c.properties['hec_source'],
#         'hec_sourcetype': c.properties['source_type'],
#         'message_count': msg_cnt,
#         'container_count': container_cnt
#     }
#
#     # Run test
#     c.roles['docker_plugin'].dispatch(
#         'run_sizing_guide_test',
#         kwargs=kwargs_test,
#         block_on_complete=False
#     )
#     run_duration = int(c.properties['test_duration'])
#     # Start monitors of splunk instance for first run
#     c.logger.custom('Monitoring started on Splunk instances!')
#     splunkconductor.control.test_steady_state(c, duration_s=run_duration)
#
#     # Cleanup and end test
#     c.end_test()


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
def shared_test(ctrl):
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


    # # Run test
    # msg_cnt = ctrl.properties['message_count']
    # container_cnt = ctrl.properties['container_count']
    # kwargs_test = {
    #     'hec_url': hec_urls[0], # TODO: sent ELB if available
    #     'hec_token': ctrl.properties['hec_token'],
    #     'hec_source': ctrl.properties['hec_source'],
    #     'hec_sourcetype': ctrl.properties['source_type'],
    #     'message_count': msg_cnt,
    #     'container_count': container_cnt
    # }
    #
    # _runtest(ctrl, kwargs_test)
    #
    # # Stop monitoring
    # monit.interrupt()

    # Cleanup and end test
    ctrl.end_test()






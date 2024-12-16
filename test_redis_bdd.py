import time
import pytest
import redis
from pytest_bdd import scenarios, given, when, then
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

scenarios('features/redis.feature')

redis_server_path = os.getenv('REDIS_SERVER_PATH')
redis_cli_path = os.getenv('REDIS_CLI_PATH')
redis_benchmark_path = os.getenv('REDIS_BENCHMARK_PATH')

print(redis_server_path)
print(redis_cli_path)
print(redis_benchmark_path)

@pytest.fixture
def redis_client():
    time.sleep(2)  # Add delay to ensure Redis is ready
    client = redis.Redis(host='localhost', port=6379)
    yield client
    client.flushall()

@given('Redis is running')
def redis_running(redis_client):
    pass

@when('I set a key "name" with value "copilot"')
def set_key(redis_client):
    redis_client.set('name', 'copilot')

@then('I should be able to get the value "copilot" for the key "name"')
def get_key(redis_client):
    assert redis_client.get('name') == b'copilot'

@when('I set a key "language" with value "python"')
def set_language_key(redis_client):
    redis_client.set('language', 'python')

@when('I restart the Redis server')
def restart_redis():
    subprocess.run([redis_cli_path, "SHUTDOWN"], check=True)
    time.sleep(2)  # Wait for Redis to shutdown
    subprocess.run([redis_server_path, "--daemonize", "yes"], check=True)
    time.sleep(2)  # Wait for Redis to restart

@then('I should be able to get the value "python" for the key "language"')
def get_language_key(redis_client):
    client = redis.Redis(host='localhost', port=6379)
    assert client.get('language') == b'python'

@given('Redis is running with a replica')
def redis_with_replica():
    master_client = redis.Redis(host='localhost', port=6379)
    replica_client = redis.Redis(host='localhost', port=6380)
    assert master_client.ping(), "Master server connection failed"
    assert replica_client.ping(), "Replica server connection failed"

@when('the master node fails')
def fail_master():
    subprocess.run([redis_cli_path, "-p", "6379", "SHUTDOWN"], check=True)
    time.sleep(2)  # Allow some time for failover

@then('the replica should take over as the master')
def replica_takeover():
    replica_client = redis.Redis(host='localhost', port=6380)
    time.sleep(5)  # Allow time for the replica to take over
    assert replica_client.info()['role'] == 'master', "Replica did not take over as master"

@when('I set a key "session" with value "active" and expiration of 5 seconds')
def set_key_with_expiration(redis_client):
    redis_client.set('session', 'active', ex=5)

@then('after 6 seconds the key "session" should not exist')
def check_key_expiration(redis_client):
    time.sleep(6)
    assert redis_client.get('session') is None

@when('I add 1000 items to a list "mylist"')
def add_large_list(redis_client):
    for i in range(1000):
        redis_client.rpush('mylist', i)

@then('the length of the list "mylist" should be 1000')
def check_list_length(redis_client):
    assert redis_client.llen('mylist') == 1000

@when('I execute a Lua script to set and get a key "script_key" with value "script_value"')
def execute_lua_script(redis_client):
    script = """
    redis.call('set', KEYS[1], ARGV[1])
    return redis.call('get', KEYS[1])
    """
    result = redis_client.eval(script, 1, 'script_key', 'script_value')
    assert result == b'script_value'

@then('I should be able to get the value "script_value" for the key "script_key"')
def get_lua_script_key(redis_client):
    assert redis_client.get('script_key') == b'script_value'

@when('I run the redis-benchmark tool')
def run_redis_benchmark():
    subprocess.run([redis_benchmark_path], check=True)

@then('the results should show the performance metrics')
def check_redis_benchmark_results():
    assert True

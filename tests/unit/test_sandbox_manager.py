import pytest
import json
from unittest.mock import MagicMock, patch

import meta_agent.sandbox.sandbox_manager as sm
from meta_agent.sandbox.sandbox_manager import SandboxManager, SandboxExecutionError
import docker

# --- __init__ tests ---

def test_init_connection_error(monkeypatch):
    fake_client = MagicMock()
    fake_client.ping.side_effect = docker.errors.DockerException("ping fail")
    monkeypatch.setattr(sm.docker, 'from_env', lambda: fake_client)
    with pytest.raises(ConnectionError) as exc:
        SandboxManager()
    assert "Could not connect to Docker daemon" in str(exc.value)


def test_init_missing_seccomp(monkeypatch, tmp_path, capsys):
    fake_client = MagicMock()
    fake_client.ping.return_value = None
    monkeypatch.setattr(sm.docker, 'from_env', lambda: fake_client)
    # Point seccomp path to a non-existent file
    monkeypatch.setattr(sm, '_seccomp_profile_path', tmp_path / 'missing.json')
    manager = SandboxManager()
    assert manager.seccomp_profile is None
    captured = capsys.readouterr()
    assert "Seccomp profile not found" in captured.err


def test_init_invalid_seccomp(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_client.ping.return_value = None
    monkeypatch.setattr(sm.docker, 'from_env', lambda: fake_client)
    # Write invalid JSON
    bad_path = tmp_path / 'seccomp.json'
    bad_path.write_text("not json")
    monkeypatch.setattr(sm, '_seccomp_profile_path', bad_path)
    manager = SandboxManager()
    assert manager.seccomp_profile is None


def test_init_valid_seccomp(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_client.ping.return_value = None
    monkeypatch.setattr(sm.docker, 'from_env', lambda: fake_client)
    # Write valid JSON
    good_path = tmp_path / 'seccomp.json'
    data = {"foo": "bar"}
    good_path.write_text(json.dumps(data))
    monkeypatch.setattr(sm, '_seccomp_profile_path', good_path)
    manager = SandboxManager()
    assert manager.seccomp_profile == data

# --- run_code_in_sandbox tests ---

@patch('meta_agent.sandbox.sandbox_manager.docker')
def test_run_code_in_sandbox_file_not_found(mock_docker, tmp_path):
    # Setup mock Docker client
    mock_client = MagicMock()
    mock_docker.from_env.return_value = mock_client
    mock_client.ping.return_value = None
    
    # Mock containers.run to raise APIError for file not found
    mock_client.containers.run.side_effect = docker.errors.APIError(
        "Error response from daemon: cannot mount volume, path not found: /nonexistent/path"
    )
    
    manager = SandboxManager()
    
    # Create a non-existent directory path
    non_existent_dir = tmp_path / 'no_exist'
    # Ensure it doesn't exist (in case tmp_path/no_exist somehow exists)
    if non_existent_dir.exists():
        non_existent_dir.rmdir()
        
    with pytest.raises(SandboxExecutionError) as exc:
        manager.run_code_in_sandbox(non_existent_dir, ['cmd'])
    assert "Failed to run sandbox container" in str(exc.value)


def test_run_code_in_sandbox_success(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_client.ping.return_value = None
    
    # Mock container behavior
    container = MagicMock()
    container.wait.return_value = {'StatusCode': 42}
    def logs_side(stdout, stderr):
        return b'stdout' if stdout else b'stderr'
    container.logs.side_effect = logs_side
    fake_client.containers.run.return_value = container

    monkeypatch.setattr(sm.docker, 'from_env', lambda: fake_client)
    manager = SandboxManager()

    code_dir = tmp_path / 'code'
    code_dir.mkdir()
    exit_code, out, err = manager.run_code_in_sandbox(code_dir, ['cmd'])
    assert exit_code == 42
    assert out == 'stdout'
    assert err == 'stderr'
    container.remove.assert_called_with(force=True)


def test_run_code_image_not_found(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_client.ping.return_value = None
    fake_client.containers.run.side_effect = docker.errors.ImageNotFound("no image")
    monkeypatch.setattr(sm.docker, 'from_env', lambda: fake_client)
    manager = SandboxManager()
    code_dir = tmp_path / 'code'
    code_dir.mkdir()
    with pytest.raises(SandboxExecutionError) as exc:
        manager.run_code_in_sandbox(code_dir, ['cmd'])
    assert "Sandbox image" in str(exc.value)


@patch('meta_agent.sandbox.sandbox_manager.docker')
def test_run_code_api_error(mock_docker, tmp_path):
    # Setup mock Docker client
    mock_client = MagicMock()
    mock_docker.from_env.return_value = mock_client
    mock_client.ping.return_value = None
    
    # Mock containers.run to raise APIError
    mock_client.containers.run.side_effect = docker.errors.APIError("api failed")
    
    manager = SandboxManager()
    code_dir = tmp_path / 'code'
    code_dir.mkdir()
    
    with pytest.raises(SandboxExecutionError) as exc:
        manager.run_code_in_sandbox(code_dir, ['cmd'])
    assert "Failed to run sandbox container" in str(exc.value)


@patch('meta_agent.sandbox.sandbox_manager.docker')
def test_run_code_timeout(mock_docker, tmp_path):
    # Setup mock Docker client
    mock_client = MagicMock()
    mock_docker.from_env.return_value = mock_client
    mock_client.ping.return_value = None
    
    # Create a container mock that will simulate a timeout
    container = MagicMock()
    container.wait.side_effect = Exception("timeout")
    
    # Return the container mock from containers.run
    mock_client.containers.run.return_value = container

    manager = SandboxManager()
    code_dir = tmp_path / 'code'
    code_dir.mkdir()
    
    with pytest.raises(SandboxExecutionError) as exc:
        manager.run_code_in_sandbox(code_dir, ['cmd'], timeout=1)
    assert "Execution timed out" in str(exc.value)
    container.stop.assert_called()
    container.remove.assert_called()


def test_security_opt_with_seccomp(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_client.ping.return_value = None
    container = MagicMock()
    container.wait.return_value = {'StatusCode': 0}
    container.logs.return_value = b''
    fake_client.containers.run.return_value = container

    monkeypatch.setattr(sm.docker, 'from_env', lambda: fake_client)
    manager = SandboxManager()
    code_dir = tmp_path / 'code'
    code_dir.mkdir()
    # Inject a fake seccomp profile
    manager.seccomp_profile = {"k": "v"}
    manager.run_code_in_sandbox(code_dir, ['cmd'])
    _, kwargs = fake_client.containers.run.call_args
    assert 'security_opt' in kwargs
    opts = kwargs['security_opt']
    assert any(str(opt).startswith('seccomp=') for opt in opts)
    container.remove.assert_called_with(force=True)

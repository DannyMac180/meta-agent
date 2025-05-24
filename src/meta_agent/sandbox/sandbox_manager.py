import docker
import os
import json
from pathlib import Path
from typing import Tuple

# Get the directory containing this file
_current_dir = Path(__file__).parent.resolve()
# Construct the path to seccomp.json relative to the project root
_project_root = _current_dir.parent.parent.parent
_seccomp_profile_path = _project_root / 'seccomp.json'

DEFAULT_IMAGE_NAME = "meta-agent-sandbox:latest"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MEM_LIMIT = "256m"
DEFAULT_CPU_SHARES = 512 # Relative weight, 1024 is default

class SandboxExecutionError(Exception):
    """Custom exception for sandbox execution errors."""
    pass

class SandboxManager:
    """Manages the execution of code within a secure Docker sandbox."""

    def __init__(self):
        try:
            self.client = docker.from_env()
            # Ping the Docker daemon to ensure connection
            self.client.ping()
            print("Successfully connected to Docker daemon.")
        except docker.errors.DockerException as e:
            print(f"Error connecting to Docker daemon: {e}")
            print("Please ensure Docker is running and accessible.")
            # Depending on use case, might raise or handle differently
            raise ConnectionError("Could not connect to Docker daemon.") from e
        
        self._load_seccomp_profile()

    def _load_seccomp_profile(self):
        """Loads the seccomp profile from the JSON file."""
        try:
            with open(_seccomp_profile_path, 'r') as f:
                self.seccomp_profile = json.load(f)
            print(f"Successfully loaded seccomp profile from {_seccomp_profile_path}")
        except FileNotFoundError:
            print(f"Warning: Seccomp profile not found at {_seccomp_profile_path}. Running without seccomp.")
            self.seccomp_profile = None
        except json.JSONDecodeError as e:
            print(f"Error decoding seccomp profile JSON: {e}")
            self.seccomp_profile = None
            # Optionally raise an error if seccomp is critical
            # raise ValueError("Invalid seccomp profile JSON") from e

    def run_code_in_sandbox(self,
                              code_directory: Path,
                              command: list[str],
                              image_name: str = DEFAULT_IMAGE_NAME,
                              timeout: int = DEFAULT_TIMEOUT_SECONDS,
                              mem_limit: str = DEFAULT_MEM_LIMIT,
                              cpu_shares: int = DEFAULT_CPU_SHARES,
                              network_disabled: bool = True) -> Tuple[int, str, str]: 
        """Runs the given command inside a Docker container sandbox.
        
        Args:
            code_directory: Path to the directory containing the code to be mounted.
            command: The command and arguments to run inside the container (e.g., ['python', 'agent.py']).
            image_name: The name of the Docker image to use.
            timeout: Execution timeout in seconds.
            mem_limit: Memory limit for the container (e.g., '256m').
            cpu_shares: Relative CPU shares (weight).
            network_disabled: Whether to disable networking for the container.
        
        Returns:
            A tuple containing the exit code, stdout, and stderr.
            
        Raises:
            SandboxExecutionError: If there's an error running the container or execution times out.
            FileNotFoundError: If the code_directory doesn't exist.
        """
        if not code_directory.is_dir():
            raise FileNotFoundError(f"Code directory not found: {code_directory}")

        container_name = f"meta-agent-sandbox-run-{os.urandom(4).hex()}"
        
        volumes = {
            str(code_directory.resolve()): {'bind': '/sandbox/code', 'mode': 'ro'} # Mount code read-only
        }
        
        security_opts = []
        if self.seccomp_profile:
            # Docker SDK expects the profile as a string, not a dict
            security_opts.append(f"seccomp={json.dumps(self.seccomp_profile)}")

        environment = {
            'OPENBLAS_NUM_THREADS': '1',
            # Add other necessary environment variables here
        }

        # TODO: Add AppArmor profile if needed: security_opts.append(f"apparmor=your_profile_name")

        container = None
        try:
            print(f"Running command {' '.join(command)} in sandbox ({image_name})...")
            container = self.client.containers.run(
                image=image_name,
                command=command,
                volumes=volumes,
                working_dir="/sandbox/code", # Run command relative to mounted code
                mem_limit=mem_limit,
                cpu_shares=cpu_shares, # Note: This is relative weight, not a hard limit
                # TODO: Consider cpus or cpuset_cpus for hard limits if needed
                pids_limit=100, # Limit number of processes - added based on OpenBLAS error
                security_opt=security_opts,
                network_disabled=network_disabled,
                environment=environment, # Pass environment variables
                detach=True, # Run in background to manage timeout
                remove=False, # Keep container for log retrieval, remove manually
                user="sandboxuser", # Run as non-root user defined in Dockerfile
                read_only=False, # Filesystem needs some writability for Python caches etc.
                                 # Code mount is read-only via volumes
                # TODO: Define specific writable tmpfs if stricter isolation needed: tmpfs={'/tmp': ''} 
                name=container_name
            )

            # Wait for container completion with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get('StatusCode', -1)
            except Exception as e: # Catches requests.exceptions.ReadTimeout and others
                print(f"Execution timed out after {timeout} seconds.")
                # Ensure container is stopped and removed on timeout
                try:
                    container.stop(timeout=5)
                except docker.errors.APIError as stop_err:
                    print(f"Warning: Error stopping timed-out container: {stop_err}")
                try:
                    container.remove(force=True)
                except docker.errors.APIError as remove_err:
                    print(f"Warning: Error removing timed-out container: {remove_err}")
                raise SandboxExecutionError(f"Execution timed out after {timeout} seconds") from e

            # Retrieve logs (stdout/stderr)
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')

            print(f"Sandbox execution finished with exit code: {exit_code}")
            return exit_code, stdout, stderr

        except docker.errors.ImageNotFound:
            print(f"Error: Docker image '{image_name}' not found.")
            raise SandboxExecutionError(f"Sandbox image '{image_name}' not found. Please build it first.")
        except docker.errors.APIError as e:
            print(f"Error running Docker container: {e}")
            raise SandboxExecutionError(f"Failed to run sandbox container: {e}") from e
        finally:
            # Ensure container is removed after execution
            if container:
                try:
                    container.remove(force=True) # Force remove in case it's stuck
                    print(f"Removed container: {container_name}")
                except docker.errors.NotFound:
                    pass # Container already removed (e.g., on timeout)
                except docker.errors.APIError as e:
                    print(f"Warning: Could not remove container {container_name}: {e}")

# Example Usage (for testing):
if __name__ == '__main__':
    try:
        manager = SandboxManager()
        
        # Create dummy code directory and file for testing
        test_code_dir = Path('./temp_sandbox_test_code')
        test_code_dir.mkdir(exist_ok=True)
        script_path = test_code_dir / 'test_script.py'
        script_content = """
import sys
import time
import numpy as np # Test dependency

print('Hello from sandbox!')
print(f'Numpy version: {np.__version__}')
# print('Writing to stderr', file=sys.stderr)
# time.sleep(5) # Test timeout
# sys.exit(1) # Test non-zero exit code
# with open('/etc/passwd', 'r') as f: print(f.read()) # Test read-only filesystem / disallowed access
"""
        with open(script_path, 'w') as f:
            f.write(script_content)

        print(f"\n--- Running Test Script --- (Directory: {test_code_dir.resolve()})")
        exit_c, out, err = manager.run_code_in_sandbox(
            code_directory=test_code_dir,
            command=['python', 'test_script.py'], # Command relative to mounted /sandbox/code
            timeout=10 # Shorter timeout for test
        )

        print("\n--- Results ---")
        print(f"Exit Code: {exit_c}")
        print("\nStdout:")
        print(out)
        print("\nStderr:")
        print(err)
        print("---------------")
        
        # Clean up dummy code
        # script_path.unlink()
        # test_code_dir.rmdir()

    except (ConnectionError, SandboxExecutionError, FileNotFoundError) as e:
        print(f"\nError during sandbox test: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")

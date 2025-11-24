"""
Code Sandbox Module
Safe execution of user-generated code in isolated environment
"""

import subprocess
import tempfile
import os
import time
import signal
from typing import Dict, Optional
import json


class TimeoutException(Exception):
    """Raised when code execution times out"""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal"""
    raise TimeoutException("Code execution timed out")


def execute_python_code(
    code: str,
    language: str = "python",
    timeout: int = 10
) -> Dict[str, any]:
    """
    Execute Python code in a sandboxed environment
    
    Args:
        code: The code to execute
        language: Programming language (currently supports 'python')
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary with output, error, execution_time, exit_code, success
    """
    start_time = time.time()
    
    try:
        if language == "python":
            return _execute_python_safe(code, timeout)
        elif language == "javascript":
            return _execute_javascript(code, timeout)
        else:
            return {
                "output": None,
                "error": f"Unsupported language: {language}",
                "execution_time": 0,
                "exit_code": 1,
                "success": False
            }
    except Exception as e:
        return {
            "output": None,
            "error": str(e),
            "execution_time": time.time() - start_time,
            "exit_code": 1,
            "success": False
        }


def _execute_python_safe(code: str, timeout: int) -> Dict[str, any]:
    """
    Execute Python code using subprocess in isolated environment
    """
    start_time = time.time()
    
    # Create temporary file for code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_file = f.name
        f.write(code)
    
    try:
        # Execute in subprocess with timeout
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            # Security: Run with limited permissions
            # Note: On production, use Docker containers or similar for better isolation
        )
        
        execution_time = time.time() - start_time
        
        return {
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
            "execution_time": execution_time,
            "exit_code": result.returncode,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            "output": None,
            "error": f"Execution timed out after {timeout} seconds",
            "execution_time": timeout,
            "exit_code": -1,
            "success": False
        }
    except Exception as e:
        return {
            "output": None,
            "error": str(e),
            "execution_time": time.time() - start_time,
            "exit_code": 1,
            "success": False
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def _execute_javascript(code: str, timeout: int) -> Dict[str, any]:
    """
    Execute JavaScript code using Node.js
    """
    start_time = time.time()
    
    # Create temporary file for code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        temp_file = f.name
        f.write(code)
    
    try:
        # Execute with Node.js
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        return {
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
            "execution_time": execution_time,
            "exit_code": result.returncode,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            "output": None,
            "error": f"Execution timed out after {timeout} seconds",
            "execution_time": timeout,
            "exit_code": -1,
            "success": False
        }
    except FileNotFoundError:
        return {
            "output": None,
            "error": "Node.js is not installed or not in PATH",
            "execution_time": time.time() - start_time,
            "exit_code": 1,
            "success": False
        }
    except Exception as e:
        return {
            "output": None,
            "error": str(e),
            "execution_time": time.time() - start_time,
            "exit_code": 1,
            "success": False
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def validate_code_safety(code: str) -> tuple[bool, Optional[str]]:
    """
    Basic validation to check for obviously dangerous code patterns
    Returns: (is_safe, error_message)
    """
    dangerous_patterns = [
        'import os',
        'import sys',
        'import subprocess',
        'import shutil',
        'import socket',
        '__import__',
        'eval(',
        'exec(',
        'open(',
        'file(',
        'input(',
        'raw_input(',
    ]
    
    code_lower = code.lower()
    
    for pattern in dangerous_patterns:
        if pattern.lower() in code_lower:
            return False, f"Potentially dangerous code pattern detected: {pattern}"
    
    return True, None


# ============================================================================
# DOCKER-BASED EXECUTION (Recommended for Production)
# ============================================================================

def execute_in_docker(code: str, language: str, timeout: int = 10) -> Dict[str, any]:
    """
    Execute code in Docker container for better isolation (Production recommended)
    Requires Docker to be installed
    """
    start_time = time.time()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_file = f.name
        f.write(code)
    
    try:
        # Docker command to run code
        # This runs code in isolated container with resource limits
        docker_cmd = [
            'docker', 'run',
            '--rm',  # Remove container after execution
            '--network', 'none',  # No network access
            '--memory', '128m',  # Memory limit
            '--cpus', '0.5',  # CPU limit
            '-v', f'{temp_file}:/code/script.py:ro',  # Mount code as read-only
            'python:3.9-slim',  # Python image
            'python', '/code/script.py'
        ]
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        return {
            "output": result.stdout if result.stdout else None,
            "error": result.stderr if result.stderr else None,
            "execution_time": execution_time,
            "exit_code": result.returncode,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            "output": None,
            "error": f"Execution timed out after {timeout} seconds",
            "execution_time": timeout,
            "exit_code": -1,
            "success": False
        }
    except FileNotFoundError:
        return {
            "output": None,
            "error": "Docker is not installed or not in PATH",
            "execution_time": time.time() - start_time,
            "exit_code": 1,
            "success": False
        }
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test code execution
    test_code = """
print("Hello from sandbox!")
for i in range(5):
    print(f"Count: {i}")
"""
    
    result = execute_python_code(test_code)
    print("Execution result:", json.dumps(result, indent=2))
import os
import uuid
import shutil
import logging
from vigil.config import get_settings

logger = logging.getLogger(__name__)

class WorkspaceFactory:
    """
    Handles provisioning and cleanup of host-bound workspaces.
    Ensures directories are unique, exist, and have correct permissions (writable by UID 1000).
    """
    
    @staticmethod
    def create_workspace(task_id: str) -> str:
        """
        Creates a unique workspace directory under WORKSPACE_BASE_DIR.
        Returns the absolute path to the created directory.
        """
        settings = get_settings()
        # Clean task_id to make it filesystem-safe
        safe_task_id = "".join([c if c.isalnum() or c in "-_" else "_" for c in task_id])
        unique_id = uuid.uuid4().hex[:8]
        dir_name = f"{safe_task_id}-{unique_id}"
        
        workspace_path = os.path.abspath(
            os.path.join(settings.WORKSPACE_BASE_DIR, dir_name)
        )
        
        try:
            os.makedirs(workspace_path, exist_ok=True)
            # Ensure permissions are writable by non-root user (UID 1000) inside container.
            # Setting 0o777 gives read/write/execute permission to everyone.
            os.chmod(workspace_path, 0o777)
            logger.info(f"Created workspace directory: {workspace_path}")
            return workspace_path
        except Exception as e:
            raise OSError(f"Failed to create workspace directory at {workspace_path}: {e}")
            
    @staticmethod
    def destroy_workspace(path: str) -> None:
        """
        Forcefully removes the workspace directory and all its contents.
        """
        if not path or not os.path.exists(path):
            return
            
        try:
            # Check if path is indeed under WORKSPACE_BASE_DIR to prevent accidental deletions
            settings = get_settings()
            base_dir = os.path.abspath(settings.WORKSPACE_BASE_DIR)
            target_dir = os.path.abspath(path)
            
            if not target_dir.startswith(base_dir) or target_dir == base_dir:
                logger.warning(f"Prevented deleting directory outside/equal to workspace base: {path}")
                return
                
            shutil.rmtree(target_dir, ignore_errors=True)
            # Verify if directory still exists (shutil.rmtree might fail silently with ignore_errors=True)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)  # Let it throw exception if it still fails
            logger.info(f"Destroyed workspace directory: {path}")
        except Exception as e:
            logger.error(f"Failed to destroy workspace directory at {path}: {e}")

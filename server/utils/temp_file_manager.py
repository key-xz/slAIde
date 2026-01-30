"""context manager for safe temporary file handling"""
import os
import tempfile
from contextlib import contextmanager
from typing import Optional


@contextmanager
def temp_pptx_file(file_storage=None, suffix='.pptx'):
    """
    context manager for creating and cleaning up temporary PPTX files
    ensures files are always cleaned up even if exceptions occur
    
    usage:
        with temp_pptx_file(file_storage) as temp_path:
            # use temp_path
            pass
        # file automatically cleaned up
    """
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            if file_storage:
                file_storage.save(temp_path)
        
        yield temp_path
    
    finally:
        # clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                # log but don't raise to avoid masking original exception
                print(f"warning: failed to cleanup temp file {temp_path}: {e}")


class TempFileTracker:
    """tracks temporary files and ensures they're cleaned up"""
    
    def __init__(self):
        self.temp_files = set()
    
    def register(self, path: str):
        """register a temp file for cleanup"""
        self.temp_files.add(path)
    
    def unregister(self, path: str):
        """unregister a temp file (already cleaned up)"""
        self.temp_files.discard(path)
    
    def cleanup_all(self):
        """clean up all registered temp files"""
        for path in list(self.temp_files):
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as e:
                    print(f"warning: failed to cleanup temp file {path}: {e}")
        self.temp_files.clear()
    
    def cleanup_file(self, path: Optional[str]):
        """clean up a specific temp file"""
        if path and os.path.exists(path):
            try:
                os.unlink(path)
                self.temp_files.discard(path)
            except Exception as e:
                print(f"warning: failed to cleanup temp file {path}: {e}")

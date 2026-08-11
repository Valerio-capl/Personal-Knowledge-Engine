class SyncEngineError(Exception):
    """Base exception for engine.sync failures."""

class FileSyncError(SyncEngineError):
    """Raised when a single file fails during load/split/index."""
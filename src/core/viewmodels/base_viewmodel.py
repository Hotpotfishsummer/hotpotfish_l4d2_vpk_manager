"""Base ViewModel class for state management"""


class BaseViewModel:
    """
    Base class for all ViewModels.
    Provides observer pattern for state management.
    
    ViewModels should inherit from this class and use notify_listeners()
    to notify all observers when state changes.
    """
    
    def __init__(self):
        self._listeners = set()
    
    def add_listener(self, callback):
        """
        Add a listener callback that will be called when state changes.
        
        Args:
            callback: Function to call when state changes
        """
        if callable(callback):
            self._listeners.add(callback)
    
    def remove_listener(self, callback):
        """
        Remove a listener callback.
        
        Args:
            callback: Callback function to remove
        """
        self._listeners.discard(callback)
    
    def notify_listeners(self):
        """
        Notify all registered listeners of state change.
        Should be called whenever state changes.
        """
        for callback in self._listeners:
            try:
                callback()
            except Exception as e:
                print(f"Error in listener callback: {e}")
    
    def dispose(self):
        """
        Clean up resources. Should be called when ViewModel is no longer needed.
        Override this method in subclasses to clean up specific resources.
        """
        self._listeners.clear()

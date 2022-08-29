import logging


class PerformanceFilter(logging.Filter):
    def filter(self, record):
        # Checking if log message should be sent to performance.log based on if it starts with Performance or Spec
        
        if record.getMessage().startswith('Performance'):
            return True
        if record.getMessage().startswith('Spec'):
            return True
        
        return False


class NonPerfFilter(logging.Filter):
    def filter(self, record):
        # Making sure performance data only goes to performance.log
        
        if record.getMessage().startswith('Performance'):
            return False
        if record.getMessage().startswith('Spec'):
            return False
        
        return True

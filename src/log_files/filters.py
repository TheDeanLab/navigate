import logging


class PerformanceFilter(logging.Filter):
    def filter(self, record):
        # Checking if log message should be sent to performance.log based on if it starts with Performance or Spec
        return record.getMessage().startswith('Performance' or 'Spec')


class NonPerfFilter(logging.Filter):
    def filter(self, record):
        # Making sure performance data only goes to performance.log
        return not record.getMessage().startswith('Performance' or 'Spec')
        
        
            
        
            
            
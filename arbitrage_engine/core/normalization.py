class StandardizedFunding:
    @staticmethod
    def normalize_apr(raw_rate: float, interval_hours: float = 1.0) -> float:
        """
        Convert raw funding rate to Standardized Annualized Percentage Rate (SAPR).
        SAPR = (RawRate / IntervalHours) * 24 * 365 * 100
        Returns the APR as a percentage (e.g., 10.0 for 10%).
        """
        if interval_hours == 0:
            return 0.0
        return (raw_rate / interval_hours) * 24 * 365 * 100

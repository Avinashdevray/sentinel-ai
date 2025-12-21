"""
Custom exceptions for the FinAgent Sentinel validation layer.
These exceptions provide clear, actionable error messages for validation failures.
"""


class ValidationError(Exception):
    """Base exception for all validation errors"""
    pass


class InsufficientFundsError(ValidationError):
    """
    Raised when a transaction amount exceeds the available balance.
    This is a hard-blocking error that prevents execution.
    """
    def __init__(self, required_amount: float, available_balance: float):
        self.required_amount = required_amount
        self.available_balance = available_balance
        super().__init__(
            f"Insufficient funds: Transaction requires {required_amount:.2f} "
            f"but only {available_balance:.2f} is available"
        )


class InvalidAmountError(ValidationError):
    """
    Raised when an amount is invalid (negative, zero, or malformed).
    """
    def __init__(self, amount: str, reason: str = "Invalid amount"):
        self.amount = amount
        self.reason = reason
        super().__init__(f"{reason}: '{amount}'")


class BalanceExtractionError(ValidationError):
    """
    Raised when the balance cannot be extracted from the page.
    This could be due to missing elements, unexpected format, or page loading issues.
    """
    def __init__(self, selector: str, reason: str = "Could not extract balance"):
        self.selector = selector
        self.reason = reason
        super().__init__(f"{reason} using selector: '{selector}'")


class PercentageCalculationError(ValidationError):
    """
    Raised when percentage-based amount calculation fails.
    """
    def __init__(self, percentage: str, balance: str, reason: str = "Invalid percentage"):
        self.percentage = percentage
        self.balance = balance
        super().__init__(f"{reason}: {percentage} of {balance}")

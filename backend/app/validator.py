"""
Neuro-Symbolic Logic Validator - The "Spock" of the FinAgent System

This module provides strictly deterministic validation for financial operations.
It serves as the guardrails between AI intent parsing (Gemini Vision) and 
browser execution (Playwright), ensuring all calculations are precise and 
all transactions are validated before execution.

Key Principles:
1. NEVER rely on LLM for calculations
2. Use Decimal for financial precision
3. Extract state from DOM (100% accuracy on known sites)
4. Hard-block invalid transactions
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, Tuple
from playwright.async_api import Page
from app.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    BalanceExtractionError,
    PercentageCalculationError
)


class LogicValidator:
    """
    The 'Spock' of the system. Strictly logical, no AI guessing.
    All financial calculations and validations are deterministic.
    """
    
    # Common balance selectors for different banking sites
    BALANCE_SELECTORS = [
        "#wallet-balance",           # ID-based (most reliable)
        ".wallet-balance",           # Class-based
        "[data-testid='balance']",   # Test ID
        ".balance-amount",           # Common class pattern
        "#account-balance",          # Alternative ID
        "text=Balance:",             # Text-based fallback
    ]
    
    @staticmethod
    def clean_currency(value_str: str) -> Decimal:
        """
        Converts currency strings to strictly validated Decimals.
        
        Handles formats like:
        - '₹ 5,000.00'
        - '$500'
        - '€1,234.56'
        - '1000 USD'
        - '5000'
        
        Args:
            value_str: Currency string to clean
            
        Returns:
            Decimal representation of the amount
            
        Raises:
            InvalidAmountError: If the string cannot be parsed
        """
        if not value_str or not isinstance(value_str, str):
            raise InvalidAmountError(str(value_str), "Empty or invalid input")
        
        try:
            # Remove currency symbols, letters, and whitespace
            # Keep only digits, dots, commas, and minus sign
            cleaned = re.sub(r'[^\d.,\-]', '', value_str.strip())
            
            # Handle comma as thousand separator (remove it)
            # Assumes format like 1,000.00 or 1.000,00
            if ',' in cleaned and '.' in cleaned:
                # Determine which is decimal separator
                last_comma = cleaned.rfind(',')
                last_dot = cleaned.rfind('.')
                
                if last_dot > last_comma:
                    # Dot is decimal separator (e.g., 1,000.00)
                    cleaned = cleaned.replace(',', '')
                else:
                    # Comma is decimal separator (e.g., 1.000,00)
                    cleaned = cleaned.replace('.', '').replace(',', '.')
            elif ',' in cleaned:
                # Only comma - could be thousands or decimal
                # If comma is in last 3 positions, treat as decimal
                comma_pos = cleaned.rfind(',')
                if len(cleaned) - comma_pos <= 3:
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            
            # Convert to Decimal for precision
            amount = Decimal(cleaned)
            
            # Validate that amount is not negative (for balance)
            if amount < 0:
                raise InvalidAmountError(value_str, "Negative amount detected")
            
            return amount
            
        except (InvalidOperation, ValueError) as e:
            raise InvalidAmountError(value_str, f"Cannot parse currency: {str(e)}")
    
    @staticmethod
    async def extract_balance_from_page(page: Page) -> str:
        """
        Extracts the wallet balance from the current page using Playwright.
        
        This is the "OCR" mechanism - we read the actual DOM text for 100% accuracy
        on known banking sites. Uses multiple selector strategies for reliability.
        
        Args:
            page: Playwright Page object
            
        Returns:
            Raw balance string (e.g., "₹ 5,000.00")
            
        Raises:
            BalanceExtractionError: If balance cannot be found
        """
        for selector in LogicValidator.BALANCE_SELECTORS:
            try:
                # Wait briefly for element (non-blocking)
                element = await page.wait_for_selector(selector, timeout=2000)
                if element:
                    balance_text = await element.inner_text()
                    if balance_text and balance_text.strip():
                        print(f"✓ Extracted balance using selector '{selector}': {balance_text}")
                        return balance_text.strip()
            except Exception as e:
                # Try next selector
                continue
        
        # If all selectors fail, try to find any element containing "balance" or currency symbols
        try:
            # Look for elements with balance-related text
            balance_element = await page.locator("text=/balance|wallet|available/i").first
            if balance_element:
                balance_text = await balance_element.inner_text()
                # Extract number from text using regex
                match = re.search(r'[₹$€£]\s*[\d,]+\.?\d*', balance_text)
                if match:
                    print(f"✓ Extracted balance from text: {match.group()}")
                    return match.group()
        except Exception:
            pass
        
        raise BalanceExtractionError(
            ", ".join(LogicValidator.BALANCE_SELECTORS),
            "Balance element not found on page"
        )
    
    @staticmethod
    def validate_affordability(current_balance_str: str, amount_needed: float) -> Tuple[bool, Decimal, Decimal]:
        """
        Validates if a transaction is affordable given the current balance.
        
        Args:
            current_balance_str: Raw balance string from page (e.g., "₹ 5,000.00")
            amount_needed: Amount required for transaction
            
        Returns:
            Tuple of (is_affordable, balance_decimal, amount_decimal)
            
        Raises:
            InsufficientFundsError: If amount exceeds balance
            InvalidAmountError: If amount is invalid
        """
        # Clean and convert balance
        balance = LogicValidator.clean_currency(current_balance_str)
        
        # Validate amount
        if amount_needed <= 0:
            raise InvalidAmountError(
                str(amount_needed),
                "Transaction amount must be positive"
            )
        
        amount = Decimal(str(amount_needed))
        
        # Check affordability
        if amount > balance:
            raise InsufficientFundsError(
                required_amount=float(amount),
                available_balance=float(balance)
            )
        
        return True, balance, amount
    
    @staticmethod
    def calculate_dynamic_amount(intent_data: Dict[str, Any], current_balance_str: str) -> float:
        """
        Handles relative amounts like "Invest 10% of my balance".
        
        This function:
        1. Parses percentage from intent (e.g., "10%")
        2. Gets absolute balance
        3. Calculates precise amount using Decimal arithmetic
        
        Args:
            intent_data: Dictionary containing parsed intent with 'value' field
            current_balance_str: Raw balance string from page
            
        Returns:
            Calculated amount as float
            
        Raises:
            PercentageCalculationError: If percentage cannot be calculated
        """
        try:
            # Extract percentage from intent value
            value_str = str(intent_data.get('value', ''))
            
            # Look for percentage pattern (e.g., "10%", "10 percent", "10 %")
            percentage_match = re.search(r'(\d+(?:\.\d+)?)\s*%|(\d+(?:\.\d+)?)\s*percent', value_str, re.IGNORECASE)
            
            if not percentage_match:
                # Not a percentage - return the value as-is
                # Try to extract numeric value
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', value_str)
                if numeric_match:
                    return float(numeric_match.group(1))
                raise PercentageCalculationError(value_str, current_balance_str, "No numeric value found")
            
            # Extract percentage value
            percentage_str = percentage_match.group(1) or percentage_match.group(2)
            percentage = Decimal(percentage_str)
            
            # Validate percentage range
            if percentage <= 0 or percentage > 100:
                raise PercentageCalculationError(
                    f"{percentage}%",
                    current_balance_str,
                    "Percentage must be between 0 and 100"
                )
            
            # Clean balance
            balance = LogicValidator.clean_currency(current_balance_str)
            
            # Calculate amount: (percentage / 100) * balance
            # Use Decimal for precision
            amount = (percentage / Decimal('100')) * balance
            
            # Round to 2 decimal places for currency
            amount = amount.quantize(Decimal('0.01'))
            
            print(f"💰 Calculated {percentage}% of {balance} = {amount}")
            
            return float(amount)
            
        except (InvalidOperation, ValueError, AttributeError) as e:
            raise PercentageCalculationError(
                intent_data.get('value', 'N/A'),
                current_balance_str,
                f"Calculation failed: {str(e)}"
            )
    
    @staticmethod
    def extract_amount_from_action(action_dict: Dict[str, Any]) -> Optional[float]:
        """
        Extracts the transaction amount from an action dictionary.
        
        Looks for amount in:
        - action['value'] (for type actions)
        - action['reasoning'] (for click actions with embedded amounts)
        - action['selector'] (for buttons with amounts)
        
        Args:
            action_dict: Action dictionary from brain node
            
        Returns:
            Extracted amount as float, or None if no amount found
        """
        # Check value field first (most common for type actions)
        value = action_dict.get('value')
        if value:
            # Try to extract numeric value
            match = re.search(r'(\d+(?:\.\d+)?)', str(value))
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        
        # Check reasoning for embedded amounts
        reasoning = action_dict.get('reasoning', '')
        amount_match = re.search(r'(?:amount|invest|transfer|pay)\s*:?\s*[₹$€£]?\s*(\d+(?:,\d{3})*(?:\.\d+)?)', reasoning, re.IGNORECASE)
        if amount_match:
            try:
                amount_str = amount_match.group(1).replace(',', '')
                return float(amount_str)
            except ValueError:
                pass
        
        # Check selector for amount-based buttons
        selector = action_dict.get('selector', '')
        selector_match = re.search(r'(\d+(?:\.\d+)?)', str(selector))
        if selector_match:
            try:
                return float(selector_match.group(1))
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def is_financial_action(action_dict: Dict[str, Any]) -> bool:
        """
        Determines if an action involves financial transactions.
        
        Args:
            action_dict: Action dictionary from brain node
            
        Returns:
            True if action involves money, False otherwise
        """
        # Keywords that indicate financial actions
        financial_keywords = [
            'buy', 'pay', 'transfer', 'withdraw', 'invest', 'purchase',
            'send money', 'deposit', 'amount', 'rupees', 'dollars', 'gold'
        ]
        
        # Check action type, selector, reasoning, and value
        text_to_check = ' '.join([
            str(action_dict.get('action', '')),
            str(action_dict.get('selector', '')),
            str(action_dict.get('reasoning', '')),
            str(action_dict.get('value', ''))
        ]).lower()
        
        return any(keyword in text_to_check for keyword in financial_keywords)


# Singleton instance for easy access
_validator_instance = None

def get_validator() -> LogicValidator:
    """Get or create the singleton validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = LogicValidator()
    return _validator_instance

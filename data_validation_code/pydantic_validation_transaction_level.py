from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
import pandas as pd


class ZampTransaction(BaseModel):
    # Transaction fields - Required
    transactionId: str
    transactionDate: str
    transactionTotal: float
    transactionSubtotal: float
    transactionTax: float
    transactionShippingHandling: float
    transactionDiscount: float
    currency: str
    shipToCountry: str
    
    # Transaction fields - Optional
    transactionParentId: Optional[str] = None
    transactionMarketplace: Optional[str] = None
    transactionPurpose: Optional[str] = None
    transactionRecalculateTax: Optional[str] = None
    transactionEntity: Optional[str] = None
    
    # Ship To fields
    shipToAddress1: Optional[str] = None
    shipToAddress2: Optional[str] = None
    shipToCity: Optional[str] = None
    shipToState: Optional[str] = None
    shipToZip: Optional[str] = None
    
    # Ship From fields
    shipFromAddress1: Optional[str] = None
    shipFromAddress2: Optional[str] = None
    shipFromCity: Optional[str] = None
    shipFromState: Optional[str] = None
    shipFromZip: Optional[str] = None
    shipFromCountry: Optional[str] = None
    
    # Line Item fields - Required
    lineItemId: str
    lineItemAmount: float
    lineItemQuantity: int
    lineItemDiscount: float
    lineItemShippingHandling: float
    
    # Line Item fields - Optional
    lineItemProductName: Optional[str] = None
    lineItemProductTaxCode: Optional[str] = None
    
    @field_validator('transactionDate')
    @classmethod
    def validate_date(cls, v):
        pd.to_datetime(v)  # Will raise error if invalid
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        allowed = ['USD', 'CAD', 'EUR', 'GBP', 'AUD', 'MXN']
        if v.upper() not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v.upper()
    
    @field_validator('shipToCountry', 'shipFromCountry')
    @classmethod
    def validate_country(cls, v):
        if v and len(v) != 2:
            raise ValueError("Country code must be 2 characters (e.g., US, CA)")
        return v.upper() if v else v
    
    @field_validator('transactionRecalculateTax')
    @classmethod
    def validate_boolean_string(cls, v):
        if v and v.strip():  # Only validate if not empty
            if v.upper() not in ['TRUE', 'FALSE']:
                raise ValueError("Must be TRUE or FALSE")
            return v.upper()
        return None
    
    @field_validator('transactionId', 'lineItemId')
    @classmethod
    def validate_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()
    
    # @field_validator('transactionTax', 'transactionShippingHandling', 'transactionDiscount',
    #                  'lineItemDiscount', 'lineItemShippingHandling')
    # @classmethod
    # def validate_non_negative(cls, v):
    #     if v < 0:
    #         raise ValueError("Value cannot be negative")
    #     return v
    
    @field_validator('lineItemQuantity')
    @classmethod
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v
    
    @field_validator('shipToState', 'shipFromState')
    @classmethod
    def validate_state(cls, v):
        if v:
            v = v.strip().upper()
            if len(v) > 3:
                raise ValueError("State code must be 2-3 characters")
        return v if v else None
    
    # @field_validator('shipToZip', 'shipFromZip')
    # @classmethod
    # def validate_zip(cls, v):
    #     if v:
    #         v = v.strip()
    #         # Allow US ZIP (5 digits or 5+4) and international postal codes
    #         if len(v) > 20:
    #             raise ValueError("ZIP/Postal code too long (max 20 characters)")
    #     return v if v else None
    
    # @field_validator('shipToAddress1', 'shipToAddress2', 'shipFromAddress1', 'shipFromAddress2')
    # @classmethod
    # def validate_address(cls, v):
    #     if v and len(v) > 255:
    #         raise ValueError("Address too long (max 255 characters)")
    #     return v.strip() if v else None
    
    # @field_validator('shipToCity', 'shipFromCity')
    # @classmethod
    # def validate_city(cls, v):
    #     if v and len(v) > 100:
    #         raise ValueError("City name too long (max 100 characters)")
    #     return v.strip() if v else None
    
    # @field_validator('lineItemProductName')
    # @classmethod
    # def validate_product_name(cls, v):
    #     if v and len(v) > 500:
    #         raise ValueError("Product name too long (max 500 characters)")
    #     return v.strip() if v else None
    
    # @field_validator('lineItemProductTaxCode')
    # @classmethod
    # def validate_tax_code(cls, v):
    #     if v and len(v) > 50:
    #         raise ValueError("Tax code too long (max 50 characters)")
    #     return v.strip() if v else None
    
    @field_validator('transactionMarketplace')
    @classmethod
    def validate_marketplace(cls, v):
        if v and v.strip():  # Only validate if not empty after stripping
            allowed = ['AMAZON', 'META', 'TIKTOK', 'WALMART', 'TARGET_PLUS', 'ETSY', 
                      'EBAY', 'MIRAKL', 'MACYS', 'ALIBABA', 'SHOP']
            v_upper = v.strip().upper()
            if v_upper not in allowed:
                raise ValueError(f"transactionMarketplace must be one of {allowed}")
            return v_upper
        return None
    
    @field_validator('transactionEntity')
    @classmethod
    def validate_entity(cls, v):
        if v and v.strip():  # Only validate if not empty after stripping
            allowed = ['FEDERAL_GOV', 'STATE_GOV', 'EDU_PUBLIC', 'NON_PROFIT']
            v_upper = v.strip().upper()
            if v_upper not in allowed:
                raise ValueError(f"transactionEntity must be one of {allowed}")
            return v_upper
        return None
    
    @field_validator('transactionPurpose')
    @classmethod
    def validate_purpose(cls, v):
        if v and v.strip():  # Only validate if not empty after stripping
            allowed = ['RESALE', 'BUSINESS_USE', 'PERSONAL_USE', 'RENTAL_USE']
            v_upper = v.strip().upper()
            if v_upper not in allowed:
                raise ValueError(f"transactionPurpose must be one of {allowed}")
            return v_upper
        return None
    
    @model_validator(mode='after')
    def validate_transaction_total_calculation(self):
        """Validate: transactionTotal = transactionSubtotal + transactionShippingHandling + transactionTax - transactionDiscount"""
        calculated = (
            self.transactionSubtotal + 
            self.transactionShippingHandling + 
            self.transactionTax - 
            self.transactionDiscount
        )
        if abs(self.transactionTotal - calculated) > 0.01:
            raise ValueError(
                f"Transaction total mismatch: {self.transactionTotal} != {calculated:.2f} "
                f"(subtotal {self.transactionSubtotal} + shipping {self.transactionShippingHandling} + "
                f"tax {self.transactionTax} - discount {self.transactionDiscount})"
            )
        return self
    
    
    @model_validator(mode='after')
    def validate_no_tax_only_transactions(self):
        """Reject tax-only transactions"""
        if (self.transactionTax >= 1 and 
            (self.transactionTotal == 0 or self.transactionSubtotal == 0)):
            raise ValueError("Invalid: tax >= 1 but total or subtotal is 0")
        return self
    
    @model_validator(mode='after')
    def validate_line_item_consistency(self):
        """Validate line item amounts are reasonable"""
        if self.lineItemAmount < 0:
            raise ValueError("Line item amount cannot be negative")
        if abs(self.lineItemAmount) > abs(self.transactionSubtotal) + 0.01:
            raise ValueError(
                f"Line item amount {self.lineItemAmount} exceeds transaction subtotal {self.transactionSubtotal}"
            )
        return self


def validate_dataframe(df: pd.DataFrame, verbose: bool = True):
    """Validate DataFrame and return valid/invalid records"""
    valid = []
    invalid = []
    
    for idx, row in df.iterrows():
        try:
            record = row.to_dict()
            # Replace NaN with None
            record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
            ZampTransaction(**record)
            valid.append(record)
        except Exception as e:
            invalid.append({
                'row': idx, 
                'transactionId': record.get('transactionId', 'Unknown'), 
                'error': str(e)
            })
    
    if verbose:
        print(f"\n=== VALIDATION SUMMARY ===")
        print(f"Total records: {len(df)}")
        print(f"Valid: {len(valid)} ({len(valid)/len(df)*100:.1f}%)")
        print(f"Invalid: {len(invalid)} ({len(invalid)/len(df)*100:.1f}%)")
        
        if invalid:
            print(f"\n=== FIRST 5 VALIDATION ERRORS ===")
            for item in invalid[:5]:
                print(f"  Row {item['row']}, ID {item['transactionId']}: {item['error']}")
            if len(invalid) > 5:
                print(f"  ... and {len(invalid) - 5} more errors")
    
    return valid, invalid


def get_validation_stats(invalid_records: list) -> dict:
    """Get statistics on validation errors"""
    error_types = {}
    for record in invalid_records:
        error = record['error']
        # Extract error type (first part before details)
        error_type = error.split(':')[0] if ':' in error else error[:50]
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    return dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True))


# if __name__ == "__main__":
#     print("Zamp Transaction Validation Model")
#     print("=" * 50)
#     print("\nValidation Rules:")
#     print("  - Required fields: transactionId, dates, amounts, currency, shipToCountry")
#     print("  - Transaction total = subtotal + shipping + tax - discount")
#     print("  - shipToZip required when tax > 0")
#     print("  - No zero dollar orders")
#     print("  - No negative values for tax, shipping, discounts")
#     print("  - Line item quantity >= 1")
#     print("  - Field length limits enforced")
#     print("  - Currency: USD, CAD, EUR, GBP, AUD, MXN")
#     print("  - Marketplace: AMAZON, META, TIKTOK, WALMART, TARGET_PLUS, ETSY, EBAY, MIRAKL, MACYS, ALIBABA, SHOP")
#     print("  - Entity: FEDERAL_GOV, STATE_GOV, EDU_PUBLIC, NON_PROFIT")
#     print("  - Purpose: RESALE, BUSINESS_USE, PERSONAL_USE, RENTAL_USE")
#     print("\nUsage:")
#     print("  from pydantic_validation_transaction_level import validate_dataframe, get_validation_stats")
#     print("  valid, invalid = validate_dataframe(your_df)")
#     print("  stats = get_validation_stats(invalid)")
# return dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True))
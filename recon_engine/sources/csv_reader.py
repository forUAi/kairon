import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from dateutil import parser
from ..recon.recon_model import ExternalTxn

class CSVReader:
    """Reads external transaction data from CSV files"""
    
    def __init__(self, required_columns: List[str] = None):
        self.required_columns = required_columns or [
            'txn_id', 'amount', 'currency', 'timestamp'
        ]
    
    def read_from_file(self, file_path: str) -> List[ExternalTxn]:
        """Read transactions from CSV file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return self.read_from_content(file.read())
    
    def read_from_content(self, csv_content: str) -> List[ExternalTxn]:
        """Read transactions from CSV content string"""
        transactions = []
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Validate headers
        self._validate_headers(csv_reader.fieldnames)
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                txn = self._parse_row(row)
                transactions.append(txn)
            except Exception as e:
                raise ValueError(f"Error parsing row {row_num}: {str(e)}")
        
        return transactions
    
    def _validate_headers(self, headers: List[str]):
        """Validate CSV headers contain required columns"""
        missing_columns = []
        for required in self.required_columns:
            if required not in headers:
                missing_columns.append(required)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    def _parse_row(self, row: Dict[str, str]) -> ExternalTxn:
        """Parse a single CSV row into ExternalTxn"""
        try:
            # Parse timestamp
            timestamp_str = row['timestamp'].strip()
            timestamp = parser.parse(timestamp_str)
            
            # Parse amount
            amount_str = row['amount'].strip().replace('$', '').replace(',', '')
            amount = Decimal(amount_str)
            
            # Build metadata from additional columns
            metadata = {}
            for key, value in row.items():
                if key not in self.required_columns and value:
                    metadata[key] = value.strip()
            
            return ExternalTxn(
                txn_id=row['txn_id'].strip(),
                amount=amount,
                currency=row['currency'].strip().upper(),
                timestamp=timestamp,
                description=row.get('description', '').strip() or None,
                metadata=metadata
            )
        
        except Exception as e:
            raise ValueError(f"Invalid row data: {str(e)}")

class BankCSVReader(CSVReader):
    """Specialized CSV reader for bank statement formats"""
    
    def __init__(self):
        super().__init__([
            'transaction_id', 'amount', 'currency', 'date', 'description'
        ])
    
    def _parse_row(self, row: Dict[str, str]) -> ExternalTxn:
        """Parse bank-specific CSV format"""
        try:
            # Handle different date formats
            date_str = row['date'].strip()
            timestamp = parser.parse(date_str)
            
            # Handle negative amounts (debits)
            amount_str = row['amount'].strip().replace('$', '').replace(',', '')
            amount = abs(Decimal(amount_str))  # Take absolute value
            
            return ExternalTxn(
                txn_id=row['transaction_id'].strip(),
                amount=amount,
                currency=row['currency'].strip().upper(),
                timestamp=timestamp,
                description=row.get('description', '').strip() or None,
                metadata={
                    'source_format': 'bank_csv',
                    'original_amount': amount_str
                }
            )
        
        except Exception as e:
            raise ValueError(f"Invalid bank CSV row: {str(e)}")

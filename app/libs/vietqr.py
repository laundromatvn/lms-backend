import base64
import requests
from pydantic import BaseModel

from app.core.config import settings


class GenerateQRCodeRequest(BaseModel):
    amount: str
    content: str
    orderId: str
    terminalCode: str
    bankCode: str
    bankAccountNumber: str
    bankAccountName: str


class GenerateQRCodeResponse(BaseModel):
	bankCode: str
	bankName: str
	bankAccount: str
	userBankName: str
	amount: str
	content: str
	qrCode: str
	imgId: str
	existing: int
	transactionId: str 
	transactionRefId: str
	qrLink: str
	terminalCode: str
	subTerminalCode: str | None
	serviceCode: str
	orderId: str
	additionalData: list | None
	vaAccount: str


class VietQR:
    def __init__(self, **kwargs):
        self.base_url = settings.VIETQR_BASE_URL
        self.username = settings.VIETQR_USERNAME
        self.password = settings.VIETQR_PASSWORD
        self.bank_account = settings.VIETQR_BANK_ACCOUNT
        self.bank_code = settings.VIETQR_BANK_CODE
        self.user_bank_name = settings.VIETQR_USER_BANK_NAME
        self.trans_type = "C"
        self.qr_type = "0"

    def _get_token(self):
        url = f"{self.base_url}/vqr/api/token_generate"
        basic_auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {basic_auth}"
        }

        try:
            response = requests.post(url, headers=headers, timeout=10)
            
            # Check HTTP status
            if response.status_code != 200:
                error_msg = f"VietQR token API returned status {response.status_code}"
                try:
                    error_data = response.json()
                    if error_data.get("message"):
                        error_msg = f"VietQR token API error: {error_data.get('message')}"
                except:
                    error_msg = f"{error_msg}: {response.text}"
                raise ValueError(error_msg)
            
            response_data = response.json()
            
            # Check for error response
            if response_data.get("status") == "FAILED" or response_data.get("status") == "ERROR":
                error_message = response_data.get("message", "Unknown error")
                raise ValueError(f"VietQR token generation failed: {error_message}")
            
            access_token = response_data.get("access_token")
            if not access_token:
                raise ValueError("Access token not found in response")
            return access_token
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to get VietQR token: {str(e)}")

    def generate_qr_code(self, request: GenerateQRCodeRequest) -> tuple[str, str, str]:
        url = f"{self.base_url}/vqr/api/qr/generate-customer"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_token()}"
        }
        payload = {
            "amount": request.amount,
            "bankAccount": request.bankAccountNumber,
            "bankCode": request.bankCode,
            "userBankName": request.bankAccountName,
            "content": request.content,
            "transType": self.trans_type,
            "orderId": request.orderId,
            "qrType": self.qr_type,
            "terminalCode": request.terminalCode
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            
            # Check HTTP status
            if response.status_code != 200:
                error_msg = f"VietQR API returned status {response.status_code}"
                try:
                    error_data = response.json()
                    if error_data.get("message"):
                        error_msg = f"VietQR API error: {error_data.get('message')}"
                except:
                    error_msg = f"{error_msg}: {response.text}"
                raise ValueError(error_msg)
            
            response_data = response.json()
            
            # Check for error response
            if response_data.get("status") == "FAILED" or response_data.get("status") == "ERROR":
                error_message = response_data.get("message", "Unknown error")
                raise ValueError(f"VietQR QR generation failed: {error_message}")
            
            # Parse success response
            qrData = GenerateQRCodeResponse(**response_data)
            
            return qrData.qrCode, qrData.transactionId, qrData.transactionRefId
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to generate VietQR code: {str(e)}")

import requests

from app.core.config import settings


class GenerateQRCodeRequest:
    amount: str
    bankAccount: str
    bankCode: str
    userBankName: str
    content: str
    transType: str
    orderId: str
    qrType: str
    terminalCode: str


class GenerateQRCodeResponse:
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
	subTerminalCode: str
	serviceCode: str
	orderId: str
	additionalData: list
	vaAccount: str


class VietQR:
    def __init__(self):
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
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "username": self.username,
            "password": self.password
        }

        try:    
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response_data = response.json()
            
            access_token = response_data.get("access_token")
            if not access_token:
                raise ValueError("Access token not found")
            return access_token
        except Exception as e:
            raise e

    def generate_qr_code(self, request: GenerateQRCodeRequest) -> tuple[str, str, str]:
        url = f"{self.base_url}/vqr/api/qr_code_generate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_token()}"
        }
        payload = {
            "amount": request.amount,
            "bankAccount": self.bank_account,
            "bankCode": self.bank_code,
            "userBankName": self.user_bank_name,
            "content": request.content,
            "transType": self.trans_type,
            "orderId": request.orderId,
            "qrType": self.qr_type,
            "terminalCode": request.terminalCode
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response_data = response.json()
            qrData = GenerateQRCodeResponse(**response_data)
            
            return qrData.qrCode, qrData.transactionId, qrData.transactionRefId
        except Exception as e:
            raise e

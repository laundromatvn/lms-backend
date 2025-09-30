from pydantic import BaseModel


class VietQRTokenGenerateResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class VietQRTokenGenerateRequest(BaseModel):
    """Empty request body as per VietQR API specification"""
    pass


class VietQRTransactionSyncRequest(BaseModel):
    bankaccount: str
    amount: str
    transType: str
    content: str
    transactionid: str
    transactiontime: str
    referencenumber: str
    orderId: str
    terminalCode: str | None = None
    subTerminalCode: str | None = None
    serviceCode: str | None = None
    urlLink: str | None = None
    sign: str | None = None


class VietQRTransactionSyncObject(BaseModel):
    reftransactionid: str


class VietQRTransactionSyncResponse(BaseModel):
    error: bool
    errorReason: str
    toastMessage: str
    object: VietQRTransactionSyncObject | None = None

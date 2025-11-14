from pydantic import BaseModel


class VNPAYSyncUpSuccessTransactionRequest(BaseModel):
    merchantMethodCode: str
    methodCode: str
    merchantCode: str
    orderCode: str
    amount: int
    transactionCode: str
    responseCode: str
    responseMessage: str
    checksum: str


class VNPAYSyncUpCancelTransactionRequest(BaseModel):
    merchantMethodCode: str
    methodCode: str
    merchantCode: str
    orderCode: str
    amount: int
    transactionCode: str
    responseCode: str
    responseMessage: str
    checksum: str



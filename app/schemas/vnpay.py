from pydantic import BaseModel


class VNPAYIpnRequest(BaseModel):
    merchantMethodCode: str
    methodCode: str
    merchantCode: str
    orderCode: str
    amount: int
    transactionCode: str
    clientTransactionCode: str
    responseCode: str
    responseMessage: str
    checksum: str

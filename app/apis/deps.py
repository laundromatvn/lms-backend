import base64
from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional

from app.core.logging import logger
from app.core.config import settings
from app.utils.security.jwt import verify_token, verify_vietqr_internal_user
from app.libs.mqtt import mqtt_client, MQTTClient


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401)

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401)
        return verify_token(token)
    except Exception as e:
        logger.error("Invalid authorization header format", error=str(e))
        raise HTTPException(status_code=401)


def verify_vietqr_partner_credentials(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    """
    Verify VietQR partner credentials using Basic Authentication.
    This is used for the token generation endpoint.
    """
    logger.info(f"Verifying VietQR partner credentials: {credentials.username} {credentials.password}")
    correct_username = credentials.username == settings.VIETQR_PARTNER_USERNAME
    correct_password = credentials.password == settings.VIETQR_PARTNER_PASSWORD
    
    if not (correct_username and correct_password):
        logger.warning(f"Invalid VietQR partner credentials attempt: {credentials.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid VietQR partner credentials",
            headers={"WWW-Authenticate": "1Basic"},
        )

    return credentials


def get_vietqr_internal_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401)

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401)
        
        return verify_vietqr_internal_user(token)
    except Exception as e:
        logger.error("Invalid authorization header format", error=str(e))
        raise HTTPException(status_code=401)


def get_mqtt_client_dependency() -> MQTTClient:
    """
    Dependency to get the MQTT client instance.
    
    Returns:
        MQTTClient instance
        
    Raises:
        HTTPException: If MQTT client is not available
    """
    try:
        if not mqtt_client:
            raise HTTPException(
                status_code=503,
                detail="MQTT client not available"
            )
        return mqtt_client
    except Exception as e:
        logger.error(f"Failed to get MQTT client: {e}")
        raise HTTPException(
            status_code=503,
            detail="MQTT service unavailable"
        )

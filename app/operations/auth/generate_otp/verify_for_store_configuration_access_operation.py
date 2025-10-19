from app.enums.auth import OTPActionEnum
from app.models.user import User
from app.operations.auth.otp_generator import OtpGenerator


class GenerateOTPForVerifyForStoreConfigurationAccessOperation:

    @classmethod
    async def execute(cls, user: User) -> str:
        return await OtpGenerator.execute(user.id, OTPActionEnum.VERIFY_FOR_STORE_CONFIGURATION_ACCESS)



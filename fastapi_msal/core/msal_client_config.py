from enum import Enum
from pathlib import Path
from pydantic import BaseSettings

from .session import SessionBackend
from .utils import OptStr, StrList


class MSALPolicies(str, Enum):
    AAD_MULTI = "AAD_MULTI"
    AAD_SINGLE = "AAD_SINGLE"
    B2C_LOGIN = "B2C_1_LOGIN"
    B2C_PROFILE = "B2C_1_PROFILE"


class MSALSessionType(str, Enum):
    IN_MEMORY = "memory"
    FILE = "filesystem"


class MSALClientConfig(BaseSettings):
    # The following params must be set according to the app registration data recieved from AAD
    # https://docs.microsoft.com/azure/active-directory/develop/quickstart-v2-register-an-app
    client_id: OptStr
    client_credential: OptStr
    tenant: OptStr

    # Optional to set, see MSALPolicies for different options, default is single AAD (B2B)
    policy: MSALPolicies = MSALPolicies.AAD_SINGLE
    # Optional to set - If you are unsure don't set - it will be filled by MSAL as required
    scopes: StrList = list()
    # Optional to set - Defaults to in-memory sessions. See SessionType for options
    session_type: MSALSessionType = MSALSessionType.IN_MEMORY
    # Optional to set, only used when session_type is filesystem
    # Specifies the folder path session data is saved
    session_file_path: Path = Path("session")

    # Set the following params if you wish to change the default MSAL Router endpoints
    path_prefix: str = ""
    login_path: str = "/_login_route"
    token_path: str = "/token"
    logout_path: str = "/_logout_route"
    show_in_docs: bool = False

    # Optional Params for Logging and Telemetry with AAD
    app_name: OptStr = None
    app_version: OptStr = None

    @property
    def authority(self) -> str:
        if not self.policy:
            raise ValueError("Policy must be specificly set before use")
        authority_url: str = ""
        if MSALPolicies.AAD_SINGLE == self.policy:
            authority_url = f"https://login.microsoftonline.com/{self.tenant}"
        elif MSALPolicies.AAD_MULTI == self.policy:
            authority_url = "https://login.microsoftonline.com/common/"
        elif (
            MSALPolicies.B2C_LOGIN == self.policy
            or MSALPolicies.B2C_PROFILE == self.policy
        ):
            authority_url = f"https://{self.tenant}.b2clogin.com/{self.tenant}.onmicrosoft.com/{self.policy}"

        return authority_url

    @property
    def login_full_path(self) -> str:
        return f"{self.path_prefix}{self.login_path}"

    def make_session_backend(self) -> SessionBackend:
        if self.session_type is MSALSessionType.IN_MEMORY:
            from .session.inmemory import InMemorySessionBackend

            return InMemorySessionBackend(self)
        elif self.session_type is MSALSessionType.FILE:
            from .session.filesystem import FileSessionBackend

            return FileSessionBackend(self)
        else:
            # TODO other backend. sql, redis?
            raise NotImplementedError()
